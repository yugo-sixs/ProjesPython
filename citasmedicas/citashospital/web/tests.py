from django.test import TestCase

# Create your tests here.
from django.test import TestCase, Client
from django.urls import reverse


class CrearUsuarioViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_get_crear_usuario(self):
        """Verifica que la vista de crear usuario responde correctamente al GET."""
        response = self.client.get(reverse('crear_usuario'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'crear_usuario.html')
