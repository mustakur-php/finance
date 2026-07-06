from django.contrib.auth.models import AbstractUser
from django.db import models


class Tenant(models.Model):
    PLAN_MONTHLY  = 'monthly'
    PLAN_YEARLY   = 'yearly'
    PLAN_CUSTOM   = 'custom'
    PLAN_CHOICES  = [
        (PLAN_MONTHLY, 'شهري'),
        (PLAN_YEARLY,  'سنوي'),
        (PLAN_CUSTOM,  'مخصص'),
    ]

    # معلومات الشركة
    name             = models.CharField(max_length=200, verbose_name='اسم الشركة')
    slug             = models.SlugField(unique=True)
    phone            = models.CharField(max_length=30, blank=True, verbose_name='الهاتف')
    email            = models.EmailField(blank=True, verbose_name='البريد الإلكتروني')
    address          = models.TextField(blank=True, verbose_name='العنوان')
    contact_person   = models.CharField(max_length=200, blank=True, verbose_name='المسؤول')

    # الاشتراك
    subscription_plan  = models.CharField(max_length=20, choices=PLAN_CHOICES, default=PLAN_MONTHLY, verbose_name='نوع الاشتراك')
    subscription_start = models.DateField(null=True, blank=True, verbose_name='بداية الاشتراك')
    subscription_end   = models.DateField(null=True, blank=True, verbose_name='نهاية الاشتراك')
    max_users          = models.PositiveIntegerField(default=10, verbose_name='الحد الأقصى للمستخدمين')

    is_active  = models.BooleanField(default=True, verbose_name='نشط')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    @property
    def is_expired(self):
        if not self.subscription_end:
            return False
        from django.utils import timezone
        return timezone.localdate() > self.subscription_end

    @property
    def days_remaining(self):
        if not self.subscription_end:
            return None
        from django.utils import timezone
        delta = (self.subscription_end - timezone.localdate()).days
        return delta

    class Meta:
        verbose_name = 'شركة'
        verbose_name_plural = 'الشركات'


class User(AbstractUser):
    ROLE_ADMIN = 'admin'
    ROLE_SALES = 'sales'
    ROLE_ACCOUNTANT = 'accountant'
    ROLE_REVIEW = 'review'

    ROLE_CHOICES = [
        (ROLE_ADMIN, 'أدمن'),
        (ROLE_SALES, 'مندوب'),
        (ROLE_ACCOUNTANT, 'محاسب'),
        (ROLE_REVIEW, 'مراجعة'),
    ]

    tenant       = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True, related_name='users')
    role         = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_SALES)
    is_superadmin = models.BooleanField(default=False, verbose_name='سوبر أدمن')
    phone = models.CharField(max_length=20, blank=True)
    whatsapp_number = models.CharField(max_length=20, blank=True, verbose_name='رقم الواتساب',
                                        help_text='مثال: 966501234567 (بدون + أو 00)')
    callmebot_api_key = models.CharField(max_length=100, blank=True, verbose_name='CallMeBot API Key')

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    @property
    def is_sales(self):
        return self.role == self.ROLE_SALES

    @property
    def is_accountant(self):
        return self.role == self.ROLE_ACCOUNTANT

    @property
    def is_review(self):
        return self.role == self.ROLE_REVIEW

    class Meta:
        verbose_name = 'مستخدم'
        verbose_name_plural = 'المستخدمون'
