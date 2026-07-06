from django.urls import path
from . import views

urlpatterns = [
    path('login/',              views.superadmin_login,     name='superadmin_login'),
    path('logout/',             views.superadmin_logout,    name='superadmin_logout'),
    path('',                    views.superadmin_dashboard, name='superadmin_dashboard'),
    path('tenants/create/',     views.tenant_create,        name='tenant_create'),
    path('tenants/<int:pk>/',   views.tenant_detail,        name='tenant_detail'),
    path('tenants/<int:pk>/edit/',   views.tenant_edit,     name='tenant_edit'),
    path('tenants/<int:pk>/toggle/', views.tenant_toggle,   name='tenant_toggle'),
    path('tenants/<int:pk>/extend/', views.tenant_extend,   name='tenant_extend'),
    path('reports/',                 views.superadmin_reports,         name='superadmin_reports'),
    path('reports/clients/',         views.superadmin_report_clients,  name='superadmin_report_clients'),
]
