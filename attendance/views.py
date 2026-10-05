import csv
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import Attendance
from registrations.models import Registration
from events.models import Event
from notifications.models import Notification

@login_required
def scanner_view(request):
    """
    Hardware Scanner Terminal & Live Attendance Verification Hub.
    Handles continuous optical barcode scanning, duplicate prevention,
    and real-time gate telemetry.
    """
    events_list = Event.objects.exclude(status='Cancelled').order_by('date')
    selected_event_id = request.GET.get('event', '').strip()
    
    selected_event = None
    if selected_event_id:
        selected_event = Event.objects.filter(id=selected_event_id).first()
    if not selected_event:
        selected_event = events_list.first()

    scan_result = None

    # Handle Barcode / Ticket scan POST
    if request.method == 'POST':
        ticket_code = request.POST.get('ticket_id', '').strip()
        station = request.POST.get('station', 'Gate 4 (VIP North)')
        auto_checkin = request.POST.get('auto_checkin', 'on') == 'on'

        if not ticket_code:
            messages.warning(request, "Please enter or scan a valid Ticket ID or attendee barcode.")
        else:
            # Look up registration by ticket ID or registration code or name or email
            reg_query = Q(ticket_id__iexact=ticket_code) | Q(registration_id__iexact=ticket_code)
            # If not exact match, search attendee email or full name
            reg = Registration.objects.filter(reg_query).select_related('event', 'attendance_record').first()
            if not reg:
                reg = Registration.objects.filter(
                    Q(email__iexact=ticket_code) | Q(name__icontains=ticket_code)
                ).select_related('event', 'attendance_record').first()

            if not reg:
                # Ticket not found
                scan_result = {
                    'status': 'error',
                    'type': 'not_found',
                    'scanned_code': ticket_code,
                    'message': f"Ticket or Barcode '{ticket_code}' not recognized in campus registry database."
                }
            elif reg.status == 'Cancelled':
                # Cancelled / Revoked ticket
                scan_result = {
                    'status': 'error',
                    'type': 'cancelled',
                    'reg': reg,
                    'scanned_code': ticket_code,
                    'message': f"Admission Revoked: Registration for '{reg.name}' was cancelled."
                }
            elif reg.status == 'Checked In':
                # Duplicate check-in detected
                att = getattr(reg, 'attendance_record', None)
                scan_result = {
                    'status': 'warning',
                    'type': 'duplicate',
                    'reg': reg,
                    'attendance': att,
                    'scanned_code': ticket_code,
                    'message': f"Duplicate Check-In Detected: '{reg.name}' was already cleared."
                }
            else:
                # Valid pass -> perform check-in
                att = Attendance.objects.create(
                    registration=reg,
                    ticket_id=reg.ticket_id,
                    checked_in_by=request.user,
                    notes=f"{station}"
                )
                reg.status = 'Checked In'
                reg.save()

                # Dispatch Notification
                Notification.objects.create(
                    title=f"Gate Admission: {reg.name}",
                    message=f"Pass {reg.ticket_id} verified and admitted via {station}.",
                    notification_type='event',
                    link_url=f"/registrations/{reg.id}/"
                )

                scan_result = {
                    'status': 'success',
                    'type': 'verified',
                    'reg': reg,
                    'attendance': att,
                    'scanned_code': reg.ticket_id,
                    'message': f"Attendee '{reg.name}' verified and checked in successfully!"
                }

    # Telemetry Metrics (Scoped to selected event if chosen, or campus aggregate)
    if selected_event:
        reg_base = Registration.objects.filter(event=selected_event)
        event_name = selected_event.name
        capacity = selected_event.capacity
    else:
        reg_base = Registration.objects.all()
        event_name = "All Campus Events"
        capacity = 4000

    total_registered = reg_base.count()
    checked_in_count = reg_base.filter(status='Checked In').count()
    check_in_pct = round((checked_in_count / total_registered * 100), 1) if total_registered > 0 else 0.0
    remaining_count = total_registered - checked_in_count
    remaining_pct = round(100.0 - check_in_pct, 1) if total_registered > 0 else 0.0

    # High Density Ledger Filter
    ledger_qs = Attendance.objects.all().select_related(
        'registration', 'registration__event', 'checked_in_by'
    ).order_by('-check_in_time')

    if selected_event:
        ledger_qs = ledger_qs.filter(registration__event=selected_event)

    search_q = request.GET.get('q', '').strip()
    if search_q:
        ledger_qs = ledger_qs.filter(
            Q(ticket_id__icontains=search_q) |
            Q(registration__name__icontains=search_q) |
            Q(registration__email__icontains=search_q)
        )

    recent_checkins = ledger_qs[:20]

    # Pre-canned Gate Stations
    stations = [
        {'id': 'STA-01', 'name': 'Gate 1 • South Quad', 'desc': 'Main General Admission', 'scans': 840, 'ping': '28ms', 'status': 'Online', 'status_color': 'success'},
        {'id': 'STA-02', 'name': 'Gate 2 • Auditorium West', 'desc': 'Faculty & Press Concourse', 'scans': 612, 'ping': '34ms', 'status': 'Online', 'status_color': 'success'},
        {'id': 'STA-04', 'name': 'Gate 4 • VIP North (Active)', 'desc': 'Speakers, Keynote, Sponsors', 'scans': 410, 'ping': '19ms', 'status': 'THIS TERMINAL', 'status_color': 'primary'},
        {'id': 'RF-M03', 'name': 'Mobile Handheld 03', 'desc': 'Roving Marshall • Atrium', 'scans': 180, 'ping': 'Idle 3m', 'status': 'Standby', 'status_color': 'warning'},
    ]

    context = {
        'events_list': events_list,
        'selected_event': selected_event,
        'scan_result': scan_result,
        'total_registered': total_registered,
        'checked_in_count': checked_in_count,
        'check_in_pct': check_in_pct,
        'remaining_count': remaining_count,
        'remaining_pct': remaining_pct,
        'capacity': capacity,
        'peak_flow': 42,
        'stations': stations,
        'recent_checkins': recent_checkins,
        'search_q': search_q,
    }
    return render(request, 'attendance/scanner.html', context)


