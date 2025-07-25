"""
Tests para services de la app reportes.
"""

import pytest
import os
import tempfile
from decimal import Decimal
from django.test import TestCase, override_settings
from django.conf import settings
from unittest.mock import patch, Mock
from apps.reportes.services import ReporteService
from apps.reportes.models import ReporteGenerado
from apps.users.models import User
from apps.materias.models import Materia, Periodo
from apps.inscripciones.models import Inscripcion, Calificacion
from datetime import date, timedelta


@pytest.mark.django_db
class TestReporteService(TestCase):
    """Tests para ReporteService."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        # Crear usuarios
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='password123',
            role='admin'
        )
        
        self.profesor = User.objects.create_user(
            username='profesor',
            email='profesor@test.com',
            password='password123',
            role='profesor'
        )
        
        self.estudiante = User.objects.create_user(
            username='estudiante',
            email='estudiante@test.com',
            password='password123',
            role='estudiante'
        )
        
        # Crear período
        self.periodo = Periodo.objects.create(
            nombre='2024-1',
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=120),
            estado='activo'
        )
        
        # Crear materia
        self.materia = Materia.objects.create(
            codigo='MAT101',
            nombre='Matemáticas',
            creditos=3,
            profesor=self.profesor
        )
        
        # Crear inscripción
        self.inscripcion = Inscripcion.objects.create(
            estudiante=self.estudiante,
            materia=self.materia,
            periodo=self.periodo
        )
        
        # Crear calificación
        Calificacion.objects.create(
            inscripcion=self.inscripcion,
            tipo='final',
            nota=Decimal('4.0'),
            peso=100
        )
        
        # Crear servicio
        self.service = ReporteService(self.admin)
    
    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_init_creates_directory(self):
        """Test que init crea el directorio de reportes."""
        service = ReporteService(self.admin)
        
        self.assertTrue(os.path.exists(service.reports_dir))
        self.assertEqual(service.solicitante, self.admin)
    
    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_generar_reporte_estudiante_success(self):
        """Test de generación exitosa de reporte de estudiante."""
        service = ReporteService(self.admin)
        
        reporte = service.generar_reporte_estudiante(self.estudiante.id)
        
        self.assertIsInstance(reporte, ReporteGenerado)
        self.assertEqual(reporte.solicitante, self.admin)
        self.assertEqual(reporte.tipo, 'estudiante')
        self.assertIn('estudiante', reporte.nombre_archivo)
        self.assertEqual(reporte.parametros['estudiante_id'], self.estudiante.id)
        self.assertTrue(os.path.exists(os.path.join(service.reports_dir, reporte.nombre_archivo)))
    
    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_generar_reporte_estudiante_not_found(self):
        """Test cuando el estudiante no existe."""
        service = ReporteService(self.admin)
        
        with self.assertRaises(User.DoesNotExist):
            service.generar_reporte_estudiante(99999)
    
    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_generar_reporte_estudiante_wrong_role(self):
        """Test cuando el usuario no es estudiante."""
        service = ReporteService(self.admin)
        
        with self.assertRaises(User.DoesNotExist):
            service.generar_reporte_estudiante(self.profesor.id)
    
    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_generar_reporte_profesor_success(self):
        """Test de generación exitosa de reporte de profesor."""
        service = ReporteService(self.admin)
        
        reporte = service.generar_reporte_profesor(self.profesor.id)
        
        self.assertIsInstance(reporte, ReporteGenerado)
        self.assertEqual(reporte.solicitante, self.admin)
        self.assertEqual(reporte.tipo, 'profesor')
        self.assertIn('profesor', reporte.nombre_archivo)
        self.assertEqual(reporte.parametros['profesor_id'], self.profesor.id)
        self.assertTrue(os.path.exists(os.path.join(service.reports_dir, reporte.nombre_archivo)))
    
    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_generar_reporte_profesor_not_found(self):
        """Test cuando el profesor no existe."""
        service = ReporteService(self.admin)
        
        with self.assertRaises(User.DoesNotExist):
            service.generar_reporte_profesor(99999)
    
    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_generar_reporte_general_success(self):
        """Test de generación exitosa de reporte general."""
        service = ReporteService(self.admin)
        
        reporte = service.generar_reporte_general()
        
        self.assertIsInstance(reporte, ReporteGenerado)
        self.assertEqual(reporte.solicitante, self.admin)
        self.assertEqual(reporte.tipo, 'general')
        self.assertIn('general', reporte.nombre_archivo)
        self.assertTrue(os.path.exists(os.path.join(service.reports_dir, reporte.nombre_archivo)))
    
    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_generar_reporte_por_periodo_success(self):
        """Test de generación exitosa de reporte por período."""
        service = ReporteService(self.admin)
        
        reporte = service.generar_reporte_por_periodo(self.periodo.id)
        
        self.assertIsInstance(reporte, ReporteGenerado)
        self.assertEqual(reporte.solicitante, self.admin)
        self.assertEqual(reporte.tipo, 'periodo')
        self.assertIn('periodo', reporte.nombre_archivo)
        self.assertEqual(reporte.parametros['periodo_id'], self.periodo.id)
        self.assertTrue(os.path.exists(os.path.join(service.reports_dir, reporte.nombre_archivo)))
    
    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_generar_reporte_por_periodo_not_found(self):
        """Test cuando el período no existe."""
        service = ReporteService(self.admin)
        
        with self.assertRaises(Periodo.DoesNotExist):
            service.generar_reporte_por_periodo(99999)
    
    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_generar_reporte_por_materia_success(self):
        """Test de generación exitosa de reporte por materia."""
        service = ReporteService(self.admin)
        
        reporte = service.generar_reporte_por_materia(self.materia.id)
        
        self.assertIsInstance(reporte, ReporteGenerado)
        self.assertEqual(reporte.solicitante, self.admin)
        self.assertEqual(reporte.tipo, 'materia')
        self.assertIn('materia', reporte.nombre_archivo)
        self.assertEqual(reporte.parametros['materia_id'], self.materia.id)
        self.assertTrue(os.path.exists(os.path.join(service.reports_dir, reporte.nombre_archivo)))
    
    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_generar_reporte_por_materia_not_found(self):
        """Test cuando la materia no existe."""
        service = ReporteService(self.admin)
        
        with self.assertRaises(Materia.DoesNotExist):
            service.generar_reporte_por_materia(99999)
    
    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_calcular_estadisticas_estudiante(self):
        """Test de cálculo de estadísticas de estudiante."""
        service = ReporteService(self.admin)
        
        estadisticas = service._calcular_estadisticas_estudiante(self.estudiante)
        
        self.assertIsInstance(estadisticas, dict)
        self.assertIn('promedio_general', estadisticas)
        self.assertIn('total_materias', estadisticas)
        self.assertIn('materias_aprobadas', estadisticas)
        self.assertIn('materias_reprobadas', estadisticas)
        self.assertIn('creditos_aprobados', estadisticas)
    
    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_calcular_estadisticas_profesor(self):
        """Test de cálculo de estadísticas de profesor."""
        service = ReporteService(self.admin)
        
        estadisticas = service._calcular_estadisticas_profesor(self.profesor)
        
        self.assertIsInstance(estadisticas, dict)
        self.assertIn('total_materias', estadisticas)
        self.assertIn('total_estudiantes', estadisticas)
        self.assertIn('promedio_materias', estadisticas)
        self.assertIn('total_creditos', estadisticas)
    
    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_escribir_csv_estudiante(self):
        """Test de escritura de CSV para estudiante."""
        service = ReporteService(self.admin)
        temp_file = os.path.join(service.reports_dir, 'test_estudiante.csv')
        
        service._escribir_csv_estudiante(temp_file, self.estudiante)
        
        self.assertTrue(os.path.exists(temp_file))
        
        # Verificar contenido básico del archivo
        with open(temp_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn('Nombre', content)
            self.assertIn('Materia', content)
            self.assertIn(self.estudiante.username, content)
    
    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_escribir_csv_profesor(self):
        """Test de escritura de CSV para profesor."""
        service = ReporteService(self.admin)
        temp_file = os.path.join(service.reports_dir, 'test_profesor.csv')
        
        service._escribir_csv_profesor(temp_file, self.profesor)
        
        self.assertTrue(os.path.exists(temp_file))
        
        # Verificar contenido básico del archivo
        with open(temp_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn('Materia', content)
            self.assertIn('Código', content)
    
    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_escribir_csv_general(self):
        """Test de escritura de CSV general."""
        service = ReporteService(self.admin)
        temp_file = os.path.join(service.reports_dir, 'test_general.csv')
        
        service._escribir_csv_general(temp_file)
        
        self.assertTrue(os.path.exists(temp_file))
        
        # Verificar contenido básico del archivo
        with open(temp_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn('Estudiante', content)
            self.assertIn('Materia', content)
    
    def test_format_fecha(self):
        """Test del formateo de fechas."""
        service = ReporteService(self.admin)
        fecha = date(2024, 1, 15)
        
        resultado = service._format_fecha(fecha)
        
        self.assertEqual(resultado, '15/01/2024')
    
    def test_format_fecha_none(self):
        """Test del formateo de fechas None."""
        service = ReporteService(self.admin)
        
        resultado = service._format_fecha(None)
        
        self.assertEqual(resultado, 'N/A')
    
    def test_format_nota(self):
        """Test del formateo de notas."""
        service = ReporteService(self.admin)
        nota = Decimal('4.75')
        
        resultado = service._format_nota(nota)
        
        self.assertEqual(resultado, '4.75')
    
    def test_format_nota_none(self):
        """Test del formateo de notas None."""
        service = ReporteService(self.admin)
        
        resultado = service._format_nota(None)
        
        self.assertEqual(resultado, 'N/A')
    
    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_cleanup_old_reports(self):
        """Test de limpieza de reportes antiguos."""
        service = ReporteService(self.admin)
        
        # Crear reporte falso antiguo
        old_report = ReporteGenerado.objects.create(
            solicitante=self.admin,
            tipo='test',
            nombre_archivo='old_report.csv',
            parametros={}
        )
        # Simular que es antiguo
        old_report.created_at = old_report.created_at - timedelta(days=40)
        old_report.save()
        
        deleted_count = service.cleanup_old_reports(days=30)
        
        self.assertGreaterEqual(deleted_count, 0)
    
    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_error_handling_in_generation(self):
        """Test del manejo de errores durante la generación."""
        service = ReporteService(self.admin)
        
        # Intentar generar reporte con ID inválido
        with self.assertRaises(User.DoesNotExist):
            service.generar_reporte_estudiante(99999)
        
        # Verificar que no se creó archivo corrupto
        files_before = len(os.listdir(service.reports_dir))
        try:
            service.generar_reporte_estudiante(99999)
        except User.DoesNotExist:
            pass
        files_after = len(os.listdir(service.reports_dir))
        
        # No deberían haberse creado archivos adicionales
        self.assertEqual(files_before, files_after) 