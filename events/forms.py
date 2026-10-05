from django import forms
from django.core.exceptions import ValidationError
from .models import Event
from datetime import date

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'event_id',
            'name',
            'description',
            'category',
            'date',
            'start_time',
            'end_time',
            'venue',
            'capacity',
            'status',
        ]
        widgets = {
            'event_id': forms.TextInput(attrs={
                'class': 'form-stitch-control font-mono-data',
                'placeholder': 'e.g. EVT-2026-107'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-stitch-control',
                'placeholder': 'Event Name or Title'
            }),
            'category': forms.Select(attrs={
                'class': 'form-stitch-control'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-stitch-control font-mono-data',
                'type': 'date'
            }),
            'start_time': forms.TimeInput(attrs={
                'class': 'form-stitch-control font-mono-data',
                'type': 'time'
            }),
            'end_time': forms.TimeInput(attrs={
                'class': 'form-stitch-control font-mono-data',
                'type': 'time'
            }),
            'venue': forms.TextInput(attrs={
                'class': 'form-stitch-control',
                'placeholder': 'e.g. Main Hall A, Science Amphitheater'
            }),
            'capacity': forms.NumberInput(attrs={
                'class': 'form-stitch-control font-mono-data',
                'min': '1',
                'placeholder': 'e.g. 500'
            }),
            'status': forms.Select(attrs={
                'class': 'form-stitch-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-stitch-control',
                'rows': 4,
                'placeholder': 'Comprehensive event overview, logistical requirements, and target audience...'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        event_date = cleaned_data.get('date')
        capacity = cleaned_data.get('capacity')

        if start_time and end_time:
            if end_time <= start_time:
                raise ValidationError({'end_time': 'Event end time must be chronologically after the start time.'})

        if capacity is not None and capacity <= 0:
            raise ValidationError({'capacity': 'Event capacity must be at least 1 attendee.'})

        return cleaned_data
