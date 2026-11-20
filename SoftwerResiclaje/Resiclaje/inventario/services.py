from decimal import Decimal
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from .models import (
    CorteCajaEmpleado, DetalleCompra, DetalleVenta, EntregaEfectivo,
    HistorialPrecio, InventarioMovimiento, Material, OperacionCompra,
    OperacionVenta, Usuario,
)


def _folio(prefijo):
    return f"{prefijo}-{timezone.localdate():%Y%m%d}-{uuid4().hex[:8].upper()}"


def _locked_materials(details):
    ids = sorted({int(line["material"].pk if isinstance(line["material"], Material) else line["material"]) for line in details})
    materials = {m.pk: m for m in Material.objects.select_for_update().filter(pk__in=ids).order_by("pk")}
    if len(materials) != len(ids):
        raise ValidationError("Uno o más materiales ya no existen.")
    return materials


@transaction.atomic
def registrar_compra(*, empleado, detalles, socio=None, folio=None):
    """Registra ticket, precios pactados, inventario y kardex en una sola transacción."""
    materials = _locked_materials(detalles)
    compra = OperacionCompra.objects.create(
        folio=folio or _folio("C"), empleado=empleado, socio=socio,
    )
    total = Decimal("0.00")
    for line in detalles:
        material = materials[int(line["material"].pk if isinstance(line["material"], Material) else line["material"])]
        detalle = DetalleCompra(
            compra=compra,
            material=material,
            peso_bruto=line["peso_bruto"],
            tara=line.get("tara", Decimal("0")),
            merma_porcentaje=line.get("merma_porcentaje", Decimal("0")),
            precio_por_kg=line.get("precio_por_kg", material.precio_compra),
        )
        detalle.full_clean()
        detalle.calcular()
        detalle.save()
        anterior = material.stock_actual
        material.stock_actual = (anterior + detalle.peso_neto).quantize(Decimal("0.001"))
        material.save(update_fields=["stock_actual"])
        InventarioMovimiento.objects.create(
            material=material, tipo=InventarioMovimiento.Tipo.COMPRA,
            cantidad=detalle.peso_neto, saldo_anterior=anterior,
            saldo_nuevo=material.stock_actual, compra=compra, usuario=empleado,
        )
        total += detalle.total
    compra.total = total
    compra.save(update_fields=["total"])
    if empleado.limite_compra_efectivo and total > empleado.limite_compra_efectivo:
        if not empleado.has_perm("inventario.puede_registrar_compra") and empleado.rol != Usuario.Rol.SUPERVISOR:
            raise ValidationError("El total supera el límite de efectivo autorizado para este empleado.")
    return compra


@transaction.atomic
def registrar_venta(*, empleado, detalles, socio=None, folio=None):
    materials = _locked_materials(detalles)
    venta = OperacionVenta.objects.create(
        folio=folio or _folio("V"), empleado=empleado, socio=socio,
    )
    total = Decimal("0.00")
    for line in detalles:
        material = materials[int(line["material"].pk if isinstance(line["material"], Material) else line["material"])]
        detalle = DetalleVenta(
            venta=venta, material=material, peso_bruto=line["peso_bruto"],
            tara=line.get("tara", Decimal("0")),
            unidad_capturada=line.get("unidad_capturada", "kg"),
            precio_por_kg=line.get("precio_por_kg", material.precio_venta),
        )
        detalle.full_clean()
        detalle.calcular()
        if material.stock_actual < detalle.peso_neto:
            raise ValidationError(f"Existencia insuficiente de {material.nombre}.")
        detalle.save()
        anterior = material.stock_actual
        material.stock_actual = (anterior - detalle.peso_neto).quantize(Decimal("0.001"))
        material.save(update_fields=["stock_actual"])
        InventarioMovimiento.objects.create(
            material=material, tipo=InventarioMovimiento.Tipo.VENTA,
            cantidad=-detalle.peso_neto, saldo_anterior=anterior,
            saldo_nuevo=material.stock_actual, venta=venta, usuario=empleado,
        )
        total += detalle.total
    venta.total = total
    venta.save(update_fields=["total"])
    return venta


