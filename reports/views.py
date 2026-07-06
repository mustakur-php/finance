from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from accounts.decorators import admin_required
import datetime


def _date_filters(request):
    date_from = request.GET.get('date_from', '')
    date_to   = request.GET.get('date_to', '')
    return date_from, date_to


# ─────────────────────────────────────────
# الصفحة الرئيسية للتقارير
# ─────────────────────────────────────────
@login_required
@admin_required
def reports_home(request):
    from clients.models import Client
    from commissions.models import CommissionEntry
    from calendar_app.models import Event
    from workflow.models import ReviewClient, WorkflowStage

    tenant = request.user.tenant
    today  = timezone.localdate()

    ctx = {
        'total_clients':      Client.objects.filter(tenant=tenant, is_active=True, client_type='actual').count(),
        'total_targeted':     Client.objects.filter(tenant=tenant, is_active=True, client_type='potential').count(),
        'total_commission':   CommissionEntry.objects.filter(sheet__tenant=tenant).aggregate(
                                  s=Sum('commission_amount'))['s'] or 0,
        'total_accountant':   CommissionEntry.objects.filter(sheet__tenant=tenant).aggregate(
                                  s=Sum('accountant_commission_amount'))['s'] or 0,
        'total_review_comm':  CommissionEntry.objects.filter(sheet__tenant=tenant).aggregate(
                                  s=Sum('review_commission_amount'))['s'] or 0,
        'total_amount':       CommissionEntry.objects.filter(sheet__tenant=tenant).aggregate(
                                  s=Sum('amount'))['s'] or 0,
        'events_done':        Event.objects.filter(tenant=tenant, status='done').count(),
        'events_cancelled':   Event.objects.filter(tenant=tenant, status='cancelled').count(),
        'events_pending':     Event.objects.filter(tenant=tenant, status='pending').count(),
        'workflow_clients':   ReviewClient.objects.filter(tenant=tenant).count(),
        'workflow_overdue':   WorkflowStage.objects.filter(
                                  client__tenant=tenant,
                                  due_date__lt=today,
                                  status__in=['in_progress', 'waiting_approval']
                              ).count(),
        'today': today,
    }
    return render(request, 'reports/home.html', ctx)


# ─────────────────────────────────────────
# تقرير العملاء
# ─────────────────────────────────────────
@login_required
@admin_required
def report_clients(request):
    from clients.models import Client, Activity
    from accounts.models import User

    tenant = request.user.tenant
    date_from, date_to = _date_filters(request)
    city_filter    = request.GET.get('city', '')
    sales_filter   = request.GET.get('sales', '')
    type_filter    = request.GET.get('type', 'actual')

    qs = Client.objects.filter(tenant=tenant, is_active=True, client_type=type_filter)
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)
    if city_filter:
        qs = qs.filter(city=city_filter)
    if sales_filter:
        qs = qs.filter(assigned_sales_id=sales_filter)

    by_city     = qs.values('city').annotate(count=Count('id')).order_by('-count')
    by_activity = qs.values('activity__name').annotate(count=Count('id')).order_by('-count')
    by_sales    = qs.values('assigned_sales__first_name','assigned_sales__last_name','assigned_sales__username').annotate(count=Count('id')).order_by('-count')
    cities      = Client.objects.filter(tenant=tenant, is_active=True).exclude(city='').values_list('city', flat=True).distinct()
    sales_users = User.objects.filter(tenant=tenant, role='sales', is_active=True)

    return render(request, 'reports/clients.html', {
        'clients': qs.select_related('assigned_sales','assigned_accountant','activity'),
        'total': qs.count(),
        'by_city': by_city,
        'by_activity': by_activity,
        'by_sales': by_sales,
        'cities': cities,
        'sales_users': sales_users,
        'filters': {'date_from': date_from, 'date_to': date_to,
                    'city': city_filter, 'sales': sales_filter, 'type': type_filter},
    })


