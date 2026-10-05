from django.urls import path
from . import views

app_name = 'vendors'

urlpatterns = [
    path('', views.list_vendors, name='list'),
    path('create/', views.create_vendor, name='create'),
    path('<int:vendor_id>/', views.detail_vendor, name='detail'),
    path('<int:vendor_id>/edit/', views.edit_vendor, name='edit'),
    path('<int:vendor_id>/delete/', views.delete_vendor, name='delete'),
    path('dispatch/', views.quick_dispatch, name='dispatch'),
    path('export/csv/', views.export_vendors_csv, name='export_csv'),
]
