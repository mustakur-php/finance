from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('zatca', '0005_zatcaclient_source_client'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='zatcasession',
            name='assigned_accountant',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='zatca_sessions', to=settings.AUTH_USER_MODEL,
                verbose_name='محاسب الدورة',
            ),
        ),
    ]
