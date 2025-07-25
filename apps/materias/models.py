# models.py para la app materias
# Todo sobre materias, prerrequisitos, períodos académicos, etc.

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from apps.users.models import User


class Materia(models.Model):
    """
    Modelo para representar las materias del sistema académico.
    Incluye información sobre créditos, prerrequisitos y profesor asignado.
    """
    
    # Información básica
    codigo = models.CharField(
        max_length=10,
        unique=True,
        verbose_name='Código'
    )
    
    nombre = models.CharField(
        max_length=200,
        verbose_name='Nombre'
    )
    
    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción'
    )
    
    # Créditos y carga académica
    creditos = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name='Créditos'
    )
    
    # Estado de la materia
    ESTADO_CHOICES = [
        ('activa', 'Activa'),
        ('inactiva', 'Inactiva'),
        ('en_revision', 'En Revisión'),
    ]
    
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='activa',
        verbose_name='Estado'
    )
    
    # Profesor asignado
    profesor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'profesor'},
        related_name='materias_asignadas',
        verbose_name='Profesor'
    )
    
    # Campos de auditoría
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Fecha de actualización')
    
    class Meta:
        verbose_name = 'Materia'
        verbose_name_plural = 'Materias'
        db_table = 'materias'
        ordering = ['codigo']
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    def clean(self):
        """Validamos que los datos de la materia sean correctos."""
        super().clean()
        
        # Validar que el profesor tenga rol de profesor
        if self.profesor and self.profesor.role != 'profesor':
            raise ValidationError({
                'profesor': 'El usuario asignado debe tener rol de profesor.'
            })
    
    @property
    def estudiantes_inscritos_count(self):
        """Obtener el número de estudiantes inscritos."""
        return self.inscripciones.filter(estado='activa').count()
    
    @property
    def cupo_disponible(self):
        """Calcular cupo disponible (si se implementa límite de estudiantes)."""
        # Por ahora retorna None (sin límite)
        return None


class Prerrequisito(models.Model):
    """
    Modelo para manejar prerrequisitos entre materias.
    Permite definir qué materias son necesarias para inscribir otra.
    """
    
    materia = models.ForeignKey(
        Materia,
        on_delete=models.CASCADE,
        related_name='prerrequisitos',
        verbose_name='Materia'
    )
    
    prerrequisito = models.ForeignKey(
        Materia,
        on_delete=models.CASCADE,
        related_name='materias_que_requieren',
        verbose_name='Prerrequisito'
    )
    
    # Tipo de prerrequisito
    TIPO_CHOICES = [
        ('obligatorio', 'Obligatorio'),
        ('recomendado', 'Recomendado'),
    ]
    
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='obligatorio',
        verbose_name='Tipo'
    )
    
    # Campos de auditoría
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    
    class Meta:
        verbose_name = 'Prerrequisito'
        verbose_name_plural = 'Prerrequisitos'
        db_table = 'materias_prerrequisitos'
        unique_together = ['materia', 'prerrequisito']
        ordering = ['materia', 'prerrequisito']
    
    def __str__(self):
        return f"{self.materia.codigo} requiere {self.prerrequisito.codigo}"
    
    def clean(self):
        """Validamos que no haya prerrequisitos circulares."""
        super().clean()
        
        # Evitar prerrequisito circular
        if self.materia == self.prerrequisito:
            raise ValidationError(
                'Una materia no puede ser prerrequisito de sí misma.'
            )
        
        # Verificar que no se cree un ciclo de prerrequisitos
        if self._crearia_ciclo():
            raise ValidationError(
                'No se puede crear un ciclo de prerrequisitos.'
            )
    
    def _crearia_ciclo(self):
        """Verificar si agregar este prerrequisito crearía un ciclo."""
        # Implementación simplificada - en producción se necesitaría un algoritmo más robusto
        prereqs_actuales = set()
        self._obtener_prerrequisitos_recursivos(self.prerrequisito, prereqs_actuales)
        return self.materia in prereqs_actuales
    
    def _obtener_prerrequisitos_recursivos(self, materia, prereqs_set):
        """Obtener todos los prerrequisitos de una materia de forma recursiva."""
        for prereq in materia.prerrequisitos.all():
            if prereq.prerrequisito not in prereqs_set:
                prereqs_set.add(prereq.prerrequisito)
                self._obtener_prerrequisitos_recursivos(prereq.prerrequisito, prereqs_set)


class Periodo(models.Model):
    """
    Modelo para representar períodos académicos (semestres, trimestres, etc.).
    """
    
    nombre = models.CharField(
        max_length=100,
        verbose_name='Nombre'
    )
    
    fecha_inicio = models.DateField(verbose_name='Fecha de inicio')
    fecha_fin = models.DateField(verbose_name='Fecha de fin')
    
    # Estado del período
    ESTADO_CHOICES = [
        ('planificacion', 'Planificación'),
        ('inscripciones', 'Inscripciones'),
        ('en_curso', 'En Curso'),
        ('finalizado', 'Finalizado'),
    ]
    
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='planificacion',
        verbose_name='Estado'
    )
    
    # Campos de auditoría
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Fecha de actualización')
    
    class Meta:
        verbose_name = 'Período'
        verbose_name_plural = 'Períodos'
        db_table = 'materias_periodos'
        ordering = ['-fecha_inicio']
    
    def __str__(self):
        return f"{self.nombre} ({self.get_estado_display()})"
    
    def clean(self):
        """Validamos las fechas del período académico."""
        super().clean()
        
        if self.fecha_inicio >= self.fecha_fin:
            raise ValidationError(
                'La fecha de inicio debe ser anterior a la fecha de fin.'
            )
    
    @property
    def es_activo(self):
        """Verificar si el período está activo (en inscripciones o en curso)."""
        return self.estado in ['inscripciones', 'en_curso'] 