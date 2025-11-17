# Generated migration

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('tables', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Reservation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(verbose_name='Дата бронирования')),
                ('time', models.TimeField(verbose_name='Время бронирования')),
                ('duration', models.PositiveIntegerField(verbose_name='Длительность (минуты)')),
                ('status', models.CharField(choices=[('pending', 'Ожидает подтверждения'), ('confirmed', 'Подтверждено'), ('cancelled', 'Отменено')], default='pending', max_length=20, verbose_name='Статус')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('confirmation_token', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('table', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tables.table', verbose_name='Столик')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['date', 'status'], name='reservation_date_status_idx'),
                    models.Index(fields=['user', 'status'], name='reservation_user_status_idx'),
                    models.Index(fields=['table', 'date', 'status'], name='reservation_table_date_idx'),
                    models.Index(fields=['-created_at'], name='reservation_created_idx'),
                ],
            },
        ),
    ]
