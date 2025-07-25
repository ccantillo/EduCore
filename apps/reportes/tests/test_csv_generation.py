"""
Tests para generación de reportes CSV.
Incluye reportes de estudiantes y profesores según los requerimientos del documento.
"""

import pytest
import csv
import io
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.materias.models import Materia, Periodo
from apps.inscripciones.models import Inscripcion, Calificacion
from apps.users.models import Profile
from apps.reportes.models import ReporteGenerado
from apps.reportes.services import ReporteService

User = get_user_model()


@pytest.mark.django_db
class TestCSVReportGeneration:
    """Tests para generación de reportes CSV."""
    
    def setup_method(self):
        """Configuración inicial para cada test."""
        # Crear usuarios
        self.admin_user = User.objects.create_user(
            username='admin_reports',
            email='admin@test.com',
            password='testpass123',
            role='admin'
        )
        
        self.student = User.objects.create_user(
            username='student_reports',
            email='student@test.com',
            password='testpass123',
            role='estudiante',
            first_name='Juan',
            last_name='Pérez'
        )
        
        self.professor = User.objects.create_user(
            username='prof_reports',
            email='prof@test.com',
            password='testpass123',
            role='profesor',
            first_name='María',
            last_name='García'
        )
        
        # Crear perfil de estudiante
        self.profile = Profile.objects.create(
            user=self.student,
            identification='1234567890',
            max_credits_per_semester=18
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
            profesor=self.professor
        )
        
        self.materia2 = Materia.objects.create(
            codigo='FIS001',
            nombre='Física I',
            creditos=3,
            profesor=self.professor
        )
        
        # Crear inscripciones con calificaciones
        self.inscripcion1 = Inscripcion.objects.create(
            estudiante=self.student,
            materia=self.materia1,
            periodo=self.period,
            estado='aprobada'
        )
        
        self.inscripcion2 = Inscripcion.objects.create(
            estudiante=self.student,
            materia=self.materia2,
            periodo=self.period,
            estado='activa'
        )
        
        # Crear calificaciones
        Calificacion.objects.create(
            inscripcion=self.inscripcion1,
            nota=4.5,
            tipo='final',
            porcentaje=100,
            fecha='2024-05-10'
        )
        
        Calificacion.objects.create(
            inscripcion=self.inscripcion2,
            nota=3.8,
            tipo='parcial',
            porcentaje=60,
            fecha='2024-04-15'
        )
        
        Calificacion.objects.create(
            inscripcion=self.inscripcion2,
            nota=4.2,
            tipo='final',
            porcentaje=40,
            fecha='2024-05-12'
        )
    
    def test_generate_student_csv_report(self):
        """Test de generación de reporte CSV para estudiante."""
        service = ReporteService()
        
        # Generar reporte
        csv_content = service.generate_student_report(self.student.id)
        
        # Verificar que se generó contenido
        assert csv_content is not None
        assert len(csv_content) > 0
        
        # Parsear CSV
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)
        
        # Verificar estructura del CSV
        assert len(rows) >= 2  # Al menos 2 materias
        
        # Verificar headers según requerimientos
        expected_headers = ['nombre', 'materia', 'calificacion', 'estado', 'promedio']
        actual_headers = [header.lower() for header in reader.fieldnames]
        
        for header in expected_headers:
            assert header in actual_headers
        
        # Verificar contenido específico
        student_row = next((row for row in rows if row['materia'] == 'Matemáticas I'), None)
        assert student_row is not None
        assert 'Juan Pérez' in student_row['nombre']
        assert student_row['estado'] == 'aprobada'
        assert float(student_row['calificacion']) == 4.5
    
    def test_generate_professor_csv_report(self):
        """Test de generación de reporte CSV para profesor."""
        service = ReporteService()
        
        # Generar reporte
        csv_content = service.generate_professor_report(self.professor.id)
        
        # Verificar que se generó contenido
        assert csv_content is not None
        assert len(csv_content) > 0
        
        # Parsear CSV
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)
        
        # Verificar que tiene datos
        assert len(rows) >= 2  # Al menos 2 materias impartidas
        
        # Verificar headers
        expected_headers = ['nombre', 'materia', 'calificacion', 'estado', 'promedio']
        actual_headers = [header.lower() for header in reader.fieldnames]
        
        for header in expected_headers:
            assert header in actual_headers
        
        # Verificar contenido del profesor
        prof_row = next((row for row in rows if row['materia'] == 'Física I'), None)
        assert prof_row is not None
        assert 'María García' in prof_row['nombre']
    
    def test_csv_format_compliance(self):
        """Test de cumplimiento del formato CSV requerido."""
        service = ReporteService()
        
        # Generar reporte de estudiante
        csv_content = service.generate_student_report(self.student.id)
        
        # Verificar formato CSV válido
        try:
            reader = csv.reader(io.StringIO(csv_content))
            rows = list(reader)
            assert len(rows) > 1  # Al menos header + 1 fila de datos
        except csv.Error:
            pytest.fail("El contenido generado no es CSV válido")
        
        # Verificar que cada fila tiene el mismo número de columnas
        header_cols = len(rows[0])
        for i, row in enumerate(rows[1:], 1):
            assert len(row) == header_cols, f"Fila {i} tiene {len(row)} columnas, esperaba {header_cols}"
    
    def test_csv_content_accuracy(self):
        """Test de precisión del contenido en CSV."""
        service = ReporteService()
        
        # Generar reporte
        csv_content = service.generate_student_report(self.student.id)
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)
        
        # Verificar información específica del estudiante
        math_row = next((row for row in rows if 'Matemáticas I' in row['materia']), None)
        assert math_row is not None
        
        # Verificar datos exactos
        assert 'Juan Pérez' in math_row['nombre']
        assert math_row['estado'].lower() == 'aprobada'
        assert float(math_row['calificacion']) == 4.5
        
        # Verificar promedio general
        physics_row = next((row for row in rows if 'Física I' in row['materia']), None)
        assert physics_row is not None
        
        # Promedio de Física I: (3.8 * 0.6) + (4.2 * 0.4) = 2.28 + 1.68 = 3.96
        expected_physics_grade = (3.8 * 0.6) + (4.2 * 0.4)
        assert abs(float(physics_row['calificacion']) - expected_physics_grade) < 0.01
    
    def test_empty_report_handling(self):
        """Test de manejo de reportes vacíos."""
        # Crear estudiante sin inscripciones
        empty_student = User.objects.create_user(
            username='empty_student',
            email='empty@test.com',
            password='testpass123',
            role='estudiante',
            first_name='Empty',
            last_name='Student'
        )
        
        service = ReporteService()
        
        # Generar reporte vacío
        csv_content = service.generate_student_report(empty_student.id)
        
        # Debe generar CSV válido aunque esté vacío
        assert csv_content is not None
        
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)
        
        # Debe tener headers pero sin filas de datos
        assert len(rows) == 0
        assert reader.fieldnames is not None
    
    def test_special_characters_in_csv(self):
        """Test de manejo de caracteres especiales en CSV."""
        # Crear materia con caracteres especiales
        special_materia = Materia.objects.create(
            codigo='ESP001',
            nombre='Español & Comunicación, "Nivel I"',
            creditos=2,
            profesor=self.professor
        )
        
        # Crear inscripción
        special_inscripcion = Inscripcion.objects.create(
            estudiante=self.student,
            materia=special_materia,
            periodo=self.period,
            estado='activa'
        )
        
        # Crear calificación
        Calificacion.objects.create(
            inscripcion=special_inscripcion,
            nota=3.5,
            tipo='final',
            fecha='2024-05-15'
        )
        
        service = ReporteService()
        csv_content = service.generate_student_report(self.student.id)
        
        # Verificar que CSV se genera correctamente con caracteres especiales
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)
        
        special_row = next((row for row in rows if 'Español & Comunicación' in row['materia']), None)
        assert special_row is not None
        assert '"Nivel I"' in special_row['materia']


