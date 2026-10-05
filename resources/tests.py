from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from datetime import date, time, timedelta

from events.models import Event
from resources.models import Resource, ResourceAllocation, ResourceConflict
from resources.engine import run_collision_detection, resolve_with_alternative_resource, resolve_shift_event_time, resolve_cancel_allocation

class ResourcesTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='logistics_coordinator',
            password='testpassword123',
            first_name='Dr. Sarah',
            last_name='Jenkins'
        )
        self.client.login(username='logistics_coordinator', password='testpassword123')

        # Events
        self.event_a = Event.objects.create(
            event_id='EVT-2026-9042',
            name='Python Bootcamp',
            category='Academic',
            date=date.today() + timedelta(days=5),
            start_time=time(10, 0),
            end_time=time(13, 0),
            venue='Science Hall 101',
            capacity=150,
            status='Upcoming'
        )

        self.event_b = Event.objects.create(
            event_id='EVT-2026-9088',
            name='AI Workshop',
            category='Academic',
            date=self.event_a.date,
            start_time=time(10, 0),
            end_time=time(12, 0),
            venue='Innovation Lab B',
            capacity=80,
            status='Upcoming'
        )

        # Resources
        self.res1 = Resource.objects.create(
            resource_id='RES-PRJ-001',
            name='4K Laser Projector P-001',
            resource_type='Projector',
            quantity=1,
            location='Central A/V Bay',
            status='Available'
        )

        self.res2 = Resource.objects.create(
            resource_id='RES-PRJ-003',
            name='Laser Projector P-003',
            resource_type='Projector',
            quantity=1,
            location='Depot Bay 2',
            status='Available'
        )

    def test_resource_list_view(self):
        url = reverse('resources:list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Resource Coordination & Inventory')
        self.assertContains(response, '4K Laser Projector P-001')

    def test_resource_search_and_filters(self):
        url = reverse('resources:list') + '?q=P-003'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.res2, response.context['resources'])
        self.assertNotIn(self.res1, response.context['resources'])

    def test_create_resource_success(self):
        url = reverse('resources:create')
        post_data = {
            'resource_id': 'RES-AUD-99',
            'name': 'Memorial Lecture Amphitheater',
            'resource_type': 'Auditorium',
            'quantity': 1,
            'location': 'East Wing Bldg 4',
            'status': 'Available',
            'description': '300-seat tiered amphitheater with multi-mic arrays'
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Resource.objects.filter(resource_id='RES-AUD-99').exists())

    def test_edit_resource(self):
        url = reverse('resources:edit', kwargs={'resource_id': self.res1.id})
        post_data = {
            'resource_id': self.res1.resource_id,
            'name': 'Barco Cinema 4K Projector P-001',
            'resource_type': self.res1.resource_type,
            'quantity': 1,
            'location': 'West Wing Depot',
            'status': 'Assigned',
            'description': 'Upgraded lens kit'
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)
        self.res1.refresh_from_db()
        self.assertEqual(self.res1.name, 'Barco Cinema 4K Projector P-001')

    def test_delete_resource(self):
        url = reverse('resources:delete', kwargs={'resource_id': self.res2.id})
        # GET confirm
        response_get = self.client.get(url)
        self.assertEqual(response_get.status_code, 200)
        self.assertContains(response_get, 'Decommission Campus Resource')

        # POST delete
        response_post = self.client.post(url)
        self.assertEqual(response_post.status_code, 302)
        self.assertFalse(Resource.objects.filter(id=self.res2.id).exists())

    def test_collision_detection_engine(self):
        # Create overlapping allocation A: 10:00 - 13:00
        alloc_a = ResourceAllocation.objects.create(
            event=self.event_a,
            resource=self.res1,
            date=self.event_a.date,
            start_time=time(10, 0),
            end_time=time(13, 0),
            status='Confirmed'
        )

        # Create overlapping allocation B: 10:00 - 12:00 (Direct overlap on res1)
        alloc_b = ResourceAllocation.objects.create(
            event=self.event_b,
            resource=self.res1,
            date=self.event_b.date,
            start_time=time(10, 0),
            end_time=time(12, 0),
            status='Confirmed'
        )

        # Run collision engine
        audit = run_collision_detection()
        self.assertGreaterEqual(audit['active_conflicts'], 1)

        # Verify allocations marked Conflicted
        alloc_a.refresh_from_db()
        alloc_b.refresh_from_db()
        self.assertEqual(alloc_a.status, 'Conflicted')
        self.assertEqual(alloc_b.status, 'Conflicted')

        # Verify ResourceConflict record exists
        conflict = ResourceConflict.objects.filter(resource=self.res1, is_resolved=False).first()
        self.assertIsNotNone(conflict)
        self.assertEqual(conflict.event_a, self.event_a)
        self.assertEqual(conflict.event_b, self.event_b)

    def test_conflicts_view(self):
        # Trigger conflict
        ResourceAllocation.objects.create(
            event=self.event_a,
            resource=self.res1,
            date=self.event_a.date,
            start_time=time(10, 0),
            end_time=time(13, 0)
        )
        ResourceAllocation.objects.create(
            event=self.event_b,
            resource=self.res1,
            date=self.event_b.date,
            start_time=time(10, 0),
            end_time=time(12, 0)
        )
        run_collision_detection()

        url = reverse('resources:conflicts')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Resource Conflict Detected')
        self.assertContains(response, 'Python Bootcamp')
        self.assertContains(response, 'AI Workshop')

    def test_conflict_resolution_swap_alternative(self):
        ResourceAllocation.objects.create(
            event=self.event_a,
            resource=self.res1,
            date=self.event_a.date,
            start_time=time(10, 0),
            end_time=time(13, 0)
        )
        ResourceAllocation.objects.create(
            event=self.event_b,
            resource=self.res1,
            date=self.event_b.date,
            start_time=time(10, 0),
            end_time=time(12, 0)
        )
        run_collision_detection()
        conflict = ResourceConflict.objects.filter(resource=self.res1, is_resolved=False).first()

        # Resolve via swap alternative
        url = reverse('resources:resolve_conflict', kwargs={'conflict_id': conflict.id})
        response = self.client.post(url, {'action': 'swap', 'alt_resource_id': self.res2.id})
        self.assertEqual(response.status_code, 302)

        conflict.refresh_from_db()
        self.assertTrue(conflict.is_resolved)

        # Verify allocation B now assigned to res2
        alloc_b = ResourceAllocation.objects.get(event=self.event_b, date=self.event_b.date)
        self.assertEqual(alloc_b.resource, self.res2)
        self.assertEqual(alloc_b.status, 'Confirmed')

    def test_conflict_resolution_shift_time(self):
        ResourceAllocation.objects.create(
            event=self.event_a,
            resource=self.res1,
            date=self.event_a.date,
            start_time=time(10, 0),
            end_time=time(13, 0)
        )
        ResourceAllocation.objects.create(
            event=self.event_b,
            resource=self.res1,
            date=self.event_b.date,
            start_time=time(10, 0),
            end_time=time(12, 0)
        )
        run_collision_detection()
        conflict = ResourceConflict.objects.filter(resource=self.res1, is_resolved=False).first()

        # Resolve via time shift
        url = reverse('resources:resolve_conflict', kwargs={'conflict_id': conflict.id})
        response = self.client.post(url, {'action': 'shift'})
        self.assertEqual(response.status_code, 302)

        conflict.refresh_from_db()
        self.assertTrue(conflict.is_resolved)

    def test_conflict_resolution_cancel_allocation(self):
        ResourceAllocation.objects.create(
            event=self.event_a,
            resource=self.res1,
            date=self.event_a.date,
            start_time=time(10, 0),
            end_time=time(13, 0)
        )
        ResourceAllocation.objects.create(
            event=self.event_b,
            resource=self.res1,
            date=self.event_b.date,
            start_time=time(10, 0),
            end_time=time(12, 0)
        )
        run_collision_detection()
        conflict = ResourceConflict.objects.filter(resource=self.res1, is_resolved=False).first()

        # Resolve via cancel
        url = reverse('resources:resolve_conflict', kwargs={'conflict_id': conflict.id})
        response = self.client.post(url, {'action': 'cancel'})
        self.assertEqual(response.status_code, 302)

        conflict.refresh_from_db()
        self.assertTrue(conflict.is_resolved)

    def test_export_resources_csv(self):
        url = reverse('resources:export_csv')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        content = response.content.decode('utf-8')
        self.assertIn('Resource ID', content)
        self.assertIn('4K Laser Projector P-001', content)