@login_required
def api_scan_ticket(request):
    """
    Continuous AJAX Endpoint for hardware handheld scanners and USB optical readers.
    Returns JSON response with badge profile, duplicate detection, or invalid flags.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST method authorized'}, status=405)

    # Support JSON payload or Form data
    if request.content_type == 'application/json':
        try:
            body = json.loads(request.body)
            ticket_code = body.get('ticket_id', '').strip()
            station = body.get('station', 'Gate 4 (VIP North)')
        except Exception:
            return JsonResponse({'status': 'error', 'message': 'Malformed JSON'}, status=400)
    else:
        ticket_code = request.POST.get('ticket_id', '').strip()
        station = request.POST.get('station', 'Gate 4 (VIP North)')

    if not ticket_code:
        return JsonResponse({'status': 'error', 'message': 'Missing ticket barcode code'}, status=400)

    reg = Registration.objects.filter(
        Q(ticket_id__iexact=ticket_code) | Q(registration_id__iexact=ticket_code) | Q(email__iexact=ticket_code)
    ).select_related('event', 'attendance_record').first()

    if not reg:
        return JsonResponse({
            'status': 'error',
            'type': 'not_found',
            'message': f"Ticket '{ticket_code}' not found in registry."
        }, status=404)

    if reg.status == 'Cancelled':
        return JsonResponse({
            'status': 'error',
            'type': 'cancelled',
            'message': f"Ticket {reg.ticket_id} ({reg.name}) has been CANCELLED and admission is REVOKED.",
            'attendee': {
                'name': reg.name,
                'ticket_id': reg.ticket_id,
                'email': reg.email,
                'event': reg.event.name
            }
        }, status=403)

    if reg.status == 'Checked In':
        att = getattr(reg, 'attendance_record', None)
        check_time_str = att.check_in_time.strftime('%I:%M %p') if att else "earlier"
        return JsonResponse({
            'status': 'warning',
            'type': 'duplicate',
            'message': f"Duplicate check-in! {reg.name} was already admitted at {check_time_str}.",
            'attendee': {
                'name': reg.name,
                'ticket_id': reg.ticket_id,
                'email': reg.email,
                'event': reg.event.name,
                'check_in_time': check_time_str,
                'station': att.notes if att else 'Unknown'
            }
        })

    # Success check-in
    att = Attendance.objects.create(
        registration=reg,
        ticket_id=reg.ticket_id,
        checked_in_by=request.user,
        notes=station
    )
    reg.status = 'Checked In'
    reg.save()

    return JsonResponse({
        'status': 'success',
        'type': 'verified',
        'message': f"Attendee {reg.name} verified and admitted.",
        'attendee': {
            'id': reg.id,
            'name': reg.name,
            'ticket_id': reg.ticket_id,
            'email': reg.email,
            'event': reg.event.name,
            'check_in_time': att.check_in_time.strftime('%I:%M:%S %p'),
            'station': station
        }
    })


@login_required
def export_attendance_csv(request):
    """
    Exports the current attendance ledger to a formatted CSV spreadsheet.
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="attendance_ledger_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Ticket ID',
        'Attendee Name',
        'Email',
        'Phone',
        'Event Name',
        'Venue',
        'Check-In Time',
        'Operator',
        'Station / Gate Notes'
    ])

    event_id = request.GET.get('event')
    qs = Attendance.objects.select_related('registration', 'registration__event', 'checked_in_by').order_by('-check_in_time')
    if event_id:
        qs = qs.filter(registration__event_id=event_id)

    for item in qs:
        writer.writerow([
            item.ticket_id,
            item.registration.name,
            item.registration.email,
            item.registration.phone,
            item.registration.event.name,
            item.registration.event.venue,
            item.check_in_time.strftime('%Y-%m-%d %H:%M:%S'),
            item.checked_in_by.username if item.checked_in_by else 'System / Auto',
            item.notes
        ])

    return response
