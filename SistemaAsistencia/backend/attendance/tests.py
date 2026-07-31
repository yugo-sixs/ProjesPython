from django.test import SimpleTestCase


class RootUrlTests(SimpleTestCase):
    def test_root_redirects_to_api_root(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/api/")

    def test_api_root_is_public(self):
        response = self.client.get("/api/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], "API de control de asistencia")
        self.assertIn("rh", response.json()["endpoints"])

    def test_rh_login_page_is_available(self):
        response = self.client.get("/rh/login/")

        self.assertEqual(response.status_code, 200)
