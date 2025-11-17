from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
import logging
from .models import Reservation
from .serializers import (
    ReservationCreateSerializer,
    ReservationUpdateSerializer,
    ReservationCancelSerializer,
)
from .filters import ReservationFilter

logger = logging.getLogger(__name__)


@extend_schema(tags=['Reservation'])
class ReservationViewSet(viewsets.ModelViewSet):
    """ ViewSet для бронирований. """
    queryset = Reservation.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ReservationFilter

    def get_serializer_class(self):
        """ Выбираем сериализатор в зависимости от действия. """
        if self.action == "create":
            return ReservationCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return ReservationUpdateSerializer
        return ReservationCreateSerializer

    def perform_create(self, serializer):
        """ Привязываем бронирование к текущему пользователю. """
        reservation = serializer.save(user=self.request.user)
        logger.info(
            f"Reservation created: ID={reservation.id}, User={self.request.user.email}, "
            f"Table={reservation.table.number}, Date={reservation.date}, Time={reservation.time}"
        )

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """ Кастомный метод для отмены бронирования. """
        reservation = self.get_object()
        serializer = ReservationCancelSerializer(instance=reservation, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info(
            f"Reservation cancelled: ID={reservation.id}, User={request.user.email}, "
            f"Table={reservation.table.number}, Date={reservation.date}"
        )
        return Response({"detail": "Бронирование отменено."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="confirm/(?P<token>[0-9a-f-]+)", permission_classes=[AllowAny])
    def confirm_reservation(self, request, token=None):
        """
        Подтверждение бронирования по токену.
        """
        reservation = get_object_or_404(Reservation, confirmation_token=token)

        if reservation.status != "pending":
            logger.warning(
                f"Attempted to confirm non-pending reservation: ID={reservation.id}, Status={reservation.status}"
            )
            return Response({"error": "Бронирование уже подтверждено или отменено."},
                            status=status.HTTP_400_BAD_REQUEST)

        reservation.status = "confirmed"
        reservation.save()
        logger.info(
            f"Reservation confirmed: ID={reservation.id}, User={reservation.user.email}, "
            f"Table={reservation.table.number}, Date={reservation.date}"
        )

        return Response({"message": "Бронирование подтверждено!"}, status=status.HTTP_200_OK)


    def get_queryset(self):
        """
        Фильтруем бронирования только для текущего пользователя (если не админ).
        """
        user = self.request.user
        if user.is_staff:
            return Reservation.objects.all()
        return Reservation.objects.filter(user=user)
