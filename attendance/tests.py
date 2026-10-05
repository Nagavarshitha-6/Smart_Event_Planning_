from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from datetime import date, time, timedelta
import json

from events.models import Event
from registrations.models import Registration
from attendance.models import Attendance

class AttendanceScannerTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='gatekeeper',
            password='testpassword123',
            first_name='Dr. Sarah',
            last_name='Jenkins'
        )
        self.client.login(username='gatekeeper', password='testpassword123')

        self.event = Event.objects.create(
            event_id='EVT-2026-CONF',
            name='AI & Robotics Symposium',
            category='Academic',
            date=date.today(),
            start_time=time(8, 30),
            end_time=time(16, 30),
            venue='Central Concourse Hall',
            capacity=600,
            status='Upcoming'
        )

        self.reg_valid = Registration.objects.create(
            registration_id='REG-2026-3001',
            name='Dr. Alan Turing',
            email='alan@institution.edu',
            event=self.event,
            ticket_id='TKT-3001-A',
            status='Registered'
        )

        self.reg_checked = Registration.objects.create(
            registration_id='REG-2026-3002',
            name='Ada Lovelace',
            email='ada@institution.edu',
            event=self.event,
            ticket_id='TKT-3002-B',
            status='Checked In'
        )
        self.att_existing = Attendance.objects.create(
            registration=self.reg_checked,
            ticket_id=self.reg_checked.ticket_id,
            checked_in_by=self.user,
            notes='Gate 1 (South Quad)'
        )

        self.reg_cancelled = Registration.objects.create(
            registration_id='REG-2026-3003',
            name='Charles Babbage',
            email='charles@institution.edu',
            event=self.event,
            ticket_id='TKT-3003-C',
            status='Cancelled'
        )

    def test_scanner_page_loads(self):
        url = reverse('attendance:scanner')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Hardware Scanner Terminal')
        self.assertContains(response, 'Attendance & Real-Time Check-In')

    def test_scanner_post_valid_ticket(self):
        url = reverse('attendance:scanner')
        post_data = {
            'ticket_id': 'TKT-3001-A',
            'station': 'Gate 4 (VIP North)'
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Attendee Checked In Successfully')
        self.assertContains(response, 'Dr. Alan Turing')

        # Check in DB
        self.reg_valid.refresh_from_db()
        self.assertEqual(self.reg_valid.status, 'Checked In')
        self.assertTrue(Attendance.objects.filter(ticket_id='TKT-3001-A').exists())

    def test_scanner_post_duplicate_ticket(self):
        url = reverse('attendance:scanner')
        post_data = {
            'ticket_id': 'TKT-3002-B',
            'station': 'Gate 4 (VIP North)'
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Duplicate Check-In Detected')
        self.assertContains(response, 'Ada Lovelace')

    def test_scanner_post_cancelled_ticket(self):
        url = reverse('attendance:scanner')
        post_data = {
            'ticket_id': 'TKT-3003-C',
            'station': 'Gate 4 (VIP North)'
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Admission Revoked')

    def test_scanner_post_unknown_ticket(self):
        url = reverse('attendance:scanner')
        post_data = {
            'ticket_id': 'TKT-NONEXISTENT',
            'station': 'Gate 4 (VIP North)'
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'not recognized in campus registry')

    def test_api_scan_success(self):
        # Create a fresh registration
        fresh_reg = Registration.objects.create(
            registration_id='REG-2026-9999',
            name='Grace Hopper',
            email='grace@navy.mil',
            event=self.event,
            ticket_id='TKT-9999-G',
            status='Registered'
        )
        url = reverse('attendance:api_scan')
        response = self.client.post(
            url,
            data=json.dumps({'ticket_id': 'TKT-9999-G', 'station': 'Gate 2 West'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['attendee']['name'], 'Grace Hopper')

    def test_api_scan_duplicate(self):
        url = reverse('attendance:api_scan')
        response = self.client.post(
            url,
            data=json.dumps({'ticket_id': 'TKT-3002-B'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'warning')
        self.assertEqual(data['type'], 'duplicate')

    def test_export_attendance_csv(self):
        url = reverse('attendance:export_csv')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        content = response.content.decode('utf-8')
        self.assertIn('Ticket ID', content)
        self.assertIn('Ada Lovelace', content)
        self.assertIn('TKT-3002-B', content)
