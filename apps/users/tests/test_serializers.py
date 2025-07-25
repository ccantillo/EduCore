"""
Tests para serializers de la app users.
"""

import pytest
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from rest_framework.test import APIRequestFactory
from rest_framework import serializers
from unittest.mock import patch, Mock
from apps.users.models import User, Profile
from apps.users.serializers import (
    ProfileSerializer,
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    ProfileUpdateSerializer,
    LoginSerializer,
    ChangePasswordSerializer
)
from datetime import date


@pytest.mark.django_db
class TestProfileSerializer(TestCase):
    """Tests para ProfileSerializer."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='password123',
            role='estudiante'
        )
        self.profile = Profile.objects.create(
            user=self.user,
            birth_date=date(1990, 1, 1),
            address='Calle Test 123'
        )
    
    def test_profile_serialization(self):
        """Test de serialización del perfil."""
        serializer = ProfileSerializer(self.profile)
        data = serializer.data
        
        self.assertIn('birth_date', data)
        self.assertIn('address', data)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
        self.assertEqual(data['address'], 'Calle Test 123')
        self.assertEqual(data['birth_date'], '1990-01-01')
    
    def test_profile_deserialization(self):
        """Test de deserialización del perfil."""
        data = {
            'birth_date': '1992-05-15',
            'address': 'Nueva Dirección 456'
        }
        
        serializer = ProfileSerializer(self.profile, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        updated_profile = serializer.save()
        self.assertEqual(updated_profile.address, 'Nueva Dirección 456')
        self.assertEqual(updated_profile.birth_date, date(1992, 5, 15))
    
    def test_read_only_fields(self):
        """Test que los campos de solo lectura no se pueden actualizar."""
        serializer = ProfileSerializer()
        read_only_fields = serializer.Meta.read_only_fields
        
        expected_read_only = ['student_id', 'professional_id', 'created_at', 'updated_at']
        for field in expected_read_only:
            self.assertIn(field, read_only_fields)


@pytest.mark.django_db
class TestUserSerializer(TestCase):
    """Tests para UserSerializer."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='password123',
            role='estudiante',
            first_name='Test',
            last_name='User',
            phone='3001234567'
        )
        self.profile = Profile.objects.create(
            user=self.user,
            birth_date=date(1990, 1, 1),
            address='Calle Test 123'
        )
    
    def test_user_serialization(self):
        """Test de serialización del usuario."""
        serializer = UserSerializer(self.user)
        data = serializer.data
        
        self.assertEqual(data['username'], 'testuser')
        self.assertEqual(data['email'], 'test@test.com')
        self.assertEqual(data['first_name'], 'Test')
        self.assertEqual(data['last_name'], 'User')
        self.assertEqual(data['role'], 'estudiante')
        self.assertEqual(data['role_display'], 'Estudiante')
        self.assertEqual(data['phone'], '3001234567')
        self.assertIn('profile', data)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
    
    def test_profile_nested_serialization(self):
        """Test de serialización anidada del perfil."""
        serializer = UserSerializer(self.user)
        data = serializer.data
        
        self.assertIsInstance(data['profile'], dict)
        self.assertEqual(data['profile']['address'], 'Calle Test 123')
        self.assertEqual(data['profile']['birth_date'], '1990-01-01')
    
    def test_user_without_profile(self):
        """Test de serialización de usuario sin perfil."""
        user_without_profile = User.objects.create_user(
            username='noprofile',
            email='noprofile@test.com',
            password='password123',
            role='profesor'
        )
        
        serializer = UserSerializer(user_without_profile)
        data = serializer.data
        
        self.assertIsNone(data['profile'])
    
    def test_read_only_fields(self):
        """Test que los campos de solo lectura están correctos."""
        serializer = UserSerializer()
        read_only_fields = serializer.Meta.read_only_fields
        
        expected_read_only = ['id', 'created_at', 'updated_at']
        for field in expected_read_only:
            self.assertIn(field, read_only_fields)


