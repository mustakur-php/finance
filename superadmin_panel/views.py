from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from django.utils.text import slugify
from django.db.models import Count, Sum, Q
from accounts.models import Tenant, User
import datetime


def superadmin_required(view_func):
    from functools import wraps
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superadmin:
            return redirect('superadmin_login')
        return view_func(request, *args, **kwargs)
    return wrapper


def superadmin_login(request):
    if request.user.is_authenticated and request.user.is_superadmin:
        return redirect('superadmin_dashboard')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user and user.is_superadmin:
            login(request, user)
            return redirect('superadmin_dashboard')
        messages.error(request, 'بيانات الدخول غير صحيحة')
    return render(request, 'superadmin/login.html')


def superadmin_logout(request):
    if request.method == 'POST':
        logout(request)
    return redirect('superadmin_login')


@superadmin_required
def superadmin_dashboard(request):
    tenants = Tenant.objects.annotate(user_count=Count('users'))
    ctx = {
        'total_tenants':  tenants.count(),
        'active_tenants': tenants.filter(is_active=True).count(),
        'expired_tenants': [t for t in tenants if t.is_expired and t.is_active],
        'expiring_soon':  [t for t in tenants if t.days_remaining is not None and 0 <= t.days_remaining <= 7 and not t.is_expired],
        'tenants':        tenants.order_by('-created_at'),
    }
    return render(request, 'superadmin/dashboard.html', ctx)


@superadmin_required
def tenant_create(request):
    if request.method == 'POST':
        name     = request.POST.get('name', '').strip()
        phone    = request.POST.get('phone', '').strip()
        email    = request.POST.get('email', '').strip()
        address  = request.POST.get('address', '').strip()
        contact  = request.POST.get('contact_person', '').strip()
        plan     = request.POST.get('subscription_plan', Tenant.PLAN_MONTHLY)
        sub_start = request.POST.get('subscription_start') or timezone.localdate()
        sub_end   = request.POST.get('subscription_end') or None
        max_users = int(request.POST.get('max_users') or 10)
        admin_username = request.POST.get('admin_username', '').strip()
        admin_password = request.POST.get('admin_password', '').strip()
        admin_name     = request.POST.get('admin_fullname', '').strip()
        admin_email    = request.POST.get('admin_email', '').strip()

        if not name or not admin_username or not admin_password:
            messages.error(request, 'اسم الشركة واسم المستخدم وكلمة المرور مطلوبة')
            return render(request, 'superadmin/tenant_form.html', {'plan_choices': Tenant.PLAN_CHOICES})

        if User.objects.filter(username=admin_username).exists():
            messages.error(request, 'اسم المستخدم موجود مسبقاً')
            return render(request, 'superadmin/tenant_form.html', {'plan_choices': Tenant.PLAN_CHOICES})

        base_slug = slugify(name, allow_unicode=False) or 'tenant'
        slug, counter = base_slug, 1
        while Tenant.objects.filter(slug=slug).exists():
            slug = f'{base_slug}-{counter}'
            counter += 1

        tenant = Tenant.objects.create(
            name=name, slug=slug, phone=phone, email=email,
            address=address, contact_person=contact,
            subscription_plan=plan, subscription_start=sub_start,
            subscription_end=sub_end, max_users=max_users,
        )
        parts = admin_name.split(' ', 1)
        User.objects.create_user(
            username=admin_username, password=admin_password,
            first_name=parts[0], last_name=parts[1] if len(parts) > 1 else '',
            email=admin_email, tenant=tenant, role=User.ROLE_ADMIN,
        )
        messages.success(request, f'تم إنشاء شركة "{name}" بنجاح مع حساب الأدمن')
        return redirect('superadmin_dashboard')

    return render(request, 'superadmin/tenant_form.html', {
        'plan_choices': Tenant.PLAN_CHOICES, 'today': timezone.localdate(),
    })


@superadmin_required
def tenant_detail(request, pk):
    tenant = get_object_or_404(Tenant, pk=pk)
    users  = tenant.users.all()
    return render(request, 'superadmin/tenant_detail.html', {
        'tenant': tenant, 'users': users, 'plan_choices': Tenant.PLAN_CHOICES,
    })


@superadmin_required
def tenant_edit(request, pk):
    tenant = get_object_or_404(Tenant, pk=pk)
    if request.method == 'POST':
        tenant.name           = request.POST.get('name', tenant.name).strip()
        tenant.phone          = request.POST.get('phone', '').strip()
        tenant.email          = request.POST.get('email', '').strip()
        tenant.address        = request.POST.get('address', '').strip()
        tenant.contact_person = request.POST.get('contact_person', '').strip()
        tenant.subscription_plan  = request.POST.get('subscription_plan', tenant.subscription_plan)
        tenant.subscription_start = request.POST.get('subscription_start') or tenant.subscription_start
        tenant.subscription_end   = request.POST.get('subscription_end') or None
        tenant.max_users  = int(request.POST.get('max_users') or tenant.max_users)
        tenant.is_active  = request.POST.get('is_active') == 'on'
        tenant.save()
        messages.success(request, 'تم تحديث بيانات الشركة')
        return redirect('tenant_detail', pk=pk)
    return render(request, 'superadmin/tenant_form.html', {
        'tenant': tenant, 'plan_choices': Tenant.PLAN_CHOICES, 'edit': True,
        'today': timezone.localdate(),
    })


