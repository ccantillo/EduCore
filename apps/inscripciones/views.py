# views.py para la app inscripciones
# Aquí se implementarán las vistas relacionadas con inscripciones.

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Avg, Sum
from django.shortcuts import get_object_or_404

from .models import Inscripcion, Calificacion
from .serializers import (
    InscripcionSerializer,
    InscripcionCreateSerializer,
    InscripcionUpdateSerializer,
    InscripcionDetalleSerializer,
    InscripcionListSerializer,
    InscripcionResumenSerializer,
    CalificacionSerializer,
    CalificacionCreateSerializer,
    CalificacionBulkCreateSerializer,
    EstudiantePromedioSerializer
)
from apps.users.permissions import (
    IsAdminUser,
    IsProfesorUser,
    IsEstudianteUser,
    IsAdminOrProfesor,
    IsAdminOrProfesorOrSelf
)


class InscripcionViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de inscripciones."""
    
    # Optimizamos el queryset base con select_related y prefetch_related
    queryset = Inscripcion.objects.select_related('estudiante', 'materia', 'periodo').prefetch_related('calificaciones').all()
    serializer_class = InscripcionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Retornar el serializer apropiado según la acción."""
        if self.action == 'create':
            return InscripcionCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return InscripcionUpdateSerializer
        elif self.action == 'retrieve':
            return InscripcionDetalleSerializer
        elif self.action == 'list':
            return InscripcionListSerializer
        return InscripcionSerializer
    
    def get_permissions(self):
        """Configurar permisos según la acción."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminOrProfesorOrSelf]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """
        Filtrar queryset según el rol del usuario y optimizar consultas.
        select_related: para traer estudiante, materia y periodo en la misma consulta.
        prefetch_related: para traer calificaciones en lote.
        annotate: para agregar promedios o conteos si es necesario.
        """
        user = self.request.user
        base_qs = Inscripcion.objects.select_related('estudiante', 'materia', 'periodo').prefetch_related('calificaciones')
        if user.is_admin:
            return base_qs.all()
        elif user.is_profesor:
            return base_qs.filter(materia__profesor=user)
        else:
            return base_qs.filter(estudiante=user)
    
    def list(self, request, *args, **kwargs):
        """
        Listar inscripciones optimizando con annotate para agregar promedios si es útil.
        """
        queryset = self.get_queryset()
        # Ejemplo: podríamos agregar un promedio de calificaciones por inscripción si se requiere
        # queryset = queryset.annotate(promedio=Avg('calificaciones__nota'))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def mis_inscripciones(self, request):
        """Obtener inscripciones del estudiante actual."""
        if not request.user.is_estudiante:
            return Response(
                {'error': 'Solo los estudiantes pueden acceder a este endpoint.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        inscripciones = self.get_queryset().filter(estudiante=request.user)
        serializer = InscripcionResumenSerializer(inscripciones, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def activas(self, request):
        """Obtener inscripciones activas."""
        inscripciones = self.get_queryset().filter(estado='activa')
        serializer = self.get_serializer(inscripciones, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def aprobadas(self, request):
        """Obtener inscripciones aprobadas."""
        inscripciones = self.get_queryset().filter(estado='aprobada')
        serializer = self.get_serializer(inscripciones, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def retirar(self, request, pk=None):
        """Retirar una inscripción."""
        inscripcion = self.get_object()
        
        # Verificar permisos
        if not (request.user.is_admin or 
                (request.user.is_profesor and inscripcion.materia.profesor == request.user) or
                (request.user.is_estudiante and inscripcion.estudiante == request.user)):
            return Response(
                {'error': 'No tienes permisos para retirar esta inscripción.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if inscripcion.estado != 'activa':
            return Response(
                {'error': 'Solo se pueden retirar inscripciones activas.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        inscripcion.estado = 'retirada'
        inscripcion.save()
        
        serializer = self.get_serializer(inscripcion)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def promedio_estudiante(self, request):
        """Obtener promedio de un estudiante."""
        estudiante_id = request.query_params.get('estudiante_id')
        
        if not estudiante_id:
            return Response(
                {'error': 'Se requiere estudiante_id.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar permisos
        if not (request.user.is_admin or 
                (request.user.is_profesor and request.user.materias_asignadas.filter(
                    inscripciones__estudiante_id=estudiante_id
                ).exists()) or
                (request.user.is_estudiante and request.user.id == int(estudiante_id))):
            return Response(
                {'error': 'No tienes permisos para ver esta información.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        inscripciones = Inscripcion.objects.filter(
            estudiante_id=estudiante_id,
            nota_final__isnull=False
        )
        
        if not inscripciones.exists():
            return Response({
                'estudiante_id': estudiante_id,
                'promedio_general': 0.0,
                'total_creditos': 0,
                'materias_aprobadas': 0,
                'materias_reprobadas': 0,
                'materias_activas': 0
            })
        
        # Calcular estadísticas
        promedio = inscripciones.aggregate(
            promedio=Avg('nota_final')
        )['promedio']
        
        total_creditos = inscripciones.filter(estado='aprobada').aggregate(
            total=Sum('materia__creditos')
        )['total'] or 0
        
        materias_aprobadas = inscripciones.filter(estado='aprobada').count()
        materias_reprobadas = inscripciones.filter(estado='reprobada').count()
        materias_activas = Inscripcion.objects.filter(
            estudiante_id=estudiante_id,
            estado='activa'
        ).count()
        
        from apps.users.models import User
        estudiante = User.objects.get(id=estudiante_id)
        
        return Response({
            'estudiante_id': estudiante_id,
            'estudiante_nombre': estudiante.get_full_name(),
            'promedio_general': round(promedio, 2),
            'total_creditos': total_creditos,
            'materias_aprobadas': materias_aprobadas,
            'materias_reprobadas': materias_reprobadas,
            'materias_activas': materias_activas
        })


class CalificacionViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de calificaciones."""
    
    queryset = Calificacion.objects.select_related('inscripcion__estudiante', 'inscripcion__materia').all()
    serializer_class = CalificacionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Retornar el serializer apropiado según la acción."""
        if self.action == 'create':
            return CalificacionCreateSerializer
        elif self.action == 'bulk_create':
            return CalificacionBulkCreateSerializer
        return CalificacionSerializer
    
    def get_permissions(self):
        """Configurar permisos según la acción."""
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'bulk_create']:
            permission_classes = [IsAdminOrProfesor]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filtrar queryset según el rol del usuario."""
        user = self.request.user
        
        if user.is_admin:
            return Calificacion.objects.select_related(
                'inscripcion__estudiante', 'inscripcion__materia'
            ).all()
        elif user.is_profesor:
            # Los profesores pueden ver calificaciones de sus materias
            return Calificacion.objects.select_related(
                'inscripcion__estudiante', 'inscripcion__materia'
            ).filter(
                inscripcion__materia__profesor=user
            )
        else:
            return Calificacion.objects.none()
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Crear múltiples calificaciones a la vez."""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            result = serializer.save()
            return Response(result, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def por_inscripcion(self, request):
        """Obtener calificaciones de una inscripción específica."""
        inscripcion_id = request.query_params.get('inscripcion_id')
        if not inscripcion_id:
            return Response(
                {'error': 'Se requiere inscripcion_id.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        calificaciones = self.get_queryset().filter(inscripcion_id=inscripcion_id)
        serializer = self.get_serializer(calificaciones, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def por_materia(self, request):
        """Obtener calificaciones de una materia específica."""
        materia_id = request.query_params.get('materia_id')
        if not materia_id:
            return Response(
                {'error': 'Se requiere materia_id.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        calificaciones = self.get_queryset().filter(inscripcion__materia_id=materia_id)
        serializer = self.get_serializer(calificaciones, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def estadisticas_materia(self, request):
        """Obtener estadísticas de calificaciones de una materia."""
        materia_id = request.query_params.get('materia_id')
        if not materia_id:
            return Response(
                {'error': 'Se requiere materia_id.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar permisos
        if not (request.user.is_admin or 
                request.user.materias_asignadas.filter(id=materia_id).exists()):
            return Response(
                {'error': 'No tienes permisos para ver esta información.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        inscripciones = Inscripcion.objects.filter(
            materia_id=materia_id,
            nota_final__isnull=False
        )
        
        if not inscripciones.exists():
            return Response({
                'materia_id': materia_id,
                'promedio_general': 0.0,
                'total_estudiantes': 0,
                'aprobados': 0,
                'reprobados': 0
            })
        
        # Calcular estadísticas
        promedio = inscripciones.aggregate(
            promedio=Avg('nota_final')
        )['promedio']
        
        total_estudiantes = inscripciones.count()
        aprobados = inscripciones.filter(estado='aprobada').count()
        reprobados = inscripciones.filter(estado='reprobada').count()
        
        return Response({
            'materia_id': materia_id,
            'promedio_general': round(promedio, 2),
            'total_estudiantes': total_estudiantes,
            'aprobados': aprobados,
            'reprobados': reprobados,
            'porcentaje_aprobacion': round((aprobados / total_estudiantes) * 100, 2)
        }) 