"""
Analizador mejorado de matchmaking.
Analiza y evalúa matches entre candidatos y vacantes.
"""
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

from app.ml.analyzers.matchmaking_analyzer import MatchmakingAnalyzer
from app.ml.core.models.matchmaking.factors_model import FactorsMatchmakingModel
from app.ml.core.utils.matchmaking import _get_ml_utils

logger = logging.getLogger(__name__)

class EnhancedMatchmakingAnalyzer:
    """Analizador mejorado de matchmaking."""
    
    def __init__(self):
        self.analyzer = MatchmakingAnalyzer()
        self.model = FactorsMatchmakingModel()
        self.ml_utils = _get_ml_utils()
        
    async def analyze_match(
        self,
        candidate_data: Dict,
        job_data: Dict,
        business_unit: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analiza un match entre candidato y vacante.
        
        Args:
            candidate_data: Datos del candidato
            job_data: Datos de la vacante
            business_unit: Unidad de negocio (opcional)
            
        Returns:
            Dict con resultados del análisis
        """
        try:
            # 1. Análisis base
            base_analysis = await self.analyzer.analyze_match(
                candidate_data,
                job_data,
                business_unit
            )
            
            # 2. Análisis de ML
            ml_analysis = await self._analyze_with_ml(
                candidate_data,
                job_data,
                business_unit
            )
            
            # 3. Combinar resultados
            match_score = self._combine_scores(
                base_analysis['match_score'],
                ml_analysis['match_score']
            )
            
            # 4. Generar reporte
            report = self._generate_report(
                base_analysis,
                ml_analysis,
                match_score
            )
            
            # 5. Generar insights
            insights = self._generate_insights(
                base_analysis,
                ml_analysis,
                match_score
            )
            
            return {
                'match_score': match_score,
                'report': report,
                'insights': insights,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error en análisis de match: {str(e)}")
            raise
            
    async def _analyze_with_ml(
        self,
        candidate_data: Dict,
        job_data: Dict,
        business_unit: Optional[str]
    ) -> Dict[str, Any]:
        """Realiza análisis usando modelos de ML."""
        try:
            # 1. Preparar datos
            candidate_features = self._prepare_candidate_features(candidate_data)
            job_features = self._prepare_job_features(job_data)
            
            # 2. Obtener predicción
            match_probability = self.model.predict_proba([
                (candidate_features, job_features)
            ])[0]
            
            # 3. Obtener explicación
            explanation = self.ml_utils.explain_prediction(
                candidate_features,
                job_features,
                match_probability
            )
            
            return {
                'match_score': float(match_probability),
                'explanation': explanation
            }
            
        except Exception as e:
            logger.error(f"Error en análisis ML: {str(e)}")
            return {
                'match_score': 0.0,
                'explanation': {}
            }
            
    def _prepare_candidate_features(self, candidate_data: Dict) -> Dict:
        """Prepara features del candidato para ML."""
        return {
            'skills': candidate_data.get('skills', []),
            'experience': candidate_data.get('experience', {}),
            'personality': candidate_data.get('personality', {}),
            'metadata': candidate_data.get('metadata', {})
        }
        
    def _prepare_job_features(self, job_data: Dict) -> Dict:
        """Prepara features de la vacante para ML."""
        return {
            'requirements': job_data.get('requirements', {}),
            'responsibilities': job_data.get('responsibilities', []),
            'metadata': job_data.get('metadata', {})
        }
        
    def _combine_scores(self, base_score: float, ml_score: float) -> float:
        """Combina scores de diferentes análisis."""
        # Peso mayor al análisis base (60%) que al ML (40%)
        return (base_score * 0.6) + (ml_score * 0.4)
        
    def _generate_report(
        self,
        base_analysis: Dict,
        ml_analysis: Dict,
        final_score: float
    ) -> Dict[str, Any]:
        """Genera reporte detallado del match."""
        return {
            'base_analysis': base_analysis,
            'ml_analysis': ml_analysis,
            'final_score': final_score,
            'timestamp': datetime.now().isoformat()
        }
        
    def _generate_insights(
        self,
        base_analysis: Dict,
        ml_analysis: Dict,
        final_score: float
    ) -> List[Dict[str, Any]]:
        """Genera insights clave del match."""
        insights = []
        
        # Insights del análisis base
        if base_analysis.get('insights'):
            insights.extend(base_analysis['insights'])
            
        # Insights del análisis ML
        if ml_analysis.get('explanation'):
            for feature, importance in ml_analysis['explanation'].items():
                insights.append({
                    'type': 'ml_insight',
                    'feature': feature,
                    'importance': importance,
                    'description': f"El modelo ML indica que {feature} es {'muy' if importance > 0.7 else 'moderadamente'} importante para este match"
                })
                
        return insights 