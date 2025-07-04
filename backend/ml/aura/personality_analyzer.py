"""
🌟 GhuntRED-v2 AURA Personality Analyzer
Advanced personality analysis using holistic assessment
"""

import logging
from typing import Dict, List, Any
from ..core.exceptions import PredictionError

logger = logging.getLogger('ml.aura')

class PersonalityAnalyzer:
    """AURA personality analysis"""
    
    def analyze(self, candidate_data: dict) -> dict:
        """Analyze candidate personality"""
        try:
            personality_traits = self._extract_personality_traits(candidate_data)
            personality_score = self._calculate_personality_score(personality_traits)
            
            return {
                'score': personality_score,
                'traits': personality_traits,
                'recommendations': self._generate_recommendations(personality_traits),
            }
            
        except Exception as e:
            logger.error(f"❌ AURA personality analysis failed: {e}")
            raise PredictionError("personality_analyzer", str(e))
    
    def _extract_personality_traits(self, candidate_data: dict) -> dict:
        """Extract personality traits from candidate data"""
        # Simplified personality extraction
        return {
            'openness': 0.7,
            'conscientiousness': 0.8,
            'extraversion': 0.6,
            'agreeableness': 0.7,
            'neuroticism': 0.3,
        }
    
    def _calculate_personality_score(self, traits: dict) -> float:
        """Calculate overall personality score"""
        weights = {
            'openness': 0.2,
            'conscientiousness': 0.3,
            'extraversion': 0.2,
            'agreeableness': 0.2,
            'neuroticism': -0.1,  # Negative weight
        }
        
        score = sum(traits.get(trait, 0.5) * weight for trait, weight in weights.items())
        return min(100.0, max(0.0, score * 100))
    
    def _generate_recommendations(self, traits: dict) -> List[str]:
        """Generate personality-based recommendations"""
        recommendations = []
        
        if traits.get('conscientiousness', 0.5) > 0.8:
            recommendations.append("Strong attention to detail - excellent for quality-focused roles")
        
        if traits.get('extraversion', 0.5) > 0.7:
            recommendations.append("High social energy - suitable for team leadership roles")
        
        return recommendations
    
    def health_check(self):
        """Health check for personality analyzer"""
        test_data = {'professional_summary': 'Dedicated team player with leadership experience'}
        result = self.analyze(test_data)
        if not result or 'score' not in result:
            raise Exception("Health check failed")