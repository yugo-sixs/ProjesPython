from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    CorteCajaEmpleado, DetalleCompra, DetalleVenta, EntregaEfectivo,
    HistorialPrecio, InventarioMovimiento, Material, OperacionCompra,
    OperacionVenta, Socio, Usuario,
)


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Datos operativos", {"fields": ("rol", "numero_empleado", "turno", "telefono", "limite_compra_efectivo")}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Datos operativos", {"fields": ("rol", "numero_empleado", "turno", "telefono", "limite_compra_efectivo")}),)


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ("nombre", "categoria", "precio_compra", "precio_venta", "stock_actual", "activo")
    readonly_fields = ("stock_actual",)
    search_fields = ("nombre", "categoria")
    list_filter = ("categoria", "activo")

    def save_model(self, request, obj, form, change):
        if change:
            anterior = Material.objects.get(pk=obj.pk)
            if (anterior.precio_compra, anterior.precio_venta) != (obj.precio_compra, obj.precio_venta):
                from .models import HistorialPrecio
                HistorialPrecio.objects.create(
                    material=obj, usuario=request.user,
                    precio_compra_anterior=anterior.precio_compra, precio_compra_nuevo=obj.precio_compra,
                    precio_venta_anterior=anterior.precio_venta, precio_venta_nuevo=obj.precio_venta,
                )
        super().save_model(request, obj, form, change)


@admin.register(Socio)
class SocioAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tipo", "telefono", "activo")
    search_fields = ("nombre", "identificacion_fiscal", "telefono")
    list_filter = ("tipo", "activo")


@admin.register(OperacionCompra)
class CompraAdmin(admin.ModelAdmin):
    list_display = ("folio", "fecha", "empleado", "socio", "total", "estado")
    list_filter = ("estado", "fecha")
    search_fields = ("folio", "socio__nombre", "empleado__username")
    readonly_fields = tuple(field.name for field in OperacionCompra._meta.fields)
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(OperacionVenta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ("folio", "fecha", "empleado", "socio", "total", "estado")
    list_filter = ("estado", "fecha")
    search_fields = ("folio", "socio__nombre", "empleado__username")
    readonly_fields = tuple(field.name for field in OperacionVenta._meta.fields)
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(InventarioMovimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = ("fecha", "material", "tipo", "cantidad", "saldo_anterior", "saldo_nuevo", "usuario")
    list_filter = ("tipo", "fecha")
    search_fields = ("material__nombre", "motivo", "compra__folio", "venta__folio")
    readonly_fields = tuple(field.name for field in InventarioMovimiento._meta.fields)


@admin.register(HistorialPrecio)
class HistorialPrecioAdmin(admin.ModelAdmin):
    list_display = ("fecha", "material", "precio_compra_anterior", "precio_compra_nuevo", "precio_venta_anterior", "precio_venta_nuevo", "usuario")
    readonly_fields = tuple(field.name for field in HistorialPrecio._meta.fields)

    def has_add_permission(self, request):
        return False


@admin.register(EntregaEfectivo)
class EntregaEfectivoAdmin(admin.ModelAdmin):
    list_display = ("fecha", "empleado", "autorizada_por", "cantidad", "corte_caja", "observaciones")
    list_filter = ("fecha",)
    search_fields = ("empleado__username", "autorizada_por__username")


@admin.register(CorteCajaEmpleado)
class CorteCajaEmpleadoAdmin(admin.ModelAdmin):
    list_display = ("empleado", "desde", "hasta", "efectivo_asignado", "efectivo_ejercido", "efectivo_declarado", "diferencia", "cerrado_por")
    list_filter = ("desde", "hasta")
    readonly_fields = tuple(field.name for field in CorteCajaEmpleado._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
