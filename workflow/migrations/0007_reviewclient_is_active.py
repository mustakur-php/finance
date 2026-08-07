from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0006_reviewclient_source_client'),
    ]

    operations = [
        migrations.AddField(
            model_name='reviewclient',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='نشط'),
        ),
    ]
