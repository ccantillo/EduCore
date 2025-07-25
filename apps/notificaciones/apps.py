from django.apps import AppConfig


class NotificacionesConfig(AppConfig):
    """
    Configuración de la app notificaciones.
    Registra automáticamente las señales cuando Django inicia.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.notificaciones'
    verbose_name = 'Notificaciones'
    
    def ready(self):
        """
        Importar señales cuando la app esté lista.
        Esto asegura que las señales se registren automáticamente.
        """
        try:
            import apps.notificaciones.signals  # noqa F401
        except ImportError:
            pass 