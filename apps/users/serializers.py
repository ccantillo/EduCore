# serializers.py para la app users
# Serializers para convertir datos de usuarios a JSON y viceversa

from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, Profile


class ProfileSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Profile."""
    
    class Meta:
        model = Profile
        fields = [
            'birth_date',
            'address',
            'student_id',
            'professional_id',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['student_id', 'professional_id', 'created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """Serializer para el modelo User (solo lectura)."""
    
    profile = ProfileSerializer(read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'role',
            'role_display',
            'phone',
            'is_active',
            'created_at',
            'updated_at',
            'profile'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear usuarios."""
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password',
            'password_confirm',
            'first_name',
            'last_name',
            'role',
            'phone'
        ]
    
    def validate(self, attrs):
        """Validar que las contraseñas coincidan."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError(
                {"password_confirm": "Las contraseñas no coinciden."}
            )
        return attrs
    
    def create(self, validated_data):
        """Crear usuario con contraseña encriptada."""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        
        # Crear perfil automáticamente
        Profile.objects.create(user=user)
        
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar usuarios."""
    
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'phone'
        ]


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar perfiles."""
    
    class Meta:
        model = Profile
        fields = [
            'birth_date',
            'address'
        ]


class LoginSerializer(serializers.Serializer):
    """Serializer para autenticación de usuarios."""
    
    username = serializers.CharField(max_length=255)
    password = serializers.CharField(max_length=128, write_only=True)
    
    def validate(self, attrs):
        """Validar credenciales de usuario."""
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError(
                    'Credenciales inválidas. Por favor, verifica tu usuario y contraseña.'
                )
            if not user.is_active:
                raise serializers.ValidationError(
                    'Tu cuenta está desactivada. Contacta al administrador.'
                )
            attrs['user'] = user
        else:
            raise serializers.ValidationError(
                'Debes proporcionar tanto el usuario como la contraseña.'
            )
        
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer para cambiar contraseña."""
    
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)
    
    def validate(self, attrs):
        """Validar que las nuevas contraseñas coincidan."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError(
                {"new_password_confirm": "Las contraseñas no coinciden."}
            )
        return attrs
    
    def validate_old_password(self, value):
        """Validar que la contraseña actual sea correcta."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('La contraseña actual es incorrecta.')
        return value 