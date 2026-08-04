"""
Run this once to register Celery Beat periodic tasks in the DB:
    python setup_celery_beat.py
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule

every_hour, _ = IntervalSchedule.objects.get_or_create(
    every=1,
    period=IntervalSchedule.HOURS,
)

# التذكير الأول (خلال 25 ساعة من الموعد) — يعمل كل ساعة
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

# التذكير الصباحي (الثاني) — يومياً الساعة 8 صباحاً بتوقيت الرياض (CELERY_TIMEZONE)
daily_8am, _ = CrontabSchedule.objects.get_or_create(
    minute=0, hour=8, day_of_week='*', day_of_month='*', month_of_year='*',
)

PeriodicTask.objects.update_or_create(
    name='send-visit-day-reminders',
    defaults={
        'crontab': daily_8am,
        'interval': None,
        'task': 'visits.tasks.send_visit_day_reminders',
    }
)

PeriodicTask.objects.update_or_create(
    name='send-event-day-reminders',
    defaults={
        'crontab': daily_8am,
        'interval': None,
        'task': 'visits.tasks.send_event_day_reminders',
    }
)

print("Periodic tasks registered successfully.")
