import csv
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.db.models import Sum, Q, Count

from events.models import Event
from vendors.models import Vendor
from expenses.models import Expense
from budgets.models import Budget
from budgets.forms import ExpenseForm, BudgetForm, RebalanceFundsForm

CATEGORY_PALETTE = {
    'Catering & Hospitality': '#1d4ed8',
    'Venue & Facility': '#004870',
    'Audio/Visual & Rigging': '#006194',
    'Marketing & Signage': '#565e74',
    'Security & Staffing': '#7c3aed',
    'Logistics & Transport': '#059669',
    'Other': '#b7c4ff',
}

@login_required
def list_budgets(request):
    # Update all budget records from current expenses
    for b in Budget.objects.all():
        b.update_totals()

    # Search & filters
    q = request.GET.get('q', '').strip()
    category_filter = request.GET.get('category', '').strip()
    status_filter = request.GET.get('status', '').strip()
    event_filter = request.GET.get('event', '').strip()

    expenses_qs = Expense.objects.select_related('event', 'vendor').all().order_by('-date', '-created_date')

    if q:
        expenses_qs = expenses_qs.filter(
            Q(expense_id__icontains=q) |
            Q(description__icontains=q) |
            Q(vendor__name__icontains=q) |
            Q(event__name__icontains=q) |
            Q(receipt_ref__icontains=q)
        )
    if category_filter:
        expenses_qs = expenses_qs.filter(category=category_filter)
    if status_filter:
        expenses_qs = expenses_qs.filter(payment_status=status_filter)
    if event_filter:
        expenses_qs = expenses_qs.filter(event__event_id=event_filter)

    filtered_total = expenses_qs.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # Pagination
    paginator = Paginator(expenses_qs, 8)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Executive KPI Quad Cards
    total_approved_pool = Budget.objects.aggregate(total=Sum('allocated_amount'))['total'] or Decimal('0.00')
    if total_approved_pool == Decimal('0.00'):
        total_approved_pool = Decimal('485000.00')

    total_spent = Expense.objects.exclude(payment_status='Cancelled').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    encumbered_qs = Expense.objects.filter(payment_status__in=['Pending', 'Pending Approval', 'Invoiced'])
    total_encumbered = encumbered_qs.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    active_pos_count = encumbered_qs.count()

    total_surplus = max(Decimal('0.00'), total_approved_pool - total_spent)

    spent_pct = min(round((total_spent / total_approved_pool * Decimal('100.0')), 1), 100.0) if total_approved_pool > 0 else 0.0
    encumbered_pct = min(round((total_encumbered / total_approved_pool * Decimal('100.0')), 1), 100.0) if total_approved_pool > 0 else 0.0
    surplus_pct = min(round((total_surplus / total_approved_pool * Decimal('100.0')), 1), 100.0) if total_approved_pool > 0 else 0.0

    # Event Budget Utilization cards
    budgets_list = list(Budget.objects.select_related('event').all())
    event_trackers = []
    for b in budgets_list:
        pct = b.utilization_percentage
        if pct >= 90.0:
            tier_class = 'danger'
            tier_label = 'Lock Trigger Active'
            badge_bg = 'bg-danger-subtle text-danger'
            bar_color = '#dc2626'
        elif pct >= 75.0:
            tier_class = 'warning'
            tier_label = 'Approaching Cap'
            badge_bg = 'bg-warning-subtle text-warning-emphasis'
            bar_color = '#006194'
        else:
            tier_class = 'primary'
            tier_label = 'Safe Margin'
            badge_bg = 'bg-primary-subtle text-primary'
            bar_color = '#1d4ed8'

        event_trackers.append({
            'budget': b,
            'pct': pct,
            'tier_class': tier_class,
            'tier_label': tier_label,
            'badge_bg': badge_bg,
            'bar_color': bar_color,
        })

    # Category Variance Breakdown for Donut Chart
    cat_aggregates = Expense.objects.exclude(payment_status='Cancelled')\
        .values('category')\
        .annotate(cat_total=Sum('amount'))\
        .order_by('-cat_total')

    category_breakdown = []
    accumulated_offset = 0
    total_valid_spent = sum((c['cat_total'] for c in cat_aggregates), Decimal('0.00'))

    for cat in cat_aggregates:
        amount = cat['cat_total']
        pct = round(float(amount / total_valid_spent * 100), 1) if total_valid_spent > 0 else 0
        color = CATEGORY_PALETTE.get(cat['category'], '#64748b')
        dash_array = f"{pct} {100 - pct}"
        offset = accumulated_offset
        accumulated_offset -= pct

        category_breakdown.append({
            'category': cat['category'],
            'amount': amount,
            'pct': pct,
            'color': color,
            'dash_array': dash_array,
            'dash_offset': offset,
        })

    # Requisition Dual Sign-Off Queue (amount >= $5,000 or status Pending Approval)
    signoff_queue = Expense.objects.filter(
        Q(amount__gte=Decimal('5000.00'), is_authorized=False) |
        Q(payment_status='Pending Approval')
    ).exclude(payment_status='Cancelled').select_related('event', 'vendor')[:5]

    # Forms
    expense_form = ExpenseForm()
    rebalance_form = RebalanceFundsForm()

    context = {
        'page_title': 'Budgets & Expense Ledger',
        'expenses': page_obj,
        'page_obj': page_obj,
        'filtered_total': filtered_total,
        'q': q,
        'category_filter': category_filter,
        'status_filter': status_filter,
        'event_filter': event_filter,
        'all_categories': [c[0] for c in Expense.CATEGORY_CHOICES],
        'all_statuses': [s[0] for s in Expense.STATUS_CHOICES],
        'events': Event.objects.all(),
        # KPIs
        'total_approved_pool': total_approved_pool,
        'total_spent': total_spent,
        'total_encumbered': total_encumbered,
        'total_surplus': total_surplus,
        'active_pos_count': active_pos_count,
        'spent_pct': spent_pct,
        'encumbered_pct': encumbered_pct,
        'surplus_pct': surplus_pct,
        # Bento components
        'event_trackers': event_trackers,
        'category_breakdown': category_breakdown,
        'signoff_queue': signoff_queue,
        'signoff_count': signoff_queue.count(),
        # Forms
        'expense_form': expense_form,
        'rebalance_form': rebalance_form,
    }
    return render(request, 'budgets/list.html', context)

