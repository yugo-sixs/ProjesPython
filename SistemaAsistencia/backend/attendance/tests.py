from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase

from attendance.models import Employee, WorkSchedule, WorkScheduleDay


class RootUrlTests(SimpleTestCase):
    def test_root_welcome_page_is_available(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sistema de Checado")

    def test_api_root_is_public(self):
        response = self.client.get("/api/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], "API de control de asistencia")
        self.assertIn("rh", response.json()["endpoints"])

    def test_rh_login_page_is_available(self):
        response = self.client.get("/rh/login/")

        self.assertEqual(response.status_code, 200)


class EmployeeManagementTests(TestCase):
    def setUp(self):
        self.User = get_user_model()

    def test_rh_can_create_employee_with_auto_number_and_role(self):
        rh_user = self.User.objects.create_user(username="rh_test", password="secret123", is_staff=True)
        self.client.force_login(rh_user)

        response = self.client.post(
            "/rh/empleados/",
            {
                "first_name": "Carlos",
                "last_name": "Pérez",
                "department": "Ventas",
                "position": "Vendedor",
                "status": "ACTIVO",
                "role_type": "WORKER",
            },
        )

        self.assertEqual(response.status_code, 302)
        employee = Employee.objects.get(first_name="Carlos", last_name="Pérez")
        self.assertEqual(employee.employee_number, "EMP-001")
        self.assertEqual(employee.role_type, "WORKER")

    def test_rh_can_create_schedule_days(self):
        rh_user = self.User.objects.create_user(username="rh_schedule", password="secret123", is_staff=True)
        self.client.force_login(rh_user)

        payload = {
            "name": "Matutino",
            "description": "Horario base",
            "active": "on",
        }
        for weekday in range(1, 8):
            payload[f"day_{weekday}_start_time"] = "08:00"
            payload[f"day_{weekday}_end_time"] = "16:00"
            payload[f"day_{weekday}_tolerance_minutes"] = "10"
            payload[f"day_{weekday}_regular_hours"] = "8.00"
        payload["day_6_is_rest_day"] = "on"
        payload["day_7_is_rest_day"] = "on"

        response = self.client.post("/rh/horarios/", payload)

        self.assertEqual(response.status_code, 302)
        schedule = WorkSchedule.objects.get(name="Matutino")
        self.assertEqual(schedule.days.count(), 7)
        self.assertTrue(WorkScheduleDay.objects.get(schedule=schedule, weekday=6).is_rest_day)


class RoleRedirectTests(TestCase):
    def setUp(self):
        self.User = get_user_model()

    def test_superuser_redirects_to_admin_dashboard(self):
        admin_user = self.User.objects.create_user(username="admin_test", password="secret123", is_superuser=True, is_staff=True)
        Employee.objects.create(user=admin_user, employee_number="ADM-TEST", first_name="Admin", last_name="Test")

        response = self.client.post(
            "/rh/login/",
            {"username": "admin_test", "password": "secret123"},
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/rh/admin-dashboard/")

    def test_rh_user_redirects_to_rh_dashboard(self):
        rh_user = self.User.objects.create_user(username="rh_test", password="secret123", is_staff=True)
        Employee.objects.create(user=rh_user, employee_number="RH-TEST", first_name="RH", last_name="Test", role_type=Employee.RoleType.RH)

        response = self.client.post(
            "/rh/login/",
            {"username": "rh_test", "password": "secret123"},
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/rh/dashboard/")

    def test_worker_redirects_to_worker_dashboard(self):
        worker_user = self.User.objects.create_user(username="worker_test", password="secret123")
        Employee.objects.create(user=worker_user, employee_number="EMP-TEST", first_name="Juan", last_name="Test")

        response = self.client.post(
            "/rh/login/",
            {"username": "worker_test", "password": "secret123"},
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/rh/mi-asistencia/")
