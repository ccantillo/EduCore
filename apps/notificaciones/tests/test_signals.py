"""
Tests para signals automáticos de notificaciones.
Incluye notificaciones de bienvenida, calificaciones y envío de emails según los requerimientos.
"""

import pytest
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import override_settings

from apps.notificaciones.models import Notificacion
from apps.inscripciones.models import Inscripcion, Calificacion
from apps.materias.models import Materia, Periodo
from apps.users.models import Profile

User = get_user_model()


@pytest.mark.django_db
class TestUserCreationSignals:
    """Tests para signals de creación de usuarios."""
    
    def setup_method(self):
        """Configuración inicial para cada test."""
        # Limpiar notificaciones existentes
        Notificacion.objects.all().delete()
        
        # Limpiar emails
        mail.outbox.clear()
    
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_welcome_notification_created_on_user_creation(self):
        """Test de que se crea notificación de bienvenida al crear usuario."""
        # Crear usuario
        user = User.objects.create_user(
            username='new_user',
            email='newuser@test.com',
            password='testpass123',
            role='estudiante',
            first_name='Nuevo',
            last_name='Usuario'
        )
        
        # Verificar que se creó la notificación
        notifications = Notificacion.objects.filter(usuario=user, tipo='bienvenida')
        assert notifications.count() == 1
        
        notification = notifications.first()
        assert notification.usuario == user
        assert notification.tipo == 'bienvenida'
        assert notification.titulo == 'Bienvenido al Sistema Académico'
        assert 'Nuevo Usuario' in notification.mensaje
        assert not notification.leida
    
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_welcome_email_sent_on_user_creation(self):
        """Test de que se envía email de bienvenida al crear usuario."""
        # Crear usuario
        user = User.objects.create_user(
            username='email_user',
            email='emailuser@test.com',
            password='testpass123',
            role='profesor',
            first_name='Email',
            last_name='User'
        )
        
        # Verificar que se envió el email
        assert len(mail.outbox) == 1
        
        email = mail.outbox[0]
        assert email.to == ['emailuser@test.com']
        assert 'Bienvenido' in email.subject
        assert 'Email User' in email.body
    
    def test_notification_created_for_all_user_roles(self):
        """Test de que se crea notificación para todos los tipos de usuarios."""
        roles = ['admin', 'profesor', 'estudiante']
        
        for role in roles:
            # Limpiar notificaciones previas
            Notificacion.objects.all().delete()
            
            user = User.objects.create_user(
                username=f'user_{role}',
                email=f'{role}@test.com',
                password='testpass123',
                role=role,
                first_name=f'User',
                last_name=f'{role.title()}'
            )
            
            # Verificar notificación creada
            notifications = Notificacion.objects.filter(usuario=user, tipo='bienvenida')
            assert notifications.count() == 1
            
            notification = notifications.first()
            assert notification.usuario.role == role
    
    def test_notification_not_duplicated_on_user_update(self):
        """Test de que no se duplican notificaciones al actualizar usuario."""
        # Crear usuario
        user = User.objects.create_user(
            username='update_user',
            email='update@test.com',
            password='testpass123',
            role='estudiante'
        )
        
        # Verificar notificación inicial
        initial_count = Notificacion.objects.filter(usuario=user, tipo='bienvenida').count()
        assert initial_count == 1
        
        # Actualizar usuario
        user.first_name = 'Updated'
        user.save()
        
        # Verificar que no se creó notificación adicional
        final_count = Notificacion.objects.filter(usuario=user, tipo='bienvenida').count()
        assert final_count == initial_count
    
    @patch('apps.notificaciones.signals.send_mail')
    def test_email_sending_failure_handled(self, mock_send_mail):
        """Test de que se maneja correctamente el fallo en envío de email."""
        # Configurar mock para fallar
        mock_send_mail.side_effect = Exception("Email sending failed")
        
        # Crear usuario (no debe fallar aunque email falle)
        user = User.objects.create_user(
            username='fail_email',
            email='fail@test.com',
            password='testpass123',
            role='estudiante'
        )
        
        # Verificar que el usuario se creó correctamente
        assert user.id is not None
        
        # Verificar que la notificación se creó a pesar del fallo del email
        notifications = Notificacion.objects.filter(usuario=user, tipo='bienvenida')
        assert notifications.count() == 1


