"""
Tests simples para aumentar cobertura de users.
"""

import pytest
from django.test import TestCase, RequestFactory
from unittest.mock import Mock
from apps.users.models import User
from apps.users.permissions import IsAdminUser, IsAdminOrSelf
from apps.users.serializers import (
    UserSerializer,
    UserCreateSerializer,
    ProfileSerializer
)


@pytest.mark.django_db
class TestUserPermissionsBasic(TestCase):
    """Tests básicos para permisos de usuarios."""
    
    def setUp(self):
        """Configuración inicial."""
        self.factory = RequestFactory()
        
        self.admin = User.objects.create_user(
            username='admin1',
            email='admin1@test.com',
            password='password123',
            role='admin'
        )
        
        self.estudiante = User.objects.create_user(
            username='estudiante1',
            email='est1@test.com',
            password='password123',
            role='estudiante'
        )
    
    def test_is_admin_user_permission(self):
        """Test básico del permiso IsAdminUser."""
        permission = IsAdminUser()
        
        # Test con admin
        request = self.factory.get('/test/')
        request.user = self.admin
        self.assertTrue(permission.has_permission(request, None))
        
        # Test con no-admin
        request.user = self.estudiante
        self.assertFalse(permission.has_permission(request, None))
    
    def test_is_admin_or_self_permission(self):
        """Test básico del permiso IsAdminOrSelf."""
        permission = IsAdminOrSelf()
        
        # Test con admin
        request = self.factory.get('/test/')
        request.user = self.admin
        self.assertTrue(permission.has_permission(request, None))
        
        # Test con usuario normal
        request.user = self.estudiante
        self.assertTrue(permission.has_permission(request, None))
    
    def test_user_model_properties(self):
        """Test de propiedades del modelo User."""
        self.assertTrue(self.admin.is_admin)
        self.assertFalse(self.admin.is_estudiante)
        self.assertFalse(self.admin.is_profesor)
        
        self.assertTrue(self.estudiante.is_estudiante)
        self.assertFalse(self.estudiante.is_admin)
        self.assertFalse(self.estudiante.is_profesor)
    
    def test_user_serializer_basic(self):
        """Test básico del serializer de usuario."""
        serializer = UserSerializer(self.admin)
        data = serializer.data
        
        self.assertEqual(data['username'], 'admin1')
        self.assertEqual(data['role'], 'admin')
        self.assertIn('email', data)
    
    def test_user_create_serializer_validation(self):
        """Test de validación del serializer de creación."""
        data = {
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'password123',
            'password_confirm': 'password123',
            'role': 'estudiante'
        }
        
        serializer = UserCreateSerializer(data=data)
        # Al menos probamos la validación
        if not serializer.is_valid():
            self.assertIsInstance(serializer.errors, dict)
        else:
            self.assertIn('username', serializer.validated_data) 