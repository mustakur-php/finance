from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0006_user_role_add_developer'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SolutionMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('body', models.TextField(verbose_name='النص')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('sender', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL,
                                              related_name='solution_messages', to=settings.AUTH_USER_MODEL)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                              related_name='solution_messages', to='accounts.tenant')),
            ],
            options={
                'verbose_name': 'رسالة حلول التطبيقات',
                'verbose_name_plural': 'رسائل حلول التطبيقات',
                'ordering': ['created_at'],
            },
        ),
    ]
