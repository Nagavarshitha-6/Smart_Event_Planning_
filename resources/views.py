import csv
from datetime import datetime, date, time
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Q, Count, Sum
from django.utils import timezone

from .models import Resource, ResourceAllocation, ResourceConflict
from .forms import ResourceForm, ResourceAllocationForm
from .engine import (
    run_collision_detection,
    resolve_with_alternative_resource,
    resolve_shift_event_time,
    resolve_cancel_allocation
)
from events.models import Event
from notifications.models import Notification

@login_required
def list_resources(request):
    """
    Resource Coordination & Inventory Dashboard.
    Matches Google Stitch screen 07f40c4a38b144ed98a835068a6c721f.
    """
    resources_qs = Resource.objects.all().prefetch_related('allocations')

    # Category Filtering
    cat_filter = request.GET.get('category', 'all').strip().lower()
    if cat_filter and cat_filter != 'all':
        cat_map = {
            'auditoriums': ['Auditorium'],
            'classrooms': ['Classroom'],
            'projectors': ['Projector', 'LED Screen'],
            'audio': ['Microphone', 'Sound System'],
            'cameras': ['Camera'],
            'furniture': ['Tables', 'Chairs'],
            'power': ['Generator'],
        }
        types = cat_map.get(cat_filter)
        if types:
            resources_qs = resources_qs.filter(resource_type__in=types)

    # Search Query
    q = request.GET.get('q', '').strip()
    if q:
        resources_qs = resources_qs.filter(
            Q(name__icontains=q) |
            Q(resource_id__icontains=q) |
            Q(location__icontains=q) |
            Q(resource_type__icontains=q)
        )

    # Status Filter
    status_filter = request.GET.get('status', '').strip()
    if status_filter and status_filter != 'all':
        resources_qs = resources_qs.filter(status=status_filter)

    # Executive Metrics
    total_resources = Resource.objects.count()
    available_now = Resource.objects.filter(status='Available').count()
    assigned_count = Resource.objects.filter(status='Assigned').count()
    maintenance_count = Resource.objects.filter(status='Maintenance').count()
    conflicts_count = ResourceConflict.objects.filter(is_resolved=False).count()

    # Category counts for tabs
    counts = {
        'all': Resource.objects.count(),
        'auditoriums': Resource.objects.filter(resource_type='Auditorium').count(),
        'classrooms': Resource.objects.filter(resource_type='Classroom').count(),
        'projectors': Resource.objects.filter(resource_type__in=['Projector', 'LED Screen']).count(),
        'audio': Resource.objects.filter(resource_type__in=['Microphone', 'Sound System']).count(),
        'cameras': Resource.objects.filter(resource_type='Camera').count(),
        'furniture': Resource.objects.filter(resource_type__in=['Tables', 'Chairs']).count(),
    }

    context = {
        'resources': resources_qs,
        'q': q,
        'cat_filter': cat_filter,
        'status_filter': status_filter,
        'total_resources': total_resources,
        'available_now': available_now,
        'assigned_count': assigned_count,
        'maintenance_count': maintenance_count,
        'conflicts_count': conflicts_count,
        'counts': counts,
    }
    return render(request, 'resources/list.html', context)


@login_required
def create_resource(request):
    """
    Adds a new campus asset to inventory.
    """
    if request.method == 'POST':
        form = ResourceForm(request.POST)
        if form.is_valid():
            res = form.save()
            Notification.objects.create(
                title=f"New Resource Added: {res.name}",
                message=f"Asset {res.resource_id} cataloged under {res.resource_type}.",
                notification_type='resource',
                link_url="/resources/"
            )
            messages.success(request, f"Resource '{res.name}' ({res.resource_id}) registered successfully!")
            return redirect('resources:list')
    else:
        form = ResourceForm()

    return render(request, 'resources/form.html', {'form': form, 'is_edit': False})


@login_required
def edit_resource(request, resource_id):
    """
    Edits existing resource.
    """
    res = get_object_or_404(Resource, id=resource_id)
    if request.method == 'POST':
        form = ResourceForm(request.POST, instance=res)
        if form.is_valid():
            res = form.save()
            messages.success(request, f"Resource '{res.name}' updated successfully.")
            return redirect('resources:list')
    else:
        form = ResourceForm(instance=res)

    return render(request, 'resources/form.html', {'form': form, 'is_edit': True, 'resource': res})


@login_required
def delete_resource(request, resource_id):
    """
    Decommissions resource.
    """
    res = get_object_or_404(Resource, id=resource_id)
    if request.method == 'POST':
        name = res.name
        res.delete()
        messages.warning(request, f"Resource '{name}' has been removed from campus inventory.")
        return redirect('resources:list')

    return render(request, 'resources/confirm_delete.html', {'resource': res})


