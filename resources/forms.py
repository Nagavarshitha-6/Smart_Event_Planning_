from django import forms
from django.core.exceptions import ValidationError
import random

from .models import Resource, ResourceAllocation
from events.models import Event

class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = [
            'resource_id',
            'name',
            'resource_type',
            'quantity',
            'location',
            'status',
            'description',
        ]
        widgets = {
            'resource_id': forms.TextInput(attrs={
                'class': 'form-stitch-control font-mono-data',
                'placeholder': 'e.g. RES-AUD-04'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-stitch-control',
                'placeholder': 'Descriptive Asset Name'
            }),
            'resource_type': forms.Select(attrs={
                'class': 'form-stitch-control'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-stitch-control font-mono-data',
                'min': '1'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-stitch-control',
                'placeholder': 'Building / Wing / Depot Bay'
            }),
            'status': forms.Select(attrs={
                'class': 'form-stitch-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-stitch-control',
                'rows': 3,
                'placeholder': 'Hardware specifications, rigging requirements, or serial info.'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk and not self.initial.get('resource_id'):
            rand_code = random.randint(100, 999)
            self.fields['resource_id'].initial = f"RES-NEW-{rand_code}"


class ResourceAllocationForm(forms.ModelForm):
    class Meta:
        model = ResourceAllocation
        fields = [
            'event',
            'resource',
            'quantity',
            'date',
            'start_time',
            'end_time',
            'status',
        ]
        widgets = {
            'event': forms.Select(attrs={'class': 'form-stitch-control'}),
            'resource': forms.Select(attrs={'class': 'form-stitch-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-stitch-control font-mono-data', 'min': '1'}),
            'date': forms.DateInput(attrs={'class': 'form-stitch-control font-mono-data', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-stitch-control font-mono-data', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-stitch-control font-mono-data', 'type': 'time'}),
            'status': forms.Select(attrs={'class': 'form-stitch-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['event'].queryset = Event.objects.exclude(status='Cancelled').order_by('date')
        self.fields['resource'].queryset = Resource.objects.exclude(status='Maintenance').order_by('name')

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')
        if start and end and start >= end:
            raise ValidationError("End time must be strictly after start time.")
        return cleaned_data
