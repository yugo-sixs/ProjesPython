from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Usuario(AbstractUser):
    class Rol(models.TextChoices):
        ADMINISTRADOR = "admin", "Administrador"
        BASCULERO = "basculero", "Comprador / Basculero"
        CAJERO = "cajero", "Cajero"
        SUPERVISOR = "supervisor", "Supervisor"

    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.BASCULERO)
    numero_empleado = models.CharField(max_length=30, unique=True, null=True, blank=True)
    turno = models.CharField(max_length=40, blank=True)
    telefono = models.CharField(max_length=15, blank=True)
    limite_compra_efectivo = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        permissions = [
            ("puede_cancelar_ticket", "Puede cancelar tickets"),
            ("puede_cambiar_precio_material", "Puede cambiar precios de materiales"),
            ("puede_ajustar_inventario", "Puede ajustar inventario"),
        ]

    def __str__(self):
        return self.get_full_name() or self.username


class Material(models.Model):
    UNIDADES = [("kg", "Kilogramos")]

    nombre = models.CharField(max_length=100, unique=True)
    categoria = models.CharField(max_length=80, blank=True)
    unidad_medida = models.CharField(max_length=10, choices=UNIDADES, default="kg")
    precio_compra = models.DecimalField(max_digits=12, decimal_places=2)
    precio_venta = models.DecimalField(max_digits=12, decimal_places=2)
    stock_actual = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nombre"]
        permissions = [("puede_ver_kardex", "Puede consultar el kardex")]

    def __str__(self):
        return self.nombre


class HistorialPrecio(models.Model):
    material = models.ForeignKey(Material, on_delete=models.PROTECT, related_name="historial_precios")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    precio_compra_anterior = models.DecimalField(max_digits=12, decimal_places=2)
    precio_compra_nuevo = models.DecimalField(max_digits=12, decimal_places=2)
    precio_venta_anterior = models.DecimalField(max_digits=12, decimal_places=2)
    precio_venta_nuevo = models.DecimalField(max_digits=12, decimal_places=2)
    fecha = models.DateTimeField(default=timezone.now)


class Socio(models.Model):
    class Tipo(models.TextChoices):
        PROVEEDOR = "proveedor", "Proveedor"
        CLIENTE = "cliente", "Cliente"
        AMBOS = "ambos", "Proveedor y cliente"

    nombre = models.CharField(max_length=160)
    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.PROVEEDOR)
    telefono = models.CharField(max_length=30, blank=True)
    identificacion_fiscal = models.CharField(max_length=30, blank=True)
    direccion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class OperacionBase(models.Model):
    class Estado(models.TextChoices):
        VIGENTE = "vigente", "Vigente"
        CANCELADO = "cancelado", "Cancelado"

    folio = models.CharField(max_length=40, unique=True)
    fecha = models.DateTimeField(default=timezone.now, db_index=True)
    empleado = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    socio = models.ForeignKey(Socio, on_delete=models.PROTECT, null=True, blank=True)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.VIGENTE, db_index=True)
    cancelado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name="%(class)s_cancelaciones",
    )
    fecha_cancelacion = models.DateTimeField(null=True, blank=True)
    motivo_cancelacion = models.TextField(blank=True)

    class Meta:
        abstract = True


class OperacionCompra(OperacionBase):
    class Meta:
        ordering = ["-fecha"]
        permissions = [("puede_registrar_compra", "Puede registrar compras")]

    def __str__(self):
        return f"Compra {self.folio}"


class DetalleCompra(models.Model):
    compra = models.ForeignKey(OperacionCompra, on_delete=models.PROTECT, related_name="detalles")
    material = models.ForeignKey(Material, on_delete=models.PROTECT)
    peso_bruto = models.DecimalField(max_digits=14, decimal_places=3)
    tara = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    merma_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    peso_neto = models.DecimalField(max_digits=14, decimal_places=3, editable=False)
    precio_por_kg = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=14, decimal_places=2, editable=False)

    def clean(self):
        super().clean()
        if self.peso_bruto is not None and self.tara is not None and self.peso_bruto <= self.tara:
            raise ValidationError({"peso_bruto": "El peso bruto debe ser mayor que la tara."})
        if self.merma_porcentaje is not None and not Decimal("0") <= self.merma_porcentaje <= Decimal("100"):
            raise ValidationError({"merma_porcentaje": "La merma debe estar entre 0 y 100%."})

    def calcular(self):
        peso_sin_merma = self.peso_bruto - self.tara
        self.peso_neto = (peso_sin_merma * (Decimal("1") - self.merma_porcentaje / Decimal("100"))).quantize(Decimal("0.001"))
        self.total = (self.peso_neto * self.precio_por_kg).quantize(Decimal("0.01"))