@login_required
def log_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            if not expense.expense_id:
                count = Expense.objects.count() + 1
                expense.expense_id = f"EXP-{8820 + count}"
            # Check dual authorization threshold
            if expense.amount >= Decimal('5000.00') and not expense.is_authorized:
                if expense.payment_status not in ['Pending', 'Pending Approval']:
                    messages.warning(
                        request,
                        f"Per Campus Fiscal Dual Authorization Policy, expenses ≥ $5,000.00 require joint Dean sign-off before release."
                    )
            expense.save()
            messages.success(request, f"Expense {expense.expense_id} (${expense.amount:,.2f}) recorded successfully.")
            return redirect('budgets:list')
        else:
            messages.error(request, "Failed to record expense. Please inspect form inputs.")
    return redirect('budgets:list')

@login_required
def edit_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, f"Expense {expense.expense_id} updated successfully.")
            return redirect('budgets:list')
        else:
            messages.error(request, "Please correct the errors in the expense form.")
    else:
        form = ExpenseForm(instance=expense)
    return render(request, 'budgets/expense_form.html', {'form': form, 'expense': expense, 'page_title': f'Edit Expense {expense.expense_id}'})

@login_required
def delete_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id)
    if request.method == 'POST':
        code = expense.expense_id
        amount = expense.amount
        expense.delete()
        messages.success(request, f"Expense {code} (${amount:,.2f}) removed and budget recalculated.")
        return redirect('budgets:list')
    return render(request, 'budgets/confirm_delete.html', {'expense': expense, 'page_title': 'Confirm Expense Deletion'})

@login_required
def authorize_requisition(request, expense_id):
    if request.method == 'POST':
        expense = get_object_or_404(Expense, id=expense_id)
        expense.is_authorized = True
        expense.payment_status = 'Paid'
        expense.save()
        messages.success(
            request,
            f"Dual authorization granted for {expense.expense_id} (${expense.amount:,.2f}) by {request.user.get_full_name() or request.user.username}. Disbursed to {expense.vendor.name if expense.vendor else 'Payee'}."
        )
    return redirect('budgets:list')

@login_required
def rebalance_funds(request):
    if request.method == 'POST':
        form = RebalanceFundsForm(request.POST)
        if form.is_valid():
            source = form.cleaned_data['source_budget']
            target = form.cleaned_data['target_budget']
            amount = form.cleaned_data['transfer_amount']
            justification = form.cleaned_data.get('justification', '')

            # Execute rebalance transfer
            source.allocated_amount -= amount
            target.allocated_amount += amount
            source.save()
            target.save()
            source.update_totals()
            target.update_totals()

            messages.success(
                request,
                f"Successfully rebalanced ${amount:,.2f} from {source.event.name} to {target.event.name}. Reason: {justification or 'Surplus reallocation'}"
            )
            return redirect('budgets:list')
        else:
            for error in form.non_field_errors():
                messages.error(request, error)
    return redirect('budgets:list')

@login_required
def export_ledger_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="campus_eventcore_expense_ledger.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Expense ID',
        'Event ID',
        'Event Name',
        'Category',
        'Description',
        'Vendor Name',
        'Transaction Date',
        'Amount (USD)',
        'Payment Status',
        'Dual Authorized',
        'Receipt / PO Ref'
    ])

    expenses = Expense.objects.select_related('event', 'vendor').all().order_by('-date')
    for exp in expenses:
        writer.writerow([
            exp.expense_id,
            exp.event.event_id,
            exp.event.name,
            exp.category,
            exp.description,
            exp.vendor.name if exp.vendor else 'Direct Disbursed',
            exp.date.strftime('%Y-%m-%d'),
            f"{exp.amount:.2f}",
            exp.payment_status,
            'YES' if exp.is_authorized else 'NO',
            exp.receipt_ref
        ])

    return response
