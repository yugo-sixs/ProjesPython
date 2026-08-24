from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from attendance.models import Employee


class Command(BaseCommand):
    help = "Crea usuarios demo para admin, RH y trabajador."

    def handle(self, *args, **options):
        User = get_user_model()

        admin_user, _ = User.objects.get_or_create(
            username="admin",
            defaults={"is_staff": True, "is_superuser": True, "email": "admin@example.com"},
        )
        admin_user.set_password("admin123456")
        admin_user.save()

        rh_user, _ = User.objects.get_or_create(
            username="rh",
            defaults={"is_staff": True, "is_superuser": False, "email": "rh@example.com"},
        )
        rh_user.set_password("rh123456")
        rh_user.save()

        worker_user, _ = User.objects.get_or_create(
            username="trabajador",
            defaults={"is_staff": False, "is_superuser": False, "email": "trabajador@example.com"},
        )
        worker_user.set_password("trabajador123")
        worker_user.save()

        Employee.objects.get_or_create(
            user=admin_user,
            defaults={"employee_number": "ADM-001", "first_name": "Administrador", "last_name": "Sistema", "status": Employee.Status.ACTIVE},
        )
        Employee.objects.get_or_create(
            user=rh_user,
            defaults={"employee_number": "RH-001", "first_name": "Recursos", "last_name": "Humanos", "status": Employee.Status.ACTIVE},
        )
        Employee.objects.get_or_create(
            user=worker_user,
            defaults={"employee_number": "EMP-001", "first_name": "Juan", "last_name": "Pérez", "status": Employee.Status.ACTIVE},
        )

        self.stdout.write(self.style.SUCCESS("Usuarios demo creados correctamente."))
        self.stdout.write("- admin / admin123456")
        self.stdout.write("- rh / rh123456")
        self.stdout.write("- trabajador / trabajador123")
