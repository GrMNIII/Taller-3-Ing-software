from django.test import TestCase, RequestFactory
from tevo.views import login_view  
from unittest.mock import patch

class LoginViewTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_login_view_missing_credentials(self):
        # Crear una solicitud POST simulada con campos vacíos
        request = self.factory.post('/login/', {
            'email': '',  # Falta el correo
            'password': ''  # Falta la contraseña
        })

        # Llamar a la vista con la solicitud simulada
        response = login_view(request)

        # Verificar que el código de estado sea 200
        self.assertEqual(response.status_code, 200)

        # Verificar que el mensaje de error sea diferente al que realmente devuelve la vista
        self.assertIn('Correo electrónico y contraseña son obligatorios', response.content.decode('utf-8'))

    @patch('services.api.client.APIClient.login')  # Simula el comportamiento del método login
    def test_login_view_missing_token(self, mock_login):
        # Configurar el mock para devolver una respuesta sin token
        mock_login.return_value = {}

        # Crear una solicitud POST simulada con datos válidos
        request = self.factory.post('/login/', {
            'email': 'test@example.com',
            'password': 'password123'
        })

        # Llamar a la vista con la solicitud simulada
        response = login_view(request)

        # Verificar que el código de estado sea 200
        self.assertEqual(response.status_code, 200)

        # Verificar que el mensaje de error correcto esté en el contenido
        self.assertIn('No fue posible iniciar sesión. Intente más tarde.', response.content.decode('utf-8'))
