import re
from decimal import Decimal, InvalidOperation

from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Attendance, AttendanceRecord, Employee, Justification, WorkSchedule, WorkScheduleDay
from .permissions import IsEmployee, IsHumanResources
from .serializers import (
    AttendanceCaptureSerializer,
    AttendanceSerializer,
    EmployeeSerializer,
    JustificationSerializer,
    WorkScheduleSerializer,
)
from .services import register_attendance_record


WEEKDAYS = [
    (WorkScheduleDay.Weekday.MONDAY, "Lunes"),
    (WorkScheduleDay.Weekday.TUESDAY, "Martes"),
    (WorkScheduleDay.Weekday.WEDNESDAY, "Miércoles"),
    (WorkScheduleDay.Weekday.THURSDAY, "Jueves"),
    (WorkScheduleDay.Weekday.FRIDAY, "Viernes"),
    (WorkScheduleDay.Weekday.SATURDAY, "Sábado"),
    (WorkScheduleDay.Weekday.SUNDAY, "Domingo"),
]


def build_next_employee_number():
    values = Employee.objects.values_list("employee_number", flat=True)
    numeric_values = []
    for value in values:
        match = re.search(r"(\d+)$", str(value))
        if match:
            numeric_values.append(int(match.group(1)))

    next_number = max(numeric_values) + 1 if numeric_values else 1
    return f"EMP-{next_number:03d}"


def build_unique_username(first_name, last_name):
    User = get_user_model()
    first = re.sub(r"[^a-z0-9]+", "", first_name.lower()) or "empleado"
    last_initial = re.sub(r"[^a-z0-9]+", "", last_name[:1].lower()) if last_name else ""
    username = f"{first}.{last_initial}" if last_initial else first
    candidate_username = username
    counter = 1
    while User.objects.filter(username=candidate_username).exists():
        candidate_username = f"{username}{counter}"
        counter += 1
    return candidate_username


def welcome_view(request):
    return render(request, "attendance/welcome.html")


def logout_view(request):
    logout(request)
    return redirect("home")


def rh_login_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect("rh-admin-dashboard")
        if request.user.is_staff and not request.user.is_superuser:
            return redirect("rh-dashboard")
        if hasattr(request.user, "employee"):
            return redirect("rh-my-attendance")
        return redirect("rh-dashboard")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.is_superuser:
                return redirect("rh-admin-dashboard")
            if user.is_staff and not user.is_superuser:
                return redirect("rh-dashboard")
            if hasattr(user, "employee"):
                return redirect("rh-my-attendance")
            return redirect("rh-dashboard")
    else:
        form = AuthenticationForm(request)

    return render(request, "attendance/login.html", {"form": form})


