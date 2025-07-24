# serializers.py para la app reportes
# Aquí se definirán los serializers para los modelos de reportes.

from rest_framework import serializers
from .models import ReporteGenerado


class ReporteGeneradoSerializer(serializers.ModelSerializer):
    """Serializer para el modelo ReporteGenerado."""
    
    class Meta:
        model = ReporteGenerado
        fields = [
            'id',
            'solicitante',
            'tipo',
            'nombre_archivo',
            'ruta_archivo',
            'parametros',
            'estado',
            'registros_procesados',
            'mensaje_error',
            'created_at',
            'updated_at',
            'completado_at'
        ]
        read_only_fields = [
            'id', 'nombre_archivo', 'ruta_archivo', 'parametros', 
            'estado', 'registros_procesados', 'mensaje_error',
            'created_at', 'updated_at', 'completado_at'
        ]


class ReporteGeneradoListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listar reportes."""
    
    solicitante_nombre = serializers.CharField(source='solicitante.get_full_name', read_only=True)
    tiempo_generacion = serializers.SerializerMethodField()
    
    class Meta:
        model = ReporteGenerado
        fields = [
            'id',
            'tipo',
            'nombre_archivo',
            'estado',
            'registros_procesados',
            'solicitante_nombre',
            'created_at',
            'completado_at',
            'tiempo_generacion'
        ]
        read_only_fields = ['id', 'nombre_archivo', 'created_at', 'completado_at']
    
    def get_tiempo_generacion(self, obj):
        """Obtener el tiempo de generación del reporte."""
        if obj.tiempo_generacion:
            total_seconds = obj.tiempo_generacion.total_seconds()
            if total_seconds < 60:
                return f"{total_seconds:.1f} segundos"
            elif total_seconds < 3600:
                minutes = total_seconds / 60
                return f"{minutes:.1f} minutos"
            else:
                hours = total_seconds / 3600
                return f"{hours:.1f} horas"
        return None


class ReporteGeneradoDetalleSerializer(ReporteGeneradoSerializer):
    """Serializer detallado para reportes."""
    
    solicitante_nombre = serializers.CharField(source='solicitante.get_full_name', read_only=True)
    tiempo_generacion = serializers.SerializerMethodField()
    es_completado = serializers.BooleanField(read_only=True)
    es_error = serializers.BooleanField(read_only=True)
    es_pendiente = serializers.BooleanField(read_only=True)
    
    class Meta(ReporteGeneradoSerializer.Meta):
        fields = ReporteGeneradoSerializer.Meta.fields + [
            'solicitante_nombre',
            'tiempo_generacion',
            'es_completado',
            'es_error',
            'es_pendiente'
        ]
    
    def get_tiempo_generacion(self, obj):
        """Obtener el tiempo de generación del reporte."""
        if obj.tiempo_generacion:
            total_seconds = obj.tiempo_generacion.total_seconds()
            if total_seconds < 60:
                return f"{total_seconds:.1f} segundos"
            elif total_seconds < 3600:
                minutes = total_seconds / 60
                return f"{minutes:.1f} minutos"
            else:
                hours = total_seconds / 3600
                return f"{hours:.1f} horas"
        return None


class ReporteEstudianteSerializer(serializers.Serializer):
    """Serializer para solicitar reporte de estudiante."""
    
    estudiante_id = serializers.IntegerField(
        help_text="ID del estudiante para generar el reporte"
    )
    
    periodo_id = serializers.IntegerField(
        required=False,
        help_text="ID del período (opcional, si no se especifica se incluyen todos)"
    )
    
    def validate_estudiante_id(self, value):
        """Validar que el estudiante existe y es un estudiante."""
        from apps.users.models import User
        
        try:
            estudiante = User.objects.get(id=value, role='estudiante')
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("Estudiante no encontrado o no es un estudiante válido.")
    
    def validate_periodo_id(self, value):
        """Validar que el período existe."""
        if value:
            from apps.materias.models import Periodo
            
            try:
                Periodo.objects.get(id=value)
                return value
            except Periodo.DoesNotExist:
                raise serializers.ValidationError("Período no encontrado.")
        return value


class ReporteProfesorSerializer(serializers.Serializer):
    """Serializer para solicitar reporte de profesor."""
    
    profesor_id = serializers.IntegerField(
        help_text="ID del profesor para generar el reporte"
    )
    
    periodo_id = serializers.IntegerField(
        required=False,
        help_text="ID del período (opcional, si no se especifica se incluyen todos)"
    )
    
    def validate_profesor_id(self, value):
        """Validar que el profesor existe y es un profesor."""
        from apps.users.models import User
        
        try:
            profesor = User.objects.get(id=value, role='profesor')
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("Profesor no encontrado o no es un profesor válido.")
    
    def validate_periodo_id(self, value):
        """Validar que el período existe."""
        if value:
            from apps.materias.models import Periodo
            
            try:
                Periodo.objects.get(id=value)
                return value
            except Periodo.DoesNotExist:
                raise serializers.ValidationError("Período no encontrado.")
        return value


class ReporteGeneralSerializer(serializers.Serializer):
    """Serializer para solicitar reporte general."""
    
    periodo_id = serializers.IntegerField(
        required=False,
        help_text="ID del período (opcional, si no se especifica se incluyen todos)"
    )
    
    def validate_periodo_id(self, value):
        """Validar que el período existe."""
        if value:
            from apps.materias.models import Periodo
            
            try:
                Periodo.objects.get(id=value)
                return value
            except Periodo.DoesNotExist:
                raise serializers.ValidationError("Período no encontrado.")
        return value


class ReporteFiltroSerializer(serializers.Serializer):
    """Serializer para filtrar reportes."""
    
    tipo = serializers.ChoiceField(
        choices=ReporteGenerado.TIPO_CHOICES,
        required=False,
        help_text="Filtrar por tipo de reporte"
    )
    
    estado = serializers.ChoiceField(
        choices=ReporteGenerado.ESTADO_CHOICES,
        required=False,
        help_text="Filtrar por estado del reporte"
    )
    
    solicitante_id = serializers.IntegerField(
        required=False,
        help_text="Filtrar por ID del solicitante"
    )
    
    fecha_desde = serializers.DateField(
        required=False,
        help_text="Filtrar reportes desde esta fecha"
    )
    
    fecha_hasta = serializers.DateField(
        required=False,
        help_text="Filtrar reportes hasta esta fecha"
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


class ReporteEstadisticasSerializer(serializers.Serializer):
    """Serializer para estadísticas de reportes."""
    
    total_reportes = serializers.IntegerField()
    reportes_completados = serializers.IntegerField()
    reportes_pendientes = serializers.IntegerField()
    reportes_error = serializers.IntegerField()
    promedio_tiempo_generacion = serializers.FloatField()
    reportes_por_tipo = serializers.DictField()
    reportes_por_estado = serializers.DictField()
    
    class Meta:
        fields = [
            'total_reportes',
            'reportes_completados',
            'reportes_pendientes',
            'reportes_error',
            'promedio_tiempo_generacion',
            'reportes_por_tipo',
            'reportes_por_estado'
        ] 