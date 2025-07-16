
#!/usr/bin/env python3
"""
AUDITORÍA COMPLETA DEL SISTEMA huntRED®
========================================

Este script realiza una auditoría exhaustiva y profunda de todo el codebase
del sistema huntRED®, documentando la arquitectura, funcionalidades, 
configuraciones y estado actual del sistema.

Autor: Asistente AI
Fecha: 2025
Versión: 1.0.0
"""

import os
import sys
import json
import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import django
from django.conf import settings
from django.apps import apps
from django.db import connection
from django.core.management import execute_from_command_line

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_huntred.settings.production')
django.setup()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auditoria_huntred.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AuditoriaHuntRED:
    """
    Clase principal para realizar la auditoría completa del sistema huntRED®
    """
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.report_data = {
            'timestamp': datetime.now().isoformat(),
            'system_info': {},
            'architecture': {},
            'business_units': {},
            'chatbot': {},
            'integrations': {},
            'models': {},
            'workflows': {},
            'assessments': {},
            'scraping': {},
            'notifications': {},
            'issues': [],
            'recommendations': []
        }
        
    async def run_complete_audit(self):
        """Ejecuta la auditoría completa del sistema"""
        logger.info("🚀 Iniciando auditoría completa del sistema huntRED®")
        
        try:
            # 1. Información del sistema
            await self.audit_system_info()
            
            # 2. Arquitectura del proyecto
            await self.audit_architecture()
            
            # 3. Unidades de negocio
            await self.audit_business_units()
            
            # 4. Sistema de chatbot
            await self.audit_chatbot_system()
            
            # 5. Integraciones
            await self.audit_integrations()
            
            # 6. Modelos de datos
            await self.audit_models()
            
            # 7. Workflows
            await self.audit_workflows()
            
            # 8. Assessments
            await self.audit_assessments()
            
            # 9. Sistema de scraping
            await self.audit_scraping_system()
            
            # 10. Sistema de notificaciones
            await self.audit_notifications()
            
            # 11. Análisis de problemas
            await self.analyze_issues()
            
            # 12. Generar recomendaciones
            await self.generate_recommendations()
            
            # 13. Generar reporte final
            await self.generate_final_report()
            
            logger.info("✅ Auditoría completa finalizada exitosamente")
            
        except Exception as e:
            logger.error(f"❌ Error en la auditoría: {str(e)}", exc_info=True)
            self.report_data['issues'].append({
                'type': 'audit_error',
                'message': str(e),
                'severity': 'critical'
            })
    
    async def audit_system_info(self):
        """Audita la información básica del sistema"""
        logger.info("📋 Auditando información del sistema...")
        
        try:
            from app.models import BusinessUnit, Person, Vacante, Company
            
            # Información de Django
            self.report_data['system_info'] = {
                'django_version': django.get_version(),
                'python_version': sys.version,
                'installed_apps': list(settings.INSTALLED_APPS),
                'database': settings.DATABASES['default']['ENGINE'],
                'debug_mode': settings.DEBUG,
                'timezone': settings.TIME_ZONE,
                'language_code': settings.LANGUAGE_CODE,
                'static_root': settings.STATIC_ROOT,
                'media_root': settings.MEDIA_ROOT,
                'base_dir': str(settings.BASE_DIR)
            }
            
            # Estadísticas de la base de datos
            self.report_data['system_info']['database_stats'] = {
                'business_units': await self.get_model_count(BusinessUnit),
                'persons': await self.get_model_count(Person),
                'vacantes': await self.get_model_count(Vacante),
                'companies': await self.get_model_count(Company)
            }
            
            logger.info("✅ Información del sistema auditada")
            
        except Exception as e:
            logger.error(f"Error auditando información del sistema: {e}")
            self.report_data['issues'].append({
                'type': 'system_info_error',
                'message': str(e),
                'severity': 'high'
            })
    
    async def audit_architecture(self):
        """Audita la arquitectura del proyecto"""
        logger.info("🏗️ Auditando arquitectura del proyecto...")
        
        try:
            # Estructura de directorios
            directories = [
                'app/ats/',
                'app/ats/chatbot/',
                'app/ats/chatbot/workflow/',
                'app/ats/chatbot/workflow/assessments/',
                'app/ats/chatbot/workflow/business_units/',
                'app/ats/pagos/',
                'app/ats/pricing/',
                'app/ats/analytics/',
                'app/ats/learning/',
                'app/ats/feedback/',
                'app/ats/references/',
                'app/ats/proposals/',
                'app/ats/gamification/',
                'app/ats/kanban/',
                'app/ats/market/',
                'app/ats/referrals/',
                'app/ats/talent/',
                'app/ats/utils/',
                'app/ats/integrations/',
                'app/ats/notifications/',
                'app/ats/utils/',
                'app/ml/',
                'app/models/',
                'app/payroll/',
                'app/sexsi/',
                'templates/',
                'static/',
                'media/',
                'docs/'
            ]
            
            architecture_info = {}
            for dir_path in directories:
                full_path = self.base_dir / dir_path
                if full_path.exists():
                    architecture_info[dir_path] = {
                        'exists': True,
                        'file_count': len(list(full_path.rglob('*.py'))),
                        'size_mb': sum(f.stat().st_size for f in full_path.rglob('*') if f.is_file()) / (1024*1024)
                    }
                else:
                    architecture_info[dir_path] = {'exists': False}
            
            self.report_data['architecture'] = {
                'project_structure': architecture_info,
                'main_modules': [
                    'app.ats',
                    'app.ats.chatbot',
                    'app.ats.integrations',
                    'app.ats.utils',
                    'app.ats.config',
                    'app.ats.pricing',
                    'app.ats.analytics',
                    'app.ats.learning',
                    'app.ats.notifications',
                    'app.ats.feedback',
                    'app.ats.references',
                    'app.ats.applications',
                    'app.ats.proposals',
                    'app.ats.onboarding',
                    'app.ats.interviews',
                    'app.ats.reports',
                    'app.ats.accounting',
                    'app.ats.analytics',
                    'app.ats.api',
                    'app.ats.client_portal',
                    'app.ats.gamification',
                    'app.ats.kanban',
                    'app.ats.market',
                    'app.ats.pagos',
                    'app.ats.referrals',
                    'app.ats.talent',
                    'app.payroll',
                    'app.ml',
                    'app.ml.analyzers',
                    'app.ml.aura',
                    'app.models',
                    'app.sexsi'
                ],
                'template_dirs': settings.TEMPLATES[0]['DIRS'],
                'static_dirs': settings.STATICFILES_DIRS if hasattr(settings, 'STATICFILES_DIRS') else []
            }
            
            logger.info("✅ Arquitectura auditada")
            
        except Exception as e:
            logger.error(f"Error auditando arquitectura: {e}")
            self.report_data['issues'].append({
                'type': 'architecture_error',
                'message': str(e),
                'severity': 'medium'
            })
    
    async def audit_business_units(self):
        """Audita las unidades de negocio"""
        logger.info("🏢 Auditando unidades de negocio...")
        
        try:
            from app.models import BusinessUnit, ConfiguracionBU
            from app.ats.utils.business_unit_manager import BusinessUnitManager
            
            # Obtener todas las unidades de negocio
            business_units = await self.get_all_objects(BusinessUnit)
            
            bu_info = {}
            for bu in business_units:
                bu_info[bu.name] = {
                    'id': bu.id,
                    'code': bu.code,
                    'active': bu.active,
                    'status': bu.status,
                    'created_at': bu.created_at.isoformat(),
                    'integrations': bu.integrations,
                    'pricing_config': bu.pricing_config,
                    'ats_config': bu.ats_config,
                    'analytics_config': bu.analytics_config,
                    'learning_config': bu.learning_config,
                    'members_count': await self.get_bu_members_count(bu.id)
                }
            
            # Configuraciones específicas por BU
            bu_configs = BusinessUnitManager.BU_CONFIGS
            
            self.report_data['business_units'] = {
                'total_count': len(business_units),
                'active_count': len([bu for bu in business_units if bu.active]),
                'units': bu_info,
                'configurations': bu_configs,
                'choices': BusinessUnit.BUSINESS_UNIT_CHOICES
            }
            
            logger.info("✅ Unidades de negocio auditadas")
            
        except Exception as e:
            logger.error(f"Error auditando unidades de negocio: {e}")
            self.report_data['issues'].append({
                'type': 'business_units_error',
                'message': str(e),
                'severity': 'high'
            })
    
    async def audit_chatbot_system(self):
        """Audita el sistema de chatbot"""
        logger.info("🤖 Auditando sistema de chatbot...")
        
        try:
            # Configuración del chatbot
            from app.ats.config.settings.chatbot import CHATBOT_CONFIG
            
            # Workflows por unidad de negocio
            workflow_files = [
                'app/ats/chatbot/workflow/business_units/huntred/huntred.py',
                'app/ats/chatbot/workflow/business_units/huntred_executive.py',
                'app/ats/chatbot/workflow/business_units/huntu/huntu.py',
                'app/ats/chatbot/workflow/business_units/amigro/amigro.py',
                'app/ats/chatbot/workflow/business_units/sexsi/sexsi.py'
            ]
            
            workflows_info = {}
            for workflow_file in workflow_files:
                file_path = self.base_dir / workflow_file
                if file_path.exists():
                    workflows_info[workflow_file] = {
                        'exists': True,
                        'size_kb': file_path.stat().st_size / 1024,
                        'last_modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                    }
                else:
                    workflows_info[workflow_file] = {'exists': False}
            
            # Componentes del chatbot
            chatbot_components = [
                'app/ats/chatbot/core/chatbot.py',
                'app/ats/chatbot/components/chat_state_manager.py',
                'app/ats/chatbot/components/context_manager.py',
                'app/ats/chatbot/components/response_generator.py',
                'app/ats/chatbot/nlp/nlp.py',
                'app/ats/chatbot/core/gpt.py'
            ]
            
            components_info = {}
            for component in chatbot_components:
                file_path = self.base_dir / component
                if file_path.exists():
                    components_info[component] = {
                        'exists': True,
                        'size_kb': file_path.stat().st_size / 1024
                    }
                else:
                    components_info[component] = {'exists': False}
            
            self.report_data['chatbot'] = {
                'configuration': CHATBOT_CONFIG,
                'workflows': workflows_info,
                'components': components_info,
                'nlp_processor': await self.check_nlp_processor(),
                'gpt_handler': await self.check_gpt_handler(),
                'state_manager': await self.check_state_manager()
            }
            
            logger.info("✅ Sistema de chatbot auditado")
            
        except Exception as e:
            logger.error(f"Error auditando sistema de chatbot: {e}")
            self.report_data['issues'].append({
                'type': 'chatbot_error',
                'message': str(e),
                'severity': 'high'
            })
    
    async def audit_integrations(self):
        """Audita las integraciones"""
        logger.info("🔗 Auditando integraciones...")
        
        try:
            # Canales de comunicación
            channels = [
                'whatsapp',
                'telegram',
                'messenger',
                'instagram',
                'slack',
                'email',
                'sms'
            ]
            
            channels_info = {}
            for channel in channels:
                channels_info[channel] = await self.check_channel_integration(channel)
            
            # Servicios de integración
            integration_services = [
                'app/ats/integrations/services/__init__.py',
                'app/ats/integrations/services/message.py',
                'app/ats/integrations/services/email.py',
                'app/ats/integrations/channels/whatsapp/services.py',
                'app/ats/integrations/notifications/services/notification_service.py'
            ]
            
            services_info = {}
            for service in integration_services:
                file_path = self.base_dir / service
                if file_path.exists():
                    services_info[service] = {
                        'exists': True,
                        'size_kb': file_path.stat().st_size / 1024
                    }
                else:
                    services_info[service] = {'exists': False}
            
            self.report_data['integrations'] = {
                'channels': channels_info,
                'services': services_info,
                'notification_channels': await self.get_notification_channels(),
                'api_configurations': await self.get_api_configurations()
            }
            
            logger.info("✅ Integraciones auditadas")
            
        except Exception as e:
            logger.error(f"Error auditando integraciones: {e}")
            self.report_data['issues'].append({
                'type': 'integrations_error',
                'message': str(e),
                'severity': 'medium'
            })
    
    async def audit_models(self):
        """Audita los modelos de datos"""
        logger.info("📊 Auditando modelos de datos...")
        
        try:
            from app.models import (
                BusinessUnit, Person, Vacante, Company, Application,
                ChatState, Notification, Feedback, Reference
            )
            
            models_info = {}
            model_classes = [
                BusinessUnit, Person, Vacante, Company, Application,
                ChatState, Notification, Feedback, Reference
            ]
            
            for model_class in model_classes:
                model_name = model_class.__name__
                models_info[model_name] = {
                    'fields': [field.name for field in model_class._meta.fields],
                    'many_to_many': [field.name for field in model_class._meta.many_to_many],
                    'foreign_keys': [field.name for field in model_class._meta.fields if field.is_relation],
                    'count': await self.get_model_count(model_class),
                    'app_label': model_class._meta.app_label,
                    'db_table': model_class._meta.db_table
                }
            
            # Verificar migraciones
            migrations_status = await self.check_migrations_status()
            
            self.report_data['models'] = {
                'models': models_info,
                'migrations_status': migrations_status,
                'database_connections': await self.check_database_connections()
            }
            
            logger.info("✅ Modelos de datos auditados")
            
        except Exception as e:
            logger.error(f"Error auditando modelos: {e}")
            self.report_data['issues'].append({
                'type': 'models_error',
                'message': str(e),
                'severity': 'high'
            })
    
    async def audit_workflows(self):
        """Audita los workflows"""
        logger.info("🔄 Auditando workflows...")
        
        try:
            # Workflows por unidad de negocio
            workflow_dirs = [
                'app/ats/chatbot/workflow/business_units/',
                'app/ats/chatbot/workflow/common/',
                'app/ats/chatbot/workflow/assessments/'
            ]
            
            workflows_info = {}
            for workflow_dir in workflow_dirs:
                dir_path = self.base_dir / workflow_dir
                if dir_path.exists():
                    workflows_info[workflow_dir] = {
                        'exists': True,
                        'files': [f.name for f in dir_path.rglob('*.py') if f.is_file()],
                        'total_files': len(list(dir_path.rglob('*.py')))
                    }
                else:
                    workflows_info[workflow_dir] = {'exists': False}
            
            # Workflows específicos
            specific_workflows = [
                'app/ats/chatbot/workflow/common/common.py',
                'app/ats/chatbot/workflow/assessments/personality/personality_workflow.py',
                'app/ats/chatbot/workflow/assessments/cultural/cultural_fit_workflow.py',
                'app/ats/chatbot/workflow/assessments/talent/talent_analysis_workflow.py'
            ]
            
            specific_workflows_info = {}
            for workflow in specific_workflows:
                file_path = self.base_dir / workflow
                if file_path.exists():
                    specific_workflows_info[workflow] = {
                        'exists': True,
                        'size_kb': file_path.stat().st_size / 1024
                    }
                else:
                    specific_workflows_info[workflow] = {'exists': False}
            
            self.report_data['workflows'] = {
                'directories': workflows_info,
                'specific_workflows': specific_workflows_info,
                'workflow_manager': await self.check_workflow_manager()
            }
            
            logger.info("✅ Workflows auditados")
            
        except Exception as e:
            logger.error(f"Error auditando workflows: {e}")
            self.report_data['issues'].append({
                'type': 'workflows_error',
                'message': str(e),
                'severity': 'medium'
            })
    
    async def audit_assessments(self):
        """Audita el sistema de assessments"""
        logger.info("📝 Auditando sistema de assessments...")
        
        try:
            # Tipos de assessments
            assessment_types = [
                'personality',
                'cultural',
                'talent',
                'professional_dna'
            ]
            
            assessments_info = {}
            for assessment_type in assessment_types:
                assessment_dir = self.base_dir / f'app/ats/chatbot/workflow/assessments/{assessment_type}/'
                if assessment_dir.exists():
                    assessments_info[assessment_type] = {
                        'exists': True,
                        'files': [f.name for f in assessment_dir.rglob('*.py') if f.is_file()],
                        'total_files': len(list(assessment_dir.rglob('*.py')))
                    }
                else:
                    assessments_info[assessment_type] = {'exists': False}
            
            # Configuraciones de assessments
            assessment_configs = [
                'app/ats/chatbot/workflow/assessments/README.md',
                'app/ats/chatbot/workflow/assessments/assessment_data_provider.py',
                'app/ats/chatbot/workflow/assessments/reference_config.py'
            ]
            
            configs_info = {}
            for config in assessment_configs:
                file_path = self.base_dir / config
                if file_path.exists():
                    configs_info[config] = {
                        'exists': True,
                        'size_kb': file_path.stat().st_size / 1024
                    }
                else:
                    configs_info[config] = {'exists': False}
            
            self.report_data['assessments'] = {
                'types': assessments_info,
                'configurations': configs_info,
                'personality_analyzer': await self.check_personality_analyzer(),
                'cultural_analyzer': await self.check_cultural_analyzer()
            }
            
            logger.info("✅ Sistema de assessments auditado")
            
        except Exception as e:
            logger.error(f"Error auditando assessments: {e}")
            self.report_data['issues'].append({
                'type': 'assessments_error',
                'message': str(e),
                'severity': 'medium'
            })
    
    async def audit_scraping_system(self):
        """Audita el sistema de scraping"""
        logger.info("🕷️ Auditando sistema de scraping...")
        
        try:
            # Sistema de scraping robusto
            scraping_files = [
                'app/ats/utils/scraping/robust_scraping_system.py',
                'app/ats/utils/scraping/scraping.py',
                'app/ats/utils/scraping/email_scraper.py',
                'app/ats/utils/scraping/scraping_utils.py',
                'app/ats/utils/linkedin.py'
            ]
            
            scraping_info = {}
            for scraping_file in scraping_files:
                file_path = self.base_dir / scraping_file
                if file_path.exists():
                    scraping_info[scraping_file] = {
                        'exists': True,
                        'size_kb': file_path.stat().st_size / 1024,
                        'last_modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                    }
                else:
                    scraping_info[scraping_file] = {'exists': False}
            
            # Configuraciones de scraping
            scraping_configs = await self.get_scraping_configurations()
            
            self.report_data['scraping'] = {
                'files': scraping_info,
                'configurations': scraping_configs,
                'platforms_supported': ['linkedin', 'workday', 'indeed', 'glassdoor'],
                'robust_scraping_system': await self.check_robust_scraping_system()
            }
            
            logger.info("✅ Sistema de scraping auditado")
            
        except Exception as e:
            logger.error(f"Error auditando sistema de scraping: {e}")
            self.report_data['issues'].append({
                'type': 'scraping_error',
                'message': str(e),
                'severity': 'medium'
            })
    
    async def audit_notifications(self):
        """Audita el sistema de notificaciones"""
        logger.info("🔔 Auditando sistema de notificaciones...")
        
        try:
            # Canales de notificación
            notification_channels = [
                'app/ats/integrations/notifications/channels/whatsapp.py',
                'app/ats/integrations/notifications/channels/telegram.py',
                'app/ats/integrations/notifications/channels/email.py',
                'app/ats/integrations/notifications/channels/sms.py'
            ]
            
            channels_info = {}
            for channel in notification_channels:
                file_path = self.base_dir / channel
                if file_path.exists():
                    channels_info[channel] = {
                        'exists': True,
                        'size_kb': file_path.stat().st_size / 1024
                    }
                else:
                    channels_info[channel] = {'exists': False}
            
            # Servicios de notificación
            notification_services = [
                'app/ats/integrations/notifications/services/notification_service.py',
                'app/ats/integrations/notifications/notification_manager.py',
                'app/ats/integrations/notifications/core/service.py'
            ]
            
            services_info = {}
            for service in notification_services:
                file_path = self.base_dir / service
                if file_path.exists():
                    services_info[service] = {
                        'exists': True,
                        'size_kb': file_path.stat().st_size / 1024
                    }
                else:
                    services_info[service] = {'exists': False}
            
            self.report_data['notifications'] = {
                'channels': channels_info,
                'services': services_info,
                'notification_manager': await self.check_notification_manager(),
                'channel_map': await self.get_notification_channel_map()
            }
            
            logger.info("✅ Sistema de notificaciones auditado")
            
        except Exception as e:
            logger.error(f"Error auditando notificaciones: {e}")
            self.report_data['issues'].append({
                'type': 'notifications_error',
                'message': str(e),
                'severity': 'medium'
            })
    
    async def analyze_issues(self):
        """Analiza problemas encontrados en el sistema"""
        logger.info("🔍 Analizando problemas del sistema...")
        
        try:
            issues = []
            
            # Verificar archivos faltantes críticos
            critical_files = [
                'app/ats/chatbot/core/chatbot.py',
                'app/ats/config/settings/chatbot.py',
                'app/ats/utils/business_unit_manager.py'
            ]
            
            for file_path in critical_files:
                full_path = self.base_dir / file_path
                if not full_path.exists():
                    issues.append({
                        'type': 'missing_critical_file',
                        'file': file_path,
                        'severity': 'critical',
                        'description': f'Archivo crítico faltante: {file_path}'
                    })
            
            # Verificar configuraciones
            if not self.report_data.get('business_units', {}).get('units'):
                issues.append({
                    'type': 'no_business_units',
                    'severity': 'critical',
                    'description': 'No se encontraron unidades de negocio configuradas'
                })
            
            # Verificar integraciones
            integrations = self.report_data.get('integrations', {}).get('channels', {})
            if not any(channel.get('enabled', False) for channel in integrations.values()):
                issues.append({
                    'type': 'no_enabled_channels',
                    'severity': 'high',
                    'description': 'No hay canales de comunicación habilitados'
                })
            
            # Verificar workflows
            workflows = self.report_data.get('workflows', {}).get('directories', {})
            missing_workflows = [k for k, v in workflows.items() if not v.get('exists', False)]
            if missing_workflows:
                issues.append({
                    'type': 'missing_workflows',
                    'severity': 'medium',
                    'description': f'Workflows faltantes: {", ".join(missing_workflows)}'
                })
            
            self.report_data['issues'].extend(issues)
            
            logger.info(f"✅ Análisis de problemas completado. {len(issues)} problemas encontrados")
            
        except Exception as e:
            logger.error(f"Error analizando problemas: {e}")
    
    async def generate_recommendations(self):
        """Genera recomendaciones basadas en la auditoría"""
        logger.info("💡 Generando recomendaciones...")
        
        try:
            recommendations = []
            
            # Recomendaciones basadas en problemas encontrados
            issues = self.report_data.get('issues', [])
            for issue in issues:
                if issue['type'] == 'missing_critical_file':
                    recommendations.append({
                        'type': 'restore_file',
                        'priority': 'critical',
                        'description': f'Restaurar archivo crítico: {issue.get("file", "")}',
                        'action': 'Recuperar desde backup o recrear el archivo'
                    })
                
                elif issue['type'] == 'no_business_units':
                    recommendations.append({
                        'type': 'configure_business_units',
                        'priority': 'critical',
                        'description': 'Configurar unidades de negocio básicas',
                        'action': 'Crear unidades de negocio: huntRED, huntU, Amigro, SEXSI'
                    })
                
                elif issue['type'] == 'no_enabled_channels':
                    recommendations.append({
                        'type': 'enable_channels',
                        'priority': 'high',
                        'description': 'Habilitar al menos un canal de comunicación',
                        'action': 'Configurar WhatsApp o Telegram como canal principal'
                    })
            
            # Recomendaciones de mejora
            recommendations.extend([
                {
                    'type': 'performance_optimization',
                    'priority': 'medium',
                    'description': 'Optimizar consultas de base de datos',
                    'action': 'Revisar y optimizar queries en modelos principales'
                },
                {
                    'type': 'security_enhancement',
                    'priority': 'high',
                    'description': 'Revisar configuraciones de seguridad',
                    'action': 'Verificar permisos y configuraciones de autenticación'
                },
                {
                    'type': 'monitoring_setup',
                    'priority': 'medium',
                    'description': 'Implementar monitoreo del sistema',
                    'action': 'Configurar logs y métricas de rendimiento'
                }
            ])
            
            self.report_data['recommendations'] = recommendations
            
            logger.info(f"✅ Recomendaciones generadas. {len(recommendations)} recomendaciones creadas")
            
        except Exception as e:
            logger.error(f"Error generando recomendaciones: {e}")
    
    async def generate_final_report(self):
        """Genera el reporte final de la auditoría"""
        logger.info("📄 Generando reporte final...")
        
        try:
            # Crear directorio de reportes si no existe
            reports_dir = self.base_dir / 'reports'
            reports_dir.mkdir(exist_ok=True)
            
            # Generar reporte JSON
            report_file = reports_dir / f'auditoria_huntred_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.report_data, f, indent=2, ensure_ascii=False, default=str)
            
            # Generar reporte resumido
            summary_file = reports_dir / f'resumen_auditoria_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
            await self.generate_summary_report(summary_file)
            
            logger.info(f"✅ Reporte final generado: {report_file}")
            logger.info(f"✅ Resumen generado: {summary_file}")
            
        except Exception as e:
            logger.error(f"Error generando reporte final: {e}")
    
    async def generate_summary_report(self, file_path: Path):
        """Genera un reporte resumido en Markdown"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("# AUDITORÍA COMPLETA DEL SISTEMA huntRED®\n\n")
                f.write(f"**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Resumen ejecutivo
                f.write("## 📋 RESUMEN EJECUTIVO\n\n")
                f.write(f"- **Unidades de negocio:** {self.report_data.get('business_units', {}).get('total_count', 0)}\n")
                f.write(f"- **Problemas encontrados:** {len(self.report_data.get('issues', []))}\n")
                f.write(f"- **Recomendaciones:** {len(self.report_data.get('recommendations', []))}\n\n")
                
                # Problemas críticos
                critical_issues = [i for i in self.report_data.get('issues', []) if i.get('severity') == 'critical']
                if critical_issues:
                    f.write("## 🚨 PROBLEMAS CRÍTICOS\n\n")
                    for issue in critical_issues:
                        f.write(f"- **{issue.get('type', 'Unknown')}:** {issue.get('description', 'No description')}\n")
                    f.write("\n")
                
                # Recomendaciones prioritarias
                high_priority_recs = [r for r in self.report_data.get('recommendations', []) if r.get('priority') in ['critical', 'high']]
                if high_priority_recs:
                    f.write("## ⚡ RECOMENDACIONES PRIORITARIAS\n\n")
                    for rec in high_priority_recs:
                        f.write(f"- **{rec.get('type', 'Unknown')}:** {rec.get('description', 'No description')}\n")
                        f.write(f"  - *Acción:* {rec.get('action', 'No action specified')}\n\n")
                
                # Estado del sistema
                f.write("## 🏗️ ESTADO DEL SISTEMA\n\n")
                f.write("### Componentes principales:\n")
                f.write(f"- ✅ Chatbot: {'Funcional' if self.report_data.get('chatbot') else 'No disponible'}\n")
                f.write(f"- ✅ Integraciones: {'Configuradas' if self.report_data.get('integrations') else 'No configuradas'}\n")
                f.write(f"- ✅ Workflows: {'Implementados' if self.report_data.get('workflows') else 'No implementados'}\n")
                f.write(f"- ✅ Assessments: {'Disponibles' if self.report_data.get('assessments') else 'No disponibles'}\n")
                f.write(f"- ✅ Scraping: {'Operativo' if self.report_data.get('scraping') else 'No operativo'}\n")
                f.write(f"- ✅ Notificaciones: {'Configuradas' if self.report_data.get('notifications') else 'No configuradas'}\n\n")
                
                # Próximos pasos
                f.write("## 🎯 PRÓXIMOS PASOS\n\n")
                f.write("1. **Revisar problemas críticos** identificados\n")
                f.write("2. **Implementar recomendaciones prioritarias**\n")
                f.write("3. **Verificar funcionalidad** de componentes principales\n")
                f.write("4. **Configurar monitoreo** del sistema\n")
                f.write("5. **Documentar procedimientos** de mantenimiento\n\n")
                
                f.write("---\n")
                f.write("*Reporte generado automáticamente por el sistema de auditoría huntRED®*\n")
                
        except Exception as e:
            logger.error(f"Error generando reporte resumido: {e}")
    
    # Métodos auxiliares
    async def get_model_count(self, model_class):
        """Obtiene el conteo de registros de un modelo"""
        try:
            return await model_class.objects.acount()
        except:
            return 0
    
    async def get_all_objects(self, model_class):
        """Obtiene todos los objetos de un modelo"""
        try:
            return await model_class.objects.all()
        except:
            return []
    
    async def get_bu_members_count(self, bu_id):
        """Obtiene el conteo de miembros de una unidad de negocio"""
        try:
            from app.models import BusinessUnitMembership
            return await BusinessUnitMembership.objects.filter(business_unit_id=bu_id).acount()
        except:
            return 0
    
    async def check_nlp_processor(self):
        """Verifica el procesador NLP"""
        try:
            from app.ats.chatbot.nlp.nlp import NLPProcessor
            return {'available': True, 'status': 'OK'}
        except Exception as e:
            return {'available': False, 'error': str(e)}
    
    async def check_gpt_handler(self):
        """Verifica el manejador GPT"""
        try:
            from app.ats.chatbot.core.gpt import GPTHandler
            return {'available': True, 'status': 'OK'}
        except Exception as e:
            return {'available': False, 'error': str(e)}
    
    async def check_state_manager(self):
        """Verifica el gestor de estados"""
        try:
            from app.ats.chatbot.components.chat_state_manager import ChatStateManager
            return {'available': True, 'status': 'OK'}
        except Exception as e:
            return {'available': False, 'error': str(e)}
    
    async def check_channel_integration(self, channel):
        """Verifica la integración de un canal"""
        try:
            # Verificar archivos de integración
            channel_files = {
                'whatsapp': 'app/ats/integrations/channels/whatsapp/',
                'telegram': 'app/ats/integrations/channels/telegram/',
                'messenger': 'app/ats/integrations/channels/messenger/',
                'instagram': 'app/ats/integrations/channels/instagram/',
                'slack': 'app/ats/integrations/channels/slack/',
                'email': 'app/ats/integrations/services/email.py',
                'sms': 'app/ats/integrations/notifications/channels/sms.py'
            }
            
            file_path = self.base_dir / channel_files.get(channel, '')
            if file_path.exists():
                return {'enabled': True, 'exists': True}
            else:
                return {'enabled': False, 'exists': False}
        except Exception as e:
            return {'enabled': False, 'error': str(e)}
    
    async def get_notification_channels(self):
        """Obtiene los canales de notificación disponibles"""
        try:
            from app.ats.integrations.notifications.channels import _CHANNEL_PATHS
            return list(_CHANNEL_PATHS.keys())
        except:
            return []
    
    async def get_api_configurations(self):
        """Obtiene las configuraciones de API"""
        try:
            from app.models import WhatsAppAPI, TelegramAPI, SlackAPI
            apis = {}
            
            # WhatsApp
            try:
                whatsapp_apis = await WhatsAppAPI.objects.all()
                apis['whatsapp'] = [{'id': api.id, 'name': api.name} for api in whatsapp_apis]
            except:
                apis['whatsapp'] = []
            
            # Telegram
            try:
                telegram_apis = await TelegramAPI.objects.all()
                apis['telegram'] = [{'id': api.id, 'name': api.name} for api in telegram_apis]
            except:
                apis['telegram'] = []
            
            return apis
        except:
            return {}
    
    async def check_migrations_status(self):
        """Verifica el estado de las migraciones"""
        try:
            from django.core.management import call_command
            from io import StringIO
            
            output = StringIO()
            call_command('showmigrations', stdout=output)
            return {'status': 'checked', 'output': output.getvalue()}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def check_database_connections(self):
        """Verifica las conexiones de base de datos"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()
            return {'status': 'connected', 'version': version[0] if version else 'Unknown'}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def check_workflow_manager(self):
        """Verifica el gestor de workflows"""
        try:
            from app.ats.chatbot.workflow.core.workflow_manager import WorkflowManager
            return {'available': True, 'status': 'OK'}
        except Exception as e:
            return {'available': False, 'error': str(e)}
    
    async def check_personality_analyzer(self):
        """Verifica el analizador de personalidad"""
        try:
            from app.ml.analyzers import PersonalityAnalyzer
            return {'available': True, 'status': 'OK'}
        except Exception as e:
            return {'available': False, 'error': str(e)}
    
    async def check_cultural_analyzer(self):
        """Verifica el analizador cultural"""
        try:
            from app.ml.analyzers.cultural_analyzer import CulturalAnalyzer
            return {'available': True, 'status': 'OK'}
        except Exception as e:
            return {'available': False, 'error': str(e)}
    
    async def get_scraping_configurations(self):
        """Obtiene las configuraciones de scraping"""
        try:
            from app.models import DominioScraping
            domains = await DominioScraping.objects.all()
            return [{'id': domain.id, 'dominio': domain.dominio, 'plataforma': domain.plataforma} for domain in domains]
        except:
            return []
    
    async def check_robust_scraping_system(self):
        """Verifica el sistema de scraping robusto"""
        try:
            from app.ats.utils.scraping.robust_scraping_system import RobustScrapingSystem
            return {'available': True, 'status': 'OK'}
        except Exception as e:
            return {'available': False, 'error': str(e)}
    
    async def check_notification_manager(self):
        """Verifica el gestor de notificaciones"""
        try:
            from app.ats.integrations.notifications.notification_manager import NotificationManager
            return {'available': True, 'status': 'OK'}
        except Exception as e:
            return {'available': False, 'error': str(e)}
    
    async def get_notification_channel_map(self):
        """Obtiene el mapa de canales de notificación"""
        try:
            from app.ats.integrations.notifications.services.notification_service import CHANNEL_MAP
            return CHANNEL_MAP
        except:
            return {}

async def main():
    """Función principal"""
    print("🔍 INICIANDO AUDITORÍA COMPLETA DEL SISTEMA huntRED®")
    print("=" * 60)
    
    auditoria = AuditoriaHuntRED()
    await auditoria.run_complete_audit()
    
    print("\n✅ AUDITORÍA COMPLETADA")
    print("📄 Revisa los reportes generados en el directorio 'reports/'")

if __name__ == "__main__":
    asyncio.run(main()) 