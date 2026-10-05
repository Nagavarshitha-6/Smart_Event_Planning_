from datetime import datetime, date, time
from django.db.models import Q
from .models import Resource, ResourceAllocation, ResourceConflict
from notifications.models import Notification

def run_collision_detection():
    """
    Authoritative temporal and physical asset collision engine.
    Scans all resource allocations for overlapping time windows on the same date.
    Detects interval collisions: a.start_time < b.end_time AND a.end_time > b.start_time
    """
    active_allocations = ResourceAllocation.objects.exclude(
        status='Released'
    ).select_related('resource', 'event').order_by('date', 'start_time')

    # Group allocations by (resource_id, date)
    grouped = {}
    for alloc in active_allocations:
        key = (alloc.resource_id, alloc.date)
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(alloc)

    detected_conflict_pks = set()
    conflicts_count = 0

    for (res_id, cdate), alloc_list in grouped.items():
        if len(alloc_list) < 2:
            continue

        # Pairwise comparison
        for i in range(len(alloc_list)):
            for j in range(i + 1, len(alloc_list)):
                a = alloc_list[i]
                b = alloc_list[j]

                # Check if same event (rare but possible)
                if a.event_id == b.event_id:
                    continue

                # Interval overlap: max(start_a, start_b) < min(end_a, end_b)
                overlap_start = max(a.start_time, b.start_time)
                overlap_end = min(a.end_time, b.end_time)

                if overlap_start < overlap_end:
                    # Colliding!
                    a.status = 'Conflicted'
                    a.save()
                    b.status = 'Conflicted'
                    b.save()

                    res = a.resource
                    overlap_mins = int((datetime.combine(date.today(), overlap_end) - datetime.combine(date.today(), overlap_start)).total_seconds() / 60)

                    conflict, created = ResourceConflict.objects.get_or_create(
                        resource=res,
                        event_a=a.event,
                        event_b=b.event,
                        conflict_date=cdate,
                        defaults={
                            'time_a': f"{a.start_time.strftime('%I:%M %p')} – {a.end_time.strftime('%I:%M %p')}",
                            'time_b': f"{b.start_time.strftime('%I:%M %p')} – {b.end_time.strftime('%I:%M %p')}",
                            'description': f"Critical Collision: {res.name} is double-booked on {cdate.strftime('%B %d, %Y')} between {overlap_start.strftime('%I:%M %p')} and {overlap_end.strftime('%I:%M %p')} ({overlap_mins} min direct overlap).",
                            'is_resolved': False
                        }
                    )
                    if not created:
                        conflict.is_resolved = False
                        conflict.description = f"Critical Collision: {res.name} is double-booked on {cdate.strftime('%B %d, %Y')} between {overlap_start.strftime('%I:%M %p')} and {overlap_end.strftime('%I:%M %p')} ({overlap_mins} min direct overlap)."
                        conflict.save()

                    detected_conflict_pks.add(conflict.id)
                    conflicts_count += 1

    # Check previously open conflicts that are no longer colliding
    open_conflicts = ResourceConflict.objects.filter(is_resolved=False)
    for c in open_conflicts:
        if c.id not in detected_conflict_pks:
            c.is_resolved = True
            c.save()

    total_monitored = active_allocations.count()
    return {
        'total_monitored': total_monitored,
        'conflicts_count': conflicts_count,
        'active_conflicts': ResourceConflict.objects.filter(is_resolved=False).count()
    }


