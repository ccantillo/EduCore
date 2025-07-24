from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Notificacion
from apps.users.models import User
from apps.inscripciones.models import Inscripcion, Calificacion
from apps.materias.models import Materia


@receiver(post_save, sender=User)
def crear_notificacion_bienvenida(sender, instance, created, **kwargs):
    """
    Crear notificación de bienvenida cuando se crea un nuevo usuario.
    """
    if created:
        try:
            Notificacion.notificar_bienvenida(instance)
        except Exception as e:
            # Log del error pero no fallar la creación del usuario
            print(f"Error al crear notificación de bienvenida: {e}")


@receiver(post_save, sender=Inscripcion)
def notificar_inscripcion(sender, instance, created, **kwargs):
    """
    Crear notificación cuando se crea una inscripción exitosa.
    """
    if created:
        try:
            Notificacion.notificar_inscripcion_exitosa(instance)
        except Exception as e:
            print(f"Error al crear notificación de inscripción: {e}")


@receiver(post_save, sender=Calificacion)
def notificar_calificacion(sender, instance, created, **kwargs):
    """
    Crear notificación cuando se publica una nueva calificación.
    """
    if created:
        try:
            Notificacion.notificar_calificacion_publicada(instance)
        except Exception as e:
            print(f"Error al crear notificación de calificación: {e}")


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
                except Materia.DoesNotExist:
                    # Es una nueva materia con profesor asignado
                    Notificacion.notificar_materia_asignada(instance, instance.profesor)
        except Exception as e:
            print(f"Error al crear notificación de asignación de materia: {e}")


# Señal personalizada para inscripciones rechazadas
def notificar_inscripcion_rechazada(estudiante, materia, periodo, motivo):
    """
    Función para crear notificación de inscripción rechazada.
    Se llama desde las vistas cuando falla la validación.
    """
    try:
        Notificacion.notificar_inscripcion_rechazada(estudiante, materia, periodo, motivo)
    except Exception as e:
        print(f"Error al crear notificación de inscripción rechazada: {e}")


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
    except Exception as e:
        print(f"Error al crear notificación del sistema: {e}")


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
    except Exception as e:
        print(f"Error al crear recordatorio: {e}")


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
        
        print(f"Se archivaron {count} notificaciones antiguas")
        
        return count
    except Exception as e:
        print(f"Error al limpiar notificaciones antiguas: {e}")
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
        
        return {
            'total': total,
            'no_leidas': no_leidas,
            'leidas': leidas,
            'archivadas': archivadas,
            'porcentaje_leidas': round((leidas / total * 100) if total > 0 else 0, 2)
        }
    except Exception as e:
        print(f"Error al obtener estadísticas de notificaciones: {e}")
        return {
            'total': 0,
            'no_leidas': 0,
            'leidas': 0,
            'archivadas': 0,
            'porcentaje_leidas': 0
        } 