@transaction.atomic
def cancelar_operacion(*, operacion, usuario, motivo):
    if not motivo.strip():
        raise ValidationError("Indica el motivo de cancelación.")
    if operacion.estado != operacion.Estado.VIGENTE:
        raise ValidationError("La operación ya está cancelada.")

    compra = isinstance(operacion, OperacionCompra)
    detalles = list(operacion.detalles.select_related("material").all())
    ids = sorted({d.material_id for d in detalles})
    materials = {m.pk: m for m in Material.objects.select_for_update().filter(pk__in=ids).order_by("pk")}
    for detalle in detalles:
        material = materials[detalle.material_id]
        delta = -detalle.peso_neto if compra else detalle.peso_neto
        nuevo = (material.stock_actual + delta).quantize(Decimal("0.001"))
        if nuevo < 0:
            raise ValidationError(f"No se puede cancelar: el inventario de {material.nombre} ya fue comprometido.")
        anterior = material.stock_actual
        material.stock_actual = nuevo
        material.save(update_fields=["stock_actual"])
        InventarioMovimiento.objects.create(
            material=material, tipo=InventarioMovimiento.Tipo.CANCELACION,
            cantidad=delta, saldo_anterior=anterior, saldo_nuevo=nuevo,
            compra=operacion if compra else None,
            venta=None if compra else operacion,
            usuario=usuario, motivo=motivo,
        )
    operacion.estado = operacion.Estado.CANCELADO
    operacion.cancelado_por = usuario
    operacion.fecha_cancelacion = timezone.now()
    operacion.motivo_cancelacion = motivo.strip()
    operacion.save(update_fields=["estado", "cancelado_por", "fecha_cancelacion", "motivo_cancelacion"])
    return operacion


@transaction.atomic
def ajustar_inventario(*, material_id, cantidad, usuario, motivo, tipo=InventarioMovimiento.Tipo.AJUSTE):
    if not motivo.strip():
        raise ValidationError("Indica el motivo del ajuste.")
    material = Material.objects.select_for_update().get(pk=material_id)
    cantidad = Decimal(cantidad).quantize(Decimal("0.001"))
    nuevo = material.stock_actual + cantidad
    if nuevo < 0:
        raise ValidationError("El ajuste dejaría el inventario en negativo.")
    anterior = material.stock_actual
    material.stock_actual = nuevo
    material.save(update_fields=["stock_actual"])
    return InventarioMovimiento.objects.create(
        material=material, tipo=tipo, cantidad=cantidad,
        saldo_anterior=anterior, saldo_nuevo=nuevo, usuario=usuario, motivo=motivo.strip(),
    )


@transaction.atomic
def actualizar_precios(*, material_id, usuario, precio_compra, precio_venta):
    material = Material.objects.select_for_update().get(pk=material_id)
    HistorialPrecio.objects.create(
        material=material, usuario=usuario,
        precio_compra_anterior=material.precio_compra, precio_compra_nuevo=precio_compra,
        precio_venta_anterior=material.precio_venta, precio_venta_nuevo=precio_venta,
    )
    material.precio_compra = precio_compra
    material.precio_venta = precio_venta
    material.save(update_fields=["precio_compra", "precio_venta"])
    return material


@transaction.atomic
def cerrar_caja_empleado(*, empleado, desde, hasta, efectivo_declarado, cerrado_por):
    if desde >= hasta:
        raise ValidationError("El inicio del corte debe ser anterior al final.")
    Usuario.objects.select_for_update().get(pk=empleado.pk)
    if CorteCajaEmpleado.objects.filter(empleado=empleado, desde__lt=hasta, hasta__gt=desde).exists():
        raise ValidationError("El periodo se cruza con un corte de caja que ya fue cerrado.")
    entregas = EntregaEfectivo.objects.select_for_update().filter(
        empleado=empleado, fecha__gte=desde, fecha__lt=hasta, corte_caja__isnull=True,
    )
    compras = OperacionCompra.objects.filter(
        empleado=empleado, fecha__gte=desde, fecha__lt=hasta,
        estado=OperacionCompra.Estado.VIGENTE,
    )
    asignado = entregas.aggregate(total=Sum("cantidad"))["total"] or Decimal("0.00")
    ejercido = compras.aggregate(total=Sum("total"))["total"] or Decimal("0.00")
    esperado = asignado - ejercido
    declarado = Decimal(efectivo_declarado).quantize(Decimal("0.01"))
    corte = CorteCajaEmpleado.objects.create(
        empleado=empleado, desde=desde, hasta=hasta, efectivo_asignado=asignado,
        efectivo_ejercido=ejercido, efectivo_declarado=declarado,
        diferencia=declarado - esperado, cerrado_por=cerrado_por,
    )
    entregas.update(corte_caja=corte)
    return corte
