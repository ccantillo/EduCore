"""
Tests para serializers de la app notificaciones.
"""

import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from rest_framework.test import APIRequestFactory
from rest_framework import serializers
from datetime import date, timedelta
from apps.users.models import User
from apps.notificaciones.models import Notificacion
from apps.notificaciones.serializers import (
    NotificacionSerializer,
    NotificacionCreateSerializer,
    NotificacionDetalleSerializer,
    NotificacionListSerializer
)


@pytest.mark.django_db
class TestNotificacionSerializer(TestCase):
    """Tests para NotificacionSerializer."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        self.usuario = User.objects.create_user(
            username='usuario1',
            email='usuario1@test.com',
            password='password123',
            role='estudiante'
        )
        
        self.tipo_notificacion = TipoNotificacion.objects.create(
            nombre='Calificación',
            descripcion='Notificación de nueva calificación'
        )
        
        self.notificacion = Notificacion.objects.create(
            usuario=self.usuario,
            tipo=self.tipo_notificacion,
            titulo='Nueva Calificación',
            mensaje='Has recibido una nueva calificación',
            leida=False
        )
    
    def test_notificacion_serialization(self):
        """Test de serialización de notificación."""
        serializer = NotificacionSerializer(self.notificacion)
        data = serializer.data
        
        self.assertEqual(data['id'], self.notificacion.id)
        self.assertEqual(data['titulo'], 'Nueva Calificación')
        self.assertEqual(data['mensaje'], 'Has recibido una nueva calificación')
        self.assertEqual(data['leida'], False)
        self.assertIn('usuario', data)
        self.assertIn('tipo', data)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
    
    def test_notificacion_nested_serialization(self):
        """Test de serialización anidada."""
        serializer = NotificacionSerializer(self.notificacion)
        data = serializer.data
        
        # Verificar que los datos anidados están presentes
        self.assertIsInstance(data['usuario'], dict)
        self.assertIsInstance(data['tipo'], dict)
        
        # Verificar contenido del usuario
        self.assertEqual(data['usuario']['username'], 'usuario1')
        
        # Verificar contenido del tipo
        self.assertEqual(data['tipo']['nombre'], 'Calificación')
    
    def test_read_only_fields(self):
        """Test que los campos de solo lectura están correctos."""
        serializer = NotificacionSerializer()
        read_only_fields = serializer.Meta.read_only_fields
        
        expected_read_only = ['id', 'created_at', 'updated_at']
        for field in expected_read_only:
            self.assertIn(field, read_only_fields)


@pytest.mark.django_db
class TestNotificacionCreateSerializer(TestCase):
    """Tests para NotificacionCreateSerializer."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        self.usuario = User.objects.create_user(
            username='usuario1',
            email='usuario1@test.com',
            password='password123',
            role='estudiante'
        )
        
        self.tipo_notificacion = TipoNotificacion.objects.create(
            nombre='Inscripción',
            descripcion='Notificación de inscripción'
        )
    
    def test_valid_notificacion_creation(self):
        """Test de creación válida de notificación."""
        data = {
            'usuario': self.usuario.id,
            'tipo': self.tipo_notificacion.id,
            'titulo': 'Inscripción Exitosa',
            'mensaje': 'Te has inscrito correctamente a la materia',
            'leida': False
        }
        
        serializer = NotificacionCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        notificacion = serializer.save()
        
        self.assertEqual(notificacion.usuario, self.usuario)
        self.assertEqual(notificacion.tipo, self.tipo_notificacion)
        self.assertEqual(notificacion.titulo, 'Inscripción Exitosa')
        self.assertEqual(notificacion.mensaje, 'Te has inscrito correctamente a la materia')
        self.assertEqual(notificacion.leida, False)
    
    def test_required_fields(self):
        """Test que los campos requeridos fallan cuando no están presentes."""
        data = {}
        
        serializer = NotificacionCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        
        required_fields = ['usuario', 'tipo', 'titulo', 'mensaje']
        for field in required_fields:
            self.assertIn(field, serializer.errors)
    
    def test_invalid_usuario_id(self):
        """Test con ID de usuario inválido."""
        data = {
            'usuario': 99999,
            'tipo': self.tipo_notificacion.id,
            'titulo': 'Test',
            'mensaje': 'Test mensaje'
        }
        
        serializer = NotificacionCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('usuario', serializer.errors)
    
    def test_invalid_tipo_id(self):
        """Test con ID de tipo inválido."""
        data = {
            'usuario': self.usuario.id,
            'tipo': 99999,
            'titulo': 'Test',
            'mensaje': 'Test mensaje'
        }
        
        serializer = NotificacionCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('tipo', serializer.errors)


