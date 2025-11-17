from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.db import transaction
from django.conf import settings
from django.utils import timezone
import logging
from .models import Reservation

from .tasks import schedule_reminders, send_reservation_email  # ✅ добавили Celery-таску

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Reservation)
def reservation_created(sender, instance, created, **kwargs):
    if not created:
        return

    confirm_link = f"{settings.SITE_URL}/api/reservation/confirm/{instance.confirmation_token}/"
    subject = "Подтвердите ваше бронирование"
    message = (
        f"Здравствуйте, {instance.user.email}!\n\n"
        f"Вы забронировали столик №{instance.table.number} на {instance.date} в {instance.time}.\n"
        f"Для подтверждения бронирования перейдите по ссылке: {confirm_link}\n\n"
        f"Если вы не подтвердите бронирование за 15 минут до начала, оно будет автоматически отменено.\n"
        f"Спасибо за выбор нашего ресторана!"
    )

    def _enqueue():
        send_reservation_email.delay(instance.user.email, subject, message)
        schedule_reminders.delay(instance.id)  # планирование напоминаний

    transaction.on_commit(_enqueue)


@receiver(post_save, sender=Reservation)
def update_table_status_on_reservation_save(sender, instance, created, **kwargs):
    """
    Автоматически обновляет статус столика при создании или обновлении бронирования.
    Если бронирование подтверждено (confirmed) и активно, столик помечается как "reserved".
    """
    table = instance.table

    # Если бронирование подтверждено и еще не истекло
    if instance.status == "confirmed":
        now = timezone.now()
        reservation_datetime = timezone.make_aware(
            timezone.datetime.combine(instance.date, instance.time)
        )

        # Если бронирование еще не закончилось (учитываем длительность)
        end_time = reservation_datetime + timezone.timedelta(minutes=instance.duration)

        if now < end_time and table.status != "reserved":
            table.status = "reserved"
            table.save(update_fields=['status'])
            logger.info(f"Table #{table.number} status updated to 'reserved' due to reservation #{instance.id}")

    # Если бронирование отменено, проверяем, есть ли другие активные брони
    elif instance.status == "cancelled":
        update_table_status_if_no_active_reservations(table)


@receiver(post_delete, sender=Reservation)
def update_table_status_on_reservation_delete(sender, instance, **kwargs):
    """
    Автоматически обновляет статус столика при удалении бронирования.
    Если нет других активных бронирований, столик помечается как "available".
    """
    table = instance.table
    update_table_status_if_no_active_reservations(table)


def update_table_status_if_no_active_reservations(table):
    """
    Вспомогательная функция для проверки активных бронирований столика.
    Если активных бронирований нет, статус столика обновляется на "available".
    """
    now = timezone.now()

    # Проверяем, есть ли активные (подтвержденные) бронирования для этого столика
    active_reservations = Reservation.objects.filter(
        table=table,
        status="confirmed",
        date__gte=now.date()
    ).exists()

    if not active_reservations and table.status == "reserved":
        table.status = "available"
        table.save(update_fields=['status'])
        logger.info(f"Table #{table.number} status updated to 'available' (no active reservations)")
