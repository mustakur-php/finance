from django import forms
from django.contrib.auth.password_validation import validate_password
from .models import User


class LoginForm(forms.Form):
    username = forms.CharField(label='اسم المستخدم', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم المستخدم'}))
    password = forms.CharField(label='كلمة المرور', widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'كلمة المرور'}))


class UserForm(forms.ModelForm):
    password = forms.CharField(label='كلمة المرور',
                                widget=forms.PasswordInput(attrs={'class': 'form-control'}),
                                required=False,
                                help_text='مطلوب عند الإنشاء — اتركه فارغاً إذا لا تريد تغييره عند التعديل')

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'role', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.tenant = tenant
        if not self.instance.pk:
            self.fields['password'].required = True
            self.fields['password'].help_text = 'مطلوب'

    def clean(self):
        cleaned_data = super().clean()
        if not self.instance.pk and not cleaned_data.get('password'):
            self.add_error('password', 'كلمة المرور مطلوبة عند إنشاء مستخدم جديد')
        return cleaned_data


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'first_name': 'الاسم الأول',
            'last_name': 'الاسم الأخير',
            'email': 'البريد الإلكتروني',
            'phone': 'رقم الجوال',
        }


class ChangePasswordForm(forms.Form):
    current_password = forms.CharField(
        label='كلمة المرور الحالية',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    new_password = forms.CharField(
        label='كلمة المرور الجديدة',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    confirm_password = forms.CharField(
        label='تأكيد كلمة المرور الجديدة',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_current_password(self):
        current = self.cleaned_data.get('current_password')
        if not self.user.check_password(current):
            raise forms.ValidationError('كلمة المرور الحالية غير صحيحة')
        return current

    def clean(self):
        cleaned_data = super().clean()
        new = cleaned_data.get('new_password')
        confirm = cleaned_data.get('confirm_password')
        if new and confirm and new != confirm:
            self.add_error('confirm_password', 'كلمتا المرور غير متطابقتين')
        if new:
            try:
                validate_password(new, self.user)
            except Exception as e:
                self.add_error('new_password', list(e.messages))
        return cleaned_data
