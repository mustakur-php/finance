from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import OneTimeServiceClient, OneTimeService
from accounts.decorators import admin_required
from core.uploads import validate_upload


def _log(request, action, **kwargs):
    from audit_log.utils import log_action
    from audit_log.models import AuditLog
    log_action(request, action, **kwargs)


def _can_access(user, client):
    """الأدمن يصل للجميع. غيره يصل فقط لعميل أُسندت له إحدى خدماته."""
    if user.is_admin:
        return True
    return client.services.filter(assigned_to=user).exists()


@login_required
def onetime_list(request):
    from django.db.models import Q
    user = request.user
    if user.is_admin:
        qs = OneTimeServiceClient.objects.filter(tenant=user.tenant)
    else:
        qs = OneTimeServiceClient.objects.filter(tenant=user.tenant, services__assigned_to=user).distinct()

    status_filter = request.GET.get('status', '')
    q = request.GET.get('q', '').strip()
    if status_filter == 'active':
        qs = qs.filter(is_active=True)
    elif status_filter == 'inactive':
        qs = qs.filter(is_active=False)
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(company__icontains=q))

    total_active = qs.filter(is_active=True).count()
    total_inactive = qs.filter(is_active=False).count()

    paginator = Paginator(qs.order_by('-created_at'), 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'onetime_services/list.html', {
        'clients': page_obj,
        'page_obj': page_obj,
        'status_filter': status_filter,
        'q': q,
        'total_active': total_active,
        'total_inactive': total_inactive,
    })


@login_required
def onetime_detail(request, pk):
    client = get_object_or_404(OneTimeServiceClient, pk=pk, tenant=request.user.tenant)
    if not _can_access(request.user, client):
        messages.error(request, 'ليس لديك صلاحية عرض هذا العميل')
        return redirect('onetime_list')

    services = client.services.select_related('assigned_to')
    current = services.filter(status=OneTimeService.STATUS_IN_PROGRESS).first()

    from accounts.models import User as UserModel
    executors = UserModel.objects.filter(tenant=request.user.tenant, is_active=True).order_by('first_name', 'username')

    return render(request, 'onetime_services/detail.html', {
        'client': client,
        'services': services,
        'current': current,
        'executors': executors,
    })


@login_required
def onetime_edit(request, pk):
    client = get_object_or_404(OneTimeServiceClient, pk=pk, tenant=request.user.tenant)
    if not _can_access(request.user, client):
        messages.error(request, 'ليس لديك صلاحية تعديل هذا العميل')
        return redirect('onetime_list')
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
        client.save()
        from audit_log.utils import log_action
        from audit_log.models import AuditLog
        log_action(request, AuditLog.ACTION_UPDATE, obj=client)
        messages.success(request, 'تم تحديث بيانات العميل بنجاح')
        return redirect('onetime_detail', pk=pk)
    return render(request, 'onetime_services/client_edit.html', {'client': client})


@login_required
@admin_required
def onetime_delete(request, pk):
    if request.method != 'POST':
        return redirect('onetime_list')
    client = get_object_or_404(OneTimeServiceClient, pk=pk, tenant=request.user.tenant)
    name = client.name
    from audit_log.models import AuditLog
    _log(request, AuditLog.ACTION_DELETE, model_name='OneTimeServiceClient',
         object_repr=name, object_id=str(pk))
    client.delete()
    messages.success(request, f'تم حذف العميل "{name}"')
    return redirect('onetime_list')


@login_required
@admin_required
def onetime_toggle_commissionable(request, pk):
    from django.http import JsonResponse, HttpResponseNotAllowed
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    client = get_object_or_404(OneTimeServiceClient, pk=pk, tenant=request.user.tenant)
    client.is_commissionable = not client.is_commissionable
    client.save(update_fields=['is_commissionable'])
    from audit_log.models import AuditLog
    _log(request, AuditLog.ACTION_UPDATE, obj=client,
         changes={'العمولة': {'من': 'غير خاضع' if client.is_commissionable else 'خاضع',
                              'إلى': 'خاضع' if client.is_commissionable else 'غير خاضع'}})
    return JsonResponse({'status': 'ok', 'is_commissionable': client.is_commissionable})


@login_required
@admin_required
def onetime_service_create(request, pk):
    """
    فتح خدمة جديدة — يتطلب نوع الخدمة (نص حر). متاح فقط عندما لا توجد خدمة
    نشطة حالياً؛ يعيد تنشيط العميل تلقائياً.
    """
    client = get_object_or_404(OneTimeServiceClient, pk=pk, tenant=request.user.tenant)
    if request.method != 'POST':
        return redirect('onetime_detail', pk=pk)

    if client.services.filter(status=OneTimeService.STATUS_IN_PROGRESS).exists():
        messages.error(request, 'يوجد خدمة تحت الإجراء بالفعل لهذا العميل')
        return redirect('onetime_detail', pk=pk)

    service_type = request.POST.get('service_type', '').strip()
    if not service_type:
        messages.error(request, 'يجب تحديد نوع الخدمة')
        return redirect('onetime_detail', pk=pk)

    start_date = request.POST.get('start_date', '').strip()
    if not start_date:
        messages.error(request, 'يجب تحديد تاريخ الفتح')
        return redirect('onetime_detail', pk=pk)

    assigned_id = request.POST.get('assigned_to')
    assigned_to = None
    if assigned_id:
        from accounts.models import User as UserModel
        assigned_to = UserModel.objects.filter(pk=assigned_id, tenant=request.user.tenant, is_active=True).first()

    service = OneTimeService.objects.create(
        client=client,
        service_type=service_type,
        assigned_to=assigned_to,
        start_date=start_date,
        created_by=request.user,
    )
    client.is_active = True
    client.save(update_fields=['is_active'])

    from audit_log.utils import log_action
    from audit_log.models import AuditLog
    log_action(request, AuditLog.ACTION_CREATE, obj=service)
    messages.success(request, 'تم فتح الخدمة بنجاح')
    return redirect('onetime_detail', pk=pk)


