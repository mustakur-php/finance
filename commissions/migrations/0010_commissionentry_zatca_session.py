from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('commissions', '0009_commissionentry_zatca_client'),
        ('zatca', '0003_zatcaclient_period_months_zatcasession'),
    ]

    operations = [
        migrations.AddField(
            model_name='commissionentry',
            name='zatca_session',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='commission_entries',
                to='zatca.zatcasession',
                verbose_name='دورة ZATCA',
            ),
        ),
    ]
