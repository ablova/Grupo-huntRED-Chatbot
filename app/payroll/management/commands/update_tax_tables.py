"""
Comando de Django para actualización manual de tablas fiscales
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction

from app.payroll.tasks import (
    update_tax_tables, update_uma_values, update_imss_tables,
    update_infonavit_tables, update_sat_tables, validate_tax_calculations
)
from app.payroll.models import TaxTable, UMARegistry, TaxUpdateLog


class Command(BaseCommand):
    help = 'Actualiza tablas fiscales desde fuentes oficiales'

    def add_arguments(self, parser):
        parser.add_argument(
            '--country',
            type=str,
            default='MEX',
            help='Código del país (MEX, COL, ARG)'
        )
        
        parser.add_argument(
            '--type',
            type=str,
            choices=['all', 'uma', 'imss', 'infonavit', 'sat', 'validate'],
            default='all',
            help='Tipo de actualización'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar actualización incluso si no hay cambios'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simular actualización sin hacer cambios'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mostrar información detallada'
        )

    def handle(self, *args, **options):
        country = options['country']
        update_type = options['type']
        force = options['force']
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Iniciando actualización de tablas fiscales para {country}'
            )
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('MODO SIMULACIÓN - No se harán cambios reales')
            )
        
        try:
            if update_type == 'all' or update_type == 'uma':
                self._update_uma(country, force, dry_run, verbose)
            
            if update_type == 'all' or update_type == 'imss':
                self._update_imss(force, dry_run, verbose)
            
            if update_type == 'all' or update_type == 'infonavit':
                self._update_infonavit(force, dry_run, verbose)
            
            if update_type == 'all' or update_type == 'sat':
                self._update_sat(force, dry_run, verbose)
            
            if update_type == 'validate':
                self._validate_calculations(verbose)
            
            self.stdout.write(
                self.style.SUCCESS('Actualización completada exitosamente')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error durante la actualización: {str(e)}')
            )
            raise CommandError(str(e))

    def _update_uma(self, country, force, dry_run, verbose):
        """Actualiza valores UMA"""
        self.stdout.write('Actualizando valores UMA...')
        
        if dry_run:
            # Simular actualización
            current_uma = UMARegistry.objects.filter(
                country_code=country,
                is_active=True
            ).first()
            
            if current_uma:
                self.stdout.write(
                    f'UMA actual: {current_uma.uma_value} ({current_uma.year})'
                )
            else:
                self.stdout.write('No hay valores UMA activos')
            
            return
        
        # Ejecutar tarea real
        result = update_uma_values.delay(country)
        
        if verbose:
            self.stdout.write(f'Tarea UMA iniciada: {result.id}')
        
        # Esperar resultado
        try:
            task_result = result.get(timeout=300)  # 5 minutos timeout
            
            if task_result['success']:
                self.stdout.write(
                    self.style.SUCCESS('UMA actualizada exitosamente')
                )
                if verbose:
                    self.stdout.write(f"Valores: {task_result['updated_values']}")
            else:
                self.stdout.write(
                    self.style.ERROR(f'Error actualizando UMA: {task_result["error"]}')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error esperando resultado UMA: {str(e)}')
            )

    def _update_imss(self, force, dry_run, verbose):
        """Actualiza tablas IMSS"""
        self.stdout.write('Actualizando tablas IMSS...')
        
        if dry_run:
            # Simular actualización
            imss_tables = TaxTable.objects.filter(
                table_type__startswith='imss_',
                is_active=True
            ).count()
            
            self.stdout.write(f'Tablas IMSS activas: {imss_tables}')
            return
        
        # Ejecutar tarea real
        result = update_imss_tables.delay()
        
        if verbose:
            self.stdout.write(f'Tarea IMSS iniciada: {result.id}')
        
        # Esperar resultado
        try:
            task_result = result.get(timeout=300)
            
            if task_result['success']:
                self.stdout.write(
                    self.style.SUCCESS('Tablas IMSS actualizadas exitosamente')
                )
                if verbose:
                    self.stdout.write(f"Tablas: {task_result['updated_tables']}")
            else:
                self.stdout.write(
                    self.style.ERROR(f'Error actualizando IMSS: {task_result["error"]}')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error esperando resultado IMSS: {str(e)}')
            )

    def _update_infonavit(self, force, dry_run, verbose):
        """Actualiza tablas INFONAVIT"""
        self.stdout.write('Actualizando tablas INFONAVIT...')
        
        if dry_run:
            # Simular actualización
            infonavit_tables = TaxTable.objects.filter(
                table_type__startswith='infonavit_',
                is_active=True
            ).count()
            
            self.stdout.write(f'Tablas INFONAVIT activas: {infonavit_tables}')
            return
        
        # Ejecutar tarea real
        result = update_infonavit_tables.delay()
        
        if verbose:
            self.stdout.write(f'Tarea INFONAVIT iniciada: {result.id}')
        
        # Esperar resultado
        try:
            task_result = result.get(timeout=300)
            
            if task_result['success']:
                self.stdout.write(
                    self.style.SUCCESS('Tablas INFONAVIT actualizadas exitosamente')
                )
                if verbose:
                    self.stdout.write(f"Tablas: {task_result['updated_tables']}")
            else:
                self.stdout.write(
                    self.style.ERROR(f'Error actualizando INFONAVIT: {task_result["error"]}')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error esperando resultado INFONAVIT: {str(e)}')
            )

    def _update_sat(self, force, dry_run, verbose):
        """Actualiza tablas SAT"""
        self.stdout.write('Actualizando tablas SAT...')
        
        if dry_run:
            # Simular actualización
            sat_tables = TaxTable.objects.filter(
                table_type__startswith='sat_',
                is_active=True
            ).count()
            
            self.stdout.write(f'Tablas SAT activas: {sat_tables}')
            return
        
        # Ejecutar tarea real
        result = update_sat_tables.delay()
        
        if verbose:
            self.stdout.write(f'Tarea SAT iniciada: {result.id}')
        
        # Esperar resultado
        try:
            task_result = result.get(timeout=300)
            
            if task_result['success']:
                self.stdout.write(
                    self.style.SUCCESS('Tablas SAT actualizadas exitosamente')
                )
                if verbose:
                    self.stdout.write(f"Tablas: {task_result['updated_tables']}")
            else:
                self.stdout.write(
                    self.style.ERROR(f'Error actualizando SAT: {task_result["error"]}')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error esperando resultado SAT: {str(e)}')
            )

    def _validate_calculations(self, verbose):
        """Valida cálculos fiscales"""
        self.stdout.write('Validando cálculos fiscales...')
        
        # Ejecutar tarea real
        result = validate_tax_calculations.delay()
        
        if verbose:
            self.stdout.write(f'Tarea de validación iniciada: {result.id}')
        
        # Esperar resultado
        try:
            task_result = result.get(timeout=600)  # 10 minutos timeout
            
            if task_result['success']:
                self.stdout.write(
                    self.style.SUCCESS('Validación completada exitosamente')
                )
                
                # Mostrar resultados
                results = task_result['validation_results']
                ok_count = len([r for r in results if r['status'] == 'ok'])
                warning_count = len([r for r in results if r['status'] == 'warning'])
                error_count = len([r for r in results if r['status'] == 'error'])
                
                self.stdout.write(f'Resultados: OK={ok_count}, Warning={warning_count}, Error={error_count}')
                
                if verbose and error_count > 0:
                    self.stdout.write('\nErrores encontrados:')
                    for result in results:
                        if result['status'] == 'error':
                            self.stdout.write(
                                f"- {result['company']}: {result['message']}"
                            )
                
            else:
                self.stdout.write(
                    self.style.ERROR(f'Error en validación: {task_result["error"]}')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error esperando resultado de validación: {str(e)}')
            )

    def _log_update(self, update_type, country, success, message, old_values=None, new_values=None):
        """Registra actualización en log"""
        TaxUpdateLog.objects.create(
            update_type=update_type,
            country_code=country,
            description=message,
            old_values=old_values,
            new_values=new_values,
            success=success,
            source='management_command'
        ) 