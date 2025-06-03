"""
Cargador de datos para modelos de ML.

Este módulo proporciona funcionalidades para cargar y preparar datos
para el entrenamiento de modelos de ML.
"""
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from typing import Optional, Dict, Any
import json

logger = logging.getLogger(__name__)

class DataLoader:
    """
    Clase para cargar y preparar datos de entrenamiento.
    """
    
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent.parent.parent / "data"
        
    def load_cultural_data(self) -> Optional[pd.DataFrame]:
        """
        Carga datos históricos de compatibilidad cultural.
        
        Returns:
            DataFrame con los datos o None si hay error
        """
        try:
            # Cargar datos de evaluación cultural
            cultural_data_path = self.data_dir / "cultural" / "evaluations.json"
            
            if not cultural_data_path.exists():
                logger.warning(f"No se encontró el archivo {cultural_data_path}")
                return None
                
            with open(cultural_data_path, 'r') as f:
                data = json.load(f)
                
            # Convertir a DataFrame
            records = []
            for evaluation in data:
                record = {
                    'innovation': evaluation['dimensions']['innovation'],
                    'collaboration': evaluation['dimensions']['collaboration'],
                    'adaptability': evaluation['dimensions']['adaptability'],
                    'results_orientation': evaluation['dimensions']['results_orientation'],
                    'customer_focus': evaluation['dimensions']['customer_focus'],
                    'integrity': evaluation['dimensions']['integrity'],
                    'diversity': evaluation['dimensions']['diversity'],
                    'learning': evaluation['dimensions']['learning'],
                    'compatibility_score': evaluation['compatibility_score']
                }
                records.append(record)
                
            df = pd.DataFrame(records)
            
            # Validar datos
            if df.isnull().any().any():
                logger.warning("Se encontraron valores nulos en los datos")
                df = df.fillna(df.mean())
                
            return df
            
        except Exception as e:
            logger.error(f"Error al cargar datos culturales: {str(e)}")
            return None
            
    def load_personality_data(self) -> Optional[pd.DataFrame]:
        """
        Carga datos históricos de evaluación de personalidad.
        
        Returns:
            DataFrame con los datos o None si hay error
        """
        try:
            # Cargar datos de evaluación de personalidad
            personality_data_path = self.data_dir / "personality" / "evaluations.json"
            
            if not personality_data_path.exists():
                logger.warning(f"No se encontró el archivo {personality_data_path}")
                return None
                
            with open(personality_data_path, 'r') as f:
                data = json.load(f)
                
            # Convertir a DataFrame
            records = []
            for evaluation in data:
                record = {
                    'extraversion': evaluation['traits']['extraversion'],
                    'agreeableness': evaluation['traits']['agreeableness'],
                    'conscientiousness': evaluation['traits']['conscientiousness'],
                    'emotional_stability': evaluation['traits']['emotional_stability'],
                    'openness': evaluation['traits']['openness'],
                    'success_score': evaluation['success_score']
                }
                records.append(record)
                
            df = pd.DataFrame(records)
            
            # Validar datos
            if df.isnull().any().any():
                logger.warning("Se encontraron valores nulos en los datos")
                df = df.fillna(df.mean())
                
            return df
            
        except Exception as e:
            logger.error(f"Error al cargar datos de personalidad: {str(e)}")
            return None
            
    def load_professional_data(self) -> Optional[pd.DataFrame]:
        """
        Carga datos históricos de evaluación profesional.
        
        Returns:
            DataFrame con los datos o None si hay error
        """
        try:
            # Cargar datos de evaluación profesional
            professional_data_path = self.data_dir / "professional" / "evaluations.json"
            
            if not professional_data_path.exists():
                logger.warning(f"No se encontró el archivo {professional_data_path}")
                return None
                
            with open(professional_data_path, 'r') as f:
                data = json.load(f)
                
            # Convertir a DataFrame
            records = []
            for evaluation in data:
                record = {
                    'leadership': evaluation['dimensions']['leadership'],
                    'innovation': evaluation['dimensions']['innovation'],
                    'emotional_intelligence': evaluation['dimensions']['emotional_intelligence'],
                    'strategic_thinking': evaluation['dimensions']['strategic_thinking'],
                    'execution': evaluation['dimensions']['execution'],
                    'success_score': evaluation['success_score']
                }
                records.append(record)
                
            df = pd.DataFrame(records)
            
            # Validar datos
            if df.isnull().any().any():
                logger.warning("Se encontraron valores nulos en los datos")
                df = df.fillna(df.mean())
                
            return df
            
        except Exception as e:
            logger.error(f"Error al cargar datos profesionales: {str(e)}")
            return None
            
    def save_evaluation(self, 
                       evaluation_type: str,
                       evaluation_data: Dict[str, Any]) -> bool:
        """
        Guarda una nueva evaluación en el archivo correspondiente.
        
        Args:
            evaluation_type: Tipo de evaluación ('cultural', 'personality', 'professional')
            evaluation_data: Datos de la evaluación
            
        Returns:
            True si se guardó exitosamente, False en caso contrario
        """
        try:
            # Determinar ruta del archivo
            data_path = self.data_dir / evaluation_type / "evaluations.json"
            
            # Crear directorio si no existe
            data_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Cargar datos existentes
            if data_path.exists():
                with open(data_path, 'r') as f:
                    data = json.load(f)
            else:
                data = []
                
            # Añadir nueva evaluación
            data.append(evaluation_data)
            
            # Guardar datos actualizados
            with open(data_path, 'w') as f:
                json.dump(data, f, indent=2)
                
            return True
            
        except Exception as e:
            logger.error(f"Error al guardar evaluación {evaluation_type}: {str(e)}")
            return False 