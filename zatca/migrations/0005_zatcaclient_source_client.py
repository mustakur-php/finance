from django.db import migrations, models
import django.db.models.deletion


def link_existing(apps, schema_editor):
    """يربط عملاء ZATCA الموجودين بأصولهم بالمطابقة على الاسم داخل نفس الشركة."""
    ZatcaClient = apps.get_model('zatca', 'ZatcaClient')
    Client = apps.get_model('clients', 'Client')
    for zc in ZatcaClient.objects.filter(source_client__isnull=True).iterator():
        matches = list(Client.objects.filter(tenant_id=zc.tenant_id, name=zc.name)[:2])
        if len(matches) == 1:
            zc.source_client = matches[0]
            zc.save(update_fields=['source_client'])


class Migration(migrations.Migration):

    dependencies = [
        ('zatca', '0004_remove_zatcaclient_status_report_file_completed_at'),
        ('clients', '0010_fix_converted_actual_client_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='zatcaclient',
            name='source_client',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='zatca_copies', to='clients.client',
                verbose_name='العميل الأصلي',
            ),
        ),
        migrations.RunPython(link_existing, migrations.RunPython.noop),
    ]
