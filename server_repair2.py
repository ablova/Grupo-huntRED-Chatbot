#!/usr/bin/env python
"""
Script de reparación secundario para el servidor de Grupo huntRED® Chatbot.
Enfocado en la migración de intents a la base de datos y optimizaciones avanzadas.

Creado: Mayo 20, 2025
Autor: Equipo Desarrollo Grupo huntRED®

Este script se ejecuta desde server_repair.py y continúa con las tareas
de reparación y optimización del sistema.
"""

import os
import sys
import re
import json
import time
import shutil
import logging
import importlib
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Union

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('server_repair2.log')
    ]
)
logger = logging.getLogger('Server-Repair2')

# Ruta raíz de la aplicación
APP_ROOT = Path("/Users/pablollh/MEGA/GitHub/Grupo-huntRED-Chatbot/app")
if not APP_ROOT.exists():
    APP_ROOT = Path(os.getcwd()) / "app"
    if not APP_ROOT.exists():
        APP_ROOT = Path(os.path.dirname(os.path.abspath(__file__))) / "app"

def migrate_intent_patterns_to_database():
    """
    Migra los patrones de intents definidos en el diccionario INTENT_PATTERNS a la base de datos.
    Esto garantiza que todos los intents estén disponibles como registros de IntentPattern en la base de datos.
    
    NOTA: Esta función requiere que Django esté configurado y que el modelo IntentPattern exista.
    Se ejecuta después de que se hayan aplicado todas las otras reparaciones.
    """
    try:
        # Intentar importar Django y los modelos necesarios
        import django
        from django.conf import settings
        from django.db import transaction
        from django.utils import timezone
        
        # No importamos directamente para evitar problemas de dependencia circular
        # ya que el script se ejecuta fuera del entorno Django
        logger.info("Verificando instalación de Django para migración de patrones de intents...")
        
        # Intentar importar el modelo IntentPattern
        try:
            from app.models import IntentPattern, BusinessUnit, INTENT_TYPE_CHOICES
            logger.info("Modelo IntentPattern cargado correctamente")
        except ImportError as e:
            logger.error(f"No se pudo importar el modelo IntentPattern: {e}")
            return False
        
        # Intentar importar el diccionario INTENT_PATTERNS
        try:
            # Primero verificamos si el módulo está disponible
            import importlib.util
            spec = importlib.util.find_spec("app.com.chatbot.intents_handler")
            if spec is None:
                logger.error("No se encontró el módulo app.com.chatbot.intents_handler")
                return False
                
            # Importar el módulo dinámicamente
            intents_handler = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(intents_handler)
            
            # Intentar acceder al diccionario INTENT_PATTERNS
            if not hasattr(intents_handler, 'INTENT_PATTERNS'):
                logger.error("No se encontró el diccionario INTENT_PATTERNS en el módulo intents_handler")
                return False
                
            INTENT_PATTERNS = intents_handler.INTENT_PATTERNS
            logger.info(f"Diccionario INTENT_PATTERNS cargado con {len(INTENT_PATTERNS)} patrones")
        except Exception as e:
            logger.error(f"Error al cargar el diccionario INTENT_PATTERNS: {e}")
            return False
        
        # Obtener todas las unidades de negocio para la migración
        business_units = {}
        try:
            for bu in BusinessUnit.objects.all():
                business_units[bu.code.lower()] = bu
            logger.info(f"Cargadas {len(business_units)} unidades de negocio")
        except Exception as e:
            logger.error(f"Error al cargar unidades de negocio: {e}")
            return False
            
        # Iniciar la migración en una transacción
        with transaction.atomic():
            count_created = 0
            count_updated = 0
            
            # Procesar cada intent en el diccionario
            for intent_name, intent_data in INTENT_PATTERNS.items():
                try:
                    # Obtener o crear el IntentPattern en la base de datos
                    intent, created = IntentPattern.objects.get_or_create(
                        intent_name=intent_name,
                        defaults={
                            'patterns': intent_data.get('patterns', []),
                            'responses': '|||'.join(intent_data.get('responses', [])) if isinstance(intent_data.get('responses', []), list) else intent_data.get('responses', ''),
                            'priority': intent_data.get('priority', 5),
                            'requires_context': intent_data.get('requires_context', False),
                            'changes_state': intent_data.get('changes_state', False),
                            'next_state': intent_data.get('next_state', ''),
                            'intent_type': 'GENERAL',  # Tipo por defecto
                            'active': True
                        }
                    )
                    
                    if created:
                        count_created += 1
                        logger.info(f"Creado intent {intent_name} en la base de datos")
                    else:
                        # Actualizar si ya existe
                        intent.patterns = intent_data.get('patterns', [])
                        intent.responses = '|||'.join(intent_data.get('responses', [])) if isinstance(intent_data.get('responses', []), list) else intent_data.get('responses', '')
                        intent.priority = intent_data.get('priority', 5)
                        intent.requires_context = intent_data.get('requires_context', False)
                        intent.changes_state = intent_data.get('changes_state', False)
                        intent.next_state = intent_data.get('next_state', '')
                        intent.save()
                        count_updated += 1
                        logger.info(f"Actualizado intent {intent_name} en la base de datos")
                    
                    # Asignar a unidades de negocio si aplica (por ejemplo, basado en el nombre del intent)
                    for bu_code, bu in business_units.items():
                        if bu_code in intent_name.lower():
                            intent.business_units.add(bu)
                            logger.info(f"Intent {intent_name} asignado a {bu.name}")
                    
                except Exception as e:
                    logger.error(f"Error procesando intent {intent_name}: {e}")
            
            logger.info(f"Migración completada: {count_created} intents creados, {count_updated} intents actualizados")
            return True
            
    except Exception as e:
        logger.error(f"Error general en la migración de intents: {e}")
        return False

