# serializers.py para la app inscripciones
# Serializers para inscripciones - incluir materia, estado, calificaciones

from rest_framework import serializers
from .models import Inscripcion, Calificacion
from apps.users.serializers import UserSerializer
from apps.materias.serializers import MateriaSerializer, PeriodoSerializer


class CalificacionSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Calificacion."""
    
    class Meta:
        model = Calificacion
        fields = [
            'id',
            'inscripcion',
            'tipo',
            'nota',
            'peso',
            'comentarios',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CalificacionCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear calificaciones."""
    
    class Meta:
        model = Calificacion
        fields = [
            'inscripcion',
            'tipo',
            'nota',
            'peso',
            'comentarios'
        ]
    
    def validate(self, attrs):
        """Validamos que se pueda crear esta calificación."""
        inscripcion = attrs.get('inscripcion')
        tipo = attrs.get('tipo')
        peso = attrs.get('peso')
        
        # Verificar que no exista ya una calificación del mismo tipo
        if Calificacion.objects.filter(
            inscripcion=inscripcion,
            tipo=tipo
        ).exists():
            raise serializers.ValidationError({
                'tipo': f'Ya existe una calificación de tipo {tipo} para esta inscripción.'
            })
        
        # Verificar que el peso total no exceda 100%
        peso_total_actual = Calificacion.objects.filter(
            inscripcion=inscripcion
        ).aggregate(
            total=serializers.Sum('peso')
        )['total'] or 0
        
        if peso_total_actual + peso > 100:
            raise serializers.ValidationError({
                'peso': f'El peso total de las evaluaciones no puede exceder 100%. Actual: {peso_total_actual + peso}%'
            })
        
        return attrs


class InscripcionSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Inscripcion."""
    
    estudiante = UserSerializer(read_only=True)
    materia = MateriaSerializer(read_only=True)
    periodo = PeriodoSerializer(read_only=True)
    calificaciones = CalificacionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Inscripcion
        fields = [
            'id',
            'estudiante',
            'materia',
            'periodo',
            'estado',
            'nota_final',
            'fecha_inscripcion',
            'fecha_retiro',
            'calificaciones',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'fecha_inscripcion', 'created_at', 'updated_at']


class InscripcionCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear inscripciones."""
    
    class Meta:
        model = Inscripcion
        fields = [
            'estudiante',
            'materia',
            'periodo'
        ]
    
    def validate(self, attrs):
        """Validamos que se pueda crear la inscripción."""
        estudiante = attrs.get('estudiante')
        materia = attrs.get('materia')
        periodo = attrs.get('periodo')
        
        # Verificar que el estudiante tenga rol de estudiante
        if estudiante.role != 'estudiante':
            raise serializers.ValidationError({
                'estudiante': 'El usuario debe tener rol de estudiante.'
            })
        
        # Verificar que no haya inscripción duplicada
        if Inscripcion.objects.filter(
            estudiante=estudiante,
            materia=materia,
            periodo=periodo
        ).exists():
            raise serializers.ValidationError(
                'El estudiante ya está inscrito en esta materia para este período.'
            )
        
        # Verificar que el período esté activo
        if not periodo.es_activo:
            raise serializers.ValidationError({
                'periodo': 'El período debe estar activo para realizar inscripciones.'
            })
        
        return attrs


class InscripcionUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar inscripciones."""
    
    class Meta:
        model = Inscripcion
        fields = [
            'estado',
            'fecha_retiro'
        ]
    
    def validate(self, attrs):
        """Validamos los cambios de estado de la inscripción."""
        estado = attrs.get('estado')
        fecha_retiro = attrs.get('fecha_retiro')
        
        # Si se está retirando, agregar fecha de retiro
        if estado == 'retirada' and not fecha_retiro:
            from django.utils import timezone
            attrs['fecha_retiro'] = timezone.now()
        
        return attrs


class InscripcionDetalleSerializer(InscripcionSerializer):
    """Serializer detallado para inscripciones con información completa."""
    
    # Propiedades calculadas
    aprobada = serializers.BooleanField(read_only=True)
    reprobada = serializers.BooleanField(read_only=True)
    activa = serializers.BooleanField(read_only=True)
    
    class Meta(InscripcionSerializer.Meta):
        fields = InscripcionSerializer.Meta.fields + ['aprobada', 'reprobada', 'activa']


class InscripcionListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listar inscripciones."""
    
    estudiante_nombre = serializers.CharField(source='estudiante.get_full_name', read_only=True)
    materia_codigo = serializers.CharField(source='materia.codigo', read_only=True)
    materia_nombre = serializers.CharField(source='materia.nombre', read_only=True)
    periodo_nombre = serializers.CharField(source='periodo.nombre', read_only=True)
    
    class Meta:
        model = Inscripcion
        fields = [
            'id',
            'estudiante_nombre',
            'materia_codigo',
            'materia_nombre',
            'periodo_nombre',
            'estado',
            'nota_final',
            'fecha_inscripcion'
        ]
        read_only_fields = ['id', 'fecha_inscripcion']


class CalificacionBulkCreateSerializer(serializers.Serializer):
    """Serializer para crear múltiples calificaciones a la vez."""
    
    calificaciones = CalificacionCreateSerializer(many=True)
    
    def create(self, validated_data):
        """Crear múltiples calificaciones."""
        calificaciones_data = validated_data.pop('calificaciones')
        calificaciones = []
        
        for cal_data in calificaciones_data:
            calificacion = Calificacion.objects.create(**cal_data)
            calificaciones.append(calificacion)
        
        return {'calificaciones': calificaciones}


class InscripcionResumenSerializer(serializers.ModelSerializer):
    """Serializer para resumen de inscripciones de un estudiante."""
    
    materia_codigo = serializers.CharField(source='materia.codigo', read_only=True)
    materia_nombre = serializers.CharField(source='materia.nombre', read_only=True)
    materia_creditos = serializers.IntegerField(source='materia.creditos', read_only=True)
    profesor_nombre = serializers.CharField(source='materia.profesor.get_full_name', read_only=True)
    periodo_nombre = serializers.CharField(source='periodo.nombre', read_only=True)
    
    class Meta:
        model = Inscripcion
        fields = [
            'id',
            'materia_codigo',
            'materia_nombre',
            'materia_creditos',
            'profesor_nombre',
            'periodo_nombre',
            'estado',
            'nota_final',
            'fecha_inscripcion'
        ]
        read_only_fields = ['id', 'fecha_inscripcion']


class EstudiantePromedioSerializer(serializers.Serializer):
    """Serializer para calcular y mostrar el promedio de un estudiante."""
    
    estudiante_id = serializers.IntegerField()
    estudiante_nombre = serializers.CharField()
    promedio_general = serializers.DecimalField(max_digits=4, decimal_places=2)
    total_creditos = serializers.IntegerField()
    materias_aprobadas = serializers.IntegerField()
    materias_reprobadas = serializers.IntegerField()
    materias_activas = serializers.IntegerField()
    
    class Meta:
        fields = [
            'estudiante_id',
            'estudiante_nombre',
            'promedio_general',
            'total_creditos',
            'materias_aprobadas',
            'materias_reprobadas',
            'materias_activas'
        ] 