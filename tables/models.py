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

    def __str__(self):
        return f"Стол {self.number} ({self.get_type_display()})"
