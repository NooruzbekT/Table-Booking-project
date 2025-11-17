from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils.timezone import now, make_aware
from datetime import datetime, timedelta
from smtplib import (
    SMTPException, SMTPServerDisconnected,
    SMTPDataError, SMTPSenderRefused, SMTPRecipientsRefused
)
import logging
from .models import Reservation

logger = logging.getLogger(__name__)


TEMPORARY_SMTP_CODES = {421, 450, 451, 452, 454, 471, 472}

def _is_temporary_error(exc: Exception) -> bool:

    if isinstance(exc, SMTPRecipientsRefused):
        try:
            codes = {code for (code, _msg) in exc.recipients.values()}
        except Exception:
            try:

                codes = {code for (code, _msg) in exc.args[0].values()}
            except Exception:
                codes = set()
        return any(int(c) in TEMPORARY_SMTP_CODES for c in codes if str(c).isdigit())


    if isinstance(exc, (SMTPServerDisconnected, )):
        return True

    # 3) Ошибки с кодом
    if isinstance(exc, (SMTPDataError, SMTPSenderRefused)):
        try:
            code = int(getattr(exc, 'smtp_code', exc.args[0]))
            return code in TEMPORARY_SMTP_CODES
        except Exception:
            return False

    # Остальные SMTPException без кода — не ретраим по умолчанию
    return False


@shared_task(bind=True, max_retries=6)
def send_reservation_email(self, to_email: str, subject: str, message: str):
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [to_email],
            fail_silently=False,
        )
        return "ok"
    except Exception as exc:
        if _is_temporary_error(exc) and self.request.retries < self.max_retries:
            countdown = 60 * (2 ** self.request.retries)  # экспоненциальный backoff
            raise self.retry(exc=exc, countdown=countdown)
        raise


@shared_task
def schedule_reminders(reservation_id: int):
    """
    Планируем напоминания и автоотмену брони.
    """
    try:
        reservation = Reservation.objects.get(id=reservation_id)
        start_time = reservation.time
        date = reservation.date
        start_datetime = make_aware(datetime.combine(date, start_time))

        # Ссылка подтверждения — приводим к API-роуту
        confirmation_link = f"{settings.SITE_URL}/api/reservation/confirm/{reservation.confirmation_token}/"

        # Напоминание за 1 час
        reminder_time = start_datetime - timedelta(hours=1)
        if reminder_time > now():
            send_reservation_email.apply_async(
                args=[
                    reservation.user.email,
                    "Напоминание о бронировании",
                    f"Ваше бронирование на {date} {start_time} начнется через 1 час."
                ],
                eta=reminder_time
            )

        # Запрос на подтверждение за 15 минут
        confirm_time = start_datetime - timedelta(minutes=20)
        if confirm_time > now():
            send_reservation_email.apply_async(
                args=[
                    reservation.user.email,
                    "Подтвердите бронирование",
                    (
                        f"Пожалуйста, подтвердите ваше бронирование на {date} {start_time}, "
                        f"иначе оно будет отменено.\n"
                        f"Подтвердите его здесь: {confirmation_link}"
                    )
                ],
                eta=confirm_time
            )

            # Автоотмена, если не подтвердили (через 1 минуту после письма)
            auto_cancel_time = start_datetime - timedelta(minutes=15)
            auto_cancel_reservation.apply_async(args=[reservation.id], eta=auto_cancel_time)

    except Reservation.DoesNotExist:
        # тихо выходим, если запись уже исчезла
        return


@shared_task
def auto_cancel_reservation(reservation_id: int):
    """
    Отмена брони, если не подтверждена за 15 минут до начала.
    """
    try:
        reservation = Reservation.objects.get(id=reservation_id)
        if reservation.status == "pending":
            reservation.status = "cancelled"
            reservation.save()

            send_reservation_email.delay(
                reservation.user.email,
                "Бронирование отменено",
                (
                    f"Ваше бронирование на {reservation.date} {reservation.time} "
                    f"было автоматически отменено, так как не было подтверждено."
                )
            )
    except Reservation.DoesNotExist:
        return


@shared_task
def cleanup_old_reservations():
    """
    Периодическая задача для очистки старых бронирований.
    Удаляет бронирования старше 30 дней.
    """
    cutoff_date = now().date() - timedelta(days=30)

    old_reservations = Reservation.objects.filter(date__lt=cutoff_date)
    count = old_reservations.count()

    if count > 0:
        old_reservations.delete()
        logger.info(f"Cleanup task: deleted {count} old reservations (older than {cutoff_date})")
    else:
        logger.info(f"Cleanup task: no old reservations to delete (cutoff: {cutoff_date})")
