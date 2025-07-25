"""
Tests corregidos para los modelos de la app users.
Adaptados para funcionar con la implementación real.
"""

import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.contrib.auth import get_user_model
from apps.users.models import Profile

User = get_user_model()


@pytest.mark.django_db
class TestUserModelFixed:
    """Tests corregidos para el modelo User personalizado."""
    
    def test_create_user_with_valid_data(self):
        """Test de creación de usuario con datos válidos."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='estudiante',
            phone='3001234567'
        )
        
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.role == 'estudiante'
        assert user.phone == '3001234567'
        assert user.check_password('testpass123')
        assert user.is_active
        assert not user.is_staff
    
    def test_user_role_choices(self):
        """Test de opciones válidas para el campo role."""
        valid_roles = ['admin', 'profesor', 'estudiante']
        
        for role in valid_roles:
            user = User.objects.create_user(
                username=f'user_{role}',
                email=f'{role}@example.com',
                password='testpass123',
                role=role
            )
            assert user.role == role
            user.delete()  # Limpiar para evitar conflictos
    
    def test_user_str_representation(self):
        """Test de la representación en string del usuario."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            role='estudiante'
        )
        
        expected = 'Test User (Estudiante)'
        assert str(user) == expected
    
    def test_user_role_properties(self):
        """Test de las propiedades de rol del usuario."""
        admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            role='admin'
        )
        
        assert admin.is_admin
        assert not admin.is_profesor
        assert not admin.is_estudiante
        
        profesor = User.objects.create_user(
            username='profesor',
            email='profesor@example.com',
            password='testpass123',
            role='profesor'
        )
        
        assert not profesor.is_admin
        assert profesor.is_profesor
        assert not profesor.is_estudiante


@pytest.mark.django_db
class TestProfileModelFixed:
    """Tests corregidos para el modelo Profile."""
    
    def test_create_profile_for_student(self):
        """Test de creación de perfil para estudiante."""
        user = User.objects.create_user(
            username='student',
            email='student@example.com',
            password='testpass123',
            role='estudiante'
        )
        
        profile = Profile.objects.create(
            user=user,
            birth_date='1995-01-01',
            address='Calle 123'
        )
        
        assert profile.user == user
        assert profile.birth_date is not None
        assert profile.student_id is not None  # Se genera automáticamente
    
    def test_create_profile_for_professor(self):
        """Test de creación de perfil para profesor."""
        user = User.objects.create_user(
            username='professor',
            email='professor@example.com',
            password='testpass123',
            role='profesor'
        )
        
        profile = Profile.objects.create(
            user=user,
            address='Avenida 456'
        )
        
        assert profile.user == user
        assert profile.professional_id is not None  # Se genera automáticamente
    
    def test_profile_auto_codes_generation(self):
        """Test de generación automática de códigos."""
        # Crear estudiante
        student_user = User.objects.create_user(
            username='student_code',
            email='student@example.com',
            password='testpass123',
            role='estudiante'
        )
        
        student_profile = Profile.objects.create(user=student_user)
        assert student_profile.student_id == "000001"
        
        # Crear profesor
        prof_user = User.objects.create_user(
            username='prof_code',
            email='prof@example.com',
            password='testpass123',
            role='profesor'
        )
        
        prof_profile = Profile.objects.create(user=prof_user)
        assert prof_profile.professional_id == "P0001"
    
    def test_profile_str_representation(self):
        """Test de la representación en string del profile."""
        user = User.objects.create_user(
            username='profiletest',
            email='profile@example.com',
            password='testpass123',
            first_name='Profile',
            last_name='Test'
        )
        
        profile = Profile.objects.create(user=user)
        
        expected = "Perfil de Profile Test"
        assert str(profile) == expected 