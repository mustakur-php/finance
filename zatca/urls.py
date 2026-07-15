from django.urls import path
from . import views

urlpatterns = [
    path('',                    views.zatca_list,                name='zatca_list'),
    path('<int:pk>/',           views.zatca_detail,              name='zatca_detail'),
    path('<int:pk>/edit/',      views.zatca_edit,                name='zatca_edit'),
    path('<int:pk>/complete/',  views.zatca_complete,            name='zatca_complete'),
    path('<int:pk>/delete/',    views.zatca_delete,              name='zatca_delete'),
    path('<int:pk>/toggle-commissionable/', views.zatca_toggle_commissionable, name='zatca_toggle_commissionable'),
    path('<int:pk>/session/create/',        views.zatca_session_create,         name='zatca_session_create'),
    path('session/<int:session_pk>/complete/', views.zatca_session_complete,    name='zatca_session_complete'),
    path('session/<int:session_pk>/delete/',   views.zatca_session_delete,      name='zatca_session_delete'),
]
