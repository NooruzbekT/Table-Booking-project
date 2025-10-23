from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.conf import settings
from .models import Reservation
from .tasks import schedule_reminders, send_reservation_email  # ✅ добавили Celery-таску

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
