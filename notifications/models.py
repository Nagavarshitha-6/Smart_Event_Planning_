from django.db import models

class Notification(models.Model):
    TYPE_CHOICES = [
        ('conflict', 'Resource Conflict'),
        ('registration', 'New Registration'),
        ('event', 'Event Approaching'),
        ('vendor', 'Vendor Assigned'),
        ('budget', 'Budget Threshold Warning'),
        ('maintenance', 'Resource Maintenance'),
        ('general', 'General Alert'),
    ]

    SEVERITY_CHOICES = [
        ('critical', 'Critical'),
        ('warning', 'Warning'),
        ('info', 'Info'),
        ('success', 'Success'),
    ]

    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default='general')
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='info')
    source_code = models.CharField(max_length=50, default='SYSTEM', blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    link_url = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.severity.upper()} | {self.source_code}] {self.title}"
