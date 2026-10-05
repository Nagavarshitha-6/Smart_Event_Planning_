from django.db import models
from django.contrib.auth.models import User
from registrations.models import Registration

class Attendance(models.Model):
    registration = models.OneToOneField(Registration, on_delete=models.CASCADE, related_name='attendance_record')
    ticket_id = models.CharField(max_length=50, db_index=True)
    check_in_time = models.DateTimeField(auto_now_add=True, db_index=True)
    checked_in_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        ordering = ['-check_in_time']

    def __str__(self):
        return f"Checked In: {self.ticket_id} at {self.check_in_time.strftime('%Y-%m-%d %H:%M')}"
