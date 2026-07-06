from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import ReviewClient, WorkflowStage
from accounts.decorators import admin_required


def _create_stages(client, start_date, due_dates):
    for i, stage_key in enumerate(WorkflowStage.STAGE_ORDER):
        WorkflowStage.objects.create(
            client     = client,
            stage      = stage_key,
            order      = i,
            status     = WorkflowStage.STATUS_IN_PROGRESS if i == 0 else WorkflowStage.STATUS_PENDING,
            start_date = start_date if i == 0 else None,
            due_date   = due_dates.get(stage_key),
        )


def _complete_stage(stage, approver):
    stage.status      = WorkflowStage.STATUS_COMPLETED
    stage.end_date    = timezone.localdate()
    stage.approved_by = approver
    stage.save()
    next_stage = WorkflowStage.objects.filter(
        client=stage.client,
        order=stage.order + 1,
        status=WorkflowStage.STATUS_PENDING,
    ).first()
    if next_stage:
        next_stage.status     = WorkflowStage.STATUS_IN_PROGRESS
        next_stage.start_date = timezone.localdate()
        next_stage.save()


@login_required
def workflow_list(request):
    clients = ReviewClient.objects.filter(tenant=request.user.tenant).prefetch_related('stages')
    # المراجع يرى العملاء المسندة إليه فقط
    if request.user.is_review and not request.user.is_admin:
        clients = clients.filter(assigned_reviewer=request.user)
    q            = request.GET.get('q', '').strip()
    stage_filter = request.GET.get('stage', '')
    status_filter = request.GET.get('status', '')

    if q:
        from django.db.models import Q
        clients = clients.filter(Q(name__icontains=q) | Q(company__icontains=q))
    if stage_filter:
        clients = clients.filter(stages__stage=stage_filter)
    if status_filter:
        clients = clients.filter(stages__status=status_filter)

    return render(request, 'workflow/list.html', {
        'clients': clients.distinct(),
        'q': q,
        'stage_filter': stage_filter,
        'status_filter': status_filter,
        'stage_choices': WorkflowStage.STAGE_CHOICES,
        'status_choices': WorkflowStage.STATUS_CHOICES,
    })


@login_required
@admin_required
def workflow_client_create(request):
    if request.method == 'POST':
        name       = request.POST.get('name', '').strip()
        company    = request.POST.get('company', '').strip()
        phone      = request.POST.get('phone', '').strip()
        notes      = request.POST.get('notes', '').strip()
        start_date = request.POST.get('start_date') or timezone.localdate()

        if not name:
            messages.error(request, 'اسم العميل مطلوب')
            return redirect('workflow_client_create')

        from accounts.models import User
        reviewer_id = request.POST.get('assigned_reviewer')
        reviewer = User.objects.filter(pk=reviewer_id, tenant=request.user.tenant, role='review').first() if reviewer_id else None

        client = ReviewClient.objects.create(
            tenant             = request.user.tenant,
            name               = name,
            company            = company,
            phone              = request.POST.get('phone', '').strip(),
            email              = request.POST.get('email', '').strip(),
            city               = request.POST.get('city', '').strip(),
            district           = request.POST.get('district', '').strip(),
            address            = request.POST.get('address', '').strip(),
            responsible_person = request.POST.get('responsible_person', '').strip(),
            job_title          = request.POST.get('job_title', '').strip(),
            activity           = request.POST.get('activity', '').strip(),
            notes              = notes,
            assigned_reviewer  = reviewer,
            created_by         = request.user,
        )

        due_dates = {
            WorkflowStage.STAGE_CONTRACT: request.POST.get('due_contract') or None,
            WorkflowStage.STAGE_REVIEW:   request.POST.get('due_review')   or None,
            WorkflowStage.STAGE_LETTERS:  request.POST.get('due_letters')  or None,
            WorkflowStage.STAGE_SUBMIT:   request.POST.get('due_submit')   or None,
        }
        _create_stages(client, start_date, due_dates)

        from audit_log.utils import log_action
        from audit_log.models import AuditLog
        log_action(request, AuditLog.ACTION_CREATE, obj=client)

        messages.success(request, f'تم إضافة العميل "{name}" وإنشاء مراحل سير العمل')
        return redirect('workflow_detail', pk=client.pk)

    from clients.forms import SAUDI_CITIES
    from accounts.models import User
    reviewers = User.objects.filter(tenant=request.user.tenant, role='review', is_active=True)
    return render(request, 'workflow/client_form.html', {
        'stage_choices': WorkflowStage.STAGE_CHOICES,
        'cities': SAUDI_CITIES,
        'reviewers': reviewers,
    })


@login_required
def workflow_detail(request, pk):
    client = get_object_or_404(ReviewClient, pk=pk, tenant=request.user.tenant)
    if request.user.is_review and not request.user.is_admin and client.assigned_reviewer != request.user:
        messages.error(request, 'ليس لديك صلاحية عرض هذا العميل')
        return redirect('workflow_list')
    stages = client.stages.all()
    return render(request, 'workflow/detail.html', {
        'client': client,
        'stages': stages,
    })


@login_required
def stage_update(request, stage_pk):
    stage = get_object_or_404(WorkflowStage, pk=stage_pk, client__tenant=request.user.tenant)

    if stage.status == WorkflowStage.STATUS_PENDING:
        messages.error(request, 'لا يمكن تحديث مرحلة لم تبدأ بعد')
        return redirect('workflow_detail', pk=stage.client.pk)

    if request.method == 'POST':
        stage.notes      = request.POST.get('notes', stage.notes)
        stage.updated_by = request.user
        action           = request.POST.get('action')

        if action == 'complete':
            if request.user.is_admin:
                _complete_stage(stage, request.user)
                messages.success(request, 'تم إكمال المرحلة والانتقال للتالية')
            else:
                stage.status = WorkflowStage.STATUS_WAITING
                stage.save()
                messages.success(request, 'تم إرسال المرحلة للاعتماد')

        elif action == 'approve' and request.user.is_admin:
            _complete_stage(stage, request.user)
            messages.success(request, 'تم اعتماد المرحلة والانتقال للتالية')

        elif action == 'reject' and request.user.is_admin:
            stage.status = WorkflowStage.STATUS_IN_PROGRESS
            stage.save()
            messages.warning(request, 'تم رفض الاعتماد وإرجاع المرحلة')

        else:
            stage.save()
            messages.success(request, 'تم حفظ الملاحظات')

    return redirect('workflow_detail', pk=stage.client.pk)


@login_required
@admin_required
def stage_set_due(request, stage_pk):
    stage = get_object_or_404(WorkflowStage, pk=stage_pk, client__tenant=request.user.tenant)
    if request.method == 'POST':
        stage.due_date = request.POST.get('due_date') or None
        stage.save(update_fields=['due_date'])
        messages.success(request, 'تم تحديث تاريخ الاستحقاق')
    return redirect('workflow_detail', pk=stage.client.pk)


@login_required
def workflow_report(request):
    clients = ReviewClient.objects.filter(tenant=request.user.tenant).prefetch_related('stages')
    return render(request, 'workflow/report.html', {
        'clients': clients,
        'stage_choices': WorkflowStage.STAGE_CHOICES,
        'today': timezone.localdate(),
    })
