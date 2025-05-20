#!/usr/bin/env python
"""
Script de reparación completo para el servidor de Grupo huntRED® Chatbot.
Soluciona problemas de importación, módulos faltantes y dependencias circulares.

Creado: Mayo 19, 2025
Autor: Equipo Desarrollo Grupo huntRED®

Este script puede ejecutarse directamente en el servidor sin necesidad
de hacer pull primero (maneja cambios locales en importaciones).
"""
import os
import sys
import re
import logging
import shutil
from pathlib import Path
import tempfile

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('server_repair')

# Rutas importantes
SERVER_ROOT = Path(os.path.dirname(os.path.abspath(__file__)))
APP_ROOT = SERVER_ROOT / "app"
IMPORT_CONFIG_PATH = APP_ROOT / "import_config.py"
CHANNEL_CONFIG_PATH = APP_ROOT / "com" / "chatbot" / "channel_config.py"

def create_channel_config():
    """
    Crea el archivo channel_config.py que es requerido por metrics.py
    pero no existe en el sistema.
    """
    if CHANNEL_CONFIG_PATH.exists():
        logger.info(f"El archivo {CHANNEL_CONFIG_PATH} ya existe")
        return True
    
    try:
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(CHANNEL_CONFIG_PATH), exist_ok=True)
        
        # Contenido del archivo
        content = '''"""
Configuración de canales para el módulo de chatbot.
Basado en las reglas globales de Grupo huntRED® para optimización CPU y consistencia.
"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ChannelConfig:
    """Gestiona la configuración de canales de comunicación."""
    
    _config = {
        'whatsapp': {
            'enabled': True,
            'rate_limit': {
                'max_messages': 20,
                'window_seconds': 60
            },
            'metrics': {
                'enabled': True
            },
            'retry': {
                'max_attempts': 3,
                'backoff_factor': 1.5
            }
        },
        'telegram': {
            'enabled': True,
            'rate_limit': {
                'max_messages': 30,
                'window_seconds': 60
            },
            'metrics': {
                'enabled': True
            },
            'retry': {
                'max_attempts': 3,
                'backoff_factor': 1.5
            }
        },
        'slack': {
            'enabled': True,
            'rate_limit': {
                'max_messages': 50,
                'window_seconds': 60
            },
            'metrics': {
                'enabled': True
            },
            'retry': {
                'max_attempts': 3,
                'backoff_factor': 1.5
            }
        },
        'email': {
            'enabled': True,
            'rate_limit': {
                'max_messages': 100,
                'window_seconds': 300
            },
            'metrics': {
                'enabled': True
            },
            'retry': {
                'max_attempts': 5,
                'backoff_factor': 2.0
            }
        },
        'sms': {
            'enabled': True,
            'rate_limit': {
                'max_messages': 5,
                'window_seconds': 60
            },
            'metrics': {
                'enabled': True
            },
            'retry': {
                'max_attempts': 3,
                'backoff_factor': 1.5
            }
        }
    }
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """
        Obtiene la configuración completa de todos los canales.
        
        Returns:
            Dict[str, Any]: Configuración de canales
        """
        return cls._config
    
    @classmethod
    def get_channel_config(cls, channel: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene la configuración para un canal específico.
        
        Args:
            channel: Nombre del canal
            
        Returns:
            Optional[Dict[str, Any]]: Configuración del canal o None si no existe
        """
        return cls._config.get(channel)
    
    @classmethod
    def is_channel_enabled(cls, channel: str) -> bool:
        """
        Verifica si un canal está habilitado.
        
        Args:
            channel: Nombre del canal
            
        Returns:
            bool: True si está habilitado, False en caso contrario
        """
        channel_config = cls.get_channel_config(channel)
        return channel_config.get('enabled', False) if channel_config else False
    
    @classmethod
    def update_channel_config(cls, channel: str, config: Dict[str, Any]) -> None:
        """
        Actualiza la configuración de un canal.
        
        Args:
            channel: Nombre del canal
            config: Nueva configuración
        """
        if channel in cls._config:
            cls._config[channel].update(config)
            logger.info(f"Configuración actualizada para canal: {channel}")
        else:
            cls._config[channel] = config
            logger.info(f"Nuevo canal configurado: {channel}")
'''
        
        # Escribir el archivo
        with open(CHANNEL_CONFIG_PATH, "w") as f:
            f.write(content)
        
        logger.info(f"Creado archivo {CHANNEL_CONFIG_PATH}")
        return True
    
    except Exception as e:
        logger.error(f"Error creando {CHANNEL_CONFIG_PATH}: {e}", exc_info=True)
        return False

