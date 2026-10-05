from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    path('', views.scanner_view, name='scanner'),
    path('api/scan/', views.api_scan_ticket, name='api_scan'),
    path('export/csv/', views.export_attendance_csv, name='export_csv'),
]
