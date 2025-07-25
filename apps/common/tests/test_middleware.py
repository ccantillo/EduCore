"""
Tests para middleware personalizado.
Incluye logging de requests, seguimiento de usuarios y medición de duración.
"""

import pytest
import time
from unittest.mock import Mock, patch
from django.http import HttpRequest, HttpResponse
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.common.middleware import RequestLoggingMiddleware

User = get_user_model()


@pytest.mark.django_db
class TestRequestLoggingMiddleware:
    """Tests para el middleware de logging de requests."""
    
    def setup_method(self):
        """Configuración inicial para cada test."""
        self.factory = RequestFactory()
        self.client = APIClient()
        
        # Crear usuarios de prueba
        self.admin_user = User.objects.create_user(
            username='admin_middleware',
            email='admin@test.com',
            password='testpass123',
            role='admin'
        )
        
        self.student_user = User.objects.create_user(
            username='student_middleware',
            email='student@test.com',
            password='testpass123',
            role='estudiante'
        )
        
        # Mock de la vista siguiente
        self.get_response = Mock(return_value=HttpResponse('Test response'))
        
        # Inicializar middleware
        self.middleware = RequestLoggingMiddleware(self.get_response)
    
    def test_middleware_initialization(self):
        """Test de inicialización del middleware."""
        middleware = RequestLoggingMiddleware(self.get_response)
        assert middleware.get_response == self.get_response
    
    @patch('apps.common.middleware.logger')
    def test_middleware_logs_anonymous_request(self, mock_logger):
        """Test de que el middleware registra requests anónimos."""
        request = self.factory.get('/test/')
        request.user = None
        
        response = self.middleware(request)
        
        # Verificar que se llamó al logger
        assert mock_logger.info.called
        
        # Verificar el contenido del log
        log_call = mock_logger.info.call_args[0][0]
        assert 'anonymous' in log_call.lower()
        assert 'GET' in log_call
        assert '/test/' in log_call
    
    @patch('apps.common.middleware.logger')
    def test_middleware_logs_authenticated_request(self, mock_logger):
        """Test de que el middleware registra requests autenticados."""
        request = self.factory.get('/test/')
        request.user = self.admin_user
        
        response = self.middleware(request)
        
        # Verificar que se llamó al logger
        assert mock_logger.info.called
        
        # Verificar el contenido del log
        log_call = mock_logger.info.call_args[0][0]
        assert 'admin_middleware' in log_call
        assert 'admin' in log_call
        assert 'GET' in log_call
        assert '/test/' in log_call
    
    @patch('apps.common.middleware.logger')
    def test_middleware_measures_request_duration(self, mock_logger):
        """Test de que el middleware mide la duración del request."""
        # Simular una vista que toma tiempo
        def slow_response(request):
            time.sleep(0.1)  # 100ms
            return HttpResponse('Slow response')
        
        middleware = RequestLoggingMiddleware(slow_response)
        request = self.factory.get('/slow/')
        request.user = self.student_user
        
        response = middleware(request)
        
        # Verificar que se llamó al logger
        assert mock_logger.info.called
        
        # Verificar que se registró la duración
        log_call = mock_logger.info.call_args[0][0]
        assert 'ms' in log_call  # Debe contener duración en milisegundos
    
    @patch('apps.common.middleware.logger')
    def test_middleware_logs_different_http_methods(self, mock_logger):
        """Test de que el middleware registra diferentes métodos HTTP."""
        methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
        
        for method in methods:
            mock_logger.reset_mock()
            
            if method == 'GET':
                request = self.factory.get('/test/')
            elif method == 'POST':
                request = self.factory.post('/test/', {'data': 'test'})
            elif method == 'PUT':
                request = self.factory.put('/test/', {'data': 'test'})
            elif method == 'DELETE':
                request = self.factory.delete('/test/')
            elif method == 'PATCH':
                request = self.factory.patch('/test/', {'data': 'test'})
            
            request.user = self.admin_user
            
            response = self.middleware(request)
            
            # Verificar que se registró el método correcto
            assert mock_logger.info.called
            log_call = mock_logger.info.call_args[0][0]
            assert method in log_call
    
    @patch('apps.common.middleware.logger')
    def test_middleware_logs_request_path(self, mock_logger):
        """Test de que el middleware registra la ruta del request."""
        paths = [
            '/api/users/',
            '/api/materias/',
            '/api/inscripciones/',
            '/admin/',
            '/swagger/',
        ]
        
        for path in paths:
            mock_logger.reset_mock()
            
            request = self.factory.get(path)
            request.user = self.admin_user
            
            response = self.middleware(request)
            
            # Verificar que se registró la ruta correcta
            assert mock_logger.info.called
            log_call = mock_logger.info.call_args[0][0]
            assert path in log_call
    
    @patch('apps.common.middleware.logger')
    def test_middleware_logs_user_role(self, mock_logger):
        """Test de que el middleware registra el rol del usuario."""
        users_and_roles = [
            (self.admin_user, 'admin'),
            (self.student_user, 'estudiante'),
        ]
        
        for user, role in users_and_roles:
            mock_logger.reset_mock()
            
            request = self.factory.get('/test/')
            request.user = user
            
            response = self.middleware(request)
            
            # Verificar que se registró el rol correcto
            assert mock_logger.info.called
            log_call = mock_logger.info.call_args[0][0]
            assert role in log_call
    
    @patch('apps.common.middleware.logger')
    def test_middleware_handles_exception_in_view(self, mock_logger):
        """Test de que el middleware maneja excepciones en las vistas."""
        def failing_view(request):
            raise Exception("Test exception")
        
        middleware = RequestLoggingMiddleware(failing_view)
        request = self.factory.get('/failing/')
        request.user = self.admin_user
        
        # El middleware no debe fallar, aunque la vista sí
        with pytest.raises(Exception, match="Test exception"):
            middleware(request)
        
        # Debe haber registrado el request inicial
        assert mock_logger.info.called
    
    @patch('apps.common.middleware.logger')
    def test_middleware_logs_ip_address(self, mock_logger):
        """Test de que el middleware registra la dirección IP."""
        request = self.factory.get('/test/')
        request.user = self.admin_user
        request.META['REMOTE_ADDR'] = '192.168.1.100'
        
        response = self.middleware(request)
        
        # Verificar que se registró la IP
        assert mock_logger.info.called
        log_call = mock_logger.info.call_args[0][0]
        assert '192.168.1.100' in log_call
    
    @patch('apps.common.middleware.logger')
    def test_middleware_logs_user_agent(self, mock_logger):
        """Test de que el middleware registra el User-Agent."""
        request = self.factory.get('/test/')
        request.user = self.admin_user
        request.META['HTTP_USER_AGENT'] = 'Mozilla/5.0 Test Browser'
        
        response = self.middleware(request)
        
        # Verificar que se registró el User-Agent
        assert mock_logger.info.called
        log_call = mock_logger.info.call_args[0][0]
        assert 'Mozilla/5.0 Test Browser' in log_call
    
    @patch('apps.common.middleware.logger')
    def test_middleware_performance_measurement(self, mock_logger):
        """Test de medición de rendimiento del middleware."""
        def normal_view(request):
            return HttpResponse('Normal response')
        
        middleware = RequestLoggingMiddleware(normal_view)
        request = self.factory.get('/performance/')
        request.user = self.admin_user
        
        start_time = time.time()
        response = middleware(request)
        end_time = time.time()
        
        # El middleware no debe agregar mucho overhead
        total_time = end_time - start_time
        assert total_time < 0.1  # Menos de 100ms de overhead
        
        # Debe haber registrado la duración
        assert mock_logger.info.called
    
    def test_middleware_preserves_response(self):
        """Test de que el middleware preserva la respuesta original."""
        expected_content = 'Original response content'
        
        def test_view(request):
            return HttpResponse(expected_content)
        
        middleware = RequestLoggingMiddleware(test_view)
        request = self.factory.get('/test/')
        request.user = self.admin_user
        
        response = middleware(request)
        
        # La respuesta debe ser la misma que devolvió la vista
        assert response.content.decode() == expected_content
    
    def test_middleware_preserves_status_code(self):
        """Test de que el middleware preserva el código de estado."""
        def test_view(request):
            return HttpResponse('Not found', status=404)
        
        middleware = RequestLoggingMiddleware(test_view)
        request = self.factory.get('/test/')
        request.user = self.admin_user
        
        response = middleware(request)
        
        # El status code debe ser preservado
        assert response.status_code == 404


