from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

# Указываем Django настройки по умолчанию
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reservation_System.settings")

# Инициализация Celery
app = Celery("reservation_System")

# Загрузка конфигурации из settings.py (все переменные с префиксом CELERY_)
app.config_from_object("django.conf:settings", namespace="CELERY")

# Автоматически искать tasks.py во всех установленных приложениях
app.autodiscover_tasks()

# Настройка периодических задач (Celery Beat)
app.conf.beat_schedule = {
    'cleanup-old-reservations-daily': {
        'task': 'reservation.tasks.cleanup_old_reservations',
        'schedule': crontab(hour=3, minute=0),  # Запуск каждый день в 3:00 ночи
    },
}

# Проверочная задача (необязательно)
@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")

# Для проверки брокера/бэкенда при запуске
print("Celery BROKER:", app.conf.broker_url)
print("Celery BACKEND:", app.conf.result_backend)