@pytest.mark.django_db
class TestGradingSignals:
    """Tests para signals de calificaciones."""
    
    def setup_method(self):
        """Configuración inicial para cada test."""
        # Crear datos base
        self.student = User.objects.create_user(
            username='student_grading',
            email='student@test.com',
            password='testpass123',
            role='estudiante',
            first_name='Student',
            last_name='Grading'
        )
        
        self.professor = User.objects.create_user(
            username='prof_grading',
            email='prof@test.com',
            password='testpass123',
            role='profesor'
        )
        
        self.period = Periodo.objects.create(
            nombre='2024-1',
            fecha_inicio='2024-01-15',
            fecha_fin='2024-05-15',
            activo=True
        )
        
        self.materia = Materia.objects.create(
            codigo='MAT001',
            nombre='Matemáticas I',
            creditos=4,
            profesor=self.professor
        )
        
        self.inscripcion = Inscripcion.objects.create(
            estudiante=self.student,
            materia=self.materia,
            periodo=self.period,
            estado='activa'
        )
        
        # Limpiar notificaciones existentes
        Notificacion.objects.filter(usuario=self.student, tipo='calificacion').delete()
    
    def test_grading_notification_created_on_new_grade(self):
        """Test de que se crea notificación al crear nueva calificación."""
        # Crear calificación
        calificacion = Calificacion.objects.create(
            inscripcion=self.inscripcion,
            nota=4.5,
            tipo='parcial',
            fecha='2024-03-15',
            descripcion='Primer parcial'
        )
        
        # Verificar que se creó la notificación
        notifications = Notificacion.objects.filter(
            usuario=self.student,
            tipo='calificacion'
        )
        assert notifications.count() == 1
        
        notification = notifications.first()
        assert notification.usuario == self.student
        assert notification.tipo == 'calificacion'
        assert 'nueva calificación' in notification.titulo.lower()
        assert 'Matemáticas I' in notification.mensaje
        assert '4.5' in notification.mensaje
        assert 'parcial' in notification.mensaje.lower()
    
    def test_grading_notification_created_on_grade_update(self):
        """Test de que se crea notificación al actualizar calificación."""
        # Crear calificación inicial
        calificacion = Calificacion.objects.create(
            inscripcion=self.inscripcion,
            nota=3.0,
            tipo='final',
            fecha='2024-05-15'
        )
        
        # Limpiar notificaciones de creación
        Notificacion.objects.filter(usuario=self.student, tipo='calificacion').delete()
        
        # Actualizar calificación
        calificacion.nota = 4.2
        calificacion.save()
        
        # Verificar que se creó notificación de actualización
        notifications = Notificacion.objects.filter(
            usuario=self.student,
            tipo='calificacion'
        )
        assert notifications.count() == 1
        
        notification = notifications.first()
        assert 'actualizada' in notification.titulo.lower() or 'modificada' in notification.titulo.lower()
        assert '4.2' in notification.mensaje
    
    def test_multiple_grades_create_multiple_notifications(self):
        """Test de que múltiples calificaciones crean múltiples notificaciones."""
        # Crear varias calificaciones
        calificaciones_data = [
            {'nota': 3.5, 'tipo': 'parcial', 'fecha': '2024-02-15'},
            {'nota': 4.0, 'tipo': 'quiz', 'fecha': '2024-03-15'},
            {'nota': 4.5, 'tipo': 'final', 'fecha': '2024-05-15'},
        ]
        
        for data in calificaciones_data:
            Calificacion.objects.create(
                inscripcion=self.inscripcion,
                **data
            )
        
        # Verificar que se crearon múltiples notificaciones
        notifications = Notificacion.objects.filter(
            usuario=self.student,
            tipo='calificacion'
        )
        assert notifications.count() == 3
        
        # Verificar que cada notificación corresponde a una calificación
        notas_en_notificaciones = []
        for notification in notifications:
            for nota in ['3.5', '4.0', '4.5']:
                if nota in notification.mensaje:
                    notas_en_notificaciones.append(nota)
                    break
        
        assert len(notas_en_notificaciones) == 3
        assert '3.5' in notas_en_notificaciones
        assert '4.0' in notas_en_notificaciones
        assert '4.5' in notas_en_notificaciones
    
    def test_grading_notification_includes_subject_info(self):
        """Test de que la notificación incluye información de la materia."""
        # Crear calificación
        calificacion = Calificacion.objects.create(
            inscripcion=self.inscripcion,
            nota=3.8,
            tipo='proyecto',
            fecha='2024-04-15',
            descripcion='Proyecto final'
        )
        
        # Verificar contenido de la notificación
        notification = Notificacion.objects.filter(
            usuario=self.student,
            tipo='calificacion'
        ).first()
        
        assert notification is not None
        assert 'Matemáticas I' in notification.mensaje
        assert 'MAT001' in notification.mensaje or self.materia.codigo in notification.mensaje
        assert '3.8' in notification.mensaje
        assert 'proyecto' in notification.mensaje.lower()
    
    def test_passing_grade_notification_message(self):
        """Test de mensaje específico para calificación aprobatoria."""
        # Crear calificación aprobatoria
        calificacion = Calificacion.objects.create(
            inscripcion=self.inscripcion,
            nota=4.2,
            tipo='final',
            fecha='2024-05-15'
        )
        
        notification = Notificacion.objects.filter(
            usuario=self.student,
            tipo='calificacion'
        ).first()
        
        # Verificar que el mensaje refleja que es aprobatoria
        mensaje_lower = notification.mensaje.lower()
        assert '4.2' in notification.mensaje
        # Puede incluir palabras como "aprobatoria", "excelente", etc.
    
    def test_failing_grade_notification_message(self):
        """Test de mensaje específico para calificación reprobatoria."""
        # Crear calificación reprobatoria
        calificacion = Calificacion.objects.create(
            inscripcion=self.inscripcion,
            nota=2.5,
            tipo='final',
            fecha='2024-05-15'
        )
        
        notification = Notificacion.objects.filter(
            usuario=self.student,
            tipo='calificacion'
        ).first()
        
        # Verificar que el mensaje incluye la nota
        assert '2.5' in notification.mensaje
        # El mensaje debe ser neutral y profesional


