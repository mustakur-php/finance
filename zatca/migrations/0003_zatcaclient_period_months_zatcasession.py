from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('zatca', '0002_zatcaclient_distinguished_number_secret_number'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='zatcaclient',
            name='period_months',
            field=models.PositiveSmallIntegerField(
                choices=[(1,'شهري'),(3,'ربع سنوي'),(6,'نصف سنوي'),(12,'سنوي')],
                default=1,
                verbose_name='الفترة',
            ),
        ),
        migrations.CreateModel(
            name='ZatcaSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField(verbose_name='تاريخ البداية')),
                ('end_date', models.DateField(blank=True, null=True, verbose_name='تاريخ الانتهاء')),
                ('status', models.CharField(
                    choices=[('in_progress','تحت الإجراء'),('completed','مكتملة')],
                    default='in_progress', max_length=20,
                )),
                ('report_file', models.FileField(blank=True, null=True, upload_to='zatca/sessions/', verbose_name='تقرير الدورة')),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sessions', to='zatca.zatcaclient')),
                ('created_by', models.ForeignKey(
                    null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name='created_zatca_sessions', to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={'ordering': ['-start_date'], 'verbose_name': 'دورة ZATCA'},
        ),
    ]
