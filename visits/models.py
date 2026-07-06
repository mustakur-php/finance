from django.db import models
from django.conf import settings


class Visit(models.Model):
    STATUS_PLANNED = 'planned'
    STATUS_DONE = 'done'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PLANNED, 'مجدولة'),
        (STATUS_DONE, 'منجزة'),
        (STATUS_CANCELLED, 'ملغاة'),
    ]

    tenant = models.ForeignKey('accounts.Tenant', on_delete=models.CASCADE, related_name='visits')
    client = models.ForeignKey('clients.Client', on_delete=models.CASCADE, related_name='visits', verbose_name='العميل')
    sales_rep = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   related_name='visits', verbose_name='المندوب')
    visit_date = models.DateTimeField(verbose_name='تاريخ الزيارة')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PLANNED, verbose_name='الحالة')
    purpose = models.CharField(max_length=300, blank=True, verbose_name='الغرض من الزيارة')
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    result = models.TextField(blank=True, verbose_name='نتيجة الزيارة')
    reminder_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"زيارة {self.client.name} - {self.visit_date.strftime('%Y-%m-%d')}"

    class Meta:
        verbose_name = 'زيارة'
        verbose_name_plural = 'الزيارات'
        ordering = ['-visit_date']
