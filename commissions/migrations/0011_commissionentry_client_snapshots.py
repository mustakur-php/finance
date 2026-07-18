from django.db import migrations, models


def backfill_snapshots(apps, schema_editor):
    """يملأ النسخة المحفوظة للسطور الموجودة من بيانات عملائها الحالية."""
    CommissionEntry = apps.get_model('commissions', 'CommissionEntry')
    entries = CommissionEntry.objects.select_related(
        'client', 'review_client', 'zatca_client', 'zatca_session__client'
    )
    to_update = []
    for e in entries.iterator():
        src = None
        name = ''
        if e.client_id and e.client:
            src, name = e.client, e.client.name
        elif e.review_client_id and e.review_client:
            src, name = e.review_client, e.review_client.name
        elif e.zatca_session_id and e.zatca_session and e.zatca_session.client:
            src = e.zatca_session.client
            name = f"{src.name} ({e.zatca_session.start_date})"
        elif e.zatca_client_id and e.zatca_client:
            src, name = e.zatca_client, e.zatca_client.name
        if not name:
            continue
        e.client_name_snapshot = name[:250]
        e.client_company_snapshot = (getattr(src, 'company', '') or '')[:250]
        to_update.append(e)
        if len(to_update) >= 500:
            CommissionEntry.objects.bulk_update(
                to_update, ['client_name_snapshot', 'client_company_snapshot'])
            to_update = []
    if to_update:
        CommissionEntry.objects.bulk_update(
            to_update, ['client_name_snapshot', 'client_company_snapshot'])


class Migration(migrations.Migration):

    dependencies = [
        ('commissions', '0010_commissionentry_zatca_session'),
    ]

    operations = [
        migrations.AddField(
            model_name='commissionentry',
            name='client_name_snapshot',
            field=models.CharField(blank=True, max_length=250, verbose_name='اسم العميل (محفوظ)'),
        ),
        migrations.AddField(
            model_name='commissionentry',
            name='client_company_snapshot',
            field=models.CharField(blank=True, max_length=250, verbose_name='الشركة (محفوظة)'),
        ),
        migrations.RunPython(backfill_snapshots, migrations.RunPython.noop),
    ]
