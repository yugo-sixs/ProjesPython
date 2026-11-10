from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

# 1. MODELO DE USUARIO PERSONALIZADO
class Usuario(AbstractUser):
    ROLES = (
        ('admin', 'Administrador'),
        ('operador', 'Operador de Báscula'),
    )
    rol = models.CharField(max_length=20, choices=ROLES, default='operador')
    telefono = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return f"{self.username} ({self.get_rol_display()})"

# 2. CATÁLOGO DE MATERIALES (Chatarra)
class Material(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2, help_text="Precio por kg que pagamos")
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, help_text="Precio por kg al que vendemos")
    stock_actual = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        verbose_name_plural = "Materiales"

    def __str__(self):
        return self.nombre

# 3. TRANSACCIONES (Compra y Venta)
class Transaccion(models.Model):
    TIPO_CHOICES = (
        ('COMPRA', 'Compra (Entrada)'),
        ('VENTA', 'Venta (Salida)'),
    )

    fecha = models.DateTimeField(auto_now_add=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    usuario_operador = models.ForeignKey(Usuario, on_delete=models.PROTECT)
    material = models.ForeignKey(Material, on_delete=models.PROTECT)
    
    # Datos de pesaje
    peso_bruto = models.DecimalField(max_digits=10, decimal_places=2)
    tara = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Peso del recipiente o vehículo")
    peso_neto = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    
    # Financiero
    precio_unitario_aplicado = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    total_dinero = models.DecimalField(max_digits=12, decimal_places=2, editable=False)

    class Meta:
        verbose_name_plural = "Transacciones"

    def clean(self):
        # Validación básica: el peso bruto no puede ser menor a la tara
        if self.peso_bruto <= self.tara:
            raise ValidationError("El peso bruto debe ser mayor a la tara.")

    def save(self, *args, **kwargs):
        # 1. Calcular peso neto
        self.peso_neto = self.peso_bruto - self.tara
        
        # 2. Asignar precio según el tipo de movimiento
        if self.tipo == 'COMPRA':
            self.precio_unitario_aplicado = self.material.precio_compra
        else:
            self.precio_unitario_aplicado = self.material.precio_venta
            
        # 3. Calcular total
        self.total_dinero = self.peso_neto * self.precio_unitario_aplicado
        
        # 4. Actualizar el stock del material de forma automática
        if self.tipo == 'COMPRA':
            self.material.stock_actual += self.peso_neto
        else:
            self.material.stock_actual -= self.peso_neto
        
        self.material.save() # Guardamos el nuevo stock en la tabla Material
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tipo} - {self.material.nombre} - {self.fecha.date()}"