@login_required(login_url="rh-login")
def rh_admin_dashboard_view(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("No tienes acceso a este panel")

    return render(request, "attendance/admin_dashboard.html")


@login_required(login_url="rh-login")
def rh_dashboard_view(request):
    if request.user.is_superuser:
        return redirect("rh-admin-dashboard")
    if not request.user.is_staff:
        return HttpResponseForbidden("No tienes acceso a este panel")

    total_employees = Employee.objects.count()
    active_schedules = WorkSchedule.objects.filter(active=True).count()
    total_attendances = Attendance.objects.count()
    recent_attendances = Attendance.objects.select_related("employee").order_by("-date")[:8]

    return render(
        request,
        "attendance/dashboard.html",
        {
            "total_employees": total_employees,
            "active_schedules": active_schedules,
            "total_attendances": total_attendances,
            "recent_attendances": recent_attendances,
        },
    )


@login_required(login_url="rh-login")
def rh_my_attendance_view(request):
    if request.user.is_superuser or request.user.is_staff:
        return HttpResponseForbidden("Esta vista es solo para trabajadores")

    employee = getattr(request.user, "employee", None)
    return render(
        request,
        "attendance/my_attendance.html",
        {
            "employee_name": str(employee) if employee else request.user.username,
            "employee_number": employee.employee_number if employee else "N/A",
        },
    )


@login_required(login_url="rh-login")
def rh_employees_view(request):
    if request.user.is_superuser or not request.user.is_staff:
        return HttpResponseForbidden("No tienes acceso a esta vista")

    if request.method == "POST":
        employee_id = request.POST.get("employee_id")
        employee = Employee.objects.get(pk=employee_id) if employee_id else None
        if employee is None:
            employee = Employee()

        if not employee.employee_number:
            employee.employee_number = build_next_employee_number()

        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        department = request.POST.get("department", "").strip()
        position = request.POST.get("position", "").strip()
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        role_type = request.POST.get("role_type", Employee.RoleType.WORKER)
        status_value = request.POST.get("status", Employee.Status.ACTIVE)

        employee.first_name = first_name
        employee.last_name = last_name
        employee.department = department
        employee.position = position
        employee.role_type = role_type
        employee.status = status_value

        if not employee.user_id:
            User = get_user_model()
            username_value = username or build_unique_username(first_name, last_name)
            user = User.objects.create_user(username=username_value, password=password or "empleado123")
            user.is_staff = role_type == Employee.RoleType.RH
            user.is_superuser = False
            user.save(update_fields=["is_staff", "is_superuser"])
            employee.user = user
        else:
            username_value = username or employee.user.username
            employee.user.username = username_value
            if password:
                employee.user.set_password(password)
            employee.user.is_staff = role_type == Employee.RoleType.RH
            employee.user.is_superuser = False
            employee.user.save()

        employee.save()
        return redirect("rh-employees")

    editing_id = request.GET.get("edit")
    employee_to_edit = None
    if editing_id:
        employee_to_edit = get_object_or_404(Employee, pk=editing_id)

    employee_username = employee_to_edit.user.username if employee_to_edit and employee_to_edit.user_id else ""

    employees = Employee.objects.order_by("first_name", "last_name")
    return render(
        request,
        "attendance/employees.html",
        {
            "employees": employees,
            "employee_to_edit": employee_to_edit,
            "employee_username": employee_username,
            "next_employee_number": build_next_employee_number(),
        },
    )


def parse_decimal(value, default):
    try:
        return Decimal(value)
    except (InvalidOperation, TypeError):
        return Decimal(default)


def build_schedule_day_rows(schedule=None):
    existing_days = {}
    if schedule:
        existing_days = {day.weekday: day for day in schedule.days.all()}

    rows = []
    for weekday, label in WEEKDAYS:
        day = existing_days.get(weekday)
        rows.append(
            {
                "weekday": int(weekday),
                "label": label,
                "start_time": day.start_time.strftime("%H:%M") if day else "08:00",
                "end_time": day.end_time.strftime("%H:%M") if day else "16:00",
                "tolerance_minutes": day.tolerance_minutes if day else 10,
                "regular_hours": day.regular_hours if day else Decimal("8.00"),
                "is_rest_day": day.is_rest_day if day else weekday in (6, 7),
            }
        )
    return rows


def save_schedule_days(schedule, post_data):
    for weekday, _label in WEEKDAYS:
        prefix = f"day_{int(weekday)}"
        is_rest_day = post_data.get(f"{prefix}_is_rest_day") == "on"
        start_time = post_data.get(f"{prefix}_start_time") or "00:00"
        end_time = post_data.get(f"{prefix}_end_time") or "00:00"
        tolerance = int(post_data.get(f"{prefix}_tolerance_minutes") or 10)
        regular_hours = parse_decimal(post_data.get(f"{prefix}_regular_hours"), "8.00")

        WorkScheduleDay.objects.update_or_create(
            schedule=schedule,
            weekday=weekday,
            defaults={
                "start_time": start_time,
                "end_time": end_time,
                "tolerance_minutes": tolerance,
                "regular_hours": regular_hours,
                "is_rest_day": is_rest_day,
            },
        )


@login_required(login_url="rh-login")
def rh_schedules_view(request):
    if request.user.is_superuser or not request.user.is_staff:
        return HttpResponseForbidden("No tienes acceso a esta vista")

    if request.method == "POST":
        schedule_id = request.POST.get("schedule_id")
        schedule = WorkSchedule.objects.get(pk=schedule_id) if schedule_id else None
        if schedule is None:
            schedule = WorkSchedule()
        schedule.name = request.POST.get("name", "").strip()
        schedule.description = request.POST.get("description", "").strip()
        schedule.active = request.POST.get("active") == "on"
        schedule.save()
        save_schedule_days(schedule, request.POST)
        return redirect("rh-schedules")

    editing_id = request.GET.get("edit")
    schedule_to_edit = get_object_or_404(WorkSchedule, pk=editing_id) if editing_id else None
    schedules = WorkSchedule.objects.prefetch_related("days").order_by("name")
    return render(
        request,
        "attendance/schedules.html",
        {
            "schedules": schedules,
            "schedule_to_edit": schedule_to_edit,
            "schedule_day_rows": build_schedule_day_rows(schedule_to_edit),
        },
    )


@login_required(login_url="rh-login")
def rh_attendance_report_view(request):
    if request.user.is_superuser or not request.user.is_staff:
        return HttpResponseForbidden("No tienes acceso a esta vista")
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    queryset = Attendance.objects.select_related("employee")
    if start_date:
        queryset = queryset.filter(date__gte=start_date)
    if end_date:
        queryset = queryset.filter(date__lte=end_date)

    summary = {
        "total": queryset.count(),
        "puntuales": queryset.filter(status=Attendance.Status.ON_TIME).count(),
        "tolerancias": queryset.filter(status=Attendance.Status.TOLERANCE).count(),
        "retardos": queryset.filter(status=Attendance.Status.LATE).count(),
        "faltas": queryset.filter(status=Attendance.Status.ABSENT).count(),
        "justificados": queryset.filter(status=Attendance.Status.JUSTIFIED).count(),
    }

    return render(
        request,
        "attendance/attendance_report.html",
        {
            "attendances": queryset.order_by("-date")[:50],
            "summary": summary,
            "start_date": start_date or "",
            "end_date": end_date or "",
        },
    )


class MobileProfileView(APIView):
    permission_classes = [IsEmployee]

    def get(self, request):
        return Response(EmployeeSerializer(request.user.employee).data)


class MobileAttendanceHistoryView(APIView):
    permission_classes = [IsEmployee]

    def get(self, request):
        queryset = (
            Attendance.objects.filter(employee=request.user.employee)
            .prefetch_related("records")
            .select_related("employee")
            .order_by("-date")[:60]
        )
        serializer = AttendanceSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data)


