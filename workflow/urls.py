from django.urls import path
from . import views

urlpatterns = [
    path('',                              views.workflow_list,          name='workflow_list'),
    path('add/',                          views.workflow_client_create, name='workflow_client_create'),
    path('<int:pk>/',                     views.workflow_detail,        name='workflow_detail'),
    path('stage/<int:stage_pk>/update/',  views.stage_update,           name='stage_update'),
    path('stage/<int:stage_pk>/due/',     views.stage_set_due,          name='stage_set_due'),
    path('<int:pk>/toggle-commission/',   views.workflow_toggle_commissionable, name='workflow_toggle_commissionable'),
    path('report/',                       views.workflow_report,         name='workflow_report'),
]
