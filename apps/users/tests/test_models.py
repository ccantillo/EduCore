"""
Tests para los modelos de la app users.
Incluye validaciones de roles, teléfonos y creación de usuarios.
"""

import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.contrib.auth import get_user_model
from apps.users.models import Profile

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    """Tests para el modelo User personalizado."""
    
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
    
    def test_create_superuser(self):
        """Test de creación de superusuario."""
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            role='admin'
        )
        
        assert admin.is_superuser
        assert admin.is_staff
        assert admin.role == 'admin'
    
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
    
    def test_default_role_estudiante(self):
        """Test de que el rol por defecto es 'estudiante'."""
        user = User.objects.create_user(
            username='defaultuser',
            email='default@example.com',
            password='testpass123'
        )
        
        assert user.role == 'estudiante'
    
    def test_phone_validation_valid_formats(self):
        """Test de validación de teléfono con formatos válidos."""
        valid_phones = [
            '3001234567',
            '3001234567',
            '+573001234567',
            '573001234567'
        ]
        
        for i, phone in enumerate(valid_phones):
            user = User.objects.create_user(
                username=f'user_{i}',
                email=f'user{i}@example.com',
                password='testpass123',
                phone=phone
            )
            assert user.phone == phone
            user.delete()
    
    def test_phone_validation_invalid_formats(self):
        """Test de validación de teléfono con formatos inválidos."""
        invalid_phones = [
            '123456',  # Muy corto
            '12345678901234567890',  # Muy largo
            'abc123456',  # Letras
            '+1234567890',  # Código de país incorrecto
        ]
        
        for i, phone in enumerate(invalid_phones):
            with pytest.raises(ValidationError):
                user = User(
                    username=f'invalid_user_{i}',
                    email=f'invalid{i}@example.com',
                    phone=phone
                )
                user.full_clean()
    
    def test_unique_username(self):
        """Test de que el username debe ser único."""
        User.objects.create_user(
            username='duplicate',
            email='first@example.com',
            password='testpass123'
        )
        
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                username='duplicate',
                email='second@example.com',
                password='testpass123'
            )
    
    def test_unique_email(self):
        """Test de que el email debe ser único."""
        User.objects.create_user(
            username='first',
            email='duplicate@example.com',
            password='testpass123'
        )
        
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                username='second',
                email='duplicate@example.com',
                password='testpass123'
            )
    
    def test_user_str_representation(self):
        """Test de la representación en string del usuario."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        expected = 'testuser'  # AbstractUser usa username por defecto
        assert str(user) == expected
    
    def test_user_timestamps(self):
        """Test de que los timestamps se crean automáticamente."""
        user = User.objects.create_user(
            username='timestamptest',
            email='timestamp@example.com',
            password='testpass123'
        )
        
        assert user.created_at is not None
        assert user.updated_at is not None
        assert user.created_at <= user.updated_at


@pytest.mark.django_db
class TestProfileModel:
    """Tests para el modelo Profile."""
    
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
            identification='0987654321',
            max_credits_per_semester=20,
            department='Ingeniería de Sistemas'
        )
        
        assert profile.user == user
        assert profile.department == 'Ingeniería de Sistemas'
        assert profile.max_credits_per_semester == 20
    
    def test_profile_one_to_one_relationship(self):
        """Test de que Profile tiene relación uno a uno con User."""
        user = User.objects.create_user(
            username='onetoone',
            email='onetoone@example.com',
            password='testpass123'
        )
        
        Profile.objects.create(
            user=user,
            identification='5555555555'
        )
        
        # Intentar crear otro profile para el mismo usuario debe fallar
        with pytest.raises(IntegrityError):
            Profile.objects.create(
                user=user,
                identification='6666666666'
            )
    
    def test_profile_str_representation(self):
        """Test de la representación en string del profile."""
        user = User.objects.create_user(
            username='profiletest',
            email='profile@example.com',
            password='testpass123',
            first_name='Profile',
            last_name='Test'
        )
        
        profile = Profile.objects.create(
            user=user,
            identification='1111111111'
        )
        
        expected = f"Profile Test - {user.role}"
        assert str(profile) == expected 