@pytest.mark.django_db
class TestUserCreateSerializer(TestCase):
    """Tests para UserCreateSerializer."""
    
    def test_valid_user_creation(self):
        """Test de creación válida de usuario."""
        data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'ComplexPassword123!',
            'password_confirm': 'ComplexPassword123!',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'estudiante',
            'phone': '3001234567'
        }
        
        serializer = UserCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        user = serializer.save()
        
        # Verificar que el usuario se creó correctamente
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.email, 'newuser@test.com')
        self.assertEqual(user.first_name, 'New')
        self.assertEqual(user.last_name, 'User')
        self.assertEqual(user.role, 'estudiante')
        self.assertEqual(user.phone, '3001234567')
        
        # Verificar que la contraseña se encriptó
        self.assertTrue(user.check_password('ComplexPassword123!'))
        
        # Verificar que se creó el perfil automáticamente
        self.assertTrue(hasattr(user, 'profile'))
        self.assertIsNotNone(user.profile)
    
    def test_password_mismatch(self):
        """Test que falla cuando las contraseñas no coinciden."""
        data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'ComplexPassword123!',
            'password_confirm': 'DifferentPassword123!',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'estudiante'
        }
        
        serializer = UserCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password_confirm', serializer.errors)
        self.assertIn('no coinciden', str(serializer.errors['password_confirm']))
    
    def test_weak_password_validation(self):
        """Test que falla con contraseñas débiles."""
        data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': '123',  # Contraseña muy débil
            'password_confirm': '123',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'estudiante'
        }
        
        serializer = UserCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)
    
    def test_required_fields(self):
        """Test que fallan campos requeridos."""
        data = {
            'username': 'newuser',
            # Faltan password, etc.
        }
        
        serializer = UserCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        
        # Solo verificar los campos que verdaderamente son requeridos
        required_fields = ['password', 'password_confirm']
        for field in required_fields:
            self.assertIn(field, serializer.errors)
    
    def test_duplicate_username(self):
        """Test que falla con username duplicado."""
        # Crear usuario inicial
        User.objects.create_user(
            username='existinguser',
            email='existing@test.com',
            password='password123',
            role='estudiante'
        )
        
        data = {
            'username': 'existinguser',  # Username duplicado
            'email': 'new@test.com',
            'password': 'ComplexPassword123!',
            'password_confirm': 'ComplexPassword123!',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'estudiante'
        }
        
        serializer = UserCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)


