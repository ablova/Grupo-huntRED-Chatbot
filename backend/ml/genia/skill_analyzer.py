"""
🚀 GhuntRED-v2 GenIA Skill Analyzer
Advanced skill extraction and analysis using ML
"""

import logging
import re
from typing import Dict, List, Any
from ..core.exceptions import ValidationError, PredictionError

logger = logging.getLogger('ml.genia')

class SkillAnalyzer:
    """Advanced skill extraction and analysis"""
    
    def __init__(self):
        self.skill_patterns = self._load_skill_patterns()
        self.proficiency_indicators = self._load_proficiency_indicators()
        
    def _load_skill_patterns(self) -> Dict[str, List[str]]:
        """Load skill patterns for extraction"""
        return {
            'programming': [
                r'\b(python|java|javascript|typescript|c\+\+|c#|php|ruby|go|rust|swift|kotlin)\b',
                r'\b(react|angular|vue|django|flask|spring|laravel|express)\b',
                r'\b(html|css|scss|sass|bootstrap|tailwind)\b',
            ],
            'databases': [
                r'\b(mysql|postgresql|mongodb|redis|elasticsearch|cassandra|oracle)\b',
                r'\b(sql|nosql|database|db)\b',
            ],
            'cloud': [
                r'\b(aws|azure|gcp|google cloud|amazon web services)\b',
                r'\b(docker|kubernetes|terraform|ansible)\b',
            ],
            'soft_skills': [
                r'\b(leadership|communication|teamwork|problem.solving)\b',
                r'\b(project.management|agile|scrum|kanban)\b',
            ],
        }
    
    def _load_proficiency_indicators(self) -> Dict[str, List[str]]:
        """Load proficiency level indicators"""
        return {
            'expert': ['expert', 'senior', 'lead', 'architect', '10+ years', '8+ years'],
            'advanced': ['advanced', 'proficient', '5+ years', '6+ years', '7+ years'],
            'intermediate': ['intermediate', 'solid', '3+ years', '4+ years', 'good'],
            'beginner': ['beginner', 'basic', 'learning', '1+ year', '2+ years'],
        }
    
    def analyze(self, candidate_data: dict) -> dict:
        """Analyze candidate skills"""
        try:
            # Extract text from various sources
            text = self._extract_text(candidate_data)
            
            # Extract skills
            extracted_skills = self._extract_skills(text)
            
            # Determine proficiency levels
            skill_proficiencies = self._analyze_proficiency(text, extracted_skills)
            
            # Calculate skill score
            skill_score = self._calculate_skill_score(skill_proficiencies)
            
            return {
                'score': skill_score,
                'extracted_skills': extracted_skills,
                'skill_proficiencies': skill_proficiencies,
                'skill_categories': self._categorize_skills(extracted_skills),
                'recommendations': self._generate_recommendations(skill_proficiencies),
            }
            
        except Exception as e:
            logger.error(f"❌ Skill analysis failed: {e}")
            raise PredictionError("skill_analyzer", str(e))
    
    def _extract_text(self, candidate_data: dict) -> str:
        """Extract text from candidate data"""
        text_parts = []
        
        # Resume text
        if 'resume_text' in candidate_data:
            text_parts.append(candidate_data['resume_text'])
        
        # Professional summary
        if 'professional_summary' in candidate_data:
            text_parts.append(candidate_data['professional_summary'])
        
        # Work experience
        if 'work_experience' in candidate_data:
            for exp in candidate_data['work_experience']:
                text_parts.append(exp.get('description', ''))
                text_parts.append(exp.get('technologies_used', ''))
        
        # Skills
        if 'skills' in candidate_data:
            for skill in candidate_data['skills']:
                text_parts.append(skill.get('name', ''))
        
        return ' '.join(text_parts).lower()
    
    def _extract_skills(self, text: str) -> Dict[str, List[str]]:
        """Extract skills using pattern matching"""
        extracted_skills = {}
        
        for category, patterns in self.skill_patterns.items():
            category_skills = set()
            
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                category_skills.update(matches)
            
            extracted_skills[category] = list(category_skills)
        
        return extracted_skills
    
    def _analyze_proficiency(self, text: str, skills: Dict[str, List[str]]) -> Dict[str, Dict[str, str]]:
        """Analyze proficiency levels for extracted skills"""
        proficiencies = {}
        
        for category, skill_list in skills.items():
            proficiencies[category] = {}
            
            for skill in skill_list:
                # Find proficiency indicators near the skill mention
                skill_context = self._extract_skill_context(text, skill)
                proficiency = self._determine_proficiency(skill_context)
                proficiencies[category][skill] = proficiency
        
        return proficiencies
    
    def _extract_skill_context(self, text: str, skill: str, window_size: int = 50) -> str:
        """Extract context around skill mentions"""
        skill_positions = [m.start() for m in re.finditer(re.escape(skill), text, re.IGNORECASE)]
        
        contexts = []
        for pos in skill_positions:
            start = max(0, pos - window_size)
            end = min(len(text), pos + len(skill) + window_size)
            contexts.append(text[start:end])
        
        return ' '.join(contexts)
    
    def _determine_proficiency(self, context: str) -> str:
        """Determine proficiency level from context"""
        context_lower = context.lower()
        
        # Check for explicit proficiency indicators
        for level, indicators in self.proficiency_indicators.items():
            for indicator in indicators:
                if indicator in context_lower:
                    return level
        
        # Default proficiency based on context clues
        if any(word in context_lower for word in ['years', 'experience', 'worked']):
            return 'intermediate'
        
        return 'beginner'
    
    def _categorize_skills(self, skills: Dict[str, List[str]]) -> Dict[str, int]:
        """Categorize and count skills"""
        categorization = {}
        
        for category, skill_list in skills.items():
            categorization[category] = len(skill_list)
        
        return categorization
    
    def _calculate_skill_score(self, proficiencies: Dict[str, Dict[str, str]]) -> float:
        """Calculate overall skill score"""
        total_score = 0
        total_skills = 0
        
        proficiency_weights = {
            'expert': 1.0,
            'advanced': 0.8,
            'intermediate': 0.6,
            'beginner': 0.3,
        }
        
        for category, category_skills in proficiencies.items():
            for skill, proficiency in category_skills.items():
                weight = proficiency_weights.get(proficiency, 0.3)
                total_score += weight
                total_skills += 1
        
        if total_skills == 0:
            return 0.0
        
        return min(100.0, (total_score / total_skills) * 100)
    
    def _generate_recommendations(self, proficiencies: Dict[str, Dict[str, str]]) -> List[str]:
        """Generate skill improvement recommendations"""
        recommendations = []
        
        # Analyze skill gaps
        for category, category_skills in proficiencies.items():
            beginner_skills = [skill for skill, prof in category_skills.items() if prof == 'beginner']
            
            if beginner_skills:
                recommendations.append(f"Consider improving {category} skills: {', '.join(beginner_skills[:3])}")
        
        # Check for missing important skills
        if 'programming' in proficiencies and len(proficiencies['programming']) < 3:
            recommendations.append("Consider learning additional programming languages")
        
        if 'databases' not in proficiencies or len(proficiencies['databases']) == 0:
            recommendations.append("Consider learning database technologies")
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    def health_check(self):
        """Health check for skill analyzer"""
        test_data = {
            'resume_text': 'Python developer with 5+ years experience in Django and PostgreSQL',
            'professional_summary': 'Senior software engineer',
        }
        
        result = self.analyze(test_data)
        
        if not result or 'score' not in result:
            raise Exception("Health check failed: Invalid analysis result")