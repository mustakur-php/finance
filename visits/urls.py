from django.urls import path
from . import views

urlpatterns = [
    path('', views.visits_list, name='visits_list'),
    path('create/', views.visit_create, name='visit_create'),
    path('<int:pk>/edit/', views.visit_edit, name='visit_edit'),
]