# ─────────────────────────────────────────
# تقرير العمولات
# ─────────────────────────────────────────
@login_required
@admin_required
def report_commissions(request):
    from commissions.models import CommissionSheet, CommissionEntry
    from accounts.models import User

    tenant      = request.user.tenant
    date_from, date_to = _date_filters(request)
    role_filter = request.GET.get('role', '')
    user_filter = request.GET.get('user', '')

    sheets  = CommissionSheet.objects.filter(tenant=tenant)
    entries = CommissionEntry.objects.filter(sheet__tenant=tenant)

    if date_from:
        entries = entries.filter(sheet__created_at__date__gte=date_from)
    if date_to:
        entries = entries.filter(sheet__created_at__date__lte=date_to)

    # فلتر المستخدم حسب الدور
    if role_filter == 'sales' and user_filter:
        entries = entries.filter(sales_rep_id=user_filter)
    elif role_filter == 'accountant' and user_filter:
        entries = entries.filter(client__assigned_accountant_id=user_filter)
    elif role_filter == 'review' and user_filter:
        entries = entries.filter(client__assigned_review_id=user_filter)

    # قوائم المستخدمين للفلتر
    sales_users      = User.objects.filter(tenant=tenant, role='sales',      is_active=True)
    accountant_users = User.objects.filter(tenant=tenant, role='accountant', is_active=True)
    review_users     = User.objects.filter(tenant=tenant, role='review',     is_active=True)

    totals = entries.aggregate(
        total_amount    = Sum('amount'),
        total_sales     = Sum('commission_amount'),
        total_accountant= Sum('accountant_commission_amount'),
        total_review    = Sum('review_commission_amount'),
    )

    by_sheet = sheets.annotate(
        t_amount    = Sum('entries__amount'),
        t_sales     = Sum('entries__commission_amount'),
        t_accountant= Sum('entries__accountant_commission_amount'),
        t_review    = Sum('entries__review_commission_amount'),
    ).order_by('-created_at')

    top_clients = entries.values('client__name').annotate(
        total=Sum('amount')
    ).order_by('-total')[:10]

    return render(request, 'reports/commissions.html', {
        'totals':           totals,
        'by_sheet':         by_sheet,
        'sales_users':      sales_users,
        'accountant_users': accountant_users,
        'review_users':     review_users,
        'filters': {
            'date_from': date_from, 'date_to': date_to,
            'role': role_filter, 'user': user_filter,
        },
        'top_clients': top_clients,
        'filters': {'date_from': date_from, 'date_to': date_to},
    })


# ─────────────────────────────────────────
# تقرير الأحداث
# ─────────────────────────────────────────
@login_required
@admin_required
def report_events(request):
    from calendar_app.models import Event
    from accounts.models import User

    tenant = request.user.tenant
    date_from, date_to = _date_filters(request)
    user_filter   = request.GET.get('user', '')
    source_filter = request.GET.get('source', '')

    qs = Event.objects.filter(tenant=tenant)
    if date_from:
        qs = qs.filter(start_datetime__date__gte=date_from)
    if date_to:
        qs = qs.filter(start_datetime__date__lte=date_to)
    if user_filter:
        qs = qs.filter(assigned_to_id=user_filter)
    if source_filter:
        qs = qs.filter(source=source_filter)

    by_status = qs.values('status').annotate(count=Count('id'))
    by_type   = qs.values('event_type').annotate(count=Count('id'))
    by_user   = qs.values('assigned_to__first_name','assigned_to__last_name','assigned_to__username').annotate(
                    total=Count('id'), done=Count('id', filter=Q(status='done'))
                ).order_by('-total')
    users = User.objects.filter(tenant=tenant, is_active=True)

    return render(request, 'reports/events.html', {
        'total': qs.count(),
        'by_status': by_status,
        'by_type': by_type,
        'by_user': by_user,
        'events': qs.select_related('assigned_to','client').order_by('-start_datetime')[:200],
        'users': users,
        'filters': {'date_from': date_from, 'date_to': date_to,
                    'user': user_filter, 'source': source_filter},
    })


