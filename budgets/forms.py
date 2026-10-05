from django import forms
from decimal import Decimal
from events.models import Event
from vendors.models import Vendor
from expenses.models import Expense
from budgets.models import Budget

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = [
            'expense_id',
            'event',
            'category',
            'description',
            'amount',
            'date',
            'vendor',
            'payment_status',
            'receipt_ref',
            'is_authorized'
        ]
        widgets = {
            'expense_id': forms.TextInput(attrs={
                'class': 'form-control font-mono-data',
                'placeholder': 'EXP-8821'
            }),
            'event': forms.Select(attrs={
                'class': 'form-select'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'e.g. 4K Laser Projector Rigging Lease for Hall C Truss Grid'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control font-mono-data',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'vendor': forms.Select(attrs={
                'class': 'form-select'
            }),
            'payment_status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'receipt_ref': forms.TextInput(attrs={
                'class': 'form-control font-mono-data',
                'placeholder': 'INV-441.pdf or PO-8920'
            }),
            'is_authorized': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= Decimal('0.00'):
            raise forms.ValidationError("Expense amount must be greater than zero.")
        return amount

class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = [
            'budget_id',
            'event',
            'department',
            'fiscal_year',
            'allocated_amount'
        ]
        widgets = {
            'budget_id': forms.TextInput(attrs={
                'class': 'form-control font-mono-data',
                'placeholder': 'BDG-2026-001'
            }),
            'event': forms.Select(attrs={
                'class': 'form-select'
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. CS & Engineering Dept'
            }),
            'fiscal_year': forms.TextInput(attrs={
                'class': 'form-control font-mono-data',
                'placeholder': 'FY 2026'
            }),
            'allocated_amount': forms.NumberInput(attrs={
                'class': 'form-control font-mono-data',
                'step': '0.01',
                'placeholder': '50000.00'
            })
        }

    def clean_allocated_amount(self):
        allocated = self.cleaned_data.get('allocated_amount')
        if allocated is not None and allocated <= Decimal('0.00'):
            raise forms.ValidationError("Allocated budget pool must be positive.")
        return allocated

class RebalanceFundsForm(forms.Form):
    source_budget = forms.ModelChoiceField(
        queryset=Budget.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select font-mono-data'}),
        label="Source Account (Surplus)"
    )
    target_budget = forms.ModelChoiceField(
        queryset=Budget.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select font-mono-data'}),
        label="Target Account (Deficit / Overrun)"
    )
    transfer_amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('1.00'),
        widget=forms.NumberInput(attrs={'class': 'form-control font-mono-data', 'placeholder': '5000.00'}),
        label="Transfer Amount (USD)"
    )
    justification = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Approved shift for overflow AV tech'}),
        label="Audit Justification"
    )

    def clean(self):
        cleaned_data = super().clean()
        source = cleaned_data.get('source_budget')
        target = cleaned_data.get('target_budget')
        amount = cleaned_data.get('transfer_amount')

        if source and target and source == target:
            raise forms.ValidationError("Source and target budget accounts must be different.")

        if source and amount:
            if source.remaining_amount < amount:
                raise forms.ValidationError(
                    f"Insufficient surplus in {source.event.name}. Available: ${source.remaining_amount:,.2f}"
                )
        return cleaned_data
