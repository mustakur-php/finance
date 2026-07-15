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
    _log(request, 'update', obj=client,
         changes={'الحالة': {'من': 'تحت الإجراء', 'إلى': 'مكتمل'}})
    messages.success(request, f'تم إكمال ملف "{client.name}" بنجاح')
    return redirect('zatca_detail', pk=pk)


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
    return JsonResponse({'status': 'ok', 'is_commissionable': client.is_commissionable})
