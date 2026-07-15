from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('commissions', '0008_commissionentry_accountant_rep_and_more'),
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
