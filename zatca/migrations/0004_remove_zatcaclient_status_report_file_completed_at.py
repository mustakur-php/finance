from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('zatca', '0003_zatcaclient_period_months_zatcasession'),
    ]

    operations = [
        migrations.RemoveField(model_name='zatcaclient', name='status'),
        migrations.RemoveField(model_name='zatcaclient', name='report_file'),
        migrations.RemoveField(model_name='zatcaclient', name='completed_at'),
    ]
