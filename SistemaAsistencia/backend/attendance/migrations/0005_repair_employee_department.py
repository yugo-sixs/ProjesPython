from django.db import migrations, models


def add_department_if_missing(apps, schema_editor):
    employee_model = apps.get_model("attendance", "Employee")
    table_name = employee_model._meta.db_table
    column_names = {
        column.name
        for column in schema_editor.connection.introspection.get_table_description(
            schema_editor.connection.cursor(), table_name
        )
    }

    if "department" not in column_names:
        schema_editor.add_field(
            employee_model,
            employee_model._meta.get_field("department"),
        )


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("attendance", "0004_department_position"),
    ]

    operations = [
        migrations.RunPython(add_department_if_missing, migrations.RunPython.noop),
    ]