# ─────────────────────────────────────────
# تقرير قسم المراجعة
# ─────────────────────────────────────────
@login_required
@admin_required
def report_workflow(request):
    from workflow.models import ReviewClient, WorkflowStage

    tenant       = request.user.tenant
    today        = timezone.localdate()
    stage_filter = request.GET.get('stage', '')
    status_filter= request.GET.get('status', '')

    clients = ReviewClient.objects.filter(tenant=tenant).prefetch_related('stages')

    if stage_filter or status_filter:
        stage_qs = WorkflowStage.objects.filter(client__tenant=tenant)
        if stage_filter:
            stage_qs = stage_qs.filter(stage=stage_filter)
        if status_filter:
            stage_qs = stage_qs.filter(status=status_filter)
        client_ids = stage_qs.values_list('client_id', flat=True).distinct()
        clients = clients.filter(pk__in=client_ids)

    by_stage = WorkflowStage.objects.filter(client__tenant=tenant).values('stage','status').annotate(count=Count('id'))
    overdue  = WorkflowStage.objects.filter(
        client__tenant=tenant, due_date__lt=today,
        status__in=['in_progress','waiting_approval']
    ).select_related('client')

    return render(request, 'reports/workflow.html', {
        'clients':       clients,
        'by_stage':      by_stage,
        'overdue':       overdue,
        'stage_choices': WorkflowStage.STAGE_CHOICES,
        'status_choices':WorkflowStage.STATUS_CHOICES,
        'today':         today,
        'filters':       {'stage': stage_filter, 'status': status_filter},
    })


# ─────────────────────────────────────────
# تقرير المستخدمين
# ─────────────────────────────────────────
@login_required
@admin_required
def report_users(request):
    from accounts.models import User
    from calendar_app.models import Event

    tenant = request.user.tenant
    date_from, date_to = _date_filters(request)

    users = User.objects.filter(tenant=tenant, is_active=True)
    data  = []
    for u in users:
        qs = Event.objects.filter(tenant=tenant, assigned_to=u)
        if date_from:
            qs = qs.filter(start_datetime__date__gte=date_from)
        if date_to:
            qs = qs.filter(start_datetime__date__lte=date_to)
        data.append({
            'user':      u,
            'total':     qs.count(),
            'done':      qs.filter(status='done').count(),
            'cancelled': qs.filter(status='cancelled').count(),
            'pending':   qs.filter(status='pending').count(),
        })

    return render(request, 'reports/users.html', {
        'data': data,
        'filters': {'date_from': date_from, 'date_to': date_to},
    })


# ═══════════════════════════════════════════
# تصدير Excel
# ═══════════════════════════════════════════
def _make_excel_response(filename):
    from django.http import HttpResponse
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def _style_header(ws, headers, fill_color='1a3a5c'):
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    ws.append(headers)
    for cell in ws[1]:
        cell.font      = Font(bold=True, color='FFFFFF')
        cell.fill      = PatternFill(fill_type='solid', fgColor=fill_color)
        cell.alignment = Alignment(horizontal='center')


@login_required
@admin_required
def export_clients_excel(request):
    import openpyxl
    from clients.models import Client

    tenant = request.user.tenant
    qs     = Client.objects.filter(tenant=tenant, is_active=True).select_related('assigned_sales','assigned_accountant','activity')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'العملاء'
    _style_header(ws, ['الاسم','الشركة','المدينة','الجوال','المندوب','المحاسب','النشاط','تاريخ الإضافة'])
    for c in qs:
        ws.append([
            c.name, c.company, c.city, c.phone,
            c.assigned_sales.get_full_name() if c.assigned_sales else '',
            c.assigned_accountant.get_full_name() if c.assigned_accountant else '',
            c.activity.name if c.activity else '',
            str(c.created_at.date()) if c.created_at else '',
        ])
    response = _make_excel_response('clients.xlsx')
    wb.save(response)
    return response


