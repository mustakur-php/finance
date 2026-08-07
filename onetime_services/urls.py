from django.urls import path
from . import views

urlpatterns = [
    path('',                                    views.onetime_list,                     name='onetime_list'),
    path('<int:pk>/',                           views.onetime_detail,                   name='onetime_detail'),
    path('<int:pk>/edit/',                      views.onetime_edit,                     name='onetime_edit'),
    path('<int:pk>/delete/',                    views.onetime_delete,                   name='onetime_delete'),
    path('<int:pk>/toggle-commissionable/',     views.onetime_toggle_commissionable,    name='onetime_toggle_commissionable'),
    path('<int:pk>/service/create/',            views.onetime_service_create,           name='onetime_service_create'),
    path('service/<int:service_pk>/complete/',  views.onetime_service_complete,         name='onetime_service_complete'),
    path('service/<int:service_pk>/assign/',    views.onetime_service_assign,           name='onetime_service_assign'),
    path('service/<int:service_pk>/delete/',    views.onetime_service_delete,           name='onetime_service_delete'),
    path('service/<int:service_pk>/replace-report/', views.onetime_service_replace_report, name='onetime_service_replace_report'),
]
