from django.core.management.base import BaseCommand
from app.models import BusinessUnit, TalentConfig, WeightingModel

class Command(BaseCommand):
    help = 'Inicializa las configuraciones de talento y ponderaciones por defecto'
    
    def handle(self, *args, **options):
        # Configuraciones por defecto por Business Unit
        default_configs = {
            'huntRED': {
                'time_window_days': 30,
                'min_interactions': 5,
                'sentiment_threshold': 0.7,
                'match_threshold': 0.80,
                'personality_importance': 0.3,
                'cache_ttl': 3600,
                'batch_size': 100
            },
            'huntRED_executive': {
                'time_window_days': 60,
                'min_interactions': 10,
                'sentiment_threshold': 0.8,
                'match_threshold': 0.85,
                'personality_importance': 0.4,
                'cache_ttl': 7200,
                'batch_size': 50
            },
            'huntu': {
                'time_window_days': 15,
                'min_interactions': 3,
                'sentiment_threshold': 0.6,
                'match_threshold': 0.75,
                'personality_importance': 0.2,
                'cache_ttl': 1800,
                'batch_size': 150
            }
        }
        
        # Ponderaciones por defecto por nivel y BU
        default_weights = {
            'huntRED': {
                'entry_level': {
                    'weight_skills': 0.5,
                    'weight_experience': 0.2,
                    'weight_culture': 0.2,
                    'weight_location': 0.1,
                    'culture_importance': 0.2,
                    'experience_requirement': 0.3
                },
                'operativo': {
                    'weight_skills': 0.4,
                    'weight_experience': 0.3,
                    'weight_culture': 0.2,
                    'weight_location': 0.1,
                    'culture_importance': 0.3,
                    'experience_requirement': 0.4
                },
                'gerencia_media': {
                    'weight_skills': 0.3,
                    'weight_experience': 0.3,
                    'weight_culture': 0.3,
                    'weight_location': 0.1,
                    'culture_importance': 0.4,
                    'experience_requirement': 0.5
                },
                'alta_direccion': {
                    'weight_skills': 0.3,
                    'weight_experience': 0.3,
                    'weight_culture': 0.3,
                    'weight_location': 0.1,
                    'culture_importance': 0.5,
                    'experience_requirement': 0.6
                }
            },
            'huntRED_executive': {
                'entry_level': {
                    'weight_skills': 0.4,
                    'weight_experience': 0.3,
                    'weight_culture': 0.2,
                    'weight_location': 0.1,
                    'culture_importance': 0.3,
                    'experience_requirement': 0.4
                },
                'operativo': {
                    'weight_skills': 0.3,
                    'weight_experience': 0.3,
                    'weight_culture': 0.3,
                    'weight_location': 0.1,
                    'culture_importance': 0.4,
                    'experience_requirement': 0.5
                },
                'gerencia_media': {
                    'weight_skills': 0.3,
                    'weight_experience': 0.3,
                    'weight_culture': 0.3,
                    'weight_location': 0.1,
                    'culture_importance': 0.5,
                    'experience_requirement': 0.6
                },
                'alta_direccion': {
                    'weight_skills': 0.2,
                    'weight_experience': 0.3,
                    'weight_culture': 0.4,
                    'weight_location': 0.1,
                    'culture_importance': 0.6,
                    'experience_requirement': 0.7
                }
            },
            'huntu': {
                'entry_level': {
                    'weight_skills': 0.6,
                    'weight_experience': 0.2,
                    'weight_culture': 0.1,
                    'weight_location': 0.1,
                    'culture_importance': 0.1,
                    'experience_requirement': 0.2
                },
                'operativo': {
                    'weight_skills': 0.5,
                    'weight_experience': 0.2,
                    'weight_culture': 0.2,
                    'weight_location': 0.1,
                    'culture_importance': 0.2,
                    'experience_requirement': 0.3
                },
                'gerencia_media': {
                    'weight_skills': 0.4,
                    'weight_experience': 0.3,
                    'weight_culture': 0.2,
                    'weight_location': 0.1,
                    'culture_importance': 0.3,
                    'experience_requirement': 0.4
                },
                'alta_direccion': {
                    'weight_skills': 0.3,
                    'weight_experience': 0.3,
                    'weight_culture': 0.3,
                    'weight_location': 0.1,
                    'culture_importance': 0.4,
                    'experience_requirement': 0.5
                }
            }
        }
        
        # Crear configuraciones y ponderaciones para cada Business Unit
        for bu in BusinessUnit.objects.all():
            if bu.name in default_configs:
                # Crear/actualizar configuración de talento
                config_data = default_configs[bu.name]
                try:
                    config = TalentConfig.objects.get(business_unit=bu)
                    self.stdout.write(f"Actualizando configuración para {bu.name}...")
                except TalentConfig.DoesNotExist:
                    config = TalentConfig(business_unit=bu)
                    self.stdout.write(f"Creando nueva configuración para {bu.name}...")
                
                # Actualizar campos de configuración
                for field, value in config_data.items():
                    setattr(config, field, value)
                
                config.save()
                
                # Crear ponderaciones por nivel
                if bu.name in default_weights:
                    for level, weights in default_weights[bu.name].items():
                        try:
                            weighting = WeightingModel.objects.get(
                                business_unit=bu,
                                position_level=level
                            )
                            self.stdout.write(f"Actualizando ponderación para {bu.name} - {level}...")
                        except WeightingModel.DoesNotExist:
                            weighting = WeightingModel(
                                business_unit=bu,
                                position_level=level
                            )
                            self.stdout.write(f"Creando nueva ponderación para {bu.name} - {level}...")
                        
                        # Actualizar campos de ponderación
                        for field, value in weights.items():
                            setattr(weighting, field, value)
                        
                        weighting.save()
                        
                        # Establecer como default si es el primer nivel
                        if level == 'entry_level':
                            config.default_weights = weighting
                            config.save()
                
                self.stdout.write(self.style.SUCCESS(f"Configuración y ponderaciones para {bu.name} actualizadas exitosamente"))
            else:
                self.stdout.write(self.style.WARNING(f"No hay configuración por defecto para {bu.name}"))