@login_required
@admin_required
def export_commissions_excel(request):
    import openpyxl
    from commissions.models import CommissionEntry

    tenant      = request.user.tenant
    date_from   = request.GET.get('date_from', '')
    date_to     = request.GET.get('date_to', '')
    role_filter = request.GET.get('role', '')
    user_filter = request.GET.get('user', '')

    entries = CommissionEntry.objects.filter(sheet__tenant=tenant).select_related('client','sheet')
    if date_from:
        entries = entries.filter(sheet__created_at__date__gte=date_from)
    if date_to:
        entries = entries.filter(sheet__created_at__date__lte=date_to)
    if role_filter == 'sales' and user_filter:
        entries = entries.filter(sales_rep_id=user_filter)
    elif role_filter == 'accountant' and user_filter:
        entries = entries.filter(client__assigned_accountant_id=user_filter)
    elif role_filter == 'review' and user_filter:
        entries = entries.filter(client__assigned_review_id=user_filter)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'العمولات'
    _style_header(ws, ['الشيت','العميل','المبلغ','عمولة المناديب','عمولة المحاسبين','عمولة المراجعين'])
    for e in entries:
        ws.append([
            str(e.sheet), e.client.name if e.client else '',
            float(e.amount), float(e.commission_amount),
            float(e.accountant_commission_amount), float(e.review_commission_amount),
        ])
    response = _make_excel_response('commissions.xlsx')
    wb.save(response)
    return response


@login_required
@admin_required
def export_events_excel(request):
    import openpyxl
    from calendar_app.models import Event

    tenant = request.user.tenant
    qs     = Event.objects.filter(tenant=tenant).select_related('assigned_to','client')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'الأحداث'
    _style_header(ws, ['العنوان','النوع','الحالة','العميل','المسند إلى','التاريخ','ملاحظات'])
    for e in qs:
        ws.append([
            e.title, e.get_event_type_display(), e.get_status_display(),
            e.client.name if e.client else '',
            e.assigned_to.get_full_name() if e.assigned_to else '',
            str(e.start_datetime.date()),
            e.notes,
        ])
    response = _make_excel_response('events.xlsx')
    wb.save(response)
    return response


@login_required
@admin_required
def export_workflow_excel(request):
    import openpyxl
    from workflow.models import ReviewClient, WorkflowStage

    tenant       = request.user.tenant
    stage_filter = request.GET.get('stage', '')
    status_filter= request.GET.get('status', '')

    clients = ReviewClient.objects.filter(tenant=tenant).prefetch_related('stages')
    if stage_filter or status_filter:
        stage_qs = WorkflowStage.objects.filter(client__tenant=tenant)
        if stage_filter:
            stage_qs = stage_qs.filter(stage=stage_filter)
        if status_filter:
            stage_qs = stage_qs.filter(status=status_filter)
        client_ids = stage_qs.values_list('client_id', flat=True).distinct()
        clients = clients.filter(pk__in=client_ids)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'قسم المراجعة'
    _style_header(ws, ['العميل','الشركة','المرحلة','الحالة','تاريخ البداية','تاريخ النهاية','تاريخ الاستحقاق','المدة (يوم)'])
    from django.utils import timezone
    today = timezone.localdate()
    for client in clients:
        for stage in client.stages.all():
            days = stage.days_in_stage
            ws.append([
                client.name, client.company,
                stage.get_stage_display(), stage.get_status_display(),
                str(stage.start_date) if stage.start_date else '',
                str(stage.end_date)   if stage.end_date   else '',
                str(stage.due_date)   if stage.due_date   else '',
                days if days is not None else '',
            ])
    response = _make_excel_response('workflow.xlsx')
    wb.save(response)
    return response


