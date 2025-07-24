import csv
import os
from django.conf import settings
from django.utils import timezone
from django.db.models import Avg, Count, Q
from datetime import datetime

from .models import ReporteGenerado
from apps.users.models import User
from apps.inscripciones.models import Inscripcion, Calificacion
from apps.materias.models import Materia, Periodo


class ReporteService:
    """Servicio para generar reportes CSV del sistema académico."""
    
    def __init__(self, solicitante):
        self.solicitante = solicitante
        self.reports_dir = os.path.join(settings.MEDIA_ROOT, 'reportes')
        
        # Crear directorio si no existe
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)
    
    def generar_reporte_estudiante(self, estudiante_id, periodo_id=None):
        """
        Generar reporte CSV detallado de un estudiante.
        
        Args:
            estudiante_id: ID del estudiante
            periodo_id: ID del período (opcional)
        
        Returns:
            ReporteGenerado: Instancia del reporte generado
        """
        try:
            # Verificar que el estudiante existe
            estudiante = User.objects.get(id=estudiante_id, role='estudiante')
            
            # Crear registro del reporte
            reporte = ReporteGenerado.objects.create(
                solicitante=self.solicitante,
                tipo='estudiante',
                nombre_archivo=f"reporte_estudiante_{estudiante.username}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv",
                parametros={
                    'estudiante_id': estudiante_id,
                    'periodo_id': periodo_id,
                    'generado_por': self.solicitante.username
                }
            )
            
            reporte.marcar_generando()
            
            # Generar el archivo CSV
            ruta_archivo = os.path.join(self.reports_dir, reporte.nombre_archivo)
            
            with open(ruta_archivo, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Escribir encabezados
                writer.writerow([
                    'REPORTE ACADÉMICO - ESTUDIANTE',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    ''
                ])
                
                writer.writerow([
                    'Información del Estudiante',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    ''
                ])
                
                writer.writerow([
                    'ID',
                    'Username',
                    'Nombre Completo',
                    'Email',
                    'Rol',
                    'Fecha de Registro',
                    'Estado',
                    '',
                    '',
                    ''
                ])
                
                # Información del estudiante
                writer.writerow([
                    estudiante.id,
                    estudiante.username,
                    estudiante.get_full_name(),
                    estudiante.email,
                    estudiante.get_role_display(),
                    estudiante.date_joined.strftime('%Y-%m-%d %H:%M'),
                    'Activo' if estudiante.is_active else 'Inactivo',
                    '',
                    '',
                    ''
                ])
                
                writer.writerow([])  # Línea en blanco
                
                # Obtener inscripciones
                inscripciones_query = Inscripcion.objects.filter(estudiante=estudiante)
                if periodo_id:
                    inscripciones_query = inscripciones_query.filter(periodo_id=periodo_id)
                
                inscripciones = inscripciones_query.select_related(
                    'materia', 'periodo', 'materia__profesor'
                ).prefetch_related('calificaciones').order_by('periodo__nombre', 'materia__codigo')
                
                # Escribir encabezados de materias
                writer.writerow([
                    'MATERIAS INSCRITAS',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    ''
                ])
                
                writer.writerow([
                    'Código',
                    'Nombre',
                    'Créditos',
                    'Período',
                    'Profesor',
                    'Estado',
                    'Nota Final',
                    'Promedio',
                    'Calificaciones',
                    'Comentarios'
                ])
                
                registros_procesados = 0
                total_creditos = 0
                materias_aprobadas = 0
                promedio_general = 0
                
                # Escribir datos de materias
                for inscripcion in inscripciones:
                    # Calcular promedio de calificaciones
                    calificaciones = inscripcion.calificaciones.all()
                    promedio_materia = calificaciones.aggregate(Avg('nota'))['nota__avg'] or 0
                    
                    # Obtener calificaciones como texto
                    calificaciones_texto = ', '.join([
                        f"{c.get_tipo_display()}: {c.nota}/5.0" 
                        for c in calificaciones
                    ])
                    
                    writer.writerow([
                        inscripcion.materia.codigo,
                        inscripcion.materia.nombre,
                        inscripcion.materia.creditos,
                        inscripcion.periodo.nombre,
                        inscripcion.materia.profesor.get_full_name() if inscripcion.materia.profesor else 'Por asignar',
                        inscripcion.get_estado_display(),
                        inscripcion.nota_final or 'Pendiente',
                        f"{promedio_materia:.2f}" if promedio_materia > 0 else 'Sin calificaciones',
                        calificaciones_texto,
                        inscripcion.comentarios or ''
                    ])
                    
                    registros_procesados += 1
                    total_creditos += inscripcion.materia.creditos
                    
                    if inscripcion.estado == 'aprobada':
                        materias_aprobadas += 1
                        promedio_general += inscripcion.nota_final or 0
                
                writer.writerow([])  # Línea en blanco
                
                # Escribir resumen
                writer.writerow([
                    'RESUMEN ACADÉMICO',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    ''
                ])
                
                promedio_final = promedio_general / materias_aprobadas if materias_aprobadas > 0 else 0
                
                writer.writerow([
                    'Total Materias',
                    'Materias Aprobadas',
                    'Materias Reprobadas',
                    'Total Créditos',
                    'Promedio General',
                    'Porcentaje Aprobación',
                    '',
                    '',
                    '',
                    ''
                ])
                
                writer.writerow([
                    registros_procesados,
                    materias_aprobadas,
                    registros_procesados - materias_aprobadas,
                    total_creditos,
                    f"{promedio_final:.2f}" if promedio_final > 0 else 'N/A',
                    f"{(materias_aprobadas / registros_procesados * 100):.1f}%" if registros_procesados > 0 else '0%',
                    '',
                    '',
                    '',
                    ''
                ])
                
                writer.writerow([])  # Línea en blanco
                
                # Información del reporte
                writer.writerow([
                    'INFORMACIÓN DEL REPORTE',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    ''
                ])
                
                writer.writerow([
                    'Generado por',
                    'Fecha de generación',
                    'Período filtrado',
                    'Registros procesados',
                    '',
                    '',
                    '',
                    '',
                    '',
                    ''
                ])
                
                writer.writerow([
                    self.solicitante.get_full_name(),
                    timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                    Periodo.objects.get(id=periodo_id).nombre if periodo_id else 'Todos los períodos',
                    registros_procesados,
                    '',
                    '',
                    '',
                    '',
                    '',
                    ''
                ])
            
            # Actualizar reporte
            reporte.ruta_archivo = ruta_archivo
            reporte.marcar_completado(registros_procesados)
            
            return reporte
            
        except User.DoesNotExist:
            if 'reporte' in locals():
                reporte.marcar_error("Estudiante no encontrado")
            raise ValueError("Estudiante no encontrado")
        except Exception as e:
            if 'reporte' in locals():
                reporte.marcar_error(str(e))
            raise
    
    def generar_reporte_profesor(self, profesor_id, periodo_id=None):
        """
        Generar reporte CSV detallado de un profesor.
        
        Args:
            profesor_id: ID del profesor
            periodo_id: ID del período (opcional)
        
        Returns:
            ReporteGenerado: Instancia del reporte generado
        """
        try:
            # Verificar que el profesor existe
            profesor = User.objects.get(id=profesor_id, role='profesor')
            
            # Crear registro del reporte
            reporte = ReporteGenerado.objects.create(
                solicitante=self.solicitante,
                tipo='profesor',
                nombre_archivo=f"reporte_profesor_{profesor.username}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv",
                parametros={
                    'profesor_id': profesor_id,
                    'periodo_id': periodo_id,
                    'generado_por': self.solicitante.username
                }
            )
            
            reporte.marcar_generando()
            
            # Generar el archivo CSV
            ruta_archivo = os.path.join(self.reports_dir, reporte.nombre_archivo)
            
            with open(ruta_archivo, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Escribir encabezados
                writer.writerow([
                    'REPORTE ACADÉMICO - PROFESOR',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    ''
                ])
                
                writer.writerow([
                    'Información del Profesor',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    ''
                ])
                
                writer.writerow([
                    'ID',
                    'Username',
                    'Nombre Completo',
                    'Email',
                    'Rol',
                    'Fecha de Registro',
                    'Estado',
                    '',
                    '',
                    ''
                ])
                
                # Información del profesor
                writer.writerow([
                    profesor.id,
                    profesor.username,
                    profesor.get_full_name(),
                    profesor.email,
                    profesor.get_role_display(),
                    profesor.date_joined.strftime('%Y-%m-%d %H:%M'),
                    'Activo' if profesor.is_active else 'Inactivo',
                    '',
                    '',
                    ''
                ])
                
                writer.writerow([])  # Línea en blanco
                
                # Obtener materias del profesor
                materias_query = Materia.objects.filter(profesor=profesor)
                materias = materias_query.select_related('periodo').order_by('codigo')
                
                # Escribir encabezados de materias
                writer.writerow([
                    'MATERIAS ASIGNADAS',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    ''
                ])
                
                writer.writerow([
                    'Código',
                    'Nombre',
                    'Créditos',
                    'Descripción',
                    'Estado',
                    'Estudiantes Inscritos',
                    'Promedio General',
                    'Porcentaje Aprobación',
                    '',
                    ''
                ])
                
                registros_procesados = 0
                total_estudiantes = 0
                total_promedio = 0
                
                # Escribir datos de materias
                for materia in materias:
                    # Obtener inscripciones de la materia
                    inscripciones_query = Inscripcion.objects.filter(materia=materia)
                    if periodo_id:
                        inscripciones_query = inscripciones_query.filter(periodo_id=periodo_id)
                    
                    inscripciones = inscripciones_query.select_related('estudiante')
                    
                    # Calcular estadísticas
                    num_estudiantes = inscripciones.count()
                    aprobados = inscripciones.filter(estado='aprobada').count()
                    promedio_materia = inscripciones.aggregate(Avg('nota_final'))['nota_final__avg'] or 0
                    porcentaje_aprobacion = (aprobados / num_estudiantes * 100) if num_estudiantes > 0 else 0
                    
                    writer.writerow([
                        materia.codigo,
                        materia.nombre,
                        materia.creditos,
                        materia.descripcion or 'Sin descripción',
                        'Activa' if materia.activa else 'Inactiva',
                        num_estudiantes,
                        f"{promedio_materia:.2f}" if promedio_materia > 0 else 'Sin calificaciones',
                        f"{porcentaje_aprobacion:.1f}%",
                        '',
                        ''
                    ])
                    
                    registros_procesados += 1
                    total_estudiantes += num_estudiantes
                    total_promedio += promedio_materia
                
                writer.writerow([])  # Línea en blanco
                
                # Escribir detalle de estudiantes por materia
                writer.writerow([
                    'DETALLE DE ESTUDIANTES POR MATERIA',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    ''
                ])
                
                writer.writerow([
                    'Materia',
                    'Estudiante',
                    'Email',
                    'Estado',
                    'Nota Final',
                    'Calificaciones',
                    'Fecha Inscripción',
                    '',
                    '',
                    ''
                ])
                
                for materia in materias:
                    inscripciones_query = Inscripcion.objects.filter(materia=materia)
                    if periodo_id:
                        inscripciones_query = inscripciones_query.filter(periodo_id=periodo_id)
                    
                    inscripciones = inscripciones_query.select_related('estudiante').prefetch_related('calificaciones')
                    
                    for inscripcion in inscripciones:
                        # Obtener calificaciones como texto
                        calificaciones_texto = ', '.join([
                            f"{c.get_tipo_display()}: {c.nota}/5.0" 
                            for c in inscripcion.calificaciones.all()
                        ])
                        
                        writer.writerow([
                            f"{materia.codigo} - {materia.nombre}",
                            inscripcion.estudiante.get_full_name(),
                            inscripcion.estudiante.email,
                            inscripcion.get_estado_display(),
                            inscripcion.nota_final or 'Pendiente',
                            calificaciones_texto,
                            inscripcion.created_at.strftime('%Y-%m-%d'),
                            '',
                            '',
                            ''
                        ])
                
                writer.writerow([])  # Línea en blanco
                
                # Escribir resumen
                writer.writerow([
                    'RESUMEN DEL PROFESOR',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    ''
                ])
                
                promedio_final = total_promedio / registros_procesados if registros_procesados > 0 else 0
                
                writer.writerow([
                    'Total Materias',
                    'Total Estudiantes',
                    'Promedio General',
                    'Materias Activas',
                    'Materias Inactivas',
                    '',
                    '',
                    '',
                    '',
                    ''
                ])
                
                writer.writerow([
                    registros_procesados,
                    total_estudiantes,
                    f"{promedio_final:.2f}" if promedio_final > 0 else 'N/A',
                    materias.filter(activa=True).count(),
                    materias.filter(activa=False).count(),
                    '',
                    '',
                    '',
                    '',
                    ''
                ])
                
                writer.writerow([])  # Línea en blanco
                
                # Información del reporte
                writer.writerow([
                    'INFORMACIÓN DEL REPORTE',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    ''
                ])
                
                writer.writerow([
                    'Generado por',
                    'Fecha de generación',
                    'Período filtrado',
                    'Registros procesados',
                    '',
                    '',
                    '',
                    '',
                    '',
                    ''
                ])
                
                writer.writerow([
                    self.solicitante.get_full_name(),
                    timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                    Periodo.objects.get(id=periodo_id).nombre if periodo_id else 'Todos los períodos',
                    registros_procesados,
                    '',
                    '',
                    '',
                    '',
                    '',
                    ''
                ])
            
            # Actualizar reporte
            reporte.ruta_archivo = ruta_archivo
            reporte.marcar_completado(registros_procesados)
            
            return reporte
            
        except User.DoesNotExist:
            if 'reporte' in locals():
                reporte.marcar_error("Profesor no encontrado")
            raise ValueError("Profesor no encontrado")
        except Exception as e:
            if 'reporte' in locals():
                reporte.marcar_error(str(e))
            raise
    
    def generar_reporte_general(self, periodo_id=None):
        """
        Generar reporte CSV general del sistema.
        
        Args:
            periodo_id: ID del período (opcional)
        
        Returns:
            ReporteGenerado: Instancia del reporte generado
        """
        try:
            # Crear registro del reporte
            reporte = ReporteGenerado.objects.create(
                solicitante=self.solicitante,
                tipo='general',
                nombre_archivo=f"reporte_general_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv",
                parametros={
                    'periodo_id': periodo_id,
                    'generado_por': self.solicitante.username
                }
            )
            
            reporte.marcar_generando()
            
            # Generar el archivo CSV
            ruta_archivo = os.path.join(self.reports_dir, reporte.nombre_archivo)
            
            with open(ruta_archivo, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Escribir encabezados
                writer.writerow([
                    'REPORTE GENERAL DEL SISTEMA ACADÉMICO',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    ''
                ])
                
                # Estadísticas generales
                writer.writerow([
                    'ESTADÍSTICAS GENERALES',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    ''
                ])
                
                # Obtener estadísticas
                total_estudiantes = User.objects.filter(role='estudiante').count()
                total_profesores = User.objects.filter(role='profesor').count()
                total_materias = Materia.objects.count()
                total_inscripciones = Inscripcion.objects.count()
                
                if periodo_id:
                    total_inscripciones = Inscripcion.objects.filter(periodo_id=periodo_id).count()
                
                promedio_general = Inscripcion.objects.aggregate(Avg('nota_final'))['nota_final__avg'] or 0
                aprobados = Inscripcion.objects.filter(estado='aprobada').count()
                porcentaje_aprobacion = (aprobados / total_inscripciones * 100) if total_inscripciones > 0 else 0
                
                writer.writerow([
                    'Total Estudiantes',
                    'Total Profesores',
                    'Total Materias',
                    'Total Inscripciones',
                    'Promedio General',
                    'Porcentaje Aprobación',
                    '',
                    '',
                    '',
                    ''
                ])
                
                writer.writerow([
                    total_estudiantes,
                    total_profesores,
                    total_materias,
                    total_inscripciones,
                    f"{promedio_general:.2f}" if promedio_general > 0 else 'N/A',
                    f"{porcentaje_aprobacion:.1f}%",
                    '',
                    '',
                    '',
                    ''
                ])
                
                writer.writerow([])  # Línea en blanco
                
                # Información del reporte
                writer.writerow([
                    'INFORMACIÓN DEL REPORTE',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    ''
                ])
                
                writer.writerow([
                    'Generado por',
                    'Fecha de generación',
                    'Período filtrado',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    ''
                ])
                
                writer.writerow([
                    self.solicitante.get_full_name(),
                    timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                    Periodo.objects.get(id=periodo_id).nombre if periodo_id else 'Todos los períodos',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    ''
                ])
            
            # Actualizar reporte
            reporte.ruta_archivo = ruta_archivo
            reporte.marcar_completado(1)
            
            return reporte
            
        except Exception as e:
            if 'reporte' in locals():
                reporte.marcar_error(str(e))
            raise 