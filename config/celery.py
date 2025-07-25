import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')

app = Celery('prueba_tecnica')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Configuración adicional para evitar warnings
app.conf.update(
    broker_connection_retry_on_startup=True,  # Evitar warning de deprecación
)

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}') 