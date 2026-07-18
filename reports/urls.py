from django.urls import path
from . import views

urlpatterns = [
    path('',                      views.reports_home,           name='reports_home'),
    path('clients/',              views.report_clients,          name='report_clients'),
    path('commissions/',          views.report_commissions,      name='report_commissions'),
    path('events/',               views.report_events,           name='report_events'),
    path('workflow/',             views.report_workflow,         name='report_workflow'),
    path('zatca/',                views.report_zatca,            name='report_zatca'),
    path('users/',                views.report_users,            name='report_users'),

    # تصدير Excel
    path('clients/excel/',        views.export_clients_excel,    name='export_clients_excel'),
    path('commissions/excel/',    views.export_commissions_excel,name='export_commissions_excel'),
    path('events/excel/',         views.export_events_excel,     name='export_events_excel'),
    path('workflow/excel/',       views.export_workflow_excel,   name='export_workflow_excel'),
    path('zatca/excel/',          views.export_zatca_excel,      name='export_zatca_excel'),

    # تصدير PDF
    path('clients/pdf/',          views.export_clients_pdf,      name='export_clients_pdf'),
    path('commissions/pdf/',      views.export_commissions_pdf,  name='export_commissions_pdf'),
    path('events/pdf/',           views.export_events_pdf,       name='export_events_pdf'),
    path('workflow/pdf/',         views.export_workflow_pdf,     name='export_workflow_pdf'),
    path('zatca/pdf/',            views.export_zatca_pdf,        name='export_zatca_pdf'),
]
