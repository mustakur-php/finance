from django import forms
from .models import CommissionSheet, CommissionEntry
from clients.models import Client
from accounts.models import User
import datetime


class CommissionSheetForm(forms.ModelForm):
    class Meta:
        model = CommissionSheet
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثال: عمولات يناير 2025'}),
        }
        labels = {
            'name': 'اسم الشيت',
        }


class CommissionEntryForm(forms.ModelForm):
    class Meta:
        model = CommissionEntry
        fields = ['client', 'entry_date', 'amount', 'notes']
        widgets = {
            'client': forms.Select(attrs={'class': 'form-select'}),
            'entry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
        labels = {
            'client': 'العميل',
            'entry_date': 'تاريخ السطر',
            'amount': 'المبلغ',
            'notes': 'ملاحظات',
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['client'].queryset = Client.objects.filter(tenant=tenant, is_active=True).order_by('name')
        if not self.instance.pk:
            self.fields['entry_date'].initial = datetime.date.today()
