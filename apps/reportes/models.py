# models.py para la app reportes
# Aquí se definirán los modelos relacionados con reportes y exportaciones.

from django.db import models
from apps.users.models import User


class ReporteGenerado(models.Model):
    """
    Modelo para registrar los reportes generados en el sistema.
    Permite hacer seguimiento de qué reportes se han creado y cuándo.
    """
    
    # Usuario que solicitó el reporte
    solicitante = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reportes_solicitados',
        verbose_name='Solicitante'
    )
    
    # Tipo de reporte
    TIPO_CHOICES = [
        ('estudiante', 'Reporte de Estudiante'),
        ('profesor', 'Reporte de Profesor'),
        ('materia', 'Reporte de Materia'),
        ('periodo', 'Reporte de Período'),
        ('general', 'Reporte General'),
    ]
    
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        verbose_name='Tipo de Reporte'
    )
    
    # Información del reporte
    nombre_archivo = models.CharField(
        max_length=255,
        verbose_name='Nombre del Archivo'
    )
    
    ruta_archivo = models.CharField(
        max_length=500,
        verbose_name='Ruta del Archivo'
    )
    
    # Parámetros del reporte
    parametros = models.JSONField(
        default=dict,
        verbose_name='Parámetros del Reporte'
    )
    
    # Estado del reporte
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('generando', 'Generando'),
        ('completado', 'Completado'),
        ('error', 'Error'),
        ('expirado', 'Expirado'),
    ]
    
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente',
        verbose_name='Estado'
    )
    
    # Información adicional
    registros_procesados = models.IntegerField(
        default=0,
        verbose_name='Registros Procesados'
    )
    
    mensaje_error = models.TextField(
        blank=True,
        null=True,
        verbose_name='Mensaje de Error'
    )
    
    # Campos de auditoría
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Fecha de actualización')
    completado_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de completado'
    )
    
    class Meta:
        verbose_name = 'Reporte Generado'
        verbose_name_plural = 'Reportes Generados'
        db_table = 'reportes_generados'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['solicitante', 'tipo']),
            models.Index(fields=['estado', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.solicitante.username} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def marcar_completado(self, registros_procesados=0):
        """Marcar el reporte como completado."""
        from django.utils import timezone
        
        self.estado = 'completado'
        self.registros_procesados = registros_procesados
        self.completado_at = timezone.now()
        self.save(update_fields=['estado', 'registros_procesados', 'completado_at'])
    
    def marcar_error(self, mensaje_error):
        """Marcar el reporte como error."""
        self.estado = 'error'
        self.mensaje_error = mensaje_error
        self.save(update_fields=['estado', 'mensaje_error'])
    
    def marcar_generando(self):
        """Marcar el reporte como en proceso de generación."""
        self.estado = 'generando'
        self.save(update_fields=['estado'])
    
    @property
    def es_completado(self):
        """Verificar si el reporte está completado."""
        return self.estado == 'completado'
    
    @property
    def es_error(self):
        """Verificar si el reporte tuvo error."""
        return self.estado == 'error'
    
    @property
    def es_pendiente(self):
        """Verificar si el reporte está pendiente."""
        return self.estado == 'pendiente'
    
    @property
    def tiempo_generacion(self):
        """Calcular el tiempo de generación del reporte."""
        if self.completado_at and self.created_at:
            return self.completado_at - self.created_at
        return None
    
    @classmethod
    def limpiar_reportes_antiguos(cls, dias=30):
        """
        Limpiar reportes antiguos para liberar espacio.
        """
        from django.utils import timezone
        from datetime import timedelta
        
        fecha_limite = timezone.now() - timedelta(days=dias)
        
        # Obtener reportes antiguos
        reportes_antiguos = cls.objects.filter(
            created_at__lt=fecha_limite,
            estado__in=['completado', 'error']
        )
        
        count = reportes_antiguos.count()
        
        # Eliminar archivos físicos y registros
        for reporte in reportes_antiguos:
            try:
                import os
                if os.path.exists(reporte.ruta_archivo):
                    os.remove(reporte.ruta_archivo)
            except Exception:
                pass  # Ignorar errores al eliminar archivos
        
        # Eliminar registros de la base de datos
        reportes_antiguos.delete()
        
        return count 