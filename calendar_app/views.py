from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Event


@login_required
def calendar_view(request):
    if request.user.is_admin:
        events = Event.objects.filter(tenant=request.user.tenant)
    else:
        events = Event.objects.filter(tenant=request.user.tenant, assigned_to=request.user)

    from accounts.models import User as UserModel
    event_type = request.GET.get('type', '')
    source = request.GET.get('source', '')
    assigned_id = request.GET.get('assigned', '')
    if event_type:
        events = events.filter(event_type=event_type)
    if source:
        events = events.filter(source=source)
    if assigned_id and request.user.is_admin:
        events = events.filter(assigned_to_id=assigned_id)

    upcoming = events.filter(status=Event.STATUS_PENDING).order_by('start_datetime')

    source_role_map = {
        'sales': UserModel.ROLE_SALES,
        'accounts': UserModel.ROLE_ACCOUNTANT,
        'review': UserModel.ROLE_REVIEW,
    }
    source_users = []
    if source and source in source_role_map and request.user.is_admin:
        from accounts.utils import assignable_users
        source_users = assignable_users(request.user.tenant, source_role_map[source])

    return render(request, 'calendar_app/calendar.html', {
        'upcoming': upcoming,
        'source_users': source_users,
    })


@login_required
def event_create(request):
    from .forms import EventForm
    form = EventForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        event = form.save(commit=False)
        event.tenant = request.user.tenant
        event.created_by = request.user
        if not request.user.is_admin:
            event.assigned_to = request.user
            if request.user.is_sales:
                event.source = 'sales'
            elif request.user.is_accountant:
                event.source = 'accounts'
            elif request.user.is_review:
                event.source = 'review'
        event.save()
        from audit_log.utils import log_action
        from audit_log.models import AuditLog
        log_action(request, AuditLog.ACTION_CREATE, obj=event)
        messages.success(request, 'تم إضافة الحدث')
        return redirect('calendar_view')
    return render(request, 'calendar_app/form.html', {'form': form, 'title': 'إضافة حدث'})


@login_required
def event_toggle_done(request, pk):
    event = get_object_or_404(Event, pk=pk, tenant=request.user.tenant)
    if not request.user.is_admin and event.assigned_to != request.user:
        return redirect('calendar_view')
    if request.method == 'POST':
        event.status = Event.STATUS_DONE
        event.is_done = True
        if request.POST.get('notes'):
            event.notes = request.POST['notes']
        event.save()
        from audit_log.utils import log_action
        from audit_log.models import AuditLog
        log_action(request, AuditLog.ACTION_UPDATE, obj=event,
                   changes={'status': {'من': 'pending', 'إلى': 'done'}})
    return redirect('calendar_view')


@login_required
def event_edit(request, pk):
    from .forms import EventForm
    event = get_object_or_404(Event, pk=pk, tenant=request.user.tenant)
    form = EventForm(request.POST or None, instance=event, user=request.user)
    form.fields.pop('client', None)
    if request.method == 'POST' and form.is_valid():
        reschedule_note = request.POST.get('reschedule_note', '')
        # نحفظ نسخة من بيانات الحدث الأصلي قبل التعديل
        original_title    = event.title
        original_datetime = event.start_datetime
        original_notes    = event.notes

        # نغيّر الأصلي لـ rescheduled
        event.status = Event.STATUS_RESCHEDULED
        if reschedule_note:
            event.notes = reschedule_note
        event.save(update_fields=['status', 'notes'])

        # ننشئ حدث جديد pending بالبيانات الجديدة من الفورم
        new_event = Event(
            tenant      = event.tenant,
            created_by  = event.created_by,
            assigned_to = event.assigned_to,
            client      = event.client,
            review_client = event.review_client,
            zatca_client  = event.zatca_client,
            source      = event.source,
            event_type  = form.cleaned_data.get('event_type', event.event_type),
            title       = form.cleaned_data.get('title', original_title),
            start_datetime = form.cleaned_data.get('start_datetime', original_datetime),
            notes       = form.cleaned_data.get('notes', ''),
            status      = Event.STATUS_PENDING,
        )
        new_event.save()

        from audit_log.utils import log_action
        from audit_log.models import AuditLog
        log_action(request, AuditLog.ACTION_UPDATE, obj=event,
                   changes={'status': {'من': 'pending', 'إلى': 'rescheduled'}})
        messages.success(request, 'تم تحديث الحدث')
        return redirect('calendar_view')
    return render(request, 'calendar_app/form.html', {'form': form, 'title': 'إعادة جدولة الحدث', 'event': event})