# ═══════════════════════════════════════════
# تصدير PDF باستخدام reportlab + دعم عربي
# ═══════════════════════════════════════════
def _find_arabic_font():
    """Return (regular, bold) font paths — works on Windows and Linux."""
    import platform, os
    if platform.system() == 'Windows':
        return (r'C:\Windows\Fonts\arial.ttf', r'C:\Windows\Fonts\arialbd.ttf')
    # Linux / VPS — common Arabic-capable font locations
    candidates = [
        ('/usr/share/fonts/truetype/freefont/FreeSerif.ttf', '/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf'),
        ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),
        ('/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf', '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'),
    ]
    for reg, bold in candidates:
        if os.path.exists(reg):
            return (reg, bold)
    raise FileNotFoundError('لم يتم العثور على خط عربي. ثبّت fonts-freefont-ttf أو fonts-dejavu')


def _register_arabic_font():
    """Register Arial/fallback as an Arabic-capable font (done once)."""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    if 'Arial' not in pdfmetrics.getRegisteredFontNames():
        reg, bold = _find_arabic_font()
        pdfmetrics.registerFont(TTFont('Arial', reg))
        pdfmetrics.registerFont(TTFont('Arial-Bold', bold))


def _ar(text):
    """Reshape + bidi-reorder Arabic text so reportlab renders it correctly."""
    import arabic_reshaper
    from bidi.algorithm import get_display
    if not text:
        return ''
    text = str(text)
    try:
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except Exception:
        return text


def _pdf_response(filename):
    from django.http import HttpResponse
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response


def _pdf_header(canvas, doc, title, username):
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    _register_arabic_font()
    canvas.saveState()
    canvas.setFillColor(colors.HexColor('#1a3a5c'))
    canvas.rect(0, doc.pagesize[1] - 2*cm, doc.pagesize[0], 2*cm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont('Arial-Bold', 13)
    canvas.drawRightString(doc.pagesize[0] - 1*cm, doc.pagesize[1] - 1.3*cm, _ar(title))
    canvas.setFont('Arial', 8)
    from django.utils import timezone
    now_str = timezone.localtime().strftime('%Y/%m/%d %H:%M')
    canvas.drawString(1*cm, doc.pagesize[1] - 1.3*cm, f'{now_str} | {username}')
    canvas.setFillColor(colors.HexColor('#666666'))
    canvas.setFont('Arial', 8)
    canvas.drawCentredString(doc.pagesize[0]/2, 0.5*cm, _ar('نظام إدارة العملاء'))
    canvas.restoreState()


def _build_table(data, col_widths=None):
    from reportlab.platypus import Table, TableStyle, Paragraph
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_RIGHT
    _register_arabic_font()

    body_style = ParagraphStyle('ar_body', fontName='Arial',     fontSize=8,  alignment=TA_RIGHT, leading=11, wordWrap='CJK')
    head_style = ParagraphStyle('ar_head', fontName='Arial-Bold', fontSize=8, alignment=TA_RIGHT, leading=11, wordWrap='CJK', textColor=colors.white)

    def _cell(text, is_header=False):
        style = head_style if is_header else body_style
        return Paragraph(_ar(str(text)) if text else '', style)

    ar_data = []
    for i, row in enumerate(data):
        ar_data.append([_cell(cell, is_header=(i == 0)) for cell in reversed(row)])

    rtl_widths = list(reversed(col_widths)) if col_widths else None
    t = Table(ar_data, colWidths=rtl_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND',     (0,0), (-1,0),  colors.HexColor('#1a3a5c')),
        ('ALIGN',          (0,0), (-1,-1), 'RIGHT'),
        ('VALIGN',         (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f5f7fa')]),
        ('GRID',           (0,0), (-1,-1), 0.3, colors.HexColor('#dddddd')),
        ('TOPPADDING',     (0,0), (-1,-1), 5),
        ('BOTTOMPADDING',  (0,0), (-1,-1), 5),
        ('LEFTPADDING',    (0,0), (-1,-1), 4),
        ('RIGHTPADDING',   (0,0), (-1,-1), 4),
    ]))
    return t


@login_required
@admin_required
def export_clients_pdf(request):
    import io
    from reportlab.platypus import SimpleDocTemplate, Spacer, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import cm
    from clients.models import Client

    tenant  = request.user.tenant
    clients = Client.objects.filter(tenant=tenant, is_active=True).select_related('assigned_sales','assigned_accountant','activity')

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), rightMargin=1*cm, leftMargin=1*cm,
                            topMargin=2.5*cm, bottomMargin=1.5*cm)
    username = request.user.get_full_name() or request.user.username

    # landscape A4 usable width = 29.7 - 2 margins = 27.7 cm
    col_w = [3.5*cm, 3.5*cm, 3*cm, 3.2*cm, 4*cm, 4*cm, 3.5*cm, 3*cm]  # total 27.7
    rows = [['الاسم','الشركة','المدينة','الجوال','المندوب','المحاسب','النشاط','تاريخ الإضافة']]
    for c in clients:
        rows.append([
            c.name or '', c.company or '', c.city or '', c.phone or '',
            c.assigned_sales.get_full_name() if c.assigned_sales else '—',
            c.assigned_accountant.get_full_name() if c.assigned_accountant else '—',
            c.activity.name if c.activity else '—',
            str(c.created_at.date()) if c.created_at else '',
        ])

    story = [_build_table(rows, col_widths=col_w)]
    doc.build(story, onFirstPage=lambda c,d: _pdf_header(c,d,'تقرير العملاء', username),
                     onLaterPages=lambda c,d: _pdf_header(c,d,'تقرير العملاء', username))
    response = _pdf_response('clients.pdf')
    response.write(buf.getvalue())
    return response


