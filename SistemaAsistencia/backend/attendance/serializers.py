from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Attendance, AttendanceRecord, Employee, EmployeeSchedule, Justification, WorkSchedule, WorkScheduleDay


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "is_staff", "is_superuser"]


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
            "role_type",
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
            "food_break_minutes",
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
    latitude = serializers.DecimalField(max_digits=10, decimal_places=8, min_value=Decimal("-90"), max_value=Decimal("90"))
    longitude = serializers.DecimalField(max_digits=11, decimal_places=8, min_value=Decimal("-180"), max_value=Decimal("180"))
    gps_accuracy = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=Decimal("0"))
    employee_photo = serializers.ImageField()
    environment_photo = serializers.ImageField(required=False)
    device_id = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def validate(self, attrs):
        for field in ("employee_photo", "environment_photo"):
            photo = attrs.get(field)
            if photo and photo.size > 8 * 1024 * 1024:
                raise serializers.ValidationError({field: "La fotografía no puede superar 8 MB."})
        return attrs


class EmployeeScheduleSerializer(serializers.ModelSerializer):
    employee = EmployeeSerializer(read_only=True)
    schedule = WorkScheduleSerializer(read_only=True)
    employee_id = serializers.PrimaryKeyRelatedField(source="employee", queryset=Employee.objects.all(), write_only=True)
    schedule_id = serializers.PrimaryKeyRelatedField(source="schedule", queryset=WorkSchedule.objects.all(), write_only=True)

    class Meta:
        model = EmployeeSchedule
        fields = ["id", "employee", "schedule", "employee_id", "schedule_id", "start_date", "end_date", "active"]

    def validate(self, attrs):
        start_date = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end_date = attrs.get("end_date", getattr(self.instance, "end_date", None))
        if end_date and start_date and end_date < start_date:
            raise serializers.ValidationError({"end_date": "La fecha final no puede ser anterior a la fecha inicial."})
        return attrs


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
