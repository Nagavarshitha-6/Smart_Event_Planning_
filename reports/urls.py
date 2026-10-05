from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.index_reports, name='index'),
    path('export/raw/', views.export_raw_data, name='export_raw'),
    path('export/pdf/', views.export_pdf_summary, name='export_pdf'),
]
