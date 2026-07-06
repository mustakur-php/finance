from django import forms
from .models import Event
from clients.models import Client
from accounts.models import User


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'event_type', 'source', 'client', 'assigned_to', 'start_datetime', 'notes']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'event_type': forms.Select(attrs={'class': 'form-select'}),
            'source': forms.Select(attrs={'class': 'form-select'}),
            'client': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'start_datetime': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and user.tenant:
            self.fields['client'].queryset = Client.objects.filter(tenant=user.tenant, is_active=True)
            self.fields['client'].required = False
            if user.is_admin:
                self.fields['assigned_to'].queryset = User.objects.filter(tenant=user.tenant, is_active=True)
            else:
                self.fields.pop('source')
                self.fields.pop('assigned_to')