class MobileCheckInView(APIView):
    permission_classes = [IsEmployee]

    def post(self, request):
        serializer = AttendanceCaptureSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attendance = register_attendance_record(
            request.user.employee,
            AttendanceRecord.RecordType.CHECK_IN,
            serializer.validated_data,
            request,
        )
        response = AttendanceSerializer(attendance, context={"request": request})
        return Response(response.data, status=status.HTTP_201_CREATED)


class MobileCheckOutView(APIView):
    permission_classes = [IsEmployee]

    def post(self, request):
        serializer = AttendanceCaptureSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attendance = register_attendance_record(
            request.user.employee,
            AttendanceRecord.RecordType.CHECK_OUT,
            serializer.validated_data,
            request,
        )
        response = AttendanceSerializer(attendance, context={"request": request})
        return Response(response.data, status=status.HTTP_201_CREATED)


class EmployeeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsHumanResources]
    queryset = Employee.objects.select_related("user").all()
    serializer_class = EmployeeSerializer


class WorkScheduleViewSet(viewsets.ModelViewSet):
    permission_classes = [IsHumanResources]
    queryset = WorkSchedule.objects.prefetch_related("days").all()
    serializer_class = WorkScheduleSerializer


class AttendanceViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsHumanResources]
    queryset = Attendance.objects.select_related("employee").prefetch_related("records").all()
    serializer_class = AttendanceSerializer

    @action(detail=True, methods=["post"])
    def justify(self, request, pk=None):
        attendance = self.get_object()
        serializer = JustificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(
            attendance=attendance,
            employee=attendance.employee,
            approved_by=request.user,
        )
        attendance.status = serializer.validated_data["justification_type"]
        attendance.modified_by = request.user
        attendance.notes = serializer.validated_data["reason"]
        attendance.save(update_fields=["status", "modified_by", "notes", "updated_at"])
        return Response(AttendanceSerializer(attendance, context={"request": request}).data)


class ReportSummaryView(APIView):
    permission_classes = [IsHumanResources]

    def get(self, request):
        queryset = Attendance.objects.all()
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        return Response(
            {
                "total": queryset.count(),
                "puntuales": queryset.filter(status=Attendance.Status.ON_TIME).count(),
                "tolerancias": queryset.filter(status=Attendance.Status.TOLERANCE).count(),
                "retardos": queryset.filter(status=Attendance.Status.LATE).count(),
                "faltas": queryset.filter(status=Attendance.Status.ABSENT).count(),
                "justificados": queryset.filter(status=Attendance.Status.JUSTIFIED).count(),
            }
        )
