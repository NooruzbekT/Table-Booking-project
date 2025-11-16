from django.db import models


class Table(models.Model):
    STATUS_CHOICES = [
        ("available", "Доступен"),
        ("reserved", "Забронирован"),
        ("unavailable", "Недоступен"),
    ]

    TYPE_CHOICES = [
        ("standard", "Обычный"),
        ("vip", "VIP"),
        ("window", "У окна"),
        ("terrace", "На террасе"),
    ]

    number = models.PositiveIntegerField(unique=True, verbose_name="Номер столика")
    seats = models.PositiveIntegerField(verbose_name="Количество мест")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="Тип столика")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="available", verbose_name="Статус")

    class Meta:
        indexes = [
            # Индекс для фильтрации доступных столиков
            models.Index(fields=['status', 'seats'], name='table_status_seats_idx'),
            # Индекс для поиска по типу и статусу
            models.Index(fields=['type', 'status'], name='table_type_status_idx'),
        ]
        ordering = ['number']

    def __str__(self):
        return f"Стол {self.number} ({self.get_type_display()})"
