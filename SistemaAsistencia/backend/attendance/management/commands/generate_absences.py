from django.core.management.base import BaseCommand
from django.utils import timezone

from attendance.models import Attendance, Employee
from attendance.services import get_employee_schedule_day


class Command(BaseCommand):
    help = "Genera asistencias con estado FALTA para empleados activos sin entrada registrada."

    def add_arguments(self, parser):
        parser.add_argument("--date", help="Fecha en formato YYYY-MM-DD. Por defecto usa ayer.")

    def handle(self, *args, **options):
        if options["date"]:
            work_date = timezone.datetime.fromisoformat(options["date"]).date()
        else:
            work_date = timezone.localdate() - timezone.timedelta(days=1)

        created = 0
        skipped = 0

        for employee in Employee.objects.filter(status=Employee.Status.ACTIVE):
            schedule_day = get_employee_schedule_day(employee, work_date)
            if schedule_day is None or schedule_day.is_rest_day:
                skipped += 1
                continue

            _, was_created = Attendance.objects.get_or_create(
                employee=employee,
                date=work_date,
                defaults={
                    "schedule_day": schedule_day,
                    "status": Attendance.Status.ABSENT,
                },
            )
            created += int(was_created)

        self.stdout.write(
            self.style.SUCCESS(f"Faltas generadas: {created}. Registros omitidos: {skipped}. Fecha: {work_date}")
        )
