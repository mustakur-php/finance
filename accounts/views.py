from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User, Tenant
from django.contrib.auth import update_session_auth_hash
from .forms import LoginForm, UserForm, ProfileForm, ChangePasswordForm
from .decorators import admin_required


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = authenticate(request,
                            username=form.cleaned_data['username'],
                            password=form.cleaned_data['password'])
        if user and user.is_active:
            login(request, user)
            from audit_log.utils import log_action
            from audit_log.models import AuditLog
            log_action(request, AuditLog.ACTION_LOGIN, obj=user)
            return redirect('dashboard')
        messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة')
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    if request.method != 'POST':
        return redirect('login')
    if request.user.is_authenticated:
        from audit_log.utils import log_action
        from audit_log.models import AuditLog
        log_action(request, AuditLog.ACTION_LOGOUT, obj=request.user)
    logout(request)
    return redirect('login')


@login_required
def dashboard_view(request):
    from commissions.models import CommissionEntry
    from calendar_app.models import Event
    from django.db.models import Sum
    from django.utils import timezone
    import datetime
    user = request.user
    context = {'user': user}

    today = timezone.localdate()
    events_qs = Event.objects.filter(tenant=user.tenant, status=Event.STATUS_PENDING, start_datetime__date=today)
    if not user.is_admin:
        events_qs = events_qs.filter(assigned_to=user)
    context['today_events'] = events_qs.order_by('start_datetime')

    if user.is_admin:
        context['total_clients'] = user.tenant.clients.filter(is_active=True).count() if user.tenant else 0
        context['total_users'] = user.tenant.users.filter(is_active=True).count() if user.tenant else 0
        context['total_visits'] = Event.objects.filter(tenant=user.tenant, status=Event.STATUS_DONE).count() if user.tenant else 0

    if user.is_admin:
        agg = CommissionEntry.objects.filter(sheet__tenant=user.tenant).aggregate(
            total_amount=Sum('amount'),
            total_sales=Sum('commission_amount'),
            total_accountant=Sum('accountant_commission_amount'),
            total_review=Sum('review_commission_amount'),
        )
        items = [
            {'label': 'إجمالي المبالغ',    'value': float(agg['total_amount'] or 0),    'color': '#2e7d32', 'bg': '#f0f7f0'},
            {'label': 'عمولات المناديب',    'value': float(agg['total_sales'] or 0),     'color': '#c62828', 'bg': '#fff0f0'},
            {'label': 'عمولات المحاسبين',   'value': float(agg['total_accountant'] or 0),'color': '#1565c0', 'bg': '#f0f4ff'},
            {'label': 'عمولات المراجعين',   'value': float(agg['total_review'] or 0),    'color': '#6a1b9a', 'bg': '#f9f0ff'},
        ]

    elif user.is_accountant:
        context['my_clients'] = user.accountant_clients.filter(is_active=True).count()
        items = []

    elif user.is_sales:
        context['my_clients'] = user.sales_clients.filter(is_active=True).count()
        context['my_visits'] = user.visits.count()
        items = []

    elif user.is_review:
        from workflow.models import ReviewClient
        regular = user.tenant.clients.filter(is_active=True, assigned_review=user).count() if user.tenant else 0
        review = ReviewClient.objects.filter(tenant=user.tenant, assigned_reviewer=user).count() if user.tenant else 0
        context['my_clients'] = regular + review
        items = []

    else:
        items = []

    if items:
        import json
        items_sorted = sorted(items, key=lambda x: x['value'], reverse=True)
        context['chart_items'] = items_sorted
        context['chart_json'] = json.dumps({
            'labels': [i['label'] for i in items_sorted],
            'values': [i['value'] for i in items_sorted],
            'colors': [i['color'] for i in items_sorted],
        })

    return render(request, 'accounts/dashboard.html', context)


