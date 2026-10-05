from django.urls import path
from . import views

app_name = 'registrations'

urlpatterns = [
    path('', views.list_registrations, name='list'),
    path('create/', views.create_registration, name='create'),
    path('<int:registration_id>/', views.detail_registration, name='detail'),
    path('<int:registration_id>/edit/', views.edit_registration, name='edit'),
    path('<int:registration_id>/cancel/', views.cancel_registration, name='cancel'),
]