@pytest.mark.django_db
class TestUserUpdateSerializer(TestCase):
    """Tests para UserUpdateSerializer."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='password123',
            role='estudiante',
            first_name='Test',
            last_name='User',
            phone='3001234567'
        )
    
    def test_valid_user_update(self):
        """Test de actualización válida de usuario."""
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'phone': '3009998887'
        }
        
        serializer = UserUpdateSerializer(self.user, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        updated_user = serializer.save()
        
        self.assertEqual(updated_user.first_name, 'Updated')
        self.assertEqual(updated_user.last_name, 'Name')
        self.assertEqual(updated_user.phone, '3009998887')
        
        # Verificar que otros campos no cambiaron
        self.assertEqual(updated_user.username, 'testuser')
        self.assertEqual(updated_user.email, 'test@test.com')
        self.assertEqual(updated_user.role, 'estudiante')
    
    def test_partial_update(self):
        """Test de actualización parcial."""
        data = {
            'first_name': 'OnlyFirst'
        }
        
        serializer = UserUpdateSerializer(self.user, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        updated_user = serializer.save()
        
        self.assertEqual(updated_user.first_name, 'OnlyFirst')
        self.assertEqual(updated_user.last_name, 'User')  # No cambió
        self.assertEqual(updated_user.phone, '3001234567')  # No cambió


@pytest.mark.django_db
class TestProfileUpdateSerializer(TestCase):
    """Tests para ProfileUpdateSerializer."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='password123',
            role='estudiante'
        )
        self.profile = Profile.objects.create(
            user=self.user,
            birth_date=date(1990, 1, 1),
            address='Dirección Original'
        )
    
    def test_valid_profile_update(self):
        """Test de actualización válida de perfil."""
        data = {
            'birth_date': '1992-12-25',
            'address': 'Nueva Dirección Actualizada'
        }
        
        serializer = ProfileUpdateSerializer(self.profile, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        updated_profile = serializer.save()
        
        self.assertEqual(updated_profile.birth_date, date(1992, 12, 25))
        self.assertEqual(updated_profile.address, 'Nueva Dirección Actualizada')
    
    def test_partial_profile_update(self):
        """Test de actualización parcial de perfil."""
        data = {
            'address': 'Solo Nueva Dirección'
        }
        
        serializer = ProfileUpdateSerializer(self.profile, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        updated_profile = serializer.save()
        
        self.assertEqual(updated_profile.address, 'Solo Nueva Dirección')
        self.assertEqual(updated_profile.birth_date, date(1990, 1, 1))  # No cambió


@pytest.mark.django_db
class TestLoginSerializer(TestCase):
    """Tests para LoginSerializer."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='password123',
            role='estudiante'
        )
    
    def test_valid_login(self):
        """Test de login válido."""
        data = {
            'username': 'testuser',
            'password': 'password123'
        }
        
        serializer = LoginSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        validated_data = serializer.validated_data
        self.assertIn('user', validated_data)
        self.assertEqual(validated_data['user'], self.user)
    
    def test_invalid_username(self):
        """Test con username inválido."""
        data = {
            'username': 'wronguser',
            'password': 'password123'
        }
        
        serializer = LoginSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
        self.assertIn('Credenciales inválidas', str(serializer.errors))
    
    def test_invalid_password(self):
        """Test con contraseña inválida."""
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        
        serializer = LoginSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
        self.assertIn('Credenciales inválidas', str(serializer.errors))
    
    def test_inactive_user(self):
        """Test con usuario inactivo."""
        self.user.is_active = False
        self.user.save()
        
        data = {
            'username': 'testuser',
            'password': 'password123'
        }
        
        serializer = LoginSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
        # Django's authenticate() returns None for inactive users, so we get generic error
        self.assertIn('Credenciales inválidas', str(serializer.errors))
    
    def test_missing_credentials(self):
        """Test con credenciales faltantes."""
        # Sin username
        data = {
            'password': 'password123'
        }
        serializer = LoginSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)
        
        # Sin password
        data = {
            'username': 'testuser'
        }
        serializer = LoginSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)
        
        # Sin ninguno
        data = {}
        serializer = LoginSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)
        self.assertIn('password', serializer.errors)


@pytest.mark.django_db
class TestChangePasswordSerializer(TestCase):
    """Tests para ChangePasswordSerializer."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='oldpassword123',
            role='estudiante'
        )
    
    def test_valid_password_change(self):
        """Test de cambio de contraseña válido."""
        request = self.factory.post('/change-password/')
        request.user = self.user
        
        data = {
            'old_password': 'oldpassword123',
            'new_password': 'NewComplexPassword123!',
            'new_password_confirm': 'NewComplexPassword123!'
        }
        
        serializer = ChangePasswordSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid())
        
        validated_data = serializer.validated_data
        self.assertEqual(validated_data['old_password'], 'oldpassword123')
        self.assertEqual(validated_data['new_password'], 'NewComplexPassword123!')
    
    def test_incorrect_old_password(self):
        """Test con contraseña actual incorrecta."""
        request = self.factory.post('/change-password/')
        request.user = self.user
        
        data = {
            'old_password': 'wrongoldpassword',
            'new_password': 'NewComplexPassword123!',
            'new_password_confirm': 'NewComplexPassword123!'
        }
        
        serializer = ChangePasswordSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('old_password', serializer.errors)
        self.assertIn('incorrecta', str(serializer.errors['old_password']))
    
    def test_new_password_mismatch(self):
        """Test cuando las nuevas contraseñas no coinciden."""
        request = self.factory.post('/change-password/')
        request.user = self.user
        
        data = {
            'old_password': 'oldpassword123',
            'new_password': 'NewComplexPassword123!',
            'new_password_confirm': 'DifferentPassword123!'
        }
        
        serializer = ChangePasswordSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('new_password_confirm', serializer.errors)
        self.assertIn('no coinciden', str(serializer.errors['new_password_confirm']))
    
    def test_weak_new_password(self):
        """Test con nueva contraseña débil."""
        request = self.factory.post('/change-password/')
        request.user = self.user
        
        data = {
            'old_password': 'oldpassword123',
            'new_password': '123',  # Muy débil
            'new_password_confirm': '123'
        }
        
        serializer = ChangePasswordSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('new_password', serializer.errors)
    
    def test_missing_context(self):
        """Test cuando falta el contexto de request."""
        data = {
            'old_password': 'oldpassword123',
            'new_password': 'NewComplexPassword123!',
            'new_password_confirm': 'NewComplexPassword123!'
        }
        
        serializer = ChangePasswordSerializer(data=data)
        
        # Debería fallar al validar old_password sin context
        with self.assertRaises(Exception):
            serializer.is_valid(raise_exception=True)
    
    def test_required_fields(self):
        """Test que todos los campos son requeridos."""
        request = self.factory.post('/change-password/')
        request.user = self.user
        
        data = {}
        
        serializer = ChangePasswordSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        
        required_fields = ['old_password', 'new_password', 'new_password_confirm']
        for field in required_fields:
            self.assertIn(field, serializer.errors) 