# tasks.py para la app notificaciones
# Tareas de notificaciones - envío masivo de emails, limpieza de antiguas

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Notificacion
from .signals import limpiar_notificaciones_antiguas


@shared_task
def limpiar_notificaciones_antiguas_task(dias=30):
    """
    Tarea programada para limpiar notificaciones antiguas.
    Archiva (no elimina) notificaciones leídas con más de 'dias' días de antigüedad.
    Por defecto, archiva notificaciones con fecha_creacion > 30 días.
    """
    try:
        # Usar la función de signals que ya está implementada
        count = limpiar_notificaciones_antiguas(dias)
        
        mensaje = f"Tarea de limpieza completada: {count} notificaciones archivadas (más de {dias} días)"
        print(mensaje)
        
        return {
            'mensaje': mensaje,
            'notificaciones_archivadas': count,
            'dias': dias,
            'fecha_ejecucion': timezone.now().isoformat()
        }
        
    except Exception as e:
        error_msg = f"Error en tarea de limpieza de notificaciones: {e}"
        print(error_msg)
        return {
            'error': error_msg,
            'notificaciones_archivadas': 0,
            'fecha_ejecucion': timezone.now().isoformat()
        }


@shared_task
def delete_old_notifications(days=30):
    """
    DEPRECATED: Usar limpiar_notificaciones_antiguas_task en su lugar.
    Mantener por compatibilidad hacia atrás.
    """
    return limpiar_notificaciones_antiguas_task(days)


@shared_task
def enviar_resumen_notificaciones():
    """
    Enviar resumen de estadísticas de notificaciones a administradores.
    Se ejecuta diariamente para monitoreo del sistema.
    """
    try:
        from .signals import obtener_estadisticas_notificaciones
        from apps.users.models import User
        from django.core.mail import send_mail
        from django.conf import settings
        
        # Obtener estadísticas globales
        stats = obtener_estadisticas_notificaciones()
        
        # Obtener administradores para envío
        administradores = User.objects.filter(role='admin', email__isnull=False)
        
        if not administradores.exists():
            print("No hay administradores con email para enviar resumen")
            return {'enviados': 0, 'error': 'No hay administradores'}
        
        # Preparar mensaje
        mensaje = f"""
Resumen Diario de Notificaciones
{timezone.now().strftime('%d/%m/%Y %H:%M')}

ESTADÍSTICAS GLOBALES:
• Total notificaciones: {stats['total']}
• No leídas: {stats['no_leidas']}
• Leídas: {stats['leidas']} ({stats['porcentaje_leidas']}%)
• Archivadas: {stats['archivadas']}

Este es un resumen automático del sistema de notificaciones.

Saludos,
Sistema Académico
        """
        
        emails_enviados = 0
        for admin in administradores:
            try:
                send_mail(
                    subject=f'Resumen Diario de Notificaciones - {timezone.now().strftime("%d/%m/%Y")}',
                    message=mensaje,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@academic.com'),
                    recipient_list=[admin.email],
                    fail_silently=False,
                )
                emails_enviados += 1
            except Exception as e:
                print(f"Error enviando resumen a {admin.email}: {e}")
                continue
        
        resultado = {
            'emails_enviados': emails_enviados,
            'estadisticas': stats,
            'fecha_ejecucion': timezone.now().isoformat()
        }
        
        print(f"Resumen de notificaciones enviado a {emails_enviados} administradores")
        return resultado
        
    except Exception as e:
        error_msg = f"Error en tarea de resumen de notificaciones: {e}"
        print(error_msg)
        return {'error': error_msg, 'emails_enviados': 0}


@shared_task
def configurar_tareas_periodicas():
    """
    Configurar automáticamente las tareas periódicas en Celery Beat.
    Esta tarea se ejecuta al iniciar la aplicación para asegurar que
    todas las tareas periódicas estén configuradas correctamente.
    """
    try:
        from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule
        import json
        
        tareas_creadas = []
        
        # 1. Tarea semanal: Resumen para profesores (lunes a las 8:00 AM)
        schedule_semanal, created = CrontabSchedule.objects.get_or_create(
            minute=0,
            hour=8,
            day_of_week=1,  # Lunes
            day_of_month='*',
            month_of_year='*',
        )
        
        tarea_profesores, created = PeriodicTask.objects.get_or_create(
            crontab=schedule_semanal,
            name='Envío Semanal de Resumen a Profesores',
            task='apps.users.tasks.enviar_resumen_semanal_profesores',
            defaults={
                'enabled': True,
                'description': 'Envía resumen semanal de actividad académica a profesores'
            }
        )
        
        if created:
            tareas_creadas.append('Resumen semanal profesores')
        
        # 2. Tarea diaria: Limpieza de notificaciones (2:00 AM todos los días)
        schedule_diario, created = CrontabSchedule.objects.get_or_create(
            minute=0,
            hour=2,
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
        )
        
        tarea_limpieza, created = PeriodicTask.objects.get_or_create(
            crontab=schedule_diario,
            name='Limpieza Automática de Notificaciones Antiguas',
            task='apps.notificaciones.tasks.limpiar_notificaciones_antiguas_task',
            defaults={
                'enabled': True,
                'kwargs': json.dumps({'dias': 30}),
                'description': 'Archiva notificaciones leídas con más de 30 días'
            }
        )
        
        if created:
            tareas_creadas.append('Limpieza notificaciones')
        
        # 3. Tarea diaria: Resumen de notificaciones para admins (6:00 AM)
        schedule_resumen, created = CrontabSchedule.objects.get_or_create(
            minute=0,
            hour=6,
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
        )
        
        tarea_resumen, created = PeriodicTask.objects.get_or_create(
            crontab=schedule_resumen,
            name='Resumen Diario de Notificaciones',
            task='apps.notificaciones.tasks.enviar_resumen_notificaciones',
            defaults={
                'enabled': True,
                'description': 'Envía estadísticas diarias de notificaciones a administradores'
            }
        )
        
        if created:
            tareas_creadas.append('Resumen diario notificaciones')
        
        resultado = {
            'tareas_configuradas': len(tareas_creadas),
            'nuevas_tareas': tareas_creadas,
            'fecha_configuracion': timezone.now().isoformat()
        }
        
        mensaje = f"Configuración de tareas periódicas completada: {len(tareas_creadas)} tareas"
        if tareas_creadas:
            mensaje += f" (nuevas: {', '.join(tareas_creadas)})"
        
        print(mensaje)
        return resultado
        
    except Exception as e:
        error_msg = f"Error configurando tareas periódicas: {e}"
        print(error_msg)
        return {'error': error_msg, 'tareas_configuradas': 0} 