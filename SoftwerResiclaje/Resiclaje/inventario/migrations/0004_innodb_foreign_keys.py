from django.db import migrations


TABLES = (
    "auth_group", "auth_group_permissions", "auth_permission", "django_admin_log",
    "django_content_type", "django_migrations", "django_session",
    "inventario_cortecajaempleado", "inventario_detallecompra", "inventario_detalleventa",
    "inventario_entregaefectivo", "inventario_historialprecio", "inventario_inventariomovimiento",
    "inventario_material", "inventario_operacioncompra", "inventario_operacionventa",
    "inventario_socio", "inventario_usuario", "inventario_usuario_groups",
    "inventario_usuario_user_permissions",
)

FOREIGN_KEYS = (
    ("auth_group_permissions", "group_id", "fk_auth_gp_group", "auth_group"),
    ("auth_group_permissions", "permission_id", "fk_auth_gp_permission", "auth_permission"),
    ("auth_permission", "content_type_id", "fk_auth_perm_content_type", "django_content_type"),
    ("django_admin_log", "content_type_id", "fk_admin_log_content_type", "django_content_type"),
    ("django_admin_log", "user_id", "fk_admin_log_user", "inventario_usuario"),
    ("inventario_cortecajaempleado", "cerrado_por_id", "fk_inv_corte_cerrado_por", "inventario_usuario"),
    ("inventario_cortecajaempleado", "empleado_id", "fk_inv_corte_empleado", "inventario_usuario"),
    ("inventario_detallecompra", "compra_id", "fk_inv_detcompra_compra", "inventario_operacioncompra"),
    ("inventario_detallecompra", "material_id", "fk_inv_detcompra_material", "inventario_material"),
    ("inventario_detalleventa", "venta_id", "fk_inv_detventa_venta", "inventario_operacionventa"),
    ("inventario_detalleventa", "material_id", "fk_inv_detventa_material", "inventario_material"),
    ("inventario_entregaefectivo", "autorizada_por_id", "fk_inv_efectivo_autorizador", "inventario_usuario"),
    ("inventario_entregaefectivo", "empleado_id", "fk_inv_efectivo_empleado", "inventario_usuario"),
    ("inventario_historialprecio", "material_id", "fk_inv_histprecio_material", "inventario_material"),
    ("inventario_historialprecio", "usuario_id", "fk_inv_histprecio_usuario", "inventario_usuario"),
    ("inventario_inventariomovimiento", "compra_id", "fk_inv_mov_compra", "inventario_operacioncompra"),
    ("inventario_inventariomovimiento", "material_id", "fk_inv_mov_material", "inventario_material"),
    ("inventario_inventariomovimiento", "usuario_id", "fk_inv_mov_usuario", "inventario_usuario"),
    ("inventario_inventariomovimiento", "venta_id", "fk_inv_mov_venta", "inventario_operacionventa"),
    ("inventario_operacioncompra", "cancelado_por_id", "fk_inv_compra_cancelador", "inventario_usuario"),
    ("inventario_operacioncompra", "empleado_id", "fk_inv_compra_empleado", "inventario_usuario"),
    ("inventario_operacioncompra", "socio_id", "fk_inv_compra_socio", "inventario_socio"),
    ("inventario_operacionventa", "cancelado_por_id", "fk_inv_venta_cancelador", "inventario_usuario"),
    ("inventario_operacionventa", "empleado_id", "fk_inv_venta_empleado", "inventario_usuario"),
    ("inventario_operacionventa", "socio_id", "fk_inv_venta_socio", "inventario_socio"),
    ("inventario_usuario_groups", "group_id", "fk_inv_usergroup_group", "auth_group"),
    ("inventario_usuario_groups", "usuario_id", "fk_inv_usergroup_user", "inventario_usuario"),
    ("inventario_usuario_user_permissions", "permission_id", "fk_inv_userperm_permission", "auth_permission"),
    ("inventario_usuario_user_permissions", "usuario_id", "fk_inv_userperm_user", "inventario_usuario"),
)


def enforce_innodb_and_foreign_keys(apps, schema_editor):
    connection = schema_editor.connection
    quote = connection.ops.quote_name
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT TABLE_NAME FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME IN (%s)" % ",".join(["%s"] * len(TABLES)),
            TABLES,
        )
        existing_tables = {row[0] for row in cursor.fetchall()}
        for table in TABLES:
            if table in existing_tables:
                cursor.execute(f"ALTER TABLE {quote(table)} ENGINE=InnoDB")

        for table, column, name, referenced_table in FOREIGN_KEYS:
            if table not in existing_tables or referenced_table not in existing_tables:
                continue
            cursor.execute(
                "SELECT 1 FROM information_schema.KEY_COLUMN_USAGE "
                "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s "
                "AND COLUMN_NAME = %s AND REFERENCED_TABLE_NAME IS NOT NULL LIMIT 1",
                (table, column),
            )
            if cursor.fetchone():
                continue
            cursor.execute(
                f"ALTER TABLE {quote(table)} ADD CONSTRAINT {quote(name)} "
                f"FOREIGN KEY ({quote(column)}) REFERENCES {quote(referenced_table)} ({quote('id')})"
            )


class Migration(migrations.Migration):
    atomic = False

    dependencies = [("inventario", "0003_cortecajaempleado_entregaefectivo_and_more")]

    operations = [migrations.RunPython(enforce_innodb_and_foreign_keys, migrations.RunPython.noop)]
