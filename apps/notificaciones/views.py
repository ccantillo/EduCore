# views.py para la app notificaciones
# Vistas para ver notificaciones, marcar como leídas, configurar preferencias

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone
from datetime import datetime

from .models import Notificacion
from .serializers import (
    NotificacionSerializer,
    NotificacionCreateSerializer,
    NotificacionUpdateSerializer,
    NotificacionListSerializer,
    NotificacionDetalleSerializer,
    NotificacionEstadisticasSerializer,
    NotificacionBulkUpdateSerializer,
    NotificacionFiltroSerializer
)
from .signals import (
    obtener_estadisticas_notificaciones,
    limpiar_notificaciones_antiguas,
    crear_notificacion_sistema,
    crear_recordatorio
)
from apps.users.permissions import IsAdminUser


class NotificacionViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de notificaciones."""
    
    queryset = Notificacion.objects.all()
    serializer_class = NotificacionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Retornar el serializer apropiado según la acción."""
        if self.action == 'create':
            return NotificacionCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return NotificacionUpdateSerializer
        elif self.action == 'retrieve':
            return NotificacionDetalleSerializer
        elif self.action == 'list':
            return NotificacionListSerializer
        elif self.action == 'bulk_update':
            return NotificacionBulkUpdateSerializer
        elif self.action == 'estadisticas':
            return NotificacionEstadisticasSerializer
        return NotificacionSerializer
    
    def get_permissions(self):
        """Configurar permisos según la acción."""
        if self.action in ['create', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filtrar queryset para mostrar solo notificaciones del usuario."""
        user = self.request.user
        
        if user.is_admin:
            return Notificacion.objects.all()
        else:
            return Notificacion.objects.filter(usuario=user)
    
    def list(self, request, *args, **kwargs):
        """Listar notificaciones con filtros opcionales."""
        queryset = self.get_queryset()
        
        # Aplicar filtros
        serializer = NotificacionFiltroSerializer(data=request.query_params)
        if serializer.is_valid():
            filtros = serializer.validated_data
            
            if filtros.get('tipo'):
                queryset = queryset.filter(tipo=filtros['tipo'])
            
            if filtros.get('estado'):
                queryset = queryset.filter(estado=filtros['estado'])
            
            if filtros.get('fecha_desde'):
                queryset = queryset.filter(fecha_creacion__date__gte=filtros['fecha_desde'])
            
            if filtros.get('fecha_hasta'):
                queryset = queryset.filter(fecha_creacion__date__lte=filtros['fecha_hasta'])
        
        # Ordenar por fecha de creación (más recientes primero)
        queryset = queryset.order_by('-fecha_creacion')
        
        # Paginar resultados
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def mis_notificaciones(self, request):
        """Obtener notificaciones del usuario actual."""
        notificaciones = self.get_queryset().filter(usuario=request.user)
        serializer = self.get_serializer(notificaciones, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def no_leidas(self, request):
        """Obtener notificaciones no leídas del usuario."""
        notificaciones = self.get_queryset().filter(
            usuario=request.user,
            estado='no_leida'
        )
        serializer = self.get_serializer(notificaciones, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def leidas(self, request):
        """Obtener notificaciones leídas del usuario."""
        notificaciones = self.get_queryset().filter(
            usuario=request.user,
            estado='leida'
        )
        serializer = self.get_serializer(notificaciones, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def archivadas(self, request):
        """Obtener notificaciones archivadas del usuario."""
        notificaciones = self.get_queryset().filter(
            usuario=request.user,
            estado='archivada'
        )
        serializer = self.get_serializer(notificaciones, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def marcar_leida(self, request, pk=None):
        """Marcar una notificación como leída."""
        notificacion = self.get_object()
        
        # Verificar que la notificación pertenezca al usuario
        if not request.user.is_admin and notificacion.usuario != request.user:
            return Response(
                {'error': 'No tienes permisos para acceder a esta notificación.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        notificacion.marcar_como_leida()
        serializer = self.get_serializer(notificacion)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def archivar(self, request, pk=None):
        """Archivar una notificación."""
        notificacion = self.get_object()
        
        # Verificar que la notificación pertenezca al usuario
        if not request.user.is_admin and notificacion.usuario != request.user:
            return Response(
                {'error': 'No tienes permisos para acceder a esta notificación.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        notificacion.archivar()
        serializer = self.get_serializer(notificacion)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """Actualizar múltiples notificaciones a la vez."""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            result = serializer.save()
            return Response(result, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Obtener estadísticas de notificaciones."""
        if request.user.is_admin:
            # Para administradores, mostrar estadísticas globales
            stats = obtener_estadisticas_notificaciones()
        else:
            # Para usuarios normales, mostrar solo sus estadísticas
            stats = obtener_estadisticas_notificaciones(request.user)
        
        serializer = NotificacionEstadisticasSerializer(stats)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def limpiar_antiguas(self, request):
        """Limpiar notificaciones antiguas (solo administradores)."""
        if not request.user.is_admin:
            return Response(
                {'error': 'Solo los administradores pueden limpiar notificaciones antiguas.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        dias = request.data.get('dias', 30)
        count = limpiar_notificaciones_antiguas(dias)
        
        return Response({
            'mensaje': f'Se archivaron {count} notificaciones antiguas (más de {dias} días)',
            'notificaciones_archivadas': count
        })
    
    @action(detail=False, methods=['post'])
    def crear_sistema(self, request):
        """Crear notificación del sistema (solo administradores)."""
        if not request.user.is_admin:
            return Response(
                {'error': 'Solo los administradores pueden crear notificaciones del sistema.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        usuario_id = request.data.get('usuario_id')
        titulo = request.data.get('titulo')
        mensaje = request.data.get('mensaje')
        
        if not all([usuario_id, titulo, mensaje]):
            return Response(
                {'error': 'Se requieren usuario_id, titulo y mensaje.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from apps.users.models import User
            usuario = User.objects.get(id=usuario_id)
            crear_notificacion_sistema(usuario, titulo, mensaje)
            
            return Response({
                'mensaje': 'Notificación del sistema creada exitosamente'
            })
        except User.DoesNotExist:
            return Response(
                {'error': 'Usuario no encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'])
    def crear_recordatorio(self, request):
        """Crear recordatorio (solo administradores)."""
        if not request.user.is_admin:
            return Response(
                {'error': 'Solo los administradores pueden crear recordatorios.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        usuario_id = request.data.get('usuario_id')
        titulo = request.data.get('titulo')
        mensaje = request.data.get('mensaje')
        
        if not all([usuario_id, titulo, mensaje]):
            return Response(
                {'error': 'Se requieren usuario_id, titulo y mensaje.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from apps.users.models import User
            usuario = User.objects.get(id=usuario_id)
            crear_recordatorio(usuario, titulo, mensaje)
            
            return Response({
                'mensaje': 'Recordatorio creado exitosamente'
            })
        except User.DoesNotExist:
            return Response(
                {'error': 'Usuario no encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def buscar(self, request):
        """Buscar notificaciones por texto."""
        query = request.query_params.get('q', '')
        
        if not query:
            return Response(
                {'error': 'Se requiere el parámetro de búsqueda "q".'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        notificaciones = self.get_queryset().filter(
            Q(titulo__icontains=query) |
            Q(mensaje__icontains=query) |
            Q(tipo__icontains=query)
        )
        
        serializer = self.get_serializer(notificaciones, many=True)
        return Response(serializer.data) 