from django.db import models
from decimal import Decimal
from events.models import Event
from vendors.models import Vendor

class Expense(models.Model):
    STATUS_CHOICES = [
        ('Paid', 'Paid'),
        ('Pending Approval', 'Pending Approval'),
        ('Pending', 'Pending'),
        ('Invoiced', 'Invoiced'),
        ('Reconciled', 'Reconciled'),
        ('Approved', 'Approved'),
        ('Cancelled', 'Cancelled'),
    ]

    CATEGORY_CHOICES = [
        ('Catering & Hospitality', 'Catering & Hospitality'),
        ('Venue & Facility', 'Venue & Facility'),
        ('Audio/Visual & Rigging', 'Audio/Visual & Rigging'),
        ('Marketing & Signage', 'Marketing & Signage'),
        ('Security & Staffing', 'Security & Staffing'),
        ('Logistics & Transport', 'Logistics & Transport'),
        ('Other', 'Other'),
    ]

    expense_id = models.CharField(max_length=50, unique=True, db_index=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='expenses')
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES, default='Other')
    description = models.TextField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(db_index=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses')
    payment_status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Pending')
    receipt_ref = models.CharField(max_length=100, blank=True, default='')
    is_authorized = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_date']

    def __str__(self):
        return f"{self.expense_id} - ${self.amount} for {self.event.name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Automatically update event budget spending
        if hasattr(self.event, 'budget'):
            self.event.budget.update_totals()

    def delete(self, *args, **kwargs):
        event = self.event
        super().delete(*args, **kwargs)
        if hasattr(event, 'budget'):
            event.budget.update_totals()