@pytest.mark.django_db
class TestReporteProtectedEndpoints:
    """Tests para endpoints protegidos de reportes."""
    
    def setup_method(self):
        """Configuración inicial para tests de endpoints."""
        self.client = APIClient()
        
        # Crear usuarios
        self.admin_user = User.objects.create_user(
            username='admin_endpoint',
            email='admin@test.com',
            password='testpass123',
            role='admin'
        )
        
        self.student = User.objects.create_user(
            username='student_endpoint',
            email='student@test.com',
            password='testpass123',
            role='estudiante'
        )
        
        self.professor = User.objects.create_user(
            username='prof_endpoint',
            email='prof@test.com',
            password='testpass123',
            role='profesor'
        )
        
        self.other_student = User.objects.create_user(
            username='other_student',
            email='other@test.com',
            password='testpass123',
            role='estudiante'
        )
    
    def get_token_for_user(self, user):
        """Helper para obtener token JWT."""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def test_student_report_endpoint_requires_authentication(self):
        """Test de que endpoint de reporte estudiante requiere autenticación."""
        url = f'/api/reportes/estudiante/{self.student.id}/'
        
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_professor_report_endpoint_requires_authentication(self):
        """Test de que endpoint de reporte profesor requiere autenticación."""
        url = f'/api/reportes/profesor/{self.professor.id}/'
        
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_admin_can_access_any_student_report(self):
        """Test de que admin puede acceder a reporte de cualquier estudiante."""
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = f'/api/reportes/estudiante/{self.student.id}/'
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response['Content-Type'] == 'text/csv'
    
    def test_admin_can_access_any_professor_report(self):
        """Test de que admin puede acceder a reporte de cualquier profesor."""
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = f'/api/reportes/profesor/{self.professor.id}/'
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response['Content-Type'] == 'text/csv'
    
    def test_student_can_access_own_report(self):
        """Test de que estudiante puede acceder a su propio reporte."""
        token = self.get_token_for_user(self.student)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = f'/api/reportes/estudiante/{self.student.id}/'
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response['Content-Type'] == 'text/csv'
    
    def test_student_cannot_access_other_student_report(self):
        """Test de que estudiante no puede acceder a reporte de otro estudiante."""
        token = self.get_token_for_user(self.student)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = f'/api/reportes/estudiante/{self.other_student.id}/'
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_professor_can_access_own_report(self):
        """Test de que profesor puede acceder a su propio reporte."""
        token = self.get_token_for_user(self.professor)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = f'/api/reportes/profesor/{self.professor.id}/'
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response['Content-Type'] == 'text/csv'
    
    def test_student_cannot_access_professor_report(self):
        """Test de que estudiante no puede acceder a reporte de profesor."""
        token = self.get_token_for_user(self.student)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = f'/api/reportes/profesor/{self.professor.id}/'
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_csv_download_filename(self):
        """Test de que el archivo CSV se descarga con nombre correcto."""
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = f'/api/reportes/estudiante/{self.student.id}/'
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verificar header Content-Disposition
        content_disposition = response.get('Content-Disposition', '')
        assert 'attachment' in content_disposition
        assert 'filename=' in content_disposition
        assert f'estudiante_{self.student.id}' in content_disposition
    
    def test_nonexistent_user_report(self):
        """Test de reporte para usuario que no existe."""
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = '/api/reportes/estudiante/99999/'
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_invalid_user_type_for_student_report(self):
        """Test de reporte de estudiante para usuario que no es estudiante."""
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Intentar generar reporte de estudiante para un profesor
        url = f'/api/reportes/estudiante/{self.professor.id}/'
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_invalid_user_type_for_professor_report(self):
        """Test de reporte de profesor para usuario que no es profesor."""
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Intentar generar reporte de profesor para un estudiante
        url = f'/api/reportes/profesor/{self.student.id}/'
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestReporteGeneradoModel:
    """Tests para el modelo ReporteGenerado."""
    
    def setup_method(self):
        """Configuración inicial."""
        self.user = User.objects.create_user(
            username='user_modelo',
            email='user@test.com',
            password='testpass123',
            role='estudiante'
        )
        
        self.admin = User.objects.create_user(
            username='admin_modelo',
            email='admin@test.com',
            password='testpass123',
            role='admin'
        )
    
    def test_create_reporte_generado(self):
        """Test de creación de registro de reporte generado."""
        reporte = ReporteGenerado.objects.create(
            usuario=self.user,
            tipo='estudiante',
            generado_por=self.admin,
            archivo_csv='test_file.csv',
            estado='completado'
        )
        
        assert reporte.usuario == self.user
        assert reporte.tipo == 'estudiante'
        assert reporte.generado_por == self.admin
        assert reporte.archivo_csv == 'test_file.csv'
        assert reporte.estado == 'completado'
        assert reporte.fecha_generacion is not None
    
    def test_reporte_tipo_choices(self):
        """Test de opciones válidas para tipo de reporte."""
        valid_tipos = ['estudiante', 'profesor']
        
        for tipo in valid_tipos:
            reporte = ReporteGenerado.objects.create(
                usuario=self.user,
                tipo=tipo,
                generado_por=self.admin,
                estado='completado'
            )
            assert reporte.tipo == tipo
            reporte.delete()
    
    def test_reporte_estado_choices(self):
        """Test de opciones válidas para estado de reporte."""
        valid_estados = ['pendiente', 'generando', 'completado', 'error']
        
        for estado in valid_estados:
            reporte = ReporteGenerado.objects.create(
                usuario=self.user,
                tipo='estudiante',
                generado_por=self.admin,
                estado=estado
            )
            assert reporte.estado == estado
            reporte.delete()
    
    def test_reporte_str_representation(self):
        """Test de representación en string del reporte."""
        reporte = ReporteGenerado.objects.create(
            usuario=self.user,
            tipo='estudiante',
            generado_por=self.admin,
            estado='completado'
        )
        
        expected = f"Reporte estudiante - {self.user.username} (completado)"
        assert str(reporte) == expected
    
    def test_reporte_timestamps(self):
        """Test de timestamps automáticos."""
        reporte = ReporteGenerado.objects.create(
            usuario=self.user,
            tipo='estudiante',
            generado_por=self.admin,
            estado='completado'
        )
        
        assert reporte.fecha_generacion is not None
        assert reporte.fecha_actualizacion is not None
        assert reporte.fecha_generacion <= reporte.fecha_actualizacion 