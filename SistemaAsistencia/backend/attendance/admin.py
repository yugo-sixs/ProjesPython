from django.contrib import admin

from .models import Attendance, AttendanceRecord, Employee, EmployeeSchedule, Justification, WorkSchedule, WorkScheduleDay


class WorkScheduleDayInline(admin.TabularInline):
    model = WorkScheduleDay
    extra = 1


@admin.register(WorkSchedule)
class WorkScheduleAdmin(admin.ModelAdmin):
    list_display = ("name", "active", "created_at")
    search_fields = ("name",)
    inlines = [WorkScheduleDayInline]


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("employee_number", "first_name", "last_name", "department", "position", "status")
    list_filter = ("status", "department")
    search_fields = ("employee_number", "first_name", "last_name", "user__username")


@admin.register(EmployeeSchedule)
class EmployeeScheduleAdmin(admin.ModelAdmin):
    list_display = ("employee", "schedule", "start_date", "end_date", "active")
    list_filter = ("active", "schedule")
    search_fields = ("employee__employee_number", "employee__first_name", "employee__last_name")


class AttendanceRecordInline(admin.TabularInline):
    model = AttendanceRecord
    extra = 0
    readonly_fields = ("server_datetime", "source_ip")


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("employee", "date", "check_in_time", "check_out_time", "status", "total_hours", "overtime_hours")
    list_filter = ("status", "date")
    search_fields = ("employee__employee_number", "employee__first_name", "employee__last_name")
    inlines = [AttendanceRecordInline]


@admin.register(Justification)
class JustificationAdmin(admin.ModelAdmin):
    list_display = ("employee", "attendance", "justification_type", "approved_by", "approved_at")
    list_filter = ("justification_type", "approved_at")
