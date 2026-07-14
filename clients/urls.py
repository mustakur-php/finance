from django.urls import path
from . import views

urlpatterns = [
    path('', views.clients_list, name='clients_list'),
    path('targeted/', views.targeted_list, name='targeted_list'),
    path('create/', views.client_create, name='client_create'),
    path('<int:pk>/convert/', views.client_convert, name='client_convert'),
    path('targeted/export-template/', views.export_targeted_template, name='export_targeted_template'),
    path('targeted/import/', views.import_targeted_clients, name='import_targeted_clients'),
    path('<int:pk>/', views.client_detail, name='client_detail'),
    path('<int:pk>/edit/', views.client_edit, name='client_edit'),
    path('attachment/<int:pk>/delete/', views.attachment_delete, name='attachment_delete'),
    path('<int:client_pk>/commission/save/', views.commission_rule_save, name='commission_rule_save'),
    path('<int:client_pk>/commission/<str:department>/delete/', views.commission_rule_delete, name='commission_rule_delete'),
    path('<int:pk>/toggle-commission/', views.toggle_commissionable, name='toggle_commissionable'),
    path('<int:pk>/delete/', views.client_delete, name='client_delete'),
    path('activities/', views.activities_list, name='activities_list'),
    path('activities/create/', views.activity_create, name='activity_create'),
    path('activities/<int:pk>/toggle/', views.activity_toggle, name='activity_toggle'),
]