@login_required
def event_reschedule(request, pk):
    event = get_object_or_404(Event, pk=pk, tenant=request.user.tenant)
    if request.method == 'POST':
        new_datetime_str = request.POST.get('start_datetime', '')
        reschedule_note  = request.POST.get('reschedule_note', '')
        if new_datetime_str:
            from django.utils.dateparse import parse_datetime
            from django.utils import timezone as tz
            new_datetime = parse_datetime(new_datetime_str)
            if new_datetime and tz.is_naive(new_datetime):
                new_datetime = tz.make_aware(new_datetime)

            # نحفظ الأصلي كـ rescheduled
            event.status = Event.STATUS_RESCHEDULED
            if reschedule_note:
                event.notes = reschedule_note
            event.save(update_fields=['status', 'notes'])

            # ننشئ حدث جديد pending
            Event.objects.create(
                tenant         = event.tenant,
                created_by     = event.created_by,
                assigned_to    = event.assigned_to,
                client         = event.client,
                review_client  = event.review_client,
                zatca_client   = event.zatca_client,
                source         = event.source,
                event_type     = event.event_type,
                title          = event.title,
                start_datetime = new_datetime,
                status         = Event.STATUS_PENDING,
            )

            from audit_log.utils import log_action
            from audit_log.models import AuditLog
            log_action(request, AuditLog.ACTION_UPDATE, obj=event,
                       changes={'status': {'من': 'pending', 'إلى': 'rescheduled'}})
            messages.success(request, 'تم إعادة جدولة الحدث')
    return redirect('calendar_view')


@login_required
def event_cancel(request, pk):
    event = get_object_or_404(Event, pk=pk, tenant=request.user.tenant)
    if not request.user.is_admin and event.assigned_to != request.user:
        return redirect('calendar_view')
    if request.method == 'POST':
        event.status = Event.STATUS_CANCELLED
        cancel_note = request.POST.get('notes', '')
        if cancel_note:
            event.notes = cancel_note
        event.save()
        from audit_log.utils import log_action
        from audit_log.models import AuditLog
        log_action(request, AuditLog.ACTION_UPDATE, obj=event,
                   changes={'status': {'من': 'pending', 'إلى': 'cancelled'}})
        messages.success(request, 'تم إلغاء الموعد')
    return redirect('calendar_view')


@login_required
def events_history(request):
    events = Event.objects.filter(
        tenant=request.user.tenant,
        status__in=[Event.STATUS_DONE, Event.STATUS_CANCELLED, Event.STATUS_RESCHEDULED]
    ).select_related('client', 'assigned_to')

    if not request.user.is_admin:
        events = events.filter(assigned_to=request.user)

    status_filter = request.GET.get('status', '')
    source_filter = request.GET.get('source', '')
    date_from     = request.GET.get('date_from', '')
    date_to       = request.GET.get('date_to', '')

    if status_filter:
        events = events.filter(status=status_filter)
    if source_filter:
        events = events.filter(source=source_filter)
    if date_from:
        events = events.filter(start_datetime__date__gte=date_from)
    if date_to:
        events = events.filter(start_datetime__date__lte=date_to)

    events = events.order_by('-start_datetime')

    return render(request, 'calendar_app/history.html', {
        'events': events,
        'status_choices': [
            (Event.STATUS_DONE,        'منجز'),
            (Event.STATUS_CANCELLED,   'ملغي'),
            (Event.STATUS_RESCHEDULED, 'معاد جدولته'),
        ],
        'filters': {
            'status': status_filter,
            'source': source_filter,
            'date_from': date_from,
            'date_to': date_to,
        },
    })
