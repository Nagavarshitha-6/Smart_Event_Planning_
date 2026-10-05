from django.db import models
from decimal import Decimal
from events.models import Event

class Budget(models.Model):
    STATUS_CHOICES = [
        ('Within Budget', 'Within Budget'),
        ('Near Limit', 'Near Limit'),
        ('Exceeded', 'Exceeded'),
    ]

    budget_id = models.CharField(max_length=50, unique=True, db_index=True)
    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name='budget')
    department = models.CharField(max_length=100, default='Academic Operations', blank=True)
    fiscal_year = models.CharField(max_length=20, default='FY 2026')
    allocated_amount = models.DecimalField(max_digits=12, decimal_places=2)
    spent_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    remaining_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Within Budget')
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_date']

    def __str__(self):
        return f"{self.budget_id} - {self.event.name} (${self.allocated_amount})"

    @property
    def utilization_percentage(self):
        if self.allocated_amount and self.allocated_amount > Decimal('0.00'):
            pct = (self.spent_amount / self.allocated_amount) * Decimal('100.0')
            return min(round(float(pct), 1), 100.0)
        return 0.0

    def update_totals(self):
        """
        Calculates spent amount from associated expenses and updates remaining amount and status.
        """
        total_spent = sum((exp.amount for exp in self.event.expenses.exclude(payment_status='Cancelled')), Decimal('0.00'))
        self.spent_amount = total_spent
        self.remaining_amount = self.allocated_amount - total_spent

        if self.allocated_amount > Decimal('0.00'):
            ratio = total_spent / self.allocated_amount
            if ratio > Decimal('1.00'):
                self.status = 'Exceeded'
            elif ratio >= Decimal('0.85'):
                self.status = 'Near Limit'
            else:
                self.status = 'Within Budget'
        self.save()
