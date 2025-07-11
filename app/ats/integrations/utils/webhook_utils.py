# app/ats/integrations/utils/webhook_utils.py
"""
Utilidades para manejo de webhooks en integraciones.
"""

import json
import logging
from typing import Dict, Any, Optional, Union

logger = logging.getLogger(__name__)

def format_webhook_payload(
    payload: Dict[str, Any], 
    integration_type: str, 
    event_type: Optional[str] = None,
    include_metadata: bool = True
) -> Dict[str, Any]:
    """
    Formatea un payload para webhooks según el tipo de integración.
    
    Args:
        payload: Diccionario con los datos a enviar
        integration_type: Tipo de integración (ej. 'slack', 'teams', 'zapier')
        event_type: Tipo de evento (opcional)
        include_metadata: Si se debe incluir metadatos adicionales
        
    Returns:
        Diccionario formateado según los requisitos de la integración
    """
    formatted_payload = payload.copy()
    
    # Añadir metadatos si se solicita
    if include_metadata:
        from datetime import datetime
        formatted_payload["_metadata"] = {
            "timestamp": datetime.now().isoformat(),
            "integration": integration_type,
            "event_type": event_type,
            "version": "1.0"
        }
    
    # Formateo específico según el tipo de integración
    if integration_type.lower() == "slack":
        # Formato específico para Slack
        if "message" in formatted_payload:
            formatted_payload["text"] = formatted_payload.pop("message")
        
        # Convertir datos complejos a bloques de Slack si es necesario
        if "data" in formatted_payload and isinstance(formatted_payload["data"], dict):
            blocks = []
            for key, value in formatted_payload["data"].items():
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{key}*: {value}"
                    }
                })
            if blocks:
                formatted_payload["blocks"] = blocks
    
    elif integration_type.lower() == "teams":
        # Formato específico para Microsoft Teams
        if "message" in formatted_payload:
            formatted_payload["title"] = formatted_payload.pop("message")
        
        # Convertir a formato de tarjeta adaptativa de Teams
        if "data" in formatted_payload and isinstance(formatted_payload["data"], dict):
            formatted_payload["sections"] = []
            for key, value in formatted_payload["data"].items():
                formatted_payload["sections"].append({
                    "activityTitle": key,
                    "activitySubtitle": str(value)
                })
    
    elif integration_type.lower() in ["zapier", "webhook"]:
        # Para Zapier y webhooks genéricos, mantener estructura plana
        pass
    
    # Registrar la operación
    logger.debug(f"Payload formateado para {integration_type}: {json.dumps(formatted_payload)[:200]}...")
    
    return formatted_payload

def parse_webhook_payload(raw_payload: Union[str, Dict[str, Any]], integration_type: str) -> Dict[str, Any]:
    """
    Parsea un payload recibido de un webhook según el tipo de integración.
    
    Args:
        raw_payload: Payload en formato string o diccionario
        integration_type: Tipo de integración (ej. 'slack', 'teams', 'zapier')
        
    Returns:
        Diccionario con los datos parseados en formato estándar
    """
    # Convertir string a diccionario si es necesario
    if isinstance(raw_payload, str):
        try:
            payload = json.loads(raw_payload)
        except json.JSONDecodeError:
            logger.error(f"Error al decodificar payload: {raw_payload[:100]}...")
            return {"error": "Invalid JSON payload"}
    else:
        payload = raw_payload
    
    parsed_payload = {}
    
    # Parseo específico según el tipo de integración
    if integration_type.lower() == "slack":
        parsed_payload["message"] = payload.get("text", "")
        parsed_payload["user"] = payload.get("user_name", payload.get("user_id", ""))
        parsed_payload["channel"] = payload.get("channel_name", payload.get("channel_id", ""))
        
    elif integration_type.lower() == "teams":
        parsed_payload["message"] = payload.get("title", payload.get("text", ""))
        parsed_payload["user"] = payload.get("from", {}).get("name", "")
        
    elif integration_type.lower() in ["zapier", "webhook"]:
        # Para Zapier y webhooks genéricos, mantener estructura original
        parsed_payload = payload
    
    # Extraer metadatos si existen
    if "_metadata" in payload:
        parsed_payload["_metadata"] = payload["_metadata"]
    
    return parsed_payload
