"""
Tests para modelos de la app inscripciones.
"""

import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from decimal import Decimal
from datetime import date, timedelta
from apps.users.models import User
from apps.materias.models import Materia, Prerrequisito, Periodo
from apps.inscripciones.models import Inscripcion, Calificacion


@pytest.mark.django_db
class TestInscripcionModel(TestCase):
    """Tests para el modelo Inscripcion."""
    
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
        
        self.admin = User.objects.create_user(
            username='admin1',
            email='admin1@test.com',
            password='password123',
            role='admin'
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
        Prerrequisito.objects.create(
            materia=self.calculo,
            prerrequisito=self.matematicas,
            tipo='obligatorio'
        )
    
    def test_create_inscripcion_basic(self):
        """Test de creación básica de inscripción."""
        inscripcion = Inscripcion.objects.create(
            estudiante=self.estudiante,
            materia=self.matematicas,
            periodo=self.periodo
        )
        
        self.assertEqual(inscripcion.estudiante, self.estudiante)
        self.assertEqual(inscripcion.materia, self.matematicas)
        self.assertEqual(inscripcion.periodo, self.periodo)
        self.assertEqual(inscripcion.estado, 'activa')  # Estado por defecto
        self.assertIsNone(inscripcion.nota_final)
    
    def test_inscripcion_string_representation(self):
        """Test de la representación en string de la inscripción."""
        inscripcion = Inscripcion.objects.create(
            estudiante=self.estudiante,
            materia=self.matematicas,
            periodo=self.periodo
        )
        
        expected = f"{self.estudiante.username} - {self.matematicas.codigo} ({self.periodo.nombre})"
        self.assertEqual(str(inscripcion), expected)
    
    def test_unique_together_constraint(self):
        """Test de la restricción unique_together."""
        # Crear primera inscripción
        Inscripcion.objects.create(
            estudiante=self.estudiante,
            materia=self.matematicas,
            periodo=self.periodo
        )
        
        # Intentar crear inscripción duplicada
        with self.assertRaises(ValidationError):
            inscripcion_duplicada = Inscripcion(
                estudiante=self.estudiante,
                materia=self.matematicas,
                periodo=self.periodo
            )
            inscripcion_duplicada.full_clean()
    
    def test_estudiante_role_validation(self):
        """Test que valida que solo usuarios con rol estudiante puedan inscribirse."""
        # Intentar inscribir un profesor
        inscripcion = Inscripcion(
            estudiante=self.profesor,  # Profesor como estudiante
            materia=self.matematicas,
            periodo=self.periodo
        )
        
        with self.assertRaises(ValidationError):
            inscripcion.full_clean()
    
    def test_prerrequisitos_validation_success(self):
        """Test de validación exitosa de prerrequisitos."""
        # Primero inscribir y aprobar prerrequisito
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
            nota=Decimal('3.5'),
            peso=100
        )
        
        # Ahora debería poder inscribirse a Cálculo I
        inscripcion_calculo = Inscripcion(
            estudiante=self.estudiante,
            materia=self.calculo,
            periodo=self.periodo
        )
        
        # No debería levantar excepción
        inscripcion_calculo.full_clean()
    
    def test_prerrequisitos_validation_failure(self):
        """Test de validación fallida de prerrequisitos."""
        # Intentar inscribirse a Cálculo I sin haber aprobado Matemáticas
        inscripcion = Inscripcion(
            estudiante=self.estudiante,
            materia=self.calculo,
            periodo=self.periodo
        )
        
        with self.assertRaises(ValidationError):
            inscripcion.full_clean()
    
    def test_limite_creditos_validation_success(self):
        """Test de validación exitosa de límite de créditos."""
        # Inscribirse a una materia (3 créditos)
        inscripcion = Inscripcion(
            estudiante=self.estudiante,
            materia=self.matematicas,
            periodo=self.periodo
        )
        
        # No debería levantar excepción (dentro del límite)
        inscripcion.full_clean()
    
    def test_limite_creditos_validation_failure(self):
        """Test de validación fallida de límite de créditos."""
        # Crear muchas materias para exceder el límite
        materias = []
        for i in range(10):  # 10 materias de 3 créditos = 30 créditos (> 24)
            materia = Materia.objects.create(
                codigo=f'CRED{100+i}',  # Usar prefijo diferente para evitar colisiones
                nombre=f'Materia Creditos {i}',
                creditos=3,
                profesor=self.profesor
            )
            materias.append(materia)
        
        # Inscribirse a las primeras 8 materias (24 créditos)
        for i in range(8):
            Inscripcion.objects.create(
                estudiante=self.estudiante,
                materia=materias[i],
                periodo=self.periodo
            )
        
        # Intentar inscribirse a la novena materia (excedería el límite)
        inscripcion_exceso = Inscripcion(
            estudiante=self.estudiante,
            materia=materias[8],
            periodo=self.periodo
        )
        
        with self.assertRaises(ValidationError):
            inscripcion_exceso.full_clean()
    
    def test_properties(self):
        """Test de las propiedades del modelo."""
        # Crear inscripción activa
        inscripcion_activa = Inscripcion.objects.create(
            estudiante=self.estudiante,
            materia=self.matematicas,
            periodo=self.periodo,
            estado='activa'
        )
        
        self.assertTrue(inscripcion_activa.activa)
        self.assertFalse(inscripcion_activa.aprobada)
        self.assertFalse(inscripcion_activa.reprobada)
        
        # Cambiar a aprobada
        inscripcion_activa.estado = 'aprobada'
        inscripcion_activa.save()
        
        self.assertFalse(inscripcion_activa.activa)
        self.assertTrue(inscripcion_activa.aprobada)
        self.assertFalse(inscripcion_activa.reprobada)
        
        # Cambiar a reprobada
        inscripcion_activa.estado = 'reprobada'
        inscripcion_activa.save()
        
        self.assertFalse(inscripcion_activa.activa)
        self.assertFalse(inscripcion_activa.aprobada)
        self.assertTrue(inscripcion_activa.reprobada)


