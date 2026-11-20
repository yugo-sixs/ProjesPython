from datetime import datetime, time, timedelta
from decimal import Decimal
from decimal import InvalidOperation

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group
from django.contrib.auth.views import LoginView
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Count, Sum
from django.forms import formset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.views import View
from django.urls import reverse_lazy
from django.views.generic import CreateView, FormView, ListView, UpdateView

from .forms import (
    AjusteInventarioForm, AltaUsuarioForm, CancelarOperacionForm, CapturaOperacionForm,
    DetalleOperacionForm, EditarUsuarioForm, GrupoPermisosForm,
)
from .models import DetalleCompra, DetalleVenta, EntregaEfectivo, InventarioMovimiento, OperacionCompra, OperacionVenta, Socio, Usuario
from .services import ajustar_inventario, cancelar_operacion, cerrar_caja_empleado, registrar_compra, registrar_venta


class CustomLoginView(LoginView):
    template_name = "reciclaje/login.html"


class RegistrarOperacionView(LoginRequiredMixin, FormView):
    form_class = CapturaOperacionForm
    success_url = "/inventario/corte/"
    tipo = None

    def get_template_names(self):
        return [f"reciclaje/captura_{self.tipo}.html"]

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.tipo == "compra":
            form.fields["socio"].queryset = Socio.objects.filter(activo=True, tipo__in=[Socio.Tipo.PROVEEDOR, Socio.Tipo.AMBOS])
        else:
            form.fields["socio"].queryset = Socio.objects.filter(activo=True, tipo__in=[Socio.Tipo.CLIENTE, Socio.Tipo.AMBOS])
        return form

    def get_formset(self):
        formset_class = formset_factory(DetalleOperacionForm, extra=1, min_num=1, validate_min=True, max_num=50, validate_max=True)
        data = self.request.POST if self.request.method == "POST" else None
        return formset_class(data, prefix="detalles", form_kwargs={"tipo": self.tipo})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["detalle_formset"] = kwargs.get("detalle_formset") or self.get_formset()
        return context

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not (
            request.user.is_superuser or request.user.rol in self.roles_permitidos
        ):
            messages.error(request, "Tu rol no tiene acceso a esta operación.")
            return redirect("corte_diario")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        data = form.cleaned_data
        user = self.request.user
        detalle_formset = self.get_formset()
        if not detalle_formset.is_valid():
            return self.form_invalid(form)
        lineas = [item.cleaned_data for item in detalle_formset if item.cleaned_data]
        if any(line.get("precio_por_kg") is not None for line in lineas) and not (
            user.is_superuser or user.rol in ("admin", "supervisor") or user.has_perm("inventario.puede_cambiar_precio_material")
        ):
            form.add_error(None, "Solo un supervisor autorizado puede cambiar el precio pactado.")
            return self.form_invalid(form)
        detalles = []
        for line in lineas:
            detalle = {"material": line["material"], "peso_bruto": line["peso_bruto"], "tara": line["tara"]}
            if line.get("merma_porcentaje") is not None:
                detalle["merma_porcentaje"] = line["merma_porcentaje"]
            if line.get("precio_por_kg") is not None:
                detalle["precio_por_kg"] = line["precio_por_kg"]
            if line.get("unidad_capturada"):
                detalle["unidad_capturada"] = line["unidad_capturada"]
            detalles.append(detalle)
        if self.tipo == "compra":
            service = registrar_compra
        else:
            service = registrar_venta
        try:
            service(empleado=self.request.user, socio=data.get("socio"), detalles=detalles)
        except ValidationError as exc:
            form.add_error(None, exc.message if hasattr(exc, "message") else "; ".join(exc.messages))
            return self.form_invalid(form)
        messages.success(self.request, f"{self.tipo.title()} registrada correctamente.")
        return super().form_valid(form)


class RegistrarCompraView(RegistrarOperacionView):
    tipo = "compra"
    roles_permitidos = ("admin", "basculero", "supervisor")


class RegistrarVentaView(RegistrarOperacionView):
    tipo = "venta"
    roles_permitidos = ("admin", "cajero", "supervisor")


