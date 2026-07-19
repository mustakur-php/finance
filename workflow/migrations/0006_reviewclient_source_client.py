from django.db import migrations, models
import django.db.models.deletion


def link_existing(apps, schema_editor):
    """
    يربط نسخ المراجعة الموجودة بعملائها الأصليين بالمطابقة على الاسم داخل نفس الشركة.
    يتجاهل الحالات الملتبسة (أكثر من مطابقة) تجنّباً لربط خاطئ.
    """
    ReviewClient = apps.get_model('workflow', 'ReviewClient')
    Client = apps.get_model('clients', 'Client')
    for rc in ReviewClient.objects.filter(source_client__isnull=True).iterator():
        matches = list(Client.objects.filter(tenant_id=rc.tenant_id, name=rc.name)[:2])
        if len(matches) == 1:
            rc.source_client = matches[0]
            rc.save(update_fields=['source_client'])


class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0005_reviewclient_distinguished_number_secret_number'),
        ('clients', '0010_fix_converted_actual_client_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='reviewclient',
            name='source_client',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='review_copies', to='clients.client',
                verbose_name='العميل الأصلي',
            ),
        ),
        migrations.RunPython(link_existing, migrations.RunPython.noop),
    ]
