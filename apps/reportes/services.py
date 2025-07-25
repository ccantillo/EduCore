import csv
import os
from django.conf import settings
from django.utils import timezone
from django.db.models import Avg, Count, Q, Sum
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
                
                # Información del estudiante (header)
                writer.writerow([
                    f'REPORTE ACADÉMICO - {estudiante.get_full_name()}',
                    f'Email: {estudiante.email}',
                    f'Fecha: {timezone.now().strftime("%Y-%m-%d %H:%M")}'
                ])
                writer.writerow([])  # Línea en blanco
                
                # Obtener inscripciones
                inscripciones_query = Inscripcion.objects.filter(estudiante=estudiante)
                if periodo_id:
                    inscripciones_query = inscripciones_query.filter(periodo_id=periodo_id)
                
                inscripciones = inscripciones_query.select_related(
                    'materia', 'periodo', 'materia__profesor'
                ).prefetch_related('calificaciones').order_by('periodo__nombre', 'materia__codigo')
                
                # Headers según requerimientos: Nombre, Materia, Calificación, Estado, Promedio
                writer.writerow([
                    'Estudiante',
                    'Materia',
                    'Código',
                    'Créditos',
                    'Período',
                    'Profesor',
                    'Calificación',
                    'Estado',
                    'Promedio Materia'
                ])
                
                registros_procesados = 0
                total_notas = 0
                materias_con_nota = 0
                
                # Escribir datos de materias
                for inscripcion in inscripciones:
                    # Calcular promedio de calificaciones
                    calificaciones = inscripcion.calificaciones.all()
                    promedio_materia = calificaciones.aggregate(Avg('nota'))['nota__avg'] or 0
                    
                    # Determinar la calificación final
                    calificacion_final = inscripcion.nota_final
                    if calificacion_final is None and promedio_materia > 0:
                        calificacion_final = promedio_materia
                    
                    calificacion_display = f"{calificacion_final:.1f}" if calificacion_final else "Pendiente"
                    promedio_display = f"{promedio_materia:.1f}" if promedio_materia > 0 else "Sin calificar"
                    
                    writer.writerow([
                        estudiante.get_full_name(),
                        inscripcion.materia.nombre,
                        inscripcion.materia.codigo,
                        inscripcion.materia.creditos,
                        inscripcion.periodo.nombre,
                        inscripcion.materia.profesor.get_full_name() if inscripcion.materia.profesor else 'Por asignar',
                        calificacion_display,
                        inscripcion.get_estado_display(),
                        promedio_display
                    ])
                    
                    registros_procesados += 1
                    
                    # Sumar para promedio general
                    if calificacion_final:
                        total_notas += calificacion_final
                        materias_con_nota += 1
                
                # Escribir resumen académico al final
                writer.writerow([])  # Línea en blanco
                writer.writerow(['RESUMEN ACADÉMICO'])
                writer.writerow([])
                
                # Calcular promedio general
                promedio_general = total_notas / materias_con_nota if materias_con_nota > 0 else 0
                materias_aprobadas = sum(1 for insc in inscripciones if insc.estado == 'aprobada')
                
                writer.writerow(['Concepto', 'Valor'])
                writer.writerow(['Total de materias', registros_procesados])
                writer.writerow(['Materias aprobadas', materias_aprobadas])
                writer.writerow(['Materias reprobadas', registros_procesados - materias_aprobadas])
                writer.writerow(['Promedio general', f"{promedio_general:.2f}" if promedio_general > 0 else 'N/A'])
                
                writer.writerow([])  # Línea en blanco
                writer.writerow(['INFORMACIÓN DEL REPORTE'])
                writer.writerow(['Detalle', 'Información'])
                writer.writerow(['Generado por', self.solicitante.get_full_name()])
                writer.writerow(['Fecha de generación', timezone.now().strftime('%Y-%m-%d %H:%M:%S')])
                writer.writerow(['Período filtrado', Periodo.objects.get(id=periodo_id).nombre if periodo_id else 'Todos los períodos'])
                writer.writerow(['Registros procesados', registros_procesados])
            
            # Actualizar reporte
            reporte.ruta_archivo = ruta_archivo
            reporte.marcar_completado(registros_procesados)
            
            return reporte
            
        except User.DoesNotExist:
            if 'reporte' in locals():
                reporte.marcar_error("Estudiante no encontrado")
            raise
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
            raise
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

    def _calcular_estadisticas_estudiante(self, estudiante):
        """Calcular estadísticas de un estudiante."""
        inscripciones = Inscripcion.objects.filter(estudiante=estudiante)
        
        total_materias = inscripciones.count()
        materias_aprobadas = inscripciones.filter(estado='aprobada').count()
        materias_reprobadas = inscripciones.filter(estado='reprobada').count()
        
        # Calcular promedio general
        inscripciones_con_nota = inscripciones.filter(nota_final__isnull=False)
        promedio_general = 0
        if inscripciones_con_nota.exists():
            promedio_general = inscripciones_con_nota.aggregate(
                promedio=Avg('nota_final')
            )['promedio'] or 0
        
        # Calcular créditos aprobados
        creditos_aprobados = inscripciones.filter(
            estado='aprobada'
        ).aggregate(
            total=Sum('materia__creditos')
        )['total'] or 0
        
        return {
            'promedio_general': round(promedio_general, 2),
            'total_materias': total_materias,
            'materias_aprobadas': materias_aprobadas,
            'materias_reprobadas': materias_reprobadas,
            'creditos_aprobados': creditos_aprobados
        }
    
    def _calcular_estadisticas_profesor(self, profesor):
        """Calcular estadísticas de un profesor."""
        materias = Materia.objects.filter(profesor=profesor)
        
        total_materias = materias.count()
        total_estudiantes = Inscripcion.objects.filter(
            materia__profesor=profesor
        ).count()
        
        # Calcular promedio de las materias
        materias_con_promedio = materias.annotate(
            promedio_materia=Avg('inscripciones__nota_final')
        )
        
        promedio_materias = 0
        if materias_con_promedio.exists():
            promedios = [m.promedio_materia for m in materias_con_promedio if m.promedio_materia]
            if promedios:
                promedio_materias = sum(promedios) / len(promedios)
        
        # Calcular total de créditos
        total_creditos = materias.aggregate(
            total=Sum('creditos')
        )['total'] or 0
        
        return {
            'total_materias': total_materias,
            'total_estudiantes': total_estudiantes,
            'promedio_materias': round(promedio_materias, 2),
            'total_creditos': total_creditos
        }
    
    def _escribir_csv_estudiante(self, ruta_archivo, estudiante):
        """Escribir CSV para reporte de estudiante."""
        with open(ruta_archivo, 'w', newline='', encoding='utf-8') as archivo:
            writer = csv.writer(archivo)
            
            # Escribir encabezados
            writer.writerow([
                'Código', 'Materia', 'Créditos', 'Período', 'Profesor',
                'Estado', 'Nota Final', 'Promedio', 'Calificaciones', 'Comentarios'
            ])
            
            # Obtener inscripciones del estudiante
            inscripciones = Inscripcion.objects.filter(
                estudiante=estudiante
            ).select_related('materia', 'periodo', 'materia__profesor')
            
            for inscripcion in inscripciones:
                writer.writerow([
                    inscripcion.materia.codigo,
                    inscripcion.materia.nombre,
                    inscripcion.materia.creditos,
                    inscripcion.periodo.nombre,
                    inscripcion.materia.profesor.get_full_name() if inscripcion.materia.profesor else 'Por asignar',
                    inscripcion.get_estado_display(),
                    inscripcion.nota_final or 'Pendiente',
                    '',  # Promedio específico
                    '',  # Calificaciones detalladas
                    ''   # Comentarios
                ])
    
    def _escribir_csv_profesor(self, ruta_archivo, profesor):
        """Escribir CSV para reporte de profesor."""
        with open(ruta_archivo, 'w', newline='', encoding='utf-8') as archivo:
            writer = csv.writer(archivo)
            
            # Escribir encabezados
            writer.writerow([
                'Código', 'Materia', 'Créditos', 'Estudiantes Inscritos', 
                'Promedio Materia', 'Período'
            ])
            
            # Obtener materias del profesor
            materias = Materia.objects.filter(profesor=profesor)
            
            for materia in materias:
                estudiantes_count = Inscripcion.objects.filter(materia=materia).count()
                promedio = Inscripcion.objects.filter(
                    materia=materia, 
                    nota_final__isnull=False
                ).aggregate(Avg('nota_final'))['nota_final__avg'] or 0
                
                writer.writerow([
                    materia.codigo,
                    materia.nombre,
                    materia.creditos,
                    estudiantes_count,
                    f"{promedio:.2f}" if promedio > 0 else 'Sin calificaciones',
                    'Todos'  # Período
                ])
    
    def _escribir_csv_general(self, ruta_archivo):
        """Escribir CSV para reporte general."""
        with open(ruta_archivo, 'w', newline='', encoding='utf-8') as archivo:
            writer = csv.writer(archivo)
            
            # Escribir encabezados
            writer.writerow([
                'Estudiante', 'Materia', 'Código', 'Estado', 'Nota Final', 'Período'
            ])
            
            # Obtener todas las inscripciones
            inscripciones = Inscripcion.objects.select_related(
                'estudiante', 'materia', 'periodo'
            )
            
            for inscripcion in inscripciones:
                writer.writerow([
                    inscripcion.estudiante.get_full_name(),
                    inscripcion.materia.nombre,
                    inscripcion.materia.codigo,
                    inscripcion.get_estado_display(),
                    inscripcion.nota_final or 'Pendiente',
                    inscripcion.periodo.nombre
                ])
    
    def _format_fecha(self, fecha):
        """Formatear fecha para el reporte."""
        if fecha:
            return fecha.strftime('%d/%m/%Y')
        return 'N/A'
    
    def _format_nota(self, nota):
        """Formatear nota para el reporte."""
        if nota:
            return str(nota)
        return 'N/A'
    
    def cleanup_old_reports(self, days=30):
        """Limpiar reportes antiguos."""
        from datetime import timedelta
        from django.utils import timezone
        
        fecha_limite = timezone.now() - timedelta(days=days)
        reportes_antiguos = ReporteGenerado.objects.filter(
            created_at__lt=fecha_limite
        )
        
        count = reportes_antiguos.count()
        
        # Eliminar archivos físicos
        for reporte in reportes_antiguos:
            if reporte.ruta_archivo and os.path.exists(reporte.ruta_archivo):
                try:
                    os.remove(reporte.ruta_archivo)
                except OSError:
                    pass
        
        # Eliminar registros de BD
        reportes_antiguos.delete()
        
        return count
    
    def generar_reporte_por_periodo(self, periodo_id):
        """Generar reporte por período."""
        try:
            periodo = Periodo.objects.get(id=periodo_id)
            
            reporte = ReporteGenerado.objects.create(
                solicitante=self.solicitante,
                tipo='periodo',
                nombre_archivo=f"reporte_periodo_{periodo.nombre}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv",
                parametros={
                    'periodo_id': periodo_id,
                    'generado_por': self.solicitante.username
                }
            )
            
            # Generar archivo CSV
            ruta_archivo = os.path.join(self.reports_dir, reporte.nombre_archivo)
            
            with open(ruta_archivo, 'w', newline='', encoding='utf-8') as archivo:
                writer = csv.writer(archivo)
                
                writer.writerow([
                    'Estudiante', 'Materia', 'Código', 'Estado', 'Nota Final'
                ])
                
                inscripciones = Inscripcion.objects.filter(
                    periodo=periodo
                ).select_related('estudiante', 'materia')
                
                for inscripcion in inscripciones:
                    writer.writerow([
                        inscripcion.estudiante.get_full_name(),
                        inscripcion.materia.nombre,
                        inscripcion.materia.codigo,
                        inscripcion.get_estado_display(),
                        inscripcion.nota_final or 'Pendiente'
                    ])
            
            reporte.ruta_archivo = ruta_archivo
            reporte.marcar_completado(inscripciones.count())
            
            return reporte
            
        except Periodo.DoesNotExist:
            raise
    
    def generar_reporte_por_materia(self, materia_id):
        """Generar reporte por materia."""
        try:
            materia = Materia.objects.get(id=materia_id)
            
            reporte = ReporteGenerado.objects.create(
                solicitante=self.solicitante,
                tipo='materia',
                nombre_archivo=f"reporte_materia_{materia.codigo}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv",
                parametros={
                    'materia_id': materia_id,
                    'generado_por': self.solicitante.username
                }
            )
            
            # Generar archivo CSV
            ruta_archivo = os.path.join(self.reports_dir, reporte.nombre_archivo)
            
            with open(ruta_archivo, 'w', newline='', encoding='utf-8') as archivo:
                writer = csv.writer(archivo)
                
                writer.writerow([
                    'Estudiante', 'Período', 'Estado', 'Nota Final'
                ])
                
                inscripciones = Inscripcion.objects.filter(
                    materia=materia
                ).select_related('estudiante', 'periodo')
                
                for inscripcion in inscripciones:
                    writer.writerow([
                        inscripcion.estudiante.get_full_name(),
                        inscripcion.periodo.nombre,
                        inscripcion.get_estado_display(),
                        inscripcion.nota_final or 'Pendiente'
                    ])
            
            reporte.ruta_archivo = ruta_archivo
            reporte.marcar_completado(inscripciones.count())
            
            return reporte
            
        except Materia.DoesNotExist:
            raise 