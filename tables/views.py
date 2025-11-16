from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter
from datetime import datetime, timedelta
from django.utils import timezone

from .models import Table
from .serializers import TableSerializer
from .filters import TableFilter
from reservation import models as reservation_models


@extend_schema(tags=['Tables'])
class TableViewSet(viewsets.ModelViewSet):
    """
    API для управления столиками.
    GET list/retrieve — для авторизованных пользователей.
    Создание/изменение/удаление/спец-действия — только для админов.
    """
    queryset = Table.objects.all()
    serializer_class = TableSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = TableFilter

    def get_permissions(self):
        # list/retrieve — авторизованным; остальное — только админам
        if self.action in ('list', 'retrieve'):
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]
        return [perm() for perm in permission_classes]

    def destroy(self, request, *args, **kwargs):
        """
        Запрещаем удалять столики, если на них есть активные бронирования.
        """
        table = self.get_object()
        has_active = reservation_models.Reservation.objects.filter(
            table=table,
            status__in=["pending", "confirmed"],
        ).exists()

        if has_active:
            return Response(
                {"error": "Нельзя удалить столик, если на него есть активные бронирования."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["patch"], url_path="set-status")
    def set_status(self, request, pk=None):
        """
        Изменение статуса столика (available/reserved/unavailable).
        Доступно только админам (наследует правило из get_permissions()).
        """
        table = self.get_object()
        new_status = request.data.get("status")

        if new_status not in {"available", "reserved", "unavailable"}:
            return Response({"error": "Неверный статус."}, status=status.HTTP_400_BAD_REQUEST)

        table.status = new_status
        table.save(update_fields=["status"])

        return Response({"message": f"Статус столика {table.number} изменён на {new_status}."})

    @extend_schema(
        summary="Поиск доступных столиков",
        parameters=[
            OpenApiParameter(name="date", required=True, type=str, description="Дата (YYYY-MM-DD)"),
            OpenApiParameter(name="time", required=True, type=str, description="Время начала (HH:MM)"),
            OpenApiParameter(name="duration", required=True, type=int, description="Длительность в минутах"),
            OpenApiParameter(name="seats", required=False, type=int, description="Минимальное количество мест"),
            OpenApiParameter(name="type", required=False, type=str, description="Тип столика (standard, vip, window, terrace)"),
        ],
    )
    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def available(self, request):
        """
        Возвращает список доступных столиков на указанную дату и время.
        Параметры: date, time, duration, seats (опционально), type (опционально)
        """
        # Получаем параметры запроса
        date_str = request.query_params.get("date")
        time_str = request.query_params.get("time")
        duration = request.query_params.get("duration")
        min_seats = request.query_params.get("seats")
        table_type = request.query_params.get("type")

        # Валидация обязательных параметров
        if not all([date_str, time_str, duration]):
            return Response(
                {"error": "Необходимо указать параметры: date, time, duration"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Парсим дату и время
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
            time = datetime.strptime(time_str, "%H:%M").time()
            duration = int(duration)

            # Проверяем, что дата не в прошлом
            if date < timezone.now().date():
                return Response(
                    {"error": "Нельзя бронировать на прошедшую дату"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Вычисляем временные рамки бронирования
            start_datetime = datetime.combine(date, time)
            end_datetime = start_datetime + timedelta(minutes=duration)

        except (ValueError, TypeError) as e:
            return Response(
                {"error": f"Неверный формат данных: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Фильтруем столики
        tables = Table.objects.filter(status="available")

        # Фильтр по количеству мест
        if min_seats:
            try:
                tables = tables.filter(seats__gte=int(min_seats))
            except ValueError:
                return Response(
                    {"error": "Неверный формат параметра seats"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Фильтр по типу столика
        if table_type:
            if table_type not in ["standard", "vip", "window", "terrace"]:
                return Response(
                    {"error": "Неверный тип столика"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            tables = tables.filter(type=table_type)

        # Проверяем занятость столиков
        available_tables = []
        for table in tables:
            # Ищем пересекающиеся бронирования
            overlapping = reservation_models.Reservation.objects.filter(
                table=table,
                date=date,
                status__in=["pending", "confirmed"]
            )

            has_conflict = False
            for reservation in overlapping:
                existing_start = datetime.combine(reservation.date, reservation.time)
                existing_end = existing_start + timedelta(minutes=reservation.duration)

                # Проверяем пересечение временных интервалов
                if start_datetime < existing_end and end_datetime > existing_start:
                    has_conflict = True
                    break

            if not has_conflict:
                available_tables.append(table)

        # Сериализуем результат
        serializer = self.get_serializer(available_tables, many=True)
        return Response({
            "date": date_str,
            "time": time_str,
            "duration": duration,
            "available_count": len(available_tables),
            "tables": serializer.data
        })
