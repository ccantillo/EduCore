"""
Tests para serializers de la app materias.
"""

import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from rest_framework.test import APIRequestFactory
from rest_framework import serializers
from datetime import date, timedelta
from apps.users.models import User
from apps.materias.models import Materia, Prerrequisito, Periodo
from apps.materias.serializers import (
    MateriaSerializer,
    MateriaCreateSerializer,
    MateriaListSerializer,
    PrerrequisitoSerializer,
    PeriodoSerializer
)


@pytest.mark.django_db
class TestMateriaSerializer(TestCase):
    """Tests para MateriaSerializer."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        self.profesor = User.objects.create_user(
            username='profesor1',
            email='prof1@test.com',
            password='password123',
            role='profesor'
        )
        
        self.materia = Materia.objects.create(
            codigo='MAT101',
            nombre='Matemáticas Básicas',
            descripcion='Curso introductorio de matemáticas',
            creditos=3,
            profesor=self.profesor
        )
    
    def test_materia_serialization(self):
        """Test de serialización de materia."""
        serializer = MateriaSerializer(self.materia)
        data = serializer.data
        
        self.assertEqual(data['id'], self.materia.id)
        self.assertEqual(data['codigo'], 'MAT101')
        self.assertEqual(data['nombre'], 'Matemáticas Básicas')
        self.assertEqual(data['descripcion'], 'Curso introductorio de matemáticas')
        self.assertEqual(data['creditos'], 3)
        self.assertIn('profesor', data)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
    
    def test_materia_nested_serialization(self):
        """Test de serialización anidada del profesor."""
        serializer = MateriaSerializer(self.materia)
        data = serializer.data
        
        # Verificar que los datos del profesor están presentes
        self.assertIsInstance(data['profesor'], dict)
        self.assertEqual(data['profesor']['username'], 'profesor1')
    
    def test_materia_without_profesor(self):
        """Test de serialización de materia sin profesor."""
        materia_sin_profesor = Materia.objects.create(
            codigo='MAT102',
            nombre='Materia Sin Profesor',
            creditos=2
        )
        
        serializer = MateriaSerializer(materia_sin_profesor)
        data = serializer.data
        
        self.assertIsNone(data['profesor'])
    
    def test_read_only_fields(self):
        """Test que los campos de solo lectura están correctos."""
        serializer = MateriaSerializer()
        read_only_fields = serializer.Meta.read_only_fields
        
        expected_read_only = ['id', 'created_at', 'updated_at', 'estudiantes_inscritos_count']
        for field in expected_read_only:
            self.assertIn(field, read_only_fields)


@pytest.mark.django_db
class TestMateriaCreateSerializer(TestCase):
    """Tests para MateriaCreateSerializer."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        self.profesor = User.objects.create_user(
            username='profesor1',
            email='prof1@test.com',
            password='password123',
            role='profesor'
        )
        
        self.estudiante = User.objects.create_user(
            username='estudiante1',
            email='est1@test.com',
            password='password123',
            role='estudiante'
        )
    
    def test_valid_materia_creation(self):
        """Test de creación válida de materia."""
        data = {
            'codigo': 'MAT101',
            'nombre': 'Matemáticas Básicas',
            'descripcion': 'Curso introductorio',
            'creditos': 3,
            'profesor': self.profesor.id
        }
        
        serializer = MateriaCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        materia = serializer.save()
        
        self.assertEqual(materia.codigo, 'MAT101')
        self.assertEqual(materia.nombre, 'Matemáticas Básicas')
        self.assertEqual(materia.creditos, 3)
        self.assertEqual(materia.profesor, self.profesor)
    
    def test_materia_creation_without_profesor(self):
        """Test de creación de materia sin profesor."""
        data = {
            'codigo': 'MAT102',
            'nombre': 'Materia Sin Profesor',
            'creditos': 2
        }
        
        serializer = MateriaCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        materia = serializer.save()
        
        self.assertEqual(materia.codigo, 'MAT102')
        self.assertIsNone(materia.profesor)
    
    def test_required_fields(self):
        """Test que los campos requeridos fallan cuando no están presentes."""
        data = {}
        
        serializer = MateriaCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        
        required_fields = ['codigo', 'nombre', 'creditos']
        for field in required_fields:
            self.assertIn(field, serializer.errors)
    
    def test_invalid_creditos_range(self):
        """Test con créditos fuera del rango válido."""
        # Créditos demasiado altos
        data = {
            'codigo': 'MAT103',
            'nombre': 'Materia Inválida',
            'creditos': 11  # Mayor que 10
        }
        
        serializer = MateriaCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('creditos', serializer.errors)
        
        # Créditos cero
        data['creditos'] = 0
        serializer = MateriaCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('creditos', serializer.errors)
    
    def test_invalid_profesor_role(self):
        """Test con usuario que no es profesor."""
        data = {
            'codigo': 'MAT104',
            'nombre': 'Materia con Estudiante',
            'creditos': 3,
            'profesor': self.estudiante.id  # Estudiante como profesor
        }
        
        serializer = MateriaCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('profesor', serializer.errors)
    
    def test_duplicate_codigo(self):
        """Test con código duplicado."""
        # Crear primera materia
        Materia.objects.create(
            codigo='MAT105',
            nombre='Primera Materia',
            creditos=3
        )
        
        # Intentar crear segunda con mismo código
        data = {
            'codigo': 'MAT105',  # Código duplicado
            'nombre': 'Segunda Materia',
            'creditos': 2
        }
        
        serializer = MateriaCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('codigo', serializer.errors)


