"""
Tests para middleware de la app common.
"""

import pytest
import logging
from django.test import TestCase, RequestFactory
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import AnonymousUser
from django.conf import settings
from unittest.mock import Mock, patch, MagicMock
from apps.common.middleware import RoleMiddleware, SecurityMiddleware, RequestLoggingMiddleware
from apps.users.models import User


@pytest.mark.django_db
class TestRoleMiddleware(TestCase):
    """Tests para RoleMiddleware."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        self.factory = RequestFactory()
        self.get_response = Mock(return_value=HttpResponse())
        self.middleware = RoleMiddleware(self.get_response)
        
        # Crear usuario de prueba
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='password123',
            role='estudiante'
        )
    
    def test_init(self):
        """Test que el middleware se inicializa correctamente."""
        middleware = RoleMiddleware(self.get_response)
        self.assertEqual(middleware.get_response, self.get_response)
    
    @patch('apps.common.middleware.logger')
    def test_call_with_authenticated_user(self, mock_logger):
        """Test del middleware con usuario autenticado."""
        request = self.factory.get('/test/')
        request.user = self.user
        
        self.middleware(request)
        
        # Verificar que se registró la información del usuario
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        self.assertIn('testuser', call_args)
        self.assertIn('estudiante', call_args)
        self.assertIn('/test/', call_args)
        self.assertIn('GET', call_args)
    
    @patch('apps.common.middleware.logger')
    def test_call_with_anonymous_user(self, mock_logger):
        """Test del middleware con usuario anónimo."""
        request = self.factory.get('/test/')
        request.user = AnonymousUser()
        
        self.middleware(request)
        
        # No debería registrar información para usuarios anónimos
        mock_logger.info.assert_not_called()
    
    @patch('apps.common.middleware.logger')
    def test_log_response_info_with_error(self, mock_logger):
        """Test del logging de respuestas con errores."""
        request = self.factory.get('/test/')
        request.user = self.user
        
        # Configurar respuesta con error
        error_response = HttpResponse(status=400)
        self.get_response.return_value = error_response
        
        self.middleware(request)
        
        # Verificar que se registró el warning por el error
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]
        self.assertIn('testuser', call_args)
        self.assertIn('400', call_args)
        self.assertIn('/test/', call_args)
    
    @patch('apps.common.middleware.logger')
    def test_log_response_info_with_success(self, mock_logger):
        """Test del logging de respuestas exitosas."""
        request = self.factory.get('/test/')
        request.user = self.user
        
        # Configurar respuesta exitosa
        success_response = HttpResponse(status=200)
        self.get_response.return_value = success_response
        
        self.middleware(request)
        
        # No debería registrar warnings para respuestas exitosas
        mock_logger.warning.assert_not_called()
    
    def test_process_view_returns_none(self):
        """Test que process_view retorna None."""
        request = self.factory.get('/test/')
        view_func = Mock()
        view_args = ()
        view_kwargs = {}
        
        result = self.middleware.process_view(request, view_func, view_args, view_kwargs)
        
        self.assertIsNone(result)
    
    @patch('apps.common.middleware.logger')
    def test_process_exception_with_authenticated_user(self, mock_logger):
        """Test del manejo de excepciones con usuario autenticado."""
        request = self.factory.get('/test/')
        request.user = self.user
        exception = Exception("Test error")
        
        result = self.middleware.process_exception(request, exception)
        
        # Verificar que se registró el error
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args[0][0]
        self.assertIn('testuser', call_args)
        self.assertIn('/test/', call_args)
        self.assertIn('Test error', call_args)
        
        # Debería retornar None para continuar el manejo normal
        self.assertIsNone(result)
    
    @patch('apps.common.middleware.logger')
    def test_process_exception_with_anonymous_user(self, mock_logger):
        """Test del manejo de excepciones con usuario anónimo."""
        request = self.factory.get('/test/')
        request.user = AnonymousUser()
        exception = Exception("Test error")
        
        result = self.middleware.process_exception(request, exception)
        
        # No debería registrar errores para usuarios anónimos
        mock_logger.error.assert_not_called()
        self.assertIsNone(result)
    
    def test_log_request_info_without_user_attribute(self):
        """Test del logging cuando request no tiene atributo user."""
        request = self.factory.get('/test/')
        # No asignar request.user
        
        # No debería fallar
        self.middleware._log_request_info(request)
    
    def test_log_response_info_without_user_attribute(self):
        """Test del logging de respuesta cuando request no tiene atributo user."""
        request = self.factory.get('/test/')
        response = HttpResponse(status=400)
        # No asignar request.user
        
        # No debería fallar
        self.middleware._log_response_info(request, response)


class TestSecurityMiddleware(TestCase):
    """Tests para SecurityMiddleware."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        self.factory = RequestFactory()
        self.get_response = Mock(return_value=HttpResponse())
        self.middleware = SecurityMiddleware(self.get_response)
    
    def test_init(self):
        """Test que el middleware se inicializa correctamente."""
        middleware = SecurityMiddleware(self.get_response)
        self.assertEqual(middleware.get_response, self.get_response)
    
    def test_security_headers_added(self):
        """Test que se agregan los headers de seguridad."""
        request = self.factory.get('/test/')
        
        response = self.middleware(request)
        
        # Verificar que se agregaron todos los headers de seguridad
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(response['X-Frame-Options'], 'DENY')
        self.assertEqual(response['X-XSS-Protection'], '1; mode=block')
    
    @patch.object(settings, 'DEBUG', False)
    def test_hsts_header_in_production(self):
        """Test que HSTS se agrega en producción."""
        request = self.factory.get('/test/')
        
        response = self.middleware(request)
        
        # Verificar que se agregó HSTS en producción
        self.assertEqual(
            response['Strict-Transport-Security'], 
            'max-age=31536000; includeSubDomains'
        )
    
    @patch.object(settings, 'DEBUG', True)
    def test_no_hsts_header_in_debug(self):
        """Test que HSTS no se agrega en desarrollo."""
        request = self.factory.get('/test/')
        
        response = self.middleware(request)
        
        # Verificar que no se agregó HSTS en desarrollo
        self.assertNotIn('Strict-Transport-Security', response)
    
    def test_preserves_existing_headers(self):
        """Test que preserva headers existentes en la respuesta."""
        request = self.factory.get('/test/')
        original_response = HttpResponse()
        original_response['Custom-Header'] = 'custom-value'
        self.get_response.return_value = original_response
        
        response = self.middleware(request)
        
        # Verificar que se preservó el header custom y se agregaron los de seguridad
        self.assertEqual(response['Custom-Header'], 'custom-value')
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')


