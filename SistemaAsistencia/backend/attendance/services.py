from datetime import datetime, timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from .models import Attendance, AttendanceRecord, EmployeeSchedule


def get_employee_schedule_day(employee, work_date):
    assignment = (
        EmployeeSchedule.objects.select_related("schedule")
        .filter(employee=employee, active=True, start_date__lte=work_date)
        .filter(end_date__isnull=True)
        .order_by("-start_date")
        .first()
    )
    if assignment is None:
        assignment = (
            EmployeeSchedule.objects.select_related("schedule")
            .filter(employee=employee, active=True, start_date__lte=work_date, end_date__gte=work_date)
            .order_by("-start_date")
            .first()
        )
    if assignment is None:
        return None

    return assignment.schedule.days.filter(weekday=work_date.isoweekday()).first()


def classify_check_in(schedule_day, device_datetime):
    if schedule_day is None:
        return Attendance.Status.OTHER
    if schedule_day.is_rest_day:
        return Attendance.Status.REST

    scheduled_datetime = datetime.combine(device_datetime.date(), schedule_day.start_time)
    scheduled_datetime = timezone.make_aware(scheduled_datetime, timezone.get_current_timezone())
    if timezone.is_naive(device_datetime):
        device_datetime = timezone.make_aware(device_datetime, timezone.get_current_timezone())
    tolerance_limit = scheduled_datetime + timedelta(minutes=schedule_day.tolerance_minutes)

    if device_datetime <= scheduled_datetime:
        return Attendance.Status.ON_TIME
    if device_datetime <= tolerance_limit:
        return Attendance.Status.TOLERANCE
    return Attendance.Status.LATE


def calculate_worked_hours(check_in_time, check_out_time, regular_hours=Decimal("8.00")):
    if not check_in_time or not check_out_time:
        return Decimal("0.00"), Decimal("0.00")

    start = datetime.combine(timezone.localdate(), check_in_time)
    end = datetime.combine(timezone.localdate(), check_out_time)
    if end < start:
        end += timedelta(days=1)

    total = Decimal(str(round((end - start).total_seconds() / 3600, 2)))
    overtime = max(Decimal("0.00"), total - Decimal(regular_hours))
    return total, overtime


def get_client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


@transaction.atomic
def register_attendance_record(employee, record_type, validated_data, request):
    device_datetime = validated_data["device_datetime"]
    work_date = device_datetime.date()
    schedule_day = get_employee_schedule_day(employee, work_date)

    attendance, _ = Attendance.objects.get_or_create(
        employee=employee,
        date=work_date,
        defaults={"schedule_day": schedule_day},
    )

    if schedule_day and attendance.schedule_day_id is None:
        attendance.schedule_day = schedule_day

    if record_type == AttendanceRecord.RecordType.CHECK_IN:
        attendance.check_in_time = device_datetime.time()
        attendance.status = classify_check_in(schedule_day, device_datetime)
    else:
        attendance.check_out_time = device_datetime.time()
        regular_hours = schedule_day.regular_hours if schedule_day else Decimal("8.00")
        total_hours, overtime_hours = calculate_worked_hours(
            attendance.check_in_time,
            attendance.check_out_time,
            regular_hours,
        )
        attendance.total_hours = total_hours
        attendance.overtime_hours = overtime_hours

    attendance.save()

    AttendanceRecord.objects.create(
        attendance=attendance,
        employee=employee,
        record_type=record_type,
        device_date=work_date,
        device_time=device_datetime.time(),
        device_datetime=device_datetime,
        latitude=validated_data.get("latitude"),
        longitude=validated_data.get("longitude"),
        gps_accuracy=validated_data.get("gps_accuracy"),
        employee_photo=validated_data.get("employee_photo"),
        environment_photo=validated_data.get("environment_photo"),
        device_id=validated_data.get("device_id", ""),
        source_ip=get_client_ip(request),
    )

    return attendance
