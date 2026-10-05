from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, time, timedelta
from decimal import Decimal

from events.models import Event
from registrations.models import Registration
from attendance.models import Attendance
from vendors.models import Vendor
from resources.models import Resource, ResourceConflict
from budgets.models import Budget
from expenses.models import Expense

class DashboardIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testcoordinator',
            password='testpassword123',
            first_name='Sarah',
            last_name='Jenkins'
        )

        today = date.today()
        # Event
        self.event = Event.objects.create(
            event_id='EVT-TEST-01',
            name='Campus Tech Summit',
            category='Conference',
            date=today + timedelta(days=3),
            start_time=time(9, 0),
            end_time=time(17, 0),
            venue='Main Hall A',
            capacity=500,
            status='Upcoming',
            created_by=self.user
        )

        # Registration
        self.registration = Registration.objects.create(
            registration_id='REG-TEST-01',
            name='Marcus Vance',
            email='marcus.vance@campus.edu',
            event=self.event,
            ticket_id='TKT-9001',
            status='Checked In'
        )

        # Attendance
        self.attendance = Attendance.objects.create(
            registration=self.registration,
            ticket_id='TKT-9001',
            checked_in_by=self.user
        )

        # Vendor
        self.vendor = Vendor.objects.create(
            vendor_id='VND-TEST-01',
            name='Apex Hospitality',
            service_type='Catering',
            contact_person='John Miller',
            phone='555-1234',
            email='jmiller@apex.com',
            status='Active'
        )

        # Resource & Conflict
        self.resource = Resource.objects.create(
            resource_id='RES-PRJ-01',
            name='Projector 4K',
            resource_type='Projector',
            quantity=1,
            location='Depot A',
            status='Assigned'
        )

        self.conflict = ResourceConflict.objects.create(
            resource=self.resource,
            event_a=self.event,
            event_b=self.event,
            conflict_date=today + timedelta(days=3),
            time_a='09:00 - 12:00',
            time_b='11:00 - 14:00',
            description='Overlapping projector reservation',
            is_resolved=False
        )

        # Budget & Expense
        self.budget = Budget.objects.create(
            budget_id='BDG-TEST-01',
            event=self.event,
            allocated_amount=Decimal('10000.00'),
            spent_amount=Decimal('2500.00'),
            remaining_amount=Decimal('7500.00'),
            status='Within Budget'
        )

        self.expense = Expense.objects.create(
            expense_id='EXP-TEST-01',
            event=self.event,
            category='Catering & Hospitality',
            description='Breakfast buffet',
            amount=Decimal('2500.00'),
            date=today,
            vendor=self.vendor,
            payment_status='Approved'
        )

    def test_unauthenticated_user_redirected_to_login(self):
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_authenticated_dashboard_loads_with_real_data(self):
        self.client.login(username='testcoordinator', password='testpassword123')
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 200)

        # Verify context metrics
        self.assertEqual(response.context['total_events'], 1)
        self.assertEqual(response.context['total_attendees'], 1)
        self.assertEqual(response.context['checked_in_attendees'], 1)
        self.assertEqual(response.context['total_vendors'], 1)
        self.assertEqual(response.context['active_conflicts_count'], 1)
        self.assertEqual(response.context['total_budget'], Decimal('10000.00'))
        self.assertEqual(response.context['total_expenses'], Decimal('2500.00'))
        self.assertEqual(response.context['budget_remaining'], Decimal('7500.00'))

        # Verify content contains Stitch elements and event data
        self.assertContains(response, 'Operational Dashboard')
        self.assertContains(response, 'Campus Tech Summit')
        self.assertContains(response, 'Projector 4K')
        self.assertContains(response, 'Apex Hospitality')
