from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import date, time, timedelta

from events.models import Event
from vendors.models import Vendor
from budgets.models import Budget
from expenses.models import Expense

class BudgetsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='finance_director',
            password='testpassword123',
            first_name='Dr. Sarah',
            last_name='Jenkins'
        )
        self.client.login(username='finance_director', password='testpassword123')

        # Events
        self.event_a = Event.objects.create(
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

        self.event_b = Event.objects.create(
            event_id='EVT-2026-9088',
            name='Alumni Leadership Gala',
            category='Networking',
            date=date.today() + timedelta(days=20),
            start_time=time(18, 0),
            end_time=time(22, 0),
            venue='Grand Quad Pavilion',
            capacity=300,
            status='Upcoming'
        )

        # Vendors
        self.vendor_av = Vendor.objects.create(
            vendor_id='V-9021',
            name='Bay Area Production Rentals',
            service_type='Audio/Visual',
            contact_person='Alex Mercer',
            email='alex@bayproduction.com',
            phone='+1 (415) 555-0199',
            tier='Tier 1',
            sla_status='Cleared',
            status='Active'
        )

        self.vendor_cat = Vendor.objects.create(
            vendor_id='V-1184',
            name='Apex University Hospitality',
            service_type='Catering',
            contact_person='Maria Santos',
            email='events@apexhospitality.edu',
            phone='+1 (415) 555-0122',
            tier='Tier 1',
            sla_status='Cleared',
            status='Active'
        )

        # Budgets
        self.budget_a = Budget.objects.create(
            budget_id='BDG-2026-001',
            event=self.event_a,
            department='CS & Engineering Dept',
            fiscal_year='FY 2026',
            allocated_amount=Decimal('120000.00'),
            spent_amount=Decimal('0.00'),
            remaining_amount=Decimal('120000.00'),
            status='Within Budget'
        )

        self.budget_b = Budget.objects.create(
            budget_id='BDG-2026-002',
            event=self.event_b,
            department='University Relations',
            fiscal_year='FY 2026',
            allocated_amount=Decimal('85000.00'),
            spent_amount=Decimal('0.00'),
            remaining_amount=Decimal('85000.00'),
            status='Within Budget'
        )

        # Expenses
        self.exp1 = Expense.objects.create(
            expense_id='EXP-8821',
            event=self.event_a,
            category='Audio/Visual & Rigging',
            description='4K Laser Projector Rigging Lease',
            amount=Decimal('14850.00'),
            date=date.today(),
            vendor=self.vendor_av,
            payment_status='Paid',
            receipt_ref='INV-441.pdf',
            is_authorized=True
        )

        self.exp2 = Expense.objects.create(
            expense_id='EXP-8822',
            event=self.event_b,
            category='Catering & Hospitality',
            description='450 Executive VIP Luncheon Platters',
            amount=Decimal('18450.00'),
            date=date.today(),
            vendor=self.vendor_cat,
            payment_status='Pending Approval',
            receipt_ref='PO-8920.pdf',
            is_authorized=False
        )

    def test_budget_list_view(self):
        url = reverse('budgets:list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Budgets &amp; Expense Ledger')
        self.assertContains(response, 'Annual Tech Summit')
        self.assertContains(response, 'Alumni Leadership Gala')
        self.assertContains(response, 'EXP-8821')
        self.assertContains(response, 'EXP-8822')

    def test_budget_utilization_calculation(self):
        self.budget_a.update_totals()
        self.assertEqual(self.budget_a.spent_amount, Decimal('14850.00'))
        self.assertEqual(self.budget_a.remaining_amount, Decimal('105150.00'))
        self.assertEqual(self.budget_a.status, 'Within Budget')
        self.assertAlmostEqual(self.budget_a.utilization_percentage, 12.4, places=1)

    def test_log_expense_creation(self):
        url = reverse('budgets:log_expense')
        post_data = {
            'expense_id': 'EXP-8823',
            'event': self.event_a.id,
            'category': 'Venue & Facility',
            'description': 'Main Stage Acoustical Shell Setup',
            'amount': '3200.00',
            'date': str(date.today()),
            'vendor': self.vendor_av.id,
            'payment_status': 'Paid',
            'receipt_ref': 'INV-442.pdf',
            'is_authorized': False
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Expense.objects.filter(expense_id='EXP-8823').exists())

        self.budget_a.refresh_from_db()
        self.assertEqual(self.budget_a.spent_amount, Decimal('18050.00'))

    def test_dual_authorization_rule(self):
        # Expense 2 is > $5000 and not authorized
        self.assertFalse(self.exp2.is_authorized)
        self.assertEqual(self.exp2.payment_status, 'Pending Approval')

        url = reverse('budgets:authorize_requisition', kwargs={'expense_id': self.exp2.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        self.exp2.refresh_from_db()
        self.assertTrue(self.exp2.is_authorized)
        self.assertEqual(self.exp2.payment_status, 'Paid')

    def test_rebalance_funds(self):
        url = reverse('budgets:rebalance_funds')
        post_data = {
            'source_budget': self.budget_a.id,
            'target_budget': self.budget_b.id,
            'transfer_amount': '15000.00',
            'justification': 'Rebalancing excess contingency to Alumni Gala'
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)

        self.budget_a.refresh_from_db()
        self.budget_b.refresh_from_db()
        self.assertEqual(self.budget_a.allocated_amount, Decimal('105000.00'))
        self.assertEqual(self.budget_b.allocated_amount, Decimal('100000.00'))

    def test_rebalance_funds_insufficient_balance(self):
        url = reverse('budgets:rebalance_funds')
        post_data = {
            'source_budget': self.budget_b.id,
            'target_budget': self.budget_a.id,
            'transfer_amount': '999999.00',  # exceeds budget_b available
            'justification': 'Invalid excessive transfer'
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)

        # Balances should remain untouched
        self.budget_b.refresh_from_db()
        self.assertEqual(self.budget_b.allocated_amount, Decimal('85000.00'))

    def test_edit_expense(self):
        url = reverse('budgets:edit_expense', kwargs={'expense_id': self.exp1.id})
        post_data = {
            'expense_id': self.exp1.expense_id,
            'event': self.event_a.id,
            'category': self.exp1.category,
            'description': 'Updated 4K Laser Rigging Discounted',
            'amount': '12000.00',
            'date': str(self.exp1.date),
            'vendor': self.vendor_av.id,
            'payment_status': 'Paid',
            'receipt_ref': 'INV-441-REV.pdf',
            'is_authorized': True
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)

        self.exp1.refresh_from_db()
        self.assertEqual(self.exp1.amount, Decimal('12000.00'))
        self.assertEqual(self.exp1.description, 'Updated 4K Laser Rigging Discounted')

    def test_delete_expense(self):
        url = reverse('budgets:delete_expense', kwargs={'expense_id': self.exp1.id})
        # GET confirm
        response_get = self.client.get(url)
        self.assertEqual(response_get.status_code, 200)
        self.assertContains(response_get, 'Remove Ledger Line Item?')

        # POST delete
        response_post = self.client.post(url)
        self.assertEqual(response_post.status_code, 302)
        self.assertFalse(Expense.objects.filter(id=self.exp1.id).exists())

        self.budget_a.refresh_from_db()
        self.assertEqual(self.budget_a.spent_amount, Decimal('0.00'))

    def test_export_csv(self):
        url = reverse('budgets:export_csv')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertContains(response, 'Expense ID,Event ID,Event Name')
        self.assertContains(response, 'EXP-8821')

    def test_filtering_and_search(self):
        # Filter by status
        url_status = reverse('budgets:list') + '?status=Paid'
        resp_status = self.client.get(url_status)
        self.assertIn(self.exp1, resp_status.context['expenses'])
        self.assertNotIn(self.exp2, resp_status.context['expenses'])

        # Search by query
        url_q = reverse('budgets:list') + '?q=Luncheon'
        resp_q = self.client.get(url_q)
        self.assertIn(self.exp2, resp_q.context['expenses'])
        self.assertNotIn(self.exp1, resp_q.context['expenses'])
