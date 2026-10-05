from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
import random

from .models import Registration
from .forms import RegistrationForm
from events.models import Event
from attendance.models import Attendance
from notifications.models import Notification

@login_required
def list_registrations(request):
    """
    Searchable, filterable, and paginated guest registry.
    """
    regs_qs = Registration.objects.all().select_related('event', 'attendance_record')

    # Search
    q = request.GET.get('q', '').strip()
    if q:
        regs_qs = regs_qs.filter(
            Q(name__icontains=q) |
            Q(email__icontains=q) |
            Q(ticket_id__icontains=q) |
            Q(phone__icontains=q) |
            Q(registration_id__icontains=q)
        )

    # Filter by event
    event_id = request.GET.get('event', '').strip()
    if event_id:
        regs_qs = regs_qs.filter(event_id=event_id)

    # Filter by status
    status_filter = request.GET.get('status', '').strip()
    if status_filter and status_filter != 'All Statuses':
        regs_qs = regs_qs.filter(status=status_filter)

    # Metrics
    total_count = Registration.objects.count()
    checked_in_count = Registration.objects.filter(status='Checked In').count()
    registered_pending_count = Registration.objects.filter(status='Registered').count()
    cancelled_count = Registration.objects.filter(status='Cancelled').count()

    # Pagination: 10 per page
    paginator = Paginator(regs_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    events_list = Event.objects.all().order_by('date')
    statuses = [s[0] for s in Registration.STATUS_CHOICES]

    context = {
        'registrations': page_obj,
        'page_obj': page_obj,
        'q': q,
        'selected_event': event_id,
        'status_filter': status_filter,
        'events_list': events_list,
        'statuses': statuses,
        'total_count': total_count,
        'checked_in_count': checked_in_count,
        'registered_pending_count': registered_pending_count,
        'cancelled_count': cancelled_count,
    }
    return render(request, 'registrations/list.html', context)


@login_required
def create_registration(request):
    """
    Creates a new attendee registration with automatic ticket generation and duplicate protection.
    """
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            reg = form.save(commit=False)
            reg.registration_id = f"REG-2026-{random.randint(1000, 9999)}"
            reg.save()

            # If created directly as 'Checked In', create Attendance record
            if reg.status == 'Checked In':
                Attendance.objects.get_or_create(
                    registration=reg,
                    defaults={
                        'ticket_id': reg.ticket_id,
                        'checked_in_by': request.user,
                        'notes': 'Direct registration check-in'
                    }
                )

            # Notification
            Notification.objects.create(
                title=f"New Registration: {reg.name}",
                message=f"Pass {reg.ticket_id} issued for {reg.event.name}.",
                notification_type='registration',
                link_url=f"/registrations/{reg.id}/"
            )

            messages.success(request, f"Attendee '{reg.name}' registered with Ticket ID {reg.ticket_id}!")
            return redirect('registrations:detail', registration_id=reg.id)
    else:
        # Pre-select event if passed in query param
        initial = {}
        preset_event_id = request.GET.get('event')
        if preset_event_id:
            initial['event'] = preset_event_id
        form = RegistrationForm(initial=initial)

    return render(request, 'registrations/form.html', {'form': form, 'is_edit': False})


@login_required
def detail_registration(request, registration_id):
    """
    Displays single attendee registration credential pass.
    """
    reg = get_object_or_404(Registration.objects.select_related('event', 'attendance_record'), id=registration_id)
    attendance = getattr(reg, 'attendance_record', None)
    return render(request, 'registrations/detail.html', {'reg': reg, 'attendance': attendance})


@login_required
def edit_registration(request, registration_id):
    """
    Edits existing registration contact or event assignment.
    """
    reg = get_object_or_404(Registration, id=registration_id)
    if request.method == 'POST':
        form = RegistrationForm(request.POST, instance=reg)
        if form.is_valid():
            reg = form.save()
            messages.success(request, f"Registration record for '{reg.name}' updated successfully.")
            return redirect('registrations:detail', registration_id=reg.id)
    else:
        form = RegistrationForm(instance=reg)

    return render(request, 'registrations/form.html', {'form': form, 'is_edit': True, 'reg': reg})


@login_required
def cancel_registration(request, registration_id):
    """
    Cancels an attendee's registration pass.
    """
    reg = get_object_or_404(Registration, id=registration_id)
    if request.method == 'POST':
        reg.status = 'Cancelled'
        reg.save()
        messages.warning(request, f"Registration for '{reg.name}' ({reg.ticket_id}) has been cancelled.")
        return redirect('registrations:list')

    return render(request, 'registrations/confirm_cancel.html', {'reg': reg})
