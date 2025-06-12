"""
Analizador de matchmaking.
Integra múltiples fuentes de datos para un matching más preciso.
"""
from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime

from app.ml.core.models.matchmaking.factors_model import FactorsMatchmakingModel
from app.ats.utils.cv_generator.cv_analyzer import CVAnalyzer
from app.ats.integrations.channels.linkedin.profile_analyzer import LinkedInProfileAnalyzer
from app.ats.chatbot.workflow.assessments.professional_dna.analysis import ProfessionalDNAAnalysis
from app.ats.chatbot.workflow.assessments.personality.personality_workflow import PersonalityAssessment

# Importar analizadores adicionales
from app.ml.analyzers.personality_analyzer import PersonalityAnalyzer
from app.ml.analyzers.cultural_analyzer import CulturalAnalyzer
from app.ml.analyzers.professional_analyzer import ProfessionalAnalyzer
from app.ml.analyzers.talent_analyzer import TalentAnalyzer
from app.ml.analyzers.location_analyzer import LocationAnalyzer
from app.ml.analyzers.motivational_analyzer import MotivationalAnalyzer
from app.ml.analyzers.team_analyzer import TeamAnalyzerImpl
from app.ml.analyzers.reference_analyzer import ReferenceAnalyzer

logger = logging.getLogger(__name__)

