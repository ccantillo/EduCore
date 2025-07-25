# tasks.py para la app users
# Tareas en background - envío de emails de bienvenida, limpieza de sesiones, etc.

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags


@shared_task
def enviar_email_bienvenida(user_id):
    """
    Enviar email de bienvenida a un usuario recién creado.
    Se ejecuta de forma asíncrona para no bloquear la creación del usuario.
    """
    try:
        from .models import User
        user = User.objects.get(id=user_id)
        
        # Preparar contexto para el template
        context = {
            'usuario': user,
            'nombre_completo': user.get_full_name() or user.username,
            'rol': user.get_role_display(),
            'sitio_web': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
        }
        
        # Renderizar template HTML (si existe)
        try:
            html_message = render_to_string('emails/bienvenida.html', context)
            plain_message = strip_tags(html_message)
        except:
            # Fallback a mensaje plano si no existe el template
            plain_message = f"""
¡Bienvenido/a {context['nombre_completo']}!

Tu cuenta ha sido creada exitosamente en el Sistema Académico.

Detalles de tu cuenta:
- Usuario: {user.username}
- Email: {user.email}
- Rol: {context['rol']}

Puedes acceder al sistema en: {context['sitio_web']}

¡Esperamos que tengas una excelente experiencia!

Saludos,
Equipo del Sistema Académico
            """
            html_message = None
        
        # Enviar email
        send_mail(
            subject='¡Bienvenido/a al Sistema Académico!',
            message=plain_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@academic.com'),
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        print(f"Email de bienvenida enviado exitosamente a {user.email}")
        return True
        
    except Exception as e:
        print(f"Error al enviar email de bienvenida: {e}")
        return False


@shared_task
def enviar_resumen_semanal_profesores():
    """
    Enviar resumen semanal a todos los profesores con su actividad académica.
    Se ejecuta automáticamente cada semana via Celery Beat.
    """
    try:
        from .models import User
        from apps.materias.models import Materia
        from apps.inscripciones.models import Inscripcion, Calificacion
        from django.utils import timezone
        from datetime import timedelta
        
        # Obtener fecha de inicio de la semana (lunes)
        hoy = timezone.now().date()
        inicio_semana = hoy - timedelta(days=hoy.weekday())
        fin_semana = inicio_semana + timedelta(days=6)
        
        profesores = User.objects.filter(role='profesor')
        emails_enviados = 0
        
        for profesor in profesores:
            try:
                # Obtener materias del profesor
                materias = Materia.objects.filter(profesor=profesor)
                
                # Estadísticas de la semana
                inscripciones_nuevas = Inscripcion.objects.filter(
                    materia__in=materias,
                    fecha_inscripcion__date__range=[inicio_semana, fin_semana]
                ).count()
                
                calificaciones_publicadas = Calificacion.objects.filter(
                    inscripcion__materia__in=materias,
                    fecha_calificacion__date__range=[inicio_semana, fin_semana]
                ).count()
                
                total_estudiantes = Inscripcion.objects.filter(
                    materia__in=materias,
                    estado='activa'
                ).count()
                
                # Preparar contexto para el email
                context = {
                    'profesor': profesor,
                    'nombre_completo': profesor.get_full_name() or profesor.username,
                    'periodo_inicio': inicio_semana.strftime('%d/%m/%Y'),
                    'periodo_fin': fin_semana.strftime('%d/%m/%Y'),
                    'materias': materias,
                    'inscripciones_nuevas': inscripciones_nuevas,
                    'calificaciones_publicadas': calificaciones_publicadas,
                    'total_estudiantes': total_estudiantes,
                }
                
                # Solo enviar si hay actividad o materias asignadas
                if materias.exists():
                    # Renderizar mensaje
                    plain_message = f"""
Resumen Semanal Académico
{inicio_semana.strftime('%d/%m/%Y')} - {fin_semana.strftime('%d/%m/%Y')}

Estimado/a Prof. {context['nombre_completo']},

Aquí tienes el resumen de actividad de tus materias esta semana:

MATERIAS ASIGNADAS: {materias.count()}
{chr(10).join([f"• {materia.nombre} ({materia.codigo})" for materia in materias[:5]])}
{"..." if materias.count() > 5 else ""}

ESTADÍSTICAS DE LA SEMANA:
• Nuevas inscripciones: {inscripciones_nuevas}
• Calificaciones publicadas: {calificaciones_publicadas}
• Total estudiantes activos: {total_estudiantes}

¡Que tengas una excelente semana!

Saludos,
Sistema Académico
                    """
                    
                    # Enviar email
                    send_mail(
                        subject=f'Resumen Semanal Académico - {inicio_semana.strftime("%d/%m")} al {fin_semana.strftime("%d/%m")}',
                        message=plain_message,
                        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@academic.com'),
                        recipient_list=[profesor.email],
                        fail_silently=False,
                    )
                    
                    emails_enviados += 1
                    
            except Exception as e:
                print(f"Error al enviar resumen semanal a {profesor.email}: {e}")
                continue
        
        print(f"Resumen semanal enviado a {emails_enviados} profesores")
        return emails_enviados
        
    except Exception as e:
        print(f"Error en tarea de resumen semanal: {e}")
        return 0 