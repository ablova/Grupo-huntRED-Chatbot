"""
Sistema de configuración para rankings educativos.
"""
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
import yaml
import json
from pathlib import Path

class RankingSourceConfig(BaseModel):
    """Configuración de fuente de ranking."""
    
    name: str
    weight: float = Field(..., ge=0, le=1)
    url: Optional[str] = None
    api_key: Optional[str] = None
    cache_ttl: int = 86400  # 24 horas
    metrics: List[str] = Field(default_factory=list)
    
class ProgramCategoryConfig(BaseModel):
    """Configuración de categoría de programa."""
    
    name: str
    weight: float = Field(..., ge=0, le=1)
    programs: List[str] = Field(default_factory=list)
    required_metrics: List[str] = Field(default_factory=list)
    
class RankingConfig(BaseModel):
    """Configuración general de rankings."""
    
    sources: List[RankingSourceConfig] = Field(default_factory=list)
    program_categories: List[ProgramCategoryConfig] = Field(default_factory=list)
    cache_enabled: bool = True
    cache_ttl: int = 86400  # 24 horas
    validation_enabled: bool = True
    ml_enabled: bool = True
    ml_model: str = 'random_forest'
    ml_params: Dict[str, Any] = Field(default_factory=dict)
    
class RankingConfigManager:
    """Gestor de configuración de rankings."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Inicializa el gestor de configuración.
        
        Args:
            config_path: Ruta al archivo de configuración
        """
        self.config_path = config_path
        self.config = self._load_default_config()
        
        if config_path:
            self.load_config(config_path)
            
    def _load_default_config(self) -> RankingConfig:
        """
        Carga configuración por defecto.
        
        Returns:
            Configuración por defecto
        """
        return RankingConfig(
            sources=[
                RankingSourceConfig(
                    name='qs',
                    weight=0.4,
                    metrics=['academic_reputation', 'employer_reputation', 'faculty_student_ratio']
                ),
                RankingSourceConfig(
                    name='times',
                    weight=0.3,
                    metrics=['teaching', 'research', 'citations']
                ),
                RankingSourceConfig(
                    name='edurank',
                    weight=0.3,
                    metrics=['quality', 'demand', 'salary']
                )
            ],
            program_categories=[
                ProgramCategoryConfig(
                    name='engineering',
                    weight=1.0,
                    programs=['Computer Science', 'Software Engineering', 'Data Science'],
                    required_metrics=['quality', 'demand', 'salary']
                ),
                ProgramCategoryConfig(
                    name='business',
                    weight=0.9,
                    programs=['Business Administration', 'Finance', 'Marketing'],
                    required_metrics=['quality', 'demand', 'salary']
                )
            ]
        )
        
    def load_config(self, config_path: str) -> None:
        """
        Carga configuración desde archivo.
        
        Args:
            config_path: Ruta al archivo de configuración
        """
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f'Archivo de configuración no encontrado: {config_path}')
            
        if path.suffix == '.yaml':
            with open(path, 'r') as f:
                config_data = yaml.safe_load(f)
        elif path.suffix == '.json':
            with open(path, 'r') as f:
                config_data = json.load(f)
        else:
            raise ValueError('Formato de archivo no soportado')
            
        self.config = RankingConfig(**config_data)
        
    def save_config(self, config_path: Optional[str] = None) -> None:
        """
        Guarda configuración en archivo.
        
        Args:
            config_path: Ruta al archivo de configuración
        """
        path = Path(config_path or self.config_path)
        if not path:
            raise ValueError('No se especificó ruta de archivo')
            
        config_data = self.config.dict()
        
        if path.suffix == '.yaml':
            with open(path, 'w') as f:
                yaml.dump(config_data, f)
        elif path.suffix == '.json':
            with open(path, 'w') as f:
                json.dump(config_data, f, indent=2)
        else:
            raise ValueError('Formato de archivo no soportado')
            
    def get_source_config(self, source_name: str) -> Optional[RankingSourceConfig]:
        """
        Obtiene configuración de fuente.
        
        Args:
            source_name: Nombre de la fuente
            
        Returns:
            Configuración de fuente o None si no se encuentra
        """
        for source in self.config.sources:
            if source.name == source_name:
                return source
        return None
        
    def get_program_category(self, program: str) -> Optional[ProgramCategoryConfig]:
        """
        Obtiene categoría de programa.
        
        Args:
            program: Nombre del programa
            
        Returns:
            Configuración de categoría o None si no se encuentra
        """
        for category in self.config.program_categories:
            if program in category.programs:
                return category
        return None
        
    def get_required_metrics(self, program: str) -> List[str]:
        """
        Obtiene métricas requeridas para un programa.
        
        Args:
            program: Nombre del programa
            
        Returns:
            Lista de métricas requeridas
        """
        category = self.get_program_category(program)
        if category:
            return category.required_metrics
        return []
        
    def get_source_weight(self, source_name: str) -> float:
        """
        Obtiene peso de fuente.
        
        Args:
            source_name: Nombre de la fuente
            
        Returns:
            Peso de la fuente
        """
        source = self.get_source_config(source_name)
        if source:
            return source.weight
        return 0.0
        
    def get_program_weight(self, program: str) -> float:
        """
        Obtiene peso de programa.
        
        Args:
            program: Nombre del programa
            
        Returns:
            Peso del programa
        """
        category = self.get_program_category(program)
        if category:
            return category.weight
        return 0.8  # Peso por defecto
        
    def update_source_config(self,
                           source_name: str,
                           config: Dict[str, Any]) -> None:
        """
        Actualiza configuración de fuente.
        
        Args:
            source_name: Nombre de la fuente
            config: Nueva configuración
        """
        for i, source in enumerate(self.config.sources):
            if source.name == source_name:
                self.config.sources[i] = RankingSourceConfig(**config)
                return
                
        # Si no existe, agregar nueva fuente
        self.config.sources.append(RankingSourceConfig(**config))
        
    def update_program_category(self,
                              category_name: str,
                              config: Dict[str, Any]) -> None:
        """
        Actualiza configuración de categoría.
        
        Args:
            category_name: Nombre de la categoría
            config: Nueva configuración
        """
        for i, category in enumerate(self.config.program_categories):
            if category.name == category_name:
                self.config.program_categories[i] = ProgramCategoryConfig(**config)
                return
                
        # Si no existe, agregar nueva categoría
        self.config.program_categories.append(ProgramCategoryConfig(**config))
        
    def get_ml_config(self) -> Dict[str, Any]:
        """
        Obtiene configuración de ML.
        
        Returns:
            Configuración de ML
        """
        return {
            'enabled': self.config.ml_enabled,
            'model': self.config.ml_model,
            'params': self.config.ml_params
        }
        
    def update_ml_config(self, config: Dict[str, Any]) -> None:
        """
        Actualiza configuración de ML.
        
        Args:
            config: Nueva configuración
        """
        self.config.ml_enabled = config.get('enabled', True)
        self.config.ml_model = config.get('model', 'random_forest')
        self.config.ml_params = config.get('params', {}) 