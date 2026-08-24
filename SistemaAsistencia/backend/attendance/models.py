from django.conf import settings
from django.db import models


class Employee(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVO", "Activo"
        INACTIVE = "BAJA", "Baja"
        SUSPENDED = "SUSPENDIDO", "Suspendido"

    class RoleType(models.TextChoices):
        WORKER = "WORKER", "Trabajador"
        RH = "RH", "RH"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="employee")
    employee_number = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30, blank=True)
    department = models.CharField(max_length=100, blank=True)
    position = models.CharField(max_length=100, blank=True)
    role_type = models.CharField(max_length=20, choices=RoleType.choices, default=RoleType.WORKER)
    hire_date = models.DateField(null=True, blank=True)
    termination_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "empleados"

    def __str__(self):
        return f"{self.employee_number} - {self.first_name} {self.last_name}"


class WorkSchedule(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "horarios"

    def __str__(self):
        return self.name


class WorkScheduleDay(models.Model):
    class Weekday(models.IntegerChoices):
        MONDAY = 1, "Lunes"
        TUESDAY = 2, "Martes"
        WEDNESDAY = 3, "Miercoles"
        THURSDAY = 4, "Jueves"
        FRIDAY = 5, "Viernes"
        SATURDAY = 6, "Sabado"
        SUNDAY = 7, "Domingo"

    schedule = models.ForeignKey(WorkSchedule, on_delete=models.CASCADE, related_name="days")
    weekday = models.PositiveSmallIntegerField(choices=Weekday.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    tolerance_minutes = models.PositiveSmallIntegerField(default=10)
    regular_hours = models.DecimalField(max_digits=5, decimal_places=2, default=8)
    is_rest_day = models.BooleanField(default=False)

    class Meta:
        db_table = "horarios_dia"
        unique_together = ("schedule", "weekday")
        ordering = ["weekday"]

    def __str__(self):
        return f"{self.schedule.name} - {self.get_weekday_display()}"


class EmployeeSchedule(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="schedule_assignments")
    schedule = models.ForeignKey(WorkSchedule, on_delete=models.PROTECT, related_name="employee_assignments")
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "empleados_horarios"
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.employee} -> {self.schedule}"


class Attendance(models.Model):
    class Status(models.TextChoices):
        ON_TIME = "PUNTUAL", "Puntual"
        TOLERANCE = "TOLERANCIA", "Tolerancia"
        LATE = "RETARDO", "Retardo"
        ABSENT = "FALTA", "Falta"
        JUSTIFIED = "JUSTIFICADO", "Justificado"
        REST = "DESCANSO", "Descanso"
        PERMISSION = "PERMISO", "Permiso"
        MEDICAL_LEAVE = "INCAPACIDAD", "Incapacidad"
        VACATION = "VACACIONES", "Vacaciones"
        OTHER = "OTRO", "Otro"

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="attendances")
    date = models.DateField()
    schedule_day = models.ForeignKey(WorkScheduleDay, on_delete=models.SET_NULL, null=True, blank=True)
    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, null=True, blank=True)
    total_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "asistencias"
        unique_together = ("employee", "date")
        ordering = ["-date", "employee__employee_number"]

    def __str__(self):
        return f"{self.employee} - {self.date}"


class AttendanceRecord(models.Model):
    class RecordType(models.TextChoices):
        CHECK_IN = "ENTRADA", "Entrada"
        CHECK_OUT = "SALIDA", "Salida"

    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE, related_name="records")
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="attendance_records")
    record_type = models.CharField(max_length=10, choices=RecordType.choices)
    device_date = models.DateField()
    device_time = models.TimeField()
    device_datetime = models.DateTimeField()
    server_datetime = models.DateTimeField(auto_now_add=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    gps_accuracy = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    employee_photo = models.ImageField(upload_to="attendance/employee/", null=True, blank=True)
    environment_photo = models.ImageField(upload_to="attendance/environment/", null=True, blank=True)
    device_id = models.CharField(max_length=255, blank=True)
    source_ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "registros_asistencia"
        ordering = ["-device_datetime"]


class Justification(models.Model):
    class Type(models.TextChoices):
        JUSTIFIED = "JUSTIFICADO", "Justificado"
        PERMISSION = "PERMISO", "Permiso"
        MEDICAL_LEAVE = "INCAPACIDAD", "Incapacidad"
        VACATION = "VACACIONES", "Vacaciones"
        REST = "DESCANSO", "Descanso"
        OTHER = "OTRO", "Otro"

    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE, related_name="justifications")
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="justifications")
    justification_type = models.CharField(max_length=20, choices=Type.choices)
    reason = models.TextField()
    attachment = models.FileField(upload_to="justifications/", null=True, blank=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="approved_justifications")
    approved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "justificaciones"
