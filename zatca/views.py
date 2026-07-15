from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import ZatcaClient, ZatcaSession
from accounts.decorators import admin_required
from core.uploads import validate_upload


def _log(request, action, **kwargs):
    from audit_log.utils import log_action
    from audit_log.models import AuditLog
    log_action(request, action, **kwargs)


def _can_access_zatca(user, client):
    """المحاسب يتصرف فقط بعملائه المسندين؛ الأدمن بالجميع."""
    if user.is_admin:
        return True
    return user.is_accountant and client.assigned_accountant_id == user.id


@login_required
def zatca_list(request):
    if not (request.user.is_admin or request.user.is_accountant):
        return redirect('dashboard')

    from django.db.models import Exists, OuterRef, Q
    qs = ZatcaClient.objects.filter(tenant=request.user.tenant)
    if request.user.is_accountant and not request.user.is_admin:
        qs = qs.filter(assigned_accountant=request.user)

    active_subq = ZatcaSession.objects.filter(
        client=OuterRef('pk'), status=ZatcaSession.STATUS_IN_PROGRESS
    )
    any_subq = ZatcaSession.objects.filter(client=OuterRef('pk'))
    qs = qs.annotate(
        has_active_session=Exists(active_subq),
        has_any_session=Exists(any_subq),
    )

    status_filter = request.GET.get('status', '')
    q = request.GET.get('q', '').strip()
    if status_filter == 'active':
        qs = qs.filter(has_active_session=True)
    elif status_filter == 'idle':
        qs = qs.filter(has_active_session=False, has_any_session=True)
    elif status_filter == 'new':
        qs = qs.filter(has_any_session=False)
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(company__icontains=q))

    total_active = qs.filter(has_active_session=True).count()
    total_idle   = qs.filter(has_active_session=False, has_any_session=True).count()
    total_new    = qs.filter(has_any_session=False).count()

    paginator = Paginator(qs.select_related('assigned_accountant'), 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'zatca/list.html', {
        'clients': page_obj,
        'page_obj': page_obj,
        'status_filter': status_filter,
        'q': q,
        'total_active': total_active,
        'total_idle': total_idle,
        'total_new': total_new,
    })


@login_required
def zatca_detail(request, pk):
    if not (request.user.is_admin or request.user.is_accountant):
        return redirect('dashboard')

    client = get_object_or_404(ZatcaClient, pk=pk, tenant=request.user.tenant)
    if request.user.is_accountant and not request.user.is_admin:
        if client.assigned_accountant != request.user:
            messages.error(request, 'ليس لديك صلاحية عرض هذا العميل')
            return redirect('zatca_list')
    sessions = client.sessions.all()
    active_session = sessions.filter(status=ZatcaSession.STATUS_IN_PROGRESS).first()
    next_start = client.next_session_start()
    return render(request, 'zatca/detail.html', {
        'client': client,
        'sessions': sessions,
        'active_session': active_session,
        'next_start': next_start,
    })


@login_required
def zatca_edit(request, pk):
    if not (request.user.is_admin or request.user.is_accountant):
        return redirect('dashboard')
    client = get_object_or_404(ZatcaClient, pk=pk, tenant=request.user.tenant)
    if request.user.is_accountant and not request.user.is_admin:
        if client.assigned_accountant != request.user:
            messages.error(request, 'ليس لديك صلاحية تعديل هذا العميل')
            return redirect('zatca_list')
    if request.method == 'POST':
        client.name               = request.POST.get('name', '').strip() or client.name
        client.company            = request.POST.get('company', '').strip()
        client.phone              = request.POST.get('phone', '').strip()
        client.email              = request.POST.get('email', '').strip()
        client.city               = request.POST.get('city', '').strip()
        client.district           = request.POST.get('district', '').strip()
        client.address            = request.POST.get('address', '').strip()
        client.responsible_person = request.POST.get('responsible_person', '').strip()
        client.job_title          = request.POST.get('job_title', '').strip()
        client.notes              = request.POST.get('notes', '').strip()
        client.distinguished_number = request.POST.get('distinguished_number', '').strip()
        client.secret_number      = request.POST.get('secret_number', '').strip()
        if request.user.is_admin:
            period = request.POST.get('period_months', '')
            if period in ('1', '3', '6', '12'):
                client.period_months = int(period)
        client.save()
        from audit_log.utils import log_action
        from audit_log.models import AuditLog
        log_action(request, AuditLog.ACTION_UPDATE, obj=client)
        messages.success(request, 'تم تحديث بيانات العميل بنجاح')
        return redirect('zatca_detail', pk=pk)
    return render(request, 'zatca/client_edit.html', {'client': client})


