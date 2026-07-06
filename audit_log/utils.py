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


def diff_fields(old_obj, new_obj, fields):
    """يقارن قيم الحقول قبل وبعد ويرجع dict بالتغييرات فقط"""
    changes = {}
    for field in fields:
        old_val = str(getattr(old_obj, field, '') or '')
        new_val = str(getattr(new_obj, field, '') or '')
        if old_val != new_val:
            changes[field] = {'من': old_val, 'إلى': new_val}
    return changes
