"""
Tests para serializers de la app inscripciones.
"""

import pytest
from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from rest_framework.test import APIRequestFactory
from rest_framework import serializers
from datetime import date, timedelta
from apps.users.models import User
from apps.materias.models import Materia, Prerrequisito, Periodo
from apps.inscripciones.models import Inscripcion, Calificacion
from apps.inscripciones.serializers import (
    InscripcionSerializer,
    InscripcionDetalleSerializer,
    InscripcionListSerializer,
    CalificacionSerializer,
    CalificacionCreateSerializer
)


@pytest.mark.django_db
class TestInscripcionSerializer(TestCase):
    """Tests para InscripcionSerializer."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
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
        
        # Crear materia
        self.materia = Materia.objects.create(
            codigo='MAT101',
            nombre='Matemáticas Básicas',
            creditos=3,
            profesor=self.profesor
        )
        
        # Crear inscripción
        self.inscripcion = Inscripcion.objects.create(
            estudiante=self.estudiante,
            materia=self.materia,
            periodo=self.periodo
        )
    
    def test_inscripcion_serialization(self):
        """Test de serialización de inscripción."""
        serializer = InscripcionSerializer(self.inscripcion)
        data = serializer.data
        
        self.assertEqual(data['id'], self.inscripcion.id)
        self.assertEqual(data['estado'], 'activa')
        self.assertIn('estudiante', data)
        self.assertIn('materia', data)
        self.assertIn('periodo', data)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
    
    def test_inscripcion_nested_serialization(self):
        """Test de serialización anidada."""
        serializer = InscripcionSerializer(self.inscripcion)
        data = serializer.data
        
        # Verificar que los datos anidados están presentes
        self.assertIsInstance(data['estudiante'], dict)
        self.assertIsInstance(data['materia'], dict)
        self.assertIsInstance(data['periodo'], dict)
        
        # Verificar contenido de estudiante
        self.assertEqual(data['estudiante']['username'], 'estudiante1')
        
        # Verificar contenido de materia
        self.assertEqual(data['materia']['codigo'], 'MAT101')
        
        # Verificar contenido de período
        self.assertEqual(data['periodo']['nombre'], '2024-1')
    
    def test_read_only_fields(self):
        """Test que los campos de solo lectura están correctos."""
        serializer = InscripcionSerializer()
        read_only_fields = serializer.Meta.read_only_fields
        
        expected_read_only = ['id', 'created_at', 'updated_at']
        for field in expected_read_only:
            self.assertIn(field, read_only_fields)


@pytest.mark.django_db
class TestInscripcionDetalleSerializer(TestCase):
    """Tests para InscripcionDetalleSerializer."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
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
        
        # Crear materia
        self.materia = Materia.objects.create(
            codigo='MAT101',
            nombre='Matemáticas Básicas',
            creditos=3,
            profesor=self.profesor
        )
        
        # Crear inscripción
        self.inscripcion = Inscripcion.objects.create(
            estudiante=self.estudiante,
            materia=self.materia,
            periodo=self.periodo
        )
    
    def test_inscripcion_detalle_serialization(self):
        """Test de serialización detallada de inscripción."""
        serializer = InscripcionDetalleSerializer(self.inscripcion)
        data = serializer.data
        
        self.assertEqual(data['id'], self.inscripcion.id)
        self.assertEqual(data['estado'], 'activa')
        self.assertIn('aprobada', data)
        self.assertIn('reprobada', data)
        self.assertIn('activa', data)
        self.assertIn('estudiante', data)
        self.assertIn('materia', data)
        self.assertIn('periodo', data)


