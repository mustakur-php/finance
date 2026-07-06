from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Visit


@login_required
def visits_list(request):
    from calendar_app.models import Event

    visits = Visit.objects.filter(tenant=request.user.tenant).select_related('client', 'sales_rep')
    if request.user.is_sales:
        visits = visits.filter(sales_rep=request.user)

    done_events = Event.objects.filter(
        tenant=request.user.tenant,
        is_done=True,
    ).select_related('client', 'assigned_to')
    if request.user.is_sales:
        done_events = done_events.filter(assigned_to=request.user)

    return render(request, 'visits/list.html', {
        'visits': visits,
        'done_events': done_events,
    })


@login_required
def visit_create(request):
    from .forms import VisitForm
    form = VisitForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        visit = form.save(commit=False)
        visit.tenant = request.user.tenant
        visit.sales_rep = request.user
        visit.save()
        messages.success(request, 'تم تسجيل الزيارة بنجاح')
        return redirect('visits_list')
    return render(request, 'visits/form.html', {'form': form, 'title': 'تسجيل زيارة'})


@login_required
def visit_edit(request, pk):
    from .forms import VisitForm
    visit = get_object_or_404(Visit, pk=pk, tenant=request.user.tenant)
    form = VisitForm(request.POST or None, instance=visit, user=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'تم تحديث الزيارة')
        return redirect('visits_list')
    return render(request, 'visits/form.html', {'form': form, 'title': 'تعديل زيارة'})
