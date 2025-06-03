# /home/pablo/app/com/chatbot/values/principles.py
"""
Principles Analyzer module for Grupo huntRED® values system.

This module analyzes and evaluates alignment with organizational principles
across business units and candidates.
"""
import logging
from typing import Dict, List, Any, Optional
import json

from django.conf import settings

from app.models import Person, BusinessUnit
from app.ats.chatbot.values.core import ValuesPrinciples

logger = logging.getLogger(__name__)

class PrinciplesAnalyzer:
    """
    Analyzer for organizational principles alignment.
    
    Evaluates how candidates and employees align with the core principles
    of the organization and specific business units.
    """
    
    def __init__(self):
        """Initialize the principles analyzer."""
        self.values_principles = ValuesPrinciples()
        self.cache = {}
    
    def analyze_principles_alignment(self, person_id: int, 
                                     business_unit: Optional[BusinessUnit] = None) -> Dict:
        """
        Analyze a person's alignment with organizational principles.
        
        Args:
            person_id: ID of the person to analyze
            business_unit: Optional business unit for context
            
        Returns:
            Dict with principles alignment analysis
        """
        try:
            # Get person data
            person = self._get_person(person_id)
            if not person:
                logger.warning(f"Person with ID {person_id} not found")
                return self._get_default_result("Person not found")
            
            # Get relevant principles
            principles = self._get_relevant_principles(business_unit)
            
            # Calculate alignment scores
            alignment_scores = self._calculate_alignment_scores(person, principles)
            
            # Generate insights
            insights = self._generate_insights(alignment_scores, person, business_unit)
            
            # Return results
            return {
                'status': 'success',
                'person_id': person_id,
                'business_unit': business_unit.name if business_unit else 'general',
                'principles': principles,
                'alignment_scores': alignment_scores,
                'insights': insights,
                'overall_alignment': sum(alignment_scores.values()) / len(alignment_scores) if alignment_scores else 0
            }
            
        except Exception as e:
            logger.error(f"Error in principles analysis: {str(e)}", exc_info=True)
            return self._get_default_result(f"Analysis error: {str(e)}")
    
    def _get_person(self, person_id: int) -> Optional[Person]:
        """Get person object from database."""
        try:
            return Person.objects.get(id=person_id)
        except Person.DoesNotExist:
            return None
    
    def _get_relevant_principles(self, business_unit: Optional[BusinessUnit]) -> Dict[str, str]:
        """Get relevant principles for the specified business unit."""
        # Get principles from ValuesPrinciples class
        if business_unit:
            # Get BU-specific principles if available
            return self.values_principles.get_business_unit_principles(business_unit.name)
        else:
            # Get general organizational principles
            return self.values_principles.get_core_principles()
    
    def _calculate_alignment_scores(self, person: Person, principles: Dict[str, str]) -> Dict[str, float]:
        """
        Calculate alignment scores for each principle.
        
        This is a simplified implementation that would be enhanced with 
        actual assessment data in a production environment.
        """
        # In a real implementation, this would use assessment data, chat history,
        # or other sources to determine alignment scores.
        # This is a placeholder implementation.
        
        alignment_scores = {}
        
        # Example implementation using random but consistent scores based on person ID
        import hashlib
        import random
        
        # Use person ID to seed random for consistent results
        seed = int(hashlib.md5(str(person.id).encode()).hexdigest(), 16) % 10000
        random.seed(seed)
        
        for principle_name in principles:
            # Generate a score between 0.5 and 1.0
            # In a real implementation, this would use actual data
            alignment_scores[principle_name] = round(0.5 + random.random() * 0.5, 2)
        
        return alignment_scores
    
    def _generate_insights(self, alignment_scores: Dict[str, float], 
                          person: Person, business_unit: Optional[BusinessUnit]) -> Dict:
        """Generate actionable insights based on principles alignment."""
        insights = {
            'strengths': [],
            'opportunities': [],
            'recommendations': []
        }
        
        # Identify strengths (high alignment)
        strengths = [p for p, score in alignment_scores.items() if score >= 0.8]
        for principle in strengths[:3]:  # Top 3 strengths
            insights['strengths'].append(f"Strong alignment with {principle}")
        
        # Identify opportunities (low alignment)
        opportunities = [p for p, score in alignment_scores.items() if score < 0.7]
        for principle in opportunities[:3]:  # Top 3 opportunities
            insights['opportunities'].append(f"Potential to strengthen alignment with {principle}")
        
        # Generate recommendations
        if opportunities:
            insights['recommendations'].append("Review core principles during onboarding")
            insights['recommendations'].append("Include principles discussion in mentoring sessions")
        
        if business_unit:
            insights['recommendations'].append(f"Emphasize {business_unit.name} specific principles in team activities")
        
        return insights
    
    def _get_default_result(self, error_message: str = "") -> Dict:
        """Return default result when analysis cannot be completed."""
        return {
            'status': 'error',
            'error': error_message or "Could not complete principles analysis",
            'principles': {},
            'alignment_scores': {},
            'insights': {},
            'overall_alignment': 0
        }
