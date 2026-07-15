from django.db import models
from django.conf import settings


class ZatcaClient(models.Model):
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED   = 'completed'
    STATUS_CHOICES = [
        (STATUS_IN_PROGRESS, 'تحت الإجراء'),
        (STATUS_COMPLETED,   'مكتمل'),
    ]

    tenant             = models.ForeignKey('accounts.Tenant', on_delete=models.CASCADE, related_name='zatca_clients')
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
    status             = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_IN_PROGRESS)
    report_file        = models.FileField(upload_to='zatca/reports/', null=True, blank=True, verbose_name='تقرير الإنجاز')
    assigned_accountant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='zatca_clients',
        verbose_name='المحاسب المسند'
    )
    is_commissionable  = models.BooleanField(default=False, verbose_name='خاضع للعمولة')
    created_by         = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='created_zatca_clients'
    )
    created_at         = models.DateTimeField(auto_now_add=True)
    completed_at       = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'عميل ZATCA'
        verbose_name_plural = 'عملاء ZATCA'

    def __str__(self):
        return self.name
