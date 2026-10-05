from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('', views.list_events, name='list'),
    path('create/', views.create_event, name='create'),
    path('<int:event_id>/', views.event_detail, name='detail'),
    path('<int:event_id>/edit/', views.edit_event, name='edit'),
    path('<int:event_id>/delete/', views.delete_event, name='delete'),
    path('export/csv/', views.export_events_csv, name='export_csv'),
]
