"""
Tests para views de la app users.
"""

import pytest
import json
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch, Mock
from apps.users.models import User, Profile
from datetime import date


@pytest.mark.django_db
class TestAuthViewSet(APITestCase):
    """Tests para AuthViewSet."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        self.client = APIClient()
        self.register_url = '/api/v1/users/auth/register/'
        self.login_url = '/api/v1/users/auth/login/'
        self.logout_url = '/api/v1/users/auth/logout/'
        self.refresh_url = '/api/v1/users/auth/refresh/'
        
        # Crear usuario para tests
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='password123',
            role='estudiante'
        )
    
    def test_register_success(self):
        """Test de registro exitoso."""
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
        
        response = self.client.post(self.register_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        self.assertIn('refresh', response.data['tokens'])
        self.assertIn('access', response.data['tokens'])
        
        # Verificar que el usuario se creó
        new_user = User.objects.get(username='newuser')
        self.assertEqual(new_user.email, 'newuser@test.com')
        self.assertEqual(new_user.role, 'estudiante')
    
    def test_register_invalid_data(self):
        """Test de registro con datos inválidos."""
        data = {
            'username': 'newuser',
            'email': 'invalid-email',
            'password': '123',  # Muy débil
            'password_confirm': '456',  # No coincide
        }
        
        response = self.client.post(self.register_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
    
    def test_login_success(self):
        """Test de login exitoso."""
        data = {
            'username': 'testuser',
            'password': 'password123'
        }
        
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        self.assertIn('refresh', response.data['tokens'])
        self.assertIn('access', response.data['tokens'])
    
    def test_login_invalid_credentials(self):
        """Test de login con credenciales inválidas."""
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
    
    def test_logout_success(self):
        """Test de logout exitoso."""
        # Primero hacer login
        refresh = RefreshToken.for_user(self.user)
        
        data = {
            'refresh_token': str(refresh)
        }
        
        response = self.client.post(self.logout_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
    
    def test_logout_invalid_token(self):
        """Test de logout con token inválido."""
        data = {
            'refresh_token': 'invalid_token'
        }
        
        response = self.client.post(self.logout_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_refresh_token_success(self):
        """Test de refresh token exitoso."""
        refresh = RefreshToken.for_user(self.user)
        
        data = {
            'refresh': str(refresh)
        }
        
        response = self.client.post(self.refresh_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
    
    def test_refresh_token_invalid(self):
        """Test de refresh token inválido."""
        data = {
            'refresh': 'invalid_token'
        }
        
        response = self.client.post(self.refresh_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@pytest.mark.django_db
class TestUserViewSet(APITestCase):
    """Tests para UserViewSet."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        self.client = APIClient()
        
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
        
        # URLs
        self.users_url = '/api/v1/users/users/'
        self.user_detail_url = f'/api/v1/users/users/{self.estudiante.id}/'
        self.change_password_url = f'/api/v1/users/users/{self.estudiante.id}/change_password/'
        self.profile_url = f'/api/v1/users/users/{self.estudiante.id}/profile/'
    
    def test_list_users_admin(self):
        """Test que admin puede listar usuarios."""
        self.client.force_authenticate(user=self.admin)
        
        response = self.client.get(self.users_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 3)
    
    def test_list_users_non_admin(self):
        """Test que no-admin no puede listar usuarios."""
        self.client.force_authenticate(user=self.estudiante)
        
        response = self.client.get(self.users_url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_retrieve_user_self(self):
        """Test que un usuario puede ver su propio perfil."""
        self.client.force_authenticate(user=self.estudiante)
        
        response = self.client.get(self.user_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'estudiante')
    
    def test_retrieve_user_admin(self):
        """Test que admin puede ver cualquier usuario."""
        self.client.force_authenticate(user=self.admin)
        
        response = self.client.get(self.user_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'estudiante')
    
    def test_retrieve_user_other(self):
        """Test que un usuario no puede ver otros perfiles."""
        self.client.force_authenticate(user=self.profesor)
        
        response = self.client.get(self.user_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_user_admin(self):
        """Test que admin puede crear usuarios."""
        self.client.force_authenticate(user=self.admin)
        
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
        
        response = self.client.post(self.users_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], 'newuser')
    
    def test_create_user_non_admin(self):
        """Test que no-admin no puede crear usuarios."""
        self.client.force_authenticate(user=self.estudiante)
        
        data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'ComplexPassword123!',
            'password_confirm': 'ComplexPassword123!',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'estudiante'
        }
        
        response = self.client.post(self.users_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_update_user_self(self):
        """Test que un usuario puede actualizar su propio perfil."""
        self.client.force_authenticate(user=self.estudiante)
        
        data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        
        response = self.client.patch(self.user_detail_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Updated')
    
    def test_update_user_admin(self):
        """Test que admin puede actualizar cualquier usuario."""
        self.client.force_authenticate(user=self.admin)
        
        data = {
            'first_name': 'AdminUpdated',
            'last_name': 'Name'
        }
        
        response = self.client.patch(self.user_detail_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'AdminUpdated')
    
    def test_delete_user_admin(self):
        """Test que admin puede eliminar usuarios."""
        self.client.force_authenticate(user=self.admin)
        
        response = self.client.delete(self.user_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verificar que el usuario se marcó como inactivo
        self.estudiante.refresh_from_db()
        self.assertFalse(self.estudiante.is_active)
    
    def test_delete_user_non_admin(self):
        """Test que no-admin no puede eliminar usuarios."""
        self.client.force_authenticate(user=self.estudiante)
        
        response = self.client.delete(self.user_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_change_password_success(self):
        """Test de cambio de contraseña exitoso."""
        self.client.force_authenticate(user=self.estudiante)
        
        data = {
            'old_password': 'password123',
            'new_password': 'NewPassword123!',
            'new_password_confirm': 'NewPassword123!'
        }
        
        response = self.client.post(self.change_password_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Verificar que la contraseña cambió
        self.estudiante.refresh_from_db()
        self.assertTrue(self.estudiante.check_password('NewPassword123!'))
    
    def test_change_password_wrong_old(self):
        """Test de cambio de contraseña con contraseña actual incorrecta."""
        self.client.force_authenticate(user=self.estudiante)
        
        data = {
            'old_password': 'wrongpassword',
            'new_password': 'NewPassword123!',
            'new_password_confirm': 'NewPassword123!'
        }
        
        response = self.client.post(self.change_password_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_change_password_unauthenticated(self):
        """Test de cambio de contraseña sin autenticación."""
        data = {
            'old_password': 'password123',
            'new_password': 'NewPassword123!',
            'new_password_confirm': 'NewPassword123!'
        }
        
        response = self.client.post(self.change_password_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@pytest.mark.django_db
class TestProfileViewSet(APITestCase):
    """Tests para ProfileViewSet."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        self.client = APIClient()
        
        # Crear usuario y perfil
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
        
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='password123',
            role='admin'
        )
        
        # URLs
        self.profile_url = f'/api/v1/users/profiles/{self.profile.id}/'
    
    def test_get_profile_self(self):
        """Test que un usuario puede ver su propio perfil."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['address'], 'Dirección Original')
        self.assertEqual(response.data['birth_date'], '1990-01-01')
    
    def test_get_profile_admin(self):
        """Test que admin puede ver cualquier perfil."""
        self.client.force_authenticate(user=self.admin)
        
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['address'], 'Dirección Original')
    
    def test_update_profile_self(self):
        """Test que un usuario puede actualizar su propio perfil."""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'address': 'Nueva Dirección',
            'birth_date': '1992-05-15'
        }
        
        response = self.client.put(self.profile_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['address'], 'Nueva Dirección')
        self.assertEqual(response.data['birth_date'], '1992-05-15')
    
    def test_partial_update_profile(self):
        """Test de actualización parcial del perfil."""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'address': 'Solo Nueva Dirección'
        }
        
        response = self.client.patch(self.profile_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['address'], 'Solo Nueva Dirección')
        self.assertEqual(response.data['birth_date'], '1990-01-01')  # No cambió
    
    def test_get_profile_unauthenticated(self):
        """Test de acceso sin autenticación."""
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_get_profile_not_found(self):
        """Test cuando el perfil no existe."""
        user_without_profile = User.objects.create_user(
            username='noprofile',
            email='noprofile@test.com',
            password='password123',
            role='estudiante'
        )
        
        self.client.force_authenticate(user=user_without_profile)
        # Como no tiene profile, usaremos un ID inexistente
        profile_url = f'/api/v1/users/profiles/99999/'
        
        response = self.client.get(profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


@pytest.mark.django_db 
class TestPermissions(APITestCase):
    """Tests para permisos específicos."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        self.client = APIClient()
        
        # Crear usuarios de diferentes roles
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
    
    def test_admin_can_access_all_users(self):
        """Test que admin puede acceder a todos los usuarios."""
        self.client.force_authenticate(user=self.admin)
        
        # Puede ver lista
        response = self.client.get('/api/v1/users/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Puede ver detalles de cualquier usuario
        response = self.client.get(f'/api/v1/users/users/{self.estudiante.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Puede modificar cualquier usuario
        response = self.client.patch(f'/api/v1/users/users/{self.estudiante.id}/', {'first_name': 'Modified'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_profesor_can_access_self_only(self):
        """Test que profesor solo puede acceder a su propio perfil."""
        self.client.force_authenticate(user=self.profesor)
        
        # No puede ver lista
        response = self.client.get('/api/v1/users/users/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Puede ver su propio perfil
        response = self.client.get(f'/api/v1/users/users/{self.profesor.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # No puede ver perfil de otro
        response = self.client.get(f'/api/v1/users/users/{self.estudiante.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_estudiante_can_access_self_only(self):
        """Test que estudiante solo puede acceder a su propio perfil."""
        self.client.force_authenticate(user=self.estudiante)
        
        # No puede ver lista
        response = self.client.get('/api/v1/users/users/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Puede ver su propio perfil
        response = self.client.get(f'/api/v1/users/users/{self.estudiante.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # No puede ver perfil de otro
        response = self.client.get(f'/api/v1/users/users/{self.otro_estudiante.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_unauthenticated_access_denied(self):
        """Test que usuarios no autenticados no pueden acceder."""
        # No puede ver lista
        response = self.client.get('/api/v1/users/users/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # No puede ver detalles
        response = self.client.get(f'/api/v1/users/users/{self.estudiante.id}/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED) 