from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Event(models.Model):
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Upcoming', 'Upcoming'),
        ('Ongoing', 'Ongoing'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    CATEGORY_CHOICES = [
        ('Academic', 'Academic'),
        ('Conference', 'Conference'),
        ('Gala', 'Gala'),
        ('Career', 'Career'),
        ('Student Life', 'Student Life'),
        ('Workshop', 'Workshop'),
        ('Athletics', 'Athletics'),
        ('Other', 'Other'),
    ]

    event_id = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Academic')
    date = models.DateField(db_index=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    venue = models.CharField(max_length=255)
    capacity = models.PositiveIntegerField(default=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft', db_index=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_events')
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'start_time']
        indexes = [
            models.Index(fields=['status', 'date']),
        ]

    def __str__(self):
        return f"{self.event_id} - {self.name}"

    @property
    def registered_count(self):
        return self.registrations.filter(status__in=['Registered', 'Checked In']).count()

    @property
    def capacity_percentage(self):
        if self.capacity > 0:
            return min(100, round((self.registered_count / self.capacity) * 100))
        return 0