class OperacionVenta(OperacionBase):
    class Meta:
        ordering = ["-fecha"]
        permissions = [("puede_registrar_venta", "Puede registrar ventas")]

    @property
    def remision(self):
        return self.folio

    def __str__(self):
        return f"Venta {self.folio}"


class DetalleVenta(models.Model):
    class UnidadCapturada(models.TextChoices):
        KILOGRAMO = "kg", "Kilogramos"
        TONELADA = "ton", "Toneladas"

    venta = models.ForeignKey(OperacionVenta, on_delete=models.PROTECT, related_name="detalles")
    material = models.ForeignKey(Material, on_delete=models.PROTECT)
    unidad_capturada = models.CharField(max_length=3, choices=UnidadCapturada.choices, default=UnidadCapturada.KILOGRAMO)
    peso_bruto = models.DecimalField(max_digits=14, decimal_places=3)
    tara = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    peso_neto = models.DecimalField(max_digits=14, decimal_places=3, editable=False)
    precio_por_kg = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=14, decimal_places=2, editable=False)

    def clean(self):
        super().clean()
        if self.peso_bruto is not None and self.tara is not None and self.peso_bruto <= self.tara:
            raise ValidationError({"peso_bruto": "El peso bruto debe ser mayor que la tara."})

    def calcular(self):
        factor = Decimal("1000") if self.unidad_capturada == self.UnidadCapturada.TONELADA else Decimal("1")
        self.peso_neto = ((self.peso_bruto - self.tara) * factor).quantize(Decimal("0.001"))
        self.total = (self.peso_neto * self.precio_por_kg).quantize(Decimal("0.01"))


class InventarioMovimiento(models.Model):
    class Tipo(models.TextChoices):
        COMPRA = "compra", "Entrada por compra"
        VENTA = "venta", "Salida por venta"
        MERMA = "merma", "Merma de almacén"
        AJUSTE = "ajuste", "Ajuste"
        CANCELACION = "cancelacion", "Reverso por cancelación"

    material = models.ForeignKey(Material, on_delete=models.PROTECT, related_name="movimientos")
    tipo = models.CharField(max_length=16, choices=Tipo.choices)
    cantidad = models.DecimalField(max_digits=14, decimal_places=3, help_text="Delta de stock: positivo suma, negativo resta")
    saldo_anterior = models.DecimalField(max_digits=14, decimal_places=3)
    saldo_nuevo = models.DecimalField(max_digits=14, decimal_places=3)
    compra = models.ForeignKey(OperacionCompra, on_delete=models.PROTECT, null=True, blank=True, related_name="movimientos")
    venta = models.ForeignKey(OperacionVenta, on_delete=models.PROTECT, null=True, blank=True, related_name="movimientos")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    motivo = models.CharField(max_length=255, blank=True)
    fecha = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-fecha", "-pk"]

    def __str__(self):
        return f"{self.get_tipo_display()} · {self.material} · {self.cantidad} kg"


class EntregaEfectivo(models.Model):
    empleado = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="entregas_efectivo")
    autorizada_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="entregas_autorizadas")
    cantidad = models.DecimalField(max_digits=14, decimal_places=2)
    fecha = models.DateTimeField(default=timezone.now, db_index=True)
    observaciones = models.CharField(max_length=255, blank=True)
    corte_caja = models.ForeignKey(
        "CorteCajaEmpleado", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="entregas",
    )

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"Entrega a {self.empleado}: ${self.cantidad}"


class CorteCajaEmpleado(models.Model):
    empleado = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="cortes_caja")
    desde = models.DateTimeField()
    hasta = models.DateTimeField()
    efectivo_asignado = models.DecimalField(max_digits=14, decimal_places=2)
    efectivo_ejercido = models.DecimalField(max_digits=14, decimal_places=2)
    efectivo_declarado = models.DecimalField(max_digits=14, decimal_places=2)
    diferencia = models.DecimalField(max_digits=14, decimal_places=2)
    cerrado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="cortes_cerrados")
    fecha_cierre = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-fecha_cierre"]
        constraints = [models.UniqueConstraint(fields=["empleado", "desde", "hasta"], name="uniq_corte_empleado_periodo")]

    def __str__(self):
        return f"Corte {self.empleado} · {self.desde:%Y-%m-%d}"
