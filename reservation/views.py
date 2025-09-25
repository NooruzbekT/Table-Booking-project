from rest_framework import viewsets, status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Reservation
from .serializers import (
    ReservationCreateSerializer,
    ReservationUpdateSerializer,
    ReservationCancelSerializer,
)

class ReservationViewSet(viewsets.ModelViewSet):
    """ ViewSet для бронирований. """
    queryset = Reservation.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """ Фильтруем бронирования по текущему пользователю. """
        return Reservation.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        """ Выбираем сериализатор в зависимости от действия. """
        if self.action == "create":
            return ReservationCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return ReservationUpdateSerializer
        return ReservationCreateSerializer

    def perform_create(self, serializer):
        """ Привязываем бронирование к текущему пользователю. """
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """ Кастомный метод для отмены бронирования. """
        reservation = self.get_object()
        serializer = ReservationCancelSerializer(instance=reservation, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Бронирование отменено."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="confirm/(?P<token>[0-9a-f-]+)", permission_classes=[AllowAny])
    def confirm_reservation(self, request, token=None):
        """
        Подтверждение бронирования по токену.
        """
        reservation = get_object_or_404(Reservation, confirmation_token=token)

        if reservation.status != "pending":
            return Response({"error": "Бронирование уже подтверждено или отменено."},
                            status=status.HTTP_400_BAD_REQUEST)

        reservation.status = "confirmed"
        reservation.save()

        return Response({"message": "Бронирование подтверждено!"}, status=status.HTTP_200_OK)


    def get_queryset(self):
        """
        Фильтруем бронирования только для текущего пользователя (если не админ).
        """
        user = self.request.user
        if user.is_staff:
            return Reservation.objects.all()
        return Reservation.objects.filter(user=user)
