from datetime import timedelta

from django.utils import timezone


def _build_reminder(client, date, today, opened):
    delta = (date - today).days
    if delta < 0:
        label, tone = f'متأخرة منذ {abs(delta)} يوم', 'overdue'
    elif delta == 0:
        label, tone = 'تبدأ اليوم', 'today'
    else:
        label, tone = f'بعد {delta} يوم', 'soon'
    return {
        'client': client,
        'date': date,
        'label': label,
        'tone': tone,
        'opened': opened,
    }


def zatca_reminders(user, days_ahead=2):
    """
    تذكيرات دورات ZATCA للمستخدم.

    تشمل حالتين:
      1. دورة مفتوحة بالفعل ويقترب تاريخ بدايتها.
      2. عميل حان (أو تجاوز) موعد دورته القادمة ولم تُفتح له دورة بعد.

    الأدمن يرى كل عملاء الشركة؛ المحاسب يرى عملاءه المسندين فقط.
    """
    from .models import ZatcaClient, ZatcaSession

    if not user.tenant or not (user.is_admin or user.is_accountant):
        return []

    today = timezone.localdate()
    horizon = today + timedelta(days=days_ahead)

    clients = ZatcaClient.objects.filter(tenant=user.tenant)
    if user.is_accountant and not user.is_admin:
        clients = clients.filter(assigned_accountant=user)
    clients = clients.prefetch_related('sessions')

    reminders = []
    for client in clients:
        active = next(
            (s for s in client.sessions.all() if s.status == ZatcaSession.STATUS_IN_PROGRESS),
            None,
        )
        if active:
            # دورة مفتوحة — نذكّر فقط إن كانت لم تبدأ بعد وتقترب
            if today <= active.start_date <= horizon:
                reminders.append(_build_reminder(client, active.start_date, today, opened=True))
            continue

        # لا توجد دورة نشطة — هل حان موعد القادمة؟
        next_start = client.next_session_start()
        if next_start and next_start <= horizon:
            reminders.append(_build_reminder(client, next_start, today, opened=False))

    reminders.sort(key=lambda r: r['date'])
    return reminders
