# views.py para la app users
# Aquí se implementarán las vistas relacionadas con usuarios y autenticación.

from rest_framework import status, generics, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db import transaction

from .models import User, Profile
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    ProfileSerializer,
    ProfileUpdateSerializer,
    LoginSerializer,
    ChangePasswordSerializer
)
from .permissions import (
    IsAdminUser,
    IsAdminOrSelf,
    IsAdminOrProfesorOrSelf
)


class AuthViewSet(viewsets.GenericViewSet):
    """ViewSet para autenticación de usuarios."""
    
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'])
    def register(self, request):
        """Registrar un nuevo usuario."""
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generar tokens JWT
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'message': 'Usuario registrado exitosamente',
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        """Iniciar sesión de usuario."""
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Generar tokens JWT
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'message': 'Inicio de sesión exitoso',
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        """Cerrar sesión de usuario."""
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
                return Response({
                    'message': 'Sesión cerrada exitosamente'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Token de refresh requerido'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': 'Token inválido'
            }, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de usuarios."""
    
    queryset = User.objects.select_related('profile').all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Retornar el serializer apropiado según la acción."""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer
    
    def get_permissions(self):
        """Configurar permisos según la acción."""
        if self.action == 'create':
            permission_classes = [AllowAny]
        elif self.action in ['list', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAdminOrSelf]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filtrar queryset según el rol del usuario."""
        user = self.request.user
        
        if user.is_admin:
            return User.objects.select_related('profile').all()
        elif user.is_profesor:
            # Los profesores pueden ver estudiantes y otros profesores
            return User.objects.select_related('profile').filter(
                role__in=['estudiante', 'profesor']
            )
        else:
            # Los estudiantes solo pueden ver su propio perfil
            return User.objects.select_related('profile').filter(id=user.id)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Obtener información del usuario actual."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Cambiar contraseña del usuario actual."""
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            return Response({
                'message': 'Contraseña cambiada exitosamente'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def profile(self, request, pk=None):
        """Obtener perfil de un usuario específico."""
        user = self.get_object()
        serializer = ProfileSerializer(user.profile)
        return Response(serializer.data)
    
    @action(detail=True, methods=['put', 'patch'])
    def update_profile(self, request, pk=None):
        """Actualizar perfil de un usuario específico."""
        user = self.get_object()
        serializer = ProfileUpdateSerializer(
            user.profile,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de perfiles."""
    
    queryset = Profile.objects.select_related('user').all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        """Configurar permisos según la acción."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminOrProfesorOrSelf]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filtrar queryset según el rol del usuario."""
        user = self.request.user
        
        if user.is_admin:
            return Profile.objects.select_related('user').all()
        elif user.is_profesor:
            # Los profesores pueden ver perfiles de estudiantes y otros profesores
            return Profile.objects.select_related('user').filter(
                user__role__in=['estudiante', 'profesor']
            )
        else:
            # Los estudiantes solo pueden ver su propio perfil
            return Profile.objects.select_related('user').filter(user=user)
    
    def get_serializer_class(self):
        """Retornar el serializer apropiado según la acción."""
        if self.action in ['update', 'partial_update']:
            return ProfileUpdateSerializer
        return ProfileSerializer 