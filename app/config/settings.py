"""
Configuración global del sistema.

Este módulo unifica todas las configuraciones del sistema en una única instancia
accesible globalmente. Proporciona una interfaz centralizada para acceder a la
configuración de todos los módulos.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, Type
from .base import BaseConfig, Environment
from .features.ats import ATSConfig

class Settings:
    """
    Clase singleton para la configuración global.
    
    Esta clase implementa el patrón Singleton para asegurar que solo existe
    una instancia de configuración en toda la aplicación.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._load_environment()
            self._initialize_configs()
            self._initialized = True
    
    def _load_environment(self):
        """Carga la configuración del entorno."""
        self.environment = os.getenv('DJANGO_ENV', 'development')
        self.debug = os.getenv('DEBUG', 'True').lower() == 'true'
        self.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')
        
        # Cargar variables de entorno específicas
        self.database_url = os.getenv('DATABASE_URL', 'sqlite:///db.sqlite3')
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.email_host = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
        self.email_port = int(os.getenv('EMAIL_PORT', '587'))
        self.email_host_user = os.getenv('EMAIL_HOST_USER', '')
        self.email_host_password = os.getenv('EMAIL_HOST_PASSWORD', '')
    
    def _initialize_configs(self):
        """Inicializa todas las configuraciones."""
        # Configuración base
        self.base = BaseConfig(
            environment=Environment(self.environment),
            debug=self.debug,
            secret_key=self.secret_key,
            database_url=self.database_url,
            email_host=self.email_host,
            email_port=self.email_port,
            email_host_user=self.email_host_user,
            email_host_password=self.email_host_password
        )
        
        # Configuración de ATS
        self.ats = ATSConfig(
            environment=Environment(self.environment),
            debug=self.debug,
            secret_key=self.secret_key,
            database_url=self.database_url,
            email_host=self.email_host,
            email_port=self.email_port,
            email_host_user=self.email_host_user,
            email_host_password=self.email_host_password
        )
        
        # Aquí se pueden inicializar más configuraciones específicas
        # self.ml = MLConfig(...)
        # self.api = APIConfig(...)
        # etc.
    
    def get_config(self, config_type: Type[BaseConfig]) -> Optional[BaseConfig]:
        """
        Obtiene una configuración específica por su tipo.
        
        Args:
            config_type: Tipo de configuración a obtener
            
        Returns:
            BaseConfig: Instancia de la configuración solicitada
        """
        for attr_name, attr_value in self.__dict__.items():
            if isinstance(attr_value, config_type):
                return attr_value
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte toda la configuración a un diccionario.
        
        Returns:
            Dict[str, Any]: Diccionario con toda la configuración
        """
        config_dict = {}
        for attr_name, attr_value in self.__dict__.items():
            if isinstance(attr_value, BaseConfig):
                config_dict[attr_name] = attr_value.to_dict()
            else:
                config_dict[attr_name] = attr_value
        return config_dict
    
    def update_from_dict(self, config_dict: Dict[str, Any]) -> None:
        """
        Actualiza la configuración desde un diccionario.
        
        Args:
            config_dict: Diccionario con la nueva configuración
        """
        for key, value in config_dict.items():
            if hasattr(self, key):
                current_value = getattr(self, key)
                if isinstance(current_value, BaseConfig):
                    current_value.update_from_dict(value)
                else:
                    setattr(self, key, value)
    
    def validate(self) -> bool:
        """
        Valida toda la configuración.
        
        Returns:
            bool: True si la configuración es válida
        """
        try:
            for attr_name, attr_value in self.__dict__.items():
                if isinstance(attr_value, BaseConfig):
                    attr_value.validate()
            return True
        except Exception as e:
            print(f"Error validando configuración: {str(e)}")
            return False
    
    def reload(self) -> None:
        """Recarga toda la configuración."""
        self._load_environment()
        self._initialize_configs()

# Instancia global de configuración
settings = Settings()

# Exportar la instancia global
__all__ = ['settings'] 