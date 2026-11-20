from django.db import migrations


DEFAULT_GROUPS = ['Administrador', 'Doctor', 'Secretaria', 'Enfermera', 'Administrativo']


def create_default_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    for name in DEFAULT_GROUPS:
        Group.objects.using(schema_editor.connection.alias).get_or_create(name=name)


class Migration(migrations.Migration):
    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('web', '0003_medicamento_paciente_alergias_paciente_antecedentes_and_more'),
    ]

    operations = [migrations.RunPython(create_default_groups, migrations.RunPython.noop)]
