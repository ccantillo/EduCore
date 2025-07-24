# views.py para la app materias
# Aquí se implementarán las vistas relacionadas con materias.

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Avg
from django.shortcuts import get_object_or_404

from .models import Materia, Prerrequisito, Periodo
from .serializers import (
    MateriaSerializer,
    MateriaCreateSerializer,
    MateriaUpdateSerializer,
    MateriaDetalleSerializer,
    MateriaListSerializer,
    PrerrequisitoSerializer,
    PrerrequisitoCreateSerializer,
    PeriodoSerializer,
    PeriodoCreateSerializer
)
from apps.users.permissions import (
    IsAdminUser,
    IsProfesorUser,
    IsAdminOrProfesor
)


class MateriaViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de materias."""
    
    queryset = Materia.objects.select_related('profesor').prefetch_related('prerrequisitos__prerrequisito').all()
    serializer_class = MateriaSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Retornar el serializer apropiado según la acción."""
        if self.action == 'create':
            return MateriaCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return MateriaUpdateSerializer
        elif self.action == 'retrieve':
            return MateriaDetalleSerializer
        elif self.action == 'list':
            return MateriaListSerializer
        return MateriaSerializer
    
    def get_permissions(self):
        """Configurar permisos según la acción."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminOrProfesor]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filtrar queryset según el rol del usuario."""
        user = self.request.user
        
        if user.is_admin:
            return Materia.objects.select_related('profesor').prefetch_related('prerrequisitos__prerrequisito').all()
        elif user.is_profesor:
            # Los profesores pueden ver sus materias asignadas y todas las materias activas
            return Materia.objects.select_related('profesor').prefetch_related('prerrequisitos__prerrequisito').filter(
                Q(profesor=user) | Q(estado='activa')
            )
        else:
            # Los estudiantes pueden ver solo materias activas
            return Materia.objects.select_related('profesor').prefetch_related('prerrequisitos__prerrequisito').filter(
                estado='activa'
            )
    
    @action(detail=False, methods=['get'])
    def mis_materias(self, request):
        """Obtener materias asignadas al profesor."""
        if not request.user.is_profesor:
            return Response(
                {'error': 'Solo los profesores pueden acceder a este endpoint.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        materias = self.get_queryset().filter(profesor=request.user)
        serializer = self.get_serializer(materias, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def estudiantes(self, request, pk=None):
        """Obtener estudiantes inscritos en una materia."""
        materia = self.get_object()
        
        # Verificar permisos
        if not (request.user.is_admin or 
                (request.user.is_profesor and materia.profesor == request.user)):
            return Response(
                {'error': 'No tienes permisos para ver esta información.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        inscripciones = materia.inscripciones.filter(estado='activa').select_related('estudiante')
        estudiantes = [
            {
                'id': insc.estudiante.id,
                'username': insc.estudiante.username,
                'nombre_completo': insc.estudiante.get_full_name(),
                'email': insc.estudiante.email,
                'fecha_inscripcion': insc.fecha_inscripcion
            }
            for insc in inscripciones
        ]
        
        return Response({
            'materia': materia.codigo,
            'total_estudiantes': len(estudiantes),
            'estudiantes': estudiantes
        })
    
    @action(detail=False, methods=['get'])
    def disponibles(self, request):
        """Obtener materias disponibles para inscripción."""
        # Solo materias activas sin profesor asignado o con cupo disponible
        materias = self.get_queryset().filter(
            estado='activa'
        ).annotate(
            estudiantes_count=Count('inscripciones', filter=Q(inscripciones__estado='activa'))
        )
        
        serializer = MateriaListSerializer(materias, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def asignar_profesor(self, request, pk=None):
        """Asignar profesor a una materia."""
        if not request.user.is_admin:
            return Response(
                {'error': 'Solo los administradores pueden asignar profesores.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        materia = self.get_object()
        profesor_id = request.data.get('profesor_id')
        
        if not profesor_id:
            return Response(
                {'error': 'Se requiere profesor_id.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from apps.users.models import User
        try:
            profesor = User.objects.get(id=profesor_id, role='profesor')
            materia.profesor = profesor
            materia.save()
            
            serializer = self.get_serializer(materia)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(
                {'error': 'El usuario especificado no es un profesor válido.'},
                status=status.HTTP_400_BAD_REQUEST
            )


class PrerrequisitoViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de prerrequisitos."""
    
    queryset = Prerrequisito.objects.select_related('materia', 'prerrequisito').all()
    serializer_class = PrerrequisitoSerializer
    permission_classes = [IsAuthenticated, IsAdminOrProfesor]
    
    def get_serializer_class(self):
        """Retornar el serializer apropiado según la acción."""
        if self.action == 'create':
            return PrerrequisitoCreateSerializer
        return PrerrequisitoSerializer
    
    def get_queryset(self):
        """Filtrar queryset según el rol del usuario."""
        user = self.request.user
        
        if user.is_admin:
            return Prerrequisito.objects.select_related('materia', 'prerrequisito').all()
        elif user.is_profesor:
            # Los profesores pueden ver prerrequisitos de sus materias
            return Prerrequisito.objects.select_related('materia', 'prerrequisito').filter(
                materia__profesor=user
            )
        else:
            return Prerrequisito.objects.none()
    
    @action(detail=False, methods=['get'])
    def por_materia(self, request):
        """Obtener prerrequisitos de una materia específica."""
        materia_id = request.query_params.get('materia_id')
        if not materia_id:
            return Response(
                {'error': 'Se requiere materia_id.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        prerrequisitos = self.get_queryset().filter(materia_id=materia_id)
        serializer = self.get_serializer(prerrequisitos, many=True)
        return Response(serializer.data)


class PeriodoViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de períodos académicos."""
    
    queryset = Periodo.objects.all()
    serializer_class = PeriodoSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_serializer_class(self):
        """Retornar el serializer apropiado según la acción."""
        if self.action == 'create':
            return PeriodoCreateSerializer
        return PeriodoSerializer
    
    @action(detail=False, methods=['get'])
    def activos(self, request):
        """Obtener períodos activos."""
        periodos = self.get_queryset().filter(estado__in=['inscripciones', 'en_curso'])
        serializer = self.get_serializer(periodos, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cambiar_estado(self, request, pk=None):
        """Cambiar el estado de un período."""
        periodo = self.get_object()
        nuevo_estado = request.data.get('estado')
        
        if not nuevo_estado:
            return Response(
                {'error': 'Se requiere el nuevo estado.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if nuevo_estado not in dict(Periodo.ESTADO_CHOICES):
            return Response(
                {'error': 'Estado inválido.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        periodo.estado = nuevo_estado
        periodo.save()
        
        serializer = self.get_serializer(periodo)
        return Response(serializer.data) 