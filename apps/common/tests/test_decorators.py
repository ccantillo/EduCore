"""
Tests para decoradores personalizados.
Incluye validación de prerrequisitos y límites de créditos según los requerimientos académicos.
"""

import pytest
from unittest.mock import Mock, patch
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from rest_framework.response import Response
from rest_framework import status

from apps.common.decorators import validate_prerequisites, validate_credit_limits
from apps.materias.models import Materia, Prerrequisito, Periodo
from apps.inscripciones.models import Inscripcion, Calificacion

User = get_user_model()


@pytest.mark.django_db
class TestValidatePrerequisitesDecorator:
    """Tests para el decorador validate_prerequisites."""
    
    def setup_method(self):
        """Configuración inicial para cada test."""
        self.factory = APIRequestFactory()
        
        # Crear usuarios de prueba
        self.student = User.objects.create_user(
            username='student_prereq',
            email='student@test.com',
            password='testpass123',
            role='estudiante'
        )
        
        self.professor = User.objects.create_user(
            username='prof_prereq',
            email='prof@test.com',
            password='testpass123',
            role='profesor'
        )
        
        # Crear período académico
        self.period = Periodo.objects.create(
            nombre='2024-1',
            fecha_inicio='2024-01-15',
            fecha_fin='2024-05-15',
            activo=True
        )
        
        # Crear materias
        self.materia_base = Materia.objects.create(
            codigo='MAT001',
            nombre='Matemáticas Básicas',
            creditos=3,
            profesor=self.professor
        )
        
        self.materia_avanzada = Materia.objects.create(
            codigo='MAT002',
            nombre='Matemáticas Avanzadas',
            creditos=4,
            profesor=self.professor
        )
        
        # Crear prerrequisito: MAT002 requiere MAT001
        self.prerrequisito = Prerrequisito.objects.create(
            materia_principal=self.materia_avanzada,
            materia_prerequisito=self.materia_base
        )
    
    def create_mock_view(self, response_data=None):
        """Helper para crear vista mock."""
        def mock_view(request, *args, **kwargs):
            return Response(response_data or {'message': 'success'})
        return mock_view
    
    def test_decorator_allows_non_post_requests(self):
        """Test de que el decorador permite requests que no sean POST."""
        @validate_prerequisites
        def test_view(request, *args, **kwargs):
            return Response({'message': 'allowed'})
        
        # Test GET request
        request = self.factory.get('/test/')
        response = test_view(request)
        
        assert response.data['message'] == 'allowed'
    
    def test_decorator_allows_request_without_required_data(self):
        """Test de que el decorador permite requests sin datos requeridos."""
        @validate_prerequisites
        def test_view(request, *args, **kwargs):
            return Response({'message': 'allowed'})
        
        # Request POST sin datos de estudiante o materia
        request = self.factory.post('/test/', {})
        response = test_view(request)
        
        assert response.data['message'] == 'allowed'
    
    def test_decorator_blocks_enrollment_without_prerequisites(self):
        """Test de que el decorador bloquea inscripción sin prerrequisitos."""
        @validate_prerequisites
        def test_view(request, *args, **kwargs):
            return Response({'message': 'enrolled'})
        
        # Intentar inscribirse a materia avanzada sin haber aprobado la básica
        data = {
            'estudiante': self.student.id,
            'materia': self.materia_avanzada.id,
            'periodo': self.period.id
        }
        
        request = self.factory.post('/test/', data)
        request.data = data
        
        response = test_view(request)
        
        # Debe ser bloqueado
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'prerrequisitos' in response.data['error'].lower()
    
    def test_decorator_allows_enrollment_with_completed_prerequisites(self):
        """Test de que el decorador permite inscripción con prerrequisitos completados."""
        # Primero, inscribir y aprobar la materia prerrequisito
        inscripcion_base = Inscripcion.objects.create(
            estudiante=self.student,
            materia=self.materia_base,
            periodo=self.period,
            estado='aprobada'
        )
        
        # Crear calificación aprobatoria
        Calificacion.objects.create(
            inscripcion=inscripcion_base,
            nota=4.0,
            tipo='final',
            fecha='2024-05-10'
        )
        
        @validate_prerequisites
        def test_view(request, *args, **kwargs):
            return Response({'message': 'enrolled'})
        
        # Ahora intentar inscribirse a la materia avanzada
        data = {
            'estudiante': self.student.id,
            'materia': self.materia_avanzada.id,
            'periodo': self.period.id
        }
        
        request = self.factory.post('/test/', data)
        request.data = data
        
        response = test_view(request)
        
        # Debe ser permitido
        assert response.data['message'] == 'enrolled'
    
    def test_decorator_allows_enrollment_in_subject_without_prerequisites(self):
        """Test de que el decorador permite inscripción en materia sin prerrequisitos."""
        @validate_prerequisites
        def test_view(request, *args, **kwargs):
            return Response({'message': 'enrolled'})
        
        # Inscribirse a materia básica (sin prerrequisitos)
        data = {
            'estudiante': self.student.id,
            'materia': self.materia_base.id,
            'periodo': self.period.id
        }
        
        request = self.factory.post('/test/', data)
        request.data = data
        
        response = test_view(request)
        
        # Debe ser permitido
        assert response.data['message'] == 'enrolled'
    
    def test_decorator_handles_nonexistent_user_gracefully(self):
        """Test de que el decorador maneja usuarios no existentes."""
        @validate_prerequisites
        def test_view(request, *args, **kwargs):
            return Response({'message': 'enrolled'})
        
        # Intentar con usuario que no existe
        data = {
            'estudiante': 99999,  # ID que no existe
            'materia': self.materia_base.id,
            'periodo': self.period.id
        }
        
        request = self.factory.post('/test/', data)
        request.data = data
        
        response = test_view(request)
        
        # Debe permitir que la vista maneje el error
        assert response.data['message'] == 'enrolled'
    
    def test_decorator_handles_nonexistent_subject_gracefully(self):
        """Test de que el decorador maneja materias no existentes."""
        @validate_prerequisites
        def test_view(request, *args, **kwargs):
            return Response({'message': 'enrolled'})
        
        # Intentar con materia que no existe
        data = {
            'estudiante': self.student.id,
            'materia': 99999,  # ID que no existe
            'periodo': self.period.id
        }
        
        request = self.factory.post('/test/', data)
        request.data = data
        
        response = test_view(request)
        
        # Debe permitir que la vista maneje el error
        assert response.data['message'] == 'enrolled'


