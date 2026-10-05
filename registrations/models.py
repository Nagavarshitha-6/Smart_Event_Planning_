from django.db import models
from events.models import Event

class Registration(models.Model):
    STATUS_CHOICES = [
        ('Registered', 'Registered'),
        ('Checked In', 'Checked In'),
        ('Cancelled', 'Cancelled'),
    ]

    registration_id = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    ticket_id = models.CharField(max_length=50, unique=True, db_index=True)
    registration_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Registered', db_index=True)

    class Meta:
        ordering = ['-registration_date']
        constraints = [
            models.UniqueConstraint(fields=['event', 'email'], name='unique_event_attendee_registration')
        ]

    def __str__(self):
        return f"{self.ticket_id} - {self.name} ({self.event.name})"
