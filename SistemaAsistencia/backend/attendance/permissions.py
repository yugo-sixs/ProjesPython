from rest_framework.permissions import BasePermission


class IsHumanResources(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class IsEmployee(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, "employee")
            and request.user.employee.status == "ACTIVO"
        )
