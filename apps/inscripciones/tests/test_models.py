"""
Tests para los modelos de la app inscripciones.
Incluye validaciones de lógica de negocio académica según los requerimientos.
"""

import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.contrib.auth import get_user_model
from apps.inscripciones.models import Inscripcion, Calificacion
from apps.materias.models import Materia, Periodo, Prerrequisito
from apps.users.models import Profile

User = get_user_model()


@pytest.mark.django_db
class TestInscripcionModel:
    """Tests para el modelo Inscripcion."""
    
    def setup_method(self):
        """Configuración inicial para cada test."""
        # Crear usuarios
        self.student = User.objects.create_user(
            username='student_inscr',
            email='student@test.com',
            password='testpass123',
            role='estudiante'
        )
        
        self.professor = User.objects.create_user(
            username='prof_inscr',
            email='prof@test.com',
            password='testpass123',
            role='profesor'
        )
        
        # Crear perfil de estudiante
        self.profile = Profile.objects.create(
            user=self.student,
            identification='1234567890',
            max_credits_per_semester=18
        )
        
        # Crear período académico
        self.period = Periodo.objects.create(
            nombre='2024-1',
            fecha_inicio='2024-01-15',
            fecha_fin='2024-05-15',
            activo=True
        )
        
        # Crear materia
        self.materia = Materia.objects.create(
            codigo='MAT001',
            nombre='Matemáticas I',
            creditos=4,
            profesor=self.professor
        )
    
    def test_create_valid_inscription(self):
        """Test de creación de inscripción válida."""
        inscripcion = Inscripcion.objects.create(
            estudiante=self.student,
            materia=self.materia,
            periodo=self.period,
            estado='activa'
        )
        
        assert inscripcion.estudiante == self.student
        assert inscripcion.materia == self.materia
        assert inscripcion.periodo == self.period
        assert inscripcion.estado == 'activa'
        assert inscripcion.fecha_inscripcion is not None
    
    def test_inscription_estado_choices(self):
        """Test de opciones válidas para el estado de inscripción."""
        valid_estados = ['activa', 'aprobada', 'reprobada', 'retirada', 'cancelada']
        
        for estado in valid_estados:
            inscripcion = Inscripcion.objects.create(
                estudiante=self.student,
                materia=self.materia,
                periodo=self.period,
                estado=estado
            )
            assert inscripcion.estado == estado
            inscripcion.delete()  # Limpiar para evitar conflictos de unique constraint
    
    def test_inscription_unique_constraint(self):
        """Test de constraint único: estudiante no puede inscribirse dos veces a la misma materia en el mismo período."""
        # Crear primera inscripción
        Inscripcion.objects.create(
            estudiante=self.student,
            materia=self.materia,
            periodo=self.period,
            estado='activa'
        )
        
        # Intentar crear segunda inscripción (debe fallar)
        with pytest.raises(IntegrityError):
            Inscripcion.objects.create(
                estudiante=self.student,
                materia=self.materia,
                periodo=self.period,
                estado='activa'
            )
    
    def test_inscription_can_enroll_same_subject_different_periods(self):
        """Test de que se puede inscribir a la misma materia en períodos diferentes."""
        # Crear segundo período
        period2 = Periodo.objects.create(
            nombre='2024-2',
            fecha_inicio='2024-07-15',
            fecha_fin='2024-11-15',
            activo=False
        )
        
        # Inscribirse en primer período
        inscripcion1 = Inscripcion.objects.create(
            estudiante=self.student,
            materia=self.materia,
            periodo=self.period,
            estado='reprobada'
        )
        
        # Inscribirse en segundo período (debe ser válido)
        inscripcion2 = Inscripcion.objects.create(
            estudiante=self.student,
            materia=self.materia,
            periodo=period2,
            estado='activa'
        )
        
        assert inscripcion1.periodo != inscripcion2.periodo
        assert inscripcion1.materia == inscripcion2.materia
        assert inscripcion1.estudiante == inscripcion2.estudiante
    
    def test_inscription_str_representation(self):
        """Test de representación en string de la inscripción."""
        inscripcion = Inscripcion.objects.create(
            estudiante=self.student,
            materia=self.materia,
            periodo=self.period,
            estado='activa'
        )
        
        expected = f"{self.student.username} - {self.materia.nombre} ({self.period.nombre})"
        assert str(inscripcion) == expected
    
    def test_inscription_timestamps(self):
        """Test de que los timestamps se crean automáticamente."""
        inscripcion = Inscripcion.objects.create(
            estudiante=self.student,
            materia=self.materia,
            periodo=self.period,
            estado='activa'
        )
        
        assert inscripcion.fecha_inscripcion is not None
        assert inscripcion.fecha_actualizacion is not None
        assert inscripcion.fecha_inscripcion <= inscripcion.fecha_actualizacion
    
    def test_calculate_average_grade_method(self):
        """Test del método para calcular promedio de calificaciones."""
        inscripcion = Inscripcion.objects.create(
            estudiante=self.student,
            materia=self.materia,
            periodo=self.period,
            estado='activa'
        )
        
        # Crear calificaciones
        Calificacion.objects.create(
            inscripcion=inscripcion,
            nota=4.0,
            tipo='parcial',
            porcentaje=30,
            fecha='2024-03-15'
        )
        
        Calificacion.objects.create(
            inscripcion=inscripcion,
            nota=4.5,
            tipo='final',
            porcentaje=70,
            fecha='2024-05-10'
        )
        
        # Calcular promedio ponderado: (4.0 * 0.3) + (4.5 * 0.7) = 1.2 + 3.15 = 4.35
        promedio = inscripcion.calculate_average_grade()
        assert promedio == 4.35
    
    def test_is_approved_method(self):
        """Test del método para verificar si la materia está aprobada."""
        inscripcion = Inscripcion.objects.create(
            estudiante=self.student,
            materia=self.materia,
            periodo=self.period,
            estado='activa'
        )
        
        # Sin calificaciones, no está aprobada
        assert not inscripcion.is_approved()
        
        # Con nota menor a 3.0, no está aprobada
        Calificacion.objects.create(
            inscripcion=inscripcion,
            nota=2.5,
            tipo='final',
            fecha='2024-05-10'
        )
        
        assert not inscripcion.is_approved()
        
        # Cambiar a nota aprobatoria
        calificacion = inscripcion.calificaciones.first()
        calificacion.nota = 3.5
        calificacion.save()
        
        assert inscripcion.is_approved()


