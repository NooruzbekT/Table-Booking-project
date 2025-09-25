from django.core.mail import send_mail
from django.conf import settings

def send_verification_email(email, token):
    subject = "Подтверждение регистрации"
    message = f"Перейдите по ссылке для подтверждения: http://127.0.0.1:8000/api/user/users/verify-email/{token}/"
    send_mail(subject, message, settings.EMAIL_HOST_USER, [email])


def send_reset_password_email(email, reset_token):
    reset_link = f"http://127.0.0.1:8000/api/user/users/reset-password/{reset_token}/"
    subject = "Восстановление пароля"
    message = f"Для сброса пароля перейдите по ссылке: {reset_link}"
    send_mail(subject, message, settings.EMAIL_HOST_USER, [email])