def resolve_with_alternative_resource(conflict_id, alt_resource_id=None):
    """
    Resolves conflict by swapping the colliding event's allocation to an available alternative resource.
    """
    conflict = ResourceConflict.objects.get(id=conflict_id)
    colliding_event = conflict.event_b
    original_resource = conflict.resource

    if alt_resource_id:
        alt_resource = Resource.objects.get(id=alt_resource_id)
    else:
        # Find first available resource of same type
        alt_resource = Resource.objects.filter(
            resource_type=original_resource.resource_type
        ).exclude(id=original_resource.id).exclude(status='Maintenance').first()

    if not alt_resource:
        # Fallback to any available resource of similar category
        alt_resource = Resource.objects.filter(status='Available').exclude(id=original_resource.id).first()

    if alt_resource:
        alloc = ResourceAllocation.objects.filter(
            event=colliding_event,
            resource=original_resource,
            date=conflict.conflict_date
        ).first()

        if alloc:
            alloc.resource = alt_resource
            alloc.status = 'Confirmed'
            alloc.save()

        conflict.is_resolved = True
        conflict.description += f" [Resolved: Swapped to {alt_resource.name}]"
        conflict.save()

        # Update remaining allocation for event A
        alloc_a = ResourceAllocation.objects.filter(
            event=conflict.event_a,
            resource=original_resource,
            date=conflict.conflict_date
        ).first()
        if alloc_a:
            alloc_a.status = 'Confirmed'
            alloc_a.save()

        Notification.objects.create(
            title=f"Conflict Resolved: {original_resource.name}",
            message=f"Alternative resource '{alt_resource.name}' assigned to {colliding_event.name}.",
            notification_type='resource',
            link_url="/resources/conflicts/"
        )
        return True, f"Successfully assigned alternative asset '{alt_resource.name}' to {colliding_event.name}."

    return False, "No alternative resource found for substitution."


def resolve_shift_event_time(conflict_id, new_start=None, new_end=None):
    """
    Resolves conflict by shifting the colliding event's allocation time window.
    """
    conflict = ResourceConflict.objects.get(id=conflict_id)
    alloc = ResourceAllocation.objects.filter(
        event=conflict.event_b,
        resource=conflict.resource,
        date=conflict.conflict_date
    ).first()

    if alloc:
        if new_start and new_end:
            alloc.start_time = new_start
            alloc.end_time = new_end
        else:
            # Default shift: 1:00 PM to 3:00 PM
            alloc.start_time = time(13, 0)
            alloc.end_time = time(15, 0)

        alloc.status = 'Confirmed'
        alloc.save()

        # Reset primary allocation to confirmed
        alloc_a = ResourceAllocation.objects.filter(
            event=conflict.event_a,
            resource=conflict.resource,
            date=conflict.conflict_date
        ).first()
        if alloc_a:
            alloc_a.status = 'Confirmed'
            alloc_a.save()

        conflict.is_resolved = True
        conflict.description += f" [Resolved: Shifted {conflict.event_b.name} to {alloc.start_time.strftime('%I:%M %p')}]"
        conflict.save()

        Notification.objects.create(
            title=f"Conflict Resolved: Time Shift",
            message=f"Shifted {conflict.event_b.name} schedule to {alloc.start_time.strftime('%I:%M %p')}.",
            notification_type='resource',
            link_url="/resources/conflicts/"
        )
        return True, f"Shifted {conflict.event_b.name} schedule to {alloc.start_time.strftime('%I:%M %p')} – {alloc.end_time.strftime('%I:%M %p')}."

    return False, "Could not locate allocation record to shift."


def resolve_cancel_allocation(conflict_id):
    """
    Resolves conflict by cancelling the duplicate colliding allocation.
    """
    conflict = ResourceConflict.objects.get(id=conflict_id)
    alloc = ResourceAllocation.objects.filter(
        event=conflict.event_b,
        resource=conflict.resource,
        date=conflict.conflict_date
    ).first()

    if alloc:
        alloc.status = 'Released'
        alloc.save()

    # Reset event A's allocation
    alloc_a = ResourceAllocation.objects.filter(
        event=conflict.event_a,
        resource=conflict.resource,
        date=conflict.conflict_date
    ).first()
    if alloc_a:
        alloc_a.status = 'Confirmed'
        alloc_a.save()

    conflict.is_resolved = True
    conflict.description += " [Resolved: Colliding allocation cancelled]"
    conflict.save()

    Notification.objects.create(
        title=f"Conflict Resolved: Allocation Released",
        message=f"Cancelled allocation of {conflict.resource.name} for {conflict.event_b.name}.",
        notification_type='resource',
        link_url="/resources/conflicts/"
    )
    return True, f"Colliding allocation for '{conflict.event_b.name}' was released."
