# citasmedicas/citashospital/citashospital/urls.py

from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('web/', include('web.urls')),
    path('', include('web.urls')),

    # path('api/', include('core.urls')),
]