def optimize_database_queries():
    """
    Optimiza las consultas a la base de datos añadiendo índices a campos frecuentemente consultados.
    También verifica y corrige problemas de integridad de datos.
    """
    try:
        # Importar Django y los modelos necesarios
        import django
        from django.db import connection
        from django.conf import settings
        
        logger.info("Verificando índices y optimizando consultas...")
        
        # Lista de índices a verificar/crear
        indexes = [
            ('app_person', 'email'),
            ('app_person', 'phone'),
            ('app_businessunit', 'code'),
            ('app_intentpattern', 'intent_name'),
            ('app_vacante', 'status')
        ]
        
        # Verificar y crear índices si no existen
        with connection.cursor() as cursor:
            for table, column in indexes:
                index_name = f'idx_{table}_{column}'
                # Verificar si el índice ya existe
                cursor.execute(
                    f"SELECT COUNT(*) FROM pg_indexes WHERE tablename = %s AND indexname = %s", 
                    [table, index_name]
                )
                exists = cursor.fetchone()[0] > 0
                
                if not exists:
                    # Crear el índice
                    try:
                        cursor.execute(f"CREATE INDEX {index_name} ON {table} ({column})")
                        logger.info(f"Creado índice {index_name} en tabla {table} para columna {column}")
                    except Exception as e:
                        logger.error(f"Error creando índice {index_name}: {e}")
                else:
                    logger.info(f"Índice {index_name} ya existe")
        
        logger.info("Optimización de consultas completada")
        return True
    
    except Exception as e:
        logger.error(f"Error en optimización de consultas: {e}")
        return False

