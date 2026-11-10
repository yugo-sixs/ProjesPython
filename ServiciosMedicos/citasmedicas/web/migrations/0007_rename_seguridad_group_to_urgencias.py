from django.db import migrations


def rename_security_group(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    alias = schema_editor.connection.alias
    old_group = Group.objects.using(alias).filter(name='Seguridad').first()
    new_group, _ = Group.objects.using(alias).get_or_create(name='Urgencias')
    if old_group is None or old_group.pk == new_group.pk:
        return

    membership_model = Group.user_set.through
    user_ids = membership_model.objects.using(alias).filter(
        group_id=old_group.pk
    ).values_list('user_id', flat=True)
    for user_id in user_ids.iterator():
        membership_model.objects.using(alias).get_or_create(
            group_id=new_group.pk, user_id=user_id,
        )
    old_group.delete(using=alias)


class Migration(migrations.Migration):
    dependencies = [
        ('web', '0006_accesousuario_puede_registrar_urgencias_and_more'),
    ]

    operations = [migrations.RunPython(rename_security_group, migrations.RunPython.noop)]
