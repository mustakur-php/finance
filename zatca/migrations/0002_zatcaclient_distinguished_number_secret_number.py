from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zatca', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='zatcaclient',
            name='distinguished_number',
            field=models.CharField(blank=True, max_length=100, verbose_name='الرقم المميز'),
        ),
        migrations.AddField(
            model_name='zatcaclient',
            name='secret_number',
            field=models.CharField(blank=True, max_length=100, verbose_name='الرقم السري'),
        ),
    ]
