from django.db import models

# Create your models here.
from django.db import models


# ==============================================
# TABLA: ESTATUS
# ==============================================
class Estatus(models.Model):
    nombre = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre



    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)
    rol = models.ForeignKey(Rol, on_delete=models.PROTECT, null=True, blank=True)
    estatus = models.ForeignKey(Estatus, on_delete=models.PROTECT, default=1)

    def __str__(self):
        return self.username


# ==============================================
# TABLA: ESPECIALIDAD (solo doctores)
# ==============================================
class Especialidad(models.Model):
    nombre = models.CharField(max_length=100, null=True, blank=True)
    descripcion = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.nombre or "Sin especialidad"


# ==============================================
# TABLA: PERSONAL (doctores, secretarias, enfermeras, etc.)
# ==============================================
class Personal(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT, null=True, blank=True)
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
        return f"{self.nombre} ({self.usuario.rol.nombre if self.usuario and self.usuario.rol else 'Sin rol'})"


# ==============================================
# TABLA: PACIENTE
# ==============================================
class Paciente(models.Model):
    tarjeton = models.IntegerField(null=True, blank=True)
    nombre = models.CharField(max_length=100, null=True, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    sexo = models.CharField(max_length=10, null=True, blank=True)
    curp = models.CharField(max_length=20, unique=True, null=True, blank=True)
    estatus = models.ForeignKey(Estatus, on_delete=models.PROTECT, default=1)

    def __str__(self):
        return self.nombre or "Paciente sin nombre"


# ==============================================
# TABLA: CITA
# ==============================================
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
    creada_por = models.ForeignKey(Usuario, on_delete=models.PROTECT, null=True, blank=True, related_name='citas_creadas')
    estatus = models.ForeignKey(Estatus, on_delete=models.PROTECT, default=1)

    def __str__(self):
        return f"Cita {self.id} - {self.paciente} ({self.estado})"
