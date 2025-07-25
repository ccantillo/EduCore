# signals.py para la app users
# Señales que se disparan automáticamente - enviar email al crear usuario, etc.

# TODO: señales automáticas cuando las necesitemos 

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()


@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    """
    Crear perfil automáticamente cuando se registra un nuevo usuario.
    Esta señal se dispara cada vez que se guarda un objeto User.
    """
    if created:
        try:
            # Crear perfil asociado al usuario
            Profile.objects.create(user=instance)
            print(f"Perfil creado exitosamente para el usuario: {instance.username}")
        except Exception as e:
            # Log del error pero no fallar la creación del usuario
            print(f"Error al crear perfil para usuario {instance.username}: {e}")


@receiver(post_save, sender=User)
def enviar_email_bienvenida_usuario(sender, instance, created, **kwargs):
    """
    Enviar email de bienvenida cuando se crea un nuevo usuario.
    Se ejecuta de forma asíncrona para no bloquear la creación del usuario.
    """
    if created and instance.email:
        try:
            # Importar la tarea aquí para evitar importaciones circulares
            from .tasks import enviar_email_bienvenida
            
            # Ejecutar tarea asíncrona para envío de email
            enviar_email_bienvenida.delay(instance.id)
            print(f"Tarea de email de bienvenida programada para {instance.username}")
            
        except Exception as e:
            # Log del error pero no fallar la creación del usuario
            print(f"Error al programar email de bienvenida para {instance.username}: {e}") 