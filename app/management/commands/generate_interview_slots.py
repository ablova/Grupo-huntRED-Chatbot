"""
Comando de Django para generar slots de entrevista automáticamente.

Este comando permite generar slots de entrevista para vacantes específicas
o para todas las vacantes activas, con soporte para slots grupales.
"""

import logging
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction

from app.models import Vacante, BusinessUnit
from app.ats.services.interview_service import InterviewService
from app.ats.utils.vacantes import requiere_slots_grupales

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Genera slots de entrevista automáticamente para vacantes activas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--vacancy-id',
            type=int,
            help='ID de la vacante específica para generar slots'
        )
        
        parser.add_argument(
            '--business-unit',
            type=str,
            help='Nombre de la unidad de negocio'
        )
        
        parser.add_argument(
            '--start-date',
            type=str,
            help='Fecha de inicio (YYYY-MM-DD). Por defecto: hoy'
        )
        
        parser.add_argument(
            '--end-date',
            type=str,
            help='Fecha de fin (YYYY-MM-DD). Por defecto: en 30 días'
        )
        
        parser.add_argument(
            '--slot-duration',
            type=int,
            default=45,
            help='Duración de cada slot en minutos (por defecto: 45)'
        )
        
        parser.add_argument(
            '--max-slots-per-day',
            type=int,
            default=8,
            help='Máximo número de slots por día (por defecto: 8)'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar generación incluso si ya existen slots'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar qué slots se generarían sin crearlos'
        )

    def handle(self, *args, **options):
        try:
            # Procesar argumentos
            vacancy_id = options.get('vacancy_id')
            business_unit_name = options.get('business_unit')
            start_date_str = options.get('start_date')
            end_date_str = options.get('end_date')
            slot_duration = options.get('slot_duration')
            max_slots_per_day = options.get('max_slots_per_day')
            force = options.get('force')
            dry_run = options.get('dry_run')
            
            # Establecer fechas por defecto
            if start_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            else:
                start_date = timezone.now().replace(hour=9, minute=0, second=0, microsecond=0)
            
            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            else:
                end_date = start_date + timedelta(days=30)
            
            # Obtener vacantes
            if vacancy_id:
                try:
                    vacancies = [Vacante.objects.get(id=vacancy_id)]
                    self.stdout.write(f"Generando slots para vacante específica: {vacancies[0].titulo}")
                except Vacante.DoesNotExist:
                    raise CommandError(f"Vacante con ID {vacancy_id} no encontrada")
            else:
                # Filtrar por unidad de negocio si se especifica
                if business_unit_name:
                    try:
                        business_unit = BusinessUnit.objects.get(name=business_unit_name)
                        vacancies = Vacante.objects.filter(
                            business_unit=business_unit,
                            activa=True
                        )
                        self.stdout.write(f"Generando slots para unidad de negocio: {business_unit_name}")
                    except BusinessUnit.DoesNotExist:
                        raise CommandError(f"Unidad de negocio '{business_unit_name}' no encontrada")
                else:
                    vacancies = Vacante.objects.filter(activa=True)
                    self.stdout.write("Generando slots para todas las vacantes activas")
            
            if not vacancies:
                self.stdout.write(self.style.WARNING("No se encontraron vacantes activas"))
                return
            
            # Mostrar información de configuración
            self.stdout.write(f"Configuración:")
            self.stdout.write(f"  - Fecha de inicio: {start_date.strftime('%Y-%m-%d')}")
            self.stdout.write(f"  - Fecha de fin: {end_date.strftime('%Y-%m-%d')}")
            self.stdout.write(f"  - Duración de slot: {slot_duration} minutos")
            self.stdout.write(f"  - Máximo slots por día: {max_slots_per_day}")
            self.stdout.write(f"  - Modo dry-run: {'Sí' if dry_run else 'No'}")
            self.stdout.write(f"  - Forzar generación: {'Sí' if force else 'No'}")
            self.stdout.write("")
            
            total_slots_created = 0
            total_vacancies_processed = 0
            
            for vacancy in vacancies:
                self.stdout.write(f"Procesando vacante: {vacancy.titulo}")
                
                # Verificar si ya existen slots para esta vacante
                from app.ats.utils.Events import Event, EventType
                existing_slots = Event.objects.filter(
                    event_type=EventType.ENTREVISTA,
                    description__icontains=str(vacancy.id),
                    start_time__gte=start_date,
                    start_time__lte=end_date
                ).count()
                
                if existing_slots > 0 and not force:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  Ya existen {existing_slots} slots para esta vacante. "
                            "Usa --force para regenerar."
                        )
                    )
                    continue
                
                # Crear servicio de entrevistas
                interview_service = InterviewService(vacancy.business_unit)
                
                if dry_run:
                    # Calcular cuántos slots se generarían
                    current_date = start_date.replace(hour=9, minute=0, second=0, microsecond=0)
                    slots_count = 0
                    
                    while current_date <= end_date:
                        if current_date.weekday() < 5:  # Lunes a viernes
                            current_time = current_date.replace(hour=9, minute=0, second=0, microsecond=0)
                            end_time = current_date.replace(hour=17, minute=0, second=0, microsecond=0)
                            day_slots = 0
                            
                            while current_time < end_time and day_slots < max_slots_per_day:
                                slots_count += 1
                                day_slots += 1
                                current_time += timedelta(minutes=slot_duration)
                        
                        current_date += timedelta(days=1)
                    
                    self.stdout.write(f"  Se generarían {slots_count} slots")
                    total_slots_created += slots_count
                else:
                    # Generar slots reales
                    try:
                        with transaction.atomic():
                            created_slots = interview_service.generate_interview_slots(
                                vacancy=vacancy,
                                start_date=start_date,
                                end_date=end_date,
                                slot_duration=slot_duration,
                                max_slots_per_day=max_slots_per_day
                            )
                            
                            self.stdout.write(
                                self.style.SUCCESS(f"  ✅ Generados {len(created_slots)} slots")
                            )
                            
                            # Mostrar información sobre slots grupales vs individuales
                            group_slots = [s for s in created_slots if s.session_type == 'grupal']
                            individual_slots = [s for s in created_slots if s.session_type == 'individual']
                            
                            if group_slots:
                                self.stdout.write(f"    - Slots grupales: {len(group_slots)}")
                            if individual_slots:
                                self.stdout.write(f"    - Slots individuales: {len(individual_slots)}")
                            
                            total_slots_created += len(created_slots)
                            
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"  ❌ Error generando slots: {str(e)}")
                        )
                        logger.error(f"Error generando slots para vacante {vacancy.id}: {str(e)}")
                        continue
                
                total_vacancies_processed += 1
                self.stdout.write("")
            
            # Resumen final
            self.stdout.write("=" * 50)
            self.stdout.write("RESUMEN")
            self.stdout.write("=" * 50)
            self.stdout.write(f"Vacantes procesadas: {total_vacancies_processed}")
            
            if dry_run:
                self.stdout.write(f"Slots que se generarían: {total_slots_created}")
                self.stdout.write(self.style.WARNING("Modo dry-run: No se crearon slots reales"))
            else:
                self.stdout.write(f"Slots creados: {total_slots_created}")
                self.stdout.write(self.style.SUCCESS("✅ Proceso completado exitosamente"))
            
        except Exception as e:
            logger.error(f"Error en comando generate_interview_slots: {str(e)}")
            raise CommandError(f"Error ejecutando comando: {str(e)}")

    def show_help(self):
        """Muestra ejemplos de uso del comando."""
        self.stdout.write("Ejemplos de uso:")
        self.stdout.write("")
        self.stdout.write("  # Generar slots para todas las vacantes activas")
        self.stdout.write("  python manage.py generate_interview_slots")
        self.stdout.write("")
        self.stdout.write("  # Generar slots para una vacante específica")
        self.stdout.write("  python manage.py generate_interview_slots --vacancy-id 123")
        self.stdout.write("")
        self.stdout.write("  # Generar slots para una unidad de negocio")
        self.stdout.write("  python manage.py generate_interview_slots --business-unit 'Tecnología'")
        self.stdout.write("")
        self.stdout.write("  # Generar slots con fechas específicas")
        self.stdout.write("  python manage.py generate_interview_slots --start-date 2024-01-15 --end-date 2024-02-15")
        self.stdout.write("")
        self.stdout.write("  # Simular generación sin crear slots")
        self.stdout.write("  python manage.py generate_interview_slots --dry-run")
        self.stdout.write("")
        self.stdout.write("  # Forzar regeneración de slots existentes")
        self.stdout.write("  python manage.py generate_interview_slots --force") 