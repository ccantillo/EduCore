# serializers.py para la app notificaciones
# Aquí se definirán los serializers para los modelos de notificaciones.

from rest_framework import serializers
from .models import Notificacion


class NotificacionSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Notificacion."""
    
    class Meta:
        model = Notificacion
        fields = [
            'id',
            'usuario',
            'tipo',
            'titulo',
            'mensaje',
            'estado',
            'fecha_creacion',
            'fecha_lectura',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'fecha_creacion', 'created_at', 'updated_at']


class NotificacionCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear notificaciones."""
    
    class Meta:
        model = Notificacion
        fields = [
            'usuario',
            'tipo',
            'titulo',
            'mensaje'
        ]


class NotificacionUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar notificaciones."""
    
    class Meta:
        model = Notificacion
        fields = [
            'estado'
        ]


class NotificacionListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listar notificaciones."""
    
    class Meta:
        model = Notificacion
        fields = [
            'id',
            'tipo',
            'titulo',
            'estado',
            'fecha_creacion'
        ]
        read_only_fields = ['id', 'fecha_creacion']


class NotificacionDetalleSerializer(NotificacionSerializer):
    """Serializer detallado para notificaciones."""
    
    # Propiedades calculadas
    es_no_leida = serializers.BooleanField(read_only=True)
    es_leida = serializers.BooleanField(read_only=True)
    es_archivada = serializers.BooleanField(read_only=True)
    
    class Meta(NotificacionSerializer.Meta):
        fields = NotificacionSerializer.Meta.fields + ['es_no_leida', 'es_leida', 'es_archivada']


class NotificacionEstadisticasSerializer(serializers.Serializer):
    """Serializer para estadísticas de notificaciones."""
    
    total = serializers.IntegerField()
    no_leidas = serializers.IntegerField()
    leidas = serializers.IntegerField()
    archivadas = serializers.IntegerField()
    porcentaje_leidas = serializers.FloatField()
    
    class Meta:
        fields = [
            'total',
            'no_leidas',
            'leidas',
            'archivadas',
            'porcentaje_leidas'
        ]


class NotificacionBulkUpdateSerializer(serializers.Serializer):
    """Serializer para actualizar múltiples notificaciones."""
    
    notificacion_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="Lista de IDs de notificaciones a actualizar"
    )
    
    accion = serializers.ChoiceField(
        choices=[
            ('marcar_leidas', 'Marcar como leídas'),
            ('archivar', 'Archivar'),
            ('eliminar', 'Eliminar')
        ],
        help_text="Acción a realizar en las notificaciones"
    )
    
    def validate_notificacion_ids(self, value):
        """Validar que los IDs de notificaciones existan."""
        if not value:
            raise serializers.ValidationError("La lista de IDs no puede estar vacía.")
        
        # Verificar que todas las notificaciones existan y pertenezcan al usuario
        usuario = self.context['request'].user
        notificaciones_existentes = Notificacion.objects.filter(
            id__in=value,
            usuario=usuario
        ).values_list('id', flat=True)
        
        ids_existentes = set(notificaciones_existentes)
        ids_solicitados = set(value)
        
        if ids_solicitados != ids_existentes:
            ids_no_existentes = ids_solicitados - ids_existentes
            raise serializers.ValidationError(
                f"Las siguientes notificaciones no existen o no tienes acceso: {ids_no_existentes}"
            )
        
        return value
    
    def update(self, instance, validated_data):
        """Actualizar las notificaciones según la acción especificada."""
        notificacion_ids = validated_data['notificacion_ids']
        accion = validated_data['accion']
        
        notificaciones = Notificacion.objects.filter(id__in=notificacion_ids)
        
        if accion == 'marcar_leidas':
            from django.utils import timezone
            notificaciones.update(
                estado='leida',
                fecha_lectura=timezone.now()
            )
        elif accion == 'archivar':
            notificaciones.update(estado='archivada')
        elif accion == 'eliminar':
            notificaciones.delete()
        
        return {
            'accion': accion,
            'notificaciones_actualizadas': len(notificacion_ids)
        }


class NotificacionFiltroSerializer(serializers.Serializer):
    """Serializer para filtrar notificaciones."""
    
    tipo = serializers.ChoiceField(
        choices=Notificacion.TIPO_CHOICES,
        required=False,
        help_text="Filtrar por tipo de notificación"
    )
    
    estado = serializers.ChoiceField(
        choices=Notificacion.ESTADO_CHOICES,
        required=False,
        help_text="Filtrar por estado de notificación"
    )
    
    fecha_desde = serializers.DateField(
        required=False,
        help_text="Filtrar notificaciones desde esta fecha"
    )
    
    fecha_hasta = serializers.DateField(
        required=False,
        help_text="Filtrar notificaciones hasta esta fecha"
    )
    
    def validate(self, attrs):
        """Validar que las fechas sean coherentes."""
        fecha_desde = attrs.get('fecha_desde')
        fecha_hasta = attrs.get('fecha_hasta')
        
        if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
            raise serializers.ValidationError(
                "La fecha desde no puede ser posterior a la fecha hasta."
            )
        
        return attrs 