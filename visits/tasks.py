import requests
from celery import shared_task
from django.utils import timezone
from datetime import timedelta


def send_whatsapp(phone, api_key, message):
    url = "https://api.callmebot.com/whatsapp.php"
    params = {'phone': phone, 'text': message, 'apikey': api_key}
    try:
        response = requests.get(url, params=params, timeout=10)
        return response.status_code == 200
    except Exception:
        return False


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
        if user.whatsapp_number and user.callmebot_api_key:
            msg = (
                f"تذكير بزيارة غداً 📅\n"
                f"العميل: {visit.client.name}\n"
                f"الشركة: {visit.client.company or '—'}\n"
                f"الوقت: {visit.visit_date.strftime('%Y-%m-%d %H:%M')}\n"
                f"الغرض: {visit.purpose or '—'}"
            )
            if send_whatsapp(user.whatsapp_number, user.callmebot_api_key, msg):
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
        if user.whatsapp_number and user.callmebot_api_key:
            msg = (
                f"تذكير بحدث غداً 🔔\n"
                f"العنوان: {event.title}\n"
                f"النوع: {event.get_event_type_display()}\n"
                f"الوقت: {event.start_datetime.strftime('%Y-%m-%d %H:%M')}\n"
                f"{'العميل: ' + event.client.name if event.client else ''}"
            )
            if send_whatsapp(user.whatsapp_number, user.callmebot_api_key, msg):
                event.reminder_sent = True
                event.save(update_fields=['reminder_sent'])
                sent += 1

    return f"Sent {sent} event reminders"
