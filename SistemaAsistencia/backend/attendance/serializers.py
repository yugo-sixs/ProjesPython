from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Attendance, AttendanceRecord, Employee, EmployeeSchedule, Justification, WorkSchedule, WorkScheduleDay


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "is_staff"]


class EmployeeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        source="user",
        queryset=User.objects.all(),
        write_only=True,
        required=False,
    )

    class Meta:
        model = Employee
        fields = [
            "id",
            "user",
            "user_id",
            "employee_number",
            "first_name",
            "last_name",
            "phone",
            "department",
            "position",
            "hire_date",
            "termination_date",
            "status",
        ]


class WorkScheduleDaySerializer(serializers.ModelSerializer):
    weekday_label = serializers.CharField(source="get_weekday_display", read_only=True)

    class Meta:
        model = WorkScheduleDay
        fields = [
            "id",
            "weekday",
            "weekday_label",
            "start_time",
            "end_time",
            "tolerance_minutes",
            "regular_hours",
            "is_rest_day",
        ]


class WorkScheduleSerializer(serializers.ModelSerializer):
    days = WorkScheduleDaySerializer(many=True, required=False)

    class Meta:
        model = WorkSchedule
        fields = ["id", "name", "description", "active", "days"]

    def create(self, validated_data):
        days_data = validated_data.pop("days", [])
        schedule = WorkSchedule.objects.create(**validated_data)
        for day_data in days_data:
            WorkScheduleDay.objects.create(schedule=schedule, **day_data)
        return schedule

    def update(self, instance, validated_data):
        days_data = validated_data.pop("days", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if days_data is not None:
            instance.days.all().delete()
            for day_data in days_data:
                WorkScheduleDay.objects.create(schedule=instance, **day_data)

        return instance


class AttendanceRecordSerializer(serializers.ModelSerializer):
    employee_photo_url = serializers.SerializerMethodField()
    environment_photo_url = serializers.SerializerMethodField()

    class Meta:
        model = AttendanceRecord
        fields = [
            "id",
            "record_type",
            "device_datetime",
            "server_datetime",
            "latitude",
            "longitude",
            "gps_accuracy",
            "employee_photo_url",
            "environment_photo_url",
            "device_id",
        ]

    def get_employee_photo_url(self, obj):
        request = self.context.get("request")
        if obj.employee_photo and request:
            return request.build_absolute_uri(obj.employee_photo.url)
        return None

    def get_environment_photo_url(self, obj):
        request = self.context.get("request")
        if obj.environment_photo and request:
            return request.build_absolute_uri(obj.environment_photo.url)
        return None


class AttendanceSerializer(serializers.ModelSerializer):
    records = AttendanceRecordSerializer(many=True, read_only=True)
    employee = EmployeeSerializer(read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Attendance
        fields = [
            "id",
            "employee",
            "date",
            "check_in_time",
            "check_out_time",
            "status",
            "status_label",
            "total_hours",
            "overtime_hours",
            "notes",
            "records",
        ]


class AttendanceCaptureSerializer(serializers.Serializer):
    device_datetime = serializers.DateTimeField()
    latitude = serializers.DecimalField(max_digits=10, decimal_places=8, required=False)
    longitude = serializers.DecimalField(max_digits=11, decimal_places=8, required=False)
    gps_accuracy = serializers.DecimalField(max_digits=8, decimal_places=2, required=False)
    employee_photo = serializers.ImageField(required=False)
    environment_photo = serializers.ImageField(required=False)
    device_id = serializers.CharField(max_length=255, required=False, allow_blank=True)


class EmployeeScheduleSerializer(serializers.ModelSerializer):
    employee = EmployeeSerializer(read_only=True)
    schedule = WorkScheduleSerializer(read_only=True)

    class Meta:
        model = EmployeeSchedule
        fields = ["id", "employee", "schedule", "start_date", "end_date", "active"]


class JustificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Justification
        fields = [
            "id",
            "attendance",
            "employee",
            "justification_type",
            "reason",
            "attachment",
            "approved_by",
            "approved_at",
        ]
        read_only_fields = ["attendance", "employee", "approved_by", "approved_at"]
