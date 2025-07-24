# tasks.py para la app notificaciones
# Aquí se implementarán tareas asíncronas relacionadas con notificaciones.

# Tareas serán agregadas posteriormente. 
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Notificacion

@shared_task
def delete_old_notifications(days=30):
    """
    Elimina notificaciones con más de 'days' días de antigüedad.
    Por defecto, borra notificaciones con fecha_creacion > 30 días.
    """
    limite = timezone.now() - timedelta(days=days)
    # Borramos solo las notificaciones no leídas o archivadas, para no afectar historial reciente
    deleted, _ = Notificacion.objects.filter(fecha_creacion__lt=limite).delete()
    # Log simple (en entorno real usar logging)
    print(f"Notificaciones antiguas eliminadas: {deleted}") 