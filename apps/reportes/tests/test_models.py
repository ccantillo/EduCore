"""
Tests para modelos de la app reportes.
"""

import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from apps.users.models import User
from apps.reportes.models import ReporteGenerado


@pytest.mark.django_db
class TestReporteGeneradoModel(TestCase):
    """Tests para el modelo ReporteGenerado."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        self.usuario = User.objects.create_user(
            username='admin1',
            email='admin1@test.com',
            password='password123',
            role='admin'
        )
        
        self.estudiante = User.objects.create_user(
            username='estudiante1',
            email='est1@test.com',
            password='password123',
            role='estudiante'
        )
        
        self.reporte_data = {
            'solicitante': self.usuario,
            'tipo': 'estudiante',
            'nombre_archivo': 'reporte_test.csv',
            'ruta_archivo': 'reportes/test.csv',
            'parametros': {'estudiante_id': self.estudiante.id}
        }
    
    def test_create_reporte_basic(self):
        """Test de creación básica de reporte."""
        reporte = ReporteGenerado.objects.create(**self.reporte_data)
        
        self.assertEqual(reporte.solicitante, self.usuario)
        self.assertEqual(reporte.tipo, 'estudiante')
        self.assertEqual(reporte.estado, 'pendiente')
        self.assertIsNotNone(reporte.parametros)
        self.assertIsNotNone(reporte.created_at)
        self.assertIsNone(reporte.completado_at)
    
    def test_reporte_string_representation(self):
        """Test de la representación en string del reporte."""
        reporte = ReporteGenerado.objects.create(**self.reporte_data)
        expected = f"{reporte.get_tipo_display()} - {reporte.solicitante.username} - {reporte.created_at.strftime('%Y-%m-%d %H:%M')}"
        self.assertEqual(str(reporte), expected)
    
    def test_reporte_tipos_choices(self):
        """Test de los tipos válidos de reporte."""
        tipos_validos = ['estudiante', 'profesor', 'materia', 'periodo', 'general']
        
        for tipo in tipos_validos:
            reporte_data = self.reporte_data.copy()
            reporte_data['tipo'] = tipo
            
            reporte = ReporteGenerado.objects.create(**reporte_data)
            self.assertEqual(reporte.tipo, tipo)
    
    def test_reporte_estados_choices(self):
        """Test de los estados válidos de reporte."""
        estados_validos = ['pendiente', 'generando', 'completado', 'error', 'expirado']
        
        for estado in estados_validos:
            reporte_data = self.reporte_data.copy()
            reporte_data['estado'] = estado
            
            reporte = ReporteGenerado.objects.create(**reporte_data)
            self.assertEqual(reporte.estado, estado)
    
    def test_marcar_completado(self):
        """Test del método marcar_completado."""
        reporte = ReporteGenerado.objects.create(**self.reporte_data)
        
        # Inicialmente pendiente
        self.assertEqual(reporte.estado, 'pendiente')
        self.assertIsNone(reporte.completado_at)
        
        # Marcar como completado
        reporte.marcar_completado(registros_procesados=100)
        
        # Verificar cambios
        self.assertEqual(reporte.estado, 'completado')
        self.assertEqual(reporte.registros_procesados, 100)
        self.assertIsNotNone(reporte.completado_at)
    
    def test_marcar_error(self):
        """Test del método marcar_error."""
        reporte = ReporteGenerado.objects.create(**self.reporte_data)
        
        # Marcar como error con mensaje
        mensaje_error = 'Error al generar el reporte: datos no encontrados'
        reporte.marcar_error(mensaje_error)
        
        # Verificar cambios
        self.assertEqual(reporte.estado, 'error')
        self.assertEqual(reporte.mensaje_error, mensaje_error)
    
    def test_marcar_generando(self):
        """Test del método marcar_generando."""
        reporte = ReporteGenerado.objects.create(**self.reporte_data)
        
        # Marcar como generando
        reporte.marcar_generando()
        
        # Verificar cambios
        self.assertEqual(reporte.estado, 'generando')
    
    def test_properties_estado(self):
        """Test de las propiedades de estado."""
        reporte = ReporteGenerado.objects.create(**self.reporte_data)
        
        # Estado pendiente
        self.assertTrue(reporte.es_pendiente)
        self.assertFalse(reporte.es_completado)
        self.assertFalse(reporte.es_error)
        
        # Cambiar a completado
        reporte.marcar_completado()
        self.assertFalse(reporte.es_pendiente)
        self.assertTrue(reporte.es_completado)
        self.assertFalse(reporte.es_error)
        
        # Crear otro reporte con error
        reporte_error = ReporteGenerado.objects.create(
            solicitante=self.usuario,
            tipo='estudiante',
            nombre_archivo='error.csv',
            ruta_archivo='reportes/error.csv',
            parametros={'test': 'data'},
            estado='error'
        )
        self.assertFalse(reporte_error.es_pendiente)
        self.assertFalse(reporte_error.es_completado)
        self.assertTrue(reporte_error.es_error)
    
    def test_tiempo_vida_reporte(self):
        """Test para verificar tiempo de vida del reporte."""
        reporte = ReporteGenerado.objects.create(**self.reporte_data)
        
        # Simular reporte antiguo
        from django.utils import timezone
        reporte.created_at = timezone.now() - timedelta(days=10)
        reporte.save()
        
        # El reporte debería considerarse como posible candidato para limpieza
        # (esto dependería de la implementación de lógica de limpieza)
        antiguedad = timezone.now() - reporte.created_at
        self.assertGreater(antiguedad.days, 7)
    
    def test_parametros_json_field(self):
        """Test del campo JSON parametros."""
        parametros_complejos = {
            'estudiante_id': self.estudiante.id,
            'periodo': '2024-1',
            'incluir_calificaciones': True,
            'formato': 'csv',
            'filtros': {
                'materias': ['MAT101', 'MAT201'],
                'nota_minima': 3.0
            }
        }
        
        reporte = ReporteGenerado.objects.create(
            solicitante=self.usuario,
            tipo='estudiante',
            nombre_archivo='complejo.csv',
            ruta_archivo='reportes/complejo.csv',
            parametros=parametros_complejos
        )
        
        # Verificar que se guarden y recuperen correctamente
        reporte.refresh_from_db()
        self.assertEqual(reporte.parametros['estudiante_id'], self.estudiante.id)
        self.assertTrue(reporte.parametros['incluir_calificaciones'])
        self.assertEqual(reporte.parametros['filtros']['nota_minima'], 3.0)
    
    def test_ordenamiento_por_fecha(self):
        """Test del ordenamiento por fecha de solicitud."""
        # Crear reportes en orden
        reporte1 = ReporteGenerado.objects.create(
            solicitante=self.usuario,
            tipo='estudiante',
            nombre_archivo='reporte1.csv',
            ruta_archivo='reportes/reporte1.csv',
            parametros={'id': 1}
        )
        
        reporte2 = ReporteGenerado.objects.create(
            solicitante=self.usuario,
            tipo='profesor',
            nombre_archivo='reporte2.csv',
            ruta_archivo='reportes/reporte2.csv',
            parametros={'id': 2}
        )
        
        # Obtener todos ordenados por fecha (más reciente primero)
        reportes = ReporteGenerado.objects.filter(solicitante=self.usuario).order_by('-created_at')
        
        # El más reciente debe ser el primero
        self.assertEqual(reportes.first(), reporte2)
        self.assertEqual(reportes.last(), reporte1) 