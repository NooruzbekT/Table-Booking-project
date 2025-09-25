from datetime import datetime, timedelta
from rest_framework import serializers
from .models import Reservation


def check_time_overlap(table, date, time, duration, exclude_reservation=None):
    """ Проверяет, есть ли пересечение по времени для указанного столика. """
    start_datetime = datetime.combine(date, time)
    end_datetime = start_datetime + timedelta(minutes=duration)

    overlapping_reservations = Reservation.objects.filter(
        table=table,
        date=date,
        status__in=["pending", "confirmed"]
    )

    if exclude_reservation:
        overlapping_reservations = overlapping_reservations.exclude(id=exclude_reservation.id)

    for reservation in overlapping_reservations:
        existing_start = datetime.combine(reservation.date, reservation.time)
        existing_end = existing_start + timedelta(minutes=reservation.duration)

        if start_datetime < existing_end and end_datetime > existing_start:
            raise serializers.ValidationError("Этот столик уже забронирован на указанное время.")



class ReservationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = ["id", "table", "date", "time", "duration"]

    def validate(self, data):
        """ Валидация перед созданием бронирования. """
        request = self.context.get("request")
        if not request or not request.user or not request.user.is_authenticated:
            raise serializers.ValidationError("Требуется авторизация.")

        user = request.user
        table = data.get("table")
        date = data.get("date")
        time = data.get("time")
        duration = data.get("duration")

        if not all([table, date, time, duration]):
            raise serializers.ValidationError("Необходимо указать столик, дату, время и длительность.")

        # Проверка на 3 активных бронирования
        active_reservations = Reservation.objects.filter(
            user=user, status__in=["pending", "confirmed"]
        ).count()
        if active_reservations >= 3:
            raise serializers.ValidationError("У вас уже есть 3 активных бронирования.")

        # Проверка пересечения по времени
        check_time_overlap(table, date, time, duration)

        return data

    def create(self, validated_data):
        """ Создание бронирования с привязкой к пользователю. """
        request = self.context.get("request")
        validated_data["user"] = request.user
        return super().create(validated_data)



class ReservationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = ["date", "time", "duration"]

    def validate(self, data):
        """ Проверка перед обновлением бронирования. """
        instance = self.instance  # Текущее бронирование

        # Проверяем, что бронирование не отменено
        if instance.status == "cancelled":
            raise serializers.ValidationError("Нельзя изменить отмененное бронирование.")

        # Проверяем, что бронирование еще не началось
        start_time = datetime.combine(instance.date, instance.time)
        if datetime.now() >= start_time:
            raise serializers.ValidationError("Нельзя изменить прошедшее бронирование.")

        # Проверяем доступность нового времени
        new_date = data.get("date", instance.date)
        new_time = data.get("time", instance.time)
        new_duration = data.get("duration", instance.duration)

        check_time_overlap(instance.table, new_date, new_time, new_duration, exclude_reservation=instance)

        return data

    def update(self, instance, validated_data):
        """ Обновление бронирования. """
        instance.date = validated_data.get("date", instance.date)
        instance.time = validated_data.get("time", instance.time)
        instance.duration = validated_data.get("duration", instance.duration)
        instance.save()
        return instance


class ReservationCancelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = ["status"]  # Разрешаем менять только статус

    def validate(self, data):
        """ Проверка перед отменой бронирования. """
        instance = self.instance  # Текущее бронирование

        # Проверяем, что бронирование не уже отменено
        if instance.status == "cancelled":
            raise serializers.ValidationError("Это бронирование уже отменено.")

        # Проверяем, что бронирование еще не началось и есть 30 минут до него
        start_time = datetime.combine(instance.date, instance.time)
        if datetime.now() >= start_time:
            raise serializers.ValidationError("Нельзя отменить прошедшее бронирование.")
        if datetime.now() + timedelta(minutes=30) >= start_time:
            raise serializers.ValidationError("Нельзя отменить бронирование менее чем за 30 минут до начала.")

        return data

    def update(self, instance, validated_data):
        """ Отмена бронирования (изменение статуса). """
        instance.status = "cancelled"
        instance.save()
        return instance
