from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('commissions', '0011_commissionentry_client_snapshots'),
        ('onetime_services', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='commissionentry',
            name='onetime_client',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='commission_entries', to='onetime_services.onetimeserviceclient',
                verbose_name='عميل خدمة لمرة واحدة',
            ),
        ),
        migrations.AddField(
            model_name='commissionentry',
            name='onetime_service',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='commission_entries', to='onetime_services.onetimeservice',
                verbose_name='خدمة لمرة واحدة',
            ),
        ),
    ]
