from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Указываем Django настройки
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reservation_System.settings")

app = Celery("Reservation_System")


app.config_from_object("django.conf:settings", namespace="CELERY")

print("Celery BROKER:", app.conf.broker_url)
print("Celery BACKEND:", app.conf.result_backend)
app.autodiscover_tasks()
