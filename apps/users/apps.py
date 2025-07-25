from django.apps import AppConfig


class UsersConfig(AppConfig):
    """
    Configuración de la app users.
    Registra automáticamente las señales cuando Django inicia.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'
    verbose_name = 'Usuarios'
    
    def ready(self):
        """
        Importar señales cuando la app esté lista.
        Esto asegura que las señales se registren automáticamente.
        """
        try:
            import apps.users.signals  # noqa F401
        except ImportError:
            pass 