@pytest.mark.django_db
class TestValidateCreditLimitsDecorator:
    """Tests para el decorador validate_credit_limits."""
    
    def setup_method(self):
        """Configuración inicial para cada test."""
        self.factory = APIRequestFactory()
        
        # Crear usuario estudiante con límite de créditos
        self.student = User.objects.create_user(
            username='student_credits',
            email='student@test.com',
            password='testpass123',
            role='estudiante'
        )
        
        # Crear perfil con límite de créditos
        from apps.users.models import Profile
        self.profile = Profile.objects.create(
            user=self.student,
            identification='1234567890',
            max_credits_per_semester=15  # Límite de 15 créditos
        )
        
        self.professor = User.objects.create_user(
            username='prof_credits',
            email='prof@test.com',
            password='testpass123',
            role='profesor'
        )
        
        # Crear período académico
        self.period = Periodo.objects.create(
            nombre='2024-1',
            fecha_inicio='2024-01-15',
            fecha_fin='2024-05-15',
            activo=True
        )
        
        # Crear materias con diferentes créditos
        self.materia_3_creditos = Materia.objects.create(
            codigo='MAT001',
            nombre='Materia 3 Créditos',
            creditos=3,
            profesor=self.professor
        )
        
        self.materia_5_creditos = Materia.objects.create(
            codigo='MAT002',
            nombre='Materia 5 Créditos',
            creditos=5,
            profesor=self.professor
        )
        
        self.materia_10_creditos = Materia.objects.create(
            codigo='MAT003',
            nombre='Materia 10 Créditos',
            creditos=10,
            profesor=self.professor
        )
    
    def test_decorator_allows_enrollment_within_credit_limit(self):
        """Test de que permite inscripción dentro del límite de créditos."""
        @validate_credit_limits
        def test_view(request, *args, **kwargs):
            return Response({'message': 'enrolled'})
        
        # Inscribirse a materia de 3 créditos (dentro del límite de 15)
        data = {
            'estudiante': self.student.id,
            'materia': self.materia_3_creditos.id,
            'periodo': self.period.id
        }
        
        request = self.factory.post('/test/', data)
        request.data = data
        
        response = test_view(request)
        
        assert response.data['message'] == 'enrolled'
    
    def test_decorator_blocks_enrollment_exceeding_credit_limit(self):
        """Test de que bloquea inscripción que excede límite de créditos."""
        # Primero inscribirse a una materia de 10 créditos
        Inscripcion.objects.create(
            estudiante=self.student,
            materia=self.materia_10_creditos,
            periodo=self.period,
            estado='activa'
        )
        
        @validate_credit_limits
        def test_view(request, *args, **kwargs):
            return Response({'message': 'enrolled'})
        
        # Intentar inscribirse a otra materia de 10 créditos (total sería 20, excede 15)
        another_materia = Materia.objects.create(
            codigo='MAT004',
            nombre='Otra Materia 10 Créditos',
            creditos=10,
            profesor=self.professor
        )
        
        data = {
            'estudiante': self.student.id,
            'materia': another_materia.id,
            'periodo': self.period.id
        }
        
        request = self.factory.post('/test/', data)
        request.data = data
        
        response = test_view(request)
        
        # Debe ser bloqueado
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'créditos' in response.data['error'].lower()
    
    def test_decorator_allows_enrollment_at_exact_credit_limit(self):
        """Test de que permite inscripción que alcanza exactamente el límite."""
        # Inscribirse a materia de 10 créditos
        Inscripcion.objects.create(
            estudiante=self.student,
            materia=self.materia_10_creditos,
            periodo=self.period,
            estado='activa'
        )
        
        @validate_credit_limits
        def test_view(request, *args, **kwargs):
            return Response({'message': 'enrolled'})
        
        # Inscribirse a materia de 5 créditos (total sería 15, exacto al límite)
        data = {
            'estudiante': self.student.id,
            'materia': self.materia_5_creditos.id,
            'periodo': self.period.id
        }
        
        request = self.factory.post('/test/', data)
        request.data = data
        
        response = test_view(request)
        
        assert response.data['message'] == 'enrolled'
    
    def test_decorator_ignores_non_active_enrollments(self):
        """Test de que ignora inscripciones no activas para el cálculo."""
        # Crear inscripción retirada (no debe contar para el límite)
        Inscripcion.objects.create(
            estudiante=self.student,
            materia=self.materia_10_creditos,
            periodo=self.period,
            estado='retirada'
        )
        
        @validate_credit_limits
        def test_view(request, *args, **kwargs):
            return Response({'message': 'enrolled'})
        
        # Inscribirse a materia de 10 créditos (debe ser permitido)
        another_materia = Materia.objects.create(
            codigo='MAT005',
            nombre='Nueva Materia 10 Créditos',
            creditos=10,
            profesor=self.professor
        )
        
        data = {
            'estudiante': self.student.id,
            'materia': another_materia.id,
            'periodo': self.period.id
        }
        
        request = self.factory.post('/test/', data)
        request.data = data
        
        response = test_view(request)
        
        assert response.data['message'] == 'enrolled'
    
    def test_decorator_handles_student_without_profile(self):
        """Test de que maneja estudiantes sin perfil creado."""
        # Crear estudiante sin perfil
        student_no_profile = User.objects.create_user(
            username='student_no_profile',
            email='noprofile@test.com',
            password='testpass123',
            role='estudiante'
        )
        
        @validate_credit_limits
        def test_view(request, *args, **kwargs):
            return Response({'message': 'enrolled'})
        
        data = {
            'estudiante': student_no_profile.id,
            'materia': self.materia_3_creditos.id,
            'periodo': self.period.id
        }
        
        request = self.factory.post('/test/', data)
        request.data = data
        
        response = test_view(request)
        
        # Debe permitir que la vista maneje la situación
        assert response.data['message'] == 'enrolled'


