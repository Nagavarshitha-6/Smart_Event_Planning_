from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from datetime import date, time, timedelta

from events.models import Event
from vendors.models import Vendor, VendorDispatch

class VendorsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='procurement_officer',
            password='testpassword123',
            first_name='Dr. Sarah',
            last_name='Jenkins'
        )
        self.client.login(username='procurement_officer', password='testpassword123')

        self.event = Event.objects.create(
            event_id='EVT-2026-VND',
            name='Global Engineering Showcase',
            category='Academic',
            date=date.today() + timedelta(days=10),
            start_time=time(9, 0),
            end_time=time(18, 0),
            venue='Engineering Atrium',
            capacity=400,
            status='Upcoming'
        )

        self.vendor1 = Vendor.objects.create(
            vendor_id='VND-TEST-401',
            name='Apex Hospitality Group',
            service_type='Catering',
            contact_person='Marcus Sterling',
            phone='+1 (555) 438-9921',
            email='m.sterling@apexcatering.com',
            status='Active',
            tier='Tier 1',
            sla_status='Cleared',
            active_event=self.event
        )

        self.vendor2 = Vendor.objects.create(
            vendor_id='VND-TEST-552',
            name='Metro Guard Security',
            service_type='Security',
            contact_person='Capt. Sean O\'Dell',
            phone='+1 (555) 773-4419',
            email='sean@metroguard.com',
            status='Active',
            tier='Tier 2',
            sla_status='Expiring Soon'
        )

    def test_vendor_list_view(self):
        url = reverse('vendors:list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Apex Hospitality Group')
        self.assertContains(response, 'Metro Guard Security')
        self.assertContains(response, 'Vendor Management & Logistics Dispatch')

    def test_vendor_search_filter(self):
        url = reverse('vendors:list') + '?q=Sterling'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.vendor1, response.context['vendors'])
        self.assertNotIn(self.vendor2, response.context['vendors'])

    def test_vendor_category_filter(self):
        url = reverse('vendors:list') + '?category=catering'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.vendor1, response.context['vendors'])
        self.assertNotIn(self.vendor2, response.context['vendors'])

    def test_vendor_sla_filter(self):
        url = reverse('vendors:list') + '?sla=expiring'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.vendor2, response.context['vendors'])
        self.assertNotIn(self.vendor1, response.context['vendors'])

    def test_create_vendor_success(self):
        url = reverse('vendors:create')
        post_data = {
            'vendor_id': 'VND-NEW-999',
            'name': 'Stellar Sound & Lighting',
            'service_type': 'Audio/Visual',
            'contact_person': 'Rachel Vance',
            'phone': '+1 (555) 890-1120',
            'email': 'rachel@stellarsound.com',
            'status': 'Active',
            'tier': 'Tier 1',
            'sla_status': 'Cleared'
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Vendor.objects.filter(vendor_id='VND-NEW-999').exists())

    def test_detail_vendor_view(self):
        url = reverse('vendors:detail', kwargs={'vendor_id': self.vendor1.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Apex Hospitality Group')
        self.assertContains(response, 'Marcus Sterling')
        self.assertContains(response, 'Global Engineering Showcase')

    def test_edit_vendor_profile(self):
        url = reverse('vendors:edit', kwargs={'vendor_id': self.vendor1.id})
        post_data = {
            'vendor_id': self.vendor1.vendor_id,
            'name': 'Apex Hospitality International',
            'service_type': 'Catering',
            'contact_person': 'Marcus Sterling Senior',
            'phone': self.vendor1.phone,
            'email': self.vendor1.email,
            'status': 'Active',
            'tier': 'Tier 1',
            'sla_status': 'Cleared'
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)
        self.vendor1.refresh_from_db()
        self.assertEqual(self.vendor1.name, 'Apex Hospitality International')

    def test_delete_vendor(self):
        url = reverse('vendors:delete', kwargs={'vendor_id': self.vendor2.id})
        # GET confirm view
        resp_get = self.client.get(url)
        self.assertEqual(resp_get.status_code, 200)
        self.assertContains(resp_get, 'Decommission Vendor Partner')

        # POST confirm deletion
        resp_post = self.client.post(url)
        self.assertEqual(resp_post.status_code, 302)
        self.assertFalse(Vendor.objects.filter(id=self.vendor2.id).exists())

    def test_quick_dispatch_order(self):
        url = reverse('vendors:dispatch')
        post_data = {
            'vendor': self.vendor1.id,
            'event': self.event.id,
            'dock_bay': 'Bay 2 Freight',
            'call_time': '06:45 AM EDT',
            'crew_passes': 8,
            'vehicles': 2,
            'po_amount': '7500.00',
            'status': 'Cleared Dock',
            'lead_name': 'Marcus Sterling'
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(VendorDispatch.objects.filter(vendor=self.vendor1, dock_bay='Bay 2 Freight').exists())

    def test_export_vendors_csv(self):
        url = reverse('vendors:export_csv')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        content = response.content.decode('utf-8')
        self.assertIn('Vendor ID', content)
        self.assertIn('Apex Hospitality Group', content)
        self.assertIn('Metro Guard Security', content)
