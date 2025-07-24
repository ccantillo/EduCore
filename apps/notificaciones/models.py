# models.py para la app notificaciones
# Aquí se definirán los modelos relacionados con notificaciones y mensajes.

from django.db import models
from apps.users.models import User


class Notificacion(models.Model):
    """
    Modelo para representar notificaciones del sistema académico.
    Permite enviar alertas automáticas a usuarios sobre eventos importantes.
    """
    
    # Usuario destinatario
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notificaciones',
        verbose_name='Usuario'
    )
    
    # Tipo de notificación
    TIPO_CHOICES = [
        ('bienvenida', 'Bienvenida'),
        ('inscripcion_exitosa', 'Inscripción Exitosa'),
        ('inscripcion_rechazada', 'Inscripción Rechazada'),
        ('calificacion_publicada', 'Calificación Publicada'),
        ('materia_asignada', 'Materia Asignada'),
        ('recordatorio', 'Recordatorio'),
        ('sistema', 'Sistema'),
        ('otro', 'Otro'),
    ]
    
    tipo = models.CharField(
        max_length=30,
        choices=TIPO_CHOICES,
        verbose_name='Tipo'
    )
    
    # Contenido de la notificación
    titulo = models.CharField(
        max_length=200,
        verbose_name='Título'
    )
    
    mensaje = models.TextField(
        verbose_name='Mensaje'
    )
    
    # Estado de la notificación
    ESTADO_CHOICES = [
        ('no_leida', 'No Leída'),
        ('leida', 'Leída'),
        ('archivada', 'Archivada'),
    ]
    
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='no_leida',
        verbose_name='Estado'
    )
    
    # Campos adicionales
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    fecha_lectura = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de lectura')
    
    # Campos de auditoría
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Fecha de actualización')
    
    class Meta:
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        db_table = 'notificaciones'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['usuario', 'estado']),
            models.Index(fields=['tipo', 'fecha_creacion']),
        ]
    
    def __str__(self):
        return f"{self.usuario.username} - {self.titulo}"
    
    def marcar_como_leida(self):
        """Marcar la notificación como leída."""
        if self.estado == 'no_leida':
            from django.utils import timezone
            self.estado = 'leida'
            self.fecha_lectura = timezone.now()
            self.save(update_fields=['estado', 'fecha_lectura'])
    
    def archivar(self):
        """Archivar la notificación."""
        self.estado = 'archivada'
        self.save(update_fields=['estado'])
    
    @property
    def es_no_leida(self):
        """Verificar si la notificación no ha sido leída."""
        return self.estado == 'no_leida'
    
    @property
    def es_leida(self):
        """Verificar si la notificación ha sido leída."""
        return self.estado == 'leida'
    
    @property
    def es_archivada(self):
        """Verificar si la notificación está archivada."""
        return self.estado == 'archivada'
    
    @classmethod
    def crear_notificacion(cls, usuario, tipo, titulo, mensaje):
        """
        Método de clase para crear notificaciones de forma conveniente.
        """
        return cls.objects.create(
            usuario=usuario,
            tipo=tipo,
            titulo=titulo,
            mensaje=mensaje
        )
    
    @classmethod
    def notificar_bienvenida(cls, usuario):
        """Crear notificación de bienvenida para nuevos usuarios."""
        titulo = "¡Bienvenido al Sistema Académico!"
        mensaje = f"""
        Hola {usuario.get_full_name() or usuario.username},
        
        Te damos la bienvenida al Sistema Académico. Tu cuenta ha sido creada exitosamente.
        
        Tu rol en el sistema es: {usuario.get_role_display()}
        
        Si tienes alguna pregunta, no dudes en contactar al administrador.
        
        ¡Que tengas un excelente día!
        """
        
        return cls.crear_notificacion(
            usuario=usuario,
            tipo='bienvenida',
            titulo=titulo,
            mensaje=mensaje.strip()
        )
    
    @classmethod
    def notificar_inscripcion_exitosa(cls, inscripcion):
        """Crear notificación de inscripción exitosa."""
        titulo = f"Inscripción Exitosa - {inscripcion.materia.codigo}"
        mensaje = f"""
        Hola {inscripcion.estudiante.get_full_name()},
        
        Tu inscripción a la materia {inscripcion.materia.nombre} ({inscripcion.materia.codigo}) 
        para el período {inscripcion.periodo.nombre} ha sido exitosa.
        
        Detalles:
        - Materia: {inscripcion.materia.nombre}
        - Créditos: {inscripcion.materia.creditos}
        - Período: {inscripcion.periodo.nombre}
        - Profesor: {inscripcion.materia.profesor.get_full_name() if inscripcion.materia.profesor else 'Por asignar'}
        
        ¡Buena suerte en tu curso!
        """
        
        return cls.crear_notificacion(
            usuario=inscripcion.estudiante,
            tipo='inscripcion_exitosa',
            titulo=titulo,
            mensaje=mensaje.strip()
        )
    
    @classmethod
    def notificar_inscripcion_rechazada(cls, estudiante, materia, periodo, motivo):
        """Crear notificación de inscripción rechazada."""
        titulo = f"Inscripción Rechazada - {materia.codigo}"
        mensaje = f"""
        Hola {estudiante.get_full_name()},
        
        Tu solicitud de inscripción a la materia {materia.nombre} ({materia.codigo}) 
        para el período {periodo.nombre} ha sido rechazada.
        
        Motivo: {motivo}
        
        Si consideras que esto es un error, por favor contacta al administrador.
        """
        
        return cls.crear_notificacion(
            usuario=estudiante,
            tipo='inscripcion_rechazada',
            titulo=titulo,
            mensaje=mensaje.strip()
        )
    
    @classmethod
    def notificar_calificacion_publicada(cls, calificacion):
        """Crear notificación de calificación publicada."""
        inscripcion = calificacion.inscripcion
        titulo = f"Nueva Calificación - {inscripcion.materia.codigo}"
        mensaje = f"""
        Hola {inscripcion.estudiante.get_full_name()},
        
        Se ha publicado una nueva calificación en la materia {inscripcion.materia.nombre}.
        
        Detalles:
        - Tipo: {calificacion.get_tipo_display()}
        - Nota: {calificacion.nota}/5.0
        - Peso: {calificacion.peso}%
        - Comentarios: {calificacion.comentarios or 'Sin comentarios'}
        
        Tu nota final actual es: {inscripcion.nota_final or 'Pendiente'}
        """
        
        return cls.crear_notificacion(
            usuario=inscripcion.estudiante,
            tipo='calificacion_publicada',
            titulo=titulo,
            mensaje=mensaje.strip()
        )
    
    @classmethod
    def notificar_materia_asignada(cls, materia, profesor):
        """Crear notificación de materia asignada a profesor."""
        titulo = f"Materia Asignada - {materia.codigo}"
        mensaje = f"""
        Hola {profesor.get_full_name()},
        
        Se te ha asignado la materia {materia.nombre} ({materia.codigo}).
        
        Detalles:
        - Código: {materia.codigo}
        - Nombre: {materia.nombre}
        - Créditos: {materia.creditos}
        - Descripción: {materia.descripcion or 'Sin descripción'}
        
        Puedes gestionar esta materia desde tu panel de profesor.
        """
        
        return cls.crear_notificacion(
            usuario=profesor,
            tipo='materia_asignada',
            titulo=titulo,
            mensaje=mensaje.strip()
        ) 