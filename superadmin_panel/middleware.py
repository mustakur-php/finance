from django.shortcuts import render
from django.urls import resolve, reverse


EXEMPT_URLS = ['superadmin_login', 'superadmin_logout', 'login', 'logout', 'subscription_expired']


class SubscriptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated and not request.user.is_superadmin:
            tenant = getattr(request.user, 'tenant', None)
            if tenant:
                try:
                    url_name = resolve(request.path_info).url_name
                except Exception:
                    url_name = ''
                if url_name not in EXEMPT_URLS:
                    if not tenant.is_active:
                        return render(request, 'superadmin/subscription_expired.html',
                                      {'reason': 'disabled'}, status=403)
                    if tenant.is_expired:
                        return render(request, 'superadmin/subscription_expired.html',
                                      {'reason': 'expired', 'tenant': tenant}, status=403)
        return self.get_response(request)
