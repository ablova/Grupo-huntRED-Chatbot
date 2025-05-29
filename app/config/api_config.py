"""
Configuración centralizada para APIs externas.

Este módulo proporciona una configuración centralizada para todas las APIs externas
utilizadas en la aplicación, incluyendo LinkedIn, OpenAI y otros servicios.
"""

from django.conf import settings
from typing import Dict, Any, Optional
import os
import logging

logger = logging.getLogger(__name__)

class BaseAPIConfig:
    """Clase base para la configuración de APIs."""
    
    def __init__(self, config_key: str):
        """Inicializa la configuración con la clave especificada."""
        self.config_key = config_key
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Carga la configuración desde settings o usa valores por defecto."""
        return getattr(settings, f"{self.config_key}_CONFIG", {})
    
    def get(self, key: str, default: Any = None) -> Any:
        """Obtiene un valor de configuración."""
        return self._config.get(key, default)
    
    def is_enabled(self) -> bool:
        """Verifica si la API está habilitada."""
        return self._config.get('ENABLED', False)


class LinkedInAPIConfig(BaseAPIConfig):
    """Configuración específica para la API de LinkedIn."""
    
    def __init__(self):
        super().__init__('LINKEDIN')
        
        # Configuración de autenticación
        self.username = self._get_setting('USERNAME')
        self.password = self._get_setting('PASSWORD')
        self.api_key = self._get_setting('API_KEY')
        
        # Límites y control de tasa
        self.rate_limit = self.get('RATE_LIMIT', 5)  # solicitudes/minuto
        self.request_timeout = self.get('REQUEST_TIMEOUT', 30)  # segundos
        
        # Configuración de scraping
        self.scrape_timeout = self.get('SCRAPE_TIMEOUT', 120)  # segundos
        self.max_retries = self.get('MAX_RETRIES', 3)
        self.retry_delay = self.get('RETRY_DELAY', 5)  # segundos
        
        # Almacenamiento de sesión
        self.session_dir = self.get('SESSION_DIR', os.path.join(settings.BASE_DIR, '.linkedin_sessions'))
        self.cookies_file = os.path.join(self.session_dir, 'cookies.json')
        
        # Asegurar que exista el directorio de sesión
        os.makedirs(self.session_dir, exist_ok=True)
    
    def _get_setting(self, key: str) -> str:
        """Obtiene un valor de configuración con manejo de errores."""
        value = self._config.get(key)
        if not value:
            env_key = f"LINKEDIN_{key}"
            value = os.getenv(env_key)
            if not value:
                logger.warning(f"Advertencia: {env_key} no está configurado")
        return value or ''


class OpenAIConfig(BaseAPIConfig):
    """Configuración para la API de OpenAI."""
    
    def __init__(self):
        super().__init__('OPENAI')
        self.api_key = self._get_setting('API_KEY')
        self.model = self._get_setting('MODEL', 'gpt-4')
        self.temperature = float(self._config.get('TEMPERATURE', 0.7))
        self.max_tokens = int(self._config.get('MAX_TOKENS', 1000))
    
    def _get_setting(self, key: str, default: Optional[str] = None) -> str:
        """Obtiene un valor de configuración."""
        value = self._config.get(key, os.getenv(f'OPENAI_{key}'))
        if not value and default is None:
            logger.warning(f"Advertencia: OPENAI_{key} no está configurado")
        return value or default or ''


# Instancias de configuración para importación
LINKEDIN_CONFIG = LinkedInAPIConfig()
OPENAI_CONFIG = OpenAIConfig()

# Configuración de APIs
def get_api_config(api_name: str) -> Dict[str, Any]:
    """Obtiene la configuración de una API específica."""
    if api_name.upper() == 'LINKEDIN':
        return LINKEDIN_CONFIG
    elif api_name.upper() == 'OPENAI':
        return OPENAI_CONFIG
    else:
        raise ValueError(f"API no soportada: {api_name}")

# Configuración de la API (mantenida por compatibilidad)
API_CONFIG = {
    'AOMNI_AI': {
        'ENABLED': False,
        'CATEGORIES': {
            'AI': {
                'ENDPOINT': None,
                'FIELDS': [
                    'company_info',
                    'strategies',
                    'value_propositions',
                    'success_factors'
                ]
            }
        }
    },
    'LINKEDIN': {
        'ENABLED': LINKEDIN_CONFIG.is_enabled(),
        'PROFILE_LIMIT': 30000,
        'FIELDS': [
            'profile_info',
            'connections',
            'skills',
            'experience'
        ]
    },
    'CHATBOT': {
        'ENABLED': True,
        'FIELDS': [
            'company_interests',
            'contact_preferences',
            'business_needs'
        ]
    }
}
