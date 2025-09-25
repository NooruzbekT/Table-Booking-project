import uuid

from django.db import models
from django.conf import settings
from tables.models import Table

class Reservation(models.Model):
    STATUS_CHOICES = [
        ("pending", "Ожидает подтверждения"),
        ("confirmed", "Подтверждено"),
        ("cancelled", "Отменено"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Пользователь")
    table = models.ForeignKey(Table, on_delete=models.CASCADE, verbose_name="Столик")
    date = models.DateField(verbose_name="Дата бронирования")
    time = models.TimeField(verbose_name="Время бронирования")
    duration = models.PositiveIntegerField(verbose_name="Длительность (минуты)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    confirmation_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    def __str__(self):
        return f"Бронирование {self.table.number} для {self.user.email} на {self.date} {self.time}"

