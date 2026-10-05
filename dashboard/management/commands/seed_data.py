from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, time, timedelta
from decimal import Decimal
import random

from events.models import Event
from vendors.models import Vendor
from resources.models import Resource, ResourceAllocation, ResourceConflict
from registrations.models import Registration
from attendance.models import Attendance
from budgets.models import Budget
from expenses.models import Expense
from notifications.models import Notification

class Command(BaseCommand):
    help = 'Seeds database with realistic CampusOps EventCore data matching Stitch project'

    def handle(self, *args, **options):
        self.stdout.write("Starting database seeding...")

        # 1. Admin User
        admin, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@campusops.edu',
                'first_name': 'Dr. Sarah',
                'last_name': 'Jenkins',
                'is_staff': True,
                'is_superuser': True
            }
        )
        admin.set_password('adminpassword123')
        admin.save()

        # 2. Vendors
        vendors_data = [
            ("VND-2026-01", "Apex Hospitality & Catering", "Catering", "David Lin", "555-0192", "dlin@apexcatering.com"),
            ("VND-2026-02", "ProSound & Stage Dynamics", "Audio/Visual", "Sarah Vance", "555-0183", "svance@prosound.org"),
            ("VND-2026-03", "Campus Guard Services", "Security", "Capt. Robert Harris", "555-0174", "security@campusops.edu"),
            ("VND-2026-04", "Lumina LED Rigging Co.", "Staging & Lighting", "Alex Mercer", "555-0165", "amercer@lumina.com"),
            ("VND-2026-05", "Metro Janitorial Services", "Janitorial", "Maria Santos", "555-0156", "msantos@metrojanitorial.com"),
            ("VND-2026-06", "Prime Fleet Transport", "Logistics & Transport", "Jack O'Neill", "555-0147", "joneill@primefleet.com"),
        ]
        vendors = {}
        for vid, vname, stype, cperson, ph, em in vendors_data:
            v, _ = Vendor.objects.get_or_create(
                vendor_id=vid,
                defaults={
                    'name': vname,
                    'service_type': stype,
                    'contact_person': cperson,
                    'phone': ph,
                    'email': em,
                    'status': 'Active'
                }
            )
            vendors[vid] = v

        # 3. Resources
        resources_data = [
            ("RES-AUD-01", "Main Hall A", "Auditorium", 1, "Central Campus - Bldg 1", "Available", "Premier university auditorium with 700 seat capacity and built-in projection"),
            ("RES-AUD-02", "Main Hall B", "Auditorium", 1, "Central Campus - Bldg 1", "Assigned", "Mid-size hall with 300 capacity and multi-zone audio rigging"),
            ("RES-AUD-03", "Health Sciences Amphitheater", "Auditorium", 1, "Medical Quad - West Wing", "Available", "Tiered lecture hall with 250 capacity and broadcast capability"),
            ("RES-PAV-01", "Grand Pavilion", "Auditorium", 1, "North Campus Grounds", "Available", "Covered banquet space accommodating 400 guests"),
            ("RES-PRJ-01", "Projector 4K P-01", "Projector", 1, "A/V Inventory Depot A", "Assigned", "Barco 4K Laser Cinema Projector with optical zoom"),
            ("RES-PRJ-02", "Projector HD P-02", "Projector", 1, "A/V Inventory Depot A", "Available", "Epson High-Lumen Portable Projector"),
            ("RES-MIC-01", "Shure Wireless Mic Kit (Set of 4)", "Microphone", 4, "A/V Depot B", "Available", "Digital wireless handheld & lavalier kit"),
            ("RES-SND-01", "Line-Array Concert PA System", "Sound System", 2, "Central Stage Staging", "Assigned", "JBL VTX line-array active speakers with subwoofers"),
            ("RES-LED-01", "Mobile LED Video Wall 16x9", "LED Screen", 2, "Media Tech Bay", "Available", "High-refresh mobile outdoor/indoor LED panel"),
            ("RES-TBL-01", "Banquet Round Tables (10-seat)", "Tables", 50, "Facilities Warehouse Bay 3", "Available", "Solid wood foldable banquet tables"),
            ("RES-CHR-01", "Ergonomic Conference Chairs", "Chairs", 400, "Facilities Warehouse Bay 4", "Available", "Stackable padded conference chairs"),
        ]
        resources = {}
        for rid, rname, rtype, qty, loc, stat, desc in resources_data:
            r, _ = Resource.objects.get_or_create(
                resource_id=rid,
                defaults={
                    'name': rname,
                    'resource_type': rtype,
                    'quantity': qty,
                    'location': loc,
                    'status': stat,
                    'description': desc
                }
            )
            resources[rid] = r

        # 4. Events
        today = date.today()
        events_data = [
            ("EVT-2026-101", "Annual Tech & Innovation Summit 2026", "Conference", today + timedelta(days=2), time(9, 0), time(17, 30), "Main Hall A", 700, "Upcoming", "Premier technology showcase featuring keynotes, demonstrations, and hackathon finals."),
            ("EVT-2026-102", "Global Health Sciences Symposium", "Academic", today + timedelta(days=4), time(10, 30), time(15, 0), "Health Sciences Amphitheater", 250, "Upcoming", "International healthcare leaders discussing epidemic prevention and genomic biology."),
            ("EVT-2026-103", "Alumni Leadership Gala & Awards", "Gala", today + timedelta(days=8), time(18, 30), time(23, 0), "Grand Pavilion", 400, "Upcoming", "Black-tie evening celebration honoring university benefactors and distinguished alumni."),
            ("EVT-2026-104", "Global Sustainability Summit", "Academic", today + timedelta(days=10), time(8, 30), time(16, 30), "Auditorium Magna", 500, "Upcoming", "Cross-disciplinary summit focusing on clean campus energy and zero-waste initiatives."),
            ("EVT-2026-105", "Freshman Career Pathways Expo", "Career", today + timedelta(days=12), time(8, 0), time(16, 0), "Student Union Quad", 1200, "Upcoming", "Over 85 hiring partners and employers conducting on-site interviews for interns."),
            ("EVT-2026-106", "AI & Robotics Autonomous Demo", "Workshop", today + timedelta(days=2), time(11, 0), time(17, 0), "Main Hall B", 300, "Upcoming", "Hands-on robotics laboratory and reinforcement learning agent demonstrations."),
            ("EVT-2026-100", "Fall Campus Welcome Orientation", "Student Life", today - timedelta(days=5), time(9, 0), time(14, 0), "Main Hall A", 800, "Completed", "Comprehensive welcoming ceremony and resource orientation for incoming undergraduates."),
        ]

        events = {}
        for eid, ename, cat, edate, stime, etime, ven, cap, stat, desc in events_data:
            ev, _ = Event.objects.get_or_create(
                event_id=eid,
                defaults={
                    'name': ename,
                    'category': cat,
                    'date': edate,
                    'start_time': stime,
                    'end_time': etime,
                    'venue': ven,
                    'capacity': cap,
                    'status': stat,
                    'description': desc,
                    'created_by': admin
                }
            )
            events[eid] = ev

        # 5. Resource Allocations & Intentional Conflict
        ResourceAllocation.objects.get_or_create(
            event=events["EVT-2026-101"],
            resource=resources["RES-AUD-01"],
            date=events["EVT-2026-101"].date,
            defaults={'start_time': time(8, 30), 'end_time': time(18, 0), 'assigned_by': admin, 'status': 'Confirmed'}
        )
        ResourceAllocation.objects.get_or_create(
            event=events["EVT-2026-101"],
            resource=resources["RES-PRJ-01"],
            date=events["EVT-2026-101"].date,
            defaults={'start_time': time(8, 30), 'end_time': time(17, 30), 'assigned_by': admin, 'status': 'Confirmed'}
        )
        ResourceAllocation.objects.get_or_create(
            event=events["EVT-2026-106"],
            resource=resources["RES-PRJ-01"],
            date=events["EVT-2026-106"].date,
            defaults={'start_time': time(11, 0), 'end_time': time(16, 0), 'assigned_by': admin, 'status': 'Conflicted'}
        )

        # Conflict record
        ResourceConflict.objects.get_or_create(
            resource=resources["RES-PRJ-01"],
            event_a=events["EVT-2026-101"],
            event_b=events["EVT-2026-106"],
            conflict_date=events["EVT-2026-101"].date,
            defaults={
                'time_a': "08:30 AM – 05:30 PM",
                'time_b': "11:00 AM – 04:00 PM",
                'description': "Barco Projector 4K P-01 double-booked simultaneously between Tech Summit in Main Hall A and AI Demo in Main Hall B.",
                'is_resolved': False
            }
        )

        ResourceConflict.objects.get_or_create(
            resource=resources["RES-SND-01"],
            event_a=events["EVT-2026-103"],
            event_b=events["EVT-2026-106"],
            conflict_date=events["EVT-2026-103"].date,
            defaults={
                'time_a': "06:30 PM – 11:00 PM",
                'time_b': "05:00 PM – 09:00 PM",
                'description': "Concert PA line-array overlap scheduled during load-in for Alumni Gala.",
                'is_resolved': False
            }
        )

        # 6. Registrations & Attendance
        sample_attendees = [
            ("Marcus Vance", "marcus.vance@campus.edu", "555-0981"),
            ("Elena Rostova", "e.rostova@techcorp.io", "555-0982"),
            ("Prof. Arthur Pendelton", "arthur.p@university.edu", "555-0983"),
            ("Zoe Zhang", "zzhang@student.campus.edu", "555-0984"),
            ("Tariq Al-Mansoor", "t.mansoor@biotech.org", "555-0985"),
            ("Claire Beauchamp", "claire.b@globalhealth.net", "555-0986"),
            ("Harrison Ford", "hford@alumni.campus.edu", "555-0987"),
            ("Maya Patel", "mpatel@robotics.dev", "555-0988"),
            ("Liam O'Connor", "loconnor@greenenergy.gov", "555-0989"),
            ("Sofia Morales", "smorales@career.net", "555-0990"),
        ]

        ticket_counter = 8840
        for i, (name, email, phone) in enumerate(sample_attendees):
            target_ev = events["EVT-2026-101"] if i < 4 else (events["EVT-2026-102"] if i < 7 else events["EVT-2026-103"])
            tkt = f"TKT-{ticket_counter + i}"
            reg, _ = Registration.objects.get_or_create(
                event=target_ev,
                email=email,
                defaults={
                    'registration_id': f"REG-2026-{1000 + i}",
                    'name': name,
                    'phone': phone,
                    'ticket_id': tkt,
                    'status': 'Checked In' if i in [0, 1, 4] else 'Registered'
                }
            )
            if reg.status == 'Checked In':
                Attendance.objects.get_or_create(
                    registration=reg,
                    defaults={
                        'ticket_id': tkt,
                        'checked_in_by': admin,
                        'notes': 'Verified at Gate 4 Scanner'
                    }
                )

        # 7. Budgets & Expenses
        budgets_data = [
            (events["EVT-2026-101"], Decimal('35000.00')),
            (events["EVT-2026-102"], Decimal('18000.00')),
            (events["EVT-2026-103"], Decimal('45000.00')),
            (events["EVT-2026-104"], Decimal('22000.00')),
            (events["EVT-2026-105"], Decimal('15000.00')),
        ]
        for ev, alloc in budgets_data:
            b, _ = Budget.objects.get_or_create(
                event=ev,
                defaults={
                    'budget_id': f"BDG-{ev.event_id.replace('EVT-', '')}",
                    'allocated_amount': alloc,
                    'spent_amount': Decimal('0.00'),
                    'remaining_amount': alloc,
                    'status': 'Within Budget'
                }
            )

        expenses_data = [
            ("EXP-2026-01", events["EVT-2026-101"], "Audio/Visual & Rigging", "Full summit sound and multi-screen projection setup", Decimal('8450.00'), vendors["VND-2026-02"], "Paid", "INV-441.pdf", True),
            ("EXP-2026-02", events["EVT-2026-101"], "Catering & Hospitality", "Morning coffee & keynote buffet catering contract", Decimal('6200.00'), vendors["VND-2026-01"], "Paid", "INV-442.pdf", True),
            ("EXP-2026-03", events["EVT-2026-102"], "Catering & Hospitality", "Health Sciences speaker luncheon", Decimal('3100.00'), vendors["VND-2026-01"], "Paid", "INV-443.pdf", True),
            ("EXP-2026-04", events["EVT-2026-103"], "Venue & Facility", "Grand Pavilion stage preparation and ambient lighting", Decimal('12500.00'), vendors["VND-2026-04"], "Pending Approval", "PO-8920.pdf", False),
            ("EXP-2026-05", events["EVT-2026-103"], "Catering & Hospitality", "Plated dinner catering contract (Apex Hospitality)", Decimal('18200.00'), vendors["VND-2026-01"], "Pending Approval", "PO-8921.pdf", False),
        ]
        for exp_id, ev, cat, desc, amt, vnd, pstat, rref, auth in expenses_data:
            Expense.objects.get_or_create(
                expense_id=exp_id,
                defaults={
                    'event': ev,
                    'category': cat,
                    'description': desc,
                    'amount': amt,
                    'date': ev.date - timedelta(days=3),
                    'vendor': vnd,
                    'payment_status': pstat,
                    'receipt_ref': rref,
                    'is_authorized': auth
                }
            )

        # 8. Notifications
        notifications_data = [
            ("Double-Booking Collision Detected", "Projector 4K P-01 assigned simultaneously to AI Workshop & Tech Summit.", "conflict", "critical", "COLLISION_ENGINE", False, "/resources/conflicts/"),
            ("PO Requisition RQ-9921 Exceeds $5,000 Dual Sign-Off", "Apex Hospitality catering order of $18,200 requires Dean authorization.", "budget", "warning", "FINANCE_GATEWAY", False, "/budgets/"),
            ("Standing Room Capacity Alert", "Health Sciences Amphitheater has reached 96% RSVP threshold.", "event", "info", "CAPACITY_MONITOR", False, "/events/"),
            ("Janitorial Dispatch Complete", "Main Hall A has been sanitized & prepared for Oct 16 proceedings.", "maintenance", "success", "FACILITY_OPS", True, "/resources/"),
        ]
        for title, msg, ntype, sev, scode, read_st, link in notifications_data:
            Notification.objects.get_or_create(
                title=title,
                defaults={
                    'message': msg,
                    'notification_type': ntype,
                    'severity': sev,
                    'source_code': scode,
                    'is_read': read_st,
                    'link_url': link
                }
            )

        self.stdout.write(self.style.SUCCESS("Successfully seeded real database models matching Stitch design!"))
