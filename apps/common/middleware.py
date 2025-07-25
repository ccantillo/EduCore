import logging
from django.http import JsonResponse
from django.conf import settings

logger = logging.getLogger(__name__)


class RoleMiddleware:
    """
    Middleware personalizado para control de acceso basado en roles.
    Registra acciones importantes y valida permisos de acceso.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        """Procesar la solicitud y registrar información relevante."""
        
        # Registrar información de la solicitud
        self._log_request_info(request)
        
        # Procesar la solicitud
        response = self.get_response(request)
        
        # Registrar información de la respuesta
        self._log_response_info(request, response)
        
        return response
    
    def _log_request_info(self, request):
        """Registrar información de la solicitud entrante."""
        if hasattr(request, 'user') and request.user.is_authenticated:
            logger.info(
                f"Usuario {request.user.username} ({request.user.role}) "
                f"accediendo a {request.path} con método {request.method}"
            )
    
    def _log_response_info(self, request, response):
        """Registrar información de la respuesta."""
        if hasattr(request, 'user') and request.user.is_authenticated:
            status_code = response.status_code
            if status_code >= 400:
                logger.warning(
                    f"Usuario {request.user.username} recibió error {status_code} "
                    f"en {request.path}"
                )
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Procesar la vista antes de su ejecución.
        Aquí se pueden agregar validaciones adicionales de roles.
        """
        # Validaciones específicas por endpoint pueden ir aquí
        return None
    
    def process_exception(self, request, exception):
        """
        Procesar excepciones y registrar errores.
        """
        if hasattr(request, 'user') and request.user.is_authenticated:
            logger.error(
                f"Error para usuario {request.user.username} en {request.path}: {str(exception)}"
            )
        return None


class SecurityMiddleware:
    """
    Middleware para medidas de seguridad adicionales.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        """Agregar headers de seguridad a la respuesta."""
        response = self.get_response(request)
        
        # Headers de seguridad
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Solo agregar HSTS en producción
        if not settings.DEBUG:
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response


class RequestLoggingMiddleware:
    """
    Middleware para logging detallado de solicitudes.
    Registra información de usuario, duración, IP y User-Agent.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        """Registrar información detallada de la solicitud."""
        import time
        
        # Obtener tiempo de inicio
        start_time = time.time()
        
        # Obtener información del usuario
        if hasattr(request, 'user') and request.user and request.user.is_authenticated:
            user_info = f"{request.user.username} ({request.user.role})"
        else:
            user_info = "anonymous"
        
        # Obtener IP y User-Agent
        ip_address = request.META.get('REMOTE_ADDR', 'unknown')
        user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')
        
        # Procesar la solicitud
        response = self.get_response(request)
        
        # Calcular duración
        end_time = time.time()
        duration_ms = round((end_time - start_time) * 1000, 2)
        
        # Registrar información completa
        logger.info(
            f"User: {user_info} | "
            f"Method: {request.method} | "
            f"Path: {request.path} | "
            f"IP: {ip_address} | "
            f"User-Agent: {user_agent} | "
            f"Duration: {duration_ms}ms | "
            f"Status: {response.status_code}"
        )
        
        return response 