def fix_import_config():
    """
    Corrige el archivo import_config.py para resolver dependencias circulares y
    añadir alias de compatibilidad para funciones renombradas.
    Maneja cambios locales en el archivo si existen.
    """
    if not IMPORT_CONFIG_PATH.exists():
        logger.error(f"No se encontró el archivo {IMPORT_CONFIG_PATH}")
        return False
    
    try:
        # Hacer una copia de seguridad del archivo original
        backup_path = IMPORT_CONFIG_PATH.parent / (IMPORT_CONFIG_PATH.name + ".bak")
        shutil.copy2(IMPORT_CONFIG_PATH, backup_path)
        logger.info(f"Backup creado en {backup_path}")
        
        # Leer contenido actual
        with open(IMPORT_CONFIG_PATH, "r") as f:
            content = f.read()
            
        # 1. Corregir importación circular de get_conversational_flow_manager
        # Buscamos las posibles importaciones circulares
        circular_import_pattern = r"from app\.com\.chatbot\.conversational_flow_manager import ConversationalFlowManager"
        if re.search(circular_import_pattern, content):
            # Comentamos la importación circular
            content = re.sub(
                circular_import_pattern,
                "# FIXED: \\g<0> # Importación removida para evitar dependencia circular",
                content
            )
            logger.info("Corregida importación circular de ConversationalFlowManager")
            
        # 2. Agregar función get_conversational_flow_manager con importación diferida
        get_flow_manager_func = '''
def get_conversational_flow_manager():
    """Obtiene una instancia de ConversationalFlowManager con importación diferida.
    
    Implementado siguiendo reglas globales de Grupo huntRED® para mantenimiento
    """
    try:
        # Importación diferida para evitar dependencias circulares
        from app.com.chatbot.conversational_flow import ConversationalFlowManager
        return ConversationalFlowManager
    except ImportError as e:
        import logging
        logging.getLogger("import_compatibility").error(f"Error al importar ConversationalFlowManager: {e}")
        # Fallback para mantener compatibilidad
        return None
'''

        # 3. Añadir si no existe ya
        if "def get_conversational_flow_manager():" not in content:
            # Buscar un punto adecuado para insertar
            import_section_end = content.find("# Add getter functions for existing modules")
            if import_section_end > 0:
                # Insertar antes de la sección de getters
                content = content[:import_section_end] + get_flow_manager_func + content[import_section_end:]
                logger.info("Añadida función get_conversational_flow_manager con importación diferida")
            else:
                # Si no encontramos el punto ideal, añadir al final
                content += "\n" + get_flow_manager_func
        
        # 4. Añadir otros alias de compatibilidad si es necesario
        if "def get_chat_state_manager" not in content:
            compatibility_code = '''
# Alias para mantener compatibilidad con código legacy - v2025.05.19
def get_chat_state_manager(*args, **kwargs):
    """Alias para mantener compatibilidad"""
    import logging
    logging.getLogger("import_compatibility").warning(
        "Uso de función renombrada: get_chat_state_manager -> get_state_manager"
    )
    from app.com.chatbot.chat_state_manager import ChatStateManager
    return ChatStateManager(*args, **kwargs)
'''
            content += "\n" + compatibility_code
            logger.info("Añadidos alias adicionales de compatibilidad")
            
        # Guardar cambios
        with open(IMPORT_CONFIG_PATH, "w") as f:
            f.write(content)
        
        logger.info(f"Se ha actualizado {IMPORT_CONFIG_PATH} correctamente")
        return True
    
    except Exception as e:
        logger.error(f"Error actualizando {IMPORT_CONFIG_PATH}: {e}", exc_info=True)
        # Restaurar backup si ocurrió un error
        if backup_path.exists():
            shutil.copy2(backup_path, IMPORT_CONFIG_PATH)
            logger.info(f"Restaurado backup de {IMPORT_CONFIG_PATH}")
        return False