@superadmin_required
def tenant_toggle(request, pk):
    if request.method != 'POST':
        return redirect('superadmin_dashboard')
    tenant = get_object_or_404(Tenant, pk=pk)
    tenant.is_active = not tenant.is_active
    tenant.save()
    messages.success(request, f'تم {"تفعيل" if tenant.is_active else "تعطيل"} شركة "{tenant.name}"')
    return redirect('superadmin_dashboard')


@superadmin_required
def superadmin_reports(request):
    from clients.models import Client
    from commissions.models import CommissionEntry
    from calendar_app.models import Event
    from workflow.models import ReviewClient, WorkflowStage
    from zatca.models import ZatcaClient, ZatcaSession

    tenants     = Tenant.objects.filter(is_active=True).order_by('name')
    tenant_id   = request.GET.get('tenant', '')
    selected    = None
    today       = timezone.localdate()

    if tenant_id:
        selected = get_object_or_404(Tenant, pk=tenant_id)
        t_filter = Q(tenant=selected)
        e_filter = Q(sheet__tenant=selected)
        z_filter = Q(client__tenant=selected)
    else:
        t_filter = Q(tenant__in=tenants)
        e_filter = Q(sheet__tenant__in=tenants)
        z_filter = Q(client__tenant__in=tenants)

    ctx = {
        'tenants':          tenants,
        'selected':         selected,
        'today':            today,
        'total_clients':    Client.objects.filter(t_filter, is_active=True, client_type='actual').count(),
        'total_targeted':   Client.objects.filter(t_filter, is_active=True, client_type='potential').count(),
        'total_zatca':      ZatcaClient.objects.filter(t_filter).count(),
        'zatca_active':     ZatcaSession.objects.filter(z_filter, status=ZatcaSession.STATUS_IN_PROGRESS).count(),
        'zatca_completed':  ZatcaSession.objects.filter(z_filter, status=ZatcaSession.STATUS_COMPLETED).count(),
        'total_amount':     CommissionEntry.objects.filter(e_filter).aggregate(s=Sum('amount'))['s'] or 0,
        'total_commission': CommissionEntry.objects.filter(e_filter).aggregate(s=Sum('commission_amount'))['s'] or 0,
        'total_accountant': CommissionEntry.objects.filter(e_filter).aggregate(s=Sum('accountant_commission_amount'))['s'] or 0,
        'total_review_comm':CommissionEntry.objects.filter(e_filter).aggregate(s=Sum('review_commission_amount'))['s'] or 0,
        'events_done':      Event.objects.filter(t_filter, status='done').count(),
        'events_cancelled': Event.objects.filter(t_filter, status='cancelled').count(),
        'events_pending':   Event.objects.filter(t_filter, status='pending').count(),
        'workflow_clients': ReviewClient.objects.filter(t_filter).count(),
        'workflow_overdue': WorkflowStage.objects.filter(
            Q(client__tenant=selected) if selected else Q(client__tenant__in=tenants),
            due_date__lt=today,
            status__in=['in_progress', 'waiting_approval']
        ).count(),
    }
    return render(request, 'superadmin/reports.html', ctx)


@superadmin_required
def superadmin_report_clients(request):
    from clients.models import Client
    from accounts.models import User

    tenants    = Tenant.objects.filter(is_active=True).order_by('name')
    tenant_id  = request.GET.get('tenant', '')
    date_from  = request.GET.get('date_from', '')
    date_to    = request.GET.get('date_to', '')
    city_f     = request.GET.get('city', '')
    type_f     = request.GET.get('type', 'actual')
    selected   = None

    qs = Client.objects.filter(tenant__in=tenants, is_active=True, client_type=type_f)

    if tenant_id:
        selected = get_object_or_404(Tenant, pk=tenant_id)
        qs = qs.filter(tenant=selected)

    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)
    if city_f:
        qs = qs.filter(city=city_f)

    qs = qs.select_related('tenant', 'assigned_sales', 'assigned_accountant', 'activity')

    by_city     = qs.values('city').annotate(count=Count('id')).order_by('-count')
    by_activity = qs.values('activity__name').annotate(count=Count('id')).order_by('-count')
    by_sales    = qs.values('assigned_sales__first_name', 'assigned_sales__last_name').annotate(count=Count('id')).order_by('-count')
    cities      = Client.objects.filter(tenant__in=tenants, is_active=True).exclude(city='').values_list('city', flat=True).distinct()

    return render(request, 'superadmin/report_clients.html', {
        'clients':  qs,
        'total':    qs.count(),
        'tenants':  tenants,
        'selected': selected,
        'by_city':      by_city,
        'by_activity':  by_activity,
        'by_sales':     by_sales,
        'cities':       cities,
        'filters': {
            'date_from': date_from, 'date_to': date_to,
            'city': city_f, 'type': type_f,
        },
    })


@superadmin_required
def tenant_extend(request, pk):
    if request.method != 'POST':
        return redirect('tenant_detail', pk=pk)
    tenant = get_object_or_404(Tenant, pk=pk)
    sub_end = request.POST.get('subscription_end')
    if sub_end:
        tenant.subscription_end = sub_end
    tenant.subscription_plan = request.POST.get('subscription_plan', tenant.subscription_plan)
    tenant.max_users = int(request.POST.get('max_users') or tenant.max_users)
    tenant.is_active = True
    tenant.save()
    messages.success(request, f'تم تمديد الاشتراك حتى {tenant.subscription_end}')
    return redirect('tenant_detail', pk=pk)
