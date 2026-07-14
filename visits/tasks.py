import requests
from django.conf import settings
from django.core.mail import send_mail
from celery import shared_task
from django.utils import timezone
from datetime import timedelta


def send_telegram(chat_id, message):
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
    if not token or not chat_id:
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        response = requests.post(url, json={'chat_id': chat_id, 'text': message}, timeout=10)
        return response.status_code == 200
    except Exception:
        return False


def send_notification_email(user, subject, message):
    recipient = user.notification_email or user.email
    if not recipient:
        return False
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')
    try:
        send_mail(subject, message, from_email, [recipient])
        return True
    except Exception:
        return False


def notify_user(user, subject, message):
    sent = False
    if user.telegram_chat_id:
        sent = send_telegram(user.telegram_chat_id, message) or sent
    if user.notification_email or user.email:
        sent = send_notification_email(user, subject, message) or sent
    return sent


@shared_task
def send_visit_reminders():
    from .models import Visit

    now = timezone.now()
    reminder_start = now + timedelta(hours=23)
    reminder_end = now + timedelta(hours=25)

    visits = Visit.objects.filter(
        status='planned',
        visit_date__gte=reminder_start,
        visit_date__lte=reminder_end,
        reminder_sent=False,
    ).select_related('sales_rep', 'client')

    sent = 0
    for visit in visits:
        user = visit.sales_rep
        msg = (
            f"تذكير بزيارة غداً\n"
            f"العميل: {visit.client.name}\n"
            f"الشركة: {visit.client.company or '—'}\n"
            f"الوقت: {visit.visit_date.strftime('%Y-%m-%d %H:%M')}\n"
            f"الغرض: {visit.purpose or '—'}"
        )
        if notify_user(user, 'تذكير بزيارة غداً', msg):
            visit.reminder_sent = True
            visit.save(update_fields=['reminder_sent'])
            sent += 1

    return f"Sent {sent} reminders"


@shared_task
def send_event_reminders():
    from calendar_app.models import Event

    now = timezone.now()
    reminder_start = now + timedelta(hours=23)
    reminder_end = now + timedelta(hours=25)

    events = Event.objects.filter(
        is_done=False,
        reminder_sent=False,
        start_datetime__gte=reminder_start,
        start_datetime__lte=reminder_end,
    ).select_related('assigned_to', 'client')

    sent = 0
    for event in events:
        user = event.assigned_to
        msg = (
            f"تذكير بحدث غداً\n"
            f"العنوان: {event.title}\n"
            f"النوع: {event.get_event_type_display()}\n"
            f"الوقت: {event.start_datetime.strftime('%Y-%m-%d %H:%M')}\n"
            f"{'العميل: ' + event.client.name if event.client else ''}"
        )
        if notify_user(user, 'تذكير بحدث غداً', msg):
            event.reminder_sent = True
            event.save(update_fields=['reminder_sent'])
            sent += 1

    return f"Sent {sent} event reminders"