@pytest.mark.django_db
class TestCalificacionModel:
    """Tests para el modelo Calificacion."""
    
    def setup_method(self):
        """Configuración inicial para cada test."""
        # Crear datos base
        self.student = User.objects.create_user(
            username='student_calif',
            email='student@test.com',
            password='testpass123',
            role='estudiante'
        )
        
        self.professor = User.objects.create_user(
            username='prof_calif',
            email='prof@test.com',
            password='testpass123',
            role='profesor'
        )
        
        self.period = Periodo.objects.create(
            nombre='2024-1',
            fecha_inicio='2024-01-15',
            fecha_fin='2024-05-15',
            activo=True
        )
        
        self.materia = Materia.objects.create(
            codigo='MAT001',
            nombre='Matemáticas I',
            creditos=4,
            profesor=self.professor
        )
        
        self.inscripcion = Inscripcion.objects.create(
            estudiante=self.student,
            materia=self.materia,
            periodo=self.period,
            estado='activa'
        )
    
    def test_create_valid_calificacion(self):
        """Test de creación de calificación válida."""
        calificacion = Calificacion.objects.create(
            inscripcion=self.inscripcion,
            nota=4.5,
            tipo='final',
            porcentaje=100,
            fecha='2024-05-10',
            descripcion='Examen final'
        )
        
        assert calificacion.inscripcion == self.inscripcion
        assert calificacion.nota == 4.5
        assert calificacion.tipo == 'final'
        assert calificacion.porcentaje == 100
        assert calificacion.descripcion == 'Examen final'
    
    def test_grade_range_validation(self):
        """Test de validación de rango de calificaciones (0.0 - 5.0)."""
        # Nota válida en rango
        calificacion = Calificacion.objects.create(
            inscripcion=self.inscripcion,
            nota=3.5,
            tipo='parcial',
            fecha='2024-03-15'
        )
        assert calificacion.nota == 3.5
        
        # Nota mínima válida
        calificacion_min = Calificacion.objects.create(
            inscripcion=self.inscripcion,
            nota=0.0,
            tipo='quiz',
            fecha='2024-02-15'
        )
        assert calificacion_min.nota == 0.0
        
        # Nota máxima válida
        calificacion_max = Calificacion.objects.create(
            inscripcion=self.inscripcion,
            nota=5.0,
            tipo='proyecto',
            fecha='2024-04-15'
        )
        assert calificacion_max.nota == 5.0
    
    def test_invalid_grade_ranges(self):
        """Test de validación de notas fuera del rango permitido."""
        # Nota menor que 0.0
        with pytest.raises(ValidationError):
            calificacion = Calificacion(
                inscripcion=self.inscripcion,
                nota=-1.0,
                tipo='parcial',
                fecha='2024-03-15'
            )
            calificacion.full_clean()
        
        # Nota mayor que 5.0
        with pytest.raises(ValidationError):
            calificacion = Calificacion(
                inscripcion=self.inscripcion,
                nota=6.0,
                tipo='parcial',
                fecha='2024-03-15'
            )
            calificacion.full_clean()
    
    def test_calificacion_tipo_choices(self):
        """Test de opciones válidas para el tipo de calificación."""
        valid_tipos = ['parcial', 'final', 'quiz', 'taller', 'proyecto']
        
        for i, tipo in enumerate(valid_tipos):
            calificacion = Calificacion.objects.create(
                inscripcion=self.inscripcion,
                nota=4.0,
                tipo=tipo,
                fecha=f'2024-0{i+2}-15'  # Fechas diferentes para evitar conflictos
            )
            assert calificacion.tipo == tipo
    
    def test_porcentaje_validation(self):
        """Test de validación de porcentaje (0-100)."""
        # Porcentaje válido
        calificacion = Calificacion.objects.create(
            inscripcion=self.inscripcion,
            nota=4.0,
            tipo='parcial',
            porcentaje=30,
            fecha='2024-03-15'
        )
        assert calificacion.porcentaje == 30
        
        # Porcentaje mínimo válido
        calificacion_min = Calificacion.objects.create(
            inscripcion=self.inscripcion,
            nota=4.0,
            tipo='quiz',
            porcentaje=0,
            fecha='2024-02-15'
        )
        assert calificacion_min.porcentaje == 0
        
        # Porcentaje máximo válido
        calificacion_max = Calificacion.objects.create(
            inscripcion=self.inscripcion,
            nota=4.0,
            tipo='final',
            porcentaje=100,
            fecha='2024-05-15'
        )
        assert calificacion_max.porcentaje == 100
    
    def test_invalid_porcentaje_ranges(self):
        """Test de validación de porcentajes fuera del rango permitido."""
        # Porcentaje menor que 0
        with pytest.raises(ValidationError):
            calificacion = Calificacion(
                inscripcion=self.inscripcion,
                nota=4.0,
                tipo='parcial',
                porcentaje=-10,
                fecha='2024-03-15'
            )
            calificacion.full_clean()
        
        # Porcentaje mayor que 100
        with pytest.raises(ValidationError):
            calificacion = Calificacion(
                inscripcion=self.inscripcion,
                nota=4.0,
                tipo='parcial',
                porcentaje=110,
                fecha='2024-03-15'
            )
            calificacion.full_clean()
    
    def test_calificacion_str_representation(self):
        """Test de representación en string de la calificación."""
        calificacion = Calificacion.objects.create(
            inscripcion=self.inscripcion,
            nota=4.5,
            tipo='final',
            fecha='2024-05-10'
        )
        
        expected = f"{self.inscripcion} - final: 4.5"
        assert str(calificacion) == expected
    
    def test_is_passing_grade_method(self):
        """Test del método para verificar si la calificación es aprobatoria."""
        # Nota reprobatoria
        calificacion_reprobada = Calificacion.objects.create(
            inscripcion=self.inscripcion,
            nota=2.9,
            tipo='final',
            fecha='2024-05-10'
        )
        assert not calificacion_reprobada.is_passing()
        
        # Nota aprobatoria exacta
        calificacion_exacta = Calificacion.objects.create(
            inscripcion=self.inscripcion,
            nota=3.0,
            tipo='parcial',
            fecha='2024-03-15'
        )
        assert calificacion_exacta.is_passing()
        
        # Nota aprobatoria alta
        calificacion_alta = Calificacion.objects.create(
            inscripcion=self.inscripcion,
            nota=4.5,
            tipo='proyecto',
            fecha='2024-04-15'
        )
        assert calificacion_alta.is_passing()
    
    def test_multiple_calificaciones_per_inscription(self):
        """Test de múltiples calificaciones por inscripción."""
        # Crear varias calificaciones
        calificaciones_data = [
            {'nota': 3.5, 'tipo': 'parcial', 'porcentaje': 20, 'fecha': '2024-02-15'},
            {'nota': 4.0, 'tipo': 'parcial', 'porcentaje': 20, 'fecha': '2024-03-15'},
            {'nota': 4.2, 'tipo': 'proyecto', 'porcentaje': 30, 'fecha': '2024-04-15'},
            {'nota': 4.5, 'tipo': 'final', 'porcentaje': 30, 'fecha': '2024-05-15'},
        ]
        
        calificaciones = []
        for data in calificaciones_data:
            calif = Calificacion.objects.create(
                inscripcion=self.inscripcion,
                **data
            )
            calificaciones.append(calif)
        
        # Verificar que todas se crearon correctamente
        assert self.inscripcion.calificaciones.count() == 4
        
        # Verificar que se pueden acceder todas
        for calif in calificaciones:
            assert calif in self.inscripcion.calificaciones.all()
    
    def test_calificacion_ordering(self):
        """Test del orden de calificaciones por fecha."""
        # Crear calificaciones en orden aleatorio de fechas
        calif1 = Calificacion.objects.create(
            inscripcion=self.inscripcion,
            nota=4.0,
            tipo='final',
            fecha='2024-05-15'
        )
        
        calif2 = Calificacion.objects.create(
            inscripcion=self.inscripcion,
            nota=3.5,
            tipo='parcial',
            fecha='2024-02-15'
        )
        
        calif3 = Calificacion.objects.create(
            inscripcion=self.inscripcion,
            nota=4.2,
            tipo='proyecto',
            fecha='2024-04-15'
        )
        
        # Obtener calificaciones ordenadas
        calificaciones_ordenadas = self.inscripcion.calificaciones.order_by('fecha')
        
        # Verificar orden cronológico
        assert calificaciones_ordenadas[0] == calif2  # Febrero
        assert calificaciones_ordenadas[1] == calif3  # Abril
        assert calificaciones_ordenadas[2] == calif1  # Mayo


