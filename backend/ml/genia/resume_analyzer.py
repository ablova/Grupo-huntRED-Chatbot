"""
🚀 GhuntRED-v2 GenIA Resume Analyzer
Advanced resume analysis and parsing
"""

import logging
import re
from typing import Dict, List, Any
from ..core.exceptions import PredictionError

logger = logging.getLogger('ml.genia')

class ResumeAnalyzer:
    """Advanced resume analysis"""
    
    def analyze(self, candidate_data: dict) -> dict:
        """Analyze candidate resume"""
        try:
            resume_text = candidate_data.get('resume_text', '')
            
            quality_score = self._calculate_quality_score(resume_text)
            structure_analysis = self._analyze_structure(resume_text)
            content_analysis = self._analyze_content(resume_text)
            
            return {
                'score': quality_score,
                'structure': structure_analysis,
                'content': content_analysis,
                'recommendations': self._generate_recommendations(resume_text),
            }
            
        except Exception as e:
            logger.error(f"❌ Resume analysis failed: {e}")
            raise PredictionError("resume_analyzer", str(e))
    
    def _calculate_quality_score(self, resume_text: str) -> float:
        """Calculate overall resume quality score"""
        if not resume_text.strip():
            return 0.0
        
        scores = []
        
        # Length score
        length_score = self._score_length(resume_text)
        scores.append(length_score)
        
        # Structure score
        structure_score = self._score_structure(resume_text)
        scores.append(structure_score)
        
        # Content richness score
        content_score = self._score_content_richness(resume_text)
        scores.append(content_score)
        
        # Professional language score
        language_score = self._score_language(resume_text)
        scores.append(language_score)
        
        return sum(scores) / len(scores)
    
    def _score_length(self, text: str) -> float:
        """Score based on resume length"""
        word_count = len(text.split())
        
        if 300 <= word_count <= 800:
            return 100.0
        elif 200 <= word_count < 300 or 800 < word_count <= 1200:
            return 80.0
        elif 100 <= word_count < 200 or 1200 < word_count <= 1500:
            return 60.0
        else:
            return 30.0
    
    def _score_structure(self, text: str) -> float:
        """Score based on resume structure"""
        structure_keywords = [
            'experience', 'education', 'skills', 'summary',
            'objective', 'projects', 'achievements', 'certifications'
        ]
        
        found_sections = sum(1 for keyword in structure_keywords 
                           if keyword in text.lower())
        
        # Score based on number of standard sections found
        if found_sections >= 6:
            return 100.0
        elif found_sections >= 4:
            return 80.0
        elif found_sections >= 2:
            return 60.0
        else:
            return 30.0
    
    def _score_content_richness(self, text: str) -> float:
        """Score based on content richness"""
        # Check for quantifiable achievements
        numbers_pattern = r'\b\d+(?:\.\d+)?(?:\s*%|\s*percent|k|K|million|billion)?\b'
        numbers_found = len(re.findall(numbers_pattern, text))
        
        # Check for action verbs
        action_verbs = [
            'developed', 'created', 'managed', 'led', 'implemented',
            'designed', 'optimized', 'increased', 'decreased', 'improved'
        ]
        action_verbs_found = sum(1 for verb in action_verbs if verb in text.lower())
        
        # Calculate richness score
        richness_score = min(100.0, (numbers_found * 10) + (action_verbs_found * 5))
        
        return richness_score
    
    def _score_language(self, text: str) -> float:
        """Score based on professional language"""
        # Check for professional tone
        professional_indicators = [
            'responsible for', 'achieved', 'accomplished', 'resulted in',
            'collaborated', 'coordinated', 'supervised', 'analyzed'
        ]
        
        professional_count = sum(1 for indicator in professional_indicators 
                               if indicator in text.lower())
        
        # Check for grammar issues (simple heuristics)
        sentences = text.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
        
        # Score based on professional language usage
        base_score = min(100.0, professional_count * 15)
        
        # Adjust for sentence length (too short or too long might indicate issues)
        if 10 <= avg_sentence_length <= 25:
            language_bonus = 10
        else:
            language_bonus = 0
        
        return min(100.0, base_score + language_bonus)
    
    def _analyze_structure(self, text: str) -> dict:
        """Analyze resume structure"""
        sections = {
            'has_summary': 'summary' in text.lower() or 'objective' in text.lower(),
            'has_experience': 'experience' in text.lower() or 'employment' in text.lower(),
            'has_education': 'education' in text.lower() or 'degree' in text.lower(),
            'has_skills': 'skills' in text.lower() or 'technologies' in text.lower(),
            'has_contact': any(indicator in text.lower() for indicator in ['email', 'phone', '@']),
        }
        
        sections['completeness'] = sum(sections.values()) / len(sections) * 100
        
        return sections
    
    def _analyze_content(self, text: str) -> dict:
        """Analyze resume content"""
        # Extract emails, phones, URLs
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        phones = re.findall(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', text)
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
        
        # Count achievements with numbers
        achievements_with_numbers = len(re.findall(r'\b\d+(?:\.\d+)?(?:\s*%|\s*percent|k|K|million|billion)?\b', text))
        
        return {
            'contact_info': {
                'emails': len(emails),
                'phones': len(phones),
                'urls': len(urls),
            },
            'quantified_achievements': achievements_with_numbers,
            'word_count': len(text.split()),
            'character_count': len(text),
        }
    
    def _generate_recommendations(self, text: str) -> List[str]:
        """Generate resume improvement recommendations"""
        recommendations = []
        
        word_count = len(text.split())
        structure = self._analyze_structure(text)
        
        # Length recommendations
        if word_count < 200:
            recommendations.append("Consider adding more details about your experience and achievements")
        elif word_count > 1200:
            recommendations.append("Consider condensing your resume to focus on most relevant information")
        
        # Structure recommendations
        if not structure['has_summary']:
            recommendations.append("Add a professional summary or objective section")
        
        if not structure['has_skills']:
            recommendations.append("Include a dedicated skills section")
        
        if not structure['has_contact']:
            recommendations.append("Ensure contact information is clearly visible")
        
        # Content recommendations
        numbers_count = len(re.findall(r'\b\d+(?:\.\d+)?(?:\s*%|\s*percent|k|K)?\b', text))
        if numbers_count < 3:
            recommendations.append("Add quantifiable achievements with specific numbers")
        
        # Action verbs check
        action_verbs = ['developed', 'created', 'managed', 'led', 'implemented']
        action_verbs_found = sum(1 for verb in action_verbs if verb in text.lower())
        if action_verbs_found < 3:
            recommendations.append("Use more action verbs to describe your accomplishments")
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    def health_check(self):
        """Health check for resume analyzer"""
        test_data = {
            'resume_text': '''
            Professional Summary: Senior Software Engineer with 5+ years experience.
            Experience: Developed web applications using Python and Django.
            Education: Bachelor's degree in Computer Science.
            Skills: Python, JavaScript, SQL, Git.
            Contact: john@example.com, 555-123-4567
            '''
        }
        
        result = self.analyze(test_data)
        
        if not result or 'score' not in result:
            raise Exception("Health check failed: Invalid analysis result")