from django.urls import path
from . import views

app_name = 'budgets'

urlpatterns = [
    path('', views.list_budgets, name='list'),
    path('expenses/log/', views.log_expense, name='log_expense'),
    path('expenses/<int:expense_id>/edit/', views.edit_expense, name='edit_expense'),
    path('expenses/<int:expense_id>/delete/', views.delete_expense, name='delete_expense'),
    path('expenses/<int:expense_id>/authorize/', views.authorize_requisition, name='authorize_requisition'),
    path('rebalance/', views.rebalance_funds, name='rebalance_funds'),
    path('export/csv/', views.export_ledger_csv, name='export_csv'),
]
