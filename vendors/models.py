from django.db import models
from events.models import Event

class Vendor(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Pending', 'Pending'),
    ]

    SERVICE_CHOICES = [
        ('Catering', 'Catering & Hospitality'),
        ('Audio/Visual', 'AV & Production'),
        ('Staging & Lighting', 'Stage & Rigging'),
        ('Security', 'Security & Logistics'),
        ('Photography', 'Photography & Media'),
        ('Janitorial', 'Facilities & Sanitation'),
        ('Decor & Furniture', 'Decor & Furniture'),
        ('Logistics & Transport', 'Logistics & Transport'),
        ('Other', 'Other'),
    ]

    SLA_CHOICES = [
        ('Cleared', 'Cleared (Insured & Active)'),
        ('Expiring Soon', 'Expiring Soon (< 30d)'),
        ('Pending Renewal', 'Pending Renewal'),
    ]

    vendor_id = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    service_type = models.CharField(max_length=100, choices=SERVICE_CHOICES, default='Other')
    contact_person = models.CharField(max_length=255)
    phone = models.CharField(max_length=50)
    email = models.EmailField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    tier = models.CharField(max_length=50, default='Tier 1')
    sla_status = models.CharField(max_length=50, choices=SLA_CHOICES, default='Cleared')
    coi_expiry = models.DateField(null=True, blank=True)
    active_event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_vendors')
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.vendor_id} - {self.name} ({self.service_type})"

    @property
    def initials(self):
        words = self.name.split()
        if len(words) >= 2:
            return f"{words[0][0]}{words[1][0]}".upper()
        elif words:
            return words[0][:2].upper()
        return "VN"

    @property
    def total_po_amount(self):
        total = sum(exp.amount for exp in self.expenses.all())
        return total


class VendorDispatch(models.Model):
    STATUS_CHOICES = [
        ('Cleared Dock', 'Cleared Dock'),
        ('In Transit', 'In Transit'),
        ('Awaiting Escort', 'Awaiting Escort'),
        ('Dispatched', 'Dispatched'),
    ]

    dispatch_id = models.CharField(max_length=50, unique=True, db_index=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='dispatches')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='vendor_dispatches')
    dock_bay = models.CharField(max_length=100, default='Bay 3 Freight')
    call_time = models.CharField(max_length=50, default='07:00 AM EDT')
    crew_passes = models.PositiveIntegerField(default=10)
    vehicles = models.PositiveIntegerField(default=2)
    po_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Cleared Dock')
    pass_number = models.CharField(max_length=50, default='DK-9812')
    lead_name = models.CharField(max_length=255, blank=True, default='')
    dispatched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-dispatched_at']

    def __str__(self):
        return f"{self.dispatch_id}: {self.vendor.name} -> {self.event.name}"
