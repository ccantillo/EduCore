# models.py para la app inscripciones
# Aquí se definirán los modelos relacionados con inscripciones de estudiantes a materias.

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.db.models import Avg
from apps.users.models import User
from apps.materias.models import Materia, Periodo


class Inscripcion(models.Model):
    """
    Modelo para representar las inscripciones de estudiantes a materias.
    Incluye calificaciones, estados y validaciones de prerrequisitos.
    """
    
    # Relaciones principales
    estudiante = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'estudiante'},
        related_name='inscripciones',
        verbose_name='Estudiante'
    )
    
    materia = models.ForeignKey(
        Materia,
        on_delete=models.CASCADE,
        related_name='inscripciones',
        verbose_name='Materia'
    )
    
    periodo = models.ForeignKey(
        Periodo,
        on_delete=models.CASCADE,
        related_name='inscripciones',
        verbose_name='Período'
    )
    
    # Estado de la inscripción
    ESTADO_CHOICES = [
        ('activa', 'Activa'),
        ('aprobada', 'Aprobada'),
        ('reprobada', 'Reprobada'),
        ('retirada', 'Retirada'),
        ('cancelada', 'Cancelada'),
    ]
    
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='activa',
        verbose_name='Estado'
    )
    
    # Calificaciones
    nota_final = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        verbose_name='Nota Final'
    )
    
    # Campos adicionales
    fecha_inscripcion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de inscripción')
    fecha_retiro = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de retiro')
    
    # Campos de auditoría
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Fecha de actualización')
    
    class Meta:
        verbose_name = 'Inscripción'
        verbose_name_plural = 'Inscripciones'
        db_table = 'inscripciones'
        unique_together = ['estudiante', 'materia', 'periodo']
        ordering = ['-fecha_inscripcion']
    
    def __str__(self):
        return f"{self.estudiante.username} - {self.materia.codigo} ({self.periodo.nombre})"
    
    def clean(self):
        """Validaciones personalizadas del modelo."""
        super().clean()
        
        # Validar que el estudiante tenga rol de estudiante
        if self.estudiante.role != 'estudiante':
            raise ValidationError({
                'estudiante': 'El usuario debe tener rol de estudiante.'
            })
        
        # Validar que no haya inscripción duplicada
        if self.pk is None:  # Solo para nuevas inscripciones
            if Inscripcion.objects.filter(
                estudiante=self.estudiante,
                materia=self.materia,
                periodo=self.periodo
            ).exists():
                raise ValidationError(
                    'El estudiante ya está inscrito en esta materia para este período.'
                )
        
        # Validar prerrequisitos
        if not self._validar_prerrequisitos():
            raise ValidationError(
                'El estudiante no cumple con los prerrequisitos para esta materia.'
            )
        
        # Validar límite de créditos
        if not self._validar_limite_creditos():
            raise ValidationError(
                'El estudiante excede el límite de créditos permitidos.'
            )
    
    def save(self, *args, **kwargs):
        """Sobrescribir save para aplicar validaciones."""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def _validar_prerrequisitos(self):
        """Validar que el estudiante cumpla con los prerrequisitos de la materia."""
        prerrequisitos = self.materia.prerrequisitos.filter(tipo='obligatorio')
        
        for prereq in prerrequisitos:
            # Verificar si el estudiante aprobó el prerrequisito
            inscripcion_prereq = Inscripcion.objects.filter(
                estudiante=self.estudiante,
                materia=prereq.prerrequisito,
                estado='aprobada'
            ).first()
            
            if not inscripcion_prereq:
                return False
        
        return True
    
    def _validar_limite_creditos(self):
        """Validar que el estudiante no exceda el límite de créditos."""
        # Obtener créditos actuales del período
        creditos_actuales = Inscripcion.objects.filter(
            estudiante=self.estudiante,
            periodo=self.periodo,
            estado='activa'
        ).aggregate(
            total_creditos=models.Sum('materia__creditos')
        )['total_creditos'] or 0
        
        # Agregar créditos de la nueva materia
        creditos_totales = creditos_actuales + self.materia.creditos
        
        # Límite de 24 créditos por período (configurable)
        LIMITE_CREDITOS = 24
        return creditos_totales <= LIMITE_CREDITOS
    
    @property
    def aprobada(self):
        """Verificar si la inscripción está aprobada."""
        return self.estado == 'aprobada'
    
    @property
    def reprobada(self):
        """Verificar si la inscripción está reprobada."""
        return self.estado == 'reprobada'
    
    @property
    def activa(self):
        """Verificar si la inscripción está activa."""
        return self.estado == 'activa'


class Calificacion(models.Model):
    """
    Modelo para manejar calificaciones parciales de una inscripción.
    Permite registrar múltiples evaluaciones por materia.
    """
    
    inscripcion = models.ForeignKey(
        Inscripcion,
        on_delete=models.CASCADE,
        related_name='calificaciones',
        verbose_name='Inscripción'
    )
    
    # Tipo de evaluación
    TIPO_CHOICES = [
        ('parcial_1', 'Parcial 1'),
        ('parcial_2', 'Parcial 2'),
        ('final', 'Final'),
        ('trabajo', 'Trabajo'),
        ('proyecto', 'Proyecto'),
        ('otro', 'Otro'),
    ]
    
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        verbose_name='Tipo de Evaluación'
    )
    
    # Calificación
    nota = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        verbose_name='Nota'
    )
    
    # Peso de la evaluación (porcentaje)
    peso = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        verbose_name='Peso (%)'
    )
    
    # Comentarios del profesor
    comentarios = models.TextField(
        blank=True,
        verbose_name='Comentarios'
    )
    
    # Campos de auditoría
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Fecha de actualización')
    
    class Meta:
        verbose_name = 'Calificación'
        verbose_name_plural = 'Calificaciones'
        db_table = 'inscripciones_calificaciones'
        unique_together = ['inscripcion', 'tipo']
        ordering = ['inscripcion', 'tipo']
    
    def __str__(self):
        return f"{self.inscripcion} - {self.get_tipo_display()}: {self.nota}"
    
    def clean(self):
        """Validaciones personalizadas."""
        super().clean()
        
        # Validar que el peso total no exceda 100%
        peso_total = Calificacion.objects.filter(
            inscripcion=self.inscripcion
        ).exclude(
            pk=self.pk
        ).aggregate(
            total=models.Sum('peso')
        )['total'] or 0
        
        if peso_total + self.peso > 100:
            raise ValidationError({
                'peso': f'El peso total de las evaluaciones no puede exceder 100%. Actual: {peso_total + self.peso}%'
            })
    
    def save(self, *args, **kwargs):
        """Sobrescribir save para actualizar nota final."""
        self.full_clean()
        super().save(*args, **kwargs)
        
        # Actualizar nota final de la inscripción
        self._actualizar_nota_final()
    
    def _actualizar_nota_final(self):
        """Calcular y actualizar la nota final de la inscripción."""
        calificaciones = Calificacion.objects.filter(inscripcion=self.inscripcion)
        
        if calificaciones.exists():
            # Calcular promedio ponderado
            suma_ponderada = sum(cal.nota * cal.peso for cal in calificaciones)
            peso_total = sum(cal.peso for cal in calificaciones)
            
            if peso_total > 0:
                nota_final = suma_ponderada / peso_total
                self.inscripcion.nota_final = round(nota_final, 2)
                
                # Actualizar estado basado en la nota
                if nota_final >= 3.0:
                    self.inscripcion.estado = 'aprobada'
                else:
                    self.inscripcion.estado = 'reprobada'
                
                self.inscripcion.save(update_fields=['nota_final', 'estado']) 