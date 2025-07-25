"""
Configuración específica para desarrollo.
Hereda de base.py y agrega configuraciones de debug.
"""

from .base import *

# Debug activado para desarrollo
DEBUG = True

# Configuración de base de datos para desarrollo (SQLite por defecto)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Configuración de CORS para desarrollo
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Configuración de email para desarrollo (consola)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Configuración de Celery para desarrollo
CELERY_TASK_ALWAYS_EAGER = True  # Ejecutar tareas de forma síncrona en desarrollo
CELERY_TASK_EAGER_PROPAGATES = True

# Configuración de logging más detallada para desarrollo
LOGGING['loggers']['django']['level'] = 'DEBUG'
LOGGING['loggers']['apps'] = {
    'handlers': ['console', 'file'],
    'level': 'DEBUG',
    'propagate': False,
}

# Configuración de Swagger para desarrollo
SWAGGER_SETTINGS.update({
    'OPERATIONS_SORTER': 'alpha',
    'TAGS_SORTER': 'alpha',
    'DOC_EXPANSION': 'list',
    'DEFAULT_MODEL_RENDERING': 'example',
})

# Configuración de DRF para desarrollo
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (
    'rest_framework.renderers.JSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer',  # Interfaz web para desarrollo
) 