from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from notifications.models import Notification

class NotificationsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='ops_dispatcher',
            password='testpassword123',
            first_name='Dr. Sarah',
            last_name='Jenkins'
        )
        self.client.login(username='ops_dispatcher', password='testpassword123')

        self.notif_crit = Notification.objects.create(
            title='Direct Overlap in Science Hall 101',
            message='Laser Projector P-001 double-booked for Python Bootcamp and AI Workshop.',
            notification_type='conflict',
            severity='critical',
            source_code='COLLISION_ENGINE',
            is_read=False,
            link_url='/resources/conflicts/'
        )

        self.notif_warn = Notification.objects.create(
            title='PO Requisition RQ-9921 Exceeds $5,000 Dual Sign-Off',
            message='Apex Hospitality catering order of $18,450 requires Dean authorization.',
            notification_type='budget',
            severity='warning',
            source_code='FINANCE_GATEWAY',
            is_read=False,
            link_url='/budgets/'
        )

        self.notif_info = Notification.objects.create(
            title='Freight Dock Dock-B Inbound Arrival',
            message='Bay Area Production Rentals transit vehicle #DK-9042 arrived on-site.',
            notification_type='vendor',
            severity='info',
            source_code='LOGISTICS_DISPATCH',
            is_read=True
        )

    def test_notifications_list_view(self):
        url = reverse('notifications:list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Notifications &amp; Alert Dispatch Center')
        self.assertContains(response, 'Direct Overlap in Science Hall 101')
        self.assertContains(response, 'Apex Hospitality catering order')

    def test_mark_notification_read(self):
        self.assertFalse(self.notif_crit.is_read)
        url = reverse('notifications:mark_read', kwargs={'notification_id': self.notif_crit.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        self.notif_crit.refresh_from_db()
        self.assertTrue(self.notif_crit.is_read)

    def test_mark_all_read(self):
        unread_count = Notification.objects.filter(is_read=False).count()
        self.assertGreater(unread_count, 0)

        url = reverse('notifications:mark_all_read')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(Notification.objects.filter(is_read=False).count(), 0)

    def test_broadcast_urgent(self):
        url = reverse('notifications:broadcast')
        post_data = {
            'title': 'Emergency Campus Gate Closure',
            'message': 'Transit Gate 4 closed for underground fiber repair until 18:00.',
            'severity': 'critical',
            'notification_type': 'general',
            'link_url': '/events/'
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)

        created = Notification.objects.filter(title='Emergency Campus Gate Closure').first()
        self.assertIsNotNone(created)
        self.assertEqual(created.severity, 'critical')
        self.assertEqual(created.source_code, 'URGENT_BROADCAST')

    def test_notification_filtering(self):
        # Filter by severity=critical
        url_crit = reverse('notifications:list') + '?severity=critical'
        resp_crit = self.client.get(url_crit)
        self.assertIn(self.notif_crit, resp_crit.context['notifications'])
        self.assertNotIn(self.notif_warn, resp_crit.context['notifications'])

        # Filter by unread=1
        url_unread = reverse('notifications:list') + '?unread=1'
        resp_unread = self.client.get(url_unread)
        self.assertIn(self.notif_crit, resp_unread.context['notifications'])
        self.assertIn(self.notif_warn, resp_unread.context['notifications'])
        self.assertNotIn(self.notif_info, resp_unread.context['notifications'])
