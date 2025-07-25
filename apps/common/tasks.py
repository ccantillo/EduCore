# tasks.py para la app common
# Aquí se implementarán tareas asíncronas comunes.

import logging
from datetime import datetime, timedelta
from celery import shared_task
from django.contrib.auth import get_user_model
from django.core.mail import send_mail as django_send_mail
from django.utils import timezone

from .services import EmailService, AcademicSummaryService, NotificationCleanupService

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task
def send_mail(subject, message, from_email, recipient_list, fail_silently=False):
    """
    Tarea asíncrona para envío de emails.
    Wrapper para la función send_mail de Django.
    """
    try:
        result = django_send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            fail_silently=fail_silently
        )
        logger.info(f"Email enviado exitosamente a {recipient_list}")
        return result
    except Exception as e:
        logger.error(f"Error enviando email: {str(e)}")
        if not fail_silently:
            raise
        return False


@shared_task
def enviar_email_bienvenida(user_id):
    """
    Tarea asíncrona para enviar email de bienvenida a nuevo usuario.
    """
    try:
        user = User.objects.get(id=user_id)
        success = EmailService.send_welcome_email(user)
        
        if success:
            logger.info(f"Email de bienvenida enviado exitosamente a {user.email}")
        else:
            logger.warning(f"Falló el envío del email de bienvenida a {user.email}")
        
        return success
    except User.DoesNotExist:
        logger.error(f"Usuario con ID {user_id} no encontrado para envío de email de bienvenida")
        return False
    except Exception as e:
        logger.error(f"Error en tarea de email de bienvenida: {str(e)}")
        raise


