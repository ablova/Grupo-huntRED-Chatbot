#!/usr/bin/env python3
"""
Script de Configuración Integral del Sistema ATS huntRED®

Este script permite configurar:
1. Canales de comunicación (WhatsApp, Telegram, Messenger, Instagram, Email)
2. Unidades de Negocio (huntRED® Executive, huntRED®, huntU®, Amigro)
3. Workflows específicos por BU
4. Assessments y evaluaciones
5. Configuración de scraping
6. Integraciones y APIs
7. Configuración de chatbots

Autor: huntRED® Group
Versión: 2.0.0
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('configuracion_ats.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ATSConfigurator:
    """Configurador principal del sistema ATS."""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.config_dir = self.base_dir / 'app' / 'ats' / 'config'
        self.workflow_dir = self.base_dir / 'app' / 'ats' / 'chatbot' / 'workflow'
        
        # Configuraciones por defecto
        self.default_configs = {
            'business_units': {
                'huntRED_executive': {
                    'name': 'huntRED® Executive',
                    'description': 'Reclutamiento para posiciones C-level y miembros de consejo',
                    'commission_percentage': 25,
                    'salary_range': {'min': 100000, 'max': None},
                    'chatbot_greeting': 'Bienvenido a huntRED® Executive. ¿En qué puedo asistirle hoy?',
                    'workflow_states': ['INICIO', 'IDENTIFICACION', 'PERFIL', 'OPORTUNIDAD', 'ENTREVISTA', 'PROPUESTA', 'CERRADO'],
                    'assessment_types': ['executive_personality', 'leadership_style', 'board_experience', 'strategic_thinking'],
                    'channels': ['email', 'whatsapp', 'linkedin'],
                    'scraping_enabled': True,
                    'max_candidates_per_month': 50,
                    'max_vacancies_per_month': 20
                },
                'huntRED': {
                    'name': 'huntRED®',
                    'description': 'Reclutamiento especializado para posiciones gerenciales',
                    'commission_percentage': 20,
                    'salary_range': {'min': 45000, 'max': 120000},
                    'chatbot_greeting': '¡Hola! Soy el asistente de huntRED®. ¿En qué puedo ayudarte hoy?',
                    'workflow_states': ['INICIO', 'IDENTIFICACION', 'PERFIL', 'OPORTUNIDAD', 'ENTREVISTA', 'PROPUESTA', 'CERRADO'],
                    'assessment_types': ['personality', 'technical_skills', 'cultural_fit', 'leadership_potential'],
                    'channels': ['email', 'whatsapp', 'telegram'],
                    'scraping_enabled': True,
                    'max_candidates_per_month': 200,
                    'max_vacancies_per_month': 100
                },
                'huntU': {
                    'name': 'huntU®',
                    'description': 'Reclutamiento para talento universitario y puestos de entrada',
                    'commission_percentage': 15,
                    'salary_range': {'min': 20000, 'max': 45000},
                    'chatbot_greeting': '¡Hola! Soy el asistente de huntU®. ¿Cómo puedo ayudarte?',
                    'workflow_states': ['INICIO', 'IDENTIFICACION', 'PERFIL', 'OPORTUNIDAD', 'ENTREVISTA', 'PROPUESTA', 'CERRADO'],
                    'assessment_types': ['personality', 'potential_assessment', 'cultural_fit', 'learning_agility'],
                    'channels': ['email', 'whatsapp', 'instagram'],
                    'scraping_enabled': True,
                    'max_candidates_per_month': 500,
                    'max_vacancies_per_month': 200
                },
                'amigro': {
                    'name': 'Amigro',
                    'description': 'Oportunidades laborales para migrantes y puestos operativos',
                    'commission_percentage': 10,
                    'salary_range': {'min': 10000, 'max': 35000},
                    'chatbot_greeting': '¡Hola! Soy el asistente de Amigro. ¿Buscas oportunidades laborales?',
                    'workflow_states': ['INICIO', 'IDENTIFICACION', 'PERFIL', 'OPORTUNIDAD', 'ENTREVISTA', 'PROPUESTA', 'CERRADO'],
                    'assessment_types': ['basic_skills', 'language_assessment', 'cultural_adaptation', 'work_attitude'],
                    'channels': ['whatsapp', 'telegram', 'email'],
                    'scraping_enabled': True,
                    'max_candidates_per_month': 1000,
                    'max_vacancies_per_month': 500
                }
            },
            'channels': {
                'whatsapp': {
                    'enabled': True,
                    'api_provider': 'messagebird',  # o 'twilio', 'meta'
                    'webhook_url': '',
                    'api_token': '',
                    'phone_number': '',
                    'retry_delay': 30,
                    'max_retries': 3,
                    'templates': {
                        'welcome': '¡Hola! Soy AURA, tu asistente virtual de {business_unit}. ¿En qué puedo ayudarte?',
                        'profile_complete': '¡Perfecto! Tu perfil está completo. Te contactaremos pronto.',
                        'assessment_ready': 'Tu evaluación está lista. ¿Quieres comenzar?',
                        'interview_scheduled': 'Tu entrevista ha sido programada para {date} a las {time}.'
                    }
                },
                'telegram': {
                    'enabled': True,
                    'bot_token': '',
                    'webhook_url': '',
                    'retry_delay': 30,
                    'max_retries': 3,
                    'templates': {
                        'welcome': '¡Hola! Soy AURA, tu asistente virtual de {business_unit}. ¿En qué puedo ayudarte?',
                        'profile_complete': '¡Perfecto! Tu perfil está completo. Te contactaremos pronto.',
                        'assessment_ready': 'Tu evaluación está lista. ¿Quieres comenzar?',
                        'interview_scheduled': 'Tu entrevista ha sido programada para {date} a las {time}.'
                    }
                },
                'messenger': {
                    'enabled': True,
                    'page_token': '',
                    'verify_token': '',
                    'retry_delay': 30,
                    'max_retries': 3,
                    'templates': {
                        'welcome': '¡Hola! Soy AURA, tu asistente virtual de {business_unit}. ¿En qué puedo ayudarte?',
                        'profile_complete': '¡Perfecto! Tu perfil está completo. Te contactaremos pronto.',
                        'assessment_ready': 'Tu evaluación está lista. ¿Quieres comenzar?',
                        'interview_scheduled': 'Tu entrevista ha sido programada para {date} a las {time}.'
                    }
                },
                'instagram': {
                    'enabled': True,
                    'access_token': '',
                    'webhook_url': '',
                    'retry_delay': 30,
                    'max_retries': 3,
                    'templates': {
                        'welcome': '¡Hola! Soy AURA, tu asistente virtual de {business_unit}. ¿En qué puedo ayudarte?',
                        'profile_complete': '¡Perfecto! Tu perfil está completo. Te contactaremos pronto.',
                        'assessment_ready': 'Tu evaluación está lista. ¿Quieres comenzar?',
                        'interview_scheduled': 'Tu entrevista ha sido programada para {date} a las {time}.'
                    }
                },
                'email': {
                    'enabled': True,
                    'smtp_host': '',
                    'smtp_port': 587,
                    'smtp_username': '',
                    'smtp_password': '',
                    'smtp_use_tls': True,
                    'from_email': '',
                    'retry_delay': 10,
                    'max_retries': 3,
                    'templates': {
                        'welcome': '¡Bienvenido a {business_unit}!',
                        'profile_complete': 'Tu perfil está completo. Te contactaremos pronto.',
                        'assessment_ready': 'Tu evaluación está lista.',
                        'interview_scheduled': 'Tu entrevista ha sido programada.'
                    }
                }
            },
            'assessments': {
                'personality': {
                    'enabled': True,
                    'questions_count': 50,
                    'time_limit_minutes': 30,
                    'passing_score': 70,
                    'business_units': ['huntRED', 'huntU', 'amigro']
                },
                'executive_personality': {
                    'enabled': True,
                    'questions_count': 80,
                    'time_limit_minutes': 45,
                    'passing_score': 80,
                    'business_units': ['huntRED_executive']
                },
                'technical_skills': {
                    'enabled': True,
                    'questions_count': 40,
                    'time_limit_minutes': 60,
                    'passing_score': 75,
                    'business_units': ['huntRED', 'huntU']
                },
                'cultural_fit': {
                    'enabled': True,
                    'questions_count': 30,
                    'time_limit_minutes': 20,
                    'passing_score': 70,
                    'business_units': ['huntRED', 'huntU', 'amigro']
                },
                'leadership_style': {
                    'enabled': True,
                    'questions_count': 60,
                    'time_limit_minutes': 35,
                    'passing_score': 75,
                    'business_units': ['huntRED_executive', 'huntRED']
                },
                'board_experience': {
                    'enabled': True,
                    'questions_count': 40,
                    'time_limit_minutes': 25,
                    'passing_score': 80,
                    'business_units': ['huntRED_executive']
                },
                'strategic_thinking': {
                    'enabled': True,
                    'questions_count': 35,
                    'time_limit_minutes': 30,
                    'passing_score': 80,
                    'business_units': ['huntRED_executive']
                },
                'potential_assessment': {
                    'enabled': True,
                    'questions_count': 45,
                    'time_limit_minutes': 25,
                    'passing_score': 70,
                    'business_units': ['huntU']
                },
                'learning_agility': {
                    'enabled': True,
                    'questions_count': 35,
                    'time_limit_minutes': 20,
                    'passing_score': 70,
                    'business_units': ['huntU']
                },
                'basic_skills': {
                    'enabled': True,
                    'questions_count': 25,
                    'time_limit_minutes': 15,
                    'passing_score': 60,
                    'business_units': ['amigro']
                },
                'language_assessment': {
                    'enabled': True,
                    'questions_count': 30,
                    'time_limit_minutes': 20,
                    'passing_score': 65,
                    'business_units': ['amigro']
                },
                'cultural_adaptation': {
                    'enabled': True,
                    'questions_count': 20,
                    'time_limit_minutes': 15,
                    'passing_score': 60,
                    'business_units': ['amigro']
                },
                'work_attitude': {
                    'enabled': True,
                    'questions_count': 25,
                    'time_limit_minutes': 15,
                    'passing_score': 65,
                    'business_units': ['amigro']
                }
            },
            'scraping': {
                'enabled': True,
                'max_concurrent_requests': 10,
                'request_delay': 1.0,
                'timeout': 30,
                'max_retries': 3,
                'user_agent_rotation': True,
                'proxy_rotation': True,
                'anti_bot_detection': True,
                'domains': {
                    'linkedin': {
                        'enabled': True,
                        'max_retries': 5,
                        'delay_between_requests': 3.0,
                        'max_concurrent': 1
                    },
                    'workday': {
                        'enabled': True,
                        'max_retries': 3,
                        'delay_between_requests': 2.0,
                        'max_concurrent': 2
                    },
                    'indeed': {
                        'enabled': True,
                        'max_retries': 3,
                        'delay_between_requests': 2.0,
                        'max_concurrent': 3
                    },
                    'computrabajo': {
                        'enabled': True,
                        'max_retries': 3,
                        'delay_between_requests': 1.5,
                        'max_concurrent': 5
                    }
                }
            },
            'integrations': {
                'openai': {
                    'enabled': True,
                    'api_key': '',
                    'model': 'gpt-3.5-turbo',
                    'temperature': 0.7,
                    'max_tokens': 150
                },
                'stripe': {
                    'enabled': True,
                    'publishable_key': '',
                    'secret_key': '',
                    'webhook_secret': ''
                },
                'blacktrust': {
                    'enabled': True,
                    'api_key': '',
                    'api_url': 'https://api.blacktrust.com'
                },
                'incode': {
                    'enabled': True,
                    'api_key': '',
                    'api_url': 'https://api.incode.com'
                }
            }
        }
    
    def run_configuration(self):
        """Ejecuta el proceso completo de configuración."""
        logger.info("🚀 Iniciando configuración del sistema ATS huntRED®")
        
        try:
            # 1. Configurar Business Units
            self.configure_business_units()
            
            # 2. Configurar Canales
            self.configure_channels()
            
            # 3. Configurar Assessments
            self.configure_assessments()
            
            # 4. Configurar Scraping
            self.configure_scraping()
            
            # 5. Configurar Integraciones
            self.configure_integrations()
            
            # 6. Generar archivos de configuración
            self.generate_config_files()
            
            # 7. Validar configuración
            self.validate_configuration()
            
            logger.info("✅ Configuración completada exitosamente")
            
        except Exception as e:
            logger.error(f"❌ Error durante la configuración: {str(e)}")
            raise
    
    def configure_business_units(self):
        """Configura las unidades de negocio."""
        logger.info("📋 Configurando Unidades de Negocio...")
        
        for bu_code, config in self.default_configs['business_units'].items():
            logger.info(f"  Configurando {config['name']}...")
            
            # Aquí se configurarían los modelos de BusinessUnit
            # Por ahora solo mostramos la configuración
            print(f"\n🔧 {config['name']} ({bu_code})")
            print(f"   Descripción: {config['description']}")
            print(f"   Comisión: {config['commission_percentage']}%")
            print(f"   Rango salarial: ${config['salary_range']['min']:,} - {config['salary_range']['max'] or 'Sin límite'}")
            print(f"   Canales: {', '.join(config['channels'])}")
            print(f"   Scraping: {'Habilitado' if config['scraping_enabled'] else 'Deshabilitado'}")
            print(f"   Máximo candidatos/mes: {config['max_candidates_per_month']}")
            print(f"   Máximo vacantes/mes: {config['max_vacancies_per_month']}")
    
    def configure_channels(self):
        """Configura los canales de comunicación."""
        logger.info("📡 Configurando Canales de Comunicación...")
        
        for channel, config in self.default_configs['channels'].items():
            logger.info(f"  Configurando {channel.upper()}...")
            
            print(f"\n📱 {channel.upper()}")
            print(f"   Estado: {'Habilitado' if config['enabled'] else 'Deshabilitado'}")
            
            if config['enabled']:
                if channel == 'whatsapp':
                    print(f"   Proveedor: {config['api_provider']}")
                    print(f"   Número: {config['phone_number'] or 'No configurado'}")
                elif channel == 'telegram':
                    print(f"   Bot Token: {'Configurado' if config['bot_token'] else 'No configurado'}")
                elif channel == 'messenger':
                    print(f"   Page Token: {'Configurado' if config['page_token'] else 'No configurado'}")
                elif channel == 'instagram':
                    print(f"   Access Token: {'Configurado' if config['access_token'] else 'No configurado'}")
                elif channel == 'email':
                    print(f"   SMTP Host: {config['smtp_host'] or 'No configurado'}")
                    print(f"   From Email: {config['from_email'] or 'No configurado'}")
                
                print(f"   Reintentos: {config['max_retries']}")
                print(f"   Delay: {config['retry_delay']}s")
    
    def configure_assessments(self):
        """Configura los assessments."""
        logger.info("📊 Configurando Assessments...")
        
        for assessment, config in self.default_configs['assessments'].items():
            logger.info(f"  Configurando {assessment}...")
            
            print(f"\n📝 {assessment.replace('_', ' ').title()}")
            print(f"   Estado: {'Habilitado' if config['enabled'] else 'Deshabilitado'}")
            if config['enabled']:
                print(f"   Preguntas: {config['questions_count']}")
                print(f"   Tiempo límite: {config['time_limit_minutes']} minutos")
                print(f"   Puntaje mínimo: {config['passing_score']}%")
                print(f"   Unidades de Negocio: {', '.join(config['business_units'])}")
    
    def configure_scraping(self):
        """Configura el sistema de scraping."""
        logger.info("🔍 Configurando Sistema de Scraping...")
        
        scraping_config = self.default_configs['scraping']
        print(f"\n🌐 Scraping General")
        print(f"   Estado: {'Habilitado' if scraping_config['enabled'] else 'Deshabilitado'}")
        if scraping_config['enabled']:
            print(f"   Requests concurrentes: {scraping_config['max_concurrent_requests']}")
            print(f"   Delay entre requests: {scraping_config['request_delay']}s")
            print(f"   Timeout: {scraping_config['timeout']}s")
            print(f"   Máximo reintentos: {scraping_config['max_retries']}")
            print(f"   Rotación User-Agent: {'Sí' if scraping_config['user_agent_rotation'] else 'No'}")
            print(f"   Rotación Proxy: {'Sí' if scraping_config['proxy_rotation'] else 'No'}")
            print(f"   Anti-bot: {'Sí' if scraping_config['anti_bot_detection'] else 'No'}")
            
            print(f"\n📋 Dominios Configurados:")
            for domain, domain_config in scraping_config['domains'].items():
                print(f"   {domain.upper()}: {'Habilitado' if domain_config['enabled'] else 'Deshabilitado'}")
                if domain_config['enabled']:
                    print(f"     Reintentos: {domain_config['max_retries']}")
                    print(f"     Delay: {domain_config['delay_between_requests']}s")
                    print(f"     Concurrentes: {domain_config['max_concurrent']}")
    
    def configure_integrations(self):
        """Configura las integraciones externas."""
        logger.info("🔗 Configurando Integraciones...")
        
        for integration, config in self.default_configs['integrations'].items():
            logger.info(f"  Configurando {integration.upper()}...")
            
            print(f"\n🔌 {integration.upper()}")
            print(f"   Estado: {'Habilitado' if config['enabled'] else 'Deshabilitado'}")
            
            if config['enabled']:
                if integration == 'openai':
                    print(f"   Modelo: {config['model']}")
                    print(f"   Temperatura: {config['temperature']}")
                    print(f"   Max Tokens: {config['max_tokens']}")
                elif integration == 'stripe':
                    print(f"   Publishable Key: {'Configurado' if config['publishable_key'] else 'No configurado'}")
                    print(f"   Secret Key: {'Configurado' if config['secret_key'] else 'No configurado'}")
                elif integration in ['blacktrust', 'incode']:
                    print(f"   API URL: {config['api_url']}")
    
    def generate_config_files(self):
        """Genera los archivos de configuración."""
        logger.info("📄 Generando archivos de configuración...")
        
        # Crear directorio de configuración si no existe
        config_dir = self.base_dir / 'config' / 'ats'
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # Generar archivo de configuración principal
        main_config = {
            'version': '2.0.0',
            'generated_at': datetime.now().isoformat(),
            'business_units': self.default_configs['business_units'],
            'channels': self.default_configs['channels'],
            'assessments': self.default_configs['assessments'],
            'scraping': self.default_configs['scraping'],
            'integrations': self.default_configs['integrations']
        }
        
        config_file = config_dir / 'ats_config.json'
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(main_config, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Archivo de configuración generado: {config_file}")
        
        # Generar archivo de configuración de chatbot
        chatbot_config = {
            'name': 'AURA Chatbot',
            'version': '2.0.0',
            'language': 'es',
            'timezone': 'America/Mexico_City',
            'business_units': self.default_configs['business_units'],
            'channels': self.default_configs['channels'],
            'assessments': self.default_configs['assessments']
        }
        
        chatbot_config_file = config_dir / 'chatbot_config.json'
        with open(chatbot_config_file, 'w', encoding='utf-8') as f:
            json.dump(chatbot_config, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Configuración de chatbot generada: {chatbot_config_file}")
    
    def validate_configuration(self):
        """Valida la configuración generada."""
        logger.info("✅ Validando configuración...")
        
        # Validar Business Units
        for bu_code, config in self.default_configs['business_units'].items():
            if not config['name']:
                raise ValueError(f"Nombre faltante para Business Unit: {bu_code}")
            if config['commission_percentage'] < 0 or config['commission_percentage'] > 100:
                raise ValueError(f"Comisión inválida para {bu_code}: {config['commission_percentage']}%")
        
        # Validar Canales
        for channel, config in self.default_configs['channels'].items():
            if config['enabled']:
                if channel == 'whatsapp' and not config['phone_number']:
                    logger.warning(f"⚠️  Número de teléfono no configurado para WhatsApp")
                elif channel == 'email' and not config['smtp_host']:
                    logger.warning(f"⚠️  Servidor SMTP no configurado para Email")
        
        # Validar Assessments
        for assessment, config in self.default_configs['assessments'].items():
            if config['enabled']:
                if config['passing_score'] < 0 or config['passing_score'] > 100:
                    raise ValueError(f"Puntaje mínimo inválido para {assessment}: {config['passing_score']}%")
        
        logger.info("✅ Validación completada")
    
    def show_summary(self):
        """Muestra un resumen de la configuración."""
        print("\n" + "="*80)
        print("📋 RESUMEN DE CONFIGURACIÓN DEL SISTEMA ATS huntRED®")
        print("="*80)
        
        # Business Units
        print(f"\n🏢 UNIDADES DE NEGOCIO: {len(self.default_configs['business_units'])}")
        for bu_code, config in self.default_configs['business_units'].items():
            print(f"   ✅ {config['name']} ({bu_code})")
        
        # Canales
        enabled_channels = [c for c, config in self.default_configs['channels'].items() if config['enabled']]
        print(f"\n📡 CANALES HABILITADOS: {len(enabled_channels)}")
        for channel in enabled_channels:
            print(f"   ✅ {channel.upper()}")
        
        # Assessments
        enabled_assessments = [a for a, config in self.default_configs['assessments'].items() if config['enabled']]
        print(f"\n📊 ASSESSMENTS HABILITADOS: {len(enabled_assessments)}")
        for assessment in enabled_assessments:
            print(f"   ✅ {assessment.replace('_', ' ').title()}")
        
        # Scraping
        scraping_enabled = self.default_configs['scraping']['enabled']
        enabled_domains = [d for d, config in self.default_configs['scraping']['domains'].items() if config['enabled']]
        print(f"\n🔍 SCRAPING: {'Habilitado' if scraping_enabled else 'Deshabilitado'}")
        if scraping_enabled:
            print(f"   Dominios configurados: {len(enabled_domains)}")
            for domain in enabled_domains:
                print(f"   ✅ {domain.upper()}")
        
        # Integraciones
        enabled_integrations = [i for i, config in self.default_configs['integrations'].items() if config['enabled']]
        print(f"\n🔗 INTEGRACIONES HABILITADAS: {len(enabled_integrations)}")
        for integration in enabled_integrations:
            print(f"   ✅ {integration.upper()}")
        
        print("\n" + "="*80)
        print("🎉 ¡Configuración del Sistema ATS huntRED® completada!")
        print("="*80)

def main():
    """Función principal."""
    print("🚀 Configurador del Sistema ATS huntRED®")
    print("="*50)
    
    configurator = ATSConfigurator()
    
    try:
        # Ejecutar configuración
        configurator.run_configuration()
        
        # Mostrar resumen
        configurator.show_summary()
        
        print("\n📝 PRÓXIMOS PASOS:")
        print("1. Revisar y ajustar las configuraciones en los archivos generados")
        print("2. Configurar las credenciales de APIs y servicios externos")
        print("3. Ejecutar las migraciones de Django si es necesario")
        print("4. Probar los canales de comunicación")
        print("5. Verificar el funcionamiento del chatbot")
        print("6. Configurar los dominios de scraping")
        
        print("\n📚 DOCUMENTACIÓN:")
        print("- Archivos de configuración: config/ats/")
        print("- Logs: configuracion_ats.log")
        print("- Workflows: app/ats/chatbot/workflow/")
        print("- Assessments: app/ats/chatbot/workflow/assessments/")
        
    except Exception as e:
        logger.error(f"❌ Error en la configuración: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 