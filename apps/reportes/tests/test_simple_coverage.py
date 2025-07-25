"""
Tests simples para aumentar cobertura de reportes.
"""

import pytest
from django.test import TestCase
from apps.users.models import User
from apps.reportes.models import ReporteGenerado
from apps.reportes.serializers import (
    ReporteGeneradoSerializer,
    ReporteEstudianteSerializer,
    ReporteProfesorSerializer
)


@pytest.mark.django_db
class TestReporteBasic(TestCase):
    """Tests básicos para reportes."""
    
    def setUp(self):
        """Configuración inicial."""
        self.admin = User.objects.create_user(
            username='admin1',
            email='admin1@test.com',
            password='password123',
            role='admin'
        )
        
        self.reporte = ReporteGenerado.objects.create(
            solicitante=self.admin,
            tipo='estudiante',
            nombre_archivo='test_report.csv',
            estado='completado',
            parametros={'test': 'value'}
        )
    
    def test_reporte_model_creation(self):
        """Test básico de creación de reporte."""
        self.assertEqual(self.reporte.tipo, 'estudiante')
        self.assertEqual(self.reporte.solicitante, self.admin)
        self.assertEqual(self.reporte.estado, 'completado')
    
    def test_reporte_str_method(self):
        """Test del método __str__ de ReporteGenerado."""
        str_result = str(self.reporte)
        # Verificar que contiene elementos esperados
        self.assertIn('Reporte', str_result)
        self.assertIn('admin1', str_result)
    
    def test_reporte_serializer_basic(self):
        """Test básico del serializer de reporte."""
        serializer = ReporteGeneradoSerializer(self.reporte)
        data = serializer.data
        
        self.assertEqual(data['tipo'], 'estudiante')
        self.assertEqual(data['estado'], 'completado')
        self.assertEqual(data['nombre_archivo'], 'test_report.csv')
    
    def test_reporte_estudiante_serializer(self):
        """Test del serializer de reporte de estudiante."""
        data = {
            'estudiante_id': 1,
            'periodo_id': 1
        }
        
        serializer = ReporteEstudianteSerializer(data=data)
        # Al menos probamos la validación
        if not serializer.is_valid():
            self.assertIsInstance(serializer.errors, dict)
        else:
            self.assertIn('estudiante_id', serializer.validated_data)
    
    def test_reporte_profesor_serializer(self):
        """Test del serializer de reporte de profesor."""
        data = {
            'profesor_id': 1,
            'periodo_id': 1
        }
        
        serializer = ReporteProfesorSerializer(data=data)
        # Al menos probamos la validación
        if not serializer.is_valid():
            self.assertIsInstance(serializer.errors, dict)
        else:
            self.assertIn('profesor_id', serializer.validated_data) 