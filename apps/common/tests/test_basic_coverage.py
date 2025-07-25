"""
Tests básicos para aumentar cobertura de common.
"""

import pytest
from django.test import TestCase, RequestFactory
from django.http import JsonResponse
from unittest.mock import Mock, patch
from apps.common.decorators import validate_prerequisites, validate_credit_limits
from apps.common.middleware import RoleMiddleware, SecurityMiddleware, RequestLoggingMiddleware
from apps.users.models import User


@pytest.mark.django_db
class TestBasicDecorators(TestCase):
    """Tests básicos para decoradores."""
    
    def setUp(self):
        """Configuración inicial."""
        self.factory = RequestFactory()
    
    def test_validate_prerequisites_non_post(self):
        """Test básico del decorador con GET."""
        @validate_prerequisites
        def dummy_view(request):
            return JsonResponse({'success': True})
        
        request = self.factory.get('/test/')
        response = dummy_view(request)
        self.assertEqual(response.status_code, 200)
    
    def test_validate_credit_limits_non_post(self):
        """Test básico del decorador con GET."""
        @validate_credit_limits
        def dummy_view(request):
            return JsonResponse({'success': True})
        
        request = self.factory.get('/test/')
        response = dummy_view(request)
        self.assertEqual(response.status_code, 200)
    
    def test_validate_prerequisites_no_data(self):
        """Test del decorador sin datos necesarios."""
        @validate_prerequisites
        def dummy_view(request):
            return JsonResponse({'success': True})
        
        request = self.factory.post('/test/', {})
        response = dummy_view(request)
        self.assertEqual(response.status_code, 200)
    
    def test_validate_credit_limits_no_data(self):
        """Test del decorador sin datos necesarios."""
        @validate_credit_limits
        def dummy_view(request):
            return JsonResponse({'success': True})
        
        request = self.factory.post('/test/', {})
        response = dummy_view(request)
        self.assertEqual(response.status_code, 200)


@pytest.mark.django_db
class TestBasicMiddleware(TestCase):
    """Tests básicos para middleware."""
    
    def setUp(self):
        """Configuración inicial."""
        self.factory = RequestFactory()
        self.get_response = Mock(return_value=JsonResponse({'test': 'response'}))
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='password123',
            role='estudiante'
        )
    
    def test_role_middleware_basic(self):
        """Test básico del RoleMiddleware."""
        middleware = RoleMiddleware(self.get_response)
        request = self.factory.get('/test/')
        request.user = self.user
        
        with patch('apps.common.middleware.logger'):
            response = middleware(request)
        
        self.assertIsNotNone(response)
        self.get_response.assert_called_once()
    
    def test_security_middleware_basic(self):
        """Test básico del SecurityMiddleware."""
        middleware = SecurityMiddleware(self.get_response)
        request = self.factory.get('/test/')
        
        response = middleware(request)
        
        # Verificar que se agregaron headers de seguridad
        self.assertIn('X-Content-Type-Options', response)
        self.assertIn('X-Frame-Options', response)
        self.assertIn('X-XSS-Protection', response)
    
    @patch('apps.common.middleware.settings.DEBUG', True)
    def test_request_logging_middleware_debug(self):
        """Test básico del RequestLoggingMiddleware en debug."""
        middleware = RequestLoggingMiddleware(self.get_response)
        request = self.factory.get('/test/')
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        request.META['HTTP_USER_AGENT'] = 'Test-Agent'
        
        with patch('apps.common.middleware.logger'):
            response = middleware(request)
        
        self.assertIsNotNone(response)
    
    @patch('apps.common.middleware.settings.DEBUG', False)
    def test_request_logging_middleware_production(self):
        """Test básico del RequestLoggingMiddleware en producción."""
        middleware = RequestLoggingMiddleware(self.get_response)
        request = self.factory.get('/test/')
        
        with patch('apps.common.middleware.logger'):
            response = middleware(request)
        
        self.assertIsNotNone(response) 