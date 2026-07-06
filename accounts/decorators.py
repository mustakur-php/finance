from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_admin:
            messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def sales_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_sales or request.user.is_admin):
            messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def accountant_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_accountant or request.user.is_admin):
            messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def review_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_review or request.user.is_admin):
            messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper
