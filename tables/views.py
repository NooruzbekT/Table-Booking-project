from rest_framework.decorators import action
from rest_framework import viewsets, status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Table
import reservation.models
from .serializers import TableSerializer
from .filters import TableFilter

class TableViewSet(viewsets.ModelViewSet):
    """
    API для управления столиками (только для администраторов).
    """
    queryset = Table.objects.all()
    serializer_class = TableSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_class = TableFilter

    def destroy(self, request, *args, **kwargs):
        """
        Запрещаем удалять столики, если на них есть активные бронирования.
        """
        table = self.get_object()
        active_reservations = reservation.models.Reservation.objects.filter(
            table=table, status__in=["pending", "confirmed"]
        ).exists()

        if active_reservations:
            return Response(
                {"error": "Нельзя удалить столик, если на него есть активные бронирования."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["patch"], url_path="set-status")
    def set_status(self, request, pk=None):
        """
        Изменение статуса столика (Доступен, Забронирован, Недоступен).
        """
        table = self.get_object()
        new_status = request.data.get("status")

        if new_status not in ["available", "reserved", "unavailable"]:
            return Response({"error": "Неверный статус."}, status=status.HTTP_400_BAD_REQUEST)

        table.status = new_status
        table.save()

        return Response({"message": f"Статус столика {table.number} изменён на {new_status}."})
