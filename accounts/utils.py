from django.db.models import Q
from .models import User


def assignable_users(tenant, role):
    """
    المستخدمون القابلون للإسناد لدور معيّن.

    يشمل الأدمن دائماً لأنه قد ينفّذ بعض المهام بنفسه،
    فيظهر في جميع قوائم الإسناد (مندوب / محاسب / مراجع).
    """
    return User.objects.filter(tenant=tenant, is_active=True).filter(
        Q(role=role) | Q(role=User.ROLE_ADMIN)
    ).order_by('first_name', 'username')


def is_assignable(user, role):
    """يتحقق أن المستخدم صالح للإسناد لدور معيّن (أو أنه أدمن)."""
    return user is not None and user.is_active and user.role in (role, User.ROLE_ADMIN)
