# services.py para la app common
# Aquí irá la lógica de negocio común y utilitaria.

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()
logger = logging.getLogger(__name__)


class EmailService:
    """
    Servicio para manejo de emails del sistema.
    Centraliza toda la lógica de envío de correos electrónicos.
    """
    
    @staticmethod  
    def send_welcome_email(user_or_id):
        """Enviar email de bienvenida a nuevo usuario."""
        # Manejar tanto objetos User como IDs
        if isinstance(user_or_id, int):
            try:
                user = User.objects.get(id=user_or_id)
            except User.DoesNotExist:
                logger.error(f"Usuario con ID {user_or_id} no encontrado")
                return False
        else:
            user = user_or_id
        
        subject = '¡Bienvenido al Sistema Académico!'
        message = f"""
        Hola {user.get_full_name() or user.username},
        
        ¡Te damos la bienvenida al Sistema Académico!
        
        Tu cuenta ha sido creada exitosamente con los siguientes datos:
        - Usuario: {user.username}
        - Email: {user.email}
        - Rol: {user.get_role_display()}
        
        Ya puedes iniciar sesión en el sistema y comenzar a usar todas las funcionalidades disponibles.
        
        Si tienes alguna pregunta, no dudes en contactar al administrador.
        
        ¡Que tengas un excelente día!
        
        Equipo del Sistema Académico
        """
        
        try:
            send_mail(
                subject=subject,
                message=message.strip(),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            logger.info(f"Email de bienvenida enviado a {user.email}")
            return True
        except Exception as e:
            logger.error(f"Error enviando email de bienvenida a {user.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_grade_notification_email(inscripcion, calificacion):
        """Enviar email de notificación de nueva calificación."""
        subject = f'Nueva Calificación - {inscripcion.materia.codigo}'
        message = f"""
        Hola {inscripcion.estudiante.get_full_name() or inscripcion.estudiante.username},
        
        Se ha publicado una nueva calificación en tu materia {inscripcion.materia.nombre}.
        
        Detalles de la calificación:
        - Materia: {inscripcion.materia.nombre} ({inscripcion.materia.codigo})
        - Tipo: {calificacion.get_tipo_display()}
        - Nota: {calificacion.nota}/5.0
        - Fecha: {calificacion.fecha}
        
        Puedes revisar más detalles ingresando al sistema.
        
        Saludos,
        Equipo del Sistema Académico
        """
        
        try:
            send_mail(
                subject=subject,
                message=message.strip(),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[inscripcion.estudiante.email],
                fail_silently=False,
            )
            logger.info(f"Email de calificación enviado a {inscripcion.estudiante.email}")
            return True
        except Exception as e:
            logger.error(f"Error enviando email de calificación: {str(e)}")
            return False
    
    @staticmethod
    def send_weekly_summary_email(profesor, summary_data):
        """Enviar email semanal con resumen académico al profesor."""
        subject = 'Resumen Semanal Académico'
        message = f"""
        Hola {profesor.get_full_name() or profesor.username},
        
        Te enviamos tu resumen académico semanal:
        
        Materias asignadas: {summary_data.get('total_materias', 0)}
        Estudiantes activos: {summary_data.get('total_estudiantes', 0)}
        Calificaciones pendientes: {summary_data.get('calificaciones_pendientes', 0)}
        
        Detalles por materia:
        """
        
        for materia_data in summary_data.get('materias', []):
            message += f"""
        - {materia_data['nombre']} ({materia_data['codigo']})
          Estudiantes: {materia_data['estudiantes']}
          Promedio: {materia_data.get('promedio', 'N/A')}
            """
        
        message += """
        
        Puedes revisar más detalles en el sistema.
        
        Saludos,
        Equipo del Sistema Académico
        """
        
        try:
            send_mail(
                subject=subject,
                message=message.strip(),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[profesor.email],
                fail_silently=False,
            )
            logger.info(f"Email de resumen semanal enviado a {profesor.email}")
            return True
        except Exception as e:
            logger.error(f"Error enviando email de resumen semanal: {str(e)}")
            return False
    
    @staticmethod
    def send_weekly_summary(profesor_id):
        """
        Enviar resumen semanal a un profesor específico por ID.
        Wrapper que genera el resumen y envía el email.
        """
        try:
            # Obtener el profesor
            from apps.users.models import User
            profesor = User.objects.get(id=profesor_id, role='profesor')
            
            # Generar resumen académico
            summary_data = AcademicSummaryService.generate_professor_summary(profesor_id)
            
            # Enviar email con resumen
            resultado = EmailService.send_weekly_summary_email(profesor, summary_data)
            
            return resultado
            
        except User.DoesNotExist:
            logger.error(f"Profesor con ID {profesor_id} no encontrado")
            return False
        except Exception as e:
            logger.error(f"Error enviando resumen semanal al profesor {profesor_id}: {str(e)}")
            return False


class AcademicSummaryService:
    """
    Servicio para generar resúmenes académicos.
    Utilizado para reportes y notificaciones periódicas.
    """
    
    @staticmethod
    def generate_professor_weekly_summary(profesor) -> Dict[str, Any]:
        """Generar resumen semanal para un profesor."""
        from apps.materias.models import Materia
        from apps.inscripciones.models import Inscripcion, Calificacion
        
        # Obtener materias del profesor
        materias = Materia.objects.filter(profesor=profesor, estado='activa')
        
        summary = {
            'profesor': profesor,
            'total_materias': materias.count(),
            'total_estudiantes': 0,
            'calificaciones_pendientes': 0,
            'materias': []
        }
        
        for materia in materias:
            # Obtener inscripciones activas
            inscripciones = Inscripcion.objects.filter(
                materia=materia,
                estado='activa'
            )
            
            # Calcular estadísticas de la materia
            estudiantes_count = inscripciones.count()
            summary['total_estudiantes'] += estudiantes_count
            
            # Calcular promedio de la materia
            calificaciones = Calificacion.objects.filter(
                inscripcion__in=inscripciones
            )
            
            promedio = None
            if calificaciones.exists():
                promedio = round(
                    sum(c.nota for c in calificaciones) / calificaciones.count(), 
                    2
                )
            
            # Contar calificaciones pendientes (inscripciones sin calificaciones)
            pendientes = inscripciones.filter(
                calificaciones__isnull=True
            ).count()
            summary['calificaciones_pendientes'] += pendientes
            
            summary['materias'].append({
                'codigo': materia.codigo,
                'nombre': materia.nombre,
                'estudiantes': estudiantes_count,
                'promedio': promedio,
                'calificaciones_pendientes': pendientes
            })
        
        return summary
    
    @staticmethod
    def generate_student_academic_summary(estudiante) -> Dict[str, Any]:
        """Generar resumen académico para un estudiante."""
        from apps.inscripciones.models import Inscripcion, Calificacion
        
        # Obtener todas las inscripciones del estudiante
        inscripciones = Inscripcion.objects.filter(estudiante=estudiante)
        
        summary = {
            'estudiante': estudiante,
            'total_materias': inscripciones.count(),
            'materias_aprobadas': 0,
            'materias_reprobadas': 0,
            'materias_activas': 0,
            'promedio_general': 0,
            'creditos_cursados': 0,
            'creditos_aprobados': 0,
            'materias': []
        }
        
        total_notas = []
        
        for inscripcion in inscripciones:
            # Obtener calificaciones de la inscripción
            calificaciones = Calificacion.objects.filter(inscripcion=inscripcion)
            
            promedio_materia = None
            estado_materia = inscripcion.estado
            
            if calificaciones.exists():
                # Calcular promedio ponderado si hay porcentajes
                if all(c.porcentaje for c in calificaciones):
                    promedio_materia = sum(
                        c.nota * (c.porcentaje / 100) for c in calificaciones
                    )
                else:
                    promedio_materia = sum(c.nota for c in calificaciones) / calificaciones.count()
                
                promedio_materia = round(promedio_materia, 2)
                total_notas.append(promedio_materia)
                
                # Determinar estado según la nota
                if promedio_materia >= 3.0:
                    if estado_materia == 'activa':
                        estado_materia = 'aprobada'
                else:
                    if estado_materia == 'activa':
                        estado_materia = 'reprobada'
            
            # Contar por estado
            if estado_materia == 'aprobada':
                summary['materias_aprobadas'] += 1
                summary['creditos_aprobados'] += inscripcion.materia.creditos
            elif estado_materia == 'reprobada':
                summary['materias_reprobadas'] += 1
            elif estado_materia == 'activa':
                summary['materias_activas'] += 1
            
            summary['creditos_cursados'] += inscripcion.materia.creditos
            
            summary['materias'].append({
                'codigo': inscripcion.materia.codigo,
                'nombre': inscripcion.materia.nombre,
                'creditos': inscripcion.materia.creditos,
                'promedio': promedio_materia,
                'estado': estado_materia,
                'periodo': inscripcion.periodo.nombre
            })
        
        # Calcular promedio general
        if total_notas:
            summary['promedio_general'] = round(
                sum(total_notas) / len(total_notas), 2
            )
        
        return summary
    
    @staticmethod
    def generate_professor_summary(profesor_id: int) -> Dict[str, Any]:
        """Generar resumen académico para un profesor específico."""
        from apps.users.models import User
        from apps.materias.models import Materia
        from apps.inscripciones.models import Inscripcion, Calificacion
        
        try:
            profesor = User.objects.get(id=profesor_id, role='profesor')
        except User.DoesNotExist:
            logger.warning(f"Profesor con ID {profesor_id} no encontrado")
            # Retornar un resumen vacío en lugar de error
            return {
                'profesor_id': profesor_id,
                'profesor_nombre': f'Usuario {profesor_id} (no encontrado)',
                'total_materias': 0,
                'total_estudiantes': 0,
                'total_students': 0,
                'promedio_general': 0.0,
                'materias_detalle': [],
                'subjects': [],
                'recent_grades': [],
                'error': 'Profesor no encontrado'
            }
        
        # Obtener materias del profesor
        materias = Materia.objects.filter(profesor=profesor)
        
        summary = {
            'profesor_id': profesor_id,
            'profesor_nombre': profesor.get_full_name() or profesor.username,
            'total_materias': materias.count(),
            'total_estudiantes': 0,
            'total_students': 0,  # Alias para compatibilidad con pruebas
            'promedio_general': 0.0,
            'materias_detalle': [],
            'subjects': [],  # Alias para materias_detalle
            'recent_grades': []  # Calificaciones recientes
        }
        
        total_notas = []
        estudiantes_unicos = set()  # Para contar estudiantes únicos
        
        for materia in materias:
            # Obtener inscripciones de la materia
            inscripciones = Inscripcion.objects.filter(materia=materia)
            estudiantes_count = inscripciones.count()
            
            # Agregar estudiantes únicos al set
            for inscripcion in inscripciones:
                estudiantes_unicos.add(inscripcion.estudiante.id)
            
            # Calcular promedio de la materia
            calificaciones = Calificacion.objects.filter(
                inscripcion__in=inscripciones
            )
            
            promedio_materia = 0.0
            if calificaciones.exists():
                notas = [c.nota for c in calificaciones]
                promedio_materia = sum(notas) / len(notas)
                total_notas.extend(notas)
            
            # Calificaciones recientes para esta materia específica
            calificaciones_materia = calificaciones.order_by('-created_at')[:3]
            recent_grades_materia = []
            for cal in calificaciones_materia:
                recent_grades_materia.append({
                    'nota': float(cal.nota),
                    'tipo': cal.tipo,
                    'fecha': cal.created_at.date() if hasattr(cal, 'created_at') else None
                })
            
            materia_info = {
                'codigo': materia.codigo,
                'nombre': materia.nombre,
                'name': materia.nombre,  # Alias para compatibilidad con pruebas
                'estudiantes': estudiantes_count,
                'enrolled_students': estudiantes_count,  # Alias para compatibilidad con pruebas
                'promedio': round(promedio_materia, 2),
                'creditos': materia.creditos,
                'recent_grades': len(recent_grades_materia)  # Número de calificaciones recientes
            }
            
            summary['materias_detalle'].append(materia_info)
            summary['subjects'].append(materia_info)  # Mantener sincronizado
            
            # Agregar calificaciones recientes a recent_grades
            calificaciones_recientes = calificaciones.order_by('-created_at')[:5]
            for cal in calificaciones_recientes:
                summary['recent_grades'].append({
                    'materia': materia.codigo,
                    'nota': float(cal.nota),
                    'tipo': cal.tipo,
                    'fecha': cal.created_at.date() if hasattr(cal, 'created_at') else None
                })
        
        # Calcular promedio general
        if total_notas:
            summary['promedio_general'] = round(sum(total_notas) / len(total_notas), 2)
        
        # Actualizar conteo de estudiantes únicos
        summary['total_estudiantes'] = len(estudiantes_unicos)
        summary['total_students'] = len(estudiantes_unicos)
        
        return summary


class NotificationCleanupService:
    """
    Servicio para limpieza de notificaciones antiguas.
    Ayuda a mantener la base de datos optimizada.
    """
    
    @staticmethod
    def cleanup_old_notifications(days: int = 90, preserve_read: bool = False, batch_size: int = None, return_stats: bool = False):
        """
        Limpiar notificaciones antiguas.
        
        Args:
            days: Días de antigüedad para considerar notificaciones como viejas
            preserve_read: Si True, preserva las notificaciones leídas
            batch_size: Tamaño del lote para procesamiento (ignorado por compatibilidad)
            return_stats: Si True, devuelve estadísticas completas; si False, solo el count
            
        Returns:
            int o Dict según return_stats
        """
        from apps.notificaciones.models import Notificacion
        
        fecha_limite = timezone.now() - timedelta(days=days)
        
        # Obtener notificaciones a eliminar según preserve_read
        if preserve_read:
            # Solo eliminar las no leídas antiguas si preserve_read=True
            notificaciones_antiguas = Notificacion.objects.filter(
                fecha_creacion__lt=fecha_limite,
                estado='no_leida',
                leida=False
            )
        else:
            # Eliminar las leídas/archivadas antiguas
            # Considerar tanto el campo estado como el campo leida booleano
            from django.db.models import Q
            notificaciones_antiguas = Notificacion.objects.filter(
                fecha_creacion__lt=fecha_limite
            ).filter(
                Q(estado__in=['leida', 'archivada']) | Q(leida=True)
            )
        
        # Contar por tipo antes de eliminar
        stats = {
            'total_eliminadas': 0,
            'por_tipo': {},
            'por_usuario': {},
            'fecha_limite': fecha_limite
        }
        
        for notificacion in notificaciones_antiguas:
            # Contar por tipo
            tipo = notificacion.tipo
            if tipo not in stats['por_tipo']:
                stats['por_tipo'][tipo] = 0
            stats['por_tipo'][tipo] += 1
            
            # Contar por usuario
            usuario = notificacion.usuario.username
            if usuario not in stats['por_usuario']:
                stats['por_usuario'][usuario] = 0
            stats['por_usuario'][usuario] += 1
            
            stats['total_eliminadas'] += 1
        
        # Eliminar las notificaciones
        notificaciones_antiguas.delete()
        
        logger.info(f"Limpieza de notificaciones completada: {stats['total_eliminadas']} eliminadas")
        
        # Devolver según lo solicitado
        if return_stats:
            return stats
        else:
            return stats['total_eliminadas']
    
    @staticmethod
    def cleanup_unread_notifications(days_old: int = 180) -> Dict[str, int]:
        """
        Limpiar notificaciones no leídas muy antiguas.
        Solo para casos excepcionales donde hay notificaciones muy viejas sin leer.
        """
        from apps.notificaciones.models import Notificacion
        
        fecha_limite = timezone.now() - timedelta(days=days_old)
        
        notificaciones_muy_antiguas = Notificacion.objects.filter(
            fecha_creacion__lt=fecha_limite,
            estado='no_leida'
        )
        
        count = notificaciones_muy_antiguas.count()
        notificaciones_muy_antiguas.delete()
        
        logger.warning(f"Limpieza de notificaciones no leídas muy antiguas: {count} eliminadas")
        
        return {
            'total_eliminadas': count,
            'fecha_limite': fecha_limite,
            'tipo': 'no_leidas_muy_antiguas'
        }
    
    @staticmethod
    def get_cleanup_statistics() -> Dict[str, Any]:
        """Obtener estadísticas para determinar si es necesaria una limpieza."""
        from apps.notificaciones.models import Notificacion
        
        ahora = timezone.now()
        hace_30_dias = ahora - timedelta(days=30)
        hace_90_dias = ahora - timedelta(days=90)
        hace_180_dias = ahora - timedelta(days=180)
        
        stats = {
            'total_notificaciones': Notificacion.objects.count(),
            'ultimos_30_dias': Notificacion.objects.filter(
                fecha_creacion__gte=hace_30_dias
            ).count(),
            'mas_de_90_dias': Notificacion.objects.filter(
                fecha_creacion__lt=hace_90_dias
            ).count(),
            'mas_de_180_dias': Notificacion.objects.filter(
                fecha_creacion__lt=hace_180_dias
            ).count(),
            'no_leidas_totales': Notificacion.objects.filter(
                estado='no_leida'
            ).count(),
            'no_leidas_mas_30_dias': Notificacion.objects.filter(
                estado='no_leida',
                fecha_creacion__lt=hace_30_dias
            ).count(),
        }
        
        # Recomendaciones de limpieza
        stats['recomendaciones'] = []
        
        if stats['mas_de_90_dias'] > 1000:
            stats['recomendaciones'].append(
                'Considerar limpieza de notificaciones de más de 90 días'
            )
        
        if stats['no_leidas_mas_30_dias'] > 100:
            stats['recomendaciones'].append(
                'Hay muchas notificaciones no leídas de más de 30 días'
            )
        
        return stats 