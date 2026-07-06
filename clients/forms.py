from django import forms
from .models import Client, ClientNote, Activity
from accounts.models import User

SAUDI_CITIES = [
    ('', '-- اختر المدينة --'),
    # منطقة الرياض
    ('الرياض', 'الرياض'),
    ('الخرج', 'الخرج'),
    ('المجمعة', 'المجمعة'),
    ('الزلفي', 'الزلفي'),
    ('الدوادمي', 'الدوادمي'),
    ('القويعية', 'القويعية'),
    ('وادي الدواسر', 'وادي الدواسر'),
    ('الأفلاج', 'الأفلاج'),
    ('حوطة بني تميم', 'حوطة بني تميم'),
    ('ضرما', 'ضرما'),
    ('الدرعية', 'الدرعية'),
    # منطقة مكة المكرمة
    ('مكة المكرمة', 'مكة المكرمة'),
    ('جدة', 'جدة'),
    ('الطائف', 'الطائف'),
    ('رابغ', 'رابغ'),
    ('القنفذة', 'القنفذة'),
    ('الليث', 'الليث'),
    ('خليص', 'خليص'),
    ('الجموم', 'الجموم'),
    # منطقة المدينة المنورة
    ('المدينة المنورة', 'المدينة المنورة'),
    ('ينبع', 'ينبع'),
    ('العلا', 'العلا'),
    ('بدر', 'بدر'),
    ('المهد', 'المهد'),
    ('الحناكية', 'الحناكية'),
    # منطقة القصيم
    ('بريدة', 'بريدة'),
    ('عنيزة', 'عنيزة'),
    ('الرس', 'الرس'),
    ('البكيرية', 'البكيرية'),
    ('المذنب', 'المذنب'),
    ('عيون الجواء', 'عيون الجواء'),
    # المنطقة الشرقية
    ('الدمام', 'الدمام'),
    ('الخبر', 'الخبر'),
    ('الاحساء', 'الاحساء'),
    ('الجبيل', 'الجبيل'),
    ('القطيف', 'القطيف'),
    ('حفر الباطن', 'حفر الباطن'),
    ('الخفجي', 'الخفجي'),
    ('بقيق', 'بقيق'),
    ('راس تنورة', 'راس تنورة'),
    # منطقة عسير
    ('ابها', 'ابها'),
    ('خميس مشيط', 'خميس مشيط'),
    ('بيشة', 'بيشة'),
    ('النماص', 'النماص'),
    ('محايل عسير', 'محايل عسير'),
    ('سراة عبيدة', 'سراة عبيدة'),
    ('تثليث', 'تثليث'),
    # منطقة تبوك
    ('تبوك', 'تبوك'),
    ('الوجه', 'الوجه'),
    ('ضبا', 'ضبا'),
    ('املج', 'املج'),
    ('تيماء', 'تيماء'),
    # منطقة حائل
    ('حائل', 'حائل'),
    ('بقعاء', 'بقعاء'),
    ('الغزالة', 'الغزالة'),
    # منطقة الحدود الشمالية
    ('عرعر', 'عرعر'),
    ('رفحاء', 'رفحاء'),
    ('طريف', 'طريف'),
    # منطقة جازان
    ('جازان', 'جازان'),
    ('صبيا', 'صبيا'),
    ('ابو عريش', 'ابو عريش'),
    ('صامطة', 'صامطة'),
    ('العارضة', 'العارضة'),
    # منطقة نجران
    ('نجران', 'نجران'),
    ('شرورة', 'شرورة'),
    # منطقة الباحة
    ('الباحة', 'الباحة'),
    ('بلجرشي', 'بلجرشي'),
    # منطقة الجوف
    ('سكاكا', 'سكاكا'),
    ('دومة الجندل', 'دومة الجندل'),
    ('القريات', 'القريات'),
]


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['name', 'company', 'city', 'district', 'address', 'phone', 'email',
                  'responsible_person', 'job_title', 'activity', 'notes',
                  'assigned_sales', 'assigned_accountant', 'assigned_review',
                  'is_commissionable']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'company': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.Select(choices=SAUDI_CITIES, attrs={'class': 'form-select'}),
            'district': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'responsible_person': forms.TextInput(attrs={'class': 'form-control'}),
            'job_title': forms.TextInput(attrs={'class': 'form-control'}),
            'activity': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'assigned_sales': forms.Select(attrs={'class': 'form-select'}),
            'assigned_accountant': forms.Select(attrs={'class': 'form-select'}),
            'assigned_review': forms.Select(attrs={'class': 'form-select'}),
            'is_commissionable': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and user.tenant:
            self.fields['activity'].queryset = Activity.objects.filter(
                tenant=user.tenant, is_active=True)
            self.fields['activity'].empty_label = '-- اختر النشاط --'
            if user.is_admin:
                self.fields['assigned_sales'].queryset = User.objects.filter(
                    tenant=user.tenant, role=User.ROLE_SALES, is_active=True)
                self.fields['assigned_accountant'].queryset = User.objects.filter(
                    tenant=user.tenant, role=User.ROLE_ACCOUNTANT, is_active=True)
                self.fields['assigned_review'].queryset = User.objects.filter(
                    tenant=user.tenant, role=User.ROLE_REVIEW, is_active=True)
            else:
                self.fields.pop('assigned_sales', None)
                self.fields.pop('assigned_accountant', None)
                self.fields.pop('assigned_review', None)


class ClientNoteForm(forms.ModelForm):
    class Meta:
        model = ClientNote
        fields = ['note']
        widgets = {'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'اضف ملاحظة...'})}