class MatchmakingAnalyzer:
    """Analizador de matchmaking."""
    
    def __init__(self):
        # Modelo base de matchmaking
        self.model = FactorsMatchmakingModel()
        
        # Analizadores de fuentes externas
        self.cv_analyzer = CVAnalyzer()
        self.linkedin_analyzer = LinkedInProfileAnalyzer()
        self.professional_dna = ProfessionalDNAAnalysis()
        self.personality = PersonalityAssessment()
        
        # Analizadores especializados
        self.personality_analyzer = PersonalityAnalyzer()
        self.cultural_analyzer = CulturalAnalyzer()
        self.professional_analyzer = ProfessionalAnalyzer()
        self.talent_analyzer = TalentAnalyzer()
        self.location_analyzer = LocationAnalyzer()
        self.motivational_analyzer = MotivationalAnalyzer()
        self.team_analyzer = TeamAnalyzerImpl()
        self.reference_analyzer = ReferenceAnalyzer()
        
    async def analyze_match(
        self,
        candidate_data: Dict,
        job_data: Dict,
        business_unit: str
    ) -> Dict[str, Any]:
        """
        Analiza el match entre candidato y vacante.
        
        Args:
            candidate_data: Datos del candidato
            job_data: Datos de la vacante
            business_unit: Unidad de negocio
            
        Returns:
            Dict con resultados del análisis
        """
        try:
            # 1. Análisis de fuentes externas
            cv_insights = await self._analyze_cv(candidate_data)
            linkedin_insights = await self._analyze_linkedin(candidate_data)
            
            # 2. Análisis de assessments
            assessment_insights = await self._analyze_assessments(
                candidate_data,
                business_unit
            )
            
            # 3. Análisis especializado
            specialized_insights = await self._analyze_specialized(
                candidate_data,
                job_data,
                business_unit
            )
            
            # 4. Integración de insights
            integrated_insights = self._integrate_insights(
                cv_insights,
                linkedin_insights,
                assessment_insights,
                specialized_insights
            )
            
            # 5. Cálculo de match score usando el modelo ML
            match_score = self.model.predict([(integrated_insights, job_data)])[0]
            
            # 6. Generación de reporte
            report = self._generate_match_report(
                integrated_insights,
                job_data,
                match_score
            )
            
            return {
                'match_score': float(match_score),
                'report': report,
                'insights': integrated_insights,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error en análisis de match: {str(e)}")
            raise
            
    async def _analyze_cv(self, candidate_data: Dict) -> Dict:
        """Analiza el CV del candidato."""
        return await self.cv_analyzer.analyze(candidate_data['cv'])
        
    async def _analyze_linkedin(self, candidate_data: Dict) -> Dict:
        """Analiza el perfil de LinkedIn."""
        return await self.linkedin_analyzer.analyze(candidate_data['linkedin_url'])
        
    async def _analyze_assessments(
        self,
        candidate_data: Dict,
        business_unit: str
    ) -> Dict:
        """Analiza los assessments del candidato."""
        professional_insights = await self.professional_dna.analyze(
            candidate_data,
            business_unit
        )
        
        personality_insights = await self.personality.analyze(
            candidate_data
        )
        
        return {
            'professional': professional_insights,
            'personality': personality_insights
        }
        
    async def _analyze_specialized(
        self,
        candidate_data: Dict,
        job_data: Dict,
        business_unit: str
    ) -> Dict:
        """Realiza análisis especializado."""
        insights = {}
        
        # Análisis de personalidad
        personality_insights = await self.personality_analyzer.analyze(
            candidate_data,
            business_unit
        )
        insights['personality'] = personality_insights
        
        # Análisis cultural
        cultural_insights = self.cultural_analyzer.analyze(candidate_data)
        insights['cultural'] = cultural_insights
        
        # Análisis profesional
        professional_insights = self.professional_analyzer.analyze(candidate_data)
        insights['professional'] = professional_insights
        
        # Análisis de talento
        talent_insights = self.talent_analyzer.analyze(candidate_data)
        insights['talent'] = talent_insights
        
        # Análisis de ubicación
        location_insights = await self.location_analyzer.analyze(
            candidate_data,
            business_unit
        )
        insights['location'] = location_insights
        
        # Análisis motivacional
        motivational_insights = self.motivational_analyzer.analyze(candidate_data)
        insights['motivational'] = motivational_insights
        
        # Análisis de equipo
        team_insights = self.team_analyzer.analyze(candidate_data)
        insights['team'] = team_insights
        
        # Análisis de referencias
        if 'references' in candidate_data:
            reference_insights = self.reference_analyzer.analyze_reference_quality(
                candidate_data['references']
            )
            insights['references'] = reference_insights
            
        return insights
        
    def _integrate_insights(
        self,
        cv_insights: Dict,
        linkedin_insights: Dict,
        assessment_insights: Dict,
        specialized_insights: Dict
    ) -> Dict:
        """Integra insights de diferentes fuentes."""
        integrated = {}
        
        # Integrar por categoría
        for category in ['technical', 'behavioral', 'cultural', 'career', 
                        'personal', 'network', 'innovation', 'leadership']:
            category_insights = self._integrate_category_insights(
                category,
                cv_insights,
                linkedin_insights,
                assessment_insights,
                specialized_insights
            )
            integrated[category] = category_insights
            
        return integrated
        
    def _integrate_category_insights(
        self,
        category: str,
        cv_insights: Dict,
        linkedin_insights: Dict,
        assessment_insights: Dict,
        specialized_insights: Dict
    ) -> Dict:
        """Integra insights para una categoría específica."""
        category_data = {}
        
        # Mapeo de fuentes por categoría
        source_mapping = {
            'technical': ['cv', 'linkedin', 'assessments', 'talent'],
            'behavioral': ['assessments', 'linkedin_activity', 'personality'],
            'cultural': ['assessments', 'linkedin_network', 'cultural'],
            'career': ['cv', 'linkedin', 'professional'],
            'personal': ['assessments', 'linkedin_activity', 'personality'],
            'network': ['linkedin', 'team'],
            'innovation': ['assessments', 'linkedin_content', 'talent'],
            'leadership': ['assessments', 'linkedin_content', 'professional']
        }
        
        # Recolectar datos de todas las fuentes
        for source in source_mapping.get(category, []):
            if source == 'cv':
                category_data.update(cv_insights.get(category, {}))
            elif source == 'linkedin':
                category_data.update(linkedin_insights.get(category, {}))
            elif source == 'assessments':
                category_data.update(assessment_insights.get(category, {}))
            elif source in specialized_insights:
                category_data.update(specialized_insights[source].get(category, {}))
                
        return category_data
        
    def _generate_match_report(
        self,
        insights: Dict,
        job_data: Dict,
        match_score: float
    ) -> Dict:
        """Genera reporte detallado del match."""
        return {
            'summary': {
                'match_score': match_score,
                'strengths': self._identify_strengths(insights, job_data),
                'gaps': self._identify_gaps(insights, job_data),
                'recommendations': self._generate_recommendations(insights, job_data)
            },
            'details': {
                category: {
                    'score': self._calculate_category_score(insights[category]),
                    'factors': self._format_category_factors(insights[category])
                }
                for category in insights
            }
        }
        
    def _identify_strengths(self, insights: Dict, job_data: Dict) -> List[str]:
        """Identifica fortalezas del candidato para la vacante."""
        strengths = []
        
        for category, data in insights.items():
            if self._is_strength(data, job_data.get(category, {})):
                strengths.append(f"Fuerte en {category}")
                
        return strengths
        
    def _identify_gaps(self, insights: Dict, job_data: Dict) -> List[str]:
        """Identifica gaps del candidato para la vacante."""
        gaps = []
        
        for category, data in insights.items():
            if self._is_gap(data, job_data.get(category, {})):
                gaps.append(f"Necesita mejorar en {category}")
                
        return gaps
        
    def _generate_recommendations(
        self,
        insights: Dict,
        job_data: Dict
    ) -> List[str]:
        """Genera recomendaciones basadas en el análisis."""
        recommendations = []
        
        for category, data in insights.items():
            if self._needs_improvement(data, job_data.get(category, {})):
                recommendations.append(
                    self._get_recommendation(category, data, job_data)
                )
                
        return recommendations
        
    def _calculate_category_score(self, category_insights: Dict) -> float:
        """Calcula score para una categoría."""
        if not category_insights:
            return 0.0
            
        scores = [
            value for value in category_insights.values()
            if isinstance(value, (int, float))
        ]
        
        return sum(scores) / len(scores) if scores else 0.0
        
    def _format_category_factors(self, category_insights: Dict) -> List[Dict]:
        """Formatea factores de una categoría para el reporte."""
        return [
            {
                'name': key,
                'value': value,
                'description': self._get_factor_description(key, value)
            }
            for key, value in category_insights.items()
        ]
        
    def _is_strength(self, candidate_data: Dict, job_data: Dict) -> bool:
        """Determina si un aspecto es una fortaleza."""
        # Implementar lógica de fortalezas
        return False
        
    def _is_gap(self, candidate_data: Dict, job_data: Dict) -> bool:
        """Determina si hay un gap en un aspecto."""
        # Implementar lógica de gaps
        return False
        
    def _needs_improvement(
        self,
        candidate_data: Dict,
        job_data: Dict
    ) -> bool:
        """Determina si un aspecto necesita mejora."""
        # Implementar lógica de mejora
        return False
        
    def _get_recommendation(
        self,
        category: str,
        candidate_data: Dict,
        job_data: Dict
    ) -> str:
        """Genera una recomendación específica."""
        # Implementar generación de recomendaciones
        return f"Considerar mejorar en {category}"
        
    def _get_factor_description(self, factor: str, value: Any) -> str:
        """Obtiene descripción de un factor."""
        # Implementar descripciones de factores
        return f"Descripción de {factor}" 