"""
Run this once to register Celery Beat periodic tasks in the DB:
    python setup_celery_beat.py
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django_celery_beat.models import PeriodicTask, IntervalSchedule

every_hour, _ = IntervalSchedule.objects.get_or_create(
    every=1,
    period=IntervalSchedule.HOURS,
)

PeriodicTask.objects.update_or_create(
    name='send-visit-reminders',
    defaults={
        'interval': every_hour,
        'task': 'visits.tasks.send_visit_reminders',
    }
)

PeriodicTask.objects.update_or_create(
    name='send-event-reminders',
    defaults={
        'interval': every_hour,
        'task': 'visits.tasks.send_event_reminders',
    }
)

print("Periodic tasks registered successfully.")
