from django.db import models
from django.conf import settings


class AuditLog(models.Model):
    ACTION_CREATE = 'create'
    ACTION_UPDATE = 'update'
    ACTION_DELETE = 'delete'
    ACTION_LOGIN  = 'login'
    ACTION_LOGOUT = 'logout'
    ACTION_CHOICES = [
        (ACTION_CREATE, 'إضافة'),
        (ACTION_UPDATE, 'تعديل'),
        (ACTION_DELETE, 'حذف'),
        (ACTION_LOGIN,  'تسجيل دخول'),
        (ACTION_LOGOUT, 'تسجيل خروج'),
    ]

    tenant      = models.ForeignKey('accounts.Tenant', on_delete=models.CASCADE, related_name='audit_logs')
    user        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action      = models.CharField(max_length=10, choices=ACTION_CHOICES)
    model_name  = models.CharField(max_length=50, blank=True)
    object_id   = models.CharField(max_length=50, blank=True)
    object_repr = models.CharField(max_length=300, blank=True)
    changes     = models.JSONField(default=dict, blank=True)
    ip_address  = models.GenericIPAddressField(null=True, blank=True)
    timestamp   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'سجل عملية'
        verbose_name_plural = 'سجل العمليات'

    def __str__(self):
        return f"{self.user} — {self.get_action_display()} — {self.object_repr}"

    def get_action_color(self):
        return {
            'create': 'success',
            'update': 'primary',
            'delete': 'danger',
            'login':  'info',
            'logout': 'secondary',
        }.get(self.action, 'secondary')
