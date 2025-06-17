from typing import Dict, Any, List
from datetime import datetime
from app.ats.utils.nlp import NLPProcessor
from .rankings import UniversityRankingsAnalyzer
from .storage import UniversityPreferenceStorage

class UniversityAnalyzer:
    """
    Analizador de preferencias universitarias.
    Integra análisis de rankings y preferencias de universidades.
    """
    def __init__(self):
        self.nlp = NLPProcessor()
        self.rankings_analyzer = UniversityRankingsAnalyzer()
        self.storage = UniversityPreferenceStorage()
        
    async def analyze(self, job_description: str) -> Dict[str, Any]:
        """
        Analiza preferencias universitarias en el JD.
        """
        # Extraer universidades usando NLP
        universities = await self.nlp.extract_universities(job_description)
        
        # Analizar rankings
        rankings_analysis = await self._analyze_rankings(universities)
        
        # Analizar preferencias
        preferences_analysis = await self._analyze_preferences(job_description)
        
        analysis_result = {
            'universities': universities,
            'rankings': rankings_analysis,
            'preferences': preferences_analysis,
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'status': 'analyzed'
            }
        }
        
        # Almacenar para análisis futuro
        await self.storage.store_for_analysis(analysis_result)
        
        return analysis_result
    
    async def _analyze_rankings(self, universities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analiza rankings de las universidades mencionadas.
        """
        rankings = {}
        for university in universities:
            try:
                ranking_data = await self.rankings_analyzer.get_university_ranking(university['normalized'])
                rankings[university['normalized']] = await self.rankings_analyzer.analyze_university_metrics(ranking_data)
            except Exception as e:
                rankings[university['normalized']] = {'error': str(e)}
        
        return rankings
    
    async def _analyze_preferences(self, job_description: str) -> Dict[str, Any]:
        """
        Analiza preferencias universitarias en el JD.
        """
        # TODO: Implementar análisis de preferencias
        return {
            'explicit_preferences': [],
            'implicit_preferences': [],
            'confidence': 0.0
        } 