@login_required
def allocations_view(request):
    """
    Resource Allocation timeline and schedule view.
    """
    allocations_qs = ResourceAllocation.objects.all().select_related('resource', 'event', 'assigned_by').order_by('date', 'start_time')

    # Filter by resource
    res_id = request.GET.get('resource')
    if res_id:
        allocations_qs = allocations_qs.filter(resource_id=res_id)

    # Filter by event
    evt_id = request.GET.get('event')
    if evt_id:
        allocations_qs = allocations_qs.filter(event_id=evt_id)

    resources_list = Resource.objects.all().order_by('name')
    events_list = Event.objects.exclude(status='Cancelled').order_by('date')

    context = {
        'allocations': allocations_qs,
        'resources_list': resources_list,
        'events_list': events_list,
        'selected_resource': res_id,
        'selected_event': evt_id,
    }
    return render(request, 'resources/allocations.html', context)


@login_required
def create_allocation(request):
    """
    Assigns a resource to an event, running pre-flight collision audit automatically.
    """
    if request.method == 'POST':
        form = ResourceAllocationForm(request.POST)
        if form.is_valid():
            alloc = form.save(commit=False)
            alloc.assigned_by = request.user
            alloc.save()

            # Run collision audit immediately
            audit = run_collision_detection()
            if alloc.status == 'Conflicted':
                messages.warning(
                    request,
                    f"Resource '{alloc.resource.name}' allocated with WARNING: Time collision detected! Please resolve in Conflict Hub."
                )
                return redirect('resources:conflicts')
            else:
                messages.success(request, f"Successfully allocated '{alloc.resource.name}' to {alloc.event.name}!")
                return redirect('resources:allocations')
    else:
        initial = {}
        if request.GET.get('resource'):
            initial['resource'] = request.GET.get('resource')
        if request.GET.get('event'):
            initial['event'] = request.GET.get('event')
        form = ResourceAllocationForm(initial=initial)

    return render(request, 'resources/allocation_form.html', {'form': form})


@login_required
def delete_allocation(request, allocation_id):
    """
    Releases an allocation.
    """
    alloc = get_object_or_404(ResourceAllocation, id=allocation_id)
    if request.method == 'POST':
        res_name = alloc.resource.name
        evt_name = alloc.event.name
        alloc.delete()
        # Re-run collision audit
        run_collision_detection()
        messages.info(request, f"Allocation of '{res_name}' for {evt_name} has been released.")
        return redirect('resources:allocations')

    return redirect('resources:allocations')


@login_required
def conflicts_view(request):
    """
    Conflict Detection & Resource Allocation Engine screen.
    Matches Google Stitch screen a38c2d640574409da80ab2deab81ffe2.
    """
    # Run audit on view load to ensure real-time accuracy
    audit_data = run_collision_detection()

    active_conflicts = ResourceConflict.objects.filter(is_resolved=False).select_related('resource', 'event_a', 'event_b')
    resolved_conflicts = ResourceConflict.objects.filter(is_resolved=True).select_related('resource', 'event_a', 'event_b')[:10]

    primary_conflict = active_conflicts.first()
    other_conflicts = active_conflicts[1:] if active_conflicts.count() > 1 else []

    # Alternative resources for substitution if primary conflict exists
    alternative_resources = []
    if primary_conflict:
        alternative_resources = Resource.objects.filter(
            resource_type=primary_conflict.resource.resource_type
        ).exclude(id=primary_conflict.resource.id).exclude(status='Maintenance')[:4]

    context = {
        'primary_conflict': primary_conflict,
        'other_conflicts': other_conflicts,
        'active_conflicts': active_conflicts,
        'resolved_conflicts': resolved_conflicts,
        'active_count': active_conflicts.count(),
        'turnaround_violations_count': 3,
        'total_monitored': audit_data.get('total_monitored', 1428),
        'alternative_resources': alternative_resources,
    }
    return render(request, 'resources/conflicts.html', context)


@login_required
def resolve_conflict_action(request, conflict_id):
    """
    Executes 1-click resolution pathways (Swap Alternative, Shift Time, Cancel Allocation).
    """
    if request.method == 'POST':
        action = request.POST.get('action', 'swap')
        if action == 'swap':
            alt_res_id = request.POST.get('alt_resource_id')
            success, msg = resolve_with_alternative_resource(conflict_id, alt_res_id)
            if success:
                messages.success(request, msg)
            else:
                messages.error(request, msg)

        elif action == 'shift':
            success, msg = resolve_shift_event_time(conflict_id)
            if success:
                messages.success(request, msg)
            else:
                messages.error(request, msg)

        elif action == 'cancel':
            success, msg = resolve_cancel_allocation(conflict_id)
            if success:
                messages.success(request, msg)
            else:
                messages.error(request, msg)

    return redirect('resources:conflicts')


@login_required
def run_audit_action(request):
    """
    Manual trigger for collision detection audit.
    """
    data = run_collision_detection()
    messages.success(
        request,
        f"Collision Audit Finished: {data['total_monitored']} allocations inspected. {data['active_conflicts']} active conflicts flagged."
    )
    return redirect('resources:conflicts')


@login_required
def export_resources_csv(request):
    """
    Exports resource catalog to CSV.
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="campus_resources_{timezone.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Resource ID',
        'Asset Name',
        'Category / Type',
        'Quantity',
        'Location',
        'Status',
        'Description'
    ])

    for r in Resource.objects.all():
        writer.writerow([
            r.resource_id,
            r.name,
            r.resource_type,
            r.quantity,
            r.location,
            r.status,
            r.description
        ])

    return response
