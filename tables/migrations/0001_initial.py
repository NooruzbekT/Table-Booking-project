# Generated migration

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Table',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.PositiveIntegerField(unique=True, verbose_name='Номер столика')),
                ('seats', models.PositiveIntegerField(verbose_name='Количество мест')),
                ('type', models.CharField(choices=[('standard', 'Обычный'), ('vip', 'VIP'), ('window', 'У окна'), ('terrace', 'На террасе')], max_length=20, verbose_name='Тип столика')),
                ('status', models.CharField(choices=[('available', 'Доступен'), ('reserved', 'Забронирован'), ('unavailable', 'Недоступен')], default='available', max_length=20, verbose_name='Статус')),
            ],
            options={
                'ordering': ['number'],
                'indexes': [
                    models.Index(fields=['status', 'seats'], name='table_status_seats_idx'),
                    models.Index(fields=['type', 'status'], name='table_type_status_idx'),
                ],
            },
        ),
    ]
