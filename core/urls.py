# citasmedicas/citashospital/core/urls.py
from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('usuarios/', views.usuarios_crud),
    path('doctores/', views.doctores_crud),
    path('pacientes/', views.pacientes_crud),
    path('secretarias/', views.secretarias_crud),
    path('citas/', views.citas_crud),
]