def clean_duplicate_records():
    """
    Identifica y limpia registros duplicados en la base de datos.
    Se enfoca en tablas que suelen tener problemas de duplicidad como Person, Vacante, etc.
    """
    try:
        # Importar Django y los modelos necesarios
        import django
        from django.db import connection, transaction
        from django.conf import settings
        
        logger.info("Verificando registros duplicados...")
        
        # Lista de tablas y columnas a verificar para duplicados
        duplicate_checks = [
            ('app_person', ['email'], "Persona"),
            ('app_vacante', ['title', 'business_unit_id'], "Vacante"),
            ('app_intentpattern', ['intent_name'], "Patrón de Intent")
        ]
        
        total_duplicates = 0
        
        # Verificar y eliminar duplicados
        with connection.cursor() as cursor:
            for table, columns, entity_name in duplicate_checks:
                # Construcción dinámica de la consulta para encontrar duplicados
                columns_str = ', '.join(columns)
                duplicate_query = f"""
                    SELECT {columns_str}, COUNT(*)
                    FROM {table}
                    GROUP BY {columns_str}
                    HAVING COUNT(*) > 1
                """
                
                cursor.execute(duplicate_query)
                duplicates = cursor.fetchall()
                
                if duplicates:
                    logger.info(f"Encontrados {len(duplicates)} grupos de {entity_name}s duplicados")
                    total_duplicates += len(duplicates)
                    
                    # Proceso para eliminar duplicados
                    with transaction.atomic():
                        for duplicate in duplicates:
                            # Valores de las columnas que identifican el duplicado
                            values = duplicate[:-1]  # Excluir el conteo
                            
                            # Construir condiciones WHERE para encontrar estos duplicados
                            where_conditions = []
                            for i, col in enumerate(columns):
                                where_conditions.append(f"{col} = %s")
                            
                            where_clause = ' AND '.join(where_conditions)
                            
                            # Obtener todos los IDs de los registros duplicados
                            id_query = f"SELECT id FROM {table} WHERE {where_clause} ORDER BY id"
                            cursor.execute(id_query, values)
                            ids = [row[0] for row in cursor.fetchall()]
                            
                            # Conservar el primer ID (el más antiguo) y eliminar el resto
                            if len(ids) > 1:
                                keep_id = ids[0]
                                delete_ids = ids[1:]
                                
                                # Construir consulta para eliminar duplicados
                                delete_query = f"DELETE FROM {table} WHERE id IN %s"
                                cursor.execute(delete_query, [tuple(delete_ids)])
                                
                                logger.info(f"Eliminados {len(delete_ids)} {entity_name}s duplicados, conservando ID {keep_id}")
                else:
                    logger.info(f"No se encontraron {entity_name}s duplicados")
        
        logger.info(f"Limpieza de duplicados completada: {total_duplicates} grupos procesados")
        return True
    
    except Exception as e:
        logger.error(f"Error en limpieza de duplicados: {e}")
        return False

def main():
    """
    Función principal que ejecuta todas las etapas de reparación adicionales.
    """
    logger.info("=== INICIANDO REPARACIONES ADICIONALES (server_repair2.py) ===")
    
    steps = [
        ("Migración de patrones de intents a la base de datos", migrate_intent_patterns_to_database),
        ("Optimización de consultas a la base de datos", optimize_database_queries),
        ("Limpieza de registros duplicados", clean_duplicate_records)
    ]
    
    results = []
    step_counter = 1
    
    for step_name, step_func in steps:
        logger.info(f"Paso {step_counter}: {step_name}")
        try:
            result = step_func()
            results.append(result)
            logger.info(f"Resultado del paso {step_counter}: {'Exitoso' if result else 'Fallido'}")
        except Exception as e:
            logger.error(f"Error en paso {step_counter}: {e}")
            results.append(False)
        step_counter += 1
    
    success_count = sum(1 for r in results if r)
    logger.info(f"Reparaciones adicionales completadas: {success_count}/{len(steps)} pasos exitosos")
    
    if success_count == len(steps):
        logger.info("=== TODAS LAS REPARACIONES ADICIONALES COMPLETADAS CON ÉXITO ===")
    else:
        logger.warning(f"=== REPARACIONES ADICIONALES COMPLETADAS CON {len(steps) - success_count} ERRORES ===")
    
    return success_count == len(steps)

if __name__ == "__main__":
    # Iniciar la operación
    success = main()
    sys.exit(0 if success else 1)
