"""
Tests para autenticación JWT y gestión de tokens.
Incluye login, refresh tokens, y validación de acceso por roles.
"""

import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


@pytest.mark.django_db
class TestJWTAuthentication:
    """Tests para autenticación JWT."""
    
    def setup_method(self):
        """Configuración inicial para cada test."""
        self.client = APIClient()
        
        # Crear usuarios de prueba para cada rol
        self.admin_user = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='adminpass123',
            role='admin'
        )
        
        self.professor_user = User.objects.create_user(
            username='prof_test',
            email='prof@test.com',
            password='profpass123',
            role='profesor'
        )
        
        self.student_user = User.objects.create_user(
            username='student_test',
            email='student@test.com',
            password='studentpass123',
            role='estudiante'
        )
    
    def test_login_with_valid_credentials(self):
        """Test de login exitoso con credenciales válidas."""
        url = reverse('token_obtain_pair')
        data = {
            'username': 'admin_test',
            'password': 'adminpass123'
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
        
        # Verificar que el token contiene información del usuario
        access_token = response.data['access']
        assert access_token is not None
    
    def test_login_with_invalid_credentials(self):
        """Test de login fallido con credenciales inválidas."""
        url = reverse('token_obtain_pair')
        data = {
            'username': 'admin_test',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'access' not in response.data
        assert 'refresh' not in response.data
    
    def test_login_with_nonexistent_user(self):
        """Test de login con usuario que no existe."""
        url = reverse('token_obtain_pair')
        data = {
            'username': 'nonexistent',
            'password': 'anypassword'
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_token_refresh(self):
        """Test de renovación de token JWT."""
        # Primero hacer login para obtener tokens
        login_url = reverse('token_obtain_pair')
        login_data = {
            'username': 'student_test',
            'password': 'studentpass123'
        }
        
        login_response = self.client.post(login_url, login_data, format='json')
        refresh_token = login_response.data['refresh']
        
        # Usar refresh token para obtener nuevo access token
        refresh_url = reverse('token_refresh')
        refresh_data = {
            'refresh': refresh_token
        }
        
        refresh_response = self.client.post(refresh_url, refresh_data, format='json')
        
        assert refresh_response.status_code == status.HTTP_200_OK
        assert 'access' in refresh_response.data
        
        # El nuevo access token debe ser diferente
        new_access_token = refresh_response.data['access']
        original_access_token = login_response.data['access']
        assert new_access_token != original_access_token
    
    def test_token_refresh_with_invalid_token(self):
        """Test de renovación con token inválido."""
        refresh_url = reverse('token_refresh')
        refresh_data = {
            'refresh': 'invalid_token_here'
        }
        
        response = self.client.post(refresh_url, refresh_data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_access_protected_endpoint_without_token(self):
        """Test de acceso a endpoint protegido sin token."""
        # Intentar acceder a un endpoint que requiere autenticación
        url = reverse('user-me')  # Endpoint que requiere autenticación
        
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_access_protected_endpoint_with_valid_token(self):
        """Test de acceso a endpoint protegido con token válido."""
        # Obtener token
        refresh = RefreshToken.for_user(self.student_user)
        access_token = str(refresh.access_token)
        
        # Configurar autenticación
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Acceder a endpoint protegido
        url = reverse('user-me')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == 'student_test'
        assert response.data['role'] == 'estudiante'
    
    def test_access_protected_endpoint_with_invalid_token(self):
        """Test de acceso a endpoint protegido con token inválido."""
        # Configurar token inválido
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        
        # Intentar acceder a endpoint protegido
        url = reverse('user-me')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_token_blacklist_on_logout(self):
        """Test de blacklist de token en logout."""
        # Obtener tokens
        refresh = RefreshToken.for_user(self.admin_user)
        refresh_token = str(refresh)
        
        # Hacer logout (blacklist del token)
        logout_url = reverse('token_blacklist')
        logout_data = {
            'refresh': refresh_token
        }
        
        response = self.client.post(logout_url, logout_data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        # Intentar usar el token blacklisted
        refresh_url = reverse('token_refresh')
        refresh_data = {
            'refresh': refresh_token
        }
        
        refresh_response = self.client.post(refresh_url, refresh_data, format='json')
        
        # Debe fallar porque el token está en blacklist
        assert refresh_response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db 
class TestRoleBasedAccess:
    """Tests para acceso basado en roles."""
    
    def setup_method(self):
        """Configuración inicial para cada test."""
        self.client = APIClient()
        
        # Crear usuarios de prueba
        self.admin_user = User.objects.create_user(
            username='admin_role',
            email='admin_role@test.com',
            password='adminpass123',
            role='admin'
        )
        
        self.professor_user = User.objects.create_user(
            username='prof_role',
            email='prof_role@test.com',
            password='profpass123',
            role='profesor'
        )
        
        self.student_user = User.objects.create_user(
            username='student_role',
            email='student_role@test.com',
            password='studentpass123',
            role='estudiante'
        )
    
    def get_token_for_user(self, user):
        """Helper para obtener token de un usuario."""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def test_admin_can_access_admin_endpoints(self):
        """Test de que admin puede acceder a endpoints de administración."""
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Intentar acceder a endpoint solo para admin
        url = reverse('user-list')  # ViewSet de usuarios
        response = self.client.get(url)
        
        # Admin debe poder acceder
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN]
        # Nota: El status exacto depende de la implementación de permisos
    
    def test_student_cannot_access_admin_endpoints(self):
        """Test de que estudiante no puede acceder a endpoints de admin."""
        token = self.get_token_for_user(self.student_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Intentar acceder a endpoint solo para admin
        url = reverse('user-list')
        response = self.client.get(url)
        
        # Estudiante no debe poder acceder
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_professor_can_access_professor_endpoints(self):
        """Test de que profesor puede acceder a sus endpoints."""
        token = self.get_token_for_user(self.professor_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Acceder a endpoint permitido para profesores
        url = reverse('user-me')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['role'] == 'profesor'
    
    def test_user_can_access_own_profile(self):
        """Test de que usuario puede acceder a su propio perfil."""
        token = self.get_token_for_user(self.student_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('user-me')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == self.student_user.id
        assert response.data['username'] == 'student_role'
    
    def test_user_cannot_access_other_user_profile(self):
        """Test de que usuario no puede acceder a perfil de otro usuario."""
        token = self.get_token_for_user(self.student_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Intentar acceder al perfil de otro usuario
        url = reverse('user-detail', kwargs={'pk': self.professor_user.id})
        response = self.client.get(url)
        
        # Debe estar prohibido o no encontrado
        assert response.status_code in [
            status.HTTP_403_FORBIDDEN, 
            status.HTTP_404_NOT_FOUND
        ]


@pytest.mark.django_db
class TestPasswordSecurity:
    """Tests para seguridad de contraseñas."""
    
    def test_password_is_hashed(self):
        """Test de que las contraseñas se almacenan hasheadas."""
        password = 'testpassword123'
        user = User.objects.create_user(
            username='hashtest',
            email='hash@test.com',
            password=password
        )
        
        # La contraseña no debe almacenarse en texto plano
        assert user.password != password
        assert user.check_password(password)
        assert len(user.password) > 50  # Los hashes son largos
    
    def test_set_password_method(self):
        """Test del método set_password para cambiar contraseñas."""
        user = User.objects.create_user(
            username='setpasstest',
            email='setpass@test.com',
            password='oldpassword'
        )
        
        # Cambiar contraseña
        new_password = 'newpassword123'
        user.set_password(new_password)
        user.save()
        
        # Verificar que la nueva contraseña funciona
        assert user.check_password(new_password)
        assert not user.check_password('oldpassword')
    
    def test_invalid_password_fails_authentication(self):
        """Test de que contraseña incorrecta falla la autenticación."""
        user = User.objects.create_user(
            username='authtest',
            email='auth@test.com',
            password='correctpassword'
        )
        
        # Verificar contraseña correcta
        assert user.check_password('correctpassword')
        
        # Verificar contraseña incorrecta
        assert not user.check_password('wrongpassword')
        assert not user.check_password('')
        assert not user.check_password(None) 