from datetime import timedelta

from django.conf import settings
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.utils import timezone


class Estatus(models.Model):
    nombre = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre


class AccesoUsuario(models.Model):
    VISTA_INICIO_CHOICES = [
        ('AUTO', 'Automática según permisos'),
        ('INICIO', 'Inicio'),
        ('AGENDA', 'Agenda médica'),
        ('CITAS', 'Citas'),
        ('PACIENTES', 'Pacientes'),
        ('INVENTARIO', 'Inventario'),
        ('URGENCIAS', 'Urgencias'),
    ]

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='accesousuario'
    )
    vista_inicio = models.CharField(max_length=15, choices=VISTA_INICIO_CHOICES, default='AUTO')
    puede_registrar_pacientes = models.BooleanField(default=False, verbose_name='Acceso a pacientes (alta y consulta)')
    puede_ver_expedientes = models.BooleanField(default=False)
    puede_agendar_citas = models.BooleanField(default=False)
    puede_atender_citas = models.BooleanField(default=False)
    puede_ver_inventario = models.BooleanField(default=False)
    puede_ver_urgencias = models.BooleanField(default=False)
    puede_valorar_urgencias = models.BooleanField(default=False)

    def __str__(self):
        return f"Accesos de {self.usuario.username}"


class GrupoPermiso(models.Model):
    nombre = models.CharField(max_length=80, unique=True)
    puede_registrar_urgencias = models.BooleanField(default=False)
    usuarios = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name='grupos_permiso'
    )

    class Meta:
        verbose_name = 'grupo de permisos'
        verbose_name_plural = 'grupos de permisos'

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
    SEGURIDAD = 'SEGURIDAD'

    TIPO_PERSONAL_CHOICES = [
        (DOCTOR, 'Doctor'),
        (ENFERMERA, 'Enfermera'),
        (SECRETARIA, 'Secretaria'),
        (ADMINISTRATIVO, 'Administrativo'),
        (SEGURIDAD, 'Personal de apoyo'),
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
    apellidopaterno = models.CharField(max_length=100, blank=True)
    apellidomaterno = models.CharField(max_length=100, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    correo = models.EmailField(blank=True)
    domicilio = models.TextField(blank=True)
    alergias = models.TextField(blank=True)
    antecedentes = models.TextField(blank=True)
    estatus = models.ForeignKey(Estatus, on_delete=models.PROTECT, default=1)

    def __str__(self):
        return " ".join(filter(None, [self.nombre, self.apellidopaterno, self.apellidomaterno])) or "Paciente sin nombre"


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


class RecepcionUrgencias(models.Model):
    ACCESO_PROPIO = 'ACCESO_PROPIO'
    AMBULANCIA = 'AMBULANCIA'
    MEDIO_INGRESO_CHOICES = [
        (ACCESO_PROPIO, 'Acceso propio'),
        (AMBULANCIA, 'Ambulancia'),
    ]
    ESTADO_CHOICES = [
        ('EN_ESPERA', 'En espera de valoración'),
        ('EN_ATENCION', 'En atención médica'),
        ('HOSPITALIZADO', 'Ingresado a hospitalización'),
        ('REFERIDO', 'Referido a otra unidad'),
        ('EGRESO', 'Egreso'),
    ]
    TRIAGE_CHOICES = [
        ('ROJO', 'Rojo'),
        ('NARANJA', 'Naranja'),
        ('AMARILLO', 'Amarillo'),
        ('VERDE', 'Verde'),
        ('AZUL', 'Azul'),
    ]

    folio = models.CharField(
        max_length=8,
        unique=True,
        editable=False,
        validators=[RegexValidator(r'^\d{8}$', 'El folio debe tener ocho dígitos.')],
    )
    paciente = models.ForeignKey(
        Paciente, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='recepciones_urgencias',
    )
    cita = models.ForeignKey(
        Cita, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='recepciones_urgencias',
    )
    nombre_completo = models.CharField(max_length=240)
    fecha_ingreso = models.DateTimeField(default=timezone.now)
    medio_ingreso = models.CharField(max_length=15, choices=MEDIO_INGRESO_CHOICES)
    ambulancia_institucion = models.CharField(max_length=120, blank=True)
    ambulancia_unidad = models.CharField(max_length=40, blank=True)
    ambulancia_procedencia = models.CharField(max_length=160, blank=True)
    ambulancia_entrega = models.CharField(max_length=160, blank=True)
    ambulancia_observaciones = models.TextField(blank=True)
    registrado_por = models.ForeignKey(
        Personal, on_delete=models.PROTECT, related_name='recepciones_urgencias_registradas',
    )
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='EN_ESPERA')
    valorado_por = models.ForeignKey(
        Personal, on_delete=models.PROTECT, null=True, blank=True,
        related_name='recepciones_urgencias_valoradas',
    )
    fecha_valoracion = models.DateTimeField(null=True, blank=True)
    triage = models.CharField(max_length=10, choices=TRIAGE_CHOICES, blank=True)
    diagnostico_presuntivo = models.TextField(blank=True)
    manejo_inicial = models.TextField(blank=True)
    pronostico_inicial = models.TextField(blank=True)
    fecha_salida = models.DateTimeField(null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_ingreso', '-id']

    @property
    def limite_12_horas(self):
        return self.fecha_ingreso + timedelta(hours=12)

    @property
    def minutos_restantes(self):
        if self.fecha_salida:
            return None
        restante = self.limite_12_horas - timezone.now()
        return max(0, int(restante.total_seconds() // 60))

    @property
    def excedio_12_horas(self):
        return self.fecha_salida is None and timezone.now() >= self.limite_12_horas

    @property
    def minutos_hasta_valoracion(self):
        if not self.fecha_valoracion:
            return None
        return max(0, int((self.fecha_valoracion - self.fecha_ingreso).total_seconds() // 60))

    def __str__(self):
        return f"Urgencias {self.folio} - {self.nombre_completo}"


class Consulta(models.Model):
    cita = models.OneToOneField(Cita, on_delete=models.PROTECT, related_name='consulta')
    fecha_atencion = models.DateTimeField(auto_now_add=True)
    sintomas = models.TextField()
    diagnostico = models.TextField()
    notas = models.TextField(blank=True)
    peso_kg = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True,
                                  validators=[MinValueValidator(0)])
    talla_cm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True,
                                   validators=[MinValueValidator(0)])
    presion_arterial = models.CharField(max_length=20, blank=True)
    temperatura_c = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)

    def __str__(self):
        return f"Consulta {self.id} - {self.cita.paciente}"


class Medicamento(models.Model):
    nombre = models.CharField(max_length=150, unique=True)
    presentacion = models.CharField(max_length=120, blank=True)
    existencia = models.PositiveIntegerField(default=0)
    existencia_minima = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)

    @property
    def requiere_reabasto(self):
        return self.existencia <= self.existencia_minima

    def __str__(self):
        return f"{self.nombre} ({self.existencia} en existencia)"


class Receta(models.Model):
    consulta = models.ForeignKey(Consulta, on_delete=models.PROTECT, related_name='recetas')
    medicamento = models.ForeignKey(Medicamento, on_delete=models.PROTECT, related_name='recetas')
    dosis = models.CharField(max_length=120)
    frecuencia = models.CharField(max_length=120)
    duracion = models.CharField(max_length=120)
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    indicaciones = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.medicamento.nombre} para {self.consulta.cita.paciente}"


class Estudio(models.Model):
    ESTATUS_CHOICES = [
        ('SOLICITADO', 'Solicitado'),
        ('REALIZADO', 'Realizado'),
        ('CANCELADO', 'Cancelado'),
    ]
    consulta = models.ForeignKey(Consulta, on_delete=models.PROTECT, related_name='estudios')
    nombre = models.CharField(max_length=160)
    indicaciones = models.TextField(blank=True)
    resultado = models.TextField(blank=True)
    estatus = models.CharField(max_length=15, choices=ESTATUS_CHOICES, default='SOLICITADO')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_resultado = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.nombre} - {self.consulta.cita.paciente}"


class MovimientoInventario(models.Model):
    ENTRADA = 'ENTRADA'
    DISPENSACION = 'DISPENSACION'
    AJUSTE = 'AJUSTE'
    TIPO_CHOICES = [
        (ENTRADA, 'Entrada'),
        (DISPENSACION, 'Dispensación por receta'),
        (AJUSTE, 'Ajuste'),
    ]
    medicamento = models.ForeignKey(Medicamento, on_delete=models.PROTECT, related_name='movimientos')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    existencia_resultante = models.PositiveIntegerField()
    receta = models.ForeignKey(Receta, on_delete=models.PROTECT, null=True, blank=True,
                              related_name='movimientos')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    nota = models.CharField(max_length=250, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_tipo_display()}: {self.medicamento.nombre} x{self.cantidad}"
from datetime import timedelta

