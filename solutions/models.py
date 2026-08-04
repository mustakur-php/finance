from django.db import models
from django.conf import settings


class SolutionMessage(models.Model):
    """
    رسائل صفحة 'حلول التطبيقات' — قناة نقاش مستمرة بين الأدمن والمطور
    داخل نفس الشركة، على شكل شات بسيط.
    """
    tenant = models.ForeignKey('accounts.Tenant', on_delete=models.CASCADE, related_name='solution_messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='solution_messages')
    body = models.TextField(verbose_name='النص')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'رسالة حلول التطبيقات'
        verbose_name_plural = 'رسائل حلول التطبيقات'

    def __str__(self):
        name = self.sender.get_full_name() or self.sender.username if self.sender else 'محذوف'
        return f'{name}: {self.body[:40]}'
