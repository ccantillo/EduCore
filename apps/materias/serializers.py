# serializers.py para la app materias
# Serializers para materias - incluir prerrequisitos, créditos, horarios

from rest_framework import serializers
from .models import Materia, Prerrequisito, Periodo
from apps.users.serializers import UserSerializer


class PrerrequisitoSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Prerrequisito."""
    
    prerrequisito_codigo = serializers.CharField(source='prerrequisito.codigo', read_only=True)
    prerrequisito_nombre = serializers.CharField(source='prerrequisito.nombre', read_only=True)
    
    class Meta:
        model = Prerrequisito
        fields = [
            'id',
            'prerrequisito',
            'prerrequisito_codigo',
            'prerrequisito_nombre',
            'tipo',
            'created_at'
        ]
        read_only_fields = ['created_at']


class MateriaSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Materia."""
    
    profesor = UserSerializer(read_only=True)
    prerrequisitos = PrerrequisitoSerializer(many=True, read_only=True)
    estudiantes_inscritos_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Materia
        fields = [
            'id',
            'codigo',
            'nombre',
            'descripcion',
            'creditos',
            'estado',
            'profesor',
            'prerrequisitos',
            'estudiantes_inscritos_count',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class MateriaCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear materias."""
    
    class Meta:
        model = Materia
        fields = [
            'codigo',
            'nombre',
            'descripcion',
            'creditos',
            'estado',
            'profesor'
        ]
    
    def validate_codigo(self, value):
        """Validar que el código sea único."""
        if Materia.objects.filter(codigo=value).exists():
            raise serializers.ValidationError(
                'Ya existe una materia con este código.'
            )
        return value


class MateriaUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar materias."""
    
    class Meta:
        model = Materia
        fields = [
            'nombre',
            'descripcion',
            'creditos',
            'estado',
            'profesor'
        ]


class PrerrequisitoCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear prerrequisitos."""
    
    class Meta:
        model = Prerrequisito
        fields = [
            'materia',
            'prerrequisito',
            'tipo'
        ]
    
    def validate(self, attrs):
        """Validamos que no haya prerrequisitos circulares."""
        materia = attrs.get('materia')
        prerrequisito = attrs.get('prerrequisito')
        
        # Evitar prerrequisito circular
        if materia == prerrequisito:
            raise serializers.ValidationError(
                'Una materia no puede ser prerrequisito de sí misma.'
            )
        
        # Verificar que no exista ya este prerrequisito
        if Prerrequisito.objects.filter(
            materia=materia,
            prerrequisito=prerrequisito
        ).exists():
            raise serializers.ValidationError(
                'Este prerrequisito ya existe para esta materia.'
            )
        
        return attrs


class PeriodoSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Periodo."""
    
    class Meta:
        model = Periodo
        fields = [
            'id',
            'nombre',
            'fecha_inicio',
            'fecha_fin',
            'estado',
            'es_activo',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'es_activo', 'created_at', 'updated_at']


class PeriodoCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear períodos."""
    
    class Meta:
        model = Periodo
        fields = [
            'nombre',
            'fecha_inicio',
            'fecha_fin',
            'estado'
        ]
    
    def validate(self, attrs):
        """Validamos las fechas del período académico."""
        fecha_inicio = attrs.get('fecha_inicio')
        fecha_fin = attrs.get('fecha_fin')
        
        if fecha_inicio >= fecha_fin:
            raise serializers.ValidationError(
                'La fecha de inicio debe ser anterior a la fecha de fin.'
            )
        
        return attrs


class MateriaDetalleSerializer(MateriaSerializer):
    """Serializer detallado para materias con información completa."""
    
    # Incluir información de inscripciones activas
    inscripciones_activas = serializers.SerializerMethodField()
    
    class Meta(MateriaSerializer.Meta):
        fields = MateriaSerializer.Meta.fields + ['inscripciones_activas']
    
    def get_inscripciones_activas(self, obj):
        """Obtener información de inscripciones activas."""
        inscripciones = obj.inscripciones.filter(estado='activa')
        return {
            'total': inscripciones.count(),
            'estudiantes': [
                {
                    'id': insc.estudiante.id,
                    'username': insc.estudiante.username,
                    'nombre_completo': f"{insc.estudiante.first_name} {insc.estudiante.last_name}"
                }
                for insc in inscripciones.select_related('estudiante')
            ]
        }


class MateriaListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listar materias."""
    
    profesor_nombre = serializers.CharField(source='profesor.get_full_name', read_only=True)
    
    class Meta:
        model = Materia
        fields = [
            'id',
            'codigo',
            'nombre',
            'creditos',
            'estado',
            'profesor_nombre',
            'estudiantes_inscritos_count'
        ]
        read_only_fields = ['id', 'estudiantes_inscritos_count'] 