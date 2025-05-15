from django.db import migrations, models
import django.db.models.deletion

def migrate_users_to_person(apps, schema_editor):
    """
    Migra datos de User a Person para el módulo SEXSI.
    """
    # Obtener modelos
    User = apps.get_model('auth', 'User')
    Person = apps.get_model('app', 'Person')
    ConsentAgreement = apps.get_model('app', 'ConsentAgreement')
    DiscountCoupon = apps.get_model('app', 'DiscountCoupon')
    
    # Mapeo de usuarios a personas
    user_to_person_map = {}
    
    # Para cada acuerdo de consentimiento
    for agreement in ConsentAgreement.objects.all():
        # Procesar creador
        if agreement.creator_id and agreement.creator_id not in user_to_person_map:
            user = User.objects.filter(id=agreement.creator_id).first()
            if user:
                # Crear o encontrar Person correspondiente
                person, created = Person.objects.get_or_create(
                    email=user.email,
                    defaults={
                        'nombre': user.first_name or 'Anónimo',
                        'apellido_paterno': user.last_name or 'Anónimo',
                        'skills': 'Usuario SEXSI',  # Valor por defecto para cumplir con is_profile_complete
                        'phone': '0000000000',      # Valor por defecto para cumplir con is_profile_complete
                    }
                )
                user_to_person_map[user.id] = person.id
                
            # Actualizar referencia en el acuerdo
            if user and user.id in user_to_person_map:
                agreement.creator_id = user_to_person_map[user.id]
        
        # Procesar invitado
        if agreement.invitee_id and agreement.invitee_id not in user_to_person_map:
            user = User.objects.filter(id=agreement.invitee_id).first()
            if user:
                # Crear o encontrar Person correspondiente
                person, created = Person.objects.get_or_create(
                    email=user.email,
                    defaults={
                        'nombre': user.first_name or 'Anónimo',
                        'apellido_paterno': user.last_name or 'Anónimo',
                        'skills': 'Usuario SEXSI',  # Valor por defecto para cumplir con is_profile_complete
                        'phone': '0000000000',      # Valor por defecto para cumplir con is_profile_complete
                    }
                )
                user_to_person_map[user.id] = person.id
                
            # Actualizar referencia en el acuerdo
            if user and user.id in user_to_person_map:
                agreement.invitee_id = user_to_person_map[user.id]
        
        # Guardar cambios
        agreement.save()
    
    # Migrar cupones de descuento
    for coupon in DiscountCoupon.objects.all():
        if coupon.user_id and coupon.user_id not in user_to_person_map:
            user = User.objects.filter(id=coupon.user_id).first()
            if user:
                # Crear o encontrar Person correspondiente
                person, created = Person.objects.get_or_create(
                    email=user.email,
                    defaults={
                        'nombre': user.first_name or 'Anónimo',
                        'apellido_paterno': user.last_name or 'Anónimo',
                        'skills': 'Usuario SEXSI',  # Valor por defecto
                        'phone': '0000000000',      # Valor por defecto
                    }
                )
                user_to_person_map[user.id] = person.id
                
            # Actualizar referencia en el cupón
            if user and user.id in user_to_person_map:
                coupon.user_id = user_to_person_map[user.id]
                coupon.save()


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),  # Asegúrate de que esta sea la migración correcta
    ]

    operations = [
        migrations.RunPython(migrate_users_to_person),
    ]
