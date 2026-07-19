from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('calendar_app', '0003_event_status'),
        ('workflow', '0005_reviewclient_distinguished_number_secret_number'),
        ('zatca', '0004_remove_zatcaclient_status_report_file_completed_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='review_client',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='events', to='workflow.reviewclient',
                verbose_name='عميل المراجعة',
            ),
        ),
        migrations.AddField(
            model_name='event',
            name='zatca_client',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='events', to='zatca.zatcaclient',
                verbose_name='عميل ZATCA',
            ),
        ),
    ]
