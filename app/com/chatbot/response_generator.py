# /home/pablo/app/com/chatbot/response_generator.py
#
# Implementación del generador de respuestas para el chatbot
# Siguiendo las reglas globales de Grupo huntRED®:
# - Code Consistency: Seguir estándares de Django
# - Modularity: Escribir código modular, reutilizable
# - No Redundancies: Verificar antes de añadir funciones que no existan en el código
#

import logging
from typing import Dict, Any, Optional, List, Union
import json
import re

# Configuración del logger
logger = logging.getLogger(__name__)

class ResponseGenerator:
    """Generador de respuestas para el chatbot.
    
    Esta clase es responsable de formatear y generar respuestas 
    basadas en el mensaje del usuario, el contexto de la conversación,
    y las plantillas disponibles.
    """
    
    def __init__(self):
        """Inicializa el generador de respuestas con plantillas vacías."""
        self.templates = {}
        self.default_format = "text"
        self.supported_formats = ["text", "markdown", "html", "json"]
        logger.info("ResponseGenerator inicializado")

    def load_templates(self, templates_path: str = None) -> None:
        """Carga plantillas desde una ruta o usa las predeterminadas.
        
        Args:
            templates_path: Ruta opcional a un archivo JSON con plantillas
        """
        try:
            if templates_path:
                with open(templates_path, 'r', encoding='utf-8') as f:
                    self.templates = json.load(f)
                logger.info(f"Plantillas cargadas desde {templates_path}")
            else:
                # Cargar plantillas predeterminadas
                self.templates = {
                    "greeting": "Hola {name}, ¿en qué puedo ayudarte hoy?",
                    "farewell": "¡Hasta pronto {name}! Fue un placer asistirte.",
                    "fallback": "Lo siento, no he entendido tu consulta. ¿Podrías reformularla?",
                    "help": "Puedo asistirte con información sobre vacantes, procesos de selección y más.",
                    "error": "Ha ocurrido un error. Por favor, intenta nuevamente más tarde."
                }
                logger.info("Plantillas predeterminadas cargadas")
        except Exception as e:
            logger.error(f"Error al cargar plantillas: {str(e)}")
            # Configurar plantillas básicas como fallback
            self.templates = {
                "fallback": "Lo siento, no he podido procesar tu solicitud.",
                "error": "Ha ocurrido un error. Por favor, intenta nuevamente."
            }

    def generate_response(self, message: str, context: Dict[str, Any]) -> str:
        """Genera una respuesta basada en el mensaje y contexto.
        
        Args:
            message: Mensaje del usuario o identificador de plantilla
            context: Contexto de la conversación con variables
            
        Returns:
            Respuesta generada
        """
        try:
            # Si el mensaje es un identificador de plantilla conocido
            if message in self.templates:
                template = self.templates[message]
                return self._format_template(template, context)
            
            # En caso contrario, generar respuesta basada en el mensaje
            return self._process_message(message, context)
        except Exception as e:
            logger.error(f"Error generando respuesta: {str(e)}")
            return self.templates.get("error", "Ha ocurrido un error al procesar tu solicitud.")

    def _format_template(self, template: str, context: Dict[str, Any]) -> str:
        """Formatea una plantilla con variables del contexto.
        
        Args:
            template: Plantilla con marcadores {variable}
            context: Diccionario con valores para las variables
            
        Returns:
            Plantilla formateada
        """
        try:
            # Extrae todas las variables necesarias de la plantilla
            variables = re.findall(r'\{([^}]+)\}', template)
            
            # Verifica si todas las variables están presentes en el contexto
            for var in variables:
                if var not in context:
                    logger.warning(f"Variable {var} no encontrada en el contexto")
                    context[var] = f"[{var} no disponible]"
            
            # Formatea la plantilla con las variables del contexto
            return template.format(**context)
        except KeyError as e:
            logger.error(f"Variable faltante en contexto: {str(e)}")
            return template  # Devuelve la plantilla sin formatear
        except Exception as e:
            logger.error(f"Error formateando plantilla: {str(e)}")
            return template  # Devuelve la plantilla sin formatear

    def _process_message(self, message: str, context: Dict[str, Any]) -> str:
        """Procesa un mensaje para generar una respuesta personalizada.
        
        Args:
            message: Mensaje a procesar
            context: Contexto de la conversación
            
        Returns:
            Respuesta generada
        """
        # Implementación básica - esto podría extenderse para usar NLP, ML, etc.
        business_unit = context.get('business_unit', 'default')
        user_name = context.get('name', 'usuario')
        
        # Lógica simple basada en palabras clave
        if any(word in message.lower() for word in ['hola', 'buenos', 'saludos']):
            return f"Hola {user_name}, bienvenido al asistente de {business_unit}. ¿En qué puedo ayudarte?"
        
        if any(word in message.lower() for word in ['adios', 'chao', 'hasta luego']):
            return f"¡Hasta pronto {user_name}! Fue un placer asistirte."
            
        if any(word in message.lower() for word in ['gracias', 'agradezco']):
            return f"¡Es un placer ayudarte, {user_name}!"
            
        if any(word in message.lower() for word in ['ayuda', 'help', 'opciones']):
            return "Puedo asistirte con información sobre vacantes, procesos de selección, y responder preguntas frecuentes."
            
        # Respuesta predeterminada si no hay coincidencias
        return self.templates.get("fallback", "¿En qué más puedo ayudarte?")

    def format_response(self, response: str, output_format: str = None) -> Union[str, Dict]:
        """Formatea la respuesta en el formato solicitado.
        
        Args:
            response: Respuesta a formatear
            output_format: Formato de salida (text, markdown, html, json)
            
        Returns:
            Respuesta formateada en el formato solicitado
        """
        format_type = output_format or self.default_format
        
        if format_type not in self.supported_formats:
            logger.warning(f"Formato no soportado: {format_type}, usando texto plano")
            format_type = "text"
            
        if format_type == "json":
            return {"response": response}
        
        if format_type == "markdown":
            # Procesamiento básico para añadir formato markdown
            return response
            
        if format_type == "html":
            # Convertir saltos de línea en <br> para HTML
            return response.replace("\n", "<br>")
            
        # Texto plano por defecto
        return response