@login_required
def onetime_service_complete(request, service_pk):
    """إكمال الخدمة — التقرير اختياري. تُنهي الخدمة وتجعل العميل غير نشط."""
    if request.method != 'POST':
        return redirect('onetime_list')

    service = get_object_or_404(OneTimeService, pk=service_pk)
    client = service.client
    if client.tenant != request.user.tenant or not _can_access(request.user, client):
        return redirect('onetime_list')

    report = request.FILES.get('report_file')
    if report:
        ok, err = validate_upload(report)
        if not ok:
            messages.error(request, err)
            return redirect('onetime_detail', pk=client.pk)
        service.report_file = report

    from django.utils import timezone
    service.status = OneTimeService.STATUS_COMPLETED
    service.completed_at = timezone.now()
    service.save()

    client.is_active = False
    client.save(update_fields=['is_active'])

    from audit_log.utils import log_action
    from audit_log.models import AuditLog
    log_action(request, AuditLog.ACTION_UPDATE, obj=service,
               changes={'الحالة': {'من': 'تحت الإجراء', 'إلى': 'مكتملة'}})
    messages.success(request, 'تم إكمال الخدمة بنجاح — أصبح العميل غير نشط')
    return redirect('onetime_detail', pk=client.pk)


@login_required
@admin_required
def onetime_service_assign(request, service_pk):
    """تغيير المنفّذ لخدمة قائمة."""
    if request.method != 'POST':
        return redirect('onetime_list')
    service = get_object_or_404(OneTimeService, pk=service_pk)
    client = service.client
    if client.tenant != request.user.tenant:
        return redirect('onetime_list')

    from accounts.models import User as UserModel
    old = service.assigned_to
    assigned_id = request.POST.get('assigned_to') or ''
    if assigned_id:
        service.assigned_to = UserModel.objects.filter(
            pk=assigned_id, tenant=request.user.tenant, is_active=True
        ).first()
    else:
        service.assigned_to = None
    service.save(update_fields=['assigned_to'])

    def _name(u):
        return (u.get_full_name() or u.username) if u else '—'

    from audit_log.models import AuditLog
    _log(request, AuditLog.ACTION_UPDATE, obj=service,
         changes={'المنفّذ': {'من': _name(old), 'إلى': _name(service.assigned_to)}})
    messages.success(request, 'تم تحديث المنفّذ بنجاح')
    return redirect('onetime_detail', pk=client.pk)


@login_required
@admin_required
def onetime_service_delete(request, service_pk):
    if request.method != 'POST':
        return redirect('onetime_list')
    service = get_object_or_404(OneTimeService, pk=service_pk)
    client = service.client
    if client.tenant != request.user.tenant:
        return redirect('onetime_list')

    if service.status == OneTimeService.STATUS_COMPLETED:
        messages.error(request, 'لا يمكن حذف خدمة مكتملة. استخدم "استبدال التقرير" إن كان الرفع بالخطأ.')
        return redirect('onetime_detail', pk=client.pk)

    confirmed_entry = service.commission_entries.filter(is_confirmed=True).exists()
    if confirmed_entry:
        messages.warning(request, 'تنبيه: كانت هذه الخدمة مرتبطة بعمولة مؤكَّدة في شيت عمولات.')

    from audit_log.utils import log_action
    from audit_log.models import AuditLog
    log_action(request, AuditLog.ACTION_DELETE, model_name='OneTimeService',
               object_repr=str(service), object_id=str(service_pk))
    if service.report_file:
        service.report_file.delete(save=False)
    service.delete()

    # لا يوجد خدمة نشطة أخرى بالضرورة -> العميل يرجع غير نشط إن لم توجد خدمة تحت الإجراء
    if not client.services.filter(status=OneTimeService.STATUS_IN_PROGRESS).exists():
        client.is_active = False
        client.save(update_fields=['is_active'])

    messages.success(request, 'تم حذف الخدمة')
    return redirect('onetime_detail', pk=client.pk)


@login_required
@admin_required
def onetime_service_replace_report(request, service_pk):
    """استبدال تقرير خدمة (حتى لو مكتملة) — للأدمن فقط."""
    if request.method != 'POST':
        return redirect('onetime_list')
    service = get_object_or_404(OneTimeService, pk=service_pk)
    client = service.client
    if client.tenant != request.user.tenant:
        return redirect('onetime_list')

    report = request.FILES.get('report_file')
    if not report:
        messages.error(request, 'اختر ملفاً جديداً لاستبدال التقرير')
        return redirect('onetime_detail', pk=client.pk)
    ok, err = validate_upload(report)
    if not ok:
        messages.error(request, err)
        return redirect('onetime_detail', pk=client.pk)

    old_name = service.report_file.name if service.report_file else '—'
    if service.report_file:
        service.report_file.delete(save=False)
    service.report_file = report
    service.save(update_fields=['report_file'])

    from audit_log.models import AuditLog
    _log(request, AuditLog.ACTION_UPDATE, obj=service,
         changes={'تقرير الخدمة': {'من': old_name, 'إلى': report.name}})
    messages.success(request, 'تم استبدال التقرير بنجاح')
    return redirect('onetime_detail', pk=client.pk)
