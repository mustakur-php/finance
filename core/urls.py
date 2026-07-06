from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('login'), name='home'),
    path('', include('accounts.urls')),
    path('clients/', include('clients.urls')),
    path('visits/', include('visits.urls')),
    path('commissions/', include('commissions.urls')),
    path('calendar/', include('calendar_app.urls')),
    path('audit/', include('audit_log.urls')),
    path('workflow/', include('workflow.urls')),
    path('reports/', include('reports.urls')),
    path('mustafa/', include('superadmin_panel.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
