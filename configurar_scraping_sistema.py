#!/usr/bin/env python3
"""
Script de Configuración del Sistema de Scraping huntRED®

Este script configura:
1. Dominios de scraping por plataforma
2. Configuración de APIs y credenciales
3. Reglas de scraping por Business Unit
4. Configuración de proxies y anti-detección
5. Programación de scraping automático

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
        logging.FileHandler('scraping_config.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ScrapingConfigurator:
    """Configurador del sistema de scraping."""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.config_dir = self.base_dir / 'config' / 'scraping'
        
        # Configuraciones de dominios por plataforma
        self.domain_configs = {
            'linkedin': {
                'name': 'LinkedIn',
                'description': 'Plataforma profesional para networking y oportunidades',
                'enabled': True,
                'max_retries': 5,
                'delay_between_requests': 3.0,
                'max_concurrent': 1,
                'use_proxy': True,
                'rotate_user_agents': True,
                'enable_anti_detection': True,
                'rate_limit_requests': 15,
                'rate_limit_period': 60,
                'domains': [
                    {
                        'name': 'LinkedIn Jobs',
                        'url': 'https://www.linkedin.com/jobs/',
                        'patterns': [
                            'https://www.linkedin.com/jobs/view/*',
                            'https://www.linkedin.com/jobs/collections/*'
                        ],
                        'business_units': ['huntRED', 'huntRED_executive', 'huntU'],
                        'priority': 'high'
                    }
                ],
                'extraction_rules': {
                    'job_title': 'h1.job-details-jobs-unified-top-card__job-title',
                    'company_name': '.job-details-jobs-unified-top-card__company-name',
                    'location': '.job-details-jobs-unified-top-card__bullet',
                    'description': '.job-details-jobs-unified-top-card__job-description',
                    'requirements': '.job-details-jobs-unified-top-card__job-criteria-item',
                    'salary': '.job-details-jobs-unified-top-card__salary-info'
                }
            },
            'workday': {
                'name': 'Workday',
                'description': 'Sistema de gestión de recursos humanos empresarial',
                'enabled': True,
                'max_retries': 3,
                'delay_between_requests': 2.0,
                'max_concurrent': 2,
                'use_proxy': False,
                'rotate_user_agents': True,
                'enable_anti_detection': True,
                'rate_limit_requests': 20,
                'rate_limit_period': 60,
                'domains': [
                    {
                        'name': 'Workday Careers',
                        'url': 'https://*.workday.com/*/jobs',
                        'patterns': [
                            'https://*.workday.com/*/jobs/*',
                            'https://*.workday.com/*/careers/*'
                        ],
                        'business_units': ['huntRED', 'huntRED_executive'],
                        'priority': 'high'
                    }
                ],
                'extraction_rules': {
                    'job_title': '.job-title, h1[data-automation-id="job-title"]',
                    'company_name': '.company-name, [data-automation-id="company-name"]',
                    'location': '.location, [data-automation-id="location"]',
                    'description': '.job-description, [data-automation-id="job-description"]',
                    'requirements': '.requirements, [data-automation-id="requirements"]',
                    'salary': '.salary, [data-automation-id="salary"]'
                }
            },
            'indeed': {
                'name': 'Indeed',
                'description': 'Portal de empleo global',
                'enabled': True,
                'max_retries': 3,
                'delay_between_requests': 2.0,
                'max_concurrent': 3,
                'use_proxy': True,
                'rotate_user_agents': True,
                'enable_anti_detection': True,
                'rate_limit_requests': 25,
                'rate_limit_period': 60,
                'domains': [
                    {
                        'name': 'Indeed México',
                        'url': 'https://mx.indeed.com/',
                        'patterns': [
                            'https://mx.indeed.com/viewjob?*',
                            'https://mx.indeed.com/jobs?*'
                        ],
                        'business_units': ['huntRED', 'huntU', 'amigro'],
                        'priority': 'medium'
                    }
                ],
                'extraction_rules': {
                    'job_title': 'h1.jobsearch-JobInfoHeader-title',
                    'company_name': '[data-testid="jobsearch-JobInfoHeader-companyName"]',
                    'location': '[data-testid="jobsearch-JobInfoHeader-locationText"]',
                    'description': '#jobDescriptionText',
                    'requirements': '.jobsearch-JobDescriptionSection-sectionItem',
                    'salary': '[data-testid="jobsearch-JobInfoHeader-salaryText"]'
                }
            },
            'computrabajo': {
                'name': 'Computrabajo',
                'description': 'Portal de empleo en español',
                'enabled': True,
                'max_retries': 3,
                'delay_between_requests': 1.5,
                'max_concurrent': 5,
                'use_proxy': False,
                'rotate_user_agents': True,
                'enable_anti_detection': False,
                'rate_limit_requests': 30,
                'rate_limit_period': 60,
                'domains': [
                    {
                        'name': 'Computrabajo México',
                        'url': 'https://www.computrabajo.com.mx/',
                        'patterns': [
                            'https://www.computrabajo.com.mx/ofertas-de-trabajo/*',
                            'https://www.computrabajo.com.mx/empresas/*'
                        ],
                        'business_units': ['huntRED', 'huntU', 'amigro'],
                        'priority': 'medium'
                    }
                ],
                'extraction_rules': {
                    'job_title': 'h1.fs24',
                    'company_name': '.fs16.fc_aux',
                    'location': '.fs16.fc_aux.ml5',
                    'description': '.box_r',
                    'requirements': '.box_r ul li',
                    'salary': '.fs18.fc_ok'
                }
            },
            'glassdoor': {
                'name': 'Glassdoor',
                'description': 'Portal de empleo con reviews de empresas',
                'enabled': True,
                'max_retries': 3,
                'delay_between_requests': 2.5,
                'max_concurrent': 2,
                'use_proxy': True,
                'rotate_user_agents': True,
                'enable_anti_detection': True,
                'rate_limit_requests': 15,
                'rate_limit_period': 60,
                'domains': [
                    {
                        'name': 'Glassdoor Jobs',
                        'url': 'https://www.glassdoor.com/Job/',
                        'patterns': [
                            'https://www.glassdoor.com/Job/*',
                            'https://www.glassdoor.com/Jobs/*'
                        ],
                        'business_units': ['huntRED', 'huntRED_executive'],
                        'priority': 'medium'
                    }
                ],
                'extraction_rules': {
                    'job_title': 'h1.job-title',
                    'company_name': '.employer-name',
                    'location': '.location',
                    'description': '.jobDescriptionContent',
                    'requirements': '.jobDescriptionContent ul li',
                    'salary': '.salary-estimate'
                }
            },
            'greenhouse': {
                'name': 'Greenhouse',
                'description': 'Sistema de reclutamiento empresarial',
                'enabled': True,
                'max_retries': 3,
                'delay_between_requests': 2.0,
                'max_concurrent': 2,
                'use_proxy': False,
                'rotate_user_agents': True,
                'enable_anti_detection': True,
                'rate_limit_requests': 20,
                'rate_limit_period': 60,
                'domains': [
                    {
                        'name': 'Greenhouse Jobs',
                        'url': 'https://boards.greenhouse.io/',
                        'patterns': [
                            'https://boards.greenhouse.io/*/jobs/*',
                            'https://boards-api.greenhouse.io/v1/boards/*/jobs'
                        ],
                        'business_units': ['huntRED', 'huntRED_executive'],
                        'priority': 'high'
                    }
                ],
                'extraction_rules': {
                    'job_title': 'h1.app-title',
                    'company_name': '.company-name',
                    'location': '.location',
                    'description': '.content',
                    'requirements': '.content ul li',
                    'salary': '.salary'
                }
            }
        }
        
        # Configuración de proxies
        self.proxy_config = {
            'enabled': True,
            'rotation_enabled': True,
            'proxy_list': [
                # Lista de proxies (configurar según disponibilidad)
                # 'http://proxy1:port',
                # 'http://proxy2:port',
            ],
            'rotation_interval': 100,  # Cambiar proxy cada 100 requests
            'timeout': 30,
            'max_fails': 3
        }
        
        # Configuración de User-Agents
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0'
        ]
        
        # Configuración de programación
        self.scheduling_config = {
            'enabled': True,
            'frequency': 'daily',
            'start_time': '09:00',
            'end_time': '18:00',
            'timezone': 'America/Mexico_City',
            'business_units_schedule': {
                'huntRED_executive': {
                    'frequency': 'daily',
                    'start_time': '08:00',
                    'end_time': '17:00',
                    'priority_domains': ['linkedin', 'workday', 'greenhouse']
                },
                'huntRED': {
                    'frequency': 'daily',
                    'start_time': '09:00',
                    'end_time': '18:00',
                    'priority_domains': ['linkedin', 'indeed', 'computrabajo']
                },
                'huntU': {
                    'frequency': 'daily',
                    'start_time': '10:00',
                    'end_time': '19:00',
                    'priority_domains': ['indeed', 'computrabajo', 'linkedin']
                },
                'amigro': {
                    'frequency': 'daily',
                    'start_time': '08:00',
                    'end_time': '20:00',
                    'priority_domains': ['computrabajo', 'indeed']
                }
            }
        }
        
        # Configuración de notificaciones
        self.notification_config = {
            'enabled': True,
            'channels': ['email', 'slack', 'webhook'],
            'success_threshold': 80,  # Notificar si éxito < 80%
            'error_threshold': 5,     # Notificar si errores > 5
            'recipients': [
                # Configurar emails de notificación
                # 'admin@huntred.com',
                # 'tech@huntred.com'
            ]
        }
    
    def run_configuration(self):
        """Ejecuta la configuración del sistema de scraping."""
        logger.info("🚀 Iniciando configuración del Sistema de Scraping")
        
        try:
            # 1. Configurar Dominios
            self.configure_domains()
            
            # 2. Configurar Proxies
            self.configure_proxies()
            
            # 3. Configurar Programación
            self.configure_scheduling()
            
            # 4. Configurar Notificaciones
            self.configure_notifications()
            
            # 5. Generar archivos de configuración
            self.generate_config_files()
            
            # 6. Validar configuración
            self.validate_configuration()
            
            logger.info("✅ Configuración del Sistema de Scraping completada")
            
        except Exception as e:
            logger.error(f"❌ Error durante la configuración: {str(e)}")
            raise
    
    def configure_domains(self):
        """Configura los dominios de scraping."""
        logger.info("🌐 Configurando Dominios de Scraping...")
        
        for platform, config in self.domain_configs.items():
            logger.info(f"  Configurando {config['name']}...")
            
            print(f"\n🌐 {config['name']} ({platform})")
            print(f"   Estado: {'Habilitado' if config['enabled'] else 'Deshabilitado'}")
            if config['enabled']:
                print(f"   Reintentos: {config['max_retries']}")
                print(f"   Delay: {config['delay_between_requests']}s")
                print(f"   Concurrentes: {config['max_concurrent']}")
                print(f"   Proxy: {'Sí' if config['use_proxy'] else 'No'}")
                print(f"   Rotación UA: {'Sí' if config['rotate_user_agents'] else 'No'}")
                print(f"   Anti-detección: {'Sí' if config['enable_anti_detection'] else 'No'}")
                print(f"   Rate limit: {config['rate_limit_requests']} req/{config['rate_limit_period']}s")
                
                print(f"   Dominios configurados: {len(config['domains'])}")
                for domain in config['domains']:
                    print(f"     - {domain['name']} ({domain['priority']})")
                    print(f"       BUs: {', '.join(domain['business_units'])}")
    
    def configure_proxies(self):
        """Configura el sistema de proxies."""
        logger.info("🔒 Configurando Sistema de Proxies...")
        
        proxy_config = self.proxy_config
        print(f"\n🔒 Sistema de Proxies")
        print(f"   Estado: {'Habilitado' if proxy_config['enabled'] else 'Deshabilitado'}")
        if proxy_config['enabled']:
            print(f"   Rotación: {'Habilitada' if proxy_config['rotation_enabled'] else 'Deshabilitada'}")
            print(f"   Proxies configurados: {len(proxy_config['proxy_list'])}")
            print(f"   Intervalo rotación: {proxy_config['rotation_interval']} requests")
            print(f"   Timeout: {proxy_config['timeout']}s")
            print(f"   Máximo fallos: {proxy_config['max_fails']}")
            
            if not proxy_config['proxy_list']:
                print(f"   ⚠️  No hay proxies configurados")
    
    def configure_scheduling(self):
        """Configura la programación de scraping."""
        logger.info("⏰ Configurando Programación de Scraping...")
        
        scheduling_config = self.scheduling_config
        print(f"\n⏰ Programación de Scraping")
        print(f"   Estado: {'Habilitado' if scheduling_config['enabled'] else 'Deshabilitado'}")
        if scheduling_config['enabled']:
            print(f"   Frecuencia: {scheduling_config['frequency']}")
            print(f"   Horario: {scheduling_config['start_time']} - {scheduling_config['end_time']}")
            print(f"   Zona horaria: {scheduling_config['timezone']}")
            
            print(f"\n   Programación por BU:")
            for bu, schedule in scheduling_config['business_units_schedule'].items():
                print(f"     {bu}:")
                print(f"       Frecuencia: {schedule['frequency']}")
                print(f"       Horario: {schedule['start_time']} - {schedule['end_time']}")
                print(f"       Dominios prioritarios: {', '.join(schedule['priority_domains'])}")
    
    def configure_notifications(self):
        """Configura las notificaciones."""
        logger.info("🔔 Configurando Notificaciones...")
        
        notification_config = self.notification_config
        print(f"\n🔔 Sistema de Notificaciones")
        print(f"   Estado: {'Habilitado' if notification_config['enabled'] else 'Deshabilitado'}")
        if notification_config['enabled']:
            print(f"   Canales: {', '.join(notification_config['channels'])}")
            print(f"   Umbral éxito: {notification_config['success_threshold']}%")
            print(f"   Umbral errores: {notification_config['error_threshold']}")
            print(f"   Destinatarios: {len(notification_config['recipients'])}")
            
            if not notification_config['recipients']:
                print(f"   ⚠️  No hay destinatarios configurados")
    
    def generate_config_files(self):
        """Genera los archivos de configuración."""
        logger.info("📄 Generando archivos de configuración...")
        
        # Crear directorio si no existe
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Generar archivo principal de scraping
        scraping_config = {
            'version': '2.0.0',
            'generated_at': datetime.now().isoformat(),
            'domains': self.domain_configs,
            'proxy_config': self.proxy_config,
            'user_agents': self.user_agents,
            'scheduling': self.scheduling_config,
            'notifications': self.notification_config
        }
        
        main_config_file = self.config_dir / 'scraping_config.json'
        with open(main_config_file, 'w', encoding='utf-8') as f:
            json.dump(scraping_config, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Archivo principal generado: {main_config_file}")
        
        # Generar archivos individuales por plataforma
        for platform, config in self.domain_configs.items():
            platform_file = self.config_dir / f'{platform}_config.json'
            with open(platform_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Configuración generada para {platform}: {platform_file}")
        
        # Generar archivo de programación
        scheduling_file = self.config_dir / 'scheduling_config.json'
        with open(scheduling_file, 'w', encoding='utf-8') as f:
            json.dump(self.scheduling_config, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Configuración de programación generada: {scheduling_file}")
        
        # Generar archivo de notificaciones
        notification_file = self.config_dir / 'notification_config.json'
        with open(notification_file, 'w', encoding='utf-8') as f:
            json.dump(self.notification_config, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Configuración de notificaciones generada: {notification_file}")
    
    def validate_configuration(self):
        """Valida la configuración de scraping."""
        logger.info("✅ Validando configuración de scraping...")
        
        # Validar dominios
        for platform, config in self.domain_configs.items():
            if config['enabled']:
                if config['max_retries'] < 0:
                    raise ValueError(f"Reintentos inválidos para {platform}: {config['max_retries']}")
                
                if config['delay_between_requests'] < 0:
                    raise ValueError(f"Delay inválido para {platform}: {config['delay_between_requests']}")
                
                if config['max_concurrent'] < 1:
                    raise ValueError(f"Concurrentes inválidos para {platform}: {config['max_concurrent']}")
                
                if config['rate_limit_requests'] < 1:
                    raise ValueError(f"Rate limit inválido para {platform}: {config['rate_limit_requests']}")
                
                # Validar dominios
                for domain in config['domains']:
                    if not domain['url']:
                        raise ValueError(f"URL faltante para dominio en {platform}")
                    
                    if not domain['business_units']:
                        raise ValueError(f"Business Units faltantes para dominio en {platform}")
        
        # Validar programación
        if self.scheduling_config['enabled']:
            for bu, schedule in self.scheduling_config['business_units_schedule'].items():
                if not schedule['priority_domains']:
                    raise ValueError(f"Dominios prioritarios faltantes para {bu}")
        
        logger.info("✅ Validación de scraping completada")
    
    def show_summary(self):
        """Muestra un resumen de la configuración."""
        print("\n" + "="*80)
        print("📋 RESUMEN DE CONFIGURACIÓN DEL SISTEMA DE SCRAPING")
        print("="*80)
        
        # Plataformas
        enabled_platforms = [p for p, config in self.domain_configs.items() if config['enabled']]
        print(f"\n🌐 PLATAFORMAS HABILITADAS: {len(enabled_platforms)}")
        for platform in enabled_platforms:
            config = self.domain_configs[platform]
            print(f"   ✅ {config['name']} ({platform})")
            print(f"      Dominios: {len(config['domains'])}")
            print(f"      Concurrentes: {config['max_concurrent']}")
        
        # Proxies
        proxy_enabled = self.proxy_config['enabled']
        print(f"\n🔒 SISTEMA DE PROXIES: {'Habilitado' if proxy_enabled else 'Deshabilitado'}")
        if proxy_enabled:
            print(f"   Proxies configurados: {len(self.proxy_config['proxy_list'])}")
            print(f"   Rotación: {'Habilitada' if self.proxy_config['rotation_enabled'] else 'Deshabilitada'}")
        
        # Programación
        scheduling_enabled = self.scheduling_config['enabled']
        print(f"\n⏰ PROGRAMACIÓN: {'Habilitada' if scheduling_enabled else 'Deshabilitada'}")
        if scheduling_enabled:
            print(f"   Frecuencia: {self.scheduling_config['frequency']}")
            print(f"   Horario: {self.scheduling_config['start_time']} - {self.scheduling_config['end_time']}")
        
        # Notificaciones
        notification_enabled = self.notification_config['enabled']
        print(f"\n🔔 NOTIFICACIONES: {'Habilitadas' if notification_enabled else 'Deshabilitadas'}")
        if notification_enabled:
            print(f"   Canales: {', '.join(self.notification_config['channels'])}")
            print(f"   Destinatarios: {len(self.notification_config['recipients'])}")
        
        print("\n" + "="*80)
        print("🎉 ¡Configuración del Sistema de Scraping completada!")
        print("="*80)

def main():
    """Función principal."""
    print("🚀 Configurador del Sistema de Scraping huntRED®")
    print("="*60)
    
    configurator = ScrapingConfigurator()
    
    try:
        # Ejecutar configuración
        configurator.run_configuration()
        
        # Mostrar resumen
        configurator.show_summary()
        
        print("\n📝 PRÓXIMOS PASOS:")
        print("1. Configurar credenciales de APIs específicas")
        print("2. Agregar lista de proxies si es necesario")
        print("3. Configurar destinatarios de notificaciones")
        print("4. Ajustar horarios de programación según necesidades")
        print("5. Probar el scraping en cada plataforma")
        print("6. Monitorear métricas de éxito y errores")
        
        print("\n📚 ARCHIVOS GENERADOS:")
        print("- Configuración principal: config/scraping/scraping_config.json")
        print("- Configuraciones por plataforma: config/scraping/*_config.json")
        print("- Programación: config/scraping/scheduling_config.json")
        print("- Notificaciones: config/scraping/notification_config.json")
        print("- Logs: scraping_config.log")
        
    except Exception as e:
        logger.error(f"❌ Error en la configuración: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 