from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("attendance", "0002_employee_role_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="workscheduleday",
            name="food_break_minutes",
            field=models.PositiveSmallIntegerField(default=60),
        ),
    ]