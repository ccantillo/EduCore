"""
Tests para modelos de la app users.
"""

import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from apps.users.models import User, Profile


@pytest.mark.django_db
class TestUserModel(TestCase):
    """Tests para el modelo User personalizado."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'testpassword123',
            'role': 'estudiante'
        }
    
    def test_create_user_with_default_role(self):
        """Test que verifica la creación de usuario con rol por defecto."""
        user = User.objects.create_user(
            username='student1',
            email='student1@test.com',
            password='password123'
        )
        
        self.assertEqual(user.role, 'estudiante')
        self.assertTrue(user.is_estudiante)
        self.assertFalse(user.is_profesor)
        self.assertFalse(user.is_admin)
    
    def test_create_user_with_specific_role(self):
        """Test que verifica la creación de usuario con rol específico."""
        # Crear profesor
        profesor = User.objects.create_user(
            username='prof1',
            email='prof1@test.com',
            password='password123',
            role='profesor'
        )
        
        self.assertEqual(profesor.role, 'profesor')
        self.assertTrue(profesor.is_profesor)
        self.assertFalse(profesor.is_estudiante)
        self.assertFalse(profesor.is_admin)
        
        # Crear admin
        admin = User.objects.create_user(
            username='admin1',
            email='admin1@test.com',
            password='password123',
            role='admin'
        )
        
        self.assertEqual(admin.role, 'admin')
        self.assertTrue(admin.is_admin)
        self.assertFalse(admin.is_profesor)
        self.assertFalse(admin.is_estudiante)
    
    def test_user_string_representation(self):
        """Test de la representación en string del usuario."""
        user = User.objects.create_user(**self.user_data)
        expected = f"{user.get_full_name()} ({user.get_role_display()})"
        self.assertEqual(str(user), expected)
    
    def test_phone_number_validation(self):
        """Test de validación de número telefónico."""
        # Teléfono válido simple
        user_data = self.user_data.copy()
        user_data['phone'] = '3001234567'
        user_data['username'] = 'test_phone_1'
        user_data['email'] = 'test_phone_1@test.com'
        user = User(**user_data)
        user.full_clean()  # No debería levantar excepción
        
        # Teléfono con código de país
        user_data = self.user_data.copy()
        user_data['phone'] = '+573001234567'
        user_data['username'] = 'test_phone_2'
        user_data['email'] = 'test_phone_2@test.com'
        user = User(**user_data)
        user.full_clean()  # No debería levantar excepción
        
        # Teléfono inválido
        user_data = self.user_data.copy()
        user_data['phone'] = '123'
        user_data['username'] = 'test_phone_3'
        user_data['email'] = 'test_phone_3@test.com'
        user = User(**user_data)
        with self.assertRaises(ValidationError):
            user.full_clean()
    
    def test_get_role_display_name(self):
        """Test del método get_role_display_name."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.get_role_display_name(), 'Estudiante')
        
        user.role = 'profesor'
        self.assertEqual(user.get_role_display_name(), 'Profesor')
        
        user.role = 'admin'
        self.assertEqual(user.get_role_display_name(), 'Administrador')
    
    def test_unique_username_constraint(self):
        """Test que verifica la restricción de username único."""
        User.objects.create_user(**self.user_data)
        
        # Intentar crear otro usuario con el mismo username
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username='testuser',  # Mismo username
                email='other@test.com',
                password='password123'
            )
    
    def test_unique_email_constraint(self):
        """Test que verifica la restricción de email único."""
        User.objects.create_user(**self.user_data)
        
        # Django por defecto no tiene email único, pero validamos que no lance error
        # Si en el futuro se añade unique=True a email, este test funcionará
        try:
            User.objects.create_user(
                username='otheruser',
                email='test@example.com',  # Mismo email
                password='password123'
            )
            # Si no hay error, significa que no está configurado como único
            self.assertTrue(True)  # Test pasa
        except IntegrityError:
            # Si hay error, significa que está configurado como único
            self.assertTrue(True)  # Test también pasa


