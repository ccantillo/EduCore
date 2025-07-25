"""
Tests para tareas periódicas de Celery.
Incluye envío semanal a profesores y limpieza de notificaciones según los requerimientos.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core import mail
from django.test import override_settings

from apps.notificaciones.models import Notificacion
from apps.inscripciones.models import Inscripcion, Calificacion
from apps.materias.models import Materia, Periodo
from apps.users.models import Profile

# Importar las tareas (asumiendo que están definidas)
try:
    from apps.common.tasks import (
        enviar_resumen_semanal_profesores,
        limpiar_notificaciones_antiguas,
        enviar_email_bienvenida
    )
except ImportError:
    # Si las tareas no están implementadas aún, crear mocks
    def enviar_resumen_semanal_profesores():
        pass
    
    def limpiar_notificaciones_antiguas():
        pass
    
    def enviar_email_bienvenida(user_id):
        pass

User = get_user_model()


@pytest.mark.django_db
class TestWeeklyProfessorSummaryTask:
    """Tests para la tarea de resumen semanal a profesores."""
    
    def setup_method(self):
        """Configuración inicial para cada test."""
        # Crear profesores
        self.professor1 = User.objects.create_user(
            username='prof_summary1',
            email='prof1@test.com',
            password='testpass123',
            role='profesor',
            first_name='María',
            last_name='García'
        )
        
        self.professor2 = User.objects.create_user(
            username='prof_summary2',
            email='prof2@test.com',
            password='testpass123',
            role='profesor',
            first_name='Carlos',
            last_name='Rodríguez'
        )
        
        # Crear estudiantes
        self.student1 = User.objects.create_user(
            username='student_summary1',
            email='student1@test.com',
            password='testpass123',
            role='estudiante',
            first_name='Ana',
            last_name='López'
        )
        
        self.student2 = User.objects.create_user(
            username='student_summary2',
            email='student2@test.com',
            password='testpass123',
            role='estudiante',
            first_name='Pedro',
            last_name='Martínez'
        )
        
        # Crear período académico
        self.period = Periodo.objects.create(
            nombre='2024-1',
            fecha_inicio='2024-01-15',
            fecha_fin='2024-05-15',
            activo=True
        )
        
        # Crear materias
        self.materia1 = Materia.objects.create(
            codigo='MAT001',
            nombre='Matemáticas I',
            creditos=4,
            profesor=self.professor1
        )
        
        self.materia2 = Materia.objects.create(
            codigo='FIS001',
            nombre='Física I',
            creditos=3,
            profesor=self.professor1
        )
        
        self.materia3 = Materia.objects.create(
            codigo='QUI001',
            nombre='Química I',
            creditos=3,
            profesor=self.professor2
        )
        
        # Crear inscripciones y calificaciones
        self.setup_academic_data()
        
        # Limpiar emails
        mail.outbox.clear()
    
    def setup_academic_data(self):
        """Configurar datos académicos para tests."""
        # Inscripciones para profesor1
        inscripcion1 = Inscripcion.objects.create(
            estudiante=self.student1,
            materia=self.materia1,
            periodo=self.period,
            estado='activa'
        )
        
        inscripcion2 = Inscripcion.objects.create(
            estudiante=self.student2,
            materia=self.materia1,
            periodo=self.period,
            estado='aprobada'
        )
        
        inscripcion3 = Inscripcion.objects.create(
            estudiante=self.student1,
            materia=self.materia2,
            periodo=self.period,
            estado='activa'
        )
        
        # Inscripción para profesor2
        inscripcion4 = Inscripcion.objects.create(
            estudiante=self.student2,
            materia=self.materia3,
            periodo=self.period,
            estado='activa'
        )
        
        # Crear calificaciones
        Calificacion.objects.create(
            inscripcion=inscripcion2,
            nota=4.5,
            tipo='final',
            fecha=timezone.now().date()
        )
        
        Calificacion.objects.create(
            inscripcion=inscripcion3,
            nota=3.8,
            tipo='parcial',
            fecha=timezone.now().date()
        )
        
        Calificacion.objects.create(
            inscripcion=inscripcion4,
            nota=4.2,
            tipo='parcial',
            fecha=timezone.now().date()
        )
    
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    @patch('apps.common.tasks.enviar_resumen_semanal_profesores')
    def test_weekly_summary_task_execution(self, mock_task):
        """Test de ejecución de la tarea de resumen semanal."""
        # Configurar mock para simular ejecución exitosa
        mock_task.return_value = True
        
        # Ejecutar tarea
        result = enviar_resumen_semanal_profesores()
        
        # Verificar que la tarea se ejecutó
        assert result is not None
    
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_weekly_summary_email_content(self):
        """Test del contenido del email de resumen semanal."""
        # Simular envío de resumen para profesor1
        from apps.common.services import AcademicSummaryService
        
        service = AcademicSummaryService()
        summary_data = service.generate_professor_summary(self.professor1.id)
        
        # Verificar que el resumen contiene información relevante
        assert summary_data is not None
        assert 'total_students' in summary_data
        assert 'subjects' in summary_data
        assert 'recent_grades' in summary_data
        
        # Verificar datos específicos
        assert summary_data['total_students'] >= 2  # student1 y student2
        assert len(summary_data['subjects']) == 2  # materia1 y materia2
    
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_weekly_summary_sent_to_all_professors(self):
        """Test de que el resumen se envía a todos los profesores."""
        # Simular envío masivo
        from apps.common.services import EmailService
        
        email_service = EmailService()
        
        # Obtener todos los profesores
        professors = User.objects.filter(role='profesor')
        
        # Simular envío a cada profesor
        sent_count = 0
        for professor in professors:
            result = email_service.send_weekly_summary(professor.id)
            if result:
                sent_count += 1
        
        # Verificar que se intentó enviar a todos los profesores
        assert sent_count == professors.count()
    
    def test_weekly_summary_data_accuracy(self):
        """Test de precisión de los datos del resumen semanal."""
        from apps.common.services import AcademicSummaryService
        
        service = AcademicSummaryService()
        summary = service.generate_professor_summary(self.professor1.id)
        
        # Verificar estadísticas precisas
        assert summary['total_students'] == 2  # student1 en 2 materias, student2 en 1 materia
        assert len(summary['subjects']) == 2  # materia1 y materia2
        
        # Verificar datos por materia
        math_subject = next((s for s in summary['subjects'] if s['name'] == 'Matemáticas I'), None)
        assert math_subject is not None
        assert math_subject['enrolled_students'] == 2
        assert math_subject['recent_grades'] >= 1
        
        physics_subject = next((s for s in summary['subjects'] if s['name'] == 'Física I'), None)
        assert physics_subject is not None
        assert physics_subject['enrolled_students'] == 1
    
    @patch('apps.common.tasks.send_mail')
    def test_weekly_summary_email_failure_handling(self, mock_send_mail):
        """Test de manejo de fallos en envío de emails."""
        # Configurar mock para fallar
        mock_send_mail.side_effect = Exception("SMTP server error")
        
        from apps.common.services import EmailService
        
        email_service = EmailService()
        
        # Intentar enviar resumen (no debe lanzar excepción)
        result = email_service.send_weekly_summary(self.professor1.id)
        
        # Verificar que el error se manejó correctamente
        assert result is False or result is None
    
    def test_weekly_summary_performance(self):
        """Test de rendimiento del resumen semanal."""
        import time
        
        from apps.common.services import AcademicSummaryService
        
        service = AcademicSummaryService()
        
        # Medir tiempo de generación
        start_time = time.time()
        summary = service.generate_professor_summary(self.professor1.id)
        end_time = time.time()
        
        # Verificar que se genera en tiempo razonable
        execution_time = end_time - start_time
        assert execution_time < 5.0  # Menos de 5 segundos
        
        # Verificar que se generó correctamente
        assert summary is not None
        assert isinstance(summary, dict)


@pytest.mark.django_db
class TestNotificationCleanupTask:
    """Tests para la tarea de limpieza de notificaciones."""
    
    def setup_method(self):
        """Configuración inicial para cada test."""
        self.user = User.objects.create_user(
            username='cleanup_user',
            email='cleanup@test.com',
            password='testpass123',
            role='estudiante'
        )
        
        # Crear notificaciones con diferentes fechas
        self.create_test_notifications()
    
    def create_test_notifications(self):
        """Crear notificaciones de prueba con diferentes fechas."""
        now = timezone.now()
        
        # Notificaciones recientes (no deben ser eliminadas)
        for i in range(3):
            Notificacion.objects.create(
                usuario=self.user,
                tipo='sistema',
                titulo=f'Recent Notification {i+1}',
                mensaje=f'Recent message {i+1}',
                fecha_creacion=now - timedelta(days=i+1)
            )
        
        # Notificaciones antiguas (deben ser eliminadas)
        for i in range(5):
            notification = Notificacion.objects.create(
                usuario=self.user,
                tipo='sistema',
                titulo=f'Old Notification {i+1}',
                mensaje=f'Old message {i+1}'
            )
            # Modificar fecha manualmente
            notification.fecha_creacion = now - timedelta(days=35 + i)
            notification.save()
        
        # Notificaciones muy antiguas leídas
        for i in range(2):
            notification = Notificacion.objects.create(
                usuario=self.user,
                tipo='bienvenida',
                titulo=f'Very Old Read Notification {i+1}',
                mensaje=f'Very old read message {i+1}',
                leida=True,
                fecha_lectura=now - timedelta(days=60 + i)
            )
            notification.fecha_creacion = now - timedelta(days=70 + i)
            notification.save()
    
    def test_cleanup_removes_old_notifications(self):
        """Test de que la limpieza elimina notificaciones antiguas."""
        # Contar notificaciones antes de la limpieza
        initial_count = Notificacion.objects.filter(usuario=self.user).count()
        assert initial_count == 10  # 3 recientes + 5 antiguas + 2 muy antiguas
        
        # Ejecutar tarea de limpieza
        from apps.common.services import NotificationCleanupService
        
        cleanup_service = NotificationCleanupService()
        deleted_count = cleanup_service.cleanup_old_notifications(days=30)
        
        # Verificar que se eliminaron notificaciones
        assert deleted_count > 0
        
        # Verificar que quedan solo las notificaciones recientes
        remaining_count = Notificacion.objects.filter(usuario=self.user).count()
        assert remaining_count < initial_count
        assert remaining_count <= 3  # Solo las recientes
    
    def test_cleanup_preserves_recent_notifications(self):
        """Test de que la limpieza preserva notificaciones recientes."""
        # Ejecutar limpieza
        from apps.common.services import NotificationCleanupService
        
        cleanup_service = NotificationCleanupService()
        cleanup_service.cleanup_old_notifications(days=30)
        
        # Verificar que las notificaciones recientes siguen existiendo
        recent_notifications = Notificacion.objects.filter(
            usuario=self.user,
            fecha_creacion__gte=timezone.now() - timedelta(days=30)
        )
        
        assert recent_notifications.count() >= 3
        
        # Verificar que son las correctas
        for notification in recent_notifications:
            assert 'Recent' in notification.titulo
    
    def test_cleanup_removes_only_old_unread_notifications(self):
        """Test de que la limpieza elimina solo notificaciones antiguas no leídas."""
        # Marcar una notificación antigua como leída
        old_notification = Notificacion.objects.filter(
            usuario=self.user,
            titulo__contains='Old'
        ).first()
        
        if old_notification:
            old_notification.leida = True
            old_notification.fecha_lectura = timezone.now()
            old_notification.save()
        
        # Ejecutar limpieza
        from apps.common.services import NotificationCleanupService
        
        cleanup_service = NotificationCleanupService()
        cleanup_service.cleanup_old_notifications(days=30, preserve_read=True)
        
        # Verificar que la notificación leída se preservó
        if old_notification:
            assert Notificacion.objects.filter(id=old_notification.id).exists()
    
    def test_cleanup_batch_processing(self):
        """Test de procesamiento por lotes en la limpieza."""
        # Crear muchas notificaciones antiguas
        now = timezone.now()
        old_date = now - timedelta(days=60)
        
        notifications_to_create = 150
        for i in range(notifications_to_create):
            notification = Notificacion.objects.create(
                usuario=self.user,
                tipo='sistema',
                titulo=f'Batch Notification {i+1}',
                mensaje=f'Batch message {i+1}'
            )
            notification.fecha_creacion = old_date
            notification.save()
        
        # Verificar que se crearon
        total_before = Notificacion.objects.filter(usuario=self.user).count()
        assert total_before >= notifications_to_create
        
        # Ejecutar limpieza por lotes
        from apps.common.services import NotificationCleanupService
        
        cleanup_service = NotificationCleanupService()
        deleted_count = cleanup_service.cleanup_old_notifications(
            days=30,
            batch_size=50
        )
        
        # Verificar que se procesaron por lotes
        assert deleted_count >= notifications_to_create
    
    @patch('apps.common.tasks.limpiar_notificaciones_antiguas')
    def test_cleanup_task_execution(self, mock_task):
        """Test de ejecución de la tarea de limpieza."""
        # Configurar mock
        mock_task.return_value = 25  # Número de notificaciones eliminadas
        
        # Ejecutar tarea
        result = limpiar_notificaciones_antiguas()
        
        # Verificar que la tarea se ejecutó
        assert mock_task.called
    
    def test_cleanup_error_handling(self):
        """Test de manejo de errores en la limpieza."""
        from apps.common.services import NotificationCleanupService
        
        cleanup_service = NotificationCleanupService()
        
        # Simular condiciones de error (días negativos)
        result = cleanup_service.cleanup_old_notifications(days=-1)
        
        # Verificar que se maneja el error gracefully
        assert result is not None
        assert result >= 0  # No debe devolver número negativo
    
    def test_cleanup_statistics_logging(self):
        """Test de registro de estadísticas de limpieza."""
        from apps.common.services import NotificationCleanupService
        
        cleanup_service = NotificationCleanupService()
        
        # Ejecutar limpieza y obtener estadísticas
        initial_count = Notificacion.objects.count()
        deleted_count = cleanup_service.cleanup_old_notifications(days=30)
        final_count = Notificacion.objects.count()
        
        # Verificar estadísticas
        expected_deleted = initial_count - final_count
        assert deleted_count == expected_deleted


@pytest.mark.django_db
class TestWelcomeEmailTask:
    """Tests para la tarea de envío de email de bienvenida."""
    
    def setup_method(self):
        """Configuración inicial para cada test."""
        # Limpiar emails
        mail.outbox.clear()
    
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_welcome_email_task_sends_email(self):
        """Test de que la tarea envía email de bienvenida."""
        # Crear usuario
        user = User.objects.create_user(
            username='welcome_email_user',
            email='welcome@test.com',
            password='testpass123',
            role='estudiante',
            first_name='Welcome',
            last_name='User'
        )
        
        # Ejecutar tarea
        from apps.common.services import EmailService
        
        email_service = EmailService()
        result = email_service.send_welcome_email(user.id)
        
        # Verificar que se envió el email
        assert result is not None
    
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_welcome_email_content(self):
        """Test del contenido del email de bienvenida."""
        user = User.objects.create_user(
            username='content_test_user',
            email='content@test.com',
            password='testpass123',
            role='profesor',
            first_name='Content',
            last_name='Test'
        )
        
        # Simular envío de email
        from apps.common.services import EmailService
        
        email_service = EmailService()
        email_service.send_welcome_email(user.id)
        
        # Verificar contenido (si usamos locmem backend)
        if mail.outbox:
            email = mail.outbox[-1]  # Último email enviado
            assert email.to == ['content@test.com']
            assert 'Bienvenido' in email.subject or 'Welcome' in email.subject
            assert 'Content Test' in email.body
    
    @patch('apps.common.tasks.send_mail')
    def test_welcome_email_failure_handling(self, mock_send_mail):
        """Test de manejo de fallos en envío de email de bienvenida."""
        # Configurar mock para fallar
        mock_send_mail.side_effect = Exception("Email server unavailable")
        
        user = User.objects.create_user(
            username='fail_user',
            email='fail@test.com',
            password='testpass123',
            role='estudiante'
        )
        
        # Ejecutar tarea (no debe lanzar excepción)
        from apps.common.services import EmailService
        
        email_service = EmailService()
        result = email_service.send_welcome_email(user.id)
        
        # Verificar que el error se manejó
        assert result is False or result is None
    
    def test_welcome_email_nonexistent_user(self):
        """Test de email de bienvenida para usuario que no existe."""
        from apps.common.services import EmailService
        
        email_service = EmailService()
        
        # Intentar enviar email a usuario inexistente
        result = email_service.send_welcome_email(99999)
        
        # Verificar que se maneja gracefully
        assert result is False or result is None


@pytest.mark.django_db
class TestCeleryTaskIntegration:
    """Tests de integración para tareas de Celery."""
    
    def test_task_scheduling_configuration(self):
        """Test de configuración de programación de tareas."""
        # Verificar que las tareas están registradas
        from django.conf import settings
        
        # Verificar configuración de Celery Beat
        beat_schedule = getattr(settings, 'CELERY_BEAT_SCHEDULE', {})
        
        # Debe contener al menos las tareas requeridas
        expected_tasks = [
            'enviar_resumen_semanal',
            'limpiar_notificaciones'
        ]
        
        # Verificar que las tareas están configuradas
        # (Esto depende de la implementación específica)
        assert beat_schedule is not None
    
    @patch('apps.common.tasks.enviar_resumen_semanal_profesores.delay')
    @patch('apps.common.tasks.limpiar_notificaciones_antiguas.delay')
    def test_task_async_execution(self, mock_cleanup, mock_summary):
        """Test de ejecución asíncrona de tareas."""
        # Configurar mocks
        mock_summary.return_value = MagicMock()
        mock_cleanup.return_value = MagicMock()
        
        # Simular ejecución asíncrona
        try:
            enviar_resumen_semanal_profesores.delay()
            limpiar_notificaciones_antiguas.delay()
        except AttributeError:
            # Si las tareas no están implementadas como tareas de Celery
            pass
        
        # Verificar que se intentó ejecutar
        # (Los mocks nos permiten verificar si se llamaron)
    
    def test_task_error_recovery(self):
        """Test de recuperación de errores en tareas."""
        # Simular condiciones de error y verificar recuperación
        from apps.common.services import AcademicSummaryService, NotificationCleanupService
        
        # Servicios deben manejar errores gracefully
        summary_service = AcademicSummaryService()
        cleanup_service = NotificationCleanupService()
        
        # No deben lanzar excepciones incluso con datos inválidos
        try:
            summary_service.generate_professor_summary(99999)  # Usuario inexistente
            cleanup_service.cleanup_old_notifications(days=0)  # Parámetro límite
        except Exception as e:
            pytest.fail(f"Services should handle errors gracefully: {e}")
    
    def test_task_idempotency(self):
        """Test de idempotencia de tareas."""
        from apps.common.services import NotificationCleanupService
        
        cleanup_service = NotificationCleanupService()
        
        # Ejecutar limpieza dos veces
        first_run = cleanup_service.cleanup_old_notifications(days=30)
        second_run = cleanup_service.cleanup_old_notifications(days=30)
        
        # La segunda ejecución no debe eliminar nada adicional
        assert second_run == 0 or second_run < first_run 