@pytest.mark.django_db
class TestMiddlewareIntegration:
    """Tests de integración del middleware con la aplicación."""
    
    def setup_method(self):
        """Configuración inicial para tests de integración."""
        self.client = APIClient()
        
        # Crear usuario para tests
        self.test_user = User.objects.create_user(
            username='integration_user',
            email='integration@test.com',
            password='testpass123',
            role='estudiante'
        )
    
    def get_token_for_user(self, user):
        """Helper para obtener token JWT."""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    @patch('apps.common.middleware.logger')
    def test_middleware_with_real_api_request(self, mock_logger):
        """Test del middleware con request real a la API."""
        # Autenticar usuario
        token = self.get_token_for_user(self.test_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Hacer request a endpoint real
        response = self.client.get('/api/v1/users/me/')
        
        # Verificar que el middleware registró el request
        assert mock_logger.info.called
        
        # Verificar contenido del log
        log_call = mock_logger.info.call_args[0][0]
        assert 'integration_user' in log_call
        assert 'estudiante' in log_call
        assert 'GET' in log_call
        assert '/api/v1/users/me/' in log_call
    
    @patch('apps.common.middleware.logger')
    def test_middleware_with_unauthenticated_request(self, mock_logger):
        """Test del middleware con request no autenticado."""
        # Hacer request sin autenticación
        response = self.client.get('/api/v1/users/me/')
        
        # Verificar que el middleware registró el request
        assert mock_logger.info.called
        
        # Verificar que se registró como anónimo
        log_call = mock_logger.info.call_args[0][0]
        assert 'anonymous' in log_call.lower()
    
    @patch('apps.common.middleware.logger')
    def test_middleware_logs_multiple_consecutive_requests(self, mock_logger):
        """Test del middleware con múltiples requests consecutivos."""
        token = self.get_token_for_user(self.test_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        endpoints = [
            '/api/v1/users/me/',
            '/api/v1/materias/',
            '/api/v1/inscripciones/',
        ]
        
        for endpoint in endpoints:
            self.client.get(endpoint)
        
        # Verificar que se registraron todos los requests
        assert mock_logger.info.call_count >= len(endpoints)
    
    @patch('apps.common.middleware.logger')
    def test_middleware_with_different_content_types(self, mock_logger):
        """Test del middleware con diferentes tipos de contenido."""
        token = self.get_token_for_user(self.test_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Request JSON
        self.client.post('/api/v1/users/', {
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'newpass123'
        }, format='json')
        
        # Verificar que se registró
        assert mock_logger.info.called
        
        # Verificar que se registró el método POST
        log_call = mock_logger.info.call_args[0][0]
        assert 'POST' in log_call


@pytest.mark.django_db
class TestMiddlewareConfiguration:
    """Tests para configuración y comportamiento del middleware."""
    
    def test_middleware_order_independence(self):
        """Test de que el middleware funciona independiente del orden."""
        factory = RequestFactory()
        
        def simple_view(request):
            return HttpResponse('Simple response')
        
        # El middleware debe funcionar sin importar qué otros middleware estén presentes
        middleware = RequestLoggingMiddleware(simple_view)
        request = factory.get('/test/')
        request.user = None
        
        response = middleware(request)
        
        assert response.status_code == 200
        assert response.content.decode() == 'Simple response'
    
    @patch('apps.common.middleware.logger')
    def test_middleware_handles_large_request_body(self, mock_logger):
        """Test de que el middleware maneja cuerpos de request grandes."""
        factory = RequestFactory()
        
        def simple_view(request):
            return HttpResponse('OK')
        
        middleware = RequestLoggingMiddleware(simple_view)
        
        # Crear request con cuerpo grande
        large_data = {'data': 'x' * 10000}  # 10KB de datos
        request = factory.post('/test/', large_data)
        request.user = None
        
        response = middleware(request)
        
        # Debe manejar el request sin problemas
        assert response.status_code == 200
        assert mock_logger.info.called
    
    @patch('apps.common.middleware.logger')
    def test_middleware_thread_safety(self, mock_logger):
        """Test básico de thread safety del middleware."""
        import threading
        import time
        
        factory = RequestFactory()
        results = []
        
        def test_view(request):
            time.sleep(0.01)  # Simular procesamiento
            return HttpResponse(f'Response for {request.user}')
        
        middleware = RequestLoggingMiddleware(test_view)
        
        def make_request(username):
            user = User.objects.create_user(
                username=username,
                email=f'{username}@test.com',
                password='testpass123'
            )
            request = factory.get('/test/')
            request.user = user
            response = middleware(request)
            results.append((username, response.status_code))
        
        # Crear múltiples threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request, args=[f'user_{i}'])
            threads.append(thread)
            thread.start()
        
        # Esperar a que terminen todos
        for thread in threads:
            thread.join()
        
        # Verificar que todos los requests se procesaron correctamente
        assert len(results) == 5
        for username, status_code in results:
            assert status_code == 200
        
        # Verificar que se registraron todos los requests
        assert mock_logger.info.call_count >= 5 