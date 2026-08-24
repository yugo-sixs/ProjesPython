from rest_framework.permissions import BasePermission

from .models import Employee


class IsHumanResources(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_staff
        )


class IsEmployee(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_staff or request.user.is_superuser:
            return False
        if not hasattr(request.user, "employee"):
            return False

        employee = request.user.employee
        return employee.status == Employee.Status.ACTIVE and employee.role_type == Employee.RoleType.WORKER
