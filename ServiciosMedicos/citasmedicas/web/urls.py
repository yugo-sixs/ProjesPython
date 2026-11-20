# citasmedicas/citashospital/ web/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    #path('usuarios/', views.listar_usuarios, name='listar_usuarios'),
    path('usuarios/crear/', views.crear_usuario, name='crear_usuario'),
    path('usuarios/editar/<int:id>/', views.editar_usuario, name='editar_usuario'),
    path('usuarios/accesos/', views.listar_accesos, name='listar_accesos'),
    path('usuarios/<int:id>/accesos/', views.editar_accesos_usuario, name='editar_accesos_usuario'),
    #path('usuarios/desactivar/<int:usuario_id>/', views.desactivar_usuario, name='desactivar_usuario'),
    path('personal/', views.listar_personal, name='listar_personal'),
    path('personal/crear/', views.crear_personal, name='crear_personal'),
    path('pacientes/', views.listar_pacientes, name='listar_pacientes'),
    path('pacientes/crear/', views.crear_paciente, name='crear_paciente'),
    path('pacientes/<int:paciente_id>/', views.detalle_paciente, name='detalle_paciente'),
    path('citas/', views.listar_citas, name='listar_citas'),
    path('citas/crear/', views.crear_cita, name='crear_cita'),
    path('citas/<int:cita_id>/atender/', views.crear_consulta, name='crear_consulta'),
    path('estudios/<int:estudio_id>/resultado/', views.actualizar_resultado_estudio, name='actualizar_resultado_estudio'),
    path('inventario/', views.inventario, name='inventario'),
    path('inventario/medicamentos/crear/', views.crear_medicamento, name='crear_medicamento'),
    path('inventario/entradas/crear/', views.entrada_inventario, name='entrada_inventario'),
    path('urgencias/', views.listar_urgencias, name='listar_urgencias'),
    path('urgencias/recepcion/', views.registrar_urgencias, name='registrar_urgencias'),
    path('urgencias/<int:recepcion_id>/valoracion/', views.valorar_urgencias, name='valorar_urgencias'),
    path('doctor/', views.vista_doctor, name='vista_doctor'),
    path('secretaria/', views.vista_secretaria, name='vista_secretaria'),
    #path('crear_cita/', views.crear_cita, name='crear_cita'),
    #path('citas/', views.listar_citas, name='listar_citas'),    
    #path('citas/editar/<int:cita_id>/', views.editar_cita, name='editar_cita'),
    #path('citas/eliminar/<int:cita_id>/', views.eliminar_cita, name='eliminar_cita'),
   

]

