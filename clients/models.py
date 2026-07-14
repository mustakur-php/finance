from django.db import models
from django.conf import settings


class Activity(models.Model):
    tenant = models.ForeignKey('accounts.Tenant', on_delete=models.CASCADE, related_name='activities')
    name = models.CharField(max_length=200, verbose_name='اسم النشاط')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'نشاط'
        verbose_name_plural = 'الأنشطة'
        ordering = ['name']


class Client(models.Model):
    TYPE_ACTUAL = 'actual'
    TYPE_POTENTIAL = 'potential'
    TYPE_CHOICES = [
        (TYPE_ACTUAL, 'عميل فعلي'),
        (TYPE_POTENTIAL, 'عميل محتمل'),
    ]

    tenant = models.ForeignKey('accounts.Tenant', on_delete=models.CASCADE, related_name='clients')
    name = models.CharField(max_length=200, verbose_name='الاسم')
    company = models.CharField(max_length=200, blank=True, verbose_name='اسم الشركة')
    city = models.CharField(max_length=100, blank=True, verbose_name='المدينة')
    district = models.CharField(max_length=100, blank=True, verbose_name='الحي')
    address = models.TextField(blank=True, verbose_name='العنوان')
    phone = models.CharField(max_length=20, blank=True, verbose_name='رقم التواصل')
    email = models.EmailField(blank=True, verbose_name='البريد الإلكتروني')
    responsible_person = models.CharField(max_length=200, blank=True, verbose_name='المسئول')
    job_title = models.CharField(max_length=200, blank=True, verbose_name='الوظيفة')
    activity = models.ForeignKey(Activity, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='النشاط')
    client_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_POTENTIAL, verbose_name='نوع العميل')
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    assigned_sales = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='sales_clients',
                                        verbose_name='المندوب المسئول')
    assigned_accountant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                             null=True, blank=True, related_name='accountant_clients',
                                             verbose_name='المحاسب المسئول')
    assigned_review = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                         null=True, blank=True, related_name='review_clients',
                                         verbose_name='المراجع المسئول')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='created_clients',
                                    verbose_name='أضافه')
    CONVERTED_NONE = ''
    CONVERTED_ACTUAL = 'actual'
    CONVERTED_REVIEW = 'review'
    CONVERTED_CHOICES = [
        (CONVERTED_NONE,   'لم يُحوَّل'),
        (CONVERTED_ACTUAL, 'تم التحويل لعميل فعلي'),
        (CONVERTED_REVIEW, 'تم التحويل لقسم المراجعة'),
    ]
    converted_status = models.CharField(max_length=10, choices=CONVERTED_CHOICES, default=CONVERTED_NONE, blank=True, verbose_name='حالة التحويل')
    converted_at = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ التحويل')
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    is_commissionable = models.BooleanField(default=False, verbose_name='خاضع للعمولة')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.company}"

    class Meta:
        verbose_name = 'عميل'
        verbose_name_plural = 'العملاء'
        ordering = ['-created_at']


class ClientCommissionRule(models.Model):
    DEPT_SALES = 'sales'
    DEPT_ACCOUNTANT = 'accountant'
    DEPT_REVIEW = 'review'
    DEPT_CHOICES = [
        (DEPT_SALES, 'المناديب'),
        (DEPT_ACCOUNTANT, 'المحاسبين'),
        (DEPT_REVIEW, 'المراجعة'),
    ]
    TYPE_FIXED = 'fixed'
    TYPE_PERCENT = 'percent'
    TYPE_CHOICES = [
        (TYPE_FIXED, 'مبلغ ثابت'),
        (TYPE_PERCENT, 'نسبة مئوية'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='commission_rules')
    department = models.CharField(max_length=20, choices=DEPT_CHOICES, verbose_name='القسم')
    commission_type = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name='النوع')
    value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='القيمة')
    max_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='الحد الأعلى')
    reference_note = models.TextField(blank=True, verbose_name='المبلغ المرجعي / آلية الاحتساب')
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('client', 'department')
        verbose_name = 'قاعدة عمولة'
        verbose_name_plural = 'قواعد العمولات'

    def __str__(self):
        return f"{self.client.name} - {self.get_department_display()}"

    def get_summary(self):
        if self.commission_type == self.TYPE_FIXED:
            return f"{self.value} ريال"
        else:
            s = f"{self.value}%"
            if self.max_amount:
                s += f" (حد {self.max_amount} ريال)"
            return s


class ClientAttachment(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='clients/attachments/')
    name = models.CharField(max_length=200, verbose_name='اسم الملف')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'مرفق'
        verbose_name_plural = 'المرفقات'


class ClientNote(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='client_notes')
    note = models.TextField(verbose_name='الملاحظة')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ملاحظة - {self.client.name}"

    class Meta:
        verbose_name = 'ملاحظة'
        verbose_name_plural = 'الملاحظات'
        ordering = ['-created_at']
