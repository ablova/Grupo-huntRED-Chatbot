"""
🚀 GhuntRED-v2 GenIA Matching Engine
Advanced job-candidate matching with ML algorithms
"""

import logging
import math
from typing import Dict, List, Any, Tuple
from ..core.exceptions import PredictionError

logger = logging.getLogger('ml.genia')

class MatchingEngine:
    """Advanced job-candidate matching engine"""
    
    def analyze(self, candidate_data: dict, job_data: dict = None) -> dict:
        """Analyze candidate-job match"""
        try:
            if job_data:
                # Specific job matching
                match_score = self._calculate_job_match(candidate_data, job_data)
                match_details = self._get_match_details(candidate_data, job_data)
            else:
                # General matching analysis
                match_score = self._calculate_general_match_score(candidate_data)
                match_details = self._get_general_match_details(candidate_data)
            
            return {
                'score': match_score,
                'match_details': match_details,
                'recommendations': self._generate_match_recommendations(candidate_data, job_data),
            }
            
        except Exception as e:
            logger.error(f"❌ Matching analysis failed: {e}")
            raise PredictionError("matching_engine", str(e))
    
    def _calculate_job_match(self, candidate_data: dict, job_data: dict) -> float:
        """Calculate match score for specific job"""
        scores = []
        weights = []
        
        # Skills match (40% weight)
        skills_score = self._calculate_skills_match(candidate_data, job_data)
        scores.append(skills_score)
        weights.append(0.4)
        
        # Experience match (30% weight)
        experience_score = self._calculate_experience_match(candidate_data, job_data)
        scores.append(experience_score)
        weights.append(0.3)
        
        # Location match (10% weight)
        location_score = self._calculate_location_match(candidate_data, job_data)
        scores.append(location_score)
        weights.append(0.1)
        
        # Salary match (10% weight)
        salary_score = self._calculate_salary_match(candidate_data, job_data)
        scores.append(salary_score)
        weights.append(0.1)
        
        # Work type match (10% weight)
        work_type_score = self._calculate_work_type_match(candidate_data, job_data)
        scores.append(work_type_score)
        weights.append(0.1)
        
        # Calculate weighted average
        weighted_score = sum(score * weight for score, weight in zip(scores, weights))
        return min(100.0, weighted_score)
    
    def _calculate_skills_match(self, candidate_data: dict, job_data: dict) -> float:
        """Calculate skills match score"""
        candidate_skills = set()
        job_skills = set()
        
        # Extract candidate skills
        if 'skills' in candidate_data:
            for skill in candidate_data['skills']:
                if isinstance(skill, dict):
                    candidate_skills.add(skill.get('name', '').lower())
                else:
                    candidate_skills.add(str(skill).lower())
        
        # Extract job skills
        if 'required_skills' in job_data:
            for skill in job_data['required_skills']:
                if isinstance(skill, dict):
                    job_skills.add(skill.get('name', '').lower())
                else:
                    job_skills.add(str(skill).lower())
        
        if not job_skills:
            return 50.0  # Neutral score if no skills specified
        
        # Calculate Jaccard similarity
        intersection = len(candidate_skills & job_skills)
        union = len(candidate_skills | job_skills)
        
        if union == 0:
            return 0.0
        
        jaccard_score = intersection / union
        return jaccard_score * 100
    
    def _calculate_experience_match(self, candidate_data: dict, job_data: dict) -> float:
        """Calculate experience level match"""
        candidate_years = candidate_data.get('years_of_experience', 0)
        required_experience = job_data.get('required_experience', {})
        
        if not required_experience:
            return 75.0  # Neutral score
        
        min_years = required_experience.get('min_years', 0)
        max_years = required_experience.get('max_years', 20)
        
        if min_years <= candidate_years <= max_years:
            return 100.0
        elif candidate_years < min_years:
            # Penalty for less experience
            deficit = min_years - candidate_years
            return max(0.0, 100 - (deficit * 20))
        else:
            # Slight penalty for overqualification
            excess = candidate_years - max_years
            return max(70.0, 100 - (excess * 5))
    
    def _calculate_location_match(self, candidate_data: dict, job_data: dict) -> float:
        """Calculate location match score"""
        candidate_location = {
            'country': candidate_data.get('country', '').lower(),
            'state': candidate_data.get('state', '').lower(),
            'city': candidate_data.get('city', '').lower(),
        }
        
        job_location = {
            'country': job_data.get('country', '').lower(),
            'state': job_data.get('state', '').lower(),
            'city': job_data.get('city', '').lower(),
        }
        
        # Remote work consideration
        if job_data.get('remote_work') in ['full_remote', 'hybrid']:
            return 90.0  # High score for remote work
        
        # Exact location match
        if (candidate_location['city'] == job_location['city'] and
            candidate_location['state'] == job_location['state'] and
            candidate_location['country'] == job_location['country']):
            return 100.0
        
        # Same state match
        if (candidate_location['state'] == job_location['state'] and
            candidate_location['country'] == job_location['country']):
            return 80.0
        
        # Same country match
        if candidate_location['country'] == job_location['country']:
            return 60.0
        
        return 30.0  # Different country
    
    def _calculate_salary_match(self, candidate_data: dict, job_data: dict) -> float:
        """Calculate salary expectation match"""
        candidate_min = candidate_data.get('expected_salary_min', 0)
        candidate_max = candidate_data.get('expected_salary_max', float('inf'))
        
        job_min = job_data.get('salary_min', 0)
        job_max = job_data.get('salary_max', float('inf'))
        
        if not candidate_min and not job_min:
            return 75.0  # Neutral if no salary info
        
        # Check for overlap
        overlap_min = max(candidate_min, job_min)
        overlap_max = min(candidate_max, job_max)
        
        if overlap_min <= overlap_max:
            # There's an overlap
            candidate_range = candidate_max - candidate_min
            job_range = job_max - job_min
            overlap_range = overlap_max - overlap_min
            
            if candidate_range > 0 and job_range > 0:
                overlap_score = min(overlap_range / candidate_range, overlap_range / job_range)
                return overlap_score * 100
            else:
                return 100.0
        else:
            # No overlap
            gap = overlap_min - overlap_max
            penalty = min(50.0, gap / max(candidate_min, job_min) * 100)
            return max(0.0, 100 - penalty)
    
    def _calculate_work_type_match(self, candidate_data: dict, job_data: dict) -> float:
        """Calculate work type preference match"""
        candidate_preference = candidate_data.get('work_type_preference', 'flexible')
        job_type = job_data.get('remote_work', 'onsite')
        
        match_matrix = {
            ('remote', 'full_remote'): 100,
            ('hybrid', 'hybrid'): 100,
            ('onsite', 'no'): 100,
            ('flexible', 'full_remote'): 90,
            ('flexible', 'hybrid'): 90,
            ('flexible', 'no'): 90,
            ('remote', 'hybrid'): 80,
            ('hybrid', 'full_remote'): 80,
            ('hybrid', 'no'): 70,
            ('remote', 'no'): 50,
            ('onsite', 'full_remote'): 40,
            ('onsite', 'hybrid'): 60,
        }
        
        return match_matrix.get((candidate_preference, job_type), 50.0)
    
    def _calculate_general_match_score(self, candidate_data: dict) -> float:
        """Calculate general match score without specific job"""
        # Based on profile completeness and quality
        completion_score = self._calculate_profile_completion(candidate_data)
        quality_score = self._calculate_profile_quality(candidate_data)
        
        return (completion_score + quality_score) / 2
    
    def _calculate_profile_completion(self, candidate_data: dict) -> float:
        """Calculate profile completion score"""
        required_fields = [
            'professional_summary', 'years_of_experience', 'skills',
            'work_experience', 'education', 'expected_salary_min'
        ]
        
        completed_fields = sum(1 for field in required_fields 
                             if candidate_data.get(field))
        
        return (completed_fields / len(required_fields)) * 100
    
    def _calculate_profile_quality(self, candidate_data: dict) -> float:
        """Calculate profile quality score"""
        quality_indicators = []
        
        # Professional summary length
        summary = candidate_data.get('professional_summary', '')
        if 50 <= len(summary.split()) <= 200:
            quality_indicators.append(1)
        else:
            quality_indicators.append(0.5)
        
        # Number of skills
        skills_count = len(candidate_data.get('skills', []))
        if skills_count >= 5:
            quality_indicators.append(1)
        elif skills_count >= 3:
            quality_indicators.append(0.7)
        else:
            quality_indicators.append(0.3)
        
        # Work experience count
        experience_count = len(candidate_data.get('work_experience', []))
        if experience_count >= 2:
            quality_indicators.append(1)
        elif experience_count >= 1:
            quality_indicators.append(0.7)
        else:
            quality_indicators.append(0.3)
        
        return (sum(quality_indicators) / len(quality_indicators)) * 100
    
    def _get_match_details(self, candidate_data: dict, job_data: dict) -> dict:
        """Get detailed match breakdown"""
        return {
            'skills_match': self._calculate_skills_match(candidate_data, job_data),
            'experience_match': self._calculate_experience_match(candidate_data, job_data),
            'location_match': self._calculate_location_match(candidate_data, job_data),
            'salary_match': self._calculate_salary_match(candidate_data, job_data),
            'work_type_match': self._calculate_work_type_match(candidate_data, job_data),
        }
    
    def _get_general_match_details(self, candidate_data: dict) -> dict:
        """Get general match details"""
        return {
            'profile_completion': self._calculate_profile_completion(candidate_data),
            'profile_quality': self._calculate_profile_quality(candidate_data),
            'marketability': self._calculate_general_match_score(candidate_data),
        }
    
    def _generate_match_recommendations(self, candidate_data: dict, job_data: dict = None) -> List[str]:
        """Generate recommendations to improve match"""
        recommendations = []
        
        if job_data:
            # Job-specific recommendations
            skills_match = self._calculate_skills_match(candidate_data, job_data)
            if skills_match < 60:
                recommendations.append("Consider developing skills mentioned in the job requirements")
            
            experience_match = self._calculate_experience_match(candidate_data, job_data)
            if experience_match < 60:
                recommendations.append("Gain more relevant experience for this role")
            
            salary_match = self._calculate_salary_match(candidate_data, job_data)
            if salary_match < 60:
                recommendations.append("Consider adjusting salary expectations")
        
        else:
            # General recommendations
            completion = self._calculate_profile_completion(candidate_data)
            if completion < 80:
                recommendations.append("Complete your profile with missing information")
            
            quality = self._calculate_profile_quality(candidate_data)
            if quality < 70:
                recommendations.append("Improve profile quality with more detailed information")
        
        return recommendations
    
    def health_check(self):
        """Health check for matching engine"""
        test_candidate = {
            'skills': [{'name': 'Python'}, {'name': 'Django'}],
            'years_of_experience': 3,
            'expected_salary_min': 50000,
        }
        
        test_job = {
            'required_skills': [{'name': 'Python'}, {'name': 'Django'}],
            'required_experience': {'min_years': 2, 'max_years': 5},
            'salary_min': 45000,
            'salary_max': 60000,
        }
        
        result = self.analyze(test_candidate, test_job)
        
        if not result or 'score' not in result:
            raise Exception("Health check failed: Invalid analysis result")