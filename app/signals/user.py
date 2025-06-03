"""
Señales relacionadas con usuarios y personas en Grupo huntRED®.
Gestiona las señales para eventos de usuarios, candidatos y perfiles.
"""

import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver, Signal
from django.utils import timezone
from app.models import Person, User, EnhancedNetworkGamificationProfile
from app.ats.utils.parser import CVParser

logger = logging.getLogger(__name__)

# Señales personalizadas
profile_completed = Signal()
cv_analyzed = Signal()

@receiver(post_save, sender=Person)
def analyze_cv(sender, instance, created, **kwargs):
    """
    Analiza el CV del candidato y actualiza su perfil.
    """
    # Verificar si hay CV para analizar
    if instance.cv:
        logger.info(f"Analizando CV para {instance.email}")
        
        try:
            parser = CVParser()
            cv_data = parser.parse(instance.cv.path)
            
            # Actualizar campos automáticamente
            fields_updated = []
            
            # Actualizar habilidades si no están ya definidas
            if not instance.skills and cv_data.get('skills'):
                instance.skills = cv_data.get('skills')
                fields_updated.append('skills')
            
            # Actualizar experiencia si no están ya definidas
            if not instance.experience and cv_data.get('experience'):
                instance.experience = cv_data.get('experience')
                fields_updated.append('experience')
            
            # Actualizar educación si no está ya definida
            if not instance.education and cv_data.get('education'):
                instance.education = cv_data.get('education')
                fields_updated.append('education')
            
            # Guardar cambios si hubo actualizaciones
            if fields_updated:
                instance.save(update_fields=fields_updated)
                logger.info(f"CV analizado para {instance.email}, campos actualizados: {', '.join(fields_updated)}")
                
                # Emitir señal
                cv_analyzed.send(
                    sender=sender,
                    instance=instance,
                    cv_data=cv_data,
                    fields_updated=fields_updated
                )
            else:
                logger.info(f"CV analizado para {instance.email}, no se requirieron actualizaciones")
                
        except Exception as e:
            logger.error(f"Error analizando CV: {str(e)}")


@receiver(post_save, sender=User)
def create_person_profile(sender, instance, created, **kwargs):
    """
    Crea un perfil de persona cuando se registra un nuevo usuario.
    """
    if created:
        logger.info(f"Nuevo usuario registrado: {instance.username}")
        
        try:
            # Verificar si ya existe una persona con ese email
            if not Person.objects.filter(email=instance.email).exists():
                # Crear perfil de persona
                person = Person.objects.create(
                    email=instance.email,
                    first_name=instance.first_name,
                    last_name=instance.last_name,
                    user=instance,
                    registration_date=timezone.now()
                )
                logger.info(f"Perfil de persona creado para {instance.email}")
                
                # Crear perfil de gamificación si aplica
                try:
                    EnhancedNetworkGamificationProfile.objects.create(
                        person=person,
                        level=1,
                        points=0
                    )
                    logger.info(f"Perfil de gamificación creado para {instance.email}")
                except Exception as e:
                    logger.error(f"Error creando perfil de gamificación: {str(e)}")
            else:
                # Vincular usuario a persona existente
                person = Person.objects.get(email=instance.email)
                if not person.user:
                    person.user = instance
                    person.save(update_fields=['user'])
                    logger.info(f"Usuario vinculado a persona existente: {instance.email}")
        except Exception as e:
            logger.error(f"Error creando perfil de persona: {str(e)}")
