# citasmedicas/citashospital/ web/urls.py

from django.urls import path
from . import views

urlpatterns = [

    path('', views.home, name='home'),
    path('usuarios/', views.listar_usuarios, name='listar_usuarios'),
    path('usuarios/crear/', views.crear_usuario, name='crear_usuario'),
    path('usuarios/editar/<int:usuario_id>/', views.editar_usuario, name='editar_usuario'),
]