@login_required
@admin_required
def zatca_delete(request, pk):
    if request.method != 'POST':
        return redirect('zatca_list')
    client = get_object_or_404(ZatcaClient, pk=pk, tenant=request.user.tenant)
    name = client.name
    from audit_log.models import AuditLog
    _log(request, AuditLog.ACTION_DELETE, model_name='ZatcaClient',
         object_repr=name, object_id=str(pk))
    client.delete()
    messages.success(request, f'تم حذف العميل "{name}"')
    return redirect('zatca_list')


@login_required
@admin_required
def zatca_toggle_commissionable(request, pk):
    from django.http import JsonResponse, HttpResponseNotAllowed
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    client = get_object_or_404(ZatcaClient, pk=pk, tenant=request.user.tenant)
    client.is_commissionable = not client.is_commissionable
    client.save(update_fields=['is_commissionable'])
    from audit_log.models import AuditLog
    _log(request, AuditLog.ACTION_UPDATE, obj=client,
         changes={'العمولة': {'من': 'غير خاضع' if client.is_commissionable else 'خاضع',
                              'إلى': 'خاضع' if client.is_commissionable else 'غير خاضع'}})
    return JsonResponse({'status': 'ok', 'is_commissionable': client.is_commissionable})


@login_required
def zatca_session_create(request, pk):
    if not (request.user.is_admin or request.user.is_accountant):
        return redirect('dashboard')
    client = get_object_or_404(ZatcaClient, pk=pk, tenant=request.user.tenant)
    if not _can_access_zatca(request.user, client):
        messages.error(request, 'ليس لديك صلاحية على هذا العميل')
        return redirect('zatca_list')
    if request.method != 'POST':
        return redirect('zatca_detail', pk=pk)

    start_date = request.POST.get('start_date', '').strip()
    if not start_date:
        messages.error(request, 'يجب تحديد تاريخ البداية')
        return redirect('zatca_detail', pk=pk)

    session = ZatcaSession.objects.create(
        client=client,
        start_date=start_date,
        created_by=request.user,
    )
    from audit_log.utils import log_action
    from audit_log.models import AuditLog
    log_action(request, AuditLog.ACTION_CREATE, obj=session)
    messages.success(request, 'تم فتح دورة جديدة بنجاح')
    return redirect('zatca_detail', pk=pk)


@login_required
def zatca_session_complete(request, session_pk):
    if not (request.user.is_admin or request.user.is_accountant):
        return redirect('dashboard')
    if request.method != 'POST':
        return redirect('zatca_list')

    session = get_object_or_404(ZatcaSession, pk=session_pk)
    client = session.client
    if client.tenant != request.user.tenant or not _can_access_zatca(request.user, client):
        return redirect('zatca_list')

    report = request.FILES.get('report_file')
    if not report:
        messages.error(request, 'يجب رفع تقرير الدورة لإكمالها')
        return redirect('zatca_detail', pk=client.pk)
    ok, err = validate_upload(report)
    if not ok:
        messages.error(request, err)
        return redirect('zatca_detail', pk=client.pk)

    from django.utils import timezone
    session.status = ZatcaSession.STATUS_COMPLETED
    session.report_file = report
    session.completed_at = timezone.now()
    session.end_date = timezone.localdate()
    session.save()

    from audit_log.utils import log_action
    from audit_log.models import AuditLog
    log_action(request, AuditLog.ACTION_UPDATE, obj=session,
               changes={'الحالة': {'من': 'تحت الإجراء', 'إلى': 'مكتملة'}})

    # عمولة الدورة تُسحب تلقائياً عند إنشاء/تحديث شيت العمولات إذا كان العميل خاضعاً للعمولة
    messages.success(request, 'تم إكمال الدورة بنجاح')
    return redirect('zatca_detail', pk=client.pk)


@login_required
@admin_required
def zatca_session_delete(request, session_pk):
    if request.method != 'POST':
        return redirect('zatca_list')
    session = get_object_or_404(ZatcaSession, pk=session_pk)
    client = session.client
    if client.tenant != request.user.tenant:
        return redirect('zatca_list')
    from audit_log.utils import log_action
    from audit_log.models import AuditLog
    log_action(request, AuditLog.ACTION_DELETE, model_name='ZatcaSession',
               object_repr=str(session), object_id=str(session_pk))
    session.delete()
    messages.success(request, 'تم حذف الدورة')
    return redirect('zatca_detail', pk=client.pk)
