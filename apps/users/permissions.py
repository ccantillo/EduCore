from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """
    Permiso personalizado para verificar si el usuario es administrador.
    """
    
    def has_permission(self, request, view):
        """Verificar si el usuario tiene permisos de administrador."""
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_admin
        )


class IsProfesorUser(permissions.BasePermission):
    """
    Permiso personalizado para verificar si el usuario es profesor.
    """
    
    def has_permission(self, request, view):
        """Verificar si el usuario tiene permisos de profesor."""
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_profesor
        )


class IsEstudianteUser(permissions.BasePermission):
    """
    Permiso personalizado para verificar si el usuario es estudiante.
    """
    
    def has_permission(self, request, view):
        """Verificar si el usuario tiene permisos de estudiante."""
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_estudiante
        )


class IsAdminOrProfesor(permissions.BasePermission):
    """
    Permiso personalizado para verificar si el usuario es administrador o profesor.
    """
    
    def has_permission(self, request, view):
        """Verificar si el usuario tiene permisos de administrador o profesor."""
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.is_admin or request.user.is_profesor)
        )


class IsAdminOrSelf(permissions.BasePermission):
    """
    Permiso personalizado para verificar si el usuario es administrador o el propietario del recurso.
    """
    
    def has_permission(self, request, view):
        """Verificar si el usuario está autenticado."""
        return bool(request.user and request.user.is_authenticated)
    
    def has_object_permission(self, request, view, obj):
        """Verificar si el usuario puede acceder al objeto específico."""
        # Los administradores pueden acceder a todo
        if request.user.is_admin:
            return True
        
        # Los usuarios pueden acceder a sus propios datos
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'id'):
            return obj.id == request.user.id
        
        return False


class IsAdminOrProfesorOrSelf(permissions.BasePermission):
    """
    Permiso personalizado para verificar si el usuario es admin, profesor o el propietario.
    """
    
    def has_permission(self, request, view):
        """Verificar si el usuario está autenticado y tiene permisos básicos."""
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Para el listado, permitir a admins y profesores
        if view.action == 'list':
            return request.user.is_admin or request.user.is_profesor
        
        # Para otras acciones, verificar autenticación
        return True
    
    def has_object_permission(self, request, view, obj):
        """Verificar si el usuario puede acceder al objeto específico."""
        # Los administradores y profesores pueden acceder a todo
        if request.user.is_admin or request.user.is_profesor:
            return True
        
        # Los usuarios pueden acceder a sus propios datos
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'id'):
            return obj.id == request.user.id
        
        return False 