@login_required
@admin_required
def export_commissions_pdf(request):
    import io
    from reportlab.platypus import SimpleDocTemplate
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import cm
    from commissions.models import CommissionSheet
    from django.db.models import Sum

    from commissions.models import CommissionEntry

    tenant      = request.user.tenant
    date_from   = request.GET.get('date_from', '')
    date_to     = request.GET.get('date_to', '')
    role_filter = request.GET.get('role', '')
    user_filter = request.GET.get('user', '')

    entries = CommissionEntry.objects.filter(sheet__tenant=tenant).select_related('client','sheet')
    if date_from:
        entries = entries.filter(sheet__created_at__date__gte=date_from)
    if date_to:
        entries = entries.filter(sheet__created_at__date__lte=date_to)
    if role_filter == 'sales' and user_filter:
        entries = entries.filter(sales_rep_id=user_filter)
    elif role_filter == 'accountant' and user_filter:
        entries = entries.filter(client__assigned_accountant_id=user_filter)
    elif role_filter == 'review' and user_filter:
        entries = entries.filter(client__assigned_review_id=user_filter)

    username = request.user.get_full_name() or request.user.username

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), rightMargin=1*cm, leftMargin=1*cm,
                            topMargin=2.5*cm, bottomMargin=1.5*cm)
    col_w = [7.7*cm, 5*cm, 5*cm, 5*cm, 5*cm]  # total 27.7
    rows = [['الشيت','العميل','المبلغ','عمولة المناديب','عمولة المحاسبين']]
    for e in entries:
        rows.append([
            str(e.sheet), e.client.name if e.client else '—',
            str(round(e.amount or 0, 2)), str(round(e.commission_amount or 0, 2)),
            str(round(e.accountant_commission_amount or 0, 2)),
        ])

    story = [_build_table(rows, col_widths=col_w)]
    doc.build(story, onFirstPage=lambda c,d: _pdf_header(c,d,'تقرير العمولات', username),
                     onLaterPages=lambda c,d: _pdf_header(c,d,'تقرير العمولات', username))
    response = _pdf_response('commissions.pdf')
    response.write(buf.getvalue())
    return response


