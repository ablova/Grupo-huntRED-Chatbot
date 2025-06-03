"""
Configuración base del sistema.

Este módulo define la estructura base de configuración para toda la aplicación.
Utiliza un sistema de configuración basado en clases con validación de tipos
y valores por defecto.
"""

from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import os
from dataclasses import dataclass, field
from enum import Enum
import json
import yaml

class Environment(Enum):
    """Entornos disponibles."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"

@dataclass
class BaseConfig:
    """Configuración base con validación y valores por defecto."""
    
    # Entorno actual
    environment: Environment = Environment.DEVELOPMENT
    
    # Directorios base
    base_dir: Path = Path(__file__).resolve().parent.parent
    data_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data")
    logs_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "logs")
    temp_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "temp")
    
    # Configuración de logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: str = "app.log"
    
    # Configuración de caché
    cache_enabled: bool = True
    cache_timeout: int = 300  # 5 minutos
    cache_prefix: str = "huntred_"
    
    # Configuración de seguridad
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    debug: bool = False
    allowed_hosts: List[str] = field(default_factory=lambda: ["localhost", "127.0.0.1"])
    
    # Configuración de base de datos
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///db.sqlite3")
    
    # Configuración de API
    api_version: str = "v1"
    api_prefix: str = "/api"
    api_timeout: int = 30
    
    # Configuración de correo
    email_host: str = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    email_port: int = int(os.getenv("EMAIL_PORT", "587"))
    email_use_tls: bool = True
    email_host_user: str = os.getenv("EMAIL_HOST_USER", "")
    email_host_password: str = os.getenv("EMAIL_HOST_PASSWORD", "")
    
    def __post_init__(self):
        """Validación post-inicialización."""
        self._validate_paths()
        self._create_directories()
        self._validate_security()
    
    def _validate_paths(self):
        """Valida que los directorios existan."""
        for path in [self.base_dir, self.data_dir, self.logs_dir, self.temp_dir]:
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
    
    def _create_directories(self):
        """Crea los directorios necesarios."""
        for path in [self.data_dir, self.logs_dir, self.temp_dir]:
            path.mkdir(parents=True, exist_ok=True)
    
    def _validate_security(self):
        """Valida la configuración de seguridad."""
        if self.environment == Environment.PRODUCTION:
            if self.debug:
                raise ValueError("Debug no puede estar activado en producción")
            if not self.secret_key or self.secret_key == "your-secret-key-here":
                raise ValueError("Se requiere una SECRET_KEY válida en producción")
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'BaseConfig':
        """Crea una instancia desde un diccionario."""
        return cls(**config_dict)
    
    @classmethod
    def from_json(cls, json_path: Union[str, Path]) -> 'BaseConfig':
        """Crea una instancia desde un archivo JSON."""
        with open(json_path, 'r') as f:
            config_dict = json.load(f)
        return cls.from_dict(config_dict)
    
    @classmethod
    def from_yaml(cls, yaml_path: Union[str, Path]) -> 'BaseConfig':
        """Crea una instancia desde un archivo YAML."""
        with open(yaml_path, 'r') as f:
            config_dict = yaml.safe_load(f)
        return cls.from_dict(config_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la configuración a un diccionario."""
        return {
            'environment': self.environment.value,
            'base_dir': str(self.base_dir),
            'data_dir': str(self.data_dir),
            'logs_dir': str(self.logs_dir),
            'temp_dir': str(self.temp_dir),
            'log_level': self.log_level,
            'log_format': self.log_format,
            'log_file': self.log_file,
            'cache_enabled': self.cache_enabled,
            'cache_timeout': self.cache_timeout,
            'cache_prefix': self.cache_prefix,
            'secret_key': self.secret_key,
            'debug': self.debug,
            'allowed_hosts': self.allowed_hosts,
            'database_url': self.database_url,
            'api_version': self.api_version,
            'api_prefix': self.api_prefix,
            'api_timeout': self.api_timeout,
            'email_host': self.email_host,
            'email_port': self.email_port,
            'email_use_tls': self.email_use_tls,
            'email_host_user': self.email_host_user,
            'email_host_password': self.email_host_password
        }
    
    def to_json(self, json_path: Union[str, Path]) -> None:
        """Guarda la configuración en un archivo JSON."""
        with open(json_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=4)
    
    def to_yaml(self, yaml_path: Union[str, Path]) -> None:
        """Guarda la configuración en un archivo YAML."""
        with open(yaml_path, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)
    
    def get_log_path(self) -> Path:
        """Obtiene la ruta del archivo de log."""
        return self.logs_dir / self.log_file
    
    def get_temp_path(self, filename: str) -> Path:
        """Obtiene la ruta de un archivo temporal."""
        return self.temp_dir / filename
    
    def get_data_path(self, filename: str) -> Path:
        """Obtiene la ruta de un archivo de datos."""
        return self.data_dir / filename 