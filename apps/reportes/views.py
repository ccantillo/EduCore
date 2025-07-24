import os
from django.http import HttpResponse, FileResponse
from django.conf import settings
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta

from .models import ReporteGenerado
from .serializers import (
    ReporteGeneradoSerializer,
    ReporteGeneradoListSerializer,
    ReporteGeneradoDetalleSerializer,
    ReporteEstudianteSerializer,
    ReporteProfesorSerializer,
    ReporteGeneralSerializer,
    ReporteFiltroSerializer,
    ReporteEstadisticasSerializer
)
from .services import ReporteService
from apps.users.permissions import IsAdminUser, IsProfesorUser


class ReporteViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de reportes generados."""
    
    # El modelo ReporteGenerado no tiene relaciones complejas, por lo que no se requiere select_related ni prefetch_related aquí.
    queryset = ReporteGenerado.objects.all()
    serializer_class = ReporteGeneradoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Retornar el serializer apropiado según la acción."""
        if self.action == 'retrieve':
            return ReporteGeneradoDetalleSerializer
        elif self.action == 'list':
            return ReporteGeneradoListSerializer
        elif self.action == 'estadisticas':
            return ReporteEstadisticasSerializer
        return ReporteGeneradoSerializer
    
    def get_permissions(self):
        """Configurar permisos según la acción."""
        if self.action in ['create', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filtrar queryset según el rol del usuario."""
        user = self.request.user
        
        if user.is_admin:
            return ReporteGenerado.objects.all()
        else:
            return ReporteGenerado.objects.filter(solicitante=user)
    
    def list(self, request, *args, **kwargs):
        """Listar reportes con filtros opcionales."""
        queryset = self.get_queryset()
        
        # Aplicar filtros
        serializer = ReporteFiltroSerializer(data=request.query_params)
        if serializer.is_valid():
            filtros = serializer.validated_data
            
            if filtros.get('tipo'):
                queryset = queryset.filter(tipo=filtros['tipo'])
            
            if filtros.get('estado'):
                queryset = queryset.filter(estado=filtros['estado'])
            
            if filtros.get('solicitante_id'):
                queryset = queryset.filter(solicitante_id=filtros['solicitante_id'])
            
            if filtros.get('fecha_desde'):
                queryset = queryset.filter(created_at__date__gte=filtros['fecha_desde'])
            
            if filtros.get('fecha_hasta'):
                queryset = queryset.filter(created_at__date__lte=filtros['fecha_hasta'])
        
        # Ordenar por fecha de creación (más recientes primero)
        queryset = queryset.order_by('-created_at')
        
        # Paginar resultados
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def generar_estudiante(self, request):
        """Generar reporte CSV de un estudiante."""
        serializer = ReporteEstudianteSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # Verificar permisos
                if not (request.user.is_admin or request.user.is_profesor):
                    return Response(
                        {'error': 'No tienes permisos para generar reportes de estudiantes.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                
                # Generar reporte
                service = ReporteService(request.user)
                reporte = service.generar_reporte_estudiante(
                    estudiante_id=serializer.validated_data['estudiante_id'],
                    periodo_id=serializer.validated_data.get('periodo_id')
                )
                
                return Response({
                    'mensaje': 'Reporte generado exitosamente',
                    'reporte_id': reporte.id,
                    'nombre_archivo': reporte.nombre_archivo,
                    'estado': reporte.estado
                }, status=status.HTTP_201_CREATED)
                
            except ValueError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                return Response(
                    {'error': f'Error al generar reporte: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def generar_profesor(self, request):
        """Generar reporte CSV de un profesor."""
        serializer = ReporteProfesorSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # Verificar permisos (solo admins pueden generar reportes de profesores)
                if not request.user.is_admin:
                    return Response(
                        {'error': 'Solo los administradores pueden generar reportes de profesores.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                
                # Generar reporte
                service = ReporteService(request.user)
                reporte = service.generar_reporte_profesor(
                    profesor_id=serializer.validated_data['profesor_id'],
                    periodo_id=serializer.validated_data.get('periodo_id')
                )
                
                return Response({
                    'mensaje': 'Reporte generado exitosamente',
                    'reporte_id': reporte.id,
                    'nombre_archivo': reporte.nombre_archivo,
                    'estado': reporte.estado
                }, status=status.HTTP_201_CREATED)
                
            except ValueError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                return Response(
                    {'error': f'Error al generar reporte: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def generar_general(self, request):
        """Generar reporte CSV general del sistema."""
        serializer = ReporteGeneralSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # Verificar permisos (solo admins pueden generar reportes generales)
                if not request.user.is_admin:
                    return Response(
                        {'error': 'Solo los administradores pueden generar reportes generales.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                
                # Generar reporte
                service = ReporteService(request.user)
                reporte = service.generar_reporte_general(
                    periodo_id=serializer.validated_data.get('periodo_id')
                )
                
                return Response({
                    'mensaje': 'Reporte general generado exitosamente',
                    'reporte_id': reporte.id,
                    'nombre_archivo': reporte.nombre_archivo,
                    'estado': reporte.estado
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                return Response(
                    {'error': f'Error al generar reporte: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def descargar(self, request, pk=None):
        """Descargar el archivo CSV del reporte."""
        try:
            reporte = self.get_object()
            
            # Verificar que el reporte esté completado
            if not reporte.es_completado:
                return Response(
                    {
                        'error': 'El reporte aún no está listo para descargar.',
                        'estado_actual': reporte.estado,
                        'reporte_id': reporte.id
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verificar que el archivo existe
            if not reporte.ruta_archivo or not os.path.exists(reporte.ruta_archivo):
                return Response(
                    {
                        'error': 'El archivo del reporte no se encuentra.',
                        'ruta_esperada': reporte.ruta_archivo,
                        'reporte_id': reporte.id
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Crear respuesta de archivo
            response = FileResponse(
                open(reporte.ruta_archivo, 'rb'),
                content_type='text/csv'
            )
            response['Content-Disposition'] = f'attachment; filename="{reporte.nombre_archivo}"'
            
            return response
            
        except ReporteGenerado.DoesNotExist:
            return Response(
                {
                    'error': f'No se encontró el reporte con ID {pk}.',
                    'mensaje': 'Verifique que el ID del reporte sea correcto.'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {
                    'error': f'Error al descargar reporte: {str(e)}',
                    'reporte_id': pk,
                    'tipo_error': type(e).__name__
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Obtener estadísticas de reportes."""
        try:
            queryset = self.get_queryset()
            
            # Estadísticas básicas
            total_reportes = queryset.count()
            reportes_completados = queryset.filter(estado='completado').count()
            reportes_pendientes = queryset.filter(estado='pendiente').count()
            reportes_error = queryset.filter(estado='error').count()
            
            # Promedio de tiempo de generación
            reportes_con_tiempo = queryset.filter(
                estado='completado',
                completado_at__isnull=False
            )
            
            if reportes_con_tiempo.exists():
                tiempos = [
                    (r.completado_at - r.created_at).total_seconds()
                    for r in reportes_con_tiempo
                ]
                promedio_tiempo = sum(tiempos) / len(tiempos)
            else:
                promedio_tiempo = 0
            
            # Reportes por tipo
            reportes_por_tipo = dict(
                queryset.values('tipo').annotate(count=Count('id')).values_list('tipo', 'count')
            )
            
            # Reportes por estado
            reportes_por_estado = dict(
                queryset.values('estado').annotate(count=Count('id')).values_list('estado', 'count')
            )
            
            stats = {
                'total_reportes': total_reportes,
                'reportes_completados': reportes_completados,
                'reportes_pendientes': reportes_pendientes,
                'reportes_error': reportes_error,
                'promedio_tiempo_generacion': round(promedio_tiempo, 2),
                'reportes_por_tipo': reportes_por_tipo,
                'reportes_por_estado': reportes_por_estado
            }
            
            serializer = ReporteEstadisticasSerializer(stats)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': f'Error al obtener estadísticas: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def limpiar_antiguos(self, request):
        """Limpiar reportes antiguos (solo administradores)."""
        if not request.user.is_admin:
            return Response(
                {'error': 'Solo los administradores pueden limpiar reportes antiguos.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            dias = request.data.get('dias', 30)
            count = ReporteGenerado.limpiar_reportes_antiguos(dias)
            
            return Response({
                'mensaje': f'Se eliminaron {count} reportes antiguos (más de {dias} días)',
                'reportes_eliminados': count
            })
            
        except Exception as e:
            return Response(
                {'error': f'Error al limpiar reportes: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def mis_reportes(self, request):
        """Obtener reportes del usuario actual."""
        reportes = self.get_queryset().filter(solicitante=request.user)
        serializer = self.get_serializer(reportes, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def buscar(self, request):
        """Buscar reportes por nombre de archivo."""
        query = request.query_params.get('q', '')
        
        if not query:
            return Response(
                {'error': 'Se requiere el parámetro de búsqueda "q".'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reportes = self.get_queryset().filter(
            Q(nombre_archivo__icontains=query) |
            Q(tipo__icontains=query)
        )
        
        serializer = self.get_serializer(reportes, many=True)
        return Response(serializer.data)


# Endpoints específicos para reportes protegidos
class ReporteEstudianteViewSet(viewsets.ViewSet):
    """ViewSet específico para reportes de estudiantes."""
    
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        """Configurar permisos."""
        if self.action == 'create':
            permission_classes = [IsAdminUser]  # Only admin can create, but let professors access through the action method
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['get'], url_path='reporte')
    def generar_reporte(self, request, pk=None):
        """Generar reporte CSV de un estudiante específico."""
        try:
            # Verificar que el estudiante existe
            from apps.users.models import User
            estudiante = User.objects.get(id=pk, role='estudiante')
            
            # Verificar permisos
            if not (request.user.is_admin or request.user.is_profesor):
                return Response(
                    {'error': 'No tienes permisos para generar reportes de estudiantes.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Obtener período opcional
            periodo_id = request.query_params.get('periodo_id')
            
            # Generar reporte
            service = ReporteService(request.user)
            reporte = service.generar_reporte_estudiante(
                estudiante_id=pk,
                periodo_id=periodo_id
            )
            
            return Response({
                'mensaje': 'Reporte generado exitosamente',
                'reporte_id': reporte.id,
                'nombre_archivo': reporte.nombre_archivo,
                'estado': reporte.estado
            }, status=status.HTTP_201_CREATED)
            
        except User.DoesNotExist:
            return Response(
                {'error': 'Estudiante no encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Error al generar reporte: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReporteProfesorViewSet(viewsets.ViewSet):
    """ViewSet específico para reportes de profesores."""
    
    permission_classes = [IsAdminUser]
    
    @action(detail=True, methods=['get'], url_path='reporte')
    def generar_reporte(self, request, pk=None):
        """Generar reporte CSV de un profesor específico."""
        try:
            # Verificar que el profesor existe
            from apps.users.models import User
            profesor = User.objects.get(id=pk, role='profesor')
            
            # Obtener período opcional
            periodo_id = request.query_params.get('periodo_id')
            
            # Generar reporte
            service = ReporteService(request.user)
            reporte = service.generar_reporte_profesor(
                profesor_id=pk,
                periodo_id=periodo_id
            )
            
            return Response({
                'mensaje': 'Reporte generado exitosamente',
                'reporte_id': reporte.id,
                'nombre_archivo': reporte.nombre_archivo,
                'estado': reporte.estado
            }, status=status.HTTP_201_CREATED)
            
        except User.DoesNotExist:
            return Response(
                {'error': 'Profesor no encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Error al generar reporte: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 