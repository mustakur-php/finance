from django.db import models
from django.conf import settings


class ZatcaClient(models.Model):
    tenant             = models.ForeignKey('accounts.Tenant', on_delete=models.CASCADE, related_name='zatca_clients')
    source_client      = models.ForeignKey('clients.Client', on_delete=models.SET_NULL, null=True, blank=True,
                                            related_name='zatca_copies', verbose_name='العميل الأصلي')
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
    secret_number        = models.CharField(max_length=100, blank=True, verbose_name='الرقم السري')
    assigned_accountant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='zatca_clients',
        verbose_name='المحاسب المسند'
    )
    PERIOD_CHOICES = [
        (1,  'شهري'),
        (3,  'ربع سنوي'),
        (6,  'نصف سنوي'),
        (12, 'سنوي'),
    ]
    period_months      = models.PositiveSmallIntegerField(choices=PERIOD_CHOICES, default=1, verbose_name='الفترة')
    is_commissionable  = models.BooleanField(default=False, verbose_name='خاضع للعمولة')
    created_by         = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='created_zatca_clients'
    )
    created_at         = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'عميل ZATCA'
        verbose_name_plural = 'عملاء ZATCA'

    def __str__(self):
        return self.name

    def next_session_start(self):
        last = self.sessions.order_by('-start_date').first()
        if not last:
            return None
        from dateutil.relativedelta import relativedelta
        return last.start_date + relativedelta(months=self.period_months)


class ZatcaSession(models.Model):
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED   = 'completed'
    STATUS_CHOICES = [
        (STATUS_IN_PROGRESS, 'تحت الإجراء'),
        (STATUS_COMPLETED,   'مكتملة'),
    ]

    client      = models.ForeignKey(ZatcaClient, on_delete=models.CASCADE, related_name='sessions')
    start_date  = models.DateField(verbose_name='تاريخ البداية')
    end_date    = models.DateField(null=True, blank=True, verbose_name='تاريخ الانتهاء')
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_IN_PROGRESS)
    report_file = models.FileField(upload_to='zatca/sessions/', null=True, blank=True, verbose_name='تقرير الدورة')
    # اختياري — يُترك فارغاً فترث الدورة محاسب العميل، ويُملأ فقط عند إسناد دورة لمحاسب مختلف
    assigned_accountant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='zatca_sessions',
        verbose_name='محاسب الدورة'
    )
    notes       = models.TextField(blank=True)
    created_by  = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='created_zatca_sessions'
    )
    created_at  = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name = 'دورة ZATCA'

    def __str__(self):
        return f'{self.client.name} — {self.start_date}'

    @property
    def effective_accountant(self):
        """محاسب الدورة إن أُسند لها، وإلا محاسب العميل."""
        return self.assigned_accountant or self.client.assigned_accountant

    @property
    def has_custom_accountant(self):
        """هل أُسندت الدورة لمحاسب مختلف عن محاسب العميل؟"""
        return bool(self.assigned_accountant_id) and \
            self.assigned_accountant_id != self.client.assigned_accountant_id
