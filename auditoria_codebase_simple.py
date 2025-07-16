#!/usr/bin/env python3
"""
AUDITORÍA SIMPLE DEL CODEBASE huntRED®
======================================

Este script realiza una auditoría del codebase sin depender completamente
de Django, enfocándose en el análisis de archivos y estructura.

Autor: Asistente AI
Fecha: 2025
Versión: 1.0.0
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import ast
import re

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auditoria_codebase.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AuditoriaCodebase:
    """
    Clase para realizar auditoría del codebase huntRED®
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
        
    def run_complete_audit(self):
        """Ejecuta la auditoría completa del codebase"""
        logger.info("🚀 Iniciando auditoría del codebase huntRED®")
        
        try:
            # 1. Información del sistema
            self.audit_system_info()
            
            # 2. Arquitectura del proyecto
            self.audit_architecture()
            
            # 3. Unidades de negocio
            self.audit_business_units()
            
            # 4. Sistema de chatbot
            self.audit_chatbot_system()
            
            # 5. Integraciones
            self.audit_integrations()
            
            # 6. Modelos de datos
            self.audit_models()
            
            # 7. Workflows
            self.audit_workflows()
            
            # 8. Assessments
            self.audit_assessments()
            
            # 9. Sistema de scraping
            self.audit_scraping_system()
            
            # 10. Sistema de notificaciones
            self.audit_notifications()
            
            # 11. Análisis de problemas
            self.analyze_issues()
            
            # 12. Generar recomendaciones
            self.generate_recommendations()
            
            # 13. Generar reporte final
            self.generate_final_report()
            
            logger.info("✅ Auditoría del codebase finalizada exitosamente")
            
        except Exception as e:
            logger.error(f"❌ Error en la auditoría: {str(e)}", exc_info=True)
            self.report_data['issues'].append({
                'type': 'audit_error',
                'message': str(e),
                'severity': 'critical'
            })
    
    def audit_system_info(self):
        """Audita la información básica del sistema"""
        logger.info("📋 Auditando información del sistema...")
        
        try:
            # Información del sistema
            self.report_data['system_info'] = {
                'python_version': sys.version,
                'base_dir': str(self.base_dir),
                'total_files': len(list(self.base_dir.rglob('*.py'))),
                'total_size_mb': sum(f.stat().st_size for f in self.base_dir.rglob('*') if f.is_file()) / (1024*1024)
            }
            
            # Verificar archivos de configuración
            config_files = [
                'requirements.txt',
                'manage.py',
                'wsgi.py',
                'asgi.py',
                'package.json',
                'tailwind.config.js'
            ]
            
            config_info = {}
            for config_file in config_files:
                file_path = self.base_dir / config_file
                if file_path.exists():
                    config_info[config_file] = {
                        'exists': True,
                        'size_kb': file_path.stat().st_size / 1024
                    }
                else:
                    config_info[config_file] = {'exists': False}
            
            self.report_data['system_info']['config_files'] = config_info
            
            logger.info("✅ Información del sistema auditada")
            
        except Exception as e:
            logger.error(f"Error auditando información del sistema: {e}")
            self.report_data['issues'].append({
                'type': 'system_info_error',
                'message': str(e),
                'severity': 'high'
            })
    
    def audit_architecture(self):
        """Audita la arquitectura del proyecto"""
        logger.info("🏗️ Auditando arquitectura del proyecto...")
        
        try:
            # Estructura de directorios principales
            directories = [
                'app/',
                'app/ats/',
                'app/ats/chatbot/',
                'app/ats/integrations/',
                'app/ats/utils/',
                'app/ml/',
                'app/models/',
                'templates/',
                'static/',
                'media/',
                'docs/',
                'ai_huntred/',
                'ai_huntred/settings/',
                'config/'
            ]
            
            architecture_info = {}
            for dir_path in directories:
                full_path = self.base_dir / dir_path
                if full_path.exists():
                    py_files = list(full_path.rglob('*.py'))
                    architecture_info[dir_path] = {
                        'exists': True,
                        'file_count': len(py_files),
                        'size_mb': sum(f.stat().st_size for f in full_path.rglob('*') if f.is_file()) / (1024*1024),
                        'main_files': [f.name for f in py_files[:10]]  # Primeros 10 archivos
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
                    'app.ml',
                    'app.models',
                    'ai_huntred'
                ]
            }
            
            logger.info("✅ Arquitectura auditada")
            
        except Exception as e:
            logger.error(f"Error auditando arquitectura: {e}")
            self.report_data['issues'].append({
                'type': 'architecture_error',
                'message': str(e),
                'severity': 'medium'
            })
    
    def audit_business_units(self):
        """Audita las unidades de negocio"""
        logger.info("🏢 Auditando unidades de negocio...")
        
        try:
            # Buscar archivos relacionados con unidades de negocio
            bu_files = [
                'app/ats/utils/business_unit_manager.py',
                'app/ats/config/settings.py',
                'app/ats/config/settings/chatbot.py'
            ]
            
            bu_info = {}
            for bu_file in bu_files:
                file_path = self.base_dir / bu_file
                if file_path.exists():
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    bu_info[bu_file] = {
                        'exists': True,
                        'size_kb': file_path.stat().st_size / 1024,
                        'business_units_found': self.extract_business_units(content)
                    }
                else:
                    bu_info[bu_file] = {'exists': False}
            
            # Buscar configuraciones de BU en el código
            bu_configs = self.find_business_unit_configs()
            
            self.report_data['business_units'] = {
                'files': bu_info,
                'configurations': bu_configs,
                'units_found': ['huntRED', 'huntU', 'Amigro', 'SEXSI', 'MilkyLeak']
            }
            
            logger.info("✅ Unidades de negocio auditadas")
            
        except Exception as e:
            logger.error(f"Error auditando unidades de negocio: {e}")
            self.report_data['issues'].append({
                'type': 'business_units_error',
                'message': str(e),
                'severity': 'high'
            })
    
    def audit_chatbot_system(self):
        """Audita el sistema de chatbot"""
        logger.info("🤖 Auditando sistema de chatbot...")
        
        try:
            # Archivos principales del chatbot
            chatbot_files = [
                'app/ats/chatbot/core/chatbot.py',
                'app/ats/chatbot/components/chat_state_manager.py',
                'app/ats/chatbot/components/context_manager.py',
                'app/ats/chatbot/components/response_generator.py',
                'app/ats/chatbot/nlp/nlp.py',
                'app/ats/chatbot/core/gpt.py',
                'app/ats/chatbot/flow/conversational_flow.py'
            ]
            
            chatbot_info = {}
            for chatbot_file in chatbot_files:
                file_path = self.base_dir / chatbot_file
                if file_path.exists():
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    chatbot_info[chatbot_file] = {
                        'exists': True,
                        'size_kb': file_path.stat().st_size / 1024,
                        'classes_found': self.extract_classes(content),
                        'functions_found': self.extract_functions(content)
                    }
                else:
                    chatbot_info[chatbot_file] = {'exists': False}
            
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
                        'size_kb': file_path.stat().st_size / 1024
                    }
                else:
                    workflows_info[workflow_file] = {'exists': False}
            
            self.report_data['chatbot'] = {
                'core_files': chatbot_info,
                'workflows': workflows_info,
                'nlp_processor': self.check_file_exists('app/ats/chatbot/nlp/nlp.py'),
                'gpt_handler': self.check_file_exists('app/ats/chatbot/core/gpt.py'),
                'state_manager': self.check_file_exists('app/ats/chatbot/components/chat_state_manager.py')
            }
            
            logger.info("✅ Sistema de chatbot auditado")
            
        except Exception as e:
            logger.error(f"Error auditando sistema de chatbot: {e}")
            self.report_data['issues'].append({
                'type': 'chatbot_error',
                'message': str(e),
                'severity': 'high'
            })
    
    def audit_integrations(self):
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
                channels_info[channel] = self.check_channel_integration(channel)
            
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
                'notification_channels': self.get_notification_channels(),
                'api_configurations': self.get_api_configurations()
            }
            
            logger.info("✅ Integraciones auditadas")
            
        except Exception as e:
            logger.error(f"Error auditando integraciones: {e}")
            self.report_data['issues'].append({
                'type': 'integrations_error',
                'message': str(e),
                'severity': 'medium'
            })
    
    def audit_models(self):
        """Audita los modelos de datos"""
        logger.info("📊 Auditando modelos de datos...")
        
        try:
            # Archivo principal de modelos
            models_file = self.base_dir / 'app/models.py'
            if models_file.exists():
                content = models_file.read_text(encoding='utf-8', errors='ignore')
                models_info = {
                    'exists': True,
                    'size_kb': models_file.stat().st_size / 1024,
                    'classes_found': self.extract_model_classes(content),
                    'total_lines': len(content.split('\n'))
                }
            else:
                models_info = {'exists': False}
            
            # Modelos adicionales
            additional_models = [
                'app/models/corporate.py',
                'app/models/university.py',
                'app/models/signature_models.py'
            ]
            
            additional_models_info = {}
            for model_file in additional_models:
                file_path = self.base_dir / model_file
                if file_path.exists():
                    additional_models_info[model_file] = {
                        'exists': True,
                        'size_kb': file_path.stat().st_size / 1024
                    }
                else:
                    additional_models_info[model_file] = {'exists': False}
            
            self.report_data['models'] = {
                'main_models': models_info,
                'additional_models': additional_models_info,
                'model_classes_found': self.extract_model_classes_from_file(models_file) if models_file.exists() else []
            }
            
            logger.info("✅ Modelos de datos auditados")
            
        except Exception as e:
            logger.error(f"Error auditando modelos: {e}")
            self.report_data['issues'].append({
                'type': 'models_error',
                'message': str(e),
                'severity': 'high'
            })
    
    def audit_workflows(self):
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
                'specific_workflows': specific_workflows_info
            }
            
            logger.info("✅ Workflows auditados")
            
        except Exception as e:
            logger.error(f"Error auditando workflows: {e}")
            self.report_data['issues'].append({
                'type': 'workflows_error',
                'message': str(e),
                'severity': 'medium'
            })
    
    def audit_assessments(self):
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
                'configurations': configs_info
            }
            
            logger.info("✅ Sistema de assessments auditado")
            
        except Exception as e:
            logger.error(f"Error auditando assessments: {e}")
            self.report_data['issues'].append({
                'type': 'assessments_error',
                'message': str(e),
                'severity': 'medium'
            })
    
    def audit_scraping_system(self):
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
            
            self.report_data['scraping'] = {
                'files': scraping_info,
                'platforms_supported': ['linkedin', 'workday', 'indeed', 'glassdoor']
            }
            
            logger.info("✅ Sistema de scraping auditado")
            
        except Exception as e:
            logger.error(f"Error auditando sistema de scraping: {e}")
            self.report_data['issues'].append({
                'type': 'scraping_error',
                'message': str(e),
                'severity': 'medium'
            })
    
    def audit_notifications(self):
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
                'services': services_info
            }
            
            logger.info("✅ Sistema de notificaciones auditado")
            
        except Exception as e:
            logger.error(f"Error auditando notificaciones: {e}")
            self.report_data['issues'].append({
                'type': 'notifications_error',
                'message': str(e),
                'severity': 'medium'
            })
    
    def analyze_issues(self):
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
            if not self.report_data.get('business_units', {}).get('configurations'):
                issues.append({
                    'type': 'no_business_units',
                    'severity': 'critical',
                    'description': 'No se encontraron configuraciones de unidades de negocio'
                })
            
            # Verificar integraciones
            integrations = self.report_data.get('integrations', {}).get('channels', {})
            if not any(channel.get('exists', False) for channel in integrations.values()):
                issues.append({
                    'type': 'no_enabled_channels',
                    'severity': 'high',
                    'description': 'No hay canales de comunicación configurados'
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
    
    def generate_recommendations(self):
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
    
    def generate_final_report(self):
        """Genera el reporte final de la auditoría"""
        logger.info("📄 Generando reporte final...")
        
        try:
            # Crear directorio de reportes si no existe
            reports_dir = self.base_dir / 'reports'
            reports_dir.mkdir(exist_ok=True)
            
            # Generar reporte JSON
            report_file = reports_dir / f'auditoria_codebase_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.report_data, f, indent=2, ensure_ascii=False, default=str)
            
            # Generar reporte resumido
            summary_file = reports_dir / f'resumen_auditoria_codebase_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
            self.generate_summary_report(summary_file)
            
            logger.info(f"✅ Reporte final generado: {report_file}")
            logger.info(f"✅ Resumen generado: {summary_file}")
            
        except Exception as e:
            logger.error(f"Error generando reporte final: {e}")
    
    def generate_summary_report(self, file_path: Path):
        """Genera un reporte resumido en Markdown"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("# AUDITORÍA DEL CODEBASE huntRED®\n\n")
                f.write(f"**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Resumen ejecutivo
                f.write("## 📋 RESUMEN EJECUTIVO\n\n")
                f.write(f"- **Archivos Python totales:** {self.report_data.get('system_info', {}).get('total_files', 0)}\n")
                f.write(f"- **Tamaño total del proyecto:** {self.report_data.get('system_info', {}).get('total_size_mb', 0):.2f} MB\n")
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
                f.write(f"- ✅ Chatbot: {'Funcional' if self.report_data.get('chatbot', {}).get('core_files') else 'No disponible'}\n")
                f.write(f"- ✅ Integraciones: {'Configuradas' if self.report_data.get('integrations', {}).get('services') else 'No configuradas'}\n")
                f.write(f"- ✅ Workflows: {'Implementados' if self.report_data.get('workflows', {}).get('directories') else 'No implementados'}\n")
                f.write(f"- ✅ Assessments: {'Disponibles' if self.report_data.get('assessments', {}).get('types') else 'No disponibles'}\n")
                f.write(f"- ✅ Scraping: {'Operativo' if self.report_data.get('scraping', {}).get('files') else 'No operativo'}\n")
                f.write(f"- ✅ Notificaciones: {'Configuradas' if self.report_data.get('notifications', {}).get('services') else 'No configuradas'}\n\n")
                
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
    def extract_business_units(self, content: str) -> List[str]:
        """Extrae unidades de negocio del contenido"""
        bu_patterns = [
            r"'huntRED'",
            r"'huntU'",
            r"'Amigro'",
            r"'SEXSI'",
            r"'MilkyLeak'"
        ]
        found_bus = []
        for pattern in bu_patterns:
            if re.search(pattern, content):
                found_bus.append(pattern.strip("'"))
        return found_bus
    
    def find_business_unit_configs(self) -> Dict:
        """Encuentra configuraciones de unidades de negocio"""
        configs = {}
        bu_manager_file = self.base_dir / 'app/ats/utils/business_unit_manager.py'
        if bu_manager_file.exists():
            content = bu_manager_file.read_text(encoding='utf-8', errors='ignore')
            # Buscar BU_CONFIGS
            bu_config_match = re.search(r'BU_CONFIGS\s*=\s*\{([^}]+)\}', content, re.DOTALL)
            if bu_config_match:
                configs['BU_CONFIGS'] = 'Found'
        return configs
    
    def extract_classes(self, content: str) -> List[str]:
        """Extrae nombres de clases del contenido"""
        class_pattern = r'class\s+(\w+)'
        return re.findall(class_pattern, content)
    
    def extract_functions(self, content: str) -> List[str]:
        """Extrae nombres de funciones del contenido"""
        func_pattern = r'def\s+(\w+)'
        return re.findall(func_pattern, content)
    
    def check_file_exists(self, file_path: str) -> Dict:
        """Verifica si un archivo existe"""
        full_path = self.base_dir / file_path
        if full_path.exists():
            return {'exists': True, 'size_kb': full_path.stat().st_size / 1024}
        else:
            return {'exists': False}
    
    def check_channel_integration(self, channel: str) -> Dict:
        """Verifica la integración de un canal"""
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
    
    def get_notification_channels(self) -> List[str]:
        """Obtiene los canales de notificación disponibles"""
        channels = []
        channels_dir = self.base_dir / 'app/ats/integrations/notifications/channels/'
        if channels_dir.exists():
            for file in channels_dir.glob('*.py'):
                if file.name != '__init__.py':
                    channels.append(file.stem)
        return channels
    
    def get_api_configurations(self) -> Dict:
        """Obtiene las configuraciones de API"""
        apis = {}
        # Buscar archivos de configuración de API
        api_files = [
            'app/ats/integrations/channels/whatsapp/services.py',
            'app/ats/integrations/channels/telegram/telegram.py'
        ]
        
        for api_file in api_files:
            file_path = self.base_dir / api_file
            if file_path.exists():
                apis[api_file] = {'exists': True}
            else:
                apis[api_file] = {'exists': False}
        
        return apis
    
    def extract_model_classes(self, content: str) -> List[str]:
        """Extrae clases de modelo del contenido"""
        model_pattern = r'class\s+(\w+)\s*\(models\.Model\)'
        return re.findall(model_pattern, content)
    
    def extract_model_classes_from_file(self, file_path: Path) -> List[str]:
        """Extrae clases de modelo de un archivo"""
        if not file_path.exists():
            return []
        
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            return self.extract_model_classes(content)
        except:
            return []

def main():
    """Función principal"""
    print("🔍 INICIANDO AUDITORÍA DEL CODEBASE huntRED®")
    print("=" * 60)
    
    auditoria = AuditoriaCodebase()
    auditoria.run_complete_audit()
    
    print("\n✅ AUDITORÍA COMPLETADA")
    print("📄 Revisa los reportes generados en el directorio 'reports/'")

if __name__ == "__main__":
    main() 