@pytest.mark.django_db
class TestBusinessLogicValidations:
    """Tests para validaciones de lógica de negocio académica."""
    
    def setup_method(self):
        """Configuración inicial para tests de lógica de negocio."""
        # Crear usuarios
        self.student = User.objects.create_user(
            username='student_business',
            email='student@test.com',
            password='testpass123',
            role='estudiante'
        )
        
        self.professor = User.objects.create_user(
            username='prof_business',
            email='prof@test.com',
            password='testpass123',
            role='profesor'
        )
        
        # Crear perfil con límite de créditos
        self.profile = Profile.objects.create(
            user=self.student,
            identification='1234567890',
            max_credits_per_semester=15
        )
        
        # Crear período
        self.period = Periodo.objects.create(
            nombre='2024-1',
            fecha_inicio='2024-01-15',
            fecha_fin='2024-05-15',
            activo=True
        )
        
        # Crear materias
        self.basic_subject = Materia.objects.create(
            codigo='BASIC001',
            nombre='Materia Básica',
            creditos=3,
            profesor=self.professor
        )
        
        self.advanced_subject = Materia.objects.create(
            codigo='ADV001',
            nombre='Materia Avanzada',
            creditos=4,
            profesor=self.professor
        )
        
        # Crear prerrequisito
        self.prerequisite = Prerrequisito.objects.create(
            materia_principal=self.advanced_subject,
            materia_prerequisito=self.basic_subject
        )
    
    def test_student_cannot_enroll_same_subject_twice_same_period(self):
        """Test de que estudiante no puede inscribirse dos veces a la misma materia en el mismo período."""
        # Primera inscripción
        inscripcion1 = Inscripcion.objects.create(
            estudiante=self.student,
            materia=self.basic_subject,
            periodo=self.period,
            estado='activa'
        )
        
        # Intentar segunda inscripción (debe fallar)
        with pytest.raises(IntegrityError):
            Inscripcion.objects.create(
                estudiante=self.student,
                materia=self.basic_subject,
                periodo=self.period,
                estado='activa'
            )
    
    def test_student_can_retake_failed_subject(self):
        """Test de que estudiante puede volver a tomar una materia reprobada."""
        # Crear segundo período
        period2 = Periodo.objects.create(
            nombre='2024-2',
            fecha_inicio='2024-07-15',
            fecha_fin='2024-11-15',
            activo=False
        )
        
        # Primera inscripción reprobada
        inscripcion1 = Inscripcion.objects.create(
            estudiante=self.student,
            materia=self.basic_subject,
            periodo=self.period,
            estado='reprobada'
        )
        
        # Calificación reprobatoria
        Calificacion.objects.create(
            inscripcion=inscripcion1,
            nota=2.5,
            tipo='final',
            fecha='2024-05-10'
        )
        
        # Segunda inscripción en nuevo período (debe ser válida)
        inscripcion2 = Inscripcion.objects.create(
            estudiante=self.student,
            materia=self.basic_subject,
            periodo=period2,
            estado='activa'
        )
        
        assert inscripcion2.periodo != inscripcion1.periodo
        assert inscripcion2.materia == inscripcion1.materia
    
    def test_approved_subject_average_calculation(self):
        """Test de cálculo de promedio para materia aprobada."""
        inscripcion = Inscripcion.objects.create(
            estudiante=self.student,
            materia=self.basic_subject,
            periodo=self.period,
            estado='activa'
        )
        
        # Crear múltiples calificaciones
        Calificacion.objects.create(
            inscripcion=inscripcion,
            nota=3.0,
            tipo='parcial',
            porcentaje=25,
            fecha='2024-02-15'
        )
        
        Calificacion.objects.create(
            inscripcion=inscripcion,
            nota=4.0,
            tipo='parcial',
            porcentaje=25,
            fecha='2024-03-15'
        )
        
        Calificacion.objects.create(
            inscripcion=inscripcion,
            nota=4.5,
            tipo='proyecto',
            porcentaje=20,
            fecha='2024-04-15'
        )
        
        Calificacion.objects.create(
            inscripcion=inscripcion,
            nota=3.8,
            tipo='final',
            porcentaje=30,
            fecha='2024-05-15'
        )
        
        # Calcular promedio ponderado
        # (3.0*0.25) + (4.0*0.25) + (4.5*0.20) + (3.8*0.30) = 0.75 + 1.0 + 0.9 + 1.14 = 3.79
        promedio = inscripcion.calculate_average_grade()
        assert promedio == 3.79
        
        # Verificar que está aprobada (promedio >= 3.0)
        assert inscripcion.is_approved()
    
    def test_failed_subject_below_minimum_grade(self):
        """Test de materia reprobada por nota menor a 3.0."""
        inscripcion = Inscripcion.objects.create(
            estudiante=self.student,
            materia=self.basic_subject,
            periodo=self.period,
            estado='activa'
        )
        
        # Calificación reprobatoria
        Calificacion.objects.create(
            inscripcion=inscripcion,
            nota=2.8,
            tipo='final',
            fecha='2024-05-15'
        )
        
        assert not inscripcion.is_approved()
        
        # Cambiar estado a reprobada
        inscripcion.estado = 'reprobada'
        inscripcion.save()
        
        assert inscripcion.estado == 'reprobada'
    
    def test_exact_passing_grade_threshold(self):
        """Test de umbral exacto de aprobación (3.0)."""
        inscripcion = Inscripcion.objects.create(
            estudiante=self.student,
            materia=self.basic_subject,
            periodo=self.period,
            estado='activa'
        )
        
        # Calificación exactamente en el umbral
        Calificacion.objects.create(
            inscripcion=inscripcion,
            nota=3.0,
            tipo='final',
            fecha='2024-05-15'
        )
        
        # Debe estar aprobada con 3.0 exacto
        assert inscripcion.is_approved()
    
    def test_credit_hours_calculation(self):
        """Test de cálculo de horas crédito por inscripción."""
        # Inscribirse a materia de 4 créditos
        inscripcion = Inscripcion.objects.create(
            estudiante=self.student,
            materia=self.advanced_subject,  # 4 créditos
            periodo=self.period,
            estado='activa'
        )
        
        # Los créditos deben coincidir con la materia
        assert inscripcion.materia.creditos == 4
        
        # Crear otra inscripción
        inscripcion2 = Inscripcion.objects.create(
            estudiante=self.student,
            materia=self.basic_subject,  # 3 créditos
            periodo=self.period,
            estado='activa'
        )
        
        # Total de créditos inscritos: 4 + 3 = 7
        total_creditos = sum(
            inscr.materia.creditos 
            for inscr in Inscripcion.objects.filter(
                estudiante=self.student,
                periodo=self.period,
                estado='activa'
            )
        )
        
        assert total_creditos == 7
        assert total_creditos <= self.profile.max_credits_per_semester 