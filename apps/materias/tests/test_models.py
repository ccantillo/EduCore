"""
Tests para modelos de la app materias.
"""

import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from datetime import date, timedelta
from apps.users.models import User
from apps.materias.models import Materia, Prerrequisito, Periodo


@pytest.mark.django_db
class TestMateriaModel(TestCase):
    """Tests para el modelo Materia."""
    
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
        
        self.materia_data = {
            'codigo': 'MAT101',
            'nombre': 'Matemáticas Básicas',
            'descripcion': 'Curso introductorio de matemáticas',
            'creditos': 3,
            'profesor': self.profesor
        }
    
    def test_create_materia_basic(self):
        """Test de creación básica de materia."""
        materia = Materia.objects.create(**self.materia_data)
        
        self.assertEqual(materia.codigo, 'MAT101')
        self.assertEqual(materia.nombre, 'Matemáticas Básicas')
        self.assertEqual(materia.creditos, 3)
        self.assertEqual(materia.profesor, self.profesor)
        self.assertEqual(materia.estado, 'activa')  # Estado por defecto
    
    def test_materia_string_representation(self):
        """Test de la representación en string de la materia."""
        materia = Materia.objects.create(**self.materia_data)
        expected = f"{materia.codigo} - {materia.nombre}"
        self.assertEqual(str(materia), expected)
    
    def test_unique_codigo_constraint(self):
        """Test que verifica la restricción de código único."""
        Materia.objects.create(**self.materia_data)
        
        # Intentar crear otra materia con el mismo código
        with self.assertRaises(IntegrityError):
            Materia.objects.create(
                codigo='MAT101',  # Mismo código
                nombre='Otra Materia',
                creditos=2,
                profesor=self.profesor
            )
    
    def test_creditos_validation(self):
        """Test de validación de créditos (1-10)."""
        # Créditos válidos
        for creditos in [1, 5, 10]:
            materia_data = self.materia_data.copy()
            materia_data['codigo'] = f'MAT{creditos:03d}'
            materia_data['creditos'] = creditos
            materia = Materia(**materia_data)
            materia.full_clean()  # No debería levantar excepción
        
        # Créditos inválidos
        for creditos in [0, 11, -1]:
            materia_data = self.materia_data.copy()
            materia_data['creditos'] = creditos
            materia = Materia(**materia_data)
            with self.assertRaises(ValidationError):
                materia.full_clean()
    
    def test_profesor_role_validation(self):
        """Test que valida que solo usuarios con rol profesor puedan asignarse."""
        # Intentar asignar un estudiante como profesor
        materia_data = self.materia_data.copy()
        materia_data['profesor'] = self.estudiante
        materia = Materia(**materia_data)
        
        with self.assertRaises(ValidationError):
            materia.full_clean()
    
    def test_materia_without_profesor(self):
        """Test de creación de materia sin profesor asignado."""
        materia_data = self.materia_data.copy()
        del materia_data['profesor']
        
        materia = Materia.objects.create(**materia_data)
        self.assertIsNone(materia.profesor)
    
    def test_estudiantes_inscritos_count_property(self):
        """Test de la propiedad estudiantes_inscritos_count."""
        from apps.inscripciones.models import Inscripcion
        from apps.materias.models import Periodo
        
        materia = Materia.objects.create(**self.materia_data)
        
        # Sin inscripciones
        self.assertEqual(materia.estudiantes_inscritos_count, 0)
        
        # Crear período activo
        periodo = Periodo.objects.create(
            nombre='2024-1',
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=120),
            estado='en_curso'
        )
        
        # Crear inscripción activa
        Inscripcion.objects.create(
            estudiante=self.estudiante,
            materia=materia,
            periodo=periodo,
            estado='activa'
        )
        
        self.assertEqual(materia.estudiantes_inscritos_count, 1)


