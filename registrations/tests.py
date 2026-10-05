from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, time, timedelta

from events.models import Event
from registrations.models import Registration
from attendance.models import Attendance

class RegistrationsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='coordinator',
            password='testpassword123',
            first_name='Dr. Sarah',
            last_name='Jenkins'
        )
        self.client.login(username='coordinator', password='testpassword123')

        self.event = Event.objects.create(
            event_id='EVT-2026-TEST',
            name='Autonomous Systems Expo',
            category='Academic',
            date=date.today() + timedelta(days=5),
            start_time=time(9, 0),
            end_time=time(17, 0),
            venue='Tech Quad Pavilion',
            capacity=2, # Small capacity to test capacity limits
            status='Upcoming'
        )

        self.reg1 = Registration.objects.create(
            registration_id='REG-2026-1001',
            name='Marcus Vance',
            email='m.vance@campus.edu',
            phone='+1 555-0101',
            event=self.event,
            ticket_id='TKT-1001-A',
            status='Registered'
        )

    def test_list_registrations_view(self):
        url = reverse('registrations:list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Marcus Vance')
        self.assertContains(response, 'TKT-1001-A')

    def test_search_registrations(self):
        url = reverse('registrations:list') + '?q=Marcus'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Marcus Vance')

        url_empty = reverse('registrations:list') + '?q=NonExistent'
        response_empty = self.client.get(url_empty)
        self.assertNotContains(response_empty, 'Marcus Vance')

    def test_detail_registration_view(self):
        url = reverse('registrations:detail', kwargs={'registration_id': self.reg1.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Marcus Vance')
        self.assertContains(response, 'TKT-1001-A')
        self.assertContains(response, 'Autonomous Systems Expo')

    def test_create_registration_success(self):
        url = reverse('registrations:create')
        post_data = {
            'event': self.event.id,
            'name': 'Elena Rostova',
            'email': 'e.rostova@campus.edu',
            'phone': '+1 555-0102',
            'ticket_id': 'TKT-1002-B',
            'status': 'Registered'
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302) # Redirect to detail view
        self.assertTrue(Registration.objects.filter(email='e.rostova@campus.edu').exists())

    def test_duplicate_registration_prevention(self):
        url = reverse('registrations:create')
        post_data = {
            'event': self.event.id,
            'name': 'Marcus Duplicate',
            'email': 'm.vance@campus.edu', # Duplicate email for same event
            'phone': '+1 555-9999',
            'ticket_id': 'TKT-9999-D',
            'status': 'Registered'
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200) # Form re-rendered with validation error
        self.assertContains(response, 'already registered')

    def test_capacity_overflow_prevention(self):
        # Already 1 registered (reg1). Event capacity is 2.
        # Add 2nd registration:
        Registration.objects.create(
            registration_id='REG-2026-1002',
            name='Second Attendee',
            email='second@campus.edu',
            event=self.event,
            ticket_id='TKT-1002-C',
            status='Registered'
        )

        # Now capacity (2) is reached. Attempt 3rd registration:
        url = reverse('registrations:create')
        post_data = {
            'event': self.event.id,
            'name': 'Third Attendee',
            'email': 'third@campus.edu',
            'ticket_id': 'TKT-1003-D',
            'status': 'Registered'
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'maximum authorized capacity')

    def test_cancel_registration(self):
        url = reverse('registrations:cancel', kwargs={'registration_id': self.reg1.id})
        # GET confirm screen
        response_get = self.client.get(url)
        self.assertEqual(response_get.status_code, 200)
        self.assertContains(response_get, 'Cancel Registration Pass')

        # POST confirm cancellation
        response_post = self.client.post(url)
        self.assertEqual(response_post.status_code, 302)
        self.reg1.refresh_from_db()
        self.assertEqual(self.reg1.status, 'Cancelled')
