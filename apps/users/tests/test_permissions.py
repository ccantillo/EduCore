"""
Tests para permissions de la app users.
"""

import pytest
from django.test import TestCase, RequestFactory
from rest_framework.test import APIRequestFactory
from unittest.mock import Mock
from apps.users.models import User
from apps.users.permissions import IsAdminUser, IsAdminOrSelf, IsAdminOrProfesorOrSelf


@pytest.mark.django_db
class TestIsAdminUser(TestCase):
    """Tests para IsAdminUser permission."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        self.factory = APIRequestFactory()
        self.permission = IsAdminUser()
        
        # Crear usuarios de prueba
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='password123',
            role='admin'
        )
        
        self.estudiante = User.objects.create_user(
            username='estudiante',
            email='estudiante@test.com',
            password='password123',
            role='estudiante'
        )
        
        self.profesor = User.objects.create_user(
            username='profesor',
            email='profesor@test.com',
            password='password123',
            role='profesor'
        )
    
    def test_admin_user_has_permission(self):
        """Test que admin tiene permisos."""
        request = self.factory.get('/test/')
        request.user = self.admin
        view = Mock()
        
        result = self.permission.has_permission(request, view)
        
        self.assertTrue(result)
    
    def test_estudiante_no_permission(self):
        """Test que estudiante no tiene permisos."""
        request = self.factory.get('/test/')
        request.user = self.estudiante
        view = Mock()
        
        result = self.permission.has_permission(request, view)
        
        self.assertFalse(result)
    
    def test_profesor_no_permission(self):
        """Test que profesor no tiene permisos."""
        request = self.factory.get('/test/')
        request.user = self.profesor
        view = Mock()
        
        result = self.permission.has_permission(request, view)
        
        self.assertFalse(result)
    
    def test_anonymous_user_no_permission(self):
        """Test que usuario anónimo no tiene permisos."""
        request = self.factory.get('/test/')
        request.user = Mock()
        request.user.is_authenticated = False
        view = Mock()
        
        result = self.permission.has_permission(request, view)
        
        self.assertFalse(result)


@pytest.mark.django_db
class TestIsAdminOrSelf(TestCase):
    """Tests para IsAdminOrSelf permission."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        self.factory = APIRequestFactory()
        self.permission = IsAdminOrSelf()
        
        # Crear usuarios de prueba
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='password123',
            role='admin'
        )
        
        self.estudiante = User.objects.create_user(
            username='estudiante',
            email='estudiante@test.com',
            password='password123',
            role='estudiante'
        )
        
        self.otro_estudiante = User.objects.create_user(
            username='otro_estudiante',
            email='otro@test.com',
            password='password123',
            role='estudiante'
        )
    
    def test_admin_has_permission(self):
        """Test que admin tiene permisos."""
        request = self.factory.get('/test/')
        request.user = self.admin
        view = Mock()
        
        result = self.permission.has_permission(request, view)
        
        self.assertTrue(result)
    
    def test_user_accessing_self_has_permission(self):
        """Test que usuario accediendo a sí mismo tiene permisos."""
        request = self.factory.get('/test/')
        request.user = self.estudiante
        view = Mock()
        view.get_object.return_value = self.estudiante
        
        result = self.permission.has_object_permission(request, view, self.estudiante)
        
        self.assertTrue(result)
    
    def test_user_accessing_other_no_permission(self):
        """Test que usuario accediendo a otro no tiene permisos."""
        request = self.factory.get('/test/')
        request.user = self.estudiante
        view = Mock()
        view.get_object.return_value = self.otro_estudiante
        
        result = self.permission.has_object_permission(request, view, self.otro_estudiante)
        
        self.assertFalse(result)
    
    def test_admin_accessing_other_has_permission(self):
        """Test que admin accediendo a otro usuario tiene permisos."""
        request = self.factory.get('/test/')
        request.user = self.admin
        view = Mock()
        view.get_object.return_value = self.estudiante
        
        result = self.permission.has_object_permission(request, view, self.estudiante)
        
        self.assertTrue(result)
    
    def test_anonymous_user_no_permission(self):
        """Test que usuario anónimo no tiene permisos."""
        request = self.factory.get('/test/')
        request.user = Mock()
        request.user.is_authenticated = False
        view = Mock()
        
        result = self.permission.has_permission(request, view)
        
        self.assertFalse(result)


@pytest.mark.django_db
class TestIsAdminOrProfesorOrSelf(TestCase):
    """Tests para IsAdminOrProfesorOrSelf permission."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        self.factory = APIRequestFactory()
        self.permission = IsAdminOrProfesorOrSelf()
        
        # Crear usuarios de prueba
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='password123',
            role='admin'
        )
        
        self.profesor = User.objects.create_user(
            username='profesor',
            email='profesor@test.com',
            password='password123',
            role='profesor'
        )
        
        self.estudiante = User.objects.create_user(
            username='estudiante',
            email='estudiante@test.com',
            password='password123',
            role='estudiante'
        )
        
        self.otro_estudiante = User.objects.create_user(
            username='otro_estudiante',
            email='otro@test.com',
            password='password123',
            role='estudiante'
        )
    
    def test_admin_has_permission(self):
        """Test que admin tiene permisos."""
        request = self.factory.get('/test/')
        request.user = self.admin
        view = Mock()
        
        result = self.permission.has_permission(request, view)
        
        self.assertTrue(result)
    
    def test_profesor_has_permission(self):
        """Test que profesor tiene permisos."""
        request = self.factory.get('/test/')
        request.user = self.profesor
        view = Mock()
        
        result = self.permission.has_permission(request, view)
        
        self.assertTrue(result)
    
    def test_estudiante_accessing_self_has_permission(self):
        """Test que estudiante accediendo a sí mismo tiene permisos."""
        request = self.factory.get('/test/')
        request.user = self.estudiante
        view = Mock()
        view.get_object.return_value = self.estudiante
        
        result = self.permission.has_object_permission(request, view, self.estudiante)
        
        self.assertTrue(result)
    
    def test_estudiante_accessing_other_no_permission(self):
        """Test que estudiante accediendo a otro no tiene permisos."""
        request = self.factory.get('/test/')
        request.user = self.estudiante
        view = Mock()
        view.get_object.return_value = self.otro_estudiante
        
        result = self.permission.has_object_permission(request, view, self.otro_estudiante)
        
        self.assertFalse(result)
    
    def test_profesor_accessing_other_has_permission(self):
        """Test que profesor accediendo a otro usuario tiene permisos."""
        request = self.factory.get('/test/')
        request.user = self.profesor
        view = Mock()
        view.get_object.return_value = self.estudiante
        
        result = self.permission.has_object_permission(request, view, self.estudiante)
        
        self.assertTrue(result)
    
    def test_admin_accessing_other_has_permission(self):
        """Test que admin accediendo a otro usuario tiene permisos."""
        request = self.factory.get('/test/')
        request.user = self.admin
        view = Mock()
        view.get_object.return_value = self.estudiante
        
        result = self.permission.has_object_permission(request, view, self.estudiante)
        
        self.assertTrue(result)
    
    def test_anonymous_user_no_permission(self):
        """Test que usuario anónimo no tiene permisos."""
        request = self.factory.get('/test/')
        request.user = Mock()
        request.user.is_authenticated = False
        view = Mock()
        
        result = self.permission.has_permission(request, view)
        
        self.assertFalse(result) 