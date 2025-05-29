from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

# Importar el modelo de usuario de forma segura
try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
except Exception as e:
    # Fallback en caso de error
    from django.contrib.auth.models import User

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Crea un perfil de usuario cuando se crea un nuevo usuario.
    """
    if created:
        # Aquí puedes añadir lógica para crear perfiles específicos
        # basados en el tipo de usuario (consultor, ejecutivo, etc.)
        pass

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Guarda el perfil del usuario cuando se actualiza el usuario.
    """
    # Aquí puedes añadir lógica para actualizar perfiles
    pass
