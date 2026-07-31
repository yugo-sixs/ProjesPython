from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Attendance, AttendanceRecord, Employee, Justification, WorkSchedule
from .permissions import IsEmployee, IsHumanResources
from .serializers import (
    AttendanceCaptureSerializer,
    AttendanceSerializer,
    EmployeeSerializer,
    JustificationSerializer,
    WorkScheduleSerializer,
)
from .services import register_attendance_record


def rh_login_view(request):
    if request.user.is_authenticated:
        return redirect("rh-dashboard")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("rh-dashboard")
    else:
        form = AuthenticationForm(request)

    return render(request, "attendance/login.html", {"form": form})


@login_required(login_url="rh-login")
def rh_dashboard_view(request):
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
def rh_employees_view(request):
    employees = Employee.objects.order_by("first_name", "last_name")
    return render(request, "attendance/employees.html", {"employees": employees})


@login_required(login_url="rh-login")
def rh_schedules_view(request):
    schedules = WorkSchedule.objects.order_by("name")
    return render(request, "attendance/schedules.html", {"schedules": schedules})


@login_required(login_url="rh-login")
def rh_attendance_report_view(request):
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
