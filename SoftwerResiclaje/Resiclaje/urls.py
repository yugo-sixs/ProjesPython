"""
URL configuration for Resiclaje project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView
from Resiclaje.inventario.views import (
    CancelarCompraView,
    CancelarVentaView,
    AuditoriaEmpleadoView,
    AjustarInventarioView,
    CerrarCajaEmpleadoView,
    CorteDiarioView,
    CustomLoginView,
    KardexView,
    RegistrarCompraView,
    RegistrarVentaView,
    UsuariosListView,
    AltaUsuarioView,
    EditarUsuarioView,
    GruposListView,
    AltaGrupoView,
    EditarGrupoView,
)

urlpatterns = [
    path("", RedirectView.as_view(url="/login/", permanent=False), name="home"),
    path("admin/", admin.site.urls),
    path("seguridad/usuarios/", UsuariosListView.as_view(), name="usuarios_lista"),
    path("seguridad/usuarios/nuevo/", AltaUsuarioView.as_view(), name="usuario_nuevo"),
    path("seguridad/usuarios/<int:pk>/editar/", EditarUsuarioView.as_view(), name="usuario_editar"),
    path("seguridad/grupos/", GruposListView.as_view(), name="grupos_lista"),
    path("seguridad/grupos/nuevo/", AltaGrupoView.as_view(), name="grupo_nuevo"),
    path("seguridad/grupos/<int:pk>/editar/", EditarGrupoView.as_view(), name="grupo_editar"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("inventario/compra/", RegistrarCompraView.as_view(), name="registrar_compra"),
    path("inventario/venta/", RegistrarVentaView.as_view(), name="registrar_venta"),
    path("inventario/corte/", CorteDiarioView.as_view(), name="corte_diario"),
    path("inventario/kardex/", KardexView.as_view(), name="kardex"),
    path("inventario/ajuste/", AjustarInventarioView.as_view(), name="ajustar_inventario"),
    path("inventario/auditoria/", AuditoriaEmpleadoView.as_view(), name="auditoria_empleados"),
    path("inventario/auditoria/cerrar-caja/", CerrarCajaEmpleadoView.as_view(), name="cerrar_caja_empleado"),
    path("inventario/compra/<int:pk>/cancelar/", CancelarCompraView.as_view(), name="cancelar_compra"),
    path("inventario/venta/<int:pk>/cancelar/", CancelarVentaView.as_view(), name="cancelar_venta"),
]
