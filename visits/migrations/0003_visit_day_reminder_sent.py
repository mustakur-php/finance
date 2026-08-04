from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('visits', '0002_visit_reminder_sent'),
    ]

    operations = [
        migrations.AddField(
            model_name='visit',
            name='day_reminder_sent',
            field=models.BooleanField(default=False, verbose_name='تم إرسال التذكير الصباحي'),
        ),
    ]
