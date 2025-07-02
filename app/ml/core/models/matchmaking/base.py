# app/ml/core/models/matchmaking/base.py
"""
Clase base para el sistema de matchmaking.
"""
from typing import Dict, List, Optional, Any, Type
import numpy as np
from abc import ABC, abstractmethod

class BaseFactor(ABC):
    """Factor base para el sistema de matchmaking."""
    
    def __init__(self, name: str):
        """
        Inicializa el factor.
        
        Args:
            name: Nombre del factor
        """
        self.name = name
        
    @abstractmethod
    def calculate_score(self,
                       candidate_data: Dict[str, Any],
                       job_data: Dict[str, Any]) -> float:
        """
        Calcula el score del factor.
        
        Args:
            candidate_data: Datos del candidato
            job_data: Datos del trabajo
            
        Returns:
            Score del factor (0-1)
        """
        pass
        
    @abstractmethod
    def get_analysis(self,
                    candidate_data: Dict[str, Any],
                    job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtiene análisis detallado.
        
        Args:
            candidate_data: Datos del candidato
            job_data: Datos del trabajo
            
        Returns:
            Análisis detallado
        """
        pass

class MatchmakingPipeline:
    """Pipeline de matchmaking."""
    
    def __init__(self):
        """Inicializa el pipeline."""
        self.factors: List[BaseFactor] = []
        
    def register_factor(self, factor: BaseFactor) -> None:
        """
        Registra un factor en el pipeline.
        
        Args:
            factor: Factor a registrar
        """
        self.factors.append(factor)
        
    def unregister_factor(self, factor_name: str) -> None:
        """
        Elimina un factor del pipeline.
        
        Args:
            factor_name: Nombre del factor a eliminar
        """
        self.factors = [f for f in self.factors if f.name != factor_name]
        
    def get_factor(self, factor_name: str) -> Optional[BaseFactor]:
        """
        Obtiene un factor por nombre.
        
        Args:
            factor_name: Nombre del factor
            
        Returns:
            Factor encontrado o None
        """
        for factor in self.factors:
            if factor.name == factor_name:
                return factor
        return None
        
    def calculate_match_score(self,
                            candidate_data: Dict[str, Any],
                            job_data: Dict[str, Any]) -> float:
        """
        Calcula el score de match.
        
        Args:
            candidate_data: Datos del candidato
            job_data: Datos del trabajo
            
        Returns:
            Score de match (0-1)
        """
        if not self.factors:
            return 0.0
            
        scores: List[float] = []
        for factor in self.factors:
            score = factor.calculate_score(candidate_data, job_data)
            scores.append(score)
            
        return float(np.mean(scores))
        
    def get_detailed_analysis(self,
                            candidate_data: Dict[str, Any],
                            job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtiene análisis detallado.
        
        Args:
            candidate_data: Datos del candidato
            job_data: Datos del trabajo
            
        Returns:
            Análisis detallado
        """
        if not self.factors:
            return {
                'score': 0.0,
                'factors': {}
            }
            
        factor_analyses: Dict[str, Dict[str, Any]] = {}
        for factor in self.factors:
            analysis = factor.get_analysis(candidate_data, job_data)
            factor_analyses[factor.name] = analysis
            
        return {
            'score': self.calculate_match_score(candidate_data, job_data),
            'factors': factor_analyses
        } 