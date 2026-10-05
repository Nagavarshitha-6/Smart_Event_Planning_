from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from datetime import date, time, timedelta
from decimal import Decimal

from events.models import Event
from registrations.models import Registration
from attendance.models import Attendance
from vendors.models import Vendor
from resources.models import Resource, ResourceAllocation
from budgets.models import Budget
from expenses.models import Expense

class EventsModuleTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='coordinator1',
            password='password123',
            first_name='Dr. Sarah',
            last_name='Jenkins'
        )

        today = date.today()
        self.event1 = Event.objects.create(
            event_id='EVT-2026-101',
            name='Annual Tech & Innovation Summit 2026',
            category='Conference',
            date=today + timedelta(days=5),
            start_time=time(9, 0),
            end_time=time(17, 30),
            venue='Main Hall A',
            capacity=700,
            status='Upcoming',
            created_by=self.user,
            description='Keynote presentations and hackathon demo'
        )

        self.event2 = Event.objects.create(
            event_id='EVT-2026-102',
            name='Global Health Symposium',
            category='Academic',
            date=today + timedelta(days=10),
            start_time=time(10, 0),
            end_time=time(15, 0),
            venue='Health Sciences Amphitheater',
            capacity=250,
            status='Draft',
            created_by=self.user
        )

        # Attendee
        self.reg = Registration.objects.create(
            registration_id='REG-101',
            name='Marcus Vance',
            email='marcus.vance@campus.edu',
            event=self.event1,
            ticket_id='TKT-8842',
            status='Checked In'
        )

        self.att = Attendance.objects.create(
            registration=self.reg,
            ticket_id='TKT-8842',
            checked_in_by=self.user
        )

        # Vendor & Expense
        self.vendor = Vendor.objects.create(
            vendor_id='VND-01',
            name='Apex Hospitality',
            service_type='Catering',
            contact_person='David Lin',
            phone='555-0192',
            email='dlin@apex.com'
        )

        self.budget = Budget.objects.create(
            budget_id='BDG-101',
            event=self.event1,
            allocated_amount=Decimal('35000.00'),
            spent_amount=Decimal('5000.00'),
            remaining_amount=Decimal('30000.00'),
            status='Within Budget'
        )

        self.expense = Expense.objects.create(
            expense_id='EXP-101',
            event=self.event1,
            category='Catering & Hospitality',
            description='Keynote breakfast',
            amount=Decimal('5000.00'),
            date=today,
            vendor=self.vendor,
            payment_status='Approved'
        )

    def test_unauthenticated_access_redirects_to_login(self):
        response = self.client.get(reverse('events:list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_events_list_renders_for_authenticated_user(self):
        self.client.login(username='coordinator1', password='password123')
        response = self.client.get(reverse('events:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Events Management')
        self.assertContains(response, 'EVT-2026-101')
        self.assertContains(response, 'Main Hall A')

    def test_search_and_filter_events(self):
        self.client.login(username='coordinator1', password='password123')
        # Search by name
        response = self.client.get(reverse('events:list') + '?q=Tech')
        self.assertContains(response, 'EVT-2026-101')
        self.assertNotContains(response, 'EVT-2026-102')

        # Filter by status
        response = self.client.get(reverse('events:list') + '?status=Draft')
        self.assertContains(response, 'EVT-2026-102')
        self.assertNotContains(response, 'EVT-2026-101')

    def test_create_event_valid_data(self):
        self.client.login(username='coordinator1', password='password123')
        data = {
            'event_id': 'EVT-2026-103',
            'name': 'Alumni Leadership Gala',
            'category': 'Gala',
            'date': (date.today() + timedelta(days=20)).strftime('%Y-%m-%d'),
            'start_time': '18:30',
            'end_time': '23:00',
            'venue': 'Grand Pavilion',
            'capacity': 400,
            'status': 'Upcoming',
            'description': 'Annual banquet and awards gala.'
        }
        response = self.client.post(reverse('events:create'), data=data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Event.objects.filter(event_id='EVT-2026-103').exists())

    def test_create_event_invalid_timing_validation(self):
        self.client.login(username='coordinator1', password='password123')
        # End time before start time
        data = {
            'event_id': 'EVT-2026-999',
            'name': 'Bad Timing Event',
            'category': 'Academic',
            'date': date.today().strftime('%Y-%m-%d'),
            'start_time': '15:00',
            'end_time': '12:00',
            'venue': 'Room 101',
            'capacity': 50,
            'status': 'Draft',
        }
        response = self.client.post(reverse('events:create'), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'end_time', 'Event end time must be chronologically after the start time.')

    def test_event_details_view_with_all_sections(self):
        self.client.login(username='coordinator1', password='password123')
        response = self.client.get(reverse('events:detail', kwargs={'event_id': self.event1.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Annual Tech &amp; Innovation Summit 2026')
        self.assertContains(response, 'Marcus Vance')
        self.assertContains(response, 'TKT-8842')
        self.assertContains(response, 'Apex Hospitality')
        self.assertContains(response, '35000.00')

    def test_edit_event(self):
        self.client.login(username='coordinator1', password='password123')
        update_data = {
            'event_id': 'EVT-2026-101',
            'name': 'Updated Tech Summit Title',
            'category': 'Conference',
            'date': self.event1.date.strftime('%Y-%m-%d'),
            'start_time': '09:00',
            'end_time': '18:00',
            'venue': 'Main Hall A (Expanded)',
            'capacity': 850,
            'status': 'Upcoming',
            'description': 'Updated description'
        }
        response = self.client.post(reverse('events:edit', kwargs={'event_id': self.event1.id}), data=update_data)
        self.assertEqual(response.status_code, 302)
        self.event1.refresh_from_db()
        self.assertEqual(self.event1.name, 'Updated Tech Summit Title')
        self.assertEqual(self.event1.capacity, 850)

    def test_delete_event(self):
        self.client.login(username='coordinator1', password='password123')
        event_id = self.event2.id
        response = self.client.post(reverse('events:delete', kwargs={'event_id': event_id}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Event.objects.filter(id=event_id).exists())

    def test_export_events_csv(self):
        self.client.login(username='coordinator1', password='password123')
        response = self.client.get(reverse('events:export_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment; filename="events_export_', response['Content-Disposition'])
        content = response.content.decode('utf-8')
        self.assertIn('EVT-2026-101', content)
        self.assertIn('Annual Tech & Innovation Summit 2026', content)
