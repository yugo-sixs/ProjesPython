# citasmedicas/citashospital/ web/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.loogin, name='login'),
    path('logout/', views.logout, name='logout'),
    #path('usuarios/', views.listar_usuarios, name='listar_usuarios'),
    path('usuarios/crear/', views.crear_usuario, name='crear_usuario'),
    path('usuarios/editar/<int:id>/', views.editar_usuario, name='editar_usuario'),
    #path('usuarios/desactivar/<int:usuario_id>/', views.desactivar_usuario, name='desactivar_usuario'),
    path('personal/crear/', views.crear_personal, name='crear_personal'),
    #path('crear_cita/', views.crear_cita, name='crear_cita'),
    #path('citas/', views.listar_citas, name='listar_citas'),    
    #path('citas/editar/<int:cita_id>/', views.editar_cita, name='editar_cita'),
    #path('citas/eliminar/<int:cita_id>/', views.eliminar_cita, name='eliminar_cita'),
   

]

