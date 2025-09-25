from celery import shared_task
from django.conf import settings
from django.utils.timezone import now, make_aware
from datetime import datetime, timedelta
from .models import Reservation
from .utils import send_email

@shared_task
def send_email_notification(user_email, subject, message):
    """ Celery-задача для отправки email. """
    send_email(user_email, subject, message)

@shared_task
def schedule_reminders(reservation_id):
    """ Планируем напоминания и автоотмену брони. """
    try:
        reservation = Reservation.objects.get(id=reservation_id)
        start_time = reservation.time
        date = reservation.date
        start_datetime = make_aware(datetime.combine(date, start_time))

        # Формируем ссылку для подтверждения
        confirmation_link = f"{settings.SITE_URL}/confirm/{reservation.confirmation_token}"

        # Напоминание за 1 час
        reminder_time = start_datetime - timedelta(hours=1)
        if reminder_time > now():
            send_email_notification.apply_async(
                args=[reservation.user.email, "Напоминание о бронировании",
                      f"Ваше бронирование на {date} {start_time} начнется через 1 час."],
                eta=reminder_time
            )

        # Запрос на подтверждение за 15 минут
        confirm_time = start_datetime - timedelta(minutes=15)
        if confirm_time > now():
            send_email_notification.apply_async(
                args=[reservation.user.email, "Подтвердите бронирование",
                      f"Пожалуйста, подтвердите ваше бронирование на {date} {start_time}, иначе оно будет отменено.\n"
                      f"Подтвердите его здесь: {confirmation_link}"],
                eta=confirm_time
            )

            # Автоотмена, если не подтвердили
            auto_cancel_time = start_datetime - timedelta(minutes=14)
            auto_cancel_reservation.apply_async(args=[reservation.id], eta=auto_cancel_time)

    except Reservation.DoesNotExist:
        pass

@shared_task
def auto_cancel_reservation(reservation_id):
    """ Отмена брони, если не подтверждена за 15 минут. """
    try:
        reservation = Reservation.objects.get(id=reservation_id)
        if reservation.status == "pending":  # Только если не подтверждена
            reservation.status = "cancelled"
            reservation.save()
            send_email_notification.delay(
                reservation.user.email, "Бронирование отменено",
                f"Ваше бронирование на {reservation.date} {reservation.time} было автоматически отменено, так как не было подтверждено."
            )
    except Reservation.DoesNotExist:
        pass
