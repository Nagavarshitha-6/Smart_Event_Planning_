from django import forms
from django.core.exceptions import ValidationError
import random
import string

from .models import Vendor, VendorDispatch
from events.models import Event

class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = [
            'vendor_id',
            'name',
            'service_type',
            'contact_person',
            'phone',
            'email',
            'status',
            'tier',
            'sla_status',
            'coi_expiry',
            'active_event',
        ]
        widgets = {
            'vendor_id': forms.TextInput(attrs={
                'class': 'form-stitch-control font-mono-data',
                'placeholder': 'e.g. VND-401'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-stitch-control',
                'placeholder': 'Company or Provider Legal Name'
            }),
            'service_type': forms.Select(attrs={
                'class': 'form-stitch-control'
            }),
            'contact_person': forms.TextInput(attrs={
                'class': 'form-stitch-control',
                'placeholder': 'Primary Account Executive / Lead'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-stitch-control font-mono-data',
                'placeholder': '+1 (555) 000-0000'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-stitch-control',
                'placeholder': 'dispatch@provider.com'
            }),
            'status': forms.Select(attrs={
                'class': 'form-stitch-control'
            }),
            'tier': forms.Select(attrs={
                'class': 'form-stitch-control'
            }, choices=[('Tier 1', 'Tier 1 Preferred'), ('Tier 2', 'Tier 2 Approved'), ('Tier 3', 'Tier 3 Provisional')]),
            'sla_status': forms.Select(attrs={
                'class': 'form-stitch-control'
            }),
            'coi_expiry': forms.DateInput(attrs={
                'class': 'form-stitch-control font-mono-data',
                'type': 'date'
            }),
            'active_event': forms.Select(attrs={
                'class': 'form-stitch-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['active_event'].required = False
        self.fields['active_event'].queryset = Event.objects.exclude(status='Cancelled').order_by('date')
        if not self.instance.pk and not self.initial.get('vendor_id'):
            rand_num = random.randint(100, 999)
            self.fields['vendor_id'].initial = f"VND-{rand_num}"


class VendorDispatchForm(forms.ModelForm):
    class Meta:
        model = VendorDispatch
        fields = [
            'vendor',
            'event',
            'dock_bay',
            'call_time',
            'crew_passes',
            'vehicles',
            'po_amount',
            'status',
            'lead_name',
        ]
        widgets = {
            'vendor': forms.Select(attrs={'class': 'form-stitch-control', 'id': 'dispatchVendorSelect'}),
            'event': forms.Select(attrs={'class': 'form-stitch-control', 'id': 'dispatchTargetEventSelect'}),
            'dock_bay': forms.TextInput(attrs={'class': 'form-stitch-control', 'placeholder': 'e.g. Bay 3 Freight'}),
            'call_time': forms.TextInput(attrs={'class': 'form-stitch-control font-mono-data', 'placeholder': 'e.g. 07:00 AM EDT'}),
            'crew_passes': forms.NumberInput(attrs={'class': 'form-stitch-control font-mono-data'}),
            'vehicles': forms.NumberInput(attrs={'class': 'form-stitch-control font-mono-data'}),
            'po_amount': forms.NumberInput(attrs={'class': 'form-stitch-control font-mono-data', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-stitch-control'}),
            'lead_name': forms.TextInput(attrs={'class': 'form-stitch-control', 'placeholder': 'Designated Lead Onsite'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['event'].queryset = Event.objects.exclude(status='Cancelled').order_by('date')
        self.fields['vendor'].queryset = Vendor.objects.filter(status='Active').order_by('name')
