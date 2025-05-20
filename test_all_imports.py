#!/usr/bin/env python3
# /Users/pablollh/MEGA/GitHub/Grupo-huntRED-Chatbot/test_all_imports.py
#
# Script para verificar la integridad de las importaciones en todo el sistema
# Creado: 2025-05-20
# 
# Este script prueba sistemáticamente las importaciones de los módulos principales
# después de la refactorización para eliminar import_config.py redundantes.

import os
import sys
import importlib
import traceback
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger('test_imports')

def test_import(module_path):
    """Prueba importar un módulo específico."""
    try:
        module = importlib.import_module(module_path)
        logger.info(f"✅ Importación exitosa: {module_path}")
        return True
    except Exception as e:
        logger.error(f"❌ Error al importar {module_path}: {str(e)}")
        return False

def test_direct_imports():
    """Prueba importaciones directas de los módulos principales."""
    results = {}
    
    # Lista de clases y módulos importantes para probar
    modules = [
        # Módulos del sistema principal
        'app.module_registry',
        
        # Módulos de chatbot
        'app.com.chatbot.rate_limiter',
        'app.com.chatbot.channel_config',
        'app.com.chatbot.chatbot',
        'app.com.chatbot.chat_state_manager',
        'app.com.chatbot.response_generator',
        'app.com.chatbot.integrations.whatsapp',
        'app.com.chatbot.conversational_flow_manager',
        
        # Módulos de ML
        'app.ml.ml_model',
        'app.ml.data_loader',
        'app.ml.feature_extractor',
        
        # Módulos de Pagos
        'app.pagos.payment_processor',
        'app.pagos.payment_validator',
        
        # Módulos de Publish
        'app.publish.publisher_manager',
        'app.publish.publish_scheduler',
        
        # Módulos SEXSI
        'app.sexsi.contract_generator',
        'app.sexsi.contract_validator'
    ]
    
    logger.info("=== Iniciando prueba de importaciones directas ===")
    
    for module_path in modules:
        success = test_import(module_path)
        results[module_path] = success
    
    return results

def test_legacy_import_config():
    """Prueba la compatibilidad con el viejo sistema import_config."""
    legacy_imports = [
        'app.import_config',
        'app.com.import_config',
        'app.ml.import_config',
        'app.pagos.import_config',
        'app.publish.import_config',
        'app.sexsi.import_config'
    ]
    
    logger.info("=== Iniciando prueba de compatibilidad con import_config legacy ===")
    
    results = {}
    for module_path in legacy_imports:
        success = test_import(module_path)
        results[module_path] = success
    
    return results

def test_getter_functions():
    """Prueba las funciones getter que quedan para compatibilidad."""
    getters = [
        ('app.import_config', 'get_fetch_whatsapp_user_data'),
        ('app.com.import_config', 'get_chatbot'),
        ('app.ml.import_config', 'get_ml_model'),
        ('app.pagos.import_config', 'get_payment_processor'),
        ('app.publish.import_config', 'get_publisher_manager'),
        ('app.sexsi.import_config', 'get_contract_generator')
    ]
    
    logger.info("=== Iniciando prueba de funciones getter legacy ===")
    
    results = {}
    for module_path, function_name in getters:
        try:
            module = importlib.import_module(module_path)
            getter = getattr(module, function_name, None)
            
            if getter is not None:
                logger.info(f"✅ Función getter encontrada: {module_path}.{function_name}")
                results[f"{module_path}.{function_name}"] = True
            else:
                logger.error(f"❌ Función getter no encontrada: {module_path}.{function_name}")
                results[f"{module_path}.{function_name}"] = False
                
        except Exception as e:
            logger.error(f"❌ Error al verificar {module_path}.{function_name}: {str(e)}")
            results[f"{module_path}.{function_name}"] = False
    
    return results

def summarize_results(direct_results, legacy_results, getter_results):
    """Muestra un resumen de los resultados de las pruebas."""
    total_tests = len(direct_results) + len(legacy_results) + len(getter_results)
    passed_tests = sum(1 for success in direct_results.values() if success) + \
                   sum(1 for success in legacy_results.values() if success) + \
                   sum(1 for success in getter_results.values() if success)
    
    logger.info("\n=== RESUMEN DE RESULTADOS ===")
    logger.info(f"Total de pruebas: {total_tests}")
    logger.info(f"Pruebas exitosas: {passed_tests}")
    logger.info(f"Pruebas fallidas: {total_tests - passed_tests}")
    
    if passed_tests == total_tests:
        logger.info("🎉 Todas las pruebas pasaron exitosamente!")
    else:
        logger.info("⚠️ Algunas pruebas fallaron. Revisa los mensajes de error anteriores.")
    
    # Listar las pruebas fallidas para fácil referencia
    failed_tests = []
    
    for module, success in direct_results.items():
        if not success:
            failed_tests.append(f"Importación directa: {module}")
    
    for module, success in legacy_results.items():
        if not success:
            failed_tests.append(f"Importación legacy: {module}")
    
    for getter, success in getter_results.items():
        if not success:
            failed_tests.append(f"Función getter: {getter}")
    
    if failed_tests:
        logger.info("\nLista de pruebas fallidas:")
        for test in failed_tests:
            logger.info(f"  - {test}")
    
    # Sugerir siguientes pasos si hay fallos
    if total_tests - passed_tests > 0:
        logger.info("\nSugerencias para resolver problemas:")
        logger.info("1. Verifica que todas las dependencias estén instaladas (httpx, django, etc.)")
        logger.info("2. Revisa los archivos que aún importan de app.import_config y actualízalos")
        logger.info("3. Considera utilizar ModuleRegistry de app.module_registry para registros")

def main():
    """Función principal que ejecuta todas las pruebas."""
    logger.info("🔍 Iniciando pruebas de importación del sistema")
    
    # Ejecutar las pruebas
    direct_results = test_direct_imports()
    legacy_results = test_legacy_import_config()
    getter_results = test_getter_functions()
    
    # Resumir los resultados
    summarize_results(direct_results, legacy_results, getter_results)
    
    logger.info("✅ Prueba completada")

if __name__ == "__main__":
    main()
