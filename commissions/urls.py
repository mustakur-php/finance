from django.urls import path
from . import views

urlpatterns = [
    path('', views.commissions_list, name='commissions_list'),
    path('create/', views.commission_create, name='commission_create'),
    path('<int:pk>/', views.commission_detail, name='commission_detail'),
    path('<int:pk>/save-entries/', views.commission_save_entries, name='commission_save_entries'),
    path('entry/<int:pk>/toggle/', views.commission_toggle, name='commission_toggle'),
    path('entry/<int:pk>/delete/', views.commission_delete_entry, name='commission_delete_entry'),
    path('<int:pk>/delete/', views.commission_delete_sheet, name='commission_delete_sheet'),
    path('<int:pk>/refresh/', views.commission_refresh_sheet, name='commission_refresh_sheet'),
    path('entry/<int:entry_pk>/amount/save/', views.entry_amount_save, name='entry_amount_save'),
    path('entry/<int:entry_pk>/commission/save/', views.entry_commission_save, name='entry_commission_save'),
    path('entry/<int:entry_pk>/commission/<str:department>/delete/', views.entry_commission_delete, name='entry_commission_delete'),
    path('<int:pk>/export/excel/', views.export_sheet_excel, name='export_sheet_excel'),
    path('<int:pk>/export/pdf/', views.export_sheet_pdf, name='export_sheet_pdf'),
]
