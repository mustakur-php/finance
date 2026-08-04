from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calendar_app', '0004_event_review_client_zatca_client'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='day_reminder_sent',
            field=models.BooleanField(default=False, verbose_name='تم إرسال التذكير الصباحي'),
        ),
    ]
