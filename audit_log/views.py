from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from .models import AuditLog
from accounts.decorators import admin_required


@login_required
@admin_required
def audit_log_list(request):
    logs = AuditLog.objects.filter(tenant=request.user.tenant).select_related('user')

    q         = request.GET.get('q', '').strip()
    action    = request.GET.get('action', '')
    model     = request.GET.get('model', '')
    date_from = request.GET.get('date_from', '')
    date_to   = request.GET.get('date_to', '')
    user_id   = request.GET.get('user_id', '')

    if q:
        logs = logs.filter(
            Q(object_repr__icontains=q) |
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q) |
            Q(user__username__icontains=q)
        )
    if action:
        logs = logs.filter(action=action)
    if model:
        logs = logs.filter(model_name=model)
    if date_from:
        logs = logs.filter(timestamp__date__gte=date_from)
    if date_to:
        logs = logs.filter(timestamp__date__lte=date_to)
    if user_id:
        logs = logs.filter(user_id=user_id)

    from accounts.models import User
    users  = User.objects.filter(tenant=request.user.tenant, is_active=True)
    models = AuditLog.objects.filter(tenant=request.user.tenant).values_list('model_name', flat=True).distinct()

    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'audit_log/list.html', {
        'page_obj': page_obj,
        'logs': page_obj,
        'total_count': paginator.count,
        'users': users,
        'models': sorted(set(models)),
        'actions': AuditLog.ACTION_CHOICES,
        'filters': {
            'q': q, 'action': action, 'model': model,
            'date_from': date_from, 'date_to': date_to, 'user_id': user_id,
        },
    })
