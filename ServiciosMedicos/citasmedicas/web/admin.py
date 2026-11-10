from django.contrib import admin

from .models import (
    AccesoUsuario, Cita, Consulta, Estatus, Especialidad, Estudio, Medicamento,
    GrupoPermiso, MovimientoInventario, Paciente, Personal, RecepcionUrgencias, Receta,
)

admin.site.register([
    AccesoUsuario, Cita, Consulta, Estatus, Especialidad, Estudio, Medicamento,
    GrupoPermiso, MovimientoInventario, Paciente, Personal, RecepcionUrgencias, Receta,
])
