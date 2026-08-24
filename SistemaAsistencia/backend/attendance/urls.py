from django.urls import include, path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.routers import DefaultRouter

from .views import (
    AttendanceViewSet,
    EmployeeViewSet,
    MobileAttendanceHistoryView,
    MobileCheckInView,
    MobileCheckOutView,
    MobileProfileView,
    ReportSummaryView,
    WorkScheduleViewSet,
)


@api_view(["GET"])
@permission_classes([AllowAny])
def api_root(request):
    return Response(
        {
            "title": "API de control de asistencia",
            "version": "1.0",
            "description": "Endpoints principales para autenticación, app móvil y recursos humanos.",
            "documentation": "Consulte los endpoints listados a continuación.",
            "endpoints": {
                "auth": {
                    "login": "/api/auth/login/",
                    "refresh": "/api/auth/refresh/",
                },
                "mobile": {
                    "profile": "/api/mobile/me/",
                    "check_in": "/api/mobile/asistencia/entrada/",
                    "check_out": "/api/mobile/asistencia/salida/",
                    "history": "/api/mobile/asistencias/",
                },
                "rh": {
                    "employees": "/api/rh/empleados/",
                    "schedules": "/api/rh/horarios/",
                    "attendances": "/api/rh/asistencias/",
                    "summary": "/api/rh/reportes/resumen/",
                },
            },
        }
    )


router = DefaultRouter()
router.register("rh/empleados", EmployeeViewSet, basename="rh-employees")
router.register("rh/horarios", WorkScheduleViewSet, basename="rh-schedules")
router.register("rh/asistencias", AttendanceViewSet, basename="rh-attendances")

urlpatterns = [
    path("", api_root, name="api-root"),
    path("mobile/me/", MobileProfileView.as_view(), name="mobile-profile"),
    path("mobile/asistencia/entrada/", MobileCheckInView.as_view(), name="mobile-check-in"),
    path("mobile/asistencia/salida/", MobileCheckOutView.as_view(), name="mobile-check-out"),
    path("mobile/asistencias/", MobileAttendanceHistoryView.as_view(), name="mobile-attendance-history"),
    path("rh/reportes/resumen/", ReportSummaryView.as_view(), name="rh-report-summary"),
    path("", include(router.urls)),
]
