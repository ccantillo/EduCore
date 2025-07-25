import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.utils import timezone

from .models import Notificacion
from apps.users.models import User
from apps.inscripciones.models import Inscripcion, Calificacion
from apps.materias.models import Materia

# Configurar logger
logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def crear_notificacion_bienvenida(sender, instance, created, **kwargs):
    """
    Crear notificación de bienvenida cuando se crea un nuevo usuario.
    """
    if created:
        try:
            # Crear notificación de bienvenida
            notification = Notificacion.notificar_bienvenida(instance)
            logger.info(f"Notificación de bienvenida creada para {instance.username}")
            
            # Enviar email de bienvenida usando la tarea asíncrona
            try:
                from apps.common.tasks import enviar_email_bienvenida
                enviar_email_bienvenida.delay(instance.id)
                logger.info(f"Tarea de email de bienvenida programada para {instance.username}")
            except Exception as email_error:
                logger.error(f"Error programando email de bienvenida para {instance.username}: {email_error}")
                
        except Exception as e:
            # Log del error pero no fallar la creación del usuario
            logger.error(f"Error al crear notificación de bienvenida para {instance.username}: {e}")


@receiver(post_save, sender=Inscripcion)
def notificar_inscripcion(sender, instance, created, **kwargs):
    """
    Crear notificación cuando se crea una inscripción exitosa.
    """
    if created:
        try:
            Notificacion.notificar_inscripcion_exitosa(instance)
        except Exception as e:
            logger.error(f"Error al crear notificación de inscripción: {e}")


@receiver(post_save, sender=Calificacion)
def notificar_calificacion(sender, instance, created, **kwargs):
    """
    Crear notificación cuando se publica una nueva calificación.
    """
    if created:
        try:
            Notificacion.notificar_calificacion_publicada(instance)
            logger.info(f"Notificación de calificación creada para estudiante {instance.inscripcion.estudiante.username}")
            
            # Enviar email de notificación de calificación
            try:
                from apps.common.tasks import enviar_notificacion_calificacion
                enviar_notificacion_calificacion.delay(instance.inscripcion.id, instance.id)
                logger.info(f"Tarea de email de calificación programada")
            except Exception as email_error:
                logger.error(f"Error programando email de calificación: {email_error}")
                
        except Exception as e:
            logger.error(f"Error al crear notificación de calificación: {e}")


@receiver(post_save, sender=Materia)
def notificar_asignacion_materia(sender, instance, **kwargs):
    """
    Crear notificación cuando se asigna un profesor a una materia.
    """
    # Verificar si se agregó un profesor (no era None antes y ahora sí tiene uno)
    if instance.profesor:
        try:
            # Solo notificar si es una asignación nueva o cambio de profesor
            if instance.pk:  # Materia existente
                try:
                    materia_anterior = Materia.objects.get(pk=instance.pk)
                    if materia_anterior.profesor != instance.profesor:
                        Notificacion.notificar_materia_asignada(instance, instance.profesor)
                        logger.info(f"Notificación de asignación de materia creada para {instance.profesor.username}")
                except Materia.DoesNotExist:
                    # Es una nueva materia con profesor asignado
                    Notificacion.notificar_materia_asignada(instance, instance.profesor)
                    logger.info(f"Notificación de nueva materia creada para {instance.profesor.username}")
        except Exception as e:
            logger.error(f"Error al crear notificación de asignación de materia: {e}")


# Señal personalizada para inscripciones rechazadas
def notificar_inscripcion_rechazada(estudiante, materia, periodo, motivo):
    """
    Función para crear notificación de inscripción rechazada.
    Se llama desde las vistas cuando falla la validación.
    """
    try:
        Notificacion.notificar_inscripcion_rechazada(estudiante, materia, periodo, motivo)
    except Exception as e:
        logger.error(f"Error al crear notificación de inscripción rechazada: {e}")


# Señal personalizada para notificaciones del sistema
def crear_notificacion_sistema(usuario, titulo, mensaje):
    """
    Función para crear notificaciones del sistema.
    """
    try:
        Notificacion.crear_notificacion(
            usuario=usuario,
            tipo='sistema',
            titulo=titulo,
            mensaje=mensaje
        )
        logger.info(f"Notificación del sistema creada para {usuario.username}")
    except Exception as e:
        logger.error(f"Error al crear notificación del sistema: {e}")


# Señal personalizada para recordatorios
def crear_recordatorio(usuario, titulo, mensaje):
    """
    Función para crear recordatorios.
    """
    try:
        Notificacion.crear_notificacion(
            usuario=usuario,
            tipo='recordatorio',
            titulo=titulo,
            mensaje=mensaje
        )
        logger.info(f"Recordatorio creado para {usuario.username}")
    except Exception as e:
        logger.error(f"Error al crear recordatorio: {e}")


# Función para limpiar notificaciones antiguas
def limpiar_notificaciones_antiguas(dias=30):
    """
    Limpiar notificaciones más antiguas que el número de días especificado.
    """
    from datetime import timedelta
    
    fecha_limite = timezone.now() - timedelta(days=dias)
    
    try:
        # Archivar notificaciones leídas antiguas
        notificaciones_antiguas = Notificacion.objects.filter(
            estado='leida',
            fecha_creacion__lt=fecha_limite
        )
        
        count = notificaciones_antiguas.count()
        notificaciones_antiguas.update(estado='archivada')
        
        logger.info(f"Se archivaron {count} notificaciones antiguas")
        
        return count
    except Exception as e:
        logger.error(f"Error al limpiar notificaciones antiguas: {e}")
        return 0


# Función para obtener estadísticas de notificaciones
def obtener_estadisticas_notificaciones(usuario=None):
    """
    Obtener estadísticas de notificaciones.
    """
    try:
        queryset = Notificacion.objects
        
        if usuario:
            queryset = queryset.filter(usuario=usuario)
        
        total = queryset.count()
        no_leidas = queryset.filter(estado='no_leida').count()
        leidas = queryset.filter(estado='leida').count()
        archivadas = queryset.filter(estado='archivada').count()
        
        stats = {
            'total': total,
            'no_leidas': no_leidas,
            'leidas': leidas,
            'archivadas': archivadas,
            'porcentaje_leidas': round((leidas / total * 100) if total > 0 else 0, 2)
        }
        
        logger.info(f"Estadísticas de notificaciones generadas: {stats}")
        return stats
    except Exception as e:
        logger.error(f"Error al obtener estadísticas de notificaciones: {e}")
        return {
            'total': 0,
            'no_leidas': 0,
            'leidas': 0,
            'archivadas': 0,
            'porcentaje_leidas': 0
        } 