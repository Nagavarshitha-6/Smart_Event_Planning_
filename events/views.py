import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.http import HttpResponse
from django.utils import timezone
from datetime import date

from .models import Event
from .forms import EventForm
from registrations.models import Registration
from attendance.models import Attendance
from resources.models import ResourceAllocation, ResourceConflict
from budgets.models import Budget
from expenses.models import Expense
from notifications.models import Notification

@login_required
def list_events(request):
    """
    Searchable, filterable, and paginated event management dashboard
    matching the Stitch visual specification.
    """
    events_qs = Event.objects.all().select_related('created_by')

    # Search query
    q = request.GET.get('q', '').strip()
    if q:
        events_qs = events_qs.filter(
            Q(name__icontains=q) |
            Q(event_id__icontains=q) |
            Q(venue__icontains=q) |
            Q(description__icontains=q)
        )

    # Status filter
    status_filter = request.GET.get('status', '').strip()
    if status_filter and status_filter != 'All Statuses':
        events_qs = events_qs.filter(status=status_filter)

    # Category filter
    category_filter = request.GET.get('category', '').strip()
    if category_filter and category_filter != 'All Categories':
        events_qs = events_qs.filter(category=category_filter)

    # View layout (table vs cards)
    view_mode = request.GET.get('view', 'table')

    # KPI Pulse Overview
    active_events_count = Event.objects.filter(status__in=['Upcoming', 'Ongoing', 'Draft']).count()
    total_registrations_count = Registration.objects.filter(status__in=['Registered', 'Checked In']).count()
    total_capacity = Event.objects.aggregate(total=Sum('capacity'))['total'] or 1
    reg_capacity_percentage = round((total_registrations_count / total_capacity) * 100, 1)

    allocated_assets_count = ResourceAllocation.objects.filter(status='Confirmed').count()
    critical_conflicts_count = ResourceConflict.objects.filter(is_resolved=False).count()

    # Pagination: 6 events per page
    paginator = Paginator(events_qs, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Categories list for dropdown
    categories = [c[0] for c in Event.CATEGORY_CHOICES]
    statuses = [s[0] for s in Event.STATUS_CHOICES]

    context = {
        'events': page_obj,
        'page_obj': page_obj,
        'q': q,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'view_mode': view_mode,
        'categories': categories,
        'statuses': statuses,
        'active_events_count': active_events_count,
        'total_registrations_count': total_registrations_count,
        'reg_capacity_percentage': reg_capacity_percentage,
        'allocated_assets_count': allocated_assets_count,
        'critical_conflicts_count': critical_conflicts_count,
    }
    return render(request, 'events/list.html', context)


@login_required
def create_event(request):
    """
    Creates a new event with institutional validation and initial budget creation.
    """
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()

            # Auto-create baseline zero budget container if none exists
            Budget.objects.get_or_create(
                event=event,
                defaults={
                    'budget_id': f"BDG-{event.event_id.replace('EVT-', '')}",
                    'allocated_amount': 0.00,
                    'spent_amount': 0.00,
                    'remaining_amount': 0.00,
                    'status': 'Within Budget'
                }
            )

            # Notification
            Notification.objects.create(
                title=f"New Event Created: {event.name}",
                message=f"Event {event.event_id} scheduled for {event.date} at {event.venue}.",
                notification_type='event',
                link_url=f"/events/{event.id}/"
            )

            messages.success(request, f"Event '{event.name}' ({event.event_id}) successfully created!")
            return redirect('events:detail', event_id=event.id)
    else:
        # Generate clean suggested next event ID
        next_count = Event.objects.count() + 101
        initial_id = f"EVT-2026-{next_count}"
        form = EventForm(initial={'event_id': initial_id, 'status': 'Upcoming', 'category': 'Academic', 'date': date.today()})

    return render(request, 'events/create.html', {'form': form, 'is_edit': False})


@login_required
def event_detail(request, event_id):
    """
    Complete Master Event Details Page covering Overview, Attendees, Vendors,
    Resources, Schedule, Budget, Expenses, and Activity.
    """
    event = get_object_or_404(Event.objects.select_related('created_by'), id=event_id)

    # 1. Attendees & Registrations
    registrations = event.registrations.all().order_by('-registration_date')
    checked_in_count = registrations.filter(status='Checked In').count()

    # 2. Resources & Allocations
    allocations = event.resource_allocations.select_related('resource', 'assigned_by').all()
    conflicts = ResourceConflict.objects.filter(
        Q(event_a=event) | Q(event_b=event),
        is_resolved=False
    ).select_related('resource')

    # 3. Budget & Expenses
    budget = getattr(event, 'budget', None)
    expenses = event.expenses.select_related('vendor').all().order_by('-date')
    total_spent = sum((exp.amount for exp in expenses), 0)

    # 4. Associated Vendors
    vendor_ids = expenses.values_list('vendor_id', flat=True).distinct()
    from vendors.models import Vendor
    event_vendors = Vendor.objects.filter(id__in=vendor_ids)

    # 5. Live Activity Feed for this event
    recent_checkins = Attendance.objects.filter(registration__event=event).select_related('registration').order_by('-check_in_time')[:5]

    context = {
        'event': event,
        'registrations': registrations,
        'checked_in_count': checked_in_count,
        'allocations': allocations,
        'conflicts': conflicts,
        'budget': budget,
        'expenses': expenses,
        'total_spent': total_spent,
        'event_vendors': event_vendors,
        'recent_checkins': recent_checkins,
    }
    return render(request, 'events/detail.html', context)


@login_required
def edit_event(request, event_id):
    """
    Edits existing event details.
    """
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            event = form.save()
            messages.success(request, f"Event '{event.name}' updated successfully.")
            return redirect('events:detail', event_id=event.id)
    else:
        form = EventForm(instance=event)

    return render(request, 'events/create.html', {'form': form, 'is_edit': True, 'event': event})


@login_required
def delete_event(request, event_id):
    """
    Deletes an event with confirmation and cascade warnings.
    """
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        name = event.name
        event_code = event.event_id
        event.delete()
        messages.success(request, f"Event '{name}' ({event_code}) was successfully deleted.")
        return redirect('events:list')

    return render(request, 'events/confirm_delete.html', {'event': event})


@login_required
def export_events_csv(request):
    """
    Exports filtered or all events to CSV download.
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="events_export_{timezone.localdate()}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Event ID', 'Event Name', 'Category', 'Date', 'Start Time', 'End Time', 'Venue', 'Capacity', 'Registrations', 'Status'])

    events = Event.objects.all().order_by('date')
    for ev in events:
        writer.writerow([
            ev.event_id,
            ev.name,
            ev.category,
            ev.date.strftime('%Y-%m-%d'),
            ev.start_time.strftime('%H:%M'),
            ev.end_time.strftime('%H:%M'),
            ev.venue,
            ev.capacity,
            ev.registered_count,
            ev.status
        ])

    return response
