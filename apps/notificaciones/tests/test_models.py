"""
Tests para modelos de la app notificaciones.
"""

import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from apps.users.models import User
from apps.notificaciones.models import Notificacion


@pytest.mark.django_db
class TestNotificacionModel(TestCase):
    """Tests para el modelo Notificacion."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        self.usuario = User.objects.create_user(
            username='usuario1',
            email='usuario1@test.com',
            password='password123',
            role='estudiante'
        )
        
        self.notificacion_data = {
            'usuario': self.usuario,
            'tipo': 'bienvenida',
            'mensaje': 'Bienvenido al sistema académico',
            'titulo': 'Bienvenida'
        }
    
    def test_create_notificacion_basic(self):
        """Test de creación básica de notificación."""
        notificacion = Notificacion.objects.create(**self.notificacion_data)
        
        self.assertEqual(notificacion.usuario, self.usuario)
        self.assertEqual(notificacion.tipo, 'bienvenida')
        self.assertEqual(notificacion.mensaje, 'Bienvenido al sistema académico')
        self.assertEqual(notificacion.titulo, 'Bienvenida')
        self.assertEqual(notificacion.estado, 'no_leida')  # Por defecto no leída
        self.assertIsNotNone(notificacion.fecha_creacion)
    
    def test_notificacion_string_representation(self):
        """Test de la representación en string de la notificación."""
        notificacion = Notificacion.objects.create(**self.notificacion_data)
        expected = f"{notificacion.usuario.username} - {notificacion.titulo}"
        self.assertEqual(str(notificacion), expected)
    
    def test_notificacion_tipos_choices(self):
        """Test de los tipos válidos de notificación."""
        tipos_validos = ['bienvenida', 'inscripcion_exitosa', 'calificacion_publicada', 'sistema']
        
        for tipo in tipos_validos:
            notificacion_data = self.notificacion_data.copy()
            notificacion_data['tipo'] = tipo
            notificacion_data['titulo'] = f'Notificación {tipo}'
            
            notificacion = Notificacion.objects.create(**notificacion_data)
            self.assertEqual(notificacion.tipo, tipo)
    
    def test_marcar_como_leida(self):
        """Test del método marcar_como_leida."""
        notificacion = Notificacion.objects.create(**self.notificacion_data)
        
        # Inicialmente no leída
        self.assertEqual(notificacion.estado, 'no_leida')
        self.assertIsNone(notificacion.fecha_lectura)
        
        # Marcar como leída
        notificacion.marcar_como_leida()
        
        # Verificar cambios
        self.assertEqual(notificacion.estado, 'leida')
        self.assertIsNotNone(notificacion.fecha_lectura)
    
    def test_estado_properties(self):
        """Test de las propiedades de estado."""
        notificacion = Notificacion.objects.create(**self.notificacion_data)
        
        # Inicialmente no leída
        self.assertTrue(notificacion.es_no_leida)
        self.assertFalse(notificacion.es_leida)
        self.assertFalse(notificacion.es_archivada)
        
        # Marcar como leída
        notificacion.marcar_como_leida()
        self.assertFalse(notificacion.es_no_leida)
        self.assertTrue(notificacion.es_leida)
        self.assertFalse(notificacion.es_archivada)
        
        # Archivar
        notificacion.archivar()
        self.assertFalse(notificacion.es_no_leida)
        self.assertFalse(notificacion.es_leida)
        self.assertTrue(notificacion.es_archivada)
    
    def test_metodo_crear_notificacion(self):
        """Test del método de clase crear_notificacion."""
        notificacion = Notificacion.crear_notificacion(
            usuario=self.usuario,
            tipo='sistema',
            titulo='Test Sistema',
            mensaje='Mensaje de prueba del sistema'
        )
        
        self.assertEqual(notificacion.usuario, self.usuario)
        self.assertEqual(notificacion.tipo, 'sistema')
        self.assertEqual(notificacion.titulo, 'Test Sistema')
        self.assertEqual(notificacion.mensaje, 'Mensaje de prueba del sistema')
        self.assertEqual(notificacion.estado, 'no_leida')
    
    def test_notificar_bienvenida(self):
        """Test del método notificar_bienvenida."""
        notificacion = Notificacion.notificar_bienvenida(self.usuario)
        
        self.assertEqual(notificacion.usuario, self.usuario)
        self.assertEqual(notificacion.tipo, 'bienvenida')
        self.assertEqual(notificacion.titulo, '¡Bienvenido al Sistema Académico!')
        self.assertIn('bienvenida', notificacion.mensaje.lower())
        self.assertEqual(notificacion.estado, 'no_leida')
    
    def test_notificaciones_no_leidas_for_usuario(self):
        """Test para obtener notificaciones no leídas de un usuario."""
        # Crear varias notificaciones para el usuario
        notif1 = Notificacion.objects.create(
            usuario=self.usuario,
            tipo='bienvenida',
            mensaje='Mensaje 1',
            titulo='Titulo 1'
        )
        
        notif2 = Notificacion.objects.create(
            usuario=self.usuario,
            tipo='inscripcion_exitosa',
            mensaje='Mensaje 2',
            titulo='Titulo 2'
        )
        
        notif3 = Notificacion.objects.create(
            usuario=self.usuario,
            tipo='calificacion_publicada',
            mensaje='Mensaje 3',
            titulo='Titulo 3'
        )
        
        # Marcar una como leída
        notif2.marcar_como_leida()
        
        # Obtener no leídas
        no_leidas = Notificacion.objects.filter(usuario=self.usuario, estado='no_leida')
        
        self.assertEqual(no_leidas.count(), 2)
        self.assertIn(notif1, no_leidas)
        self.assertIn(notif3, no_leidas)
        self.assertNotIn(notif2, no_leidas)
    
    def test_ordenamiento_por_fecha(self):
        """Test del ordenamiento por fecha de creación."""
        # Crear notificaciones en orden
        notif1 = Notificacion.objects.create(
            usuario=self.usuario,
            tipo='bienvenida',
            mensaje='Primera',
            titulo='Primera'
        )
        
        notif2 = Notificacion.objects.create(
            usuario=self.usuario,
            tipo='inscripcion_exitosa',
            mensaje='Segunda',
            titulo='Segunda'
        )
        
        # Obtener todas ordenadas
        notificaciones = Notificacion.objects.filter(usuario=self.usuario).order_by('-fecha_creacion')
        
        # La más reciente debe ser la primera
        self.assertEqual(notificaciones.first(), notif2)
        self.assertEqual(notificaciones.last(), notif1) 