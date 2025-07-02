#!/usr/bin/env python3
"""
Comando de Django para configurar MessageBird en unidades de negocio

Este comando permite configurar fácilmente las credenciales y opciones de MessageBird
para el canal SMS, usando la estructura centralizada de BusinessUnit.
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from app.models import BusinessUnit
import logging
import json

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Configura MessageBird para una o todas las unidades de negocio'

    def add_arguments(self, parser):
        parser.add_argument(
            '--bu-id',
            type=int,
            help='ID de la unidad de negocio específica (opcional, si no se especifica se usa --bu-name o se aplica a todas)'
        )
        parser.add_argument(
            '--bu-name',
            type=str,
            help='Nombre de la unidad de negocio específica (opcional)'
        )
        parser.add_argument(
            '--api-key',
            type=str,
            help='API Key de MessageBird'
        )
        parser.add_argument(
            '--from-number',
            type=str,
            help='Número o nombre remitente para SMS (obligatorio para MessageBird)'
        )
        parser.add_argument(
            '--dlr-enabled',
            action='store_true',
            help='Habilitar reportes de entrega (DLR)'
        )
        parser.add_argument(
            '--dlr-url',
            type=str,
            help='URL de webhook para reportes de entrega'
        )
        parser.add_argument(
            '--sandbox',
            action='store_true',
            help='Habilitar modo sandbox (solo para pruebas)'
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='Listar configuración actual (no realiza cambios)'
        )

    def handle(self, *args, **options):
        # Verificar si solo quiere listar la configuración actual
        if options['list']:
            return self.list_configs()
        
        # Obtener unidades de negocio a configurar
        business_units = self.get_business_units(options)
        
        # Verificar si hay unidades de negocio
        if not business_units:
            raise CommandError('No se encontraron unidades de negocio para configurar')
        
        # Obtener configuración de MessageBird desde argumentos
        config = self.build_config(options)
        
        # Si no hay API key, mostrar error
        if not config.get('api_key') and not options['list']:
            raise CommandError('Se requiere la API key de MessageBird (--api-key)')
        
        # Configurar MessageBird en cada unidad de negocio
        for bu in business_units:
            self.configure_messagebird(bu, config)
            
        self.stdout.write(self.style.SUCCESS(
            f'Configuración de MessageBird actualizada para {len(business_units)} unidades de negocio'
        ))
    
    def get_business_units(self, options):
        """Obtiene las unidades de negocio a configurar según los argumentos."""
        if options['bu_id']:
            try:
                return [BusinessUnit.objects.get(id=options['bu_id'])]
            except BusinessUnit.DoesNotExist:
                raise CommandError(f"No existe unidad de negocio con ID {options['bu_id']}")
        
        if options['bu_name']:
            try:
                return [BusinessUnit.objects.get(name=options['bu_name'])]
            except BusinessUnit.DoesNotExist:
                raise CommandError(f"No existe unidad de negocio con nombre {options['bu_name']}")
            
        # Si no se especifica, aplicar a todas las unidades de negocio activas
        return BusinessUnit.objects.filter(active=True)
    
    def build_config(self, options):
        """Construye la configuración de MessageBird desde los argumentos."""
        config = {}
        
        if options['api_key']:
            config['api_key'] = options['api_key']
            
        if options['from_number']:
            config['from_number'] = options['from_number']
            
        if options['dlr_enabled']:
            config['dlr_enabled'] = True
            
        if options['dlr_url']:
            config['dlr_url'] = options['dlr_url']
            
        if options['sandbox']:
            config['sandbox_mode'] = True
        
        return config
    
    def configure_messagebird(self, business_unit, new_config):
        """Configura MessageBird en una unidad de negocio específica."""
        # Obtener configuración actual
        current_config = business_unit.get_integration_config('messagebird') or {}
        
        # Actualizar configuración (manteniendo valores existentes que no se especifican)
        updated_config = {**current_config, **new_config}
        
        # Guardar configuración actualizada
        business_unit.set_integration_config('messagebird', updated_config)
        
        self.stdout.write(f"Configuración de MessageBird actualizada para {business_unit.name}")
        
    def list_configs(self):
        """Lista la configuración de MessageBird para todas las unidades de negocio."""
        business_units = BusinessUnit.objects.filter(active=True)
        
        self.stdout.write(self.style.SUCCESS("===== Configuración de MessageBird ====="))
        
        for bu in business_units:
            config = bu.get_integration_config('messagebird') or {}
            
            self.stdout.write(f"\n[{bu.id}] {bu.name}:")
            if not config:
                self.stdout.write(self.style.WARNING("  Sin configuración"))
                continue
                
            self.stdout.write(f"  API Key: {'*' * 8 + config.get('api_key', '')[-4:] if config.get('api_key') else 'No configurada'}")
            self.stdout.write(f"  Remitente: {config.get('from_number', 'huntRED')}")
            self.stdout.write(f"  DLR Habilitado: {config.get('dlr_enabled', False)}")
            self.stdout.write(f"  URL Webhook: {config.get('dlr_url', 'No configurado')}")
            self.stdout.write(f"  Modo Sandbox: {config.get('sandbox_mode', False)}")