class CorteDiarioView(LoginRequiredMixin, ListView):
    model = OperacionCompra
    template_name = "reciclaje/corte_dia.html"
    context_object_name = "compras"

    def get_queryset(self):
        inicio = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)
        fin = inicio + timedelta(days=1)
        return OperacionCompra.objects.filter(fecha__gte=inicio, fecha__lt=fin, estado=OperacionCompra.Estado.VIGENTE)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        inicio = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)
        fin = inicio + timedelta(days=1)
        compras = OperacionCompra.objects.filter(fecha__gte=inicio, fecha__lt=fin, estado=OperacionCompra.Estado.VIGENTE)
        ventas = OperacionVenta.objects.filter(fecha__gte=inicio, fecha__lt=fin, estado=OperacionVenta.Estado.VIGENTE)
        context.update({
            "ventas": ventas,
            "total_compras": compras.aggregate(v=Sum("total"))["v"] or 0,
            "total_ventas": ventas.aggregate(v=Sum("total"))["v"] or 0,
            "kilos_comprados": DetalleCompra.objects.filter(compra__in=compras).aggregate(v=Sum("peso_neto"))["v"] or 0,
            "kilos_vendidos": DetalleVenta.objects.filter(venta__in=ventas).aggregate(v=Sum("peso_neto"))["v"] or 0,
            "compras_por_material": DetalleCompra.objects.filter(compra__in=compras).values("material__nombre").annotate(kilos=Sum("peso_neto")),
            "ventas_por_material": DetalleVenta.objects.filter(venta__in=ventas).values("material__nombre").annotate(kilos=Sum("peso_neto")),
            "compras_por_empleado": compras.values("empleado__username").annotate(total=Sum("total"), tickets=Count("pk")),
            "efectivo_asignado_por_empleado": EntregaEfectivo.objects.filter(fecha__gte=inicio, fecha__lt=fin).values("empleado__username").annotate(total=Sum("cantidad")),
            "fecha_corte": timezone.localdate(),
        })
        context["balance_diario"] = context["total_ventas"] - context["total_compras"]
        return context


