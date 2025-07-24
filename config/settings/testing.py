"""
Configuración específica para testing.
Hereda de base.py y agrega configuraciones optimizadas para pruebas.
"""

from .base import *

# Configuración de base de datos para testing (SQLite en memoria)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Configuración de email para testing (backend de prueba)
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Configuración de Celery para testing
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Configuración de logging para testing
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}

# Configuración de DRF para testing
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (
    'rest_framework.renderers.JSONRenderer',
)

# Configuración de caché para testing
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Configuración de archivos estáticos para testing
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Configuración de archivos media para testing
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage' 