@pytest.mark.django_db
class TestDecoratorIntegration:
    """Tests de integración para ambos decoradores juntos."""
    
    def setup_method(self):
        """Configuración inicial para tests de integración."""
        self.factory = APIRequestFactory()
        
        # Crear datos de prueba similares a los anteriores
        self.student = User.objects.create_user(
            username='integration_student',
            email='integration@test.com',
            password='testpass123',
            role='estudiante'
        )
        
        from apps.users.models import Profile
        self.profile = Profile.objects.create(
            user=self.student,
            identification='1234567890',
            max_credits_per_semester=15
        )
        
        self.professor = User.objects.create_user(
            username='integration_prof',
            email='integrationprof@test.com',
            password='testpass123',
            role='profesor'
        )
        
        self.period = Periodo.objects.create(
            nombre='2024-1',
            fecha_inicio='2024-01-15',
            fecha_fin='2024-05-15',
            activo=True
        )
        
        # Crear materias con prerrequisitos y créditos
        self.basic_subject = Materia.objects.create(
            codigo='BASIC001',
            nombre='Materia Básica',
            creditos=8,
            profesor=self.professor
        )
        
        self.advanced_subject = Materia.objects.create(
            codigo='ADV001',
            nombre='Materia Avanzada',
            creditos=10,
            profesor=self.professor
        )
        
        # El avanzado requiere el básico
        Prerrequisito.objects.create(
            materia_principal=self.advanced_subject,
            materia_prerequisito=self.basic_subject
        )
    
    def test_both_decorators_combined_success(self):
        """Test de que ambos decoradores funcionan juntos exitosamente."""
        # Primero aprobar el prerrequisito
        basic_enrollment = Inscripcion.objects.create(
            estudiante=self.student,
            materia=self.basic_subject,
            periodo=self.period,
            estado='aprobada'
        )
        
        Calificacion.objects.create(
            inscripcion=basic_enrollment,
            nota=4.0,
            tipo='final',
            fecha='2024-05-10'
        )
        
        @validate_prerequisites
        @validate_credit_limits
        def test_view(request, *args, **kwargs):
            return Response({'message': 'enrolled successfully'})
        
        # Ahora inscribirse a la materia avanzada (10 créditos, dentro del límite)
        data = {
            'estudiante': self.student.id,
            'materia': self.advanced_subject.id,
            'periodo': self.period.id
        }
        
        request = self.factory.post('/test/', data)
        request.data = data
        
        response = test_view(request)
        
        assert response.data['message'] == 'enrolled successfully'
    
    def test_both_decorators_prerequisite_failure(self):
        """Test de que falla por prerrequisitos incluso con créditos disponibles."""
        @validate_prerequisites
        @validate_credit_limits
        def test_view(request, *args, **kwargs):
            return Response({'message': 'enrolled successfully'})
        
        # Intentar inscribirse sin haber completado prerrequisitos
        data = {
            'estudiante': self.student.id,
            'materia': self.advanced_subject.id,
            'periodo': self.period.id
        }
        
        request = self.factory.post('/test/', data)
        request.data = data
        
        response = test_view(request)
        
        # Debe fallar por prerrequisitos
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'prerrequisitos' in response.data['error'].lower()
    
    def test_both_decorators_credit_limit_failure(self):
        """Test de que falla por límite de créditos incluso con prerrequisitos."""
        # Aprobar prerrequisito
        basic_enrollment = Inscripcion.objects.create(
            estudiante=self.student,
            materia=self.basic_subject,
            periodo=self.period,
            estado='aprobada'
        )
        
        Calificacion.objects.create(
            inscripcion=basic_enrollment,
            nota=4.0,
            tipo='final',
            fecha='2024-05-10'
        )
        
        # Inscribirse a otra materia que consuma casi todos los créditos
        another_subject = Materia.objects.create(
            codigo='OTHER001',
            nombre='Otra Materia',
            creditos=6,
            profesor=self.professor
        )
        
        Inscripcion.objects.create(
            estudiante=self.student,
            materia=another_subject,
            periodo=self.period,
            estado='activa'
        )
        
        @validate_prerequisites
        @validate_credit_limits
        def test_view(request, *args, **kwargs):
            return Response({'message': 'enrolled successfully'})
        
        # Intentar inscribirse a materia avanzada (10 créditos, excedería límite)
        data = {
            'estudiante': self.student.id,
            'materia': self.advanced_subject.id,
            'periodo': self.period.id
        }
        
        request = self.factory.post('/test/', data)
        request.data = data
        
        response = test_view(request)
        
        # Debe fallar por límite de créditos
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'créditos' in response.data['error'].lower() 