from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('commissions', '0002_commissionentry_entry_date_commissionentry_is_confirmed'),
        ('zatca', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='commissionentry',
            name='zatca_client',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='commission_entries',
                to='zatca.zatcaclient',
                verbose_name='عميل ZATCA',
            ),
        ),
    ]
