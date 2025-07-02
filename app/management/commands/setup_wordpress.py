"""
Comando para configurar la integración de WordPress para una Business Unit.

Este comando permite establecer o actualizar la configuración de la integración
de WordPress para una Business Unit específica, sin necesidad de modificar
código fuente o acceder directamente a la base de datos.

Ejemplo de uso:
    python manage.py setup_wordpress huntRED --token="eyJhbGciOiJIUzI1NiIsI..."

"""
from django.core.management.base import BaseCommand, CommandError
from app.models import BusinessUnit


class Command(BaseCommand):
    help = 'Configura la integración de WordPress para una Business Unit'

    def add_arguments(self, parser):
        parser.add_argument('business_unit', type=str,
                            help='Nombre de la Business Unit (huntRED, huntU, Amigro)')
        parser.add_argument('--token', type=str, required=True,
                           help='Token de autenticación para la API de WordPress')
        parser.add_argument('--base-url', type=str,
                           help='URL base de la API de WordPress (opcional)')

    def handle(self, *args, **options):
        business_unit_name = options['business_unit']
        auth_token = options['token']
        base_url = options.get('base_url')

        try:
            # Buscar la Business Unit
            business_unit = BusinessUnit.objects.filter(nombre=business_unit_name).first()
            if not business_unit:
                raise CommandError(f"Business Unit '{business_unit_name}' no encontrada")

            # Obtener configuración actual o crear nueva
            config = business_unit.get_integration_config('wordpress') or {}
            
            # Actualizar con nuevos valores
            config['auth_token'] = auth_token
            if base_url:
                config['base_url'] = base_url
            
            # Guardar configuración
            business_unit.set_integration_config('wordpress', config)
            business_unit.save()
            
            self.stdout.write(self.style.SUCCESS(
                f'✅ Configuración de WordPress actualizada exitosamente para {business_unit_name}'
            ))
            
            # Mostrar resumen de configuración
            self.stdout.write("\nResumen de configuración:")
            self.stdout.write(f"  Business Unit: {business_unit_name}")
            self.stdout.write(f"  Token: {'*' * 10}{auth_token[-6:]}")
            if base_url:
                self.stdout.write(f"  Base URL: {base_url}")
            
            self.stdout.write(self.style.SUCCESS(
                "\nLa integración de WordPress ahora está lista para usar."
            ))
            
        except Exception as e:
            raise CommandError(f"Error al configurar WordPress: {str(e)}")