@pytest.mark.django_db
class TestMateriaUpdateSerializer(TestCase):
    """Tests para MateriaUpdateSerializer."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        self.profesor1 = User.objects.create_user(
            username='profesor1',
            email='prof1@test.com',
            password='password123',
            role='profesor'
        )
        
        self.profesor2 = User.objects.create_user(
            username='profesor2',
            email='prof2@test.com',
            password='password123',
            role='profesor'
        )
        
        self.materia = Materia.objects.create(
            codigo='MAT101',
            nombre='Matemáticas Básicas',
            creditos=3,
            profesor=self.profesor1
        )
    
    def test_valid_update(self):
        """Test de actualización válida."""
        data = {
            'nombre': 'Matemáticas Avanzadas',
            'descripcion': 'Curso avanzado de matemáticas',
            'profesor': self.profesor2.id
        }
        
        serializer = MateriaUpdateSerializer(self.materia, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        updated_materia = serializer.save()
        
        self.assertEqual(updated_materia.nombre, 'Matemáticas Avanzadas')
        self.assertEqual(updated_materia.descripcion, 'Curso avanzado de matemáticas')
        self.assertEqual(updated_materia.profesor, self.profesor2)
        # El código no debería haber cambiado
        self.assertEqual(updated_materia.codigo, 'MAT101')
    
    def test_partial_update(self):
        """Test de actualización parcial."""
        data = {
            'descripcion': 'Nueva descripción'
        }
        
        serializer = MateriaUpdateSerializer(self.materia, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        updated_materia = serializer.save()
        
        self.assertEqual(updated_materia.descripcion, 'Nueva descripción')
        # Otros campos no deberían haber cambiado
        self.assertEqual(updated_materia.nombre, 'Matemáticas Básicas')
        self.assertEqual(updated_materia.profesor, self.profesor1)


@pytest.mark.django_db
class TestPrerrequisitosSerializer(TestCase):
    """Tests para PrerrequisitosSerializer."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        self.profesor = User.objects.create_user(
            username='profesor1',
            email='prof1@test.com',
            password='password123',
            role='profesor'
        )
        
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
        
        self.prerrequisito = Prerrequisito.objects.create(
            materia=self.calculo,
            prerrequisito=self.matematicas,
            tipo='obligatorio'
        )
    
    def test_prerrequisito_serialization(self):
        """Test de serialización de prerrequisito."""
        serializer = PrerrequisitosSerializer(self.prerrequisito)
        data = serializer.data
        
        self.assertEqual(data['id'], self.prerrequisito.id)
        self.assertEqual(data['tipo'], 'obligatorio')
        self.assertIn('materia', data)
        self.assertIn('prerrequisito', data)
    
    def test_prerrequisito_nested_serialization(self):
        """Test de serialización anidada."""
        serializer = PrerrequisitosSerializer(self.prerrequisito)
        data = serializer.data
        
        # Verificar que los datos de materias están presentes
        self.assertIsInstance(data['materia'], dict)
        self.assertIsInstance(data['prerrequisito'], dict)
        
        self.assertEqual(data['materia']['codigo'], 'MAT201')
        self.assertEqual(data['prerrequisito']['codigo'], 'MAT101')


