from django.db import models
from django.conf import settings
from django.utils import timezone


class ReviewClient(models.Model):
    tenant             = models.ForeignKey('accounts.Tenant', on_delete=models.CASCADE, related_name='review_clients')
    source_client      = models.ForeignKey('clients.Client', on_delete=models.SET_NULL, null=True, blank=True,
                                            related_name='review_copies', verbose_name='العميل الأصلي')
    name               = models.CharField(max_length=200)
    company            = models.CharField(max_length=200, blank=True)
    phone              = models.CharField(max_length=30, blank=True)
    email              = models.EmailField(blank=True)
    city               = models.CharField(max_length=100, blank=True)
    district           = models.CharField(max_length=100, blank=True)
    address            = models.TextField(blank=True)
    responsible_person = models.CharField(max_length=100, blank=True)
    job_title          = models.CharField(max_length=100, blank=True)
    activity           = models.CharField(max_length=100, blank=True)
    notes              = models.TextField(blank=True)
    distinguished_number = models.CharField(max_length=100, blank=True, verbose_name='الرقم المميز')
    secret_number        = models.CharField(max_length=100, blank=True, verbose_name='الرقم السري')
    assigned_reviewer    = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_review_clients')
    is_commissionable    = models.BooleanField(default=False, verbose_name='خاضع للعمولة')
    created_by  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_review_clients')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def current_stage(self):
        return self.stages.filter(status=WorkflowStage.STATUS_IN_PROGRESS).first() or \
               self.stages.filter(status=WorkflowStage.STATUS_WAITING).first()

    @property
    def start_date(self):
        first = self.stages.order_by('order').first()
        return first.start_date if first else None

    @property
    def total_days(self):
        start = self.start_date
        if not start:
            return None
        end_stage = self.stages.filter(status=WorkflowStage.STATUS_COMPLETED).order_by('-order').first()
        end = end_stage.end_date if end_stage else timezone.localdate()
        return (end - start).days


class WorkflowStage(models.Model):
    STAGE_CONTRACT = 'contract'
    STAGE_REVIEW   = 'review'
    STAGE_LETTERS  = 'letters'
    STAGE_SUBMIT   = 'submit'
    STAGE_CHOICES  = [
        (STAGE_CONTRACT, 'التعاقد'),
        (STAGE_REVIEW,   'المراجعة'),
        (STAGE_LETTERS,  'الخطابات'),
        (STAGE_SUBMIT,   'الرفع'),
    ]
    STAGE_ORDER = [STAGE_CONTRACT, STAGE_REVIEW, STAGE_LETTERS, STAGE_SUBMIT]

    STATUS_PENDING    = 'pending'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_WAITING    = 'waiting_approval'
    STATUS_COMPLETED  = 'completed'
    STATUS_CHOICES    = [
        (STATUS_PENDING,     'في الانتظار'),
        (STATUS_IN_PROGRESS, 'جارية'),
        (STATUS_WAITING,     'بانتظار الاعتماد'),
        (STATUS_COMPLETED,   'مكتملة'),
    ]

    client      = models.ForeignKey(ReviewClient, on_delete=models.CASCADE, related_name='stages')
    stage       = models.CharField(max_length=20, choices=STAGE_CHOICES)
    order       = models.PositiveSmallIntegerField()
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    start_date  = models.DateField(null=True, blank=True)
    end_date    = models.DateField(null=True, blank=True)
    due_date    = models.DateField(null=True, blank=True)
    notes       = models.TextField(blank=True)
    updated_by  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_stages')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_stages')
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        unique_together = ('client', 'stage')

    def __str__(self):
        return f'{self.client} - {self.get_stage_display()}'

    def get_status_color(self):
        return {
            self.STATUS_PENDING:     'secondary',
            self.STATUS_IN_PROGRESS: 'primary',
            self.STATUS_WAITING:     'warning',
            self.STATUS_COMPLETED:   'success',
        }.get(self.status, 'secondary')

    @property
    def days_remaining(self):
        if not self.due_date or self.status == self.STATUS_COMPLETED:
            return None
        return (self.due_date - timezone.localdate()).days

    @property
    def days_in_stage(self):
        if not self.start_date:
            return None
        end = self.end_date or timezone.localdate()
        return (end - self.start_date).days

    @property
    def due_status(self):
        r = self.days_remaining
        if r is None:
            return None
        if r < 0:
            return 'overdue'
        if r <= 3:
            return 'near'
        return 'ok'
