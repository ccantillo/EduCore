"""
Tests para decoradores de la app common.
"""

import pytest
import json
from django.test import TestCase, RequestFactory
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import status
from unittest.mock import Mock, patch
from apps.common.decorators import validate_prerequisites, validate_credit_limits
from apps.users.models import User
from apps.materias.models import Materia, Prerrequisito, Periodo
from apps.inscripciones.models import Inscripcion, Calificacion
from decimal import Decimal
from datetime import date, timedelta


@pytest.mark.django_db
class TestValidatePrerequisitesDecorator(TestCase):
    """Tests para el decorador validate_prerequisites."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        self.factory = RequestFactory()
        
        # Crear usuarios
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
        
        # Crear período
        self.periodo = Periodo.objects.create(
            nombre='2024-1',
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=120),
            estado='inscripciones'
        )
        
        # Crear materias
        self.matematicas = Materia.objects.create(
            codigo='MAT101',
            nombre='Matemáticas Básicas',
            creditos=3,
            profesor=self.profesor
        )
        
        self.calculo = Materia.objects.create(
            codigo='MAT201',
            nombre='Cálculo I',
            creditos=4,
            profesor=self.profesor
        )
        
        # Crear prerrequisito
        self.prerrequisito = Prerrequisito.objects.create(
            materia=self.calculo,
            prerrequisito=self.matematicas,
            tipo='obligatorio'
        )
    
    def test_decorator_allows_non_post_requests(self):
        """Test que el decorador permite requests que no son POST."""
        @validate_prerequisites
        def dummy_view(request):
            return JsonResponse({'message': 'success'})
        
        # Test GET request
        request = self.factory.get('/test/')
        response = dummy_view(request)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'{"message": "success"}')
    
    def test_decorator_allows_request_without_required_data(self):
        """Test que el decorador permite requests sin datos necesarios."""
        @validate_prerequisites
        def dummy_view(request):
            return JsonResponse({'message': 'success'})
        
        # POST request sin datos de estudiante y materia
        request = self.factory.post('/test/', {})
        response = dummy_view(request)
        
        self.assertEqual(response.status_code, 200)
    
    def test_decorator_with_invalid_ids(self):
        """Test que el decorador maneja IDs inválidos correctamente."""
        @validate_prerequisites
        def dummy_view(request):
            return JsonResponse({'message': 'success'})
        
        # POST request con IDs que no existen
        request = self.factory.post('/test/', {
            'estudiante_id': 99999,
            'materia_id': 99999
        })
        response = dummy_view(request)
        
        # Debería continuar sin problemas
        self.assertEqual(response.status_code, 200)
    
    def test_decorator_blocks_prerequisites_not_enrolled(self):
        """Test que el decorador bloquea cuando no se ha inscrito al prerrequisito."""
        @validate_prerequisites
        def dummy_view(request):
            return JsonResponse({'message': 'success'})
        
        request = self.factory.post('/test/', {
            'estudiante_id': self.estudiante.id,
            'materia_id': self.calculo.id
        })
        
        response = dummy_view(request)
        
        # Debería devolver error 400
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content.decode())
        self.assertIn('error', response_data)
        self.assertIn('prerrequisito', response_data['error'].lower())
    
    def test_decorator_blocks_prerequisites_not_approved(self):
        """Test que el decorador bloquea cuando no se ha aprobado el prerrequisito."""
        @validate_prerequisites
        def dummy_view(request):
            return JsonResponse({'message': 'success'})
        
        # Crear inscripción al prerrequisito pero sin aprobar
        inscripcion_prereq = Inscripcion.objects.create(
            estudiante=self.estudiante,
            materia=self.matematicas,
            periodo=self.periodo,
            estado='activa'
        )
        
        # Crear calificación reprobatoria
        Calificacion.objects.create(
            inscripcion=inscripcion_prereq,
            tipo='final',
            nota=Decimal('2.5'),  # < 3.0
            peso=100
        )
        
        request = self.factory.post('/test/', {
            'estudiante_id': self.estudiante.id,
            'materia_id': self.calculo.id
        })
        
        response = dummy_view(request)
        
        # Debería devolver error 400
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content.decode())
        self.assertIn('error', response_data)
        self.assertIn('aprobar', response_data['error'].lower())
    
    def test_decorator_allows_when_prerequisites_approved(self):
        """Test que el decorador permite cuando se ha aprobado el prerrequisito."""
        @validate_prerequisites
        def dummy_view(request):
            return JsonResponse({'message': 'success'})
        
        # Crear inscripción al prerrequisito y aprobar
        inscripcion_prereq = Inscripcion.objects.create(
            estudiante=self.estudiante,
            materia=self.matematicas,
            periodo=self.periodo,
            estado='aprobada'
        )
        
        # Crear calificación aprobatoria
        Calificacion.objects.create(
            inscripcion=inscripcion_prereq,
            tipo='final',
            nota=Decimal('3.5'),  # >= 3.0
            peso=100
        )
        
        request = self.factory.post('/test/', {
            'estudiante_id': self.estudiante.id,
            'materia_id': self.calculo.id
        })
        
        response = dummy_view(request)
        
        # Debería permitir continuar
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode())
        self.assertEqual(response_data['message'], 'success')
    
    def test_decorator_with_rest_framework_request(self):
        """Test del decorador con request de DRF."""
        @validate_prerequisites
        def dummy_view(request):
            return Response({'message': 'success'})
        
        # Simular request de DRF
        request = self.factory.post('/test/')
        request.data = {
            'estudiante': self.estudiante.id,
            'materia': self.calculo.id
        }
        
        response = dummy_view(request)
        
        # Sin prerrequisitos aprobados, debería devolver error
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)
    
    def test_decorator_handles_exceptions_gracefully(self):
        """Test que el decorador maneja excepciones sin romper el flujo."""
        @validate_prerequisites
        def dummy_view(request):
            return JsonResponse({'message': 'success'})
        
        with patch('apps.users.models.User.objects.get') as mock_get:
            # Simular excepción en la consulta
            mock_get.side_effect = Exception("Database error")
            
            request = self.factory.post('/test/', {
                'estudiante_id': self.estudiante.id,
                'materia_id': self.calculo.id
            })
            
            response = dummy_view(request)
            
            # Debería continuar a pesar del error
            self.assertEqual(response.status_code, 200)
            response_data = json.loads(response.content.decode())
            self.assertEqual(response_data['message'], 'success')


@pytest.mark.django_db  
class TestValidateCreditLimitsDecorator(TestCase):
    """Tests para el decorador validate_credit_limits."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        self.factory = RequestFactory()
        
        # Crear usuarios
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
        
        # Crear período
        self.periodo = Periodo.objects.create(
            nombre='2024-1',
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=120),
            estado='inscripciones'
        )
        
        # Crear materias
        self.materia_pequeña = Materia.objects.create(
            codigo='MAT101',
            nombre='Materia Pequeña',
            creditos=2,
            profesor=self.profesor
        )
        
        self.materia_grande = Materia.objects.create(
            codigo='MAT301',
            nombre='Materia Grande',
            creditos=25,  # Excede límite típico de 20
            profesor=self.profesor
        )
    
    def test_decorator_allows_non_post_requests(self):
        """Test que el decorador permite requests que no son POST."""
        @validate_credit_limits
        def dummy_view(request):
            return JsonResponse({'message': 'success'})
        
        request = self.factory.get('/test/')
        response = dummy_view(request)
        
        self.assertEqual(response.status_code, 200)
    
    def test_decorator_allows_request_without_required_data(self):
        """Test que el decorador permite requests sin datos necesarios."""
        @validate_credit_limits
        def dummy_view(request):
            return JsonResponse({'message': 'success'})
        
        request = self.factory.post('/test/', {})
        response = dummy_view(request)
        
        self.assertEqual(response.status_code, 200)
    
    def test_decorator_allows_within_credit_limit(self):
        """Test que el decorador permite inscripciones dentro del límite de créditos."""
        @validate_credit_limits
        def dummy_view(request):
            return JsonResponse({'message': 'success'})
        
        request = self.factory.post('/test/', {
            'estudiante_id': self.estudiante.id,
            'materia_id': self.materia_pequeña.id,
            'periodo_id': self.periodo.id
        })
        
        response = dummy_view(request)
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode())
        self.assertEqual(response_data['message'], 'success')
    
    def test_decorator_blocks_when_exceeding_credit_limit(self):
        """Test que el decorador bloquea cuando se excede el límite de créditos."""
        @validate_credit_limits
        def dummy_view(request):
            return JsonResponse({'message': 'success'})
        
        request = self.factory.post('/test/', {
            'estudiante_id': self.estudiante.id,
            'materia_id': self.materia_grande.id,
            'periodo_id': self.periodo.id
        })
        
        response = dummy_view(request)
        
        # Debería devolver error 400
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content.decode())
        self.assertIn('error', response_data)
        self.assertIn('límite', response_data['error'].lower())
    
    def test_decorator_calculates_existing_credits(self):
        """Test que el decorador calcula correctamente los créditos existentes."""
        @validate_credit_limits
        def dummy_view(request):
            return JsonResponse({'message': 'success'})
        
        # Crear varias inscripciones existentes para alcanzar cerca del límite
        for i in range(5):  # 5 materias de 2 créditos = 10 créditos
            materia = Materia.objects.create(
                codigo=f'MAT10{i+50}',  # Usar códigos únicos para evitar conflictos
                nombre=f'Materia {i}',
                creditos=2,
                profesor=self.profesor
            )
            Inscripcion.objects.create(
                estudiante=self.estudiante,
                materia=materia,
                periodo=self.periodo
            )
        
        # Intentar inscribir materia que excedería el límite
        materia_exceso = Materia.objects.create(
            codigo='MAT999',
            nombre='Materia Exceso',
            creditos=15,  # 10 existentes + 15 nuevos = 25 > 20
            profesor=self.profesor
        )
        
        request = self.factory.post('/test/', {
            'estudiante_id': self.estudiante.id,
            'materia_id': materia_exceso.id,
            'periodo_id': self.periodo.id
        })
        
        response = dummy_view(request)
        
        # Debería devolver error 400
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content.decode())
        self.assertIn('error', response_data)
        self.assertIn('límite', response_data['error'].lower())
    
    def test_decorator_with_rest_framework_request(self):
        """Test del decorador con request de DRF."""
        @validate_credit_limits  
        def dummy_view(request):
            return Response({'message': 'success'})
        
        request = self.factory.post('/test/')
        request.data = {
            'estudiante': self.estudiante.id,
            'materia': self.materia_grande.id,
            'periodo': self.periodo.id
        }
        
        response = dummy_view(request)
        
        # Debería devolver error por exceder límite
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)
    
    def test_decorator_handles_exceptions_gracefully(self):
        """Test que el decorador maneja excepciones sin romper el flujo."""
        @validate_credit_limits
        def dummy_view(request):
            return JsonResponse({'message': 'success'})
        
        with patch('apps.users.models.User.objects.get') as mock_get:
            mock_get.side_effect = Exception("Database error")
            
            request = self.factory.post('/test/', {
                'estudiante_id': self.estudiante.id,
                'materia_id': self.materia_pequeña.id
            })
            
            response = dummy_view(request)
            
            # Debería continuar a pesar del error
            self.assertEqual(response.status_code, 200)
            response_data = json.loads(response.content.decode())
            self.assertEqual(response_data['message'], 'success')
    
    def test_decorator_without_periodo_id(self):
        """Test del decorador cuando no se especifica período."""
        @validate_credit_limits
        def dummy_view(request):
            return JsonResponse({'message': 'success'})
        
        # Crear período activo
        self.periodo.activo = True
        self.periodo.save()
        
        with patch('apps.materias.models.Periodo.objects.filter') as mock_filter:
            mock_filter.return_value.first.return_value = self.periodo
            
            request = self.factory.post('/test/', {
                'estudiante_id': self.estudiante.id,
                'materia_id': self.materia_pequeña.id
                # Sin periodo_id
            })
            
            response = dummy_view(request)
            
            # Debería funcionar usando el período activo
            self.assertEqual(response.status_code, 200) 