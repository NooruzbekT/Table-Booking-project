from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from smtplib import (
    SMTPException, SMTPServerDisconnected,
    SMTPDataError, SMTPSenderRefused, SMTPRecipientsRefused
)


TEMPORARY_SMTP_CODES = {421, 450, 451, 452, 454, 471, 472}


def _is_temporary_error(exc: Exception) -> bool:
    """Проверяет, является ли ошибка временной SMTP ошибкой"""
    if isinstance(exc, SMTPRecipientsRefused):
        try:
            codes = {code for (code, _msg) in exc.recipients.values()}
        except Exception:
            try:
                codes = {code for (code, _msg) in exc.args[0].values()}
            except Exception:
                codes = set()
        return any(int(c) in TEMPORARY_SMTP_CODES for c in codes if str(c).isdigit())

    if isinstance(exc, (SMTPServerDisconnected,)):
        return True

    if isinstance(exc, (SMTPDataError, SMTPSenderRefused)):
        try:
            code = int(getattr(exc, 'smtp_code', exc.args[0]))
            return code in TEMPORARY_SMTP_CODES
        except Exception:
            return False

    return False


@shared_task(bind=True, max_retries=6)
def send_email_task(self, to_email: str, subject: str, message: str):
    """
    Асинхронная отправка email через Celery.
    Автоматически повторяет попытку при временных SMTP ошибках.
    """
    try:
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [to_email],
            fail_silently=False,
        )
        return "ok"
    except Exception as exc:
        if _is_temporary_error(exc) and self.request.retries < self.max_retries:
            countdown = 60 * (2 ** self.request.retries)  # экспоненциальный backoff
            raise self.retry(exc=exc, countdown=countdown)
        raise


def send_verification_email(email: str, token: str):
    """Отправка email подтверждения регистрации (асинхронно через Celery)"""
    subject = "Подтверждение регистрации"
    message = f"Перейдите по ссылке для подтверждения: {settings.SITE_URL}/api/users/verify-email/{token}/"
    send_email_task.delay(email, subject, message)


def send_reset_password_email(email: str, reset_token: str):
    """Отправка email для сброса пароля (асинхронно через Celery)"""
    reset_link = f"{settings.SITE_URL}/api/users/reset-password/{reset_token}/"
    subject = "Восстановление пароля"
    message = f"Для сброса пароля перейдите по ссылке: {reset_link}"
    send_email_task.delay(email, subject, message)
