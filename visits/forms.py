from django import forms
from .models import Visit
from clients.models import Client


class VisitForm(forms.ModelForm):
    class Meta:
        model = Visit
        fields = ['client', 'visit_date', 'purpose', 'status', 'notes', 'result']
        widgets = {
            'client': forms.Select(attrs={'class': 'form-select'}),
            'visit_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'purpose': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'result': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and user.tenant:
            qs = Client.objects.filter(tenant=user.tenant, is_active=True)
            if user.is_sales:
                qs = qs.filter(assigned_sales=user)
            self.fields['client'].queryset = qs
