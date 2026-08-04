from django.shortcuts import redirect
from django.urls import resolve
from django.utils.deprecation import MiddlewareMixin


class TenantMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated and hasattr(request.user, 'tenant'):
            request.tenant = request.user.tenant
        else:
            request.tenant = None


class DeveloperAccessMiddleware:
    """
    دور 'مطور' محصور في صفحة حلول التطبيقات (+ حسابه الشخصي وتسجيل الخروج) —
    أي صفحة أخرى تعيده إليها، حماية من الخادم وليس إخفاء روابط فقط.
    """
    ALLOWED_URL_NAMES = {'solutions', 'profile', 'login', 'logout', 'home'}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if user is not None and user.is_authenticated and getattr(user, 'is_developer', False):
            if not request.path.startswith(('/static/', '/media/')):
                try:
                    url_name = resolve(request.path_info).url_name
                except Exception:
                    url_name = ''
                if url_name not in self.ALLOWED_URL_NAMES:
                    return redirect('solutions')
        return self.get_response(request)
