from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0008_client_converted_at_client_converted_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='distinguished_number',
            field=models.CharField(blank=True, max_length=100, verbose_name='الرقم المميز'),
        ),
        migrations.AddField(
            model_name='client',
            name='secret_number',
            field=models.CharField(blank=True, max_length=100, verbose_name='الرقم السري'),
        ),
    ]
