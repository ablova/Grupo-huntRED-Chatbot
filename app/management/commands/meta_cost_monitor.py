"""
Comando de Django para monitorear y alertar sobre costos de Meta Conversations 2025.

Este módulo ejecuta el monitoreo periódico de costos de mensajería de Meta,
enviando alertas cuando se detectan mensajes enviados fuera de ventana o
en categorías costosas.
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User, Group
import asyncio
import logging
from app.ats.integrations.utils.meta_cost_monitor import MetaCostMonitor, run_cost_monitoring
from app.models import BusinessUnit, MessageLog, BusinessUnitMembership
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Monitorea costos de Meta Conversations 2025 y envía alertas cuando es necesario.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Ejecutar en modo simulación sin enviar alertas',
        )
        parser.add_argument(
            '--business-unit',
            type=str,
            help='ID o nombre de la unidad de negocio específica a monitorear',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=1,
            help='Número de días hacia atrás para analizar',
        )
        parser.add_argument(
            '--threshold',
            type=int,
            default=10,
            help='Umbral de mensajes fuera de ventana para alertar',
        )
        parser.add_argument(
            '--cost-threshold',
            type=float,
            default=5.0,
            help='Umbral de costo estimado para alertar',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando monitor de costos Meta'))
        
        dry_run = options['dry_run']
        days = options['days']
        threshold = options['threshold']
        cost_threshold = options['cost_threshold']
        business_unit_id = None
        
        # Obtener unidad de negocio si se especifica
        if options.get('business_unit'):
            try:
                # Intentar obtener por ID primero
                try:
                    bu_id = int(options['business_unit'])
                    business_unit = BusinessUnit.objects.get(id=bu_id)
                except ValueError:
                    # Si no es un ID válido, buscar por nombre
                    business_unit = BusinessUnit.objects.get(name=options['business_unit'])
                business_unit_id = business_unit.id
                self.stdout.write(f"Monitoreando unidad de negocio: {business_unit.name}")
            except BusinessUnit.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"Unidad de negocio no encontrada: {options['business_unit']}")
                )
                return
                
        # Crear instancia del monitor
        monitor = MetaCostMonitor(
            alert_threshold=threshold,
            cost_threshold=cost_threshold
        )
        
        # Ejecutar monitoreo de forma asíncrona
        loop = asyncio.get_event_loop()
        should_alert = loop.run_until_complete(
            monitor.check_alert_conditions(business_unit_id=business_unit_id)
        )
        
        if should_alert:
            self.stdout.write(
                self.style.WARNING('¡Se detectaron condiciones de alerta!')
            )
            
            # Obtener estadísticas para mostrar
            stats = loop.run_until_complete(
                monitor.get_window_violation_stats(
                    business_unit_id=business_unit_id,
                    days=days
                )
            )
            
            self.stdout.write(f"Total mensajes fuera de ventana: {stats['total_count']}")
            
            # Mostrar desglose por categoría
            self.stdout.write("\nDesglose por categoría:")
            for cat in stats['by_category']:
                self.stdout.write(
                    f"- {cat.get('meta_pricing_category', 'Sin clasificar')}: "
                    f"{cat.get('count', 0)} mensajes, "
                    f"Costo: ${cat.get('total_cost', 0):.2f}"
                )
            
            # Mostrar desglose por plantilla
            self.stdout.write("\nPlantillas problemáticas:")
            for template in stats['by_template'][:5]:  # Top 5
                self.stdout.write(
                    f"- {template.get('template_name', 'Sin nombre')}: "
                    f"{template.get('count', 0)} mensajes"
                )
                
            # Obtener sugerencias de optimización
            suggestions = loop.run_until_complete(
                monitor.generate_optimization_suggestions(business_unit_id=business_unit_id)
            )
            
            self.stdout.write("\nSugerencias de optimización:")
            for suggestion in suggestions:
                self.stdout.write(f"- [{suggestion['type']}] {suggestion['action']}")
            
            # Enviar alertas si no es un dry run
            if not dry_run:
                self.stdout.write("Enviando alertas por email...")
                
                # Obtener destinatarios apropiados basados en permisos
                admin_emails = self._get_admin_emails(business_unit_id)
                
                if admin_emails:
                    self.stdout.write(f"Enviando alertas a: {', '.join(admin_emails)}")
                    
                    # Enviar la alerta
                    loop.run_until_complete(
                        monitor.send_cost_alert(
                            admin_emails,
                            business_unit_id=business_unit_id
                        )
                    )
                    
                    self.stdout.write(self.style.SUCCESS("Alertas enviadas correctamente"))
                else:
                    self.stdout.write(
                        self.style.ERROR("No se encontraron destinatarios para las alertas")
                    )
            else:
                self.stdout.write(
                    self.style.NOTICE("Modo dry-run: No se enviaron alertas")
                )
        else:
            self.stdout.write(
                self.style.SUCCESS('No se detectaron condiciones de alerta')
            )
            
    def _get_admin_emails(self, business_unit_id=None):
        """Obtiene emails de administradores apropiados para las alertas."""
        admin_emails = []
        
        # Superadmins siempre reciben todas las alertas
        superadmin_emails = User.objects.filter(
            is_superuser=True, 
            is_active=True,
            email__isnull=False
        ).exclude(email='').values_list('email', flat=True)
        
        admin_emails.extend(superadmin_emails)
        
        # Para alertas de una BU específica, incluir admins de esa BU
        if business_unit_id:
            # Obtener admins específicos de la BU
            bu_admin_emails = User.objects.filter(
                is_active=True,
                businessunitmembership__business_unit_id=business_unit_id,
                businessunitmembership__role__in=['admin', 'superadmin'],
                email__isnull=False
            ).exclude(email='').values_list('email', flat=True)
            
            admin_emails.extend(bu_admin_emails)
            
            # Consultores asignados a la BU
            consultant_emails = User.objects.filter(
                is_active=True,
                businessunitmembership__business_unit_id=business_unit_id,
                businessunitmembership__role='consultor',
                groups__name='consultor',
                email__isnull=False
            ).exclude(email='').values_list('email', flat=True)
            
            admin_emails.extend(consultant_emails)
        else:
            # Para alertas globales, incluir todos los admins del sistema
            system_admin_emails = User.objects.filter(
                is_active=True,
                groups__name__in=['admin', 'superadmin'],
                email__isnull=False
            ).exclude(email='').values_list('email', flat=True)
            
            admin_emails.extend(system_admin_emails)
        
        # Eliminar duplicados y devolver la lista final
        return list(set(admin_emails))
