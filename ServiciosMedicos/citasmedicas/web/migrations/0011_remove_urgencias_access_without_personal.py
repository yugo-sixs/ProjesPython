from django.db import migrations


def remove_unlinked_urgencias_memberships(apps, schema_editor):
    PermissionGroup = apps.get_model('web', 'GrupoPermiso')
    Personal = apps.get_model('web', 'Personal')
    alias = schema_editor.connection.alias
    membership = PermissionGroup.usuarios.through

    groups = PermissionGroup.objects.using(alias).filter(
        puede_registrar_urgencias=True
    )
    for group in groups:
        user_ids = membership.objects.using(alias).filter(
            grupopermiso_id=group.pk
        ).values_list('user_id', flat=True)
        for user_id in user_ids.iterator():
            if not Personal.objects.using(alias).filter(usuario_id=user_id).exists():
                membership.objects.using(alias).filter(
                    grupopermiso_id=group.pk, user_id=user_id,
                ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('web', '0010_remove_accesousuario_puede_registrar_urgencias_and_more'),
    ]

    operations = [
        migrations.RunPython(
            remove_unlinked_urgencias_memberships,
            migrations.RunPython.noop,
        ),
    ]
