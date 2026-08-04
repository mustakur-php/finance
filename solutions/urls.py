from django.urls import path
from . import views

urlpatterns = [
    path('', views.solutions_view, name='solutions'),
]
