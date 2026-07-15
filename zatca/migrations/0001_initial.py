from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0005_replace_whatsapp_with_notifications'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ZatcaClient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('company', models.CharField(blank=True, max_length=200)),
                ('phone', models.CharField(blank=True, max_length=30)),
                ('email', models.EmailField(blank=True)),
                ('city', models.CharField(blank=True, max_length=100)),
                ('district', models.CharField(blank=True, max_length=100)),
                ('address', models.TextField(blank=True)),
                ('responsible_person', models.CharField(blank=True, max_length=100)),
                ('job_title', models.CharField(blank=True, max_length=100)),
                ('notes', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('in_progress', 'تحت الإجراء'), ('completed', 'مكتمل')], default='in_progress', max_length=20)),
                ('report_file', models.FileField(blank=True, null=True, upload_to='zatca/reports/', verbose_name='تقرير الإنجاز')),
                ('is_commissionable', models.BooleanField(default=False, verbose_name='خاضع للعمولة')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('assigned_accountant', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='zatca_clients', to=settings.AUTH_USER_MODEL, verbose_name='المحاسب المسند')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_zatca_clients', to=settings.AUTH_USER_MODEL)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='zatca_clients', to='accounts.tenant')),
            ],
            options={
                'verbose_name': 'عميل ZATCA',
                'verbose_name_plural': 'عملاء ZATCA',
                'ordering': ['-created_at'],
            },
        ),
    ]
