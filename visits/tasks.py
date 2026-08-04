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
    """
    التذكير الأول: يُرسل مرة واحدة لكل زيارة، بأقرب وقت ممكن قبل الموعد.
    بدل نافذة ثابتة [23-25 ساعة] (كانت تُهمل المواعيد التي تُنشأ بمهلة أقصر)،
    نرسل لأي زيارة لم يمضِ موعدها بعد ولم يُرسل تذكيرها، ما دام باقٍ عليها
    25 ساعة أو أقل — فتغطي المواعيد القريبة أيضاً بتذكير فوري.
    """
    from .models import Visit

    now = timezone.now()
    horizon = now + timedelta(hours=25)

    visits = Visit.objects.filter(
        status='planned',
        visit_date__gte=now,
        visit_date__lte=horizon,
        reminder_sent=False,
    ).select_related('sales_rep', 'client')

    sent = 0
    for visit in visits:
        user = visit.sales_rep
        msg = (
            f"تذكير بزيارة قادمة\n"
            f"العميل: {visit.client.name}\n"
            f"الشركة: {visit.client.company or '—'}\n"
            f"الوقت: {visit.visit_date.strftime('%Y-%m-%d %H:%M')}\n"
            f"الغرض: {visit.purpose or '—'}"
        )
        if notify_user(user, 'تذكير بزيارة قادمة', msg):
            visit.reminder_sent = True
            visit.save(update_fields=['reminder_sent'])
            sent += 1

    return f"Sent {sent} reminders"


@shared_task
def send_visit_day_reminders():
    """
    التذكير الثاني (الصباحي): يعمل يومياً حوالي الساعة 8 صباحاً، ويرسل تذكيراً
    لكل زيارة مجدولة اليوم — بصرف النظر عن نجاح التذكير الأول من عدمه (تعزيز).
    """
    from .models import Visit

    today = timezone.localdate()
    visits = Visit.objects.filter(
        status='planned',
        visit_date__date=today,
        day_reminder_sent=False,
    ).select_related('sales_rep', 'client')

    sent = 0
    for visit in visits:
        user = visit.sales_rep
        msg = (
            f"تذكير — لديك زيارة اليوم\n"
            f"العميل: {visit.client.name}\n"
            f"الشركة: {visit.client.company or '—'}\n"
            f"الوقت: {visit.visit_date.strftime('%H:%M')}\n"
            f"الغرض: {visit.purpose or '—'}"
        )
        if notify_user(user, 'تذكير — لديك زيارة اليوم', msg):
            visit.day_reminder_sent = True
            visit.save(update_fields=['day_reminder_sent'])
            sent += 1

    return f"Sent {sent} same-day visit reminders"


@shared_task
def send_event_reminders():
    """التذكير الأول للأحداث — نفس منطق الزيارات (راجع send_visit_reminders)."""
    from calendar_app.models import Event

    now = timezone.now()
    horizon = now + timedelta(hours=25)

    events = Event.objects.filter(
        is_done=False,
        reminder_sent=False,
        start_datetime__gte=now,
        start_datetime__lte=horizon,
    ).select_related('assigned_to', 'client', 'review_client', 'zatca_client')

    sent = 0
    for event in events:
        user = event.assigned_to
        msg = (
            f"تذكير بحدث قادم\n"
            f"العنوان: {event.title}\n"
            f"النوع: {event.get_event_type_display()}\n"
            f"الوقت: {event.start_datetime.strftime('%Y-%m-%d %H:%M')}\n"
            f"{'العميل: ' + event.client_name + ' (' + event.client_section + ')' if event.linked_client else ''}"
        )
        if notify_user(user, 'تذكير بحدث قادم', msg):
            event.reminder_sent = True
            event.save(update_fields=['reminder_sent'])
            sent += 1

    return f"Sent {sent} event reminders"


@shared_task
def send_event_day_reminders():
    """التذكير الصباحي اليومي للأحداث — نفس منطق الزيارات."""
    from calendar_app.models import Event

    today = timezone.localdate()
    events = Event.objects.filter(
        is_done=False,
        start_datetime__date=today,
        day_reminder_sent=False,
    ).select_related('assigned_to', 'client', 'review_client', 'zatca_client')

    sent = 0
    for event in events:
        user = event.assigned_to
        msg = (
            f"تذكير — لديك حدث اليوم\n"
            f"العنوان: {event.title}\n"
            f"النوع: {event.get_event_type_display()}\n"
            f"الوقت: {event.start_datetime.strftime('%H:%M')}\n"
            f"{'العميل: ' + event.client_name + ' (' + event.client_section + ')' if event.linked_client else ''}"
        )
        if notify_user(user, 'تذكير — لديك حدث اليوم', msg):
            event.day_reminder_sent = True
            event.save(update_fields=['day_reminder_sent'])
            sent += 1

    return f"Sent {sent} same-day event reminders"