@pytest.mark.django_db
class TestCalificacionModel(TestCase):
    """Tests para el modelo Calificacion."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        # Crear usuario y profesor
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
        
        # Crear período y materia
        self.periodo = Periodo.objects.create(
            nombre='2024-1',
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=120),
            estado='en_curso'
        )
        
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
    
    def test_create_calificacion_basic(self):
        """Test de creación básica de calificación."""
        calificacion = Calificacion.objects.create(
            inscripcion=self.inscripcion,
            tipo='parcial_1',
            nota=Decimal('4.2'),
            peso=30,
            comentarios='Excelente trabajo'
        )
        
        self.assertEqual(calificacion.inscripcion, self.inscripcion)
        self.assertEqual(calificacion.tipo, 'parcial_1')
        self.assertEqual(calificacion.nota, Decimal('4.2'))
        self.assertEqual(calificacion.peso, 30)
        self.assertEqual(calificacion.comentarios, 'Excelente trabajo')
    
    def test_calificacion_string_representation(self):
        """Test de la representación en string de la calificación."""
        calificacion = Calificacion.objects.create(
            inscripcion=self.inscripcion,
            tipo='final',
            nota=Decimal('3.8'),
            peso=100
        )
        
        expected = f"{self.inscripcion} - Final: 3.8"
        self.assertEqual(str(calificacion), expected)
    
    def test_nota_validation(self):
        """Test de validación de nota (0.0 - 5.0)."""
        # Notas válidas
        for nota in [0.0, 2.5, 5.0]:
            calificacion = Calificacion(
                inscripcion=self.inscripcion,
                tipo='parcial_1',
                nota=Decimal(str(nota)),
                peso=50
            )
            calificacion.full_clean()  # No debería levantar excepción
        
        # Notas inválidas
        for nota in [-0.1, 5.1, 10.0]:
            calificacion = Calificacion(
                inscripcion=self.inscripcion,
                tipo='parcial_2',
                nota=Decimal(str(nota)),
                peso=50
            )
            with self.assertRaises(ValidationError):
                calificacion.full_clean()
    
    def test_peso_validation(self):
        """Test de validación de peso (1-100)."""
        # Pesos válidos
        tipos_validos = ['parcial_1', 'parcial_2', 'final']
        for i, peso in enumerate([1, 50, 100]):
            calificacion = Calificacion(
                inscripcion=self.inscripcion,
                tipo=tipos_validos[i % len(tipos_validos)],
                nota=Decimal('3.0'),
                peso=peso
            )
            calificacion.full_clean()  # No debería levantar excepción
        
        # Pesos inválidos
        for peso in [0, 101, -5]:
            calificacion = Calificacion(
                inscripcion=self.inscripcion,
                tipo='trabajo',  # Usar tipo válido
                nota=Decimal('3.0'),
                peso=peso
            )
            with self.assertRaises(ValidationError):
                calificacion.full_clean()
    
    def test_peso_total_validation(self):
        """Test de validación de peso total no mayor a 100%."""
        # Crear primera calificación con 60%
        Calificacion.objects.create(
            inscripcion=self.inscripcion,
            tipo='parcial_1',
            nota=Decimal('4.0'),
            peso=60
        )
        
        # Crear segunda calificación con 40% (total = 100%)
        calificacion2 = Calificacion(
            inscripcion=self.inscripcion,
            tipo='final',
            nota=Decimal('3.5'),
            peso=40
        )
        calificacion2.full_clean()  # No debería levantar excepción
        calificacion2.save()  # Guardar para que se incluya en el cálculo
        
        # Intentar crear tercera calificación que exceda el 100%
        calificacion3 = Calificacion(
            inscripcion=self.inscripcion,
            tipo='trabajo',
            nota=Decimal('4.5'),
            peso=10  # 60 + 40 + 10 = 110% > 100%
        )
        
        with self.assertRaises(ValidationError):
            calificacion3.full_clean()
    
    def test_unique_together_constraint(self):
        """Test de la restricción unique_together."""
        # Crear primera calificación
        Calificacion.objects.create(
            inscripcion=self.inscripcion,
            tipo='parcial_1',
            nota=Decimal('4.0'),
            peso=50
        )
        
        # Intentar crear otra calificación del mismo tipo
        with self.assertRaises(ValidationError):
            calificacion_duplicada = Calificacion(
                inscripcion=self.inscripcion,
                tipo='parcial_1',  # Mismo tipo
                nota=Decimal('3.0'),
                peso=30
            )
            calificacion_duplicada.full_clean()
    
    def test_nota_final_calculation(self):
        """Test de cálculo automático de nota final."""
        # Crear calificaciones con diferentes pesos
        calificacion1 = Calificacion.objects.create(
            inscripcion=self.inscripcion,
            tipo='parcial_1',
            nota=Decimal('4.0'),
            peso=30
        )
        
        # Verificar que se actualice la nota final
        self.inscripcion.refresh_from_db()
        self.assertEqual(self.inscripcion.nota_final, Decimal('4.00'))
        
        # Agregar segunda calificación
        calificacion2 = Calificacion.objects.create(
            inscripcion=self.inscripcion,
            tipo='parcial_2',
            nota=Decimal('3.0'),
            peso=30
        )
        
        # Verificar promedio ponderado
        self.inscripcion.refresh_from_db()
        expected_nota = (4.0 * 30 + 3.0 * 30) / (30 + 30)  # (120 + 90) / 60 = 3.5
        self.assertEqual(self.inscripcion.nota_final, Decimal('3.50'))
        
        # Agregar calificación final
        calificacion3 = Calificacion.objects.create(
            inscripcion=self.inscripcion,
            tipo='final',
            nota=Decimal('4.5'),
            peso=40
        )
        
        # Verificar promedio final
        self.inscripcion.refresh_from_db()
        expected_nota = (4.0 * 30 + 3.0 * 30 + 4.5 * 40) / (30 + 30 + 40)  # 390 / 100 = 3.9
        self.assertEqual(self.inscripcion.nota_final, Decimal('3.90'))
    
    def test_estado_automatico_segun_nota(self):
        """Test de cambio automático de estado según la nota final."""
        # Crear calificación reprobatoria
        Calificacion.objects.create(
            inscripcion=self.inscripcion,
            tipo='final',
            nota=Decimal('2.5'),  # < 3.0
            peso=100
        )
        
        self.inscripcion.refresh_from_db()
        self.assertEqual(self.inscripcion.estado, 'reprobada')
        self.assertEqual(self.inscripcion.nota_final, Decimal('2.50'))
        
        # Actualizar a nota aprobatoria
        calificacion = Calificacion.objects.get(inscripcion=self.inscripcion)
        calificacion.nota = Decimal('3.5')  # >= 3.0
        calificacion.save()
        
        self.inscripcion.refresh_from_db()
        self.assertEqual(self.inscripcion.estado, 'aprobada')
        self.assertEqual(self.inscripcion.nota_final, Decimal('3.50'))
    
    def test_tipo_choices(self):
        """Test de las opciones del campo tipo."""
        tipos_validos = ['parcial_1', 'parcial_2', 'final', 'trabajo', 'proyecto', 'otro']
        
        for i, tipo in enumerate(tipos_validos):
            calificacion = Calificacion.objects.create(
                inscripcion=self.inscripcion,
                tipo=tipo,
                nota=Decimal('3.0'),
                peso=15  # Para no exceder 100% con múltiples calificaciones
            )
            self.assertEqual(calificacion.tipo, tipo) 