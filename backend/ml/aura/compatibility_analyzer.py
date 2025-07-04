"""
🌟 GhuntRED-v2 AURA Compatibility Analyzer
Team and culture compatibility analysis
"""

import logging
from typing import Dict, List, Any
from ..core.exceptions import PredictionError

logger = logging.getLogger('ml.aura')

class CompatibilityAnalyzer:
    """AURA compatibility analysis"""
    
    def analyze(self, candidate_data: dict) -> dict:
        """Analyze candidate compatibility"""
        try:
            compatibility_score = self._calculate_compatibility(candidate_data)
            cultural_fit = self._assess_cultural_fit(candidate_data)
            team_dynamics = self._analyze_team_dynamics(candidate_data)
            
            return {
                'score': compatibility_score,
                'cultural_fit': cultural_fit,
                'team_dynamics': team_dynamics,
                'recommendations': self._generate_recommendations(cultural_fit, team_dynamics),
            }
            
        except Exception as e:
            logger.error(f"❌ AURA compatibility analysis failed: {e}")
            raise PredictionError("compatibility_analyzer", str(e))
    
    def _calculate_compatibility(self, candidate_data: dict) -> float:
        """Calculate overall compatibility score"""
        # Simplified compatibility calculation
        base_score = 75.0
        
        # Adjust based on experience
        years = candidate_data.get('years_of_experience', 0)
        if years >= 5:
            base_score += 10
        elif years >= 2:
            base_score += 5
        
        return min(100.0, base_score)
    
    def _assess_cultural_fit(self, candidate_data: dict) -> dict:
        """Assess cultural fit indicators"""
        return {
            'innovation_oriented': 0.8,
            'collaboration_focused': 0.7,
            'results_driven': 0.9,
            'learning_mindset': 0.8,
        }
    
    def _analyze_team_dynamics(self, candidate_data: dict) -> dict:
        """Analyze team dynamics compatibility"""
        return {
            'leadership_potential': 0.7,
            'mentoring_ability': 0.6,
            'conflict_resolution': 0.8,
            'communication_style': 0.7,
        }
    
    def _generate_recommendations(self, cultural_fit: dict, team_dynamics: dict) -> List[str]:
        """Generate compatibility recommendations"""
        recommendations = []
        
        if cultural_fit.get('innovation_oriented', 0) > 0.8:
            recommendations.append("Strong innovation mindset - excellent for R&D teams")
        
        if team_dynamics.get('leadership_potential', 0) > 0.8:
            recommendations.append("High leadership potential - consider for team lead roles")
        
        return recommendations
    
    def health_check(self):
        """Health check for compatibility analyzer"""
        test_data = {'years_of_experience': 5}
        result = self.analyze(test_data)
        if not result or 'score' not in result:
            raise Exception("Health check failed")