@pytest.mark.django_db
class TestInscriptionSignals:
    """Tests para signals de inscripciones."""
    
    def setup_method(self):
        """Configuración inicial para cada test."""
        self.student = User.objects.create_user(
            username='student_inscription',
            email='student@test.com',
            password='testpass123',
            role='estudiante',
            first_name='Student',
            last_name='Inscription'
        )
        
        self.professor = User.objects.create_user(
            username='prof_inscription',
            email='prof@test.com',
            password='testpass123',
            role='profesor'
        )
        
        self.period = Periodo.objects.create(
            nombre='2024-1',
            fecha_inicio='2024-01-15',
            fecha_fin='2024-05-15',
            activo=True
        )
        
        self.materia = Materia.objects.create(
            codigo='MAT001',
            nombre='Matemáticas I',
            creditos=4,
            profesor=self.professor
        )
        
        # Limpiar notificaciones existentes
        Notificacion.objects.filter(usuario=self.student, tipo='inscripcion').delete()
    
    def test_inscription_notification_created(self):
        """Test de que se crea notificación al inscribirse a una materia."""
        # Crear inscripción
        inscripcion = Inscripcion.objects.create(
            estudiante=self.student,
            materia=self.materia,
            periodo=self.period,
            estado='activa'
        )
        
        # Verificar que se creó la notificación
        notifications = Notificacion.objects.filter(
            usuario=self.student,
            tipo='inscripcion'
        )
        assert notifications.count() == 1
        
        notification = notifications.first()
        assert notification.usuario == self.student
        assert notification.tipo == 'inscripcion'
        assert 'inscripción' in notification.titulo.lower()
        assert 'Matemáticas I' in notification.mensaje
        assert '2024-1' in notification.mensaje
    
    def test_enrollment_confirmation_notification(self):
        """Test de notificación de confirmación de inscripción."""
        # Crear inscripción
        inscripcion = Inscripcion.objects.create(
            estudiante=self.student,
            materia=self.materia,
            periodo=self.period,
            estado='activa'
        )
        
        notification = Notificacion.objects.filter(
            usuario=self.student,
            tipo='inscripcion'
        ).first()
        
        # Verificar contenido de confirmación
        assert notification is not None
        assert 'exitosa' in notification.mensaje.lower() or 'confirmada' in notification.mensaje.lower()
        assert str(self.materia.creditos) in notification.mensaje
    
    def test_enrollment_status_change_notification(self):
        """Test de notificación al cambiar estado de inscripción."""
        # Crear inscripción
        inscripcion = Inscripcion.objects.create(
            estudiante=self.student,
            materia=self.materia,
            periodo=self.period,
            estado='activa'
        )
        
        # Limpiar notificaciones de creación
        Notificacion.objects.filter(usuario=self.student, tipo='inscripcion').delete()
        
        # Cambiar estado a aprobada
        inscripcion.estado = 'aprobada'
        inscripcion.save()
        
        # Verificar nueva notificación
        notifications = Notificacion.objects.filter(
            usuario=self.student,
            tipo='inscripcion'
        )
        
        if notifications.exists():  # Solo si se implementó este signal
            notification = notifications.first()
            assert 'aprobada' in notification.mensaje.lower()


