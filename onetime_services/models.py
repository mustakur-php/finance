from django.db import models
from django.conf import settings


class OneTimeServiceClient(models.Model):
    """
    عميل خدمات لمرة واحدة — لا فترة متكررة (بعكس ZATCA)، كل خدمة تُفتح يدوياً
    بنوع جديد يُكتب حرّاً. العميل ينشط أثناء وجود خدمة تحت الإجراء، ويصبح
    غير نشط تلقائياً بعد إكمالها؛ إعادة التنشيط تعني فتح خدمة جديدة.
    """
    tenant             = models.ForeignKey('accounts.Tenant', on_delete=models.CASCADE, related_name='onetime_clients')
    source_client      = models.ForeignKey('clients.Client', on_delete=models.SET_NULL, null=True, blank=True,
                                            related_name='onetime_copies', verbose_name='العميل الأصلي')
    name               = models.CharField(max_length=200)
    company            = models.CharField(max_length=200, blank=True)
    phone              = models.CharField(max_length=30, blank=True)
    email              = models.EmailField(blank=True)
    city               = models.CharField(max_length=100, blank=True)
    district           = models.CharField(max_length=100, blank=True)
    address            = models.TextField(blank=True)
    responsible_person = models.CharField(max_length=100, blank=True)
    job_title          = models.CharField(max_length=100, blank=True)
    notes              = models.TextField(blank=True)
    distinguished_number = models.CharField(max_length=100, blank=True, verbose_name='الرقم المميز')
    secret_number         = models.CharField(max_length=100, blank=True, verbose_name='الرقم السري')
    is_active          = models.BooleanField(default=True, verbose_name='نشط')
    is_commissionable  = models.BooleanField(default=False, verbose_name='خاضع للعمولة')
    created_by         = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='created_onetime_clients'
    )
    created_at         = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'عميل خدمة لمرة واحدة'
        verbose_name_plural = 'عملاء الخدمات لمرة واحدة'

    def __str__(self):
        return self.name

    @property
    def current_service(self):
        return self.services.filter(status=OneTimeService.STATUS_IN_PROGRESS).first()

    @property
    def last_completed_service(self):
        return self.services.filter(status=OneTimeService.STATUS_COMPLETED).order_by('-completed_at').first()


class OneTimeService(models.Model):
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED   = 'completed'
    STATUS_CHOICES = [
        (STATUS_IN_PROGRESS, 'تحت الإجراء'),
        (STATUS_COMPLETED,   'مكتملة'),
    ]

    client       = models.ForeignKey(OneTimeServiceClient, on_delete=models.CASCADE, related_name='services')
    service_type = models.CharField(max_length=200, verbose_name='نوع الخدمة')
    assigned_to  = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='onetime_services',
        verbose_name='المنفّذ'
    )
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_IN_PROGRESS)
    report_file  = models.FileField(upload_to='onetime_services/reports/', null=True, blank=True, verbose_name='التقرير')
    notes        = models.TextField(blank=True)
    start_date   = models.DateField(verbose_name='تاريخ الفتح')
    created_by   = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='created_onetime_services'
    )
    created_at   = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name = 'خدمة لمرة واحدة'
        verbose_name_plural = 'الخدمات لمرة واحدة'

    def __str__(self):
        return f'{self.client.name} — {self.service_type}'
