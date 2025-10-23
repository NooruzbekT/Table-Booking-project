from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema

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