@login_required
@admin_required
def users_list(request):
    users = User.objects.filter(tenant=request.user.tenant).order_by('role', 'username')
    return render(request, 'accounts/users_list.html', {'users': users})


@login_required
@admin_required
def user_create(request):
    form = UserForm(request.POST or None, tenant=request.user.tenant)
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        user.tenant = request.user.tenant
        user.set_password(form.cleaned_data['password'])
        user.save()
        from audit_log.utils import log_action
        from audit_log.models import AuditLog
        log_action(request, AuditLog.ACTION_CREATE, obj=user)
        messages.success(request, f'تم إنشاء المستخدم {user.username} بنجاح')
        return redirect('users_list')
    return render(request, 'accounts/user_form.html', {'form': form, 'title': 'إضافة مستخدم'})


@login_required
@admin_required
def user_edit(request, pk):
    user = get_object_or_404(User, pk=pk, tenant=request.user.tenant)
    form = UserForm(request.POST or None, instance=user, tenant=request.user.tenant)
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        if form.cleaned_data.get('password'):
            user.set_password(form.cleaned_data['password'])
        user.save()
        from audit_log.utils import log_action
        from audit_log.models import AuditLog
        log_action(request, AuditLog.ACTION_UPDATE, obj=user)
        messages.success(request, 'تم تحديث المستخدم بنجاح')
        return redirect('users_list')
    return render(request, 'accounts/user_form.html', {'form': form, 'title': 'تعديل مستخدم'})


@login_required
def profile_view(request):
    user = request.user
    profile_form = ProfileForm(instance=user)
    password_form = ChangePasswordForm(user=user)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'profile':
            profile_form = ProfileForm(request.POST, instance=user)
            if profile_form.is_valid():
                profile_form.save()
                from audit_log.utils import log_action
                from audit_log.models import AuditLog
                log_action(request, AuditLog.ACTION_UPDATE, obj=user,
                           changes={'الملف الشخصي': {'من': '', 'إلى': 'تم التحديث'}})
                messages.success(request, 'تم تحديث المعلومات الشخصية بنجاح')
                return redirect('profile')

        elif action == 'password':
            password_form = ChangePasswordForm(request.POST, user=user)
            if password_form.is_valid():
                user.set_password(password_form.cleaned_data['new_password'])
                user.save()
                update_session_auth_hash(request, user)
                from audit_log.utils import log_action
                from audit_log.models import AuditLog
                log_action(request, AuditLog.ACTION_UPDATE, obj=user,
                           changes={'كلمة المرور': {'من': '', 'إلى': 'تم التغيير'}})
                password_form = ChangePasswordForm(user=user)
                return render(request, 'accounts/profile.html', {
                    'profile_form': profile_form,
                    'password_form': password_form,
                    'password_success': True,
                })

        elif action == 'notifications':
            user.telegram_chat_id = request.POST.get('telegram_chat_id', '').strip()
            user.notification_email = request.POST.get('notification_email', '').strip()
            user.save(update_fields=['telegram_chat_id', 'notification_email'])
            messages.success(request, 'تم حفظ إعدادات التنبيهات')
            return redirect('profile')

    return render(request, 'accounts/profile.html', {
        'profile_form': profile_form,
        'password_form': password_form,
    })



@login_required
@admin_required
def user_toggle(request, pk):
    if request.method != 'POST':
        return redirect('users_list')
    user = get_object_or_404(User, pk=pk, tenant=request.user.tenant)
    user.is_active = not user.is_active
    user.save()
    status = 'تفعيل' if user.is_active else 'تعطيل'
    from audit_log.utils import log_action
    from audit_log.models import AuditLog
    log_action(request, AuditLog.ACTION_UPDATE, obj=user,
               changes={'الحالة': {'من': 'معطّل' if user.is_active else 'مفعّل',
                                   'إلى': 'مفعّل' if user.is_active else 'معطّل'}})
    messages.success(request, f'تم {status} المستخدم {user.username}')
    return redirect('users_list')