class TestRequestLoggingMiddleware(TestCase):
    """Tests para RequestLoggingMiddleware."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        self.factory = RequestFactory()
        self.get_response = Mock(return_value=HttpResponse())
        self.middleware = RequestLoggingMiddleware(self.get_response)
    
    def test_init(self):
        """Test que el middleware se inicializa correctamente."""
        middleware = RequestLoggingMiddleware(self.get_response)
        self.assertEqual(middleware.get_response, self.get_response)
    
    @patch('apps.common.middleware.logger')
    @patch.object(settings, 'DEBUG', True)
    def test_logging_in_debug_mode(self, mock_logger):
        """Test del logging en modo debug."""
        request = self.factory.get('/test/')
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        request.META['HTTP_USER_AGENT'] = 'Test-Agent'
        
        self.middleware(request)
        
        # Verificar que se registraron la solicitud y respuesta
        self.assertEqual(mock_logger.debug.call_count, 2)
        
        # Verificar contenido del primer log (solicitud)
        first_call = mock_logger.debug.call_args_list[0][0][0]
        self.assertIn('GET', first_call)
        self.assertIn('/test/', first_call)
        self.assertIn('127.0.0.1', first_call)
        self.assertIn('Test-Agent', first_call)
        
        # Verificar contenido del segundo log (respuesta)
        second_call = mock_logger.debug.call_args_list[1][0][0]
        self.assertIn('200', second_call)
        self.assertIn('GET', second_call)
        self.assertIn('/test/', second_call)
    
    @patch('apps.common.middleware.logger')
    @patch.object(settings, 'DEBUG', False)
    def test_no_logging_in_production(self, mock_logger):
        """Test que no se registra en producción."""
        request = self.factory.get('/test/')
        
        self.middleware(request)
        
        # No debería registrar en producción
        mock_logger.debug.assert_not_called()
    
    @patch('apps.common.middleware.logger')
    @patch.object(settings, 'DEBUG', True)
    def test_logging_with_missing_meta_fields(self, mock_logger):
        """Test del logging cuando faltan campos META."""
        request = self.factory.get('/test/')
        # No configurar REMOTE_ADDR ni HTTP_USER_AGENT
        
        self.middleware(request)
        
        # Verificar que se registró con valores 'unknown'
        first_call = mock_logger.debug.call_args_list[0][0][0]
        self.assertIn('unknown', first_call)
    
    @patch('apps.common.middleware.logger')
    @patch.object(settings, 'DEBUG', True)
    def test_logging_different_http_methods(self, mock_logger):
        """Test del logging con diferentes métodos HTTP."""
        methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
        
        for method in methods:
            mock_logger.reset_mock()
            request = getattr(self.factory, method.lower())('/test/')
            
            self.middleware(request)
            
            # Verificar que se registró el método correcto
            first_call = mock_logger.debug.call_args_list[0][0][0]
            self.assertIn(method, first_call)
    
    @patch('apps.common.middleware.logger')
    @patch.object(settings, 'DEBUG', True)
    def test_logging_different_status_codes(self, mock_logger):
        """Test del logging con diferentes códigos de estado."""
        status_codes = [200, 201, 400, 404, 500]
        
        for status_code in status_codes:
            mock_logger.reset_mock()
            request = self.factory.get('/test/')
            self.get_response.return_value = HttpResponse(status=status_code)
            
            self.middleware(request)
            
            # Verificar que se registró el código de estado correcto
            second_call = mock_logger.debug.call_args_list[1][0][0]
            self.assertIn(str(status_code), second_call)


@pytest.mark.django_db
class TestMiddlewareIntegration(TestCase):
    """Tests de integración entre middlewares."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        self.factory = RequestFactory()
        
        # Crear usuario de prueba
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='password123',
            role='profesor'
        )
    
    def test_middleware_chain(self):
        """Test que los middlewares funcionan en cadena."""
        def get_response(request):
            return HttpResponse("Test response")
        
        # Crear cadena de middlewares
        security_middleware = SecurityMiddleware(get_response)
        role_middleware = RoleMiddleware(security_middleware)
        logging_middleware = RequestLoggingMiddleware(role_middleware)
        
        request = self.factory.get('/test/')
        request.user = self.user
        
        with patch('apps.common.middleware.logger'):
            response = logging_middleware(request)
        
        # Verificar que la respuesta tiene headers de seguridad
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(response['X-Frame-Options'], 'DENY')
        self.assertEqual(response['X-XSS-Protection'], '1; mode=block')
        
        # Verificar que la respuesta contiene el contenido original
        self.assertEqual(response.content, b"Test response")
    
    @patch('apps.common.middleware.logger')
    def test_exception_handling_in_chain(self, mock_logger):
        """Test del manejo de excepciones usando process_exception."""
        role_middleware = RoleMiddleware(lambda r: HttpResponse())
        request = self.factory.get('/test/')
        request.user = self.user
        exception = Exception("Test exception")
        
        # Llamar directamente a process_exception
        result = role_middleware.process_exception(request, exception)
        
        # Verificar que se registró la excepción
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args[0][0]
        self.assertIn('testuser', call_args)
        self.assertIn('/test/', call_args)
        self.assertIn('Test exception', call_args)
        
        # Debería retornar None
        self.assertIsNone(result) 