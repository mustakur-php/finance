from django.db import models
from django.conf import settings


class Event(models.Model):
    TYPE_MEETING = 'meeting'
    TYPE_VISIT = 'visit'
    TYPE_FOLLOWUP = 'followup'
    TYPE_REMINDER = 'reminder'
    TYPE_OTHER = 'other'

    TYPE_CHOICES = [
        (TYPE_MEETING, 'اجتماع'),
        (TYPE_VISIT, 'زيارة'),
        (TYPE_FOLLOWUP, 'متابعة'),
        (TYPE_REMINDER, 'تذكير'),
        (TYPE_OTHER, 'أخرى'),
    ]

    SOURCE_REVIEW = 'review'
    SOURCE_SALES = 'sales'
    SOURCE_ACCOUNTS = 'accounts'

    SOURCE_CHOICES = [
        (SOURCE_REVIEW, 'قسم المراجعة'),
        (SOURCE_SALES, 'قسم المناديب'),
        (SOURCE_ACCOUNTS, 'قسم الحسابات'),
    ]

    tenant = models.ForeignKey('accounts.Tenant', on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=300, verbose_name='العنوان')
    event_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_REMINDER, verbose_name='النوع')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, blank=True, verbose_name='القسم')
    client = models.ForeignKey('clients.Client', on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='events', verbose_name='العميل')
    review_client = models.ForeignKey('workflow.ReviewClient', on_delete=models.SET_NULL,
                                       null=True, blank=True, related_name='events', verbose_name='عميل المراجعة')
    zatca_client = models.ForeignKey('zatca.ZatcaClient', on_delete=models.SET_NULL,
                                      null=True, blank=True, related_name='events', verbose_name='عميل ZATCA')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                     related_name='events', verbose_name='مسند إلى')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, related_name='created_events', verbose_name='أنشأه')
    start_datetime = models.DateTimeField(verbose_name='وقت البداية')
    end_datetime = models.DateTimeField(null=True, blank=True, verbose_name='وقت النهاية')
    STATUS_PENDING    = 'pending'
    STATUS_DONE       = 'done'
    STATUS_CANCELLED  = 'cancelled'
    STATUS_RESCHEDULED = 'rescheduled'
    STATUS_CHOICES = [
        (STATUS_PENDING,     'قادم'),
        (STATUS_DONE,        'منجز'),
        (STATUS_CANCELLED,   'ملغي'),
        (STATUS_RESCHEDULED, 'معاد جدولته'),
    ]

    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=STATUS_PENDING, verbose_name='الحالة')
    is_done = models.BooleanField(default=False, verbose_name='منجز')  # kept for compatibility
    reminder_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def linked_client(self):
        """العميل المرتبط بالحدث من أي قسم."""
        return self.client or self.review_client or self.zatca_client

    @property
    def client_name(self):
        c = self.linked_client
        return c.name if c else ''

    @property
    def client_section(self):
        """اسم القسم الذي ينتمي له عميل الحدث."""
        if self.client:
            return 'فعلي' if self.client.client_type == 'actual' else 'مستهدف'
        if self.review_client:
            return 'مراجعة'
        if self.zatca_client:
            return 'ZATCA'
        return ''

    @property
    def client_url_name(self):
        """اسم المسار المناسب لصفحة العميل حسب قسمه."""
        if self.client:
            return 'client_detail'
        if self.review_client:
            return 'workflow_detail'
        if self.zatca_client:
            return 'zatca_detail'
        return ''

    def get_status_color(self):
        return {
            self.STATUS_PENDING:     'primary',
            self.STATUS_DONE:        'success',
            self.STATUS_CANCELLED:   'danger',
            self.STATUS_RESCHEDULED: 'warning',
        }.get(self.status, 'secondary')

    def __str__(self):
        return f"{self.title} - {self.start_datetime.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        verbose_name = 'حدث'
        verbose_name_plural = 'الأحداث'
        ordering = ['start_datetime']