@login_required
@admin_required
def export_events_pdf(request):
    import io
    from reportlab.platypus import SimpleDocTemplate
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import cm
    from calendar_app.models import Event

    tenant      = request.user.tenant
    date_from   = request.GET.get('date_from', '')
    date_to     = request.GET.get('date_to', '')
    user_filter = request.GET.get('user', '')
    source_filter = request.GET.get('source', '')

    events = Event.objects.filter(tenant=tenant).select_related('assigned_to','client').order_by('-start_datetime')
    if date_from:
        events = events.filter(start_datetime__date__gte=date_from)
    if date_to:
        events = events.filter(start_datetime__date__lte=date_to)
    if user_filter:
        events = events.filter(assigned_to_id=user_filter)
    if source_filter:
        events = events.filter(source=source_filter)
    username = request.user.get_full_name() or request.user.username

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), rightMargin=1*cm, leftMargin=1*cm,
                            topMargin=2.5*cm, bottomMargin=1.5*cm)
    col_w = [5*cm, 3*cm, 3*cm, 4*cm, 4*cm, 3*cm, 5.7*cm]  # total 27.7
    rows = [['العنوان','النوع','الحالة','العميل','المسند إلى','التاريخ','ملاحظات']]
    for e in events:
        rows.append([
            e.title, e.get_event_type_display(), e.get_status_display(),
            e.client.name if e.client else '—',
            e.assigned_to.get_full_name() if e.assigned_to else '—',
            str(e.start_datetime.date()),
            (e.notes or '')[:50],
        ])

    story = [_build_table(rows, col_widths=col_w)]
    doc.build(story, onFirstPage=lambda c,d: _pdf_header(c,d,'تقرير الأحداث', username),
                     onLaterPages=lambda c,d: _pdf_header(c,d,'تقرير الأحداث', username))
    response = _pdf_response('events.pdf')
    response.write(buf.getvalue())
    return response


@login_required
@admin_required
def export_workflow_pdf(request):
    import io
    from reportlab.platypus import SimpleDocTemplate
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import cm
    from workflow.models import ReviewClient

    from workflow.models import WorkflowStage

    tenant        = request.user.tenant
    stage_filter  = request.GET.get('stage', '')
    status_filter = request.GET.get('status', '')

    clients = ReviewClient.objects.filter(tenant=tenant).prefetch_related('stages')
    if stage_filter or status_filter:
        stage_qs = WorkflowStage.objects.filter(client__tenant=tenant)
        if stage_filter:
            stage_qs = stage_qs.filter(stage=stage_filter)
        if status_filter:
            stage_qs = stage_qs.filter(status=status_filter)
        client_ids = stage_qs.values_list('client_id', flat=True).distinct()
        clients = clients.filter(pk__in=client_ids)

    username = request.user.get_full_name() or request.user.username

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), rightMargin=1*cm, leftMargin=1*cm,
                            topMargin=2.5*cm, bottomMargin=1.5*cm)
    col_w = [4*cm, 4*cm, 3.7*cm, 3.5*cm, 3*cm, 3*cm, 3*cm, 3.5*cm]  # total 27.7
    rows = [['العميل','الشركة','المرحلة','الحالة','بداية','نهاية','استحقاق','المدة (يوم)']]
    for client in clients:
        for stage in client.stages.all():
            rows.append([
                client.name, client.company or '',
                stage.get_stage_display(), stage.get_status_display(),
                str(stage.start_date) if stage.start_date else '—',
                str(stage.end_date)   if stage.end_date   else '—',
                str(stage.due_date)   if stage.due_date   else '—',
                str(stage.days_in_stage) if stage.days_in_stage is not None else '—',
            ])

    story = [_build_table(rows, col_widths=col_w)]
    doc.build(story, onFirstPage=lambda c,d: _pdf_header(c,d,'تقرير المراجعة', username),
                     onLaterPages=lambda c,d: _pdf_header(c,d,'تقرير المراجعة', username))
    response = _pdf_response('workflow.pdf')
    response.write(buf.getvalue())
    return response