@pytest.mark.django_db
class TestPrerrequisito(TestCase):
    """Tests para el modelo Prerrequisito."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        self.profesor = User.objects.create_user(
            username='profesor1',
            email='prof1@test.com',
            password='password123',
            role='profesor'
        )
        
        # Crear materias para prerrequisitos
        self.matematicas_basicas = Materia.objects.create(
            codigo='MAT101',
            nombre='Matemáticas Básicas',
            creditos=3,
            profesor=self.profesor
        )
        
        self.calculo_1 = Materia.objects.create(
            codigo='MAT201',
            nombre='Cálculo I',
            creditos=4,
            profesor=self.profesor
        )
        
        self.calculo_2 = Materia.objects.create(
            codigo='MAT301',
            nombre='Cálculo II',
            creditos=4,
            profesor=self.profesor
        )
    
    def test_create_prerrequisito_basic(self):
        """Test de creación básica de prerrequisito."""
        prereq = Prerrequisito.objects.create(
            materia=self.calculo_1,
            prerrequisito=self.matematicas_basicas,
            tipo='obligatorio'
        )
        
        self.assertEqual(prereq.materia, self.calculo_1)
        self.assertEqual(prereq.prerrequisito, self.matematicas_basicas)
        self.assertEqual(prereq.tipo, 'obligatorio')
    
    def test_prerrequisito_string_representation(self):
        """Test de la representación en string del prerrequisito."""
        prereq = Prerrequisito.objects.create(
            materia=self.calculo_1,
            prerrequisito=self.matematicas_basicas
        )
        
        expected = f"{self.calculo_1.codigo} requiere {self.matematicas_basicas.codigo}"
        self.assertEqual(str(prereq), expected)
    
    def test_self_prerequisite_validation(self):
        """Test que valida que una materia no puede ser prerrequisito de sí misma."""
        prereq = Prerrequisito(
            materia=self.calculo_1,
            prerrequisito=self.calculo_1  # Mismo materia
        )
        
        with self.assertRaises(ValidationError):
            prereq.full_clean()
    
    def test_unique_together_constraint(self):
        """Test de la restricción unique_together."""
        # Crear primer prerrequisito
        Prerrequisito.objects.create(
            materia=self.calculo_1,
            prerrequisito=self.matematicas_basicas
        )
        
        # Intentar crear el mismo prerrequisito
        with self.assertRaises(IntegrityError):
            Prerrequisito.objects.create(
                materia=self.calculo_1,
                prerrequisito=self.matematicas_basicas
            )
    
    def test_circular_dependency_prevention(self):
        """Test de prevención de dependencias circulares."""
        # Crear prerrequisito: Cálculo I requiere Matemáticas Básicas
        Prerrequisito.objects.create(
            materia=self.calculo_1,
            prerrequisito=self.matematicas_basicas
        )
        
        # Crear prerrequisito: Cálculo II requiere Cálculo I
        Prerrequisito.objects.create(
            materia=self.calculo_2,
            prerrequisito=self.calculo_1
        )
        
        # Intentar crear dependencia circular: Matemáticas Básicas requiere Cálculo II
        prereq_circular = Prerrequisito(
            materia=self.matematicas_basicas,
            prerrequisito=self.calculo_2
        )
        
        with self.assertRaises(ValidationError):
            prereq_circular.full_clean()
    
    def test_tipo_choices(self):
        """Test de las opciones del campo tipo."""
        # Tipo obligatorio
        prereq_obligatorio = Prerrequisito.objects.create(
            materia=self.calculo_1,
            prerrequisito=self.matematicas_basicas,
            tipo='obligatorio'
        )
        self.assertEqual(prereq_obligatorio.tipo, 'obligatorio')
        
        # Tipo recomendado
        prereq_recomendado = Prerrequisito.objects.create(
            materia=self.calculo_2,
            prerrequisito=self.matematicas_basicas,
            tipo='recomendado'
        )
        self.assertEqual(prereq_recomendado.tipo, 'recomendado')


@pytest.mark.django_db
class TestPeriodoModel(TestCase):
    """Tests para el modelo Periodo."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        self.periodo_data = {
            'nombre': '2024-1',
            'fecha_inicio': date.today(),
            'fecha_fin': date.today() + timedelta(days=120),
            'estado': 'planificacion'
        }
    
    def test_create_periodo_basic(self):
        """Test de creación básica de período."""
        periodo = Periodo.objects.create(**self.periodo_data)
        
        self.assertEqual(periodo.nombre, '2024-1')
        self.assertEqual(periodo.estado, 'planificacion')
        self.assertIsNotNone(periodo.fecha_inicio)
        self.assertIsNotNone(periodo.fecha_fin)
    
    def test_periodo_string_representation(self):
        """Test de la representación en string del período."""
        periodo = Periodo.objects.create(**self.periodo_data)
        expected = f"{periodo.nombre} ({periodo.get_estado_display()})"
        self.assertEqual(str(periodo), expected)
    
    def test_fecha_validation(self):
        """Test de validación de fechas (inicio < fin)."""
        # Fechas válidas
        periodo_data = self.periodo_data.copy()
        periodo = Periodo(**periodo_data)
        periodo.full_clean()  # No debería levantar excepción
        
        # Fechas inválidas (inicio >= fin)
        periodo_data['fecha_fin'] = periodo_data['fecha_inicio']
        periodo = Periodo(**periodo_data)
        with self.assertRaises(ValidationError):
            periodo.full_clean()
        
        # Fecha inicio posterior a fecha fin
        periodo_data['fecha_fin'] = periodo_data['fecha_inicio'] - timedelta(days=1)
        periodo = Periodo(**periodo_data)
        with self.assertRaises(ValidationError):
            periodo.full_clean()
    
    def test_estado_choices(self):
        """Test de las opciones del campo estado."""
        estados_validos = ['planificacion', 'inscripciones', 'en_curso', 'finalizado']
        
        for estado in estados_validos:
            periodo_data = self.periodo_data.copy()
            periodo_data['estado'] = estado
            periodo_data['nombre'] = f'2024-{estado}'
            
            periodo = Periodo.objects.create(**periodo_data)
            self.assertEqual(periodo.estado, estado)
    
    def test_es_activo_property(self):
        """Test de la propiedad es_activo."""
        # Período en planificación (no activo)
        periodo_planificacion = Periodo.objects.create(
            nombre='2024-Planificacion',
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=120),
            estado='planificacion'
        )
        self.assertFalse(periodo_planificacion.es_activo)
        
        # Período en inscripciones (activo)
        periodo_inscripciones = Periodo.objects.create(
            nombre='2024-Inscripciones',
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=120),
            estado='inscripciones'
        )
        self.assertTrue(periodo_inscripciones.es_activo)
        
        # Período en curso (activo)
        periodo_en_curso = Periodo.objects.create(
            nombre='2024-EnCurso',
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=120),
            estado='en_curso'
        )
        self.assertTrue(periodo_en_curso.es_activo)
        
        # Período finalizado (no activo)
        periodo_finalizado = Periodo.objects.create(
            nombre='2024-Finalizado',
            fecha_inicio=date.today() - timedelta(days=120),
            fecha_fin=date.today() - timedelta(days=1),
            estado='finalizado'
        )
        self.assertFalse(periodo_finalizado.es_activo) 