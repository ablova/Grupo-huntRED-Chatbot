# /home/pablo/app/com/chatbot/channel_config.py
"""
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