class AuditoriaEmpleadoView(LoginRequiredMixin, ListView):
    template_name = "reciclaje/auditoria_empleados.html"
    context_object_name = "empleados"

    def get_queryset(self):
        hoy = timezone.localdate()
        self.desde = parse_date(self.request.GET.get("desde", "")) or hoy
        self.hasta = parse_date(self.request.GET.get("hasta", "")) or hoy
        if self.hasta < self.desde:
            self.hasta = self.desde
        inicio = timezone.make_aware(datetime.combine(self.desde, time.min))
        fin = timezone.make_aware(datetime.combine(self.hasta + timedelta(days=1), time.min))
        self.compras = OperacionCompra.objects.filter(
            fecha__gte=inicio, fecha__lt=fin, estado=OperacionCompra.Estado.VIGENTE,
        )
        rows = {
            row["empleado_id"]: {
                "empleado_id": row["empleado_id"], "empleado__username": row["empleado__username"],
                "total_ejercido": row["total_ejercido"], "tickets": row["tickets"],
                "efectivo_asignado": Decimal("0.00"),
            }
            for row in self.compras.values("empleado_id", "empleado__username").annotate(total_ejercido=Sum("total"), tickets=Count("pk"))
        }
        todos_los_pagos = EntregaEfectivo.objects.filter(fecha__gte=inicio, fecha__lt=fin).values(
            "empleado_id", "empleado__username",
        ).annotate(total=Sum("cantidad"))
        for entrega in todos_los_pagos:
            fila = rows.setdefault(entrega["empleado_id"], {
                "empleado_id": entrega["empleado_id"], "empleado__username": entrega["empleado__username"],
                "total_ejercido": Decimal("0.00"), "tickets": 0, "efectivo_asignado": Decimal("0.00"),
            })
            fila["efectivo_asignado"] = entrega["total"]
        return sorted(rows.values(), key=lambda row: row["empleado__username"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["desde"] = self.desde
        context["hasta"] = self.hasta
        kilos_por_empleado = {
            row["compra__empleado_id"]: row["kilos"]
            for row in DetalleCompra.objects.filter(compra__in=self.compras).values("compra__empleado_id").annotate(kilos=Sum("peso_neto"))
        }
        for empleado in context["empleados"]:
            empleado["kilos"] = kilos_por_empleado.get(empleado["empleado_id"], 0)
            empleado["saldo_esperado"] = empleado["efectivo_asignado"] - (empleado["total_ejercido"] or Decimal("0.00"))
        return context


class CancelarCompraView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "inventario.puede_cancelar_ticket"

    def has_permission(self):
        user = self.request.user
        return user.is_superuser or user.rol in ("admin", "supervisor") or super().has_permission()

    def post(self, request, pk):
        operacion = get_object_or_404(OperacionCompra, pk=pk)
        form = CancelarOperacionForm(request.POST)
        if form.is_valid():
            try:
                cancelar_operacion(operacion=operacion, usuario=request.user, motivo=form.cleaned_data["motivo"])
                messages.success(request, "Compra cancelada y movimiento de inventario revertido.")
            except ValidationError as exc:
                messages.error(request, "; ".join(exc.messages))
        return redirect("corte_diario")


class CerrarCajaEmpleadoView(LoginRequiredMixin, View):
    def post(self, request):
        if not (request.user.is_superuser or request.user.rol in ("admin", "supervisor")):
            messages.error(request, "Solo administración o supervisión puede cerrar cajas.")
            return redirect("auditoria_empleados")
        empleado_id = request.POST.get("empleado_id")
        desde_dia = parse_date(request.POST.get("desde", ""))
        hasta_dia = parse_date(request.POST.get("hasta", ""))
        try:
            declarado = Decimal(request.POST.get("efectivo_declarado", ""))
            empleado = get_object_or_404(Usuario, pk=empleado_id)
            if not desde_dia or not hasta_dia:
                raise ValidationError("Selecciona el periodo del corte.")
            desde = timezone.make_aware(datetime.combine(desde_dia, time.min))
            hasta = timezone.make_aware(datetime.combine(hasta_dia + timedelta(days=1), time.min))
            cerrar_caja_empleado(empleado=empleado, desde=desde, hasta=hasta, efectivo_declarado=declarado, cerrado_por=request.user)
            messages.success(request, f"Corte de caja cerrado para {empleado}.")
        except (InvalidOperation, ValueError, ValidationError) as exc:
            messages.error(request, "; ".join(exc.messages) if isinstance(exc, ValidationError) else "El efectivo declarado no es válido.")
        except IntegrityError:
            messages.error(request, "Ya existe un corte cerrado para ese empleado y periodo.")
        return redirect(f"/inventario/auditoria/?desde={desde_dia or ''}&hasta={hasta_dia or ''}")


class CancelarVentaView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "inventario.puede_cancelar_ticket"

    def has_permission(self):
        user = self.request.user
        return user.is_superuser or user.rol in ("admin", "supervisor") or super().has_permission()

    def post(self, request, pk):
        operacion = get_object_or_404(OperacionVenta, pk=pk)
        form = CancelarOperacionForm(request.POST)
        if form.is_valid():
            try:
                cancelar_operacion(operacion=operacion, usuario=request.user, motivo=form.cleaned_data["motivo"])
                messages.success(request, "Venta cancelada y movimiento de inventario revertido.")
            except ValidationError as exc:
                messages.error(request, "; ".join(exc.messages))
        return redirect("corte_diario")


class KardexView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = "inventario.puede_ver_kardex"
    model = InventarioMovimiento
    template_name = "reciclaje/kardex.html"
    context_object_name = "movimientos"
    paginate_by = 100


class AjustarInventarioView(LoginRequiredMixin, FormView):
    form_class = AjusteInventarioForm
    template_name = "reciclaje/ajuste_inventario.html"
    success_url = "/inventario/kardex/"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not (
            request.user.is_superuser or request.user.rol in ("admin", "supervisor")
            or request.user.has_perm("inventario.puede_ajustar_inventario")
        ):
            messages.error(request, "No tienes autorización para ajustar inventario.")
            return redirect("corte_diario")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            ajustar_inventario(
                material_id=data["material"].pk, cantidad=data["cantidad"],
                usuario=self.request.user, motivo=data["motivo"], tipo=data["tipo"],
            )
        except ValidationError as exc:
            form.add_error(None, "; ".join(exc.messages))
            return self.form_invalid(form)
        messages.success(self.request, "Ajuste guardado en el kardex.")
        return super().form_valid(form)


class SoloSuperusuarioMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser


class UsuariosListView(SoloSuperusuarioMixin, ListView):
    model = Usuario
    template_name = "reciclaje/usuarios_lista.html"
    context_object_name = "usuarios"
    paginate_by = 50
    queryset = Usuario.objects.order_by("username")


class AltaUsuarioView(SoloSuperusuarioMixin, CreateView):
    model = Usuario
    form_class = AltaUsuarioForm
    template_name = "reciclaje/usuario_form.html"
    success_url = reverse_lazy("usuarios_lista")

    def form_valid(self, form):
        messages.success(self.request, "Usuario creado con sus grupos y permisos.")
        return super().form_valid(form)


class EditarUsuarioView(SoloSuperusuarioMixin, UpdateView):
    model = Usuario
    form_class = EditarUsuarioForm
    template_name = "reciclaje/usuario_form.html"
    success_url = reverse_lazy("usuarios_lista")

    def form_valid(self, form):
        messages.success(self.request, "Usuario y permisos actualizados.")
        return super().form_valid(form)


class GruposListView(SoloSuperusuarioMixin, ListView):
    model = Group
    template_name = "reciclaje/grupos_lista.html"
    context_object_name = "grupos"
    queryset = Group.objects.order_by("name")


class AltaGrupoView(SoloSuperusuarioMixin, CreateView):
    model = Group
    form_class = GrupoPermisosForm
    template_name = "reciclaje/grupo_form.html"
    success_url = reverse_lazy("grupos_lista")


class EditarGrupoView(SoloSuperusuarioMixin, UpdateView):
    model = Group
    form_class = GrupoPermisosForm
    template_name = "reciclaje/grupo_form.html"
    success_url = reverse_lazy("grupos_lista")
