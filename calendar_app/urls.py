from django.urls import path
from . import views

urlpatterns = [
    path('', views.calendar_view, name='calendar_view'),
    path('create/', views.event_create, name='event_create'),
    path('<int:pk>/done/', views.event_toggle_done, name='event_toggle_done'),
    path('<int:pk>/edit/', views.event_edit, name='event_edit'),
    path('<int:pk>/reschedule/', views.event_reschedule, name='event_reschedule'),
    path('<int:pk>/cancel/', views.event_cancel, name='event_cancel'),
    path('history/', views.events_history, name='events_history'),
]
