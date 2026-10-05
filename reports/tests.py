from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from datetime import date, time, timedelta

from events.models import Event
from registrations.models import Registration
from attendance.models import Attendance

class ReportsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='reports_analyst',
            password='testpassword123',
            first_name='Dr. Sarah',
            last_name='Jenkins'
        )
        self.client.login(username='reports_analyst', password='testpassword123')

        self.event = Event.objects.create(
            event_id='EVT-2026-9042',
            name='Annual Tech Summit',
            category='Academic',
            date=date.today() + timedelta(days=10),
            start_time=time(9, 0),
            end_time=time(17, 0),
            venue='Engineering Hall C',
            capacity=500,
            status='Upcoming'
        )

        self.reg = Registration.objects.create(
            registration_id='REG-1001',
            event=self.event,
            name='Alice Student',
            email='alice@university.edu',
            ticket_id='TKT-1001-A'
        )

        self.att = Attendance.objects.create(
            registration=self.reg,
            ticket_id=self.reg.ticket_id
        )

    def test_reports_index_view(self):
        url = reverse('reports:index')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reports &amp; Institutional Analytics')
        self.assertContains(response, 'Total Events Hosted')
        self.assertContains(response, 'Resource Load')
        self.assertContains(response, 'Departmental ROI &amp; Variance Analysis')

    def test_export_raw_data_csv(self):
        url = reverse('reports:export_raw')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertContains(response, 'Event ID,Event Name,Category,Date')
        self.assertContains(response, 'EVT-2026-9042')
        self.assertContains(response, 'Annual Tech Summit')

    def test_export_pdf_summary(self):
        url = reverse('reports:export_pdf')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Executive Event Operations Briefing')
        self.assertContains(response, 'Annual Tech Summit')
