from django.db import models
from django.conf import settings


class CommissionSheet(models.Model):
    tenant = models.ForeignKey('accounts.Tenant', on_delete=models.CASCADE, related_name='commission_sheets')
    name = models.CharField(max_length=200, verbose_name='اسم الشيت')
    period_start = models.DateField(null=True, blank=True, verbose_name='بداية الفترة')
    period_end = models.DateField(null=True, blank=True, verbose_name='نهاية الفترة')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.period_start and self.period_end:
            return f"{self.name} ({self.period_start} - {self.period_end})"
        return self.name

    class Meta:
        verbose_name = 'شيت عمولات'
        verbose_name_plural = 'شيتات العمولات'
        ordering = ['-period_start']


class CommissionEntry(models.Model):
    sheet = models.ForeignKey(CommissionSheet, on_delete=models.CASCADE, related_name='entries')
    client = models.ForeignKey('clients.Client', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='العميل')
    review_client = models.ForeignKey('workflow.ReviewClient', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='عميل المراجعة')
    zatca_client  = models.ForeignKey('zatca.ZatcaClient', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='عميل ZATCA')
    zatca_session = models.ForeignKey('zatca.ZatcaSession', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='دورة ZATCA')
    sales_rep = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='commission_entries', verbose_name='المندوب')
    accountant_rep = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='accountant_commission_entries', verbose_name='المحاسب')
    reviewer_rep = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='reviewer_commission_entries', verbose_name='المراجع')
    is_confirmed = models.BooleanField(default=False, verbose_name='تم التأكيد ✓')
    entry_date = models.DateField(null=True, blank=True, verbose_name='تاريخ السطر')
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='المبلغ')
    commission_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='عمولة المندوب')
    accountant_commission_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='عمولة المحاسب')
    review_commission_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='عمولة المراجع')
    notes = models.TextField(blank=True, verbose_name='ملاحظات')

    @staticmethod
    def _calc(rule, amount):
        from decimal import Decimal
        if rule is None:
            return Decimal('0')
        if rule.commission_type == 'fixed':
            return rule.value
        result = amount * (rule.value / Decimal('100'))
        if rule.max_amount:
            result = min(result, rule.max_amount)
        return result

    def recalculate_commissions(self, rules=None):
        if rules is None:
            rules = {r.department: r for r in self.entry_commission_rules.all()}
        self.commission_amount = self._calc(rules.get('sales'), self.amount)
        self.accountant_commission_amount = self._calc(rules.get('accountant'), self.amount)
        self.review_commission_amount = self._calc(rules.get('review'), self.amount)

    def __str__(self):
        name = self.client.name if self.client else (self.review_client.name if self.review_client else (self.zatca_client.name if self.zatca_client else '—'))
        return f"{name} - {self.amount}"

    @property
    def client_name(self):
        if self.client:
            return self.client.name
        if self.review_client:
            return self.review_client.name
        if self.zatca_session:
            return f"{self.zatca_session.client.name} ({self.zatca_session.start_date})"
        if self.zatca_client:
            return self.zatca_client.name
        return '—'

    @property
    def client_company(self):
        if self.client:
            return self.client.company or ''
        if self.review_client:
            return self.review_client.company or ''
        if self.zatca_client:
            return self.zatca_client.company or ''
        return ''

    @property
    def entry_type(self):
        if self.review_client:
            return 'review'
        if self.zatca_session or self.zatca_client:
            return 'zatca'
        return 'client'

    class Meta:
        verbose_name = 'سطر عمولة'
        verbose_name_plural = 'سطور العمولات'


class EntryCommissionRule(models.Model):
    TYPE_FIXED = 'fixed'
    TYPE_PERCENT = 'percent'
    TYPE_CHOICES = [(TYPE_FIXED, 'مبلغ ثابت'), (TYPE_PERCENT, 'نسبة مئوية')]

    DEPT_SALES = 'sales'
    DEPT_ACCOUNTANT = 'accountant'
    DEPT_REVIEW = 'review'

    entry = models.ForeignKey(CommissionEntry, on_delete=models.CASCADE, related_name='entry_commission_rules')
    department = models.CharField(max_length=20)
    commission_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=TYPE_FIXED)
    value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    reference_note = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('entry', 'department')

    def get_summary(self):
        if self.commission_type == self.TYPE_FIXED:
            return f"{self.value} ريال"
        s = f"{self.value}%"
        if self.max_amount:
            s += f" (حد {self.max_amount})"
        return s
