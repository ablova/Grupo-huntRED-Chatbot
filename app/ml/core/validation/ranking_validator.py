"""
Sistema de validación para rankings educativos.
"""
from typing import Dict, List, Optional, Any, Union
import numpy as np
from datetime import datetime
import json
from pydantic import BaseModel, validator, Field

class RankingData(BaseModel):
    """Modelo de datos para rankings."""
    
    university: str
    rank: int = Field(..., gt=0)
    score: float = Field(..., ge=0, le=100)
    program: Optional[str] = None
    source: str
    timestamp: datetime
    metrics: Dict[str, float] = Field(default_factory=dict)
    
    @validator('score')
    def validate_score(cls, v):
        """Valida que el score esté en el rango correcto."""
        if not 0 <= v <= 100:
            raise ValueError('Score debe estar entre 0 y 100')
        return v
        
    @validator('rank')
    def validate_rank(cls, v):
        """Valida que el ranking sea positivo."""
        if v <= 0:
            raise ValueError('Ranking debe ser positivo')
        return v
        
class RankingValidator:
    """Sistema de validación para rankings educativos."""
    
    def __init__(self):
        """Inicializa el validador."""
        self.validation_history: List[Dict[str, Any]] = []
        
    def validate_ranking_data(self,
                            data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida datos de ranking.
        
        Args:
            data: Diccionario con datos de ranking
            
        Returns:
            Diccionario con resultados de validación
        """
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Validar estructura básica
            required_fields = ['university', 'rank', 'score', 'source']
            for field in required_fields:
                if field not in data:
                    validation_result['is_valid'] = False
                    validation_result['errors'].append(f'Campo requerido faltante: {field}')
                    
            # Validar tipos de datos
            if 'rank' in data and not isinstance(data['rank'], int):
                validation_result['is_valid'] = False
                validation_result['errors'].append('Ranking debe ser un entero')
                
            if 'score' in data and not isinstance(data['score'], (int, float)):
                validation_result['is_valid'] = False
                validation_result['errors'].append('Score debe ser un número')
                
            # Validar rangos
            if 'rank' in data and data['rank'] <= 0:
                validation_result['is_valid'] = False
                validation_result['errors'].append('Ranking debe ser positivo')
                
            if 'score' in data and not 0 <= data['score'] <= 100:
                validation_result['is_valid'] = False
                validation_result['errors'].append('Score debe estar entre 0 y 100')
                
            # Validar métricas
            if 'metrics' in data:
                if not isinstance(data['metrics'], dict):
                    validation_result['is_valid'] = False
                    validation_result['errors'].append('Métricas debe ser un diccionario')
                else:
                    for key, value in data['metrics'].items():
                        if not isinstance(value, (int, float)):
                            validation_result['is_valid'] = False
                            validation_result['errors'].append(f'Métrica {key} debe ser un número')
                            
            # Validar timestamp
            if 'timestamp' in data:
                try:
                    datetime.fromisoformat(data['timestamp'])
                except:
                    validation_result['is_valid'] = False
                    validation_result['errors'].append('Timestamp inválido')
                    
            # Validar fuente
            valid_sources = ['qs', 'times', 'edurank']
            if 'source' in data and data['source'] not in valid_sources:
                validation_result['warnings'].append(f'Fuente desconocida: {data["source"]}')
                
        except Exception as e:
            validation_result['is_valid'] = False
            validation_result['errors'].append(f'Error en validación: {str(e)}')
            
        # Guardar en historial
        validation_result['timestamp'] = datetime.now().isoformat()
        validation_result['data'] = data
        self.validation_history.append(validation_result)
        
        return validation_result
        
    def validate_program_data(self,
                            data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida datos de programa.
        
        Args:
            data: Diccionario con datos de programa
            
        Returns:
            Diccionario con resultados de validación
        """
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Validar estructura básica
            required_fields = ['program', 'university', 'rank', 'score']
            for field in required_fields:
                if field not in data:
                    validation_result['is_valid'] = False
                    validation_result['errors'].append(f'Campo requerido faltante: {field}')
                    
            # Validar tipos de datos
            if 'rank' in data and not isinstance(data['rank'], int):
                validation_result['is_valid'] = False
                validation_result['errors'].append('Ranking debe ser un entero')
                
            if 'score' in data and not isinstance(data['score'], (int, float)):
                validation_result['is_valid'] = False
                validation_result['errors'].append('Score debe ser un número')
                
            # Validar rangos
            if 'rank' in data and data['rank'] <= 0:
                validation_result['is_valid'] = False
                validation_result['errors'].append('Ranking debe ser positivo')
                
            if 'score' in data and not 0 <= data['score'] <= 100:
                validation_result['is_valid'] = False
                validation_result['errors'].append('Score debe estar entre 0 y 100')
                
            # Validar métricas específicas de programa
            if 'metrics' in data:
                required_metrics = ['quality', 'demand', 'salary']
                for metric in required_metrics:
                    if metric not in data['metrics']:
                        validation_result['warnings'].append(f'Métrica requerida faltante: {metric}')
                        
        except Exception as e:
            validation_result['is_valid'] = False
            validation_result['errors'].append(f'Error en validación: {str(e)}')
            
        # Guardar en historial
        validation_result['timestamp'] = datetime.now().isoformat()
        validation_result['data'] = data
        self.validation_history.append(validation_result)
        
        return validation_result
        
    def validate_university_data(self,
                               data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida datos de universidad.
        
        Args:
            data: Diccionario con datos de universidad
            
        Returns:
            Diccionario con resultados de validación
        """
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Validar estructura básica
            required_fields = ['university', 'country', 'rank', 'score']
            for field in required_fields:
                if field not in data:
                    validation_result['is_valid'] = False
                    validation_result['errors'].append(f'Campo requerido faltante: {field}')
                    
            # Validar tipos de datos
            if 'rank' in data and not isinstance(data['rank'], int):
                validation_result['is_valid'] = False
                validation_result['errors'].append('Ranking debe ser un entero')
                
            if 'score' in data and not isinstance(data['score'], (int, float)):
                validation_result['is_valid'] = False
                validation_result['errors'].append('Score debe ser un número')
                
            # Validar rangos
            if 'rank' in data and data['rank'] <= 0:
                validation_result['is_valid'] = False
                validation_result['errors'].append('Ranking debe ser positivo')
                
            if 'score' in data and not 0 <= data['score'] <= 100:
                validation_result['is_valid'] = False
                validation_result['errors'].append('Score debe estar entre 0 y 100')
                
            # Validar métricas específicas de universidad
            if 'metrics' in data:
                required_metrics = [
                    'faculty_student_ratio',
                    'international_faculty',
                    'international_students',
                    'citations',
                    'employer_reputation',
                    'academic_reputation'
                ]
                for metric in required_metrics:
                    if metric not in data['metrics']:
                        validation_result['warnings'].append(f'Métrica requerida faltante: {metric}')
                        
        except Exception as e:
            validation_result['is_valid'] = False
            validation_result['errors'].append(f'Error en validación: {str(e)}')
            
        # Guardar en historial
        validation_result['timestamp'] = datetime.now().isoformat()
        validation_result['data'] = data
        self.validation_history.append(validation_result)
        
        return validation_result
        
    def get_validation_history(self,
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Obtiene historial de validaciones.
        
        Args:
            start_date: Fecha de inicio (opcional)
            end_date: Fecha de fin (opcional)
            
        Returns:
            Lista de validaciones
        """
        if not start_date and not end_date:
            return self.validation_history
            
        filtered_validations = []
        for validation in self.validation_history:
            timestamp = datetime.fromisoformat(validation['timestamp'])
            if start_date and timestamp < start_date:
                continue
            if end_date and timestamp > end_date:
                continue
            filtered_validations.append(validation)
            
        return filtered_validations
        
    def get_validation_summary(self,
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Obtiene resumen de validaciones.
        
        Args:
            start_date: Fecha de inicio (opcional)
            end_date: Fecha de fin (opcional)
            
        Returns:
            Diccionario con resumen de validaciones
        """
        validations = self.get_validation_history(start_date, end_date)
        
        if not validations:
            return {}
            
        summary = {
            'total_validations': len(validations),
            'valid_count': sum(1 for v in validations if v['is_valid']),
            'invalid_count': sum(1 for v in validations if not v['is_valid']),
            'error_types': {},
            'warning_types': {}
        }
        
        # Contar tipos de errores y advertencias
        for validation in validations:
            for error in validation['errors']:
                summary['error_types'][error] = summary['error_types'].get(error, 0) + 1
            for warning in validation['warnings']:
                summary['warning_types'][warning] = summary['warning_types'].get(warning, 0) + 1
                
        return summary
        
    def export_validations(self,
                          file_path: str,
                          format: str = 'csv') -> None:
        """
        Exporta validaciones a archivo.
        
        Args:
            file_path: Ruta del archivo
            format: Formato de exportación ('csv' o 'json')
        """
        if format == 'csv':
            df = pd.DataFrame(self.validation_history)
            df.to_csv(file_path, index=False)
        elif format == 'json':
            with open(file_path, 'w') as f:
                json.dump(self.validation_history, f) 