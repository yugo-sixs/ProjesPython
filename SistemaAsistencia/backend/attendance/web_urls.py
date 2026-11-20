from django.urls import path

from .views import (
    rh_admin_dashboard_view,
    rh_attendance_report_view,
    rh_dashboard_view,
    rh_employees_view,
    rh_login_view,
    rh_my_attendance_view,
    rh_schedules_view,
)

urlpatterns = [
    path("login/", rh_login_view, name="rh-login"),
    path("admin-dashboard/", rh_admin_dashboard_view, name="rh-admin-dashboard"),
    path("dashboard/", rh_dashboard_view, name="rh-dashboard"),
    path("mi-asistencia/", rh_my_attendance_view, name="rh-my-attendance"),
    path("empleados/", rh_employees_view, name="rh-employees"),
    path("horarios/", rh_schedules_view, name="rh-schedules"),
    path("reportes/asistencias/", rh_attendance_report_view, name="rh-attendance-report"),
]
