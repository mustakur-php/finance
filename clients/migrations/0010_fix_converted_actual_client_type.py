from django.db import migrations


def fix_converted_actual(apps, schema_editor):
    """
    العملاء المحوّلون إلى 'فعلي' كان يُضبط لهم converted_status فقط دون client_type،
    فبقوا في قائمة المستهدفين ولم يظهروا في العملاء الفعليين. نصحّحهم هنا.
    """
    Client = apps.get_model('clients', 'Client')
    Client.objects.filter(
        converted_status='actual', client_type='potential'
    ).update(client_type='actual')


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0009_client_distinguished_number_secret_number'),
    ]

    operations = [
        migrations.RunPython(fix_converted_actual, migrations.RunPython.noop),
    ]
