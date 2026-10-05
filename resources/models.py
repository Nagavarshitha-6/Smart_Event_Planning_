from django.db import models
from django.contrib.auth.models import User
from events.models import Event

class Resource(models.Model):
    STATUS_CHOICES = [
        ('Available', 'Available'),
        ('Assigned', 'Assigned'),
        ('Maintenance', 'Maintenance'),
    ]

    RESOURCE_TYPE_CHOICES = [
        ('Auditorium', 'Auditorium'),
        ('Classroom', 'Classroom'),
        ('Projector', 'Projector'),
        ('Microphone', 'Microphone'),
        ('Sound System', 'Sound System'),
        ('LED Screen', 'LED Screen'),
        ('Camera', 'Camera'),
        ('Generator', 'Generator'),
        ('Tables', 'Tables'),
        ('Chairs', 'Chairs'),
        ('Other', 'Other'),
    ]

    resource_id = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    resource_type = models.CharField(max_length=100, choices=RESOURCE_TYPE_CHOICES, default='Other')
    quantity = models.PositiveIntegerField(default=1)
    location = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Available', db_index=True)
    description = models.TextField(blank=True)
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['resource_type', 'name']

    def __str__(self):
        return f"{self.resource_id} - {self.name} ({self.resource_type})"


class ResourceAllocation(models.Model):
    STATUS_CHOICES = [
        ('Confirmed', 'Confirmed'),
        ('Pending', 'Pending'),
        ('Released', 'Released'),
        ('Conflicted', 'Conflicted'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='resource_allocations')
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='allocations')
    quantity = models.PositiveIntegerField(default=1)
    date = models.DateField(db_index=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Confirmed')
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.resource.name} -> {self.event.name} on {self.date}"


class ResourceConflict(models.Model):
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='conflicts')
    event_a = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='conflicts_as_a')
    event_b = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='conflicts_as_b')
    conflict_date = models.DateField(db_index=True)
    time_a = models.CharField(max_length=100)
    time_b = models.CharField(max_length=100)
    description = models.TextField()
    is_resolved = models.BooleanField(default=False, db_index=True)
    detected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-detected_at']

    def __str__(self):
        return f"Conflict on {self.resource.name} ({self.conflict_date}) between {self.event_a.event_id} and {self.event_b.event_id}"
