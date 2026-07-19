from django import forms
from .models import Event
from clients.models import Client
from accounts.models import User


def _label(obj):
    company = getattr(obj, 'company', '') or ''
    return f'{obj.name} — {company}' if company else obj.name


def build_client_choices(tenant):
    """قائمة العملاء من كل الأقسام مجمّعة، بقيم على شكل 'قسم:رقم'."""
    from workflow.models import ReviewClient
    from zatca.models import ZatcaClient

    actual, targeted = [], []
    for c in Client.objects.filter(tenant=tenant, is_active=True).order_by('name'):
        bucket = actual if c.client_type == Client.TYPE_ACTUAL else targeted
        bucket.append((f'client:{c.pk}', _label(c)))

    review = [(f'review:{c.pk}', _label(c))
              for c in ReviewClient.objects.filter(tenant=tenant).order_by('name')]
    zatca = [(f'zatca:{c.pk}', _label(c))
             for c in ZatcaClient.objects.filter(tenant=tenant).order_by('name')]

    choices = [('', '— بدون عميل —')]
    if actual:
        choices.append(('العملاء الفعليون', actual))
    if targeted:
        choices.append(('العملاء المستهدفون', targeted))
    if review:
        choices.append(('قسم المراجعة', review))
    if zatca:
        choices.append(('قسم ZATCA', zatca))
    return choices


class EventForm(forms.ModelForm):
    client_ref = forms.ChoiceField(
        label='العميل', required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = Event
        fields = ['title', 'event_type', 'source', 'assigned_to', 'start_datetime', 'notes']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'event_type': forms.Select(attrs={'class': 'form-select'}),
            'source': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'start_datetime': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and user.tenant:
            self.fields['client_ref'].choices = build_client_choices(user.tenant)
            if user.is_admin:
                self.fields['assigned_to'].queryset = User.objects.filter(tenant=user.tenant, is_active=True)
            else:
                self.fields.pop('source', None)
                self.fields.pop('assigned_to', None)

        # تعبئة الاختيار الحالي عند التعديل
        inst = self.instance
        if inst and inst.pk and not self.data:
            if inst.client_id:
                self.fields['client_ref'].initial = f'client:{inst.client_id}'
            elif inst.review_client_id:
                self.fields['client_ref'].initial = f'review:{inst.review_client_id}'
            elif inst.zatca_client_id:
                self.fields['client_ref'].initial = f'zatca:{inst.zatca_client_id}'

    def save(self, commit=True):
        event = super().save(commit=False)
        ref = self.cleaned_data.get('client_ref') or ''
        event.client = None
        event.review_client = None
        event.zatca_client = None
        if ':' in ref:
            kind, pk = ref.split(':', 1)
            if kind == 'client':
                event.client_id = pk
            elif kind == 'review':
                event.review_client_id = pk
            elif kind == 'zatca':
                event.zatca_client_id = pk
        if commit:
            event.save()
        return event
