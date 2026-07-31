from django.conf import settings
from django.db import models


class Estatus(models.Model):
    nombre = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre


class Especialidad(models.Model):
    nombre = models.CharField(max_length=100, null=True, blank=True)
    descripcion = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.nombre or "Sin especialidad"


class Personal(models.Model):
    DOCTOR = 'DOCTOR'
    ENFERMERA = 'ENFERMERA'
    SECRETARIA = 'SECRETARIA'
    ADMINISTRATIVO = 'ADMINISTRATIVO'

    TIPO_PERSONAL_CHOICES = [
        (DOCTOR, 'Doctor'),
        (ENFERMERA, 'Enfermera'),
        (SECRETARIA, 'Secretaria'),
        (ADMINISTRATIVO, 'Administrativo'),
    ]

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    tipo_personal = models.CharField(
        max_length=20,
        choices=TIPO_PERSONAL_CHOICES,
        default=ADMINISTRATIVO,
    )
    nombre = models.CharField(max_length=100, null=True, blank=True)
    apellidopaterno = models.CharField(max_length=100, null=True, blank=True)
    apellidomaterno = models.CharField(max_length=100, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    numempleado = models.IntegerField(null=True, blank=True)
    cedula_profesional = models.CharField(max_length=50, null=True, blank=True)
    especialidad = models.ForeignKey(Especialidad, on_delete=models.PROTECT, null=True, blank=True)
    correo = models.EmailField(max_length=100, null=True, blank=True)
    estatus = models.ForeignKey(Estatus, on_delete=models.PROTECT, default=1)

    def __str__(self):
        nombre = self.nombre or "Personal sin nombre"
        return f"{nombre} ({self.get_tipo_personal_display()})"


class Paciente(models.Model):
    tarjeton = models.IntegerField(null=True, blank=True)
    nombre = models.CharField(max_length=100, null=True, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    sexo = models.CharField(max_length=10, null=True, blank=True)
    curp = models.CharField(max_length=20, unique=True, null=True, blank=True)
    estatus = models.ForeignKey(Estatus, on_delete=models.PROTECT, default=1)

    def __str__(self):
        return self.nombre or "Paciente sin nombre"


class Cita(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('CONFIRMADA', 'Confirmada'),
        ('CANCELADA', 'Cancelada'),
        ('ATENDIDA', 'Atendida'),
    ]

    paciente = models.ForeignKey(Paciente, on_delete=models.PROTECT, null=True, blank=True)
    doctor = models.ForeignKey(Personal, on_delete=models.PROTECT, null=True, blank=True, related_name='citas_doctor')
    fecha_cita = models.DateField(null=True, blank=True)
    hora_inicio = models.TimeField(null=True, blank=True)
    motivo = models.TextField(null=True, blank=True)
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='PENDIENTE')
    creada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='citas_creadas',
    )
    estatus = models.ForeignKey(Estatus, on_delete=models.PROTECT, default=1)

    def __str__(self):
        return f"Cita {self.id} - {self.paciente} ({self.estado})"
