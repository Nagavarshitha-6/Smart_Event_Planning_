from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.list_notifications, name='list'),
    path('<int:notification_id>/read/', views.mark_notification_read, name='mark_read'),
    path('read-all/', views.mark_all_read, name='mark_all_read'),
    path('broadcast/', views.broadcast_urgent, name='broadcast'),
]
