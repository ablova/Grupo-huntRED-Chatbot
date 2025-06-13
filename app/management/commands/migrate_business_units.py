from django.core.management.base import BaseCommand
from django.db import transaction
from app.models import BusinessUnit
from app.ats.validators.business_unit_validators import validate_business_unit_config
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Migra los datos existentes de BusinessUnit a la nueva estructura'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando migración de BusinessUnits...')
        
        try:
            with transaction.atomic():
                for bu in BusinessUnit.objects.all():
                    self.stdout.write(f'Procesando {bu.name}...')
                    
                    # Generar código único si no existe
                    if not bu.code:
                        bu.code = bu.name.lower().replace(' ', '_')[:10]
                    
                    # Migrar configuración general
                    if not bu.settings:
                        bu.settings = {
                            'general': {
                                'timezone': 'America/Mexico_City',
                                'language': 'es',
                                'currency': 'MXN',
                                'date_format': 'DD/MM/YYYY',
                                'time_format': '24h'
                            },
                            'notifications': {
                                'email_enabled': True,
                                'sms_enabled': True,
                                'push_enabled': True,
                                'notification_channels': ['email', 'sms', 'push'],
                                'notification_templates': {}
                            },
                            'security': {
                                'password_policy': {
                                    'min_length': 8,
                                    'require_special_chars': True,
                                    'require_numbers': True,
                                    'require_uppercase': True
                                },
                                'session_timeout': 30,
                                'max_login_attempts': 5,
                                '2fa_required': False
                            },
                            'branding': {
                                'logo_url': '',
                                'primary_color': '#000000',
                                'secondary_color': '#FFFFFF',
                                'font_family': 'Arial',
                                'custom_css': ''
                            }
                        }
                    
                    # Migrar integraciones
                    if not bu.integrations:
                        bu.integrations = {
                            'whatsapp': {
                                'enabled': bu.whatsapp_enabled,
                                'api_key': '',
                                'phone_number': bu.admin_phone or '',
                                'templates': {}
                            },
                            'telegram': {
                                'enabled': bu.telegram_enabled,
                                'bot_token': '',
                                'channel_id': '',
                                'commands': {}
                            },
                            'messenger': {
                                'enabled': bu.messenger_enabled,
                                'page_id': '',
                                'access_token': '',
                                'greeting_text': ''
                            },
                            'instagram': {
                                'enabled': bu.instagram_enabled,
                                'account_id': '',
                                'access_token': ''
                            },
                            'wordpress': {
                                'enabled': bool(bu.wordpress_base_url),
                                'base_url': bu.wordpress_base_url or '',
                                'auth_token': bu.wordpress_auth_token or '',
                                'endpoints': {}
                            }
                        }
                    
                    # Migrar configuración de ATS
                    if not bu.ats_config:
                        bu.ats_config = {
                            'workflow': {
                                'stages': ['screening', 'interview', 'offer'],
                                'default_stage': 'screening',
                                'auto_advance': True,
                                'notifications': {
                                    'stage_change': True,
                                    'new_candidate': True
                                }
                            },
                            'scoring': {
                                'criteria': ['experience', 'skills', 'education'],
                                'weights': {
                                    'experience': 0.4,
                                    'skills': 0.4,
                                    'education': 0.2
                                },
                                'threshold': 0.7
                            },
                            'automation': {
                                'auto_screening': True,
                                'auto_interview_scheduling': True,
                                'auto_rejection': True,
                                'auto_followup': True
                            },
                            'templates': {
                                'job_description': '',
                                'offer_letter': '',
                                'rejection_email': ''
                            }
                        }
                    
                    # Migrar configuración de analytics
                    if not bu.analytics_config:
                        bu.analytics_config = {
                            'metrics': {
                                'recruitment': {
                                    'time_to_hire': True,
                                    'cost_per_hire': True,
                                    'quality_of_hire': True
                                },
                                'candidate': {
                                    'application_rate': True,
                                    'acceptance_rate': True,
                                    'dropout_rate': True
                                },
                                'business': {
                                    'revenue': True,
                                    'profit_margin': True,
                                    'customer_satisfaction': True
                                }
                            },
                            'reporting': {
                                'frequency': 'weekly',
                                'recipients': [],
                                'formats': ['pdf', 'excel']
                            },
                            'dashboards': {
                                'recruitment': [],
                                'business': []
                            }
                        }
                    
                    # Migrar configuración de learning
                    if not bu.learning_config:
                        bu.learning_config = {
                            'courses': {
                                'enabled': True,
                                'categories': ['technical', 'soft_skills'],
                                'completion_criteria': {
                                    'min_score': 70,
                                    'attendance_required': True
                                }
                            },
                            'certifications': {
                                'enabled': True,
                                'validity_period': 365,
                                'renewal_required': True
                            },
                            'assessments': {
                                'frequency': 'monthly',
                                'types': ['quiz', 'project', 'interview'],
                                'passing_score': 70
                            }
                        }
                    
                    # Validar configuración
                    try:
                        validate_business_unit_config(bu)
                        bu.save()
                        self.stdout.write(self.style.SUCCESS(f'✓ {bu.name} migrado exitosamente'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'✗ Error validando {bu.name}: {str(e)}'))
                        raise
                
                self.stdout.write(self.style.SUCCESS('Migración completada exitosamente'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error durante la migración: {str(e)}'))
            raise 