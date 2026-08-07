from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0006_user_role_add_developer'),
        ('clients', '0011_client_converted_status_choices'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='OneTimeServiceClient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('company', models.CharField(blank=True, max_length=200)),
                ('phone', models.CharField(blank=True, max_length=30)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('city', models.CharField(blank=True, max_length=100)),
                ('district', models.CharField(blank=True, max_length=100)),
                ('address', models.TextField(blank=True)),
                ('responsible_person', models.CharField(blank=True, max_length=100)),
                ('job_title', models.CharField(blank=True, max_length=100)),
                ('notes', models.TextField(blank=True)),
                ('distinguished_number', models.CharField(blank=True, max_length=100, verbose_name='الرقم المميز')),
                ('secret_number', models.CharField(blank=True, max_length=100, verbose_name='الرقم السري')),
                ('is_active', models.BooleanField(default=True, verbose_name='نشط')),
                ('is_commissionable', models.BooleanField(default=False, verbose_name='خاضع للعمولة')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL,
                                                  related_name='created_onetime_clients', to=settings.AUTH_USER_MODEL)),
                ('source_client', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                                     related_name='onetime_copies', to='clients.client', verbose_name='العميل الأصلي')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                             related_name='onetime_clients', to='accounts.tenant')),
            ],
            options={
                'verbose_name': 'عميل خدمة لمرة واحدة',
                'verbose_name_plural': 'عملاء الخدمات لمرة واحدة',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='OneTimeService',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('service_type', models.CharField(max_length=200, verbose_name='نوع الخدمة')),
                ('status', models.CharField(choices=[('in_progress', 'تحت الإجراء'), ('completed', 'مكتملة')],
                                             default='in_progress', max_length=20)),
                ('report_file', models.FileField(blank=True, null=True, upload_to='onetime_services/reports/', verbose_name='التقرير')),
                ('notes', models.TextField(blank=True)),
                ('start_date', models.DateField(verbose_name='تاريخ الفتح')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                                   related_name='onetime_services', to=settings.AUTH_USER_MODEL, verbose_name='المنفّذ')),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                              related_name='services', to='onetime_services.onetimeserviceclient')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL,
                                                  related_name='created_onetime_services', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'خدمة لمرة واحدة',
                'verbose_name_plural': 'الخدمات لمرة واحدة',
                'ordering': ['-start_date'],
            },
        ),
    ]
