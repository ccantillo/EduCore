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