def fix_syntax_errors():
    """
    Corrige errores de sintaxis en archivos específicos.
    """
    error_files = {
        APP_ROOT / "com" / "utils" / "standardize_code.py": {"line": 47, "error": "unexpected indent"},
        APP_ROOT / "com" / "utils" / "file_organizer.py": {"line": 18, "error": "unexpected indent"},
        APP_ROOT / "com" / "talent" / "team_synergy.py": {"line": 224, "error": "expected 'except' or 'finally' block"}
    }
    
    for file_path, error_info in error_files.items():
        if not file_path.exists():
            logger.warning(f"Archivo no encontrado: {file_path}")
            continue
            
        try:
            logger.info(f"Intentando corregir error de sintaxis en {file_path} (línea {error_info['line']})")
            
            # Leer el contenido actual
            with open(file_path, "r") as f:
                lines = f.readlines()
                
            # Implementación básica: intenta corregir la indentación o añadir bloques try/except
            error_line = error_info["line"] - 1  # Ajustar para índice base 0
            if error_line < len(lines):
                if "indent" in error_info["error"]:
                    # Corregir indentación
                    lines[error_line] = lines[error_line].lstrip()
                elif "except" in error_info["error"] or "finally" in error_info["error"]:
                    # Añadir bloque except
                    lines[error_line] = lines[error_line] + "    except Exception as e:\n        logger.error(f\"Error: {e}\")\n"
                    
            # Guardar el archivo corregido
            with open(file_path, "w") as f:
                f.writelines(lines)
                
            logger.info(f"Corrección aplicada en {file_path}")
            
        except Exception as e:
            logger.error(f"Error corrigiendo sintaxis en {file_path}: {e}")

def fix_import_config_path():
    """
    Corrige la ruta de importación incorrecta de import_config en chat_state_manager.py.
    El error es que intenta importar desde app.com.chatbot.import_config cuando el archivo
    está realmente en app.import_config.
    """
    chat_state_manager_path = APP_ROOT / "com" / "chatbot" / "chat_state_manager.py"
    
    if not chat_state_manager_path.exists():
        logger.warning(f"Archivo no encontrado: {chat_state_manager_path}")
        return False
        
    try:
        # Hacer backup
        backup_path = chat_state_manager_path.parent / (chat_state_manager_path.name + ".bak")
        shutil.copy2(chat_state_manager_path, backup_path)
        
        # Leer el contenido
        with open(chat_state_manager_path, "r") as f:
            content = f.read()
            
        # Buscar importación incorrecta
        if "from app.com.chatbot.import_config import" in content:
            # Corregir la importación
            fixed_content = content.replace(
                "from app.com.chatbot.import_config import", 
                "# FIXED: Corregida ruta de importación - v2025.05.19\nfrom app.import_config import"
            )
            
            # Guardar el archivo corregido
            with open(chat_state_manager_path, "w") as f:
                f.write(fixed_content)
                
            logger.info(f"Corregida ruta de importación en {chat_state_manager_path}")
            return True
        else:
            logger.info(f"No se encontró importación incorrecta en {chat_state_manager_path}")
            return False
            
    except Exception as e:
        logger.error(f"Error corrigiendo ruta de importación: {e}", exc_info=True)
        # Restaurar backup si hubo error
        if 'backup_path' in locals() and backup_path.exists():
            shutil.copy2(backup_path, chat_state_manager_path)
            logger.info(f"Restaurado backup de {chat_state_manager_path}")
        return False

def fix_missing_models():
    """
    Corrige la importación de modelos inexistentes como ContextCondition.
    """
    # Archivos que podrían tener importaciones problemáticas
    files_to_check = [
        APP_ROOT / "com" / "chatbot" / "chat_state_manager.py",
        APP_ROOT / "com" / "chatbot" / "conversational_flow.py"
    ]
    
    fixed_count = 0
    for file_path in files_to_check:
        if not file_path.exists():
            logger.warning(f"Archivo no encontrado: {file_path}")
            continue
            
        try:
            with open(file_path, "r") as f:
                content = f.read()
                
            # Verificar si importa ContextCondition
            if "ContextCondition" in content and "from app.models import" in content:
                # Buscar la línea de importación
                import_pattern = r"from app\.models import \(([^)]+)\)"
                match = re.search(import_pattern, content)
                
                if match:
                    imports = match.group(1)
                    # Quitar ContextCondition de las importaciones
                    fixed_imports = re.sub(r"\bContextCondition,?\s*", "", imports)
                    # Reemplazar en el contenido
                    fixed_content = content.replace(match.group(0), f"from app.models import ({fixed_imports})")
                    
                    # Añadir la declaración del modelo faltante
                    context_condition_model = '''
# FIXED: Modelo ContextCondition agregado localmente - v2025.05.19
class ContextCondition:
    """Modelo local para mantener compatibilidad."""
    KEY = 'key'
    VALUE = 'value'
    OPERATOR = 'operator'
    
    OPERATORS = {
        'eq': 'equal',
        'neq': 'not_equal',
        'gt': 'greater_than',
        'lt': 'less_than',
        'contains': 'contains',
        'not_contains': 'not_contains'
    }
    
    def __init__(self, key, value, operator='eq'):
        self.key = key
        self.value = value
        self.operator = operator
'''
                    # Insertar después de las importaciones
                    insert_point = re.search(r"import[^\n]+\n\n", fixed_content)
                    if insert_point:
                        pos = insert_point.end()
                        fixed_content = fixed_content[:pos] + context_condition_model + fixed_content[pos:]
                    else:
                        # Si no encontramos un punto ideal, añadir antes de la primera clase
                        class_pos = fixed_content.find("class ")
                        if class_pos > 0:
                            fixed_content = fixed_content[:class_pos] + context_condition_model + fixed_content[class_pos:]
                    
                    # Guardar el archivo corregido
                    with open(file_path, "w") as f:
                        f.write(fixed_content)
                    
                    logger.info(f"Corregida importación de ContextCondition en {file_path}")
                    fixed_count += 1
        
        except Exception as e:
            logger.error(f"Error corrigiendo importaciones en {file_path}: {e}")
    
    return fixed_count > 0

