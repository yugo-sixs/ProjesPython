from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group, Permission

from .models import DetalleVenta, InventarioMovimiento, Material, Socio, Usuario


class PermissionChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, permission):
        content_type = permission.content_type
        return f"{content_type.app_label}.{content_type.model} · {permission.codename} · {permission.name}"


class CapturaOperacionForm(forms.Form):
    socio = forms.ModelChoiceField(queryset=Socio.objects.filter(activo=True), required=False, label="Proveedor o cliente")


class DetalleOperacionForm(forms.Form):
    material = forms.ModelChoiceField(queryset=Material.objects.filter(activo=True), label="Material")
    peso_bruto = forms.DecimalField(max_digits=14, decimal_places=3, min_value=0, label="Peso bruto (kg)")
    tara = forms.DecimalField(max_digits=14, decimal_places=3, min_value=0, initial=0, label="Tara (kg)")
    merma_porcentaje = forms.DecimalField(max_digits=5, decimal_places=2, min_value=0, max_value=100, initial=0, required=False, label="Merma (%)")
    precio_por_kg = forms.DecimalField(max_digits=12, decimal_places=2, min_value=0, required=False, label="Precio por kg (opcional)")
    unidad_capturada = forms.ChoiceField(choices=DetalleVenta.UnidadCapturada.choices, initial=DetalleVenta.UnidadCapturada.KILOGRAMO, label="Unidad de peso")

    def __init__(self, *args, tipo="compra", **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["material"].queryset = Material.objects.filter(activo=True)
        if tipo == "compra":
            self.fields.pop("unidad_capturada", None)
        else:
            self.fields.pop("merma_porcentaje", None)

    def clean(self):
        data = super().clean()
        bruto, tara = data.get("peso_bruto"), data.get("tara")
        if bruto is not None and tara is not None and bruto <= tara:
            self.add_error("peso_bruto", "El peso bruto debe ser mayor que la tara.")
        return data


class CancelarOperacionForm(forms.Form):
    motivo = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), max_length=1000)


class AjusteInventarioForm(forms.Form):
    material = forms.ModelChoiceField(queryset=Material.objects.filter(activo=True))
    cantidad = forms.DecimalField(max_digits=14, decimal_places=3, help_text="Positivo aumenta; negativo disminuye existencias.")
    tipo = forms.ChoiceField(choices=[
        (InventarioMovimiento.Tipo.MERMA, "Merma de almacén"),
        (InventarioMovimiento.Tipo.AJUSTE, "Ajuste de inventario"),
    ])
    motivo = forms.CharField(max_length=255)


class AltaUsuarioForm(UserCreationForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.order_by("name"), required=False,
        widget=forms.CheckboxSelectMultiple, label="Grupos / roles de permisos",
    )
    user_permissions = PermissionChoiceField(
        queryset=Permission.objects.select_related("content_type").order_by("content_type__app_label", "content_type__model", "codename"),
        required=False, widget=forms.SelectMultiple(attrs={"size": 12}), label="Permisos individuales",
    )

    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = (
            "username", "first_name", "last_name", "email", "rol", "numero_empleado",
            "turno", "telefono", "limite_compra_efectivo", "is_active", "is_staff", "is_superuser",
            "groups", "user_permissions",
        )


class EditarUsuarioForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.order_by("name"), required=False,
        widget=forms.CheckboxSelectMultiple, label="Grupos / roles de permisos",
    )
    user_permissions = PermissionChoiceField(
        queryset=Permission.objects.select_related("content_type").order_by("content_type__app_label", "content_type__model", "codename"),
        required=False, widget=forms.SelectMultiple(attrs={"size": 12}), label="Permisos individuales",
    )

    class Meta:
        model = Usuario
        fields = (
            "username", "first_name", "last_name", "email", "rol", "numero_empleado",
            "turno", "telefono", "limite_compra_efectivo", "is_active", "is_staff", "is_superuser",
            "groups", "user_permissions",
        )


class GrupoPermisosForm(forms.ModelForm):
    permissions = PermissionChoiceField(
        queryset=Permission.objects.select_related("content_type").order_by("content_type__app_label", "content_type__model", "codename"),
        required=False, widget=forms.SelectMultiple(attrs={"size": 18}), label="Permisos del grupo",
    )

    class Meta:
        model = Group
        fields = ("name", "permissions")
