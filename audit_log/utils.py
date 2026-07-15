from .models import AuditLog


def get_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def log_action(request, action, obj=None, changes=None, model_name='', object_repr='', object_id=''):
    try:
        if obj is not None:
            model_name  = model_name  or obj.__class__.__name__
            object_repr = object_repr or str(obj)[:300]
            object_id   = object_id   or str(obj.pk)

        AuditLog.objects.create(
            tenant      = request.user.tenant,
            user        = request.user,
            action      = action,
            model_name  = model_name,
            object_id   = object_id,
            object_repr = object_repr,
            changes     = changes or {},
            ip_address  = get_ip(request),
        )
    except Exception:
        pass
