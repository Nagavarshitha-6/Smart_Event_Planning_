from django import forms
from django.core.exceptions import ValidationError
from .models import Registration
from events.models import Event
import random
import string

class RegistrationForm(forms.ModelForm):
    class Meta:
        model = Registration
        fields = [
            'event',
            'name',
            'email',
            'phone',
            'ticket_id',
            'status',
        ]
        widgets = {
            'event': forms.Select(attrs={
                'class': 'form-stitch-control'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-stitch-control',
                'placeholder': 'Full Legal Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-stitch-control',
                'placeholder': 'attendee@institution.edu'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-stitch-control font-mono-data',
                'placeholder': '+1 (555) 000-0000'
            }),
            'ticket_id': forms.TextInput(attrs={
                'class': 'form-stitch-control font-mono-data',
                'placeholder': 'Auto-generated or custom ticket code'
            }),
            'status': forms.Select(attrs={
                'class': 'form-stitch-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter only active/upcoming events by default
        self.fields['event'].queryset = Event.objects.exclude(status='Cancelled').order_by('date')
        if not self.instance.pk and not self.initial.get('ticket_id'):
            # Auto-generate unique ticket code
            rand_code = ''.join(random.choices(string.digits, k=4))
            self.fields['ticket_id'].initial = f"TKT-{rand_code}"

    def clean(self):
        cleaned_data = super().clean()
        event = cleaned_data.get('event')
        email = cleaned_data.get('email')

        # Check duplicate registration for the same event unless editing current instance
        if event and email:
            qs = Registration.objects.filter(event=event, email__iexact=email)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(f"An attendee with email '{email}' is already registered for '{event.name}'.")

        # Capacity check on new registrations
        if not self.instance.pk and event:
            if event.capacity > 0 and event.registered_count >= event.capacity:
                raise ValidationError(f"Event '{event.name}' has reached its maximum authorized capacity of {event.capacity} attendees.")

        return cleaned_data
