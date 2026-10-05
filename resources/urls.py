from django.urls import path
from . import views

app_name = 'resources'

urlpatterns = [
    # Inventory
    path('', views.list_resources, name='list'),
    path('create/', views.create_resource, name='create'),
    path('<int:resource_id>/edit/', views.edit_resource, name='edit'),
    path('<int:resource_id>/delete/', views.delete_resource, name='delete'),
    path('export/csv/', views.export_resources_csv, name='export_csv'),

    # Allocations
    path('allocations/', views.allocations_view, name='allocations'),
    path('allocations/create/', views.create_allocation, name='create_allocation'),
    path('allocations/<int:allocation_id>/delete/', views.delete_allocation, name='delete_allocation'),

    # Conflict Hub & Resolution
    path('conflicts/', views.conflicts_view, name='conflicts'),
    path('conflicts/<int:conflict_id>/resolve/', views.resolve_conflict_action, name='resolve_conflict'),
    path('conflicts/audit/', views.run_audit_action, name='run_audit'),
]