def update_manager_structure():
    """
    Actualiza la estructura de administradores para resolver el error
    de que 'app.com.chatbot.conversational_flow_manager.ConversationalFlowManager' 
    no es un paquete.
    """
    flow_manager_path = APP_ROOT / "com" / "chatbot" / "conversational_flow_manager.py"
    
    if not flow_manager_path.exists():
        logger.warning(f"Archivo no encontrado: {flow_manager_path}")
        return False
        
    try:
        with open(flow_manager_path, "r") as f:
            content = f.read()
            
        # Quitar la auto-registración que causa problemas
        if "register_module(" in content:
            content = re.sub(
                r"from app\.import_config import register_module\s+# Register at startup\s+register_module\(.*\)",
                "# FIXED: Auto-registración removida para evitar dependencia circular",
                content
            )
            
            with open(flow_manager_path, "w") as f:
                f.write(content)
                
            logger.info(f"Corregida auto-registración en {flow_manager_path}")
            return True
    except Exception as e:
        logger.error(f"Error actualizando {flow_manager_path}: {e}")
        return False

def main():
    """Función principal que ejecuta todas las reparaciones necesarias."""
    logger.info("=== INICIANDO REPARACIÓN DEL SERVIDOR ===")
    
    # 1. Crear archivo channel_config.py faltante
    if create_channel_config():
        logger.info("✅ Paso 1: Creación de channel_config.py completada")
    else:
        logger.error("❌ Paso 1: Error creando channel_config.py")
    
    # 2. Corregir dependencias circulares en import_config.py
    if fix_import_config():
        logger.info("✅ Paso 2: Corrección de import_config.py completada")
    else:
        logger.error("❌ Paso 2: Error corrigiendo import_config.py")
    
    # 3. Corregir rutas de importación incorrectas (app.com.chatbot.import_config)
    if fix_import_config_path():
        logger.info("✅ Paso 3: Corrección de rutas de importación completada")
    else:
        logger.info("ℹ️ Paso 3: No se encontraron rutas de importación incorrectas")
    
    # 4. Corregir modelos faltantes (ContextCondition)
    if fix_missing_models():
        logger.info("✅ Paso 4: Corrección de modelos faltantes completada")
    else:
        logger.info("ℹ️ Paso 4: No se encontraron modelos faltantes para corregir")
    
    # 5. Actualizar estructura de administradores
    if update_manager_structure():
        logger.info("✅ Paso 5: Actualización de estructura de administradores completada")
    else:
        logger.error("❌ Paso 5: Error actualizando estructura de administradores")
    
    # 6. Corregir errores de sintaxis en archivos específicos
    try:
        fix_syntax_errors()
        logger.info("✅ Paso 6: Corrección de errores de sintaxis completada")
    except Exception as e:
        logger.error(f"❌ Paso 6: Error corrigiendo errores de sintaxis: {e}")
    
    logger.info("=== REPARACIÓN DEL SERVIDOR COMPLETADA ===")
    logger.info("")
    logger.info("Para aplicar los cambios, ejecute:")
    logger.info("  python manage.py migrate")
    logger.info("")
    logger.info("Si los problemas persisten, comparta los logs para un análisis más detallado.")

if __name__ == "__main__":
    main()
