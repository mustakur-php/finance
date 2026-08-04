from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_replace_whatsapp_with_notifications'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[
                    ('admin', 'أدمن'),
                    ('sales', 'مندوب'),
                    ('accountant', 'محاسب'),
                    ('review', 'مراجعة'),
                    ('developer', 'مطور'),
                ],
                default='sales', max_length=20,
            ),
        ),
    ]
