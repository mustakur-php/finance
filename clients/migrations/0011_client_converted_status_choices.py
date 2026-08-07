from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0010_fix_converted_actual_client_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='client',
            name='converted_status',
            field=models.CharField(
                blank=True, max_length=10,
                choices=[
                    ('', 'لم يُحوَّل'),
                    ('actual', 'تم التحويل لعميل فعلي'),
                    ('review', 'تم التحويل لقسم المراجعة'),
                    ('zatca', 'تم التحويل لقسم ZATCA'),
                    ('onetime', 'تم التحويل لخدمة لمرة واحدة'),
                ],
                default='', verbose_name='حالة التحويل',
            ),
        ),
    ]