@pytest.mark.django_db
class TestInscripcionListSerializer(TestCase):
    """Tests para InscripcionListSerializer."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        # Crear usuarios
        self.estudiante = User.objects.create_user(
            username='estudiante1',
            email='est1@test.com',
            password='password123',
            role='estudiante',
            first_name='Test',
            last_name='Student'
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
        
        # Crear materia
        self.materia = Materia.objects.create(
            codigo='MAT101',
            nombre='Matemáticas Básicas',
            creditos=3,
            profesor=self.profesor
        )
        
        # Crear inscripción
        self.inscripcion = Inscripcion.objects.create(
            estudiante=self.estudiante,
            materia=self.materia,
            periodo=self.periodo
        )
    
    def test_inscripcion_list_serialization(self):
        """Test de serialización simplificada para lista."""
        serializer = InscripcionListSerializer(self.inscripcion)
        data = serializer.data
        
        self.assertEqual(data['id'], self.inscripcion.id)
        self.assertEqual(data['estudiante_nombre'], 'Test Student')
        self.assertEqual(data['materia_codigo'], 'MAT101')
        self.assertEqual(data['materia_nombre'], 'Matemáticas Básicas')
        self.assertEqual(data['periodo_nombre'], '2024-1')
        self.assertEqual(data['estado'], 'activa')


@pytest.mark.django_db
class TestCalificacionSerializer(TestCase):
    """Tests para CalificacionSerializer."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
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
            estado='en_curso'
        )
        
        # Crear materia
        self.materia = Materia.objects.create(
            codigo='MAT101',
            nombre='Matemáticas Básicas',
            creditos=3,
            profesor=self.profesor
        )
        
        # Crear inscripción
        self.inscripcion = Inscripcion.objects.create(
            estudiante=self.estudiante,
            materia=self.materia,
            periodo=self.periodo
        )
        
        # Crear calificación
        self.calificacion = Calificacion.objects.create(
            inscripcion=self.inscripcion,
            tipo='parcial_1',
            nota=Decimal('4.2'),
            peso=30,
            comentarios='Excelente trabajo'
        )
    
    def test_calificacion_serialization(self):
        """Test de serialización de calificación."""
        serializer = CalificacionSerializer(self.calificacion)
        data = serializer.data
        
        self.assertEqual(data['id'], self.calificacion.id)
        self.assertEqual(data['tipo'], 'parcial_1')
        self.assertEqual(str(data['nota']), '4.20')
        self.assertEqual(data['peso'], 30)
        self.assertEqual(data['comentarios'], 'Excelente trabajo')
        self.assertIn('inscripcion', data)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
    
    def test_calificacion_nested_serialization(self):
        """Test de serialización anidada."""
        serializer = CalificacionSerializer(self.calificacion)
        data = serializer.data
        
        # Verificar que los datos de inscripción están presentes
        self.assertIsInstance(data['inscripcion'], dict)
        self.assertEqual(data['inscripcion']['id'], self.inscripcion.id)
    
    def test_read_only_fields(self):
        """Test que los campos de solo lectura están correctos."""
        serializer = CalificacionSerializer()
        read_only_fields = serializer.Meta.read_only_fields
        
        expected_read_only = ['id', 'created_at', 'updated_at']
        for field in expected_read_only:
            self.assertIn(field, read_only_fields)


@pytest.mark.django_db
class TestCalificacionCreateSerializer(TestCase):
    """Tests para CalificacionCreateSerializer."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
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
            estado='en_curso'
        )
        
        # Crear materia
        self.materia = Materia.objects.create(
            codigo='MAT101',
            nombre='Matemáticas Básicas',
            creditos=3,
            profesor=self.profesor
        )
        
        # Crear inscripción
        self.inscripcion = Inscripcion.objects.create(
            estudiante=self.estudiante,
            materia=self.materia,
            periodo=self.periodo
        )
    
    def test_valid_calificacion_creation(self):
        """Test de creación válida de calificación."""
        data = {
            'inscripcion': self.inscripcion.id,
            'tipo': 'parcial_1',
            'nota': Decimal('4.2'),
            'peso': 30,
            'comentarios': 'Buen trabajo'
        }
        
        serializer = CalificacionCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        calificacion = serializer.save()
        
        self.assertEqual(calificacion.inscripcion, self.inscripcion)
        self.assertEqual(calificacion.tipo, 'parcial_1')
        self.assertEqual(calificacion.nota, Decimal('4.2'))
        self.assertEqual(calificacion.peso, 30)
        self.assertEqual(calificacion.comentarios, 'Buen trabajo')
    
    def test_required_fields(self):
        """Test que los campos requeridos fallan cuando no están presentes."""
        data = {}
        
        serializer = CalificacionCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        
        required_fields = ['inscripcion', 'tipo', 'nota', 'peso']
        for field in required_fields:
            self.assertIn(field, serializer.errors)
    
    def test_invalid_nota_range(self):
        """Test con nota fuera del rango válido."""
        # Nota muy alta
        data = {
            'inscripcion': self.inscripcion.id,
            'tipo': 'parcial_1',
            'nota': Decimal('6.0'),
            'peso': 30
        }
        
        serializer = CalificacionCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('nota', serializer.errors)
        
        # Nota negativa
        data['nota'] = Decimal('-1.0')
        serializer = CalificacionCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('nota', serializer.errors)
    
    def test_invalid_peso_range(self):
        """Test con peso fuera del rango válido."""
        # Peso demasiado alto
        data = {
            'inscripcion': self.inscripcion.id,
            'tipo': 'parcial_1',
            'nota': Decimal('4.0'),
            'peso': 101
        }
        
        serializer = CalificacionCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('peso', serializer.errors)
        
        # Peso cero
        data['peso'] = 0
        serializer = CalificacionCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('peso', serializer.errors)
    
    def test_invalid_tipo(self):
        """Test con tipo de evaluación inválido."""
        data = {
            'inscripcion': self.inscripcion.id,
            'tipo': 'tipo_inexistente',
            'nota': Decimal('4.0'),
            'peso': 30
        }
        
        serializer = CalificacionCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('tipo', serializer.errors)


 