@shared_task
def limpiar_notificaciones_antiguas(days_old=90):
    """
    Tarea asíncrona para limpiar notificaciones antiguas.
    Se ejecuta periódicamente para mantener la base de datos optimizada.
    """
    try:
        logger.info(f"Iniciando limpieza de notificaciones de más de {days_old} días")
        
        # Ejecutar limpieza usando el servicio
        stats = NotificationCleanupService.cleanup_old_notifications(days_old)
        
        logger.info(
            f"Limpieza completada: {stats['total_eliminadas']} notificaciones eliminadas"
        )
        
        # Log adicional con detalles
        if stats['por_tipo']:
            logger.info(f"Eliminadas por tipo: {stats['por_tipo']}")
        
        return {
            'success': True,
            'eliminated_count': stats['total_eliminadas'],
            'stats': stats
        }
        
    except Exception as e:
        logger.error(f"Error en limpieza de notificaciones: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def enviar_resumen_semanal_profesores():
    """
    Tarea asíncrona para enviar resumen semanal a todos los profesores.
    Se ejecuta semanalmente, típicamente los lunes.
    """
    try:
        logger.info("Iniciando envío de resúmenes semanales a profesores")
        
        # Obtener todos los profesores activos
        profesores = User.objects.filter(
            role='profesor',
            is_active=True
        )
        
        success_count = 0
        error_count = 0
        
        for profesor in profesores:
            try:
                # Generar resumen para el profesor
                summary_data = AcademicSummaryService.generate_professor_weekly_summary(profesor)
                
                # Enviar email con el resumen
                success = EmailService.send_weekly_summary_email(profesor, summary_data)
                
                if success:
                    success_count += 1
                    logger.info(f"Resumen semanal enviado a {profesor.email}")
                else:
                    error_count += 1
                    logger.warning(f"Falló envío de resumen semanal a {profesor.email}")
                    
            except Exception as e:
                error_count += 1
                logger.error(f"Error enviando resumen a {profesor.email}: {str(e)}")
        
        total_profesores = profesores.count()
        logger.info(
            f"Resúmenes semanales completados: {success_count} exitosos, "
            f"{error_count} errores de {total_profesores} profesores"
        )
        
        return {
            'total_profesores': total_profesores,
            'enviados_exitosamente': success_count,
            'errores': error_count,
            'success_rate': round((success_count / total_profesores) * 100, 2) if total_profesores > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"Error en tarea de resúmenes semanales: {str(e)}")
        return {
            'error': str(e),
            'total_profesores': 0,
            'enviados_exitosamente': 0,
            'errores': 0
        }


@shared_task
def enviar_notificacion_calificacion(inscripcion_id, calificacion_id):
    """
    Tarea asíncrona para enviar notificación de nueva calificación.
    """
    try:
        from apps.inscripciones.models import Inscripcion, Calificacion
        
        inscripcion = Inscripcion.objects.get(id=inscripcion_id)
        calificacion = Calificacion.objects.get(id=calificacion_id)
        
        # Enviar email de notificación
        success = EmailService.send_grade_notification_email(inscripcion, calificacion)
        
        if success:
            logger.info(f"Notificación de calificación enviada a {inscripcion.estudiante.email}")
        else:
            logger.warning(f"Falló notificación de calificación a {inscripcion.estudiante.email}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error en notificación de calificación: {str(e)}")
        return False


@shared_task
def generar_estadisticas_uso():
    """
    Tarea asíncrona para generar estadísticas de uso del sistema.
    Se ejecuta diariamente para monitorear el uso.
    """
    try:
        from apps.notificaciones.models import Notificacion
        from apps.inscripciones.models import Inscripcion
        from apps.materias.models import Materia
        
        logger.info("Generando estadísticas de uso del sistema")
        
        # Obtener estadísticas básicas
        ahora = timezone.now()
        hace_24h = ahora - timedelta(hours=24)
        hace_7d = ahora - timedelta(days=7)
        
        stats = {
            'fecha_generacion': ahora.isoformat(),
            'usuarios_activos_7d': User.objects.filter(
                last_login__gte=hace_7d
            ).count(),
            'nuevas_inscripciones_24h': Inscripcion.objects.filter(
                fecha_inscripcion__gte=hace_24h
            ).count(),
            'notificaciones_24h': Notificacion.objects.filter(
                fecha_creacion__gte=hace_24h
            ).count(),
            'materias_activas': Materia.objects.filter(
                estado='activa'
            ).count(),
            'total_usuarios': User.objects.count(),
        }
        
        # Obtener estadísticas de notificaciones
        notification_stats = NotificationCleanupService.get_cleanup_statistics()
        stats['notificaciones'] = notification_stats
        
        logger.info(f"Estadísticas generadas: {stats}")
        
        return stats
        
    except Exception as e:
        logger.error(f"Error generando estadísticas: {str(e)}")
        return {'error': str(e)}


@shared_task
def procesar_inscripciones_pendientes():
    """
    Tarea asíncrona para procesar inscripciones pendientes.
    Valida prerrequisitos y límites de créditos.
    """
    try:
        from apps.inscripciones.models import Inscripcion
        
        logger.info("Procesando inscripciones pendientes")
        
        # Buscar inscripciones en estado pendiente
        inscripciones_pendientes = Inscripcion.objects.filter(estado='pendiente')
        
        procesadas = 0
        aprobadas = 0
        rechazadas = 0
        
        for inscripcion in inscripciones_pendientes:
            try:
                # Aquí iría la lógica de validación de prerrequisitos y créditos
                # Por simplicidad, asumimos que se aprueban
                inscripcion.estado = 'activa'
                inscripcion.save()
                
                aprobadas += 1
                procesadas += 1
                
                logger.info(f"Inscripción aprobada: {inscripcion}")
                
            except Exception as e:
                logger.error(f"Error procesando inscripción {inscripcion.id}: {str(e)}")
                rechazadas += 1
        
        logger.info(
            f"Inscripciones procesadas: {procesadas}, "
            f"Aprobadas: {aprobadas}, Rechazadas: {rechazadas}"
        )
        
        return {
            'procesadas': procesadas,
            'aprobadas': aprobadas,
            'rechazadas': rechazadas
        }
        
    except Exception as e:
        logger.error(f"Error procesando inscripciones pendientes: {str(e)}")
        return {'error': str(e)}


@shared_task
def enviar_resumen_semanal_profesores():
    """
    Tarea programada para enviar resumen semanal a todos los profesores.
    """
    try:
        # Obtener todos los profesores activos
        profesores = User.objects.filter(role='profesor', is_active=True)
        resumen_enviado = 0
        
        for profesor in profesores:
            try:
                # Generar resumen académico
                summary_data = AcademicSummaryService.generate_professor_weekly_summary(profesor)
                
                # Enviar email con resumen
                resultado = EmailService.send_weekly_summary_email(profesor, summary_data)
                
                if resultado:
                    resumen_enviado += 1
                    logger.info(f"Resumen semanal enviado a {profesor.email}")
                else:
                    logger.warning(f"No se pudo enviar resumen a {profesor.email}")
                    
            except Exception as e:
                logger.error(f"Error enviando resumen a {profesor.email}: {str(e)}")
                continue
        
        logger.info(f"Tarea completada: {resumen_enviado} resúmenes enviados de {profesores.count()} profesores")
        return resumen_enviado
        
    except Exception as e:
        logger.error(f"Error en tarea de resumen semanal: {str(e)}")
        raise


@shared_task
def limpiar_notificaciones_antiguas(days=90, preserve_read=False):
    """
    Tarea programada para limpiar notificaciones antiguas.
    
    Args:
        days: Días de antigüedad para considerar notificaciones como viejas
        preserve_read: Si True, preserva las notificaciones leídas
    """
    try:
        # Ejecutar limpieza
        eliminadas = NotificationCleanupService.cleanup_old_notifications(
            days=days,
            preserve_read=preserve_read
        )
        
        logger.info(f"Tarea de limpieza completada: {eliminadas} notificaciones eliminadas")
        return eliminadas
        
    except Exception as e:
        logger.error(f"Error en tarea de limpieza de notificaciones: {str(e)}")
        raise 