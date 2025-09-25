
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Reservation
from .tasks import schedule_reminders

@receiver(post_save, sender=Reservation)
def reservation_created(sender, instance, created, **kwargs):
    """
    Отправляет email с подтверждением бронирования и запланированными напоминаниями.
    """
    if created:
        confirm_link = f"{settings.SITE_URL}/api/reservation/reservations/confirm/{instance.confirmation_token}/"

        subject = "Подтвердите ваше бронирование"
        message = (
            f"Здравствуйте, {instance.user.email}!\n\n"
            f"Вы забронировали столик №{instance.table.number} на {instance.date} в {instance.time}.\n"
            f"Для подтверждения бронирования перейдите по ссылке: {confirm_link}\n\n"
            f"Если вы не подтвердите бронирование за 15 минут до начала, оно будет автоматически отменено.\n"
            f"Спасибо за выбор нашего ресторана!"
        )

        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [instance.user.email])


        schedule_reminders.delay(instance.id)