@pytest.mark.django_db
class TestNotificacionUpdateSerializer(TestCase):
    """Tests para NotificacionUpdateSerializer."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        self.usuario = User.objects.create_user(
            username='usuario1',
            email='usuario1@test.com',
            password='password123',
            role='estudiante'
        )
        
        self.tipo_notificacion = TipoNotificacion.objects.create(
            nombre='General',
            descripcion='Notificación general'
        )
        
        self.notificacion = Notificacion.objects.create(
            usuario=self.usuario,
            tipo=self.tipo_notificacion,
            titulo='Título Original',
            mensaje='Mensaje original',
            leida=False
        )
    
    def test_valid_update(self):
        """Test de actualización válida."""
        data = {
            'leida': True,
            'titulo': 'Título Actualizado'
        }
        
        serializer = NotificacionUpdateSerializer(self.notificacion, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        updated_notificacion = serializer.save()
        
        self.assertEqual(updated_notificacion.leida, True)
        self.assertEqual(updated_notificacion.titulo, 'Título Actualizado')
        # El mensaje no debería haber cambiado
        self.assertEqual(updated_notificacion.mensaje, 'Mensaje original')
    
    def test_partial_update(self):
        """Test de actualización parcial."""
        data = {
            'leida': True
        }
        
        serializer = NotificacionUpdateSerializer(self.notificacion, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        updated_notificacion = serializer.save()
        
        self.assertEqual(updated_notificacion.leida, True)
        # Otros campos no deberían haber cambiado
        self.assertEqual(updated_notificacion.titulo, 'Título Original')
        self.assertEqual(updated_notificacion.mensaje, 'Mensaje original')


@pytest.mark.django_db
class TestTipoNotificacionSerializer(TestCase):
    """Tests para TipoNotificacionSerializer."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        self.tipo_notificacion = TipoNotificacion.objects.create(
            nombre='Académico',
            descripcion='Notificaciones relacionadas con el ámbito académico',
            activo=True
        )
    
    def test_tipo_notificacion_serialization(self):
        """Test de serialización de tipo de notificación."""
        serializer = TipoNotificacionSerializer(self.tipo_notificacion)
        data = serializer.data
        
        self.assertEqual(data['id'], self.tipo_notificacion.id)
        self.assertEqual(data['nombre'], 'Académico')
        self.assertEqual(data['descripcion'], 'Notificaciones relacionadas con el ámbito académico')
        self.assertEqual(data['activo'], True)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
    
    def test_read_only_fields(self):
        """Test que los campos de solo lectura están correctos."""
        serializer = TipoNotificacionSerializer()
        read_only_fields = serializer.Meta.read_only_fields
        
        expected_read_only = ['id', 'created_at', 'updated_at']
        for field in expected_read_only:
            self.assertIn(field, read_only_fields)


@pytest.mark.django_db
class TestPlantillaNotificacionSerializer(TestCase):
    """Tests para PlantillaNotificacionSerializer."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        self.tipo_notificacion = TipoNotificacion.objects.create(
            nombre='Email',
            descripcion='Notificaciones por email'
        )
        
        self.plantilla = PlantillaNotificacion.objects.create(
            tipo=self.tipo_notificacion,
            nombre='Plantilla Bienvenida',
            asunto='Bienvenido al sistema',
            contenido='Hola {nombre}, bienvenido al sistema académico.',
            activa=True
        )
    
    def test_plantilla_serialization(self):
        """Test de serialización de plantilla."""
        serializer = PlantillaNotificacionSerializer(self.plantilla)
        data = serializer.data
        
        self.assertEqual(data['id'], self.plantilla.id)
        self.assertEqual(data['nombre'], 'Plantilla Bienvenida')
        self.assertEqual(data['asunto'], 'Bienvenido al sistema')
        self.assertEqual(data['contenido'], 'Hola {nombre}, bienvenido al sistema académico.')
        self.assertEqual(data['activa'], True)
        self.assertIn('tipo', data)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
    
    def test_plantilla_nested_serialization(self):
        """Test de serialización anidada del tipo."""
        serializer = PlantillaNotificacionSerializer(self.plantilla)
        data = serializer.data
        
        # Verificar que los datos del tipo están presentes
        self.assertIsInstance(data['tipo'], dict)
        self.assertEqual(data['tipo']['nombre'], 'Email')
    
    def test_read_only_fields(self):
        """Test que los campos de solo lectura están correctos."""
        serializer = PlantillaNotificacionSerializer()
        read_only_fields = serializer.Meta.read_only_fields
        
        expected_read_only = ['id', 'created_at', 'updated_at']
        for field in expected_read_only:
            self.assertIn(field, read_only_fields) 