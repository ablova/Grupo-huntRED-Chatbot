"""
🚀 GhuntRED-v2 GenIA Experience Analyzer
Analyze work experience and career progression
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any
from ..core.exceptions import PredictionError

logger = logging.getLogger('ml.genia')

class ExperienceAnalyzer:
    """Analyze candidate work experience"""
    
    def analyze(self, candidate_data: dict) -> dict:
        """Analyze candidate experience"""
        try:
            experience_score = self._calculate_experience_score(candidate_data)
            career_progression = self._analyze_career_progression(candidate_data)
            
            return {
                'score': experience_score,
                'career_progression': career_progression,
                'total_years': self._calculate_total_years(candidate_data),
                'recommendations': self._generate_recommendations(candidate_data),
            }
            
        except Exception as e:
            logger.error(f"❌ Experience analysis failed: {e}")
            raise PredictionError("experience_analyzer", str(e))
    
    def _calculate_experience_score(self, candidate_data: dict) -> float:
        """Calculate experience score based on years and progression"""
        total_years = self._calculate_total_years(candidate_data)
        
        # Base score from years of experience
        if total_years >= 10:
            base_score = 90
        elif total_years >= 5:
            base_score = 70
        elif total_years >= 2:
            base_score = 50
        else:
            base_score = 30
        
        # Bonus for career progression
        progression_bonus = self._calculate_progression_bonus(candidate_data)
        
        return min(100.0, base_score + progression_bonus)
    
    def _calculate_total_years(self, candidate_data: dict) -> float:
        """Calculate total years of experience"""
        if 'years_of_experience' in candidate_data:
            return float(candidate_data['years_of_experience'])
        
        # Calculate from work experience entries
        total_years = 0.0
        if 'work_experience' in candidate_data:
            for exp in candidate_data['work_experience']:
                years = self._calculate_experience_duration(exp)
                total_years += years
        
        return total_years
    
    def _calculate_experience_duration(self, experience: dict) -> float:
        """Calculate duration of a single experience"""
        try:
            start_date = datetime.strptime(experience.get('start_date', ''), '%Y-%m-%d')
            
            if experience.get('end_date'):
                end_date = datetime.strptime(experience['end_date'], '%Y-%m-%d')
            else:
                end_date = datetime.now()  # Current job
            
            duration = end_date - start_date
            return duration.days / 365.25  # Convert to years
            
        except:
            return 0.0
    
    def _analyze_career_progression(self, candidate_data: dict) -> dict:
        """Analyze career progression patterns"""
        progression = {
            'trend': 'stable',
            'promotions': 0,
            'career_changes': 0,
            'stability_score': 0.0,
        }
        
        if 'work_experience' not in candidate_data:
            return progression
        
        experiences = sorted(
            candidate_data['work_experience'],
            key=lambda x: x.get('start_date', ''),
            reverse=True
        )
        
        # Analyze progression indicators
        promotions = 0
        career_changes = 0
        
        for i, exp in enumerate(experiences[1:], 1):
            prev_exp = experiences[i-1]
            
            # Check for promotion (same company, higher position)
            if (exp.get('company', '').lower() == prev_exp.get('company', '').lower() and
                self._is_promotion(exp.get('position', ''), prev_exp.get('position', ''))):
                promotions += 1
            
            # Check for career change
            if exp.get('company', '').lower() != prev_exp.get('company', '').lower():
                career_changes += 1
        
        progression['promotions'] = promotions
        progression['career_changes'] = career_changes
        progression['stability_score'] = self._calculate_stability_score(experiences)
        
        # Determine trend
        if promotions > 0:
            progression['trend'] = 'ascending'
        elif career_changes > len(experiences) * 0.7:
            progression['trend'] = 'unstable'
        else:
            progression['trend'] = 'stable'
        
        return progression
    
    def _is_promotion(self, current_position: str, previous_position: str) -> bool:
        """Check if current position is a promotion from previous"""
        senior_indicators = ['senior', 'lead', 'manager', 'director', 'vp', 'chief']
        
        current_lower = current_position.lower()
        previous_lower = previous_position.lower()
        
        # Check for senior indicators
        current_seniority = sum(1 for indicator in senior_indicators if indicator in current_lower)
        previous_seniority = sum(1 for indicator in senior_indicators if indicator in previous_lower)
        
        return current_seniority > previous_seniority
    
    def _calculate_stability_score(self, experiences: List[dict]) -> float:
        """Calculate job stability score"""
        if not experiences:
            return 0.0
        
        # Average job duration
        total_duration = 0.0
        for exp in experiences:
            duration = self._calculate_experience_duration(exp)
            total_duration += duration
        
        avg_duration = total_duration / len(experiences)
        
        # Stability score based on average duration
        if avg_duration >= 3:
            return 90.0
        elif avg_duration >= 2:
            return 70.0
        elif avg_duration >= 1:
            return 50.0
        else:
            return 30.0
    
    def _calculate_progression_bonus(self, candidate_data: dict) -> float:
        """Calculate bonus points for career progression"""
        progression = self._analyze_career_progression(candidate_data)
        
        bonus = 0.0
        
        # Bonus for promotions
        bonus += progression['promotions'] * 5
        
        # Bonus for stability
        bonus += progression['stability_score'] * 0.1
        
        # Penalty for too many job changes
        if progression['career_changes'] > 5:
            bonus -= 10
        
        return max(-20.0, min(20.0, bonus))
    
    def _generate_recommendations(self, candidate_data: dict) -> List[str]:
        """Generate experience-based recommendations"""
        recommendations = []
        
        total_years = self._calculate_total_years(candidate_data)
        progression = self._analyze_career_progression(candidate_data)
        
        if total_years < 2:
            recommendations.append("Consider gaining more work experience")
        
        if progression['trend'] == 'unstable':
            recommendations.append("Consider focusing on longer-term positions for career stability")
        
        if progression['promotions'] == 0 and total_years > 3:
            recommendations.append("Look for opportunities for career advancement")
        
        return recommendations
    
    def health_check(self):
        """Health check for experience analyzer"""
        test_data = {
            'years_of_experience': 5,
            'work_experience': [
                {
                    'company': 'Tech Corp',
                    'position': 'Senior Developer',
                    'start_date': '2020-01-01',
                    'end_date': '2023-01-01'
                }
            ]
        }
        
        result = self.analyze(test_data)
        
        if not result or 'score' not in result:
            raise Exception("Health check failed: Invalid analysis result")