from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import SolutionMessage


def _can_access(user):
    return user.is_authenticated and (user.is_admin or user.is_developer)


@login_required
def solutions_view(request):
    if not _can_access(request.user):
        messages.error(request, 'ليس لديك صلاحية الوصول لهذه الصفحة')
        return redirect('dashboard')

    if request.method == 'POST':
        body = request.POST.get('body', '').strip()
        if body:
            SolutionMessage.objects.create(
                tenant=request.user.tenant,
                sender=request.user,
                body=body,
            )
        return redirect('solutions')

    msgs = SolutionMessage.objects.filter(tenant=request.user.tenant).select_related('sender')
    return render(request, 'solutions/solutions.html', {'messages_list': msgs})
