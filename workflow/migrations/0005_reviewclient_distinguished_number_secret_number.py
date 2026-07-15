from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0004_reviewclient_is_commissionable'),
    ]

    operations = [
        migrations.AddField(
            model_name='reviewclient',
            name='distinguished_number',
            field=models.CharField(blank=True, max_length=100, verbose_name='الرقم المميز'),
        ),
        migrations.AddField(
            model_name='reviewclient',
            name='secret_number',
            field=models.CharField(blank=True, max_length=100, verbose_name='الرقم السري'),
        ),
    ]