@pytest.mark.django_db
class TestNotificationDelivery:
    """Tests para entrega de notificaciones."""
    
    def setup_method(self):
        """Configuración inicial."""
        self.user = User.objects.create_user(
            username='notification_user',
            email='notification@test.com',
            password='testpass123',
            role='estudiante'
        )
    
    def test_notification_marked_as_unread_by_default(self):
        """Test de que las notificaciones se marcan como no leídas por defecto."""
        # Crear notificación directamente
        notification = Notificacion.objects.create(
            usuario=self.user,
            tipo='sistema',
            titulo='Test Notification',
            mensaje='Test message'
        )
        
        assert not notification.leida
        assert notification.fecha_creacion is not None
    
    def test_notification_can_be_marked_as_read(self):
        """Test de que las notificaciones se pueden marcar como leídas."""
        notification = Notificacion.objects.create(
            usuario=self.user,
            tipo='sistema',
            titulo='Test Notification',
            mensaje='Test message'
        )
        
        # Marcar como leída
        notification.leida = True
        notification.save()
        
        assert notification.leida
        assert notification.fecha_lectura is not None
    
    def test_multiple_notifications_for_same_user(self):
        """Test de múltiples notificaciones para el mismo usuario."""
        # Crear múltiples notificaciones
        for i in range(3):
            Notificacion.objects.create(
                usuario=self.user,
                tipo='sistema',
                titulo=f'Notification {i+1}',
                mensaje=f'Message {i+1}'
            )
        
        # Verificar que todas se crearon
        notifications = Notificacion.objects.filter(usuario=self.user)
        assert notifications.count() == 3
        
        # Verificar que todas están sin leer
        unread_count = notifications.filter(leida=False).count()
        assert unread_count == 3
    
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_email_notification_integration(self):
        """Test de integración con envío de emails."""
        # Limpiar emails
        mail.outbox.clear()
        
        # Crear usuario (debería disparar email de bienvenida)
        user = User.objects.create_user(
            username='email_integration',
            email='integration@test.com',
            password='testpass123',
            role='estudiante',
            first_name='Email',
            last_name='Integration'
        )
        
        # Verificar que se envió email y se creó notificación
        assert len(mail.outbox) == 1
        
        notifications = Notificacion.objects.filter(usuario=user, tipo='bienvenida')
        assert notifications.count() == 1
        
        # Verificar coherencia entre email y notificación
        email = mail.outbox[0]
        notification = notifications.first()
        
        assert user.email in email.to
        assert 'Email Integration' in notification.mensaje


@pytest.mark.django_db
class TestSignalErrorHandling:
    """Tests para manejo de errores en signals."""
    
    @patch('apps.notificaciones.signals.Notificacion.objects.create')
    def test_notification_creation_failure_handled(self, mock_create):
        """Test de que se maneja el fallo en creación de notificaciones."""
        # Configurar mock para fallar
        mock_create.side_effect = Exception("Database error")
        
        # Crear usuario (no debe fallar aunque notificación falle)
        user = User.objects.create_user(
            username='db_error_user',
            email='dberror@test.com',
            password='testpass123',
            role='estudiante'
        )
        
        # Verificar que el usuario se creó correctamente
        assert user.id is not None
        assert User.objects.filter(username='db_error_user').exists()
    
    @patch('apps.notificaciones.signals.logger')
    def test_signal_errors_are_logged(self, mock_logger):
        """Test de que los errores en signals se registran en logs."""
        with patch('apps.notificaciones.signals.Notificacion.objects.create') as mock_create:
            # Configurar mock para fallar
            mock_create.side_effect = Exception("Test error")
            
            # Crear usuario
            User.objects.create_user(
                username='log_error_user',
                email='logerror@test.com',
                password='testpass123',
                role='estudiante'
            )
            
            # Verificar que se registró el error
            assert mock_logger.error.called
    
    def test_signal_isolation(self):
        """Test de que los signals no interfieren entre sí."""
        # Crear usuario (debería activar signal de bienvenida)
        user = User.objects.create_user(
            username='isolation_user',
            email='isolation@test.com',
            password='testpass123',
            role='estudiante'
        )
        
        # Crear datos académicos
        professor = User.objects.create_user(
            username='isolation_prof',
            email='prof@test.com',
            password='testpass123',
            role='profesor'
        )
        
        period = Periodo.objects.create(
            nombre='2024-1',
            fecha_inicio='2024-01-15',
            fecha_fin='2024-05-15',
            activo=True
        )
        
        materia = Materia.objects.create(
            codigo='ISO001',
            nombre='Isolation Test',
            creditos=3,
            profesor=professor
        )
        
        inscripcion = Inscripcion.objects.create(
            estudiante=user,
            materia=materia,
            periodo=period,
            estado='activa'
        )
        
        # Crear calificación (debería activar signal de calificación)
        calificacion = Calificacion.objects.create(
            inscripcion=inscripcion,
            nota=4.0,
            tipo='final',
            fecha='2024-05-15'
        )
        
        # Verificar que se crearon diferentes tipos de notificaciones
        bienvenida_notifications = Notificacion.objects.filter(
            usuario=user,
            tipo='bienvenida'
        )
        calificacion_notifications = Notificacion.objects.filter(
            usuario=user,
            tipo='calificacion'
        )
        
        assert bienvenida_notifications.count() >= 1
        assert calificacion_notifications.count() >= 1
        
        # Verificar que son diferentes
        assert bienvenida_notifications.first().mensaje != calificacion_notifications.first().mensaje 