@pytest.mark.django_db
class TestPrerrequisitosCreateSerializer(TestCase):
    """Tests para PrerrequisitosCreateSerializer."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        self.profesor = User.objects.create_user(
            username='profesor1',
            email='prof1@test.com',
            password='password123',
            role='profesor'
        )
        
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
    
    def test_valid_prerrequisito_creation(self):
        """Test de creación válida de prerrequisito."""
        data = {
            'materia': self.calculo.id,
            'prerrequisito': self.matematicas.id,
            'tipo': 'obligatorio'
        }
        
        serializer = PrerrequisitosCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        prerrequisito = serializer.save()
        
        self.assertEqual(prerrequisito.materia, self.calculo)
        self.assertEqual(prerrequisito.prerrequisito, self.matematicas)
        self.assertEqual(prerrequisito.tipo, 'obligatorio')
    
    def test_self_prerequisite_validation(self):
        """Test que una materia no puede ser prerrequisito de sí misma."""
        data = {
            'materia': self.calculo.id,
            'prerrequisito': self.calculo.id,  # Misma materia
            'tipo': 'obligatorio'
        }
        
        serializer = PrerrequisitosCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
    
    def test_required_fields(self):
        """Test que los campos requeridos fallan cuando no están presentes."""
        data = {}
        
        serializer = PrerrequisitosCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        
        required_fields = ['materia', 'prerrequisito']
        for field in required_fields:
            self.assertIn(field, serializer.errors)


@pytest.mark.django_db
class TestPeriodoSerializer(TestCase):
    """Tests para PeriodoSerializer."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        self.periodo = Periodo.objects.create(
            nombre='2024-1',
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=120),
            estado='planificacion'
        )
    
    def test_periodo_serialization(self):
        """Test de serialización de período."""
        serializer = PeriodoSerializer(self.periodo)
        data = serializer.data
        
        self.assertEqual(data['id'], self.periodo.id)
        self.assertEqual(data['nombre'], '2024-1')
        self.assertEqual(data['estado'], 'planificacion')
        self.assertIn('fecha_inicio', data)
        self.assertIn('fecha_fin', data)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
    
    def test_read_only_fields(self):
        """Test que los campos de solo lectura están correctos."""
        serializer = PeriodoSerializer()
        read_only_fields = serializer.Meta.read_only_fields
        
        expected_read_only = ['id', 'created_at', 'updated_at']
        for field in expected_read_only:
            self.assertIn(field, read_only_fields)


@pytest.mark.django_db
class TestPeriodoCreateSerializer(TestCase):
    """Tests para PeriodoCreateSerializer."""
    
    def test_valid_periodo_creation(self):
        """Test de creación válida de período."""
        data = {
            'nombre': '2024-2',
            'fecha_inicio': date.today(),
            'fecha_fin': date.today() + timedelta(days=120),
            'estado': 'planificacion'
        }
        
        serializer = PeriodoCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        periodo = serializer.save()
        
        self.assertEqual(periodo.nombre, '2024-2')
        self.assertEqual(periodo.estado, 'planificacion')
    
    def test_required_fields(self):
        """Test que los campos requeridos fallan cuando no están presentes."""
        data = {}
        
        serializer = PeriodoCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        
        required_fields = ['nombre', 'fecha_inicio', 'fecha_fin']
        for field in required_fields:
            self.assertIn(field, serializer.errors)
    
    def test_invalid_date_range(self):
        """Test con rango de fechas inválido."""
        data = {
            'nombre': '2024-3',
            'fecha_inicio': date.today(),
            'fecha_fin': date.today() - timedelta(days=1),  # Fecha fin anterior
            'estado': 'planificacion'
        }
        
        serializer = PeriodoCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)


@pytest.mark.django_db
class TestPeriodoUpdateSerializer(TestCase):
    """Tests para PeriodoUpdateSerializer."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        self.periodo = Periodo.objects.create(
            nombre='2024-1',
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=120),
            estado='planificacion'
        )
    
    def test_valid_update(self):
        """Test de actualización válida."""
        data = {
            'estado': 'inscripciones',
            'fecha_fin': date.today() + timedelta(days=150)
        }
        
        serializer = PeriodoUpdateSerializer(self.periodo, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        updated_periodo = serializer.save()
        
        self.assertEqual(updated_periodo.estado, 'inscripciones')
        self.assertEqual(updated_periodo.fecha_fin, date.today() + timedelta(days=150))
    
    def test_partial_update(self):
        """Test de actualización parcial."""
        data = {
            'estado': 'en_curso'
        }
        
        serializer = PeriodoUpdateSerializer(self.periodo, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        updated_periodo = serializer.save()
        
        self.assertEqual(updated_periodo.estado, 'en_curso')
        # Otros campos no deberían haber cambiado
        self.assertEqual(updated_periodo.nombre, '2024-1') 