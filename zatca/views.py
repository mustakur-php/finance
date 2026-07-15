from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import ZatcaClient
from accounts.decorators import admin_required


def _log(request, action, **kwargs):
    from audit_log.utils import log_action
    from audit_log.models import AuditLog
    log_action(request, action, **kwargs)


@login_required
def zatca_list(request):
    if not (request.user.is_admin or request.user.is_accountant):
        return redirect('dashboard')

    qs = ZatcaClient.objects.filter(tenant=request.user.tenant)
    if request.user.is_accountant and not request.user.is_admin:
        qs = qs.filter(assigned_accountant=request.user)

    status_filter = request.GET.get('status', '')
    q = request.GET.get('q', '').strip()
    if status_filter:
        qs = qs.filter(status=status_filter)
    if q:
        from django.db.models import Q
        qs = qs.filter(Q(name__icontains=q) | Q(company__icontains=q))

    paginator = Paginator(qs.select_related('assigned_accountant'), 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'zatca/list.html', {
        'clients': page_obj,
        'page_obj': page_obj,
        'status_filter': status_filter,
        'q': q,
        'status_choices': ZatcaClient.STATUS_CHOICES,
        'total_in_progress': qs.filter(status=ZatcaClient.STATUS_IN_PROGRESS).count(),
        'total_completed': qs.filter(status=ZatcaClient.STATUS_COMPLETED).count(),
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
    return render(request, 'zatca/detail.html', {'client': client})


@login_required
def zatca_complete(request, pk):
    if not (request.user.is_admin or request.user.is_accountant):
        return redirect('dashboard')
    if request.method != 'POST':
        return redirect('zatca_detail', pk=pk)

    client = get_object_or_404(ZatcaClient, pk=pk, tenant=request.user.tenant)
    if request.user.is_accountant and not request.user.is_admin:
        if client.assigned_accountant != request.user:
            messages.error(request, 'ليس لديك صلاحية')
            return redirect('zatca_list')

    report = request.FILES.get('report_file')
    if not report:
        messages.error(request, 'يجب رفع تقرير الإنجاز لإكمال العميل')
        return redirect('zatca_detail', pk=pk)

    from django.utils import timezone
    client.status = ZatcaClient.STATUS_COMPLETED
    client.report_file = report
    client.completed_at = timezone.now()
    client.save()
    from audit_log.models import AuditLog
    _log(request, AuditLog.ACTION_UPDATE, obj=client,
         changes={'الحالة': {'من': 'تحت الإجراء', 'إلى': 'مكتمل'}})
    messages.success(request, f'تم إكمال ملف "{client.name}" بنجاح')
    return redirect('zatca_detail', pk=pk)


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
