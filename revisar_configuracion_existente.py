#!/usr/bin/env python3
"""
Script de Revisión de Configuración Existente del Sistema ATS huntRED®

Este script revisa y documenta:
1. Configuración actual de canales (WhatsApp, Telegram, etc.)
2. Workflows existentes por Business Unit
3. Assessments implementados
4. Configuración de scraping actual
5. Integraciones existentes

Autor: huntRED® Group
Versión: 2.0.0
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('revision_configuracion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ConfiguracionRevisor:
    """Revisor de la configuración existente del sistema."""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.ats_dir = self.base_dir / 'app' / 'ats'
        self.chatbot_dir = self.ats_dir / 'chatbot'
        self.integrations_dir = self.ats_dir / 'integrations'
        
        # Resultados de la revisión
        self.revision_results = {
            'channels': {},
            'workflows': {},
            'assessments': {},
            'scraping': {},
            'integrations': {},
            'business_units': {},
            'configuraciones': {}
        }
    
    def run_revision(self):
        """Ejecuta la revisión completa del sistema."""
        logger.info("🔍 Iniciando revisión de configuración existente")
        
        try:
            # 1. Revisar Canales de Comunicación
            self.revisar_canales()
            
            # 2. Revisar Workflows por BU
            self.revisar_workflows()
            
            # 3. Revisar Assessments
            self.revisar_assessments()
            
            # 4. Revisar Scraping
            self.revisar_scraping()
            
            # 5. Revisar Integraciones
            self.revisar_integraciones()
            
            # 6. Revisar Configuraciones
            self.revisar_configuraciones()
            
            # 7. Generar reporte
            self.generar_reporte()
            
            logger.info("✅ Revisión completada")
            
        except Exception as e:
            logger.error(f"❌ Error durante la revisión: {str(e)}")
            raise
    
    def revisar_canales(self):
        """Revisa los canales de comunicación existentes."""
        logger.info("📡 Revisando canales de comunicación...")
        
        channels_dir = self.integrations_dir / 'channels'
        if not channels_dir.exists():
            logger.warning("❌ Directorio de canales no encontrado")
            return
        
        # Revisar cada canal
        for channel_dir in channels_dir.iterdir():
            if channel_dir.is_dir() and not channel_dir.name.startswith('__'):
                channel_name = channel_dir.name
                logger.info(f"  Revisando canal: {channel_name}")
                
                # Buscar archivo principal del canal
                main_file = None
                for file in channel_dir.glob('*.py'):
                    if not file.name.startswith('__'):
                        main_file = file
                        break
                
                if main_file:
                    self.revision_results['channels'][channel_name] = {
                        'implementado': True,
                        'archivo_principal': str(main_file.relative_to(self.base_dir)),
                        'tamaño': main_file.stat().st_size,
                        'modificado': datetime.fromtimestamp(main_file.stat().st_mtime)
                    }
                    
                    # Revisar contenido básico
                    try:
                        with open(main_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            self.revision_results['channels'][channel_name]['lineas_codigo'] = len(content.split('\n'))
                            self.revision_results['channels'][channel_name]['tiene_webhook'] = 'webhook' in content.lower()
                            self.revision_results['channels'][channel_name]['tiene_handler'] = 'handler' in content.lower()
                    except Exception as e:
                        logger.error(f"Error leyendo {main_file}: {e}")
                else:
                    self.revision_results['channels'][channel_name] = {
                        'implementado': False,
                        'error': 'No se encontró archivo principal'
                    }
    
    def revisar_workflows(self):
        """Revisa los workflows existentes por Business Unit."""
        logger.info("🔄 Revisando workflows por Business Unit...")
        
        workflow_dir = self.chatbot_dir / 'workflow'
        if not workflow_dir.exists():
            logger.warning("❌ Directorio de workflows no encontrado")
            return
        
        # Revisar workflows comunes
        common_dir = workflow_dir / 'common'
        if common_dir.exists():
            self.revision_results['workflows']['common'] = {
                'implementado': True,
                'archivos': [f.name for f in common_dir.glob('*.py') if not f.name.startswith('__')]
            }
        
        # Revisar workflows por BU
        bu_dir = workflow_dir / 'business_units'
        if bu_dir.exists():
            for bu_dir_item in bu_dir.iterdir():
                if bu_dir_item.is_dir() and not bu_dir_item.name.startswith('__'):
                    bu_name = bu_dir_item.name
                    logger.info(f"  Revisando workflow: {bu_name}")
                    
                    # Buscar archivo principal del workflow
                    main_workflow_file = None
                    for file in bu_dir_item.glob('*.py'):
                        if not file.name.startswith('__'):
                            main_workflow_file = file
                            break
                    
                    if main_workflow_file:
                        self.revision_results['workflows'][bu_name] = {
                            'implementado': True,
                            'archivo_principal': str(main_workflow_file.relative_to(self.base_dir)),
                            'tamaño': main_workflow_file.stat().st_size,
                            'modificado': datetime.fromtimestamp(main_workflow_file.stat().st_mtime)
                        }
                        
                        # Revisar contenido
                        try:
                            with open(main_workflow_file, 'r', encoding='utf-8') as f:
                                content = f.read()
                                self.revision_results['workflows'][bu_name]['lineas_codigo'] = len(content.split('\n'))
                                self.revision_results['workflows'][bu_name]['tiene_estados'] = 'state' in content.lower()
                                self.revision_results['workflows'][bu_name]['tiene_transiciones'] = 'transition' in content.lower()
                        except Exception as e:
                            logger.error(f"Error leyendo {main_workflow_file}: {e}")
                    else:
                        self.revision_results['workflows'][bu_name] = {
                            'implementado': False,
                            'error': 'No se encontró archivo principal'
                        }
    
    def revisar_assessments(self):
        """Revisa los assessments implementados."""
        logger.info("📊 Revisando assessments...")
        
        assessment_dir = self.chatbot_dir / 'workflow' / 'assessments'
        if not assessment_dir.exists():
            logger.warning("❌ Directorio de assessments no encontrado")
            return
        
        # Revisar archivos de assessment
        assessment_files = []
        for file in assessment_dir.glob('*.py'):
            if not file.name.startswith('__'):
                assessment_files.append({
                    'nombre': file.name,
                    'tamaño': file.stat().st_size,
                    'modificado': datetime.fromtimestamp(file.stat().st_mtime)
                })
        
        self.revision_results['assessments'] = {
            'implementado': True,
            'archivos': assessment_files,
            'total_archivos': len(assessment_files)
        }
        
        # Revisar directorios específicos de assessment
        assessment_types = ['personality', 'cultural', 'talent', 'professional_dna']
        for assessment_type in assessment_types:
            type_dir = assessment_dir / assessment_type
            if type_dir.exists():
                self.revision_results['assessments'][assessment_type] = {
                    'implementado': True,
                    'archivos': [f.name for f in type_dir.glob('*.py') if not f.name.startswith('__')]
                }
            else:
                self.revision_results['assessments'][assessment_type] = {
                    'implementado': False
                }
    
    def revisar_scraping(self):
        """Revisa la configuración de scraping existente."""
        logger.info("🔍 Revisando configuración de scraping...")
        
        # Buscar archivos relacionados con scraping
        scraping_files = []
        for root, dirs, files in os.walk(self.ats_dir):
            for file in files:
                if 'scrap' in file.lower() and file.endswith('.py'):
                    file_path = Path(root) / file
                    scraping_files.append({
                        'nombre': file,
                        'ruta': str(file_path.relative_to(self.base_dir)),
                        'tamaño': file_path.stat().st_size,
                        'modificado': datetime.fromtimestamp(file_path.stat().st_mtime)
                    })
        
        self.revision_results['scraping'] = {
            'archivos_encontrados': scraping_files,
            'total_archivos': len(scraping_files)
        }
        
        # Buscar configuración específica de scraping
        scraping_config_files = []
        for root, dirs, files in os.walk(self.ats_dir):
            for file in files:
                if 'config' in file.lower() and 'scrap' in file.lower() and file.endswith('.py'):
                    file_path = Path(root) / file
                    scraping_config_files.append(str(file_path.relative_to(self.base_dir)))
        
        self.revision_results['scraping']['archivos_configuracion'] = scraping_config_files
    
    def revisar_integraciones(self):
        """Revisa las integraciones existentes."""
        logger.info("🔗 Revisando integraciones...")
        
        integrations_dir = self.integrations_dir
        if not integrations_dir.exists():
            logger.warning("❌ Directorio de integraciones no encontrado")
            return
        
        # Revisar servicios
        services_dir = integrations_dir / 'services'
        if services_dir.exists():
            services = []
            for file in services_dir.glob('*.py'):
                if not file.name.startswith('__'):
                    services.append({
                        'nombre': file.name,
                        'tamaño': file.stat().st_size,
                        'modificado': datetime.fromtimestamp(file.stat().st_mtime)
                    })
            
            self.revision_results['integrations']['services'] = services
        
        # Revisar notificaciones
        notifications_dir = integrations_dir / 'notifications'
        if notifications_dir.exists():
            notifications = []
            for file in notifications_dir.rglob('*.py'):
                if not file.name.startswith('__'):
                    notifications.append({
                        'nombre': file.name,
                        'ruta': str(file.relative_to(self.base_dir)),
                        'tamaño': file.stat().st_size
                    })
            
            self.revision_results['integrations']['notifications'] = notifications
    
    def revisar_configuraciones(self):
        """Revisa las configuraciones existentes."""
        logger.info("⚙️ Revisando configuraciones...")
        
        # Buscar archivos de configuración
        config_files = []
        for root, dirs, files in os.walk(self.ats_dir):
            for file in files:
                if 'config' in file.lower() and file.endswith('.py'):
                    file_path = Path(root) / file
                    config_files.append({
                        'nombre': file,
                        'ruta': str(file_path.relative_to(self.base_dir)),
                        'tamaño': file_path.stat().st_size,
                        'modificado': datetime.fromtimestamp(file_path.stat().st_mtime)
                    })
        
        self.revision_results['configuraciones'] = {
            'archivos': config_files,
            'total_archivos': len(config_files)
        }
        
        # Revisar configuración específica del chatbot
        chatbot_config = self.chatbot_dir / 'config'
        if chatbot_config.exists():
            chatbot_config_files = []
            for file in chatbot_config.glob('*.py'):
                if not file.name.startswith('__'):
                    chatbot_config_files.append(file.name)
            
            self.revision_results['configuraciones']['chatbot'] = chatbot_config_files
    
    def generar_reporte(self):
        """Genera un reporte detallado de la revisión."""
        logger.info("📄 Generando reporte de revisión...")
        
        # Crear directorio para reportes
        report_dir = self.base_dir / 'reportes'
        report_dir.mkdir(exist_ok=True)
        
        # Generar reporte JSON
        report_file = report_dir / f'revision_configuracion_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.revision_results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Reporte JSON generado: {report_file}")
        
        # Generar reporte legible
        self.generar_reporte_legible(report_dir)
    
    def generar_reporte_legible(self, report_dir):
        """Genera un reporte legible en formato texto."""
        report_file = report_dir / f'revision_configuracion_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("REPORTE DE REVISIÓN DE CONFIGURACIÓN SISTEMA ATS huntRED®\n")
            f.write("="*80 + "\n")
            f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Directorio base: {self.base_dir}\n\n")
            
            # Canales
            f.write("📡 CANALES DE COMUNICACIÓN\n")
            f.write("-" * 40 + "\n")
            for channel, info in self.revision_results['channels'].items():
                if info.get('implementado'):
                    f.write(f"✅ {channel.upper()}\n")
                    f.write(f"   Archivo: {info['archivo_principal']}\n")
                    f.write(f"   Tamaño: {info['tamaño']} bytes\n")
                    f.write(f"   Líneas: {info.get('lineas_codigo', 'N/A')}\n")
                    f.write(f"   Webhook: {'Sí' if info.get('tiene_webhook') else 'No'}\n")
                    f.write(f"   Handler: {'Sí' if info.get('tiene_handler') else 'No'}\n")
                else:
                    f.write(f"❌ {channel.upper()}: {info.get('error', 'No implementado')}\n")
                f.write("\n")
            
            # Workflows
            f.write("🔄 WORKFLOWS POR BUSINESS UNIT\n")
            f.write("-" * 40 + "\n")
            for workflow, info in self.revision_results['workflows'].items():
                if info.get('implementado'):
                    f.write(f"✅ {workflow.upper()}\n")
                    f.write(f"   Archivo: {info['archivo_principal']}\n")
                    f.write(f"   Tamaño: {info['tamaño']} bytes\n")
                    f.write(f"   Líneas: {info.get('lineas_codigo', 'N/A')}\n")
                    f.write(f"   Estados: {'Sí' if info.get('tiene_estados') else 'No'}\n")
                    f.write(f"   Transiciones: {'Sí' if info.get('tiene_transiciones') else 'No'}\n")
                else:
                    f.write(f"❌ {workflow.upper()}: {info.get('error', 'No implementado')}\n")
                f.write("\n")
            
            # Assessments
            f.write("📊 ASSESSMENTS\n")
            f.write("-" * 40 + "\n")
            if self.revision_results['assessments'].get('implementado'):
                f.write(f"✅ Total archivos: {self.revision_results['assessments']['total_archivos']}\n")
                for assessment_type in ['personality', 'cultural', 'talent', 'professional_dna']:
                    if assessment_type in self.revision_results['assessments']:
                        info = self.revision_results['assessments'][assessment_type]
                        if info.get('implementado'):
                            f.write(f"✅ {assessment_type.upper()}: {len(info['archivos'])} archivos\n")
                        else:
                            f.write(f"❌ {assessment_type.upper()}: No implementado\n")
            else:
                f.write("❌ Assessments no implementados\n")
            f.write("\n")
            
            # Scraping
            f.write("🔍 SCRAPING\n")
            f.write("-" * 40 + "\n")
            f.write(f"Archivos encontrados: {self.revision_results['scraping']['total_archivos']}\n")
            for file_info in self.revision_results['scraping']['archivos_encontrados']:
                f.write(f"  📄 {file_info['ruta']}\n")
            f.write("\n")
            
            # Integraciones
            f.write("🔗 INTEGRACIONES\n")
            f.write("-" * 40 + "\n")
            if 'services' in self.revision_results['integrations']:
                f.write(f"Servicios: {len(self.revision_results['integrations']['services'])}\n")
                for service in self.revision_results['integrations']['services']:
                    f.write(f"  📄 {service['nombre']}\n")
            if 'notifications' in self.revision_results['integrations']:
                f.write(f"Notificaciones: {len(self.revision_results['integrations']['notifications'])}\n")
            f.write("\n")
            
            # Configuraciones
            f.write("⚙️ CONFIGURACIONES\n")
            f.write("-" * 40 + "\n")
            f.write(f"Archivos de configuración: {self.revision_results['configuraciones']['total_archivos']}\n")
            for config in self.revision_results['configuraciones']['archivos']:
                f.write(f"  📄 {config['ruta']}\n")
            f.write("\n")
            
            f.write("="*80 + "\n")
            f.write("FIN DEL REPORTE\n")
            f.write("="*80 + "\n")
        
        logger.info(f"✅ Reporte legible generado: {report_file}")
    
    def mostrar_resumen(self):
        """Muestra un resumen de la revisión."""
        print("\n" + "="*80)
        print("📋 RESUMEN DE REVISIÓN DE CONFIGURACIÓN")
        print("="*80)
        
        # Canales
        canales_implementados = sum(1 for info in self.revision_results['channels'].values() if info.get('implementado'))
        print(f"\n📡 CANALES: {canales_implementados}/{len(self.revision_results['channels'])} implementados")
        for channel, info in self.revision_results['channels'].items():
            status = "✅" if info.get('implementado') else "❌"
            print(f"   {status} {channel.upper()}")
        
        # Workflows
        workflows_implementados = sum(1 for info in self.revision_results['workflows'].values() if info.get('implementado'))
        print(f"\n🔄 WORKFLOWS: {workflows_implementados}/{len(self.revision_results['workflows'])} implementados")
        for workflow, info in self.revision_results['workflows'].items():
            status = "✅" if info.get('implementado') else "❌"
            print(f"   {status} {workflow.upper()}")
        
        # Assessments
        if self.revision_results['assessments'].get('implementado'):
            print(f"\n📊 ASSESSMENTS: ✅ Implementados ({self.revision_results['assessments']['total_archivos']} archivos)")
        else:
            print(f"\n📊 ASSESSMENTS: ❌ No implementados")
        
        # Scraping
        print(f"\n🔍 SCRAPING: {self.revision_results['scraping']['total_archivos']} archivos encontrados")
        
        # Integraciones
        servicios = len(self.revision_results['integrations'].get('services', []))
        notificaciones = len(self.revision_results['integrations'].get('notifications', []))
        print(f"\n🔗 INTEGRACIONES: {servicios} servicios, {notificaciones} notificaciones")
        
        # Configuraciones
        print(f"\n⚙️ CONFIGURACIONES: {self.revision_results['configuraciones']['total_archivos']} archivos")
        
        print("\n" + "="*80)
        print("🎉 ¡Revisión completada!")
        print("="*80)

def main():
    """Función principal."""
    print("🔍 Revisor de Configuración del Sistema ATS huntRED®")
    print("="*60)
    
    revisor = ConfiguracionRevisor()
    
    try:
        # Ejecutar revisión
        revisor.run_revision()
        
        # Mostrar resumen
        revisor.mostrar_resumen()
        
        print("\n📝 ARCHIVOS GENERADOS:")
        print("- Reporte JSON: reportes/revision_configuracion_*.json")
        print("- Reporte legible: reportes/revision_configuracion_*.txt")
        print("- Logs: revision_configuracion.log")
        
        print("\n📚 PRÓXIMOS PASOS:")
        print("1. Revisar los reportes generados")
        print("2. Identificar componentes faltantes o incompletos")
        print("3. Priorizar implementaciones según necesidades")
        print("4. Configurar componentes específicos según el reporte")
        
    except Exception as e:
        logger.error(f"❌ Error en la revisión: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 