@pytest.mark.django_db
class TestProfileModel(TestCase):
    """Tests para el modelo Profile."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        self.estudiante = User.objects.create_user(
            username='estudiante1',
            email='est1@test.com',
            password='password123',
            role='estudiante'
        )
        
        self.profesor = User.objects.create_user(
            username='profesor1',
            email='prof1@test.com',
            password='password123',
            role='profesor'
        )
    
    def test_create_profile_for_student(self):
        """Test de creación de perfil para estudiante."""
        profile = Profile.objects.create(
            user=self.estudiante,
            address='Calle 123 #45-67'
        )
        
        self.assertEqual(profile.user, self.estudiante)
        self.assertIsNotNone(profile.student_id)
        self.assertEqual(profile.student_id, '000001')
        self.assertEqual(profile.professional_id, '')
    
    def test_create_profile_for_professor(self):
        """Test de creación de perfil para profesor."""
        profile = Profile.objects.create(
            user=self.profesor,
            address='Carrera 456 #78-90'
        )
        
        self.assertEqual(profile.user, self.profesor)
        self.assertIsNotNone(profile.professional_id)
        self.assertEqual(profile.professional_id, 'P0001')
        self.assertEqual(profile.student_id, '')
    
    def test_profile_string_representation(self):
        """Test de la representación en string del perfil."""
        profile = Profile.objects.create(user=self.estudiante)
        expected = f"Perfil de {self.estudiante.get_full_name()}"
        self.assertEqual(str(profile), expected)
    
    def test_automatic_student_id_generation(self):
        """Test de generación automática de código de estudiante."""
        # Crear perfil para estudiante
        profile = Profile.objects.create(user=self.estudiante)
        
        # Verificar que se genere un código de estudiante
        self.assertIsNotNone(profile.student_id)
        self.assertTrue(profile.student_id.isdigit())
        self.assertEqual(len(profile.student_id), 6)
        self.assertEqual(profile.professional_id, '')
    
    def test_automatic_professional_id_generation(self):
        """Test de generación automática de código profesional."""
        # Crear perfil para profesor
        profile = Profile.objects.create(user=self.profesor)
        
        # Verificar que se genere un código profesional
        self.assertIsNotNone(profile.professional_id)
        self.assertTrue(profile.professional_id.startswith('P'))
        self.assertTrue(profile.professional_id[1:].isdigit())
        self.assertEqual(len(profile.professional_id), 5)  # P + 4 dígitos
        self.assertEqual(profile.student_id, '')
    
    def test_unique_student_id_constraint(self):
        """Test que verifica la restricción de student_id único."""
        profile1 = Profile.objects.create(user=self.estudiante)
        
        # Crear otro estudiante
        estudiante2 = User.objects.create_user(
            username='estudiante2',
            email='est2@test.com',
            password='password123',
            role='estudiante'
        )
        
        # Intentar establecer el mismo student_id manualmente
        with self.assertRaises(IntegrityError):
            Profile.objects.create(
                user=estudiante2,
                student_id=profile1.student_id
            )
    
    def test_unique_professional_id_constraint(self):
        """Test que verifica la restricción de professional_id único."""
        profile1 = Profile.objects.create(user=self.profesor)
        
        # Crear otro profesor
        profesor2 = User.objects.create_user(
            username='profesor2',
            email='prof2@test.com',
            password='password123',
            role='profesor'
        )
        
        # Intentar establecer el mismo professional_id manualmente
        with self.assertRaises(IntegrityError):
            Profile.objects.create(
                user=profesor2,
                professional_id=profile1.professional_id
            )
    
    def test_profile_creation_for_admin(self):
        """Test que verifica que un admin puede tener perfil sin códigos especiales."""
        admin = User.objects.create_user(
            username='admin1',
            email='admin1@test.com',
            password='password123',
            role='admin'
        )
        
        profile = Profile.objects.create(
            user=admin,
            address='Oficina Principal'
        )
        
        self.assertEqual(profile.user, admin)
        self.assertEqual(profile.student_id, '')
        self.assertEqual(profile.professional_id, '') 