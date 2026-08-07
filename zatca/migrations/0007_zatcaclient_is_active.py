from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zatca', '0006_zatcasession_assigned_accountant'),
    ]

    operations = [
        migrations.AddField(
            model_name='zatcaclient',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='نشط'),
        ),
    ]
