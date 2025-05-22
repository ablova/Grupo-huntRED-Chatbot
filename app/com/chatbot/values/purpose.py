# /home/pablo/app/com/chatbot/values/purpose.py
"""
Purpose Analyzer module for Grupo huntRED® values system.

This module analyzes and evaluates alignment with organizational purpose
and individual purpose across business units and candidates.
"""
import logging
from typing import Dict, List, Any, Optional
import json

from django.conf import settings

from app.models import Person, BusinessUnit
from app.com.chatbot.values.core import ValuesPrinciples

logger = logging.getLogger(__name__)

class PurposeAnalyzer:
    """
    Analyzer for purpose alignment and fulfillment.
    
    Evaluates how candidates and employees align with organizational purpose
    and helps identify individual purpose alignment with business units.
    """
    
    # Purpose categories
    PURPOSE_CATEGORIES = [
        "Innovation", "Service", "Impact", "Excellence", 
        "Leadership", "Growth", "Transformation"
    ]
    
    def __init__(self):
        """Initialize the purpose analyzer."""
        self.values_principles = ValuesPrinciples()
        self.cache = {}
    
    def analyze_purpose_alignment(self, person_id: int, 
                                 business_unit: Optional[BusinessUnit] = None) -> Dict:
        """
        Analyze a person's alignment with organizational purpose.
        
        Args:
            person_id: ID of the person to analyze
            business_unit: Optional business unit for context
            
        Returns:
            Dict with purpose alignment analysis
        """
        try:
            # Get person data
            person = self._get_person(person_id)
            if not person:
                logger.warning(f"Person with ID {person_id} not found")
                return self._get_default_result("Person not found")
            
            # Get organizational purpose
            org_purpose = self._get_organizational_purpose(business_unit)
            
            # Identify individual purpose indicators
            individual_purpose = self._identify_individual_purpose(person)
            
            # Calculate alignment scores
            alignment_score = self._calculate_purpose_alignment(individual_purpose, org_purpose)
            
            # Generate insights
            insights = self._generate_purpose_insights(alignment_score, individual_purpose, 
                                                     org_purpose, person, business_unit)
            
            # Return results
            return {
                'status': 'success',
                'person_id': person_id,
                'business_unit': business_unit.name if business_unit else 'general',
                'organizational_purpose': org_purpose,
                'individual_purpose': individual_purpose,
                'alignment_score': alignment_score,
                'insights': insights
            }
            
        except Exception as e:
            logger.error(f"Error in purpose analysis: {str(e)}", exc_info=True)
            return self._get_default_result(f"Analysis error: {str(e)}")
    
    def _get_person(self, person_id: int) -> Optional[Person]:
        """Get person object from database."""
        try:
            return Person.objects.get(id=person_id)
        except Person.DoesNotExist:
            return None
    
    def _get_organizational_purpose(self, business_unit: Optional[BusinessUnit]) -> Dict:
        """Get organizational purpose for the specified business unit."""
        # Get purpose statement from ValuesPrinciples class
        if business_unit:
            # Get BU-specific purpose if available
            return {
                'statement': self.values_principles.get_business_unit_purpose(business_unit.name),
                'categories': self._get_purpose_categories(business_unit.name),
                'indicators': self._get_purpose_indicators(business_unit.name)
            }
        else:
            # Get general organizational purpose
            return {
                'statement': self.values_principles.get_core_purpose(),
                'categories': self._get_purpose_categories(),
                'indicators': self._get_purpose_indicators()
            }
    
    def _get_purpose_categories(self, business_unit_name: str = None) -> List[str]:
        """Get purpose categories for general or specific business unit."""
        # In a real implementation, this would retrieve actual purpose categories
        # from a database or configuration. This is a placeholder.
        if business_unit_name == 'IT':
            return ["Innovation", "Excellence", "Transformation"]
        elif business_unit_name == 'HR':
            return ["Service", "Growth", "Impact"]
        else:
            return self.PURPOSE_CATEGORIES[:4]  # Default to first 4 categories
    
    def _get_purpose_indicators(self, business_unit_name: str = None) -> Dict[str, List[str]]:
        """Get purpose indicators for each category."""
        # In a real implementation, this would retrieve actual indicators
        # from a database or configuration. This is a placeholder.
        indicators = {
            "Innovation": ["Creates novel solutions", "Embraces change", "Forward-thinking"],
            "Service": ["Customer-oriented", "Supportive", "Responsive"],
            "Impact": ["Results-driven", "Community-focused", "Change agent"],
            "Excellence": ["Quality-focused", "Continuous improvement", "High standards"],
            "Leadership": ["Inspires others", "Strategic thinking", "Takes initiative"],
            "Growth": ["Development-oriented", "Scaling mindset", "Long-term focused"],
            "Transformation": ["Adaptable", "Visionary", "Catalyst for change"]
        }
        
        if business_unit_name:
            categories = self._get_purpose_categories(business_unit_name)
            return {k: v for k, v in indicators.items() if k in categories}
        else:
            return indicators
    
    def _identify_individual_purpose(self, person: Person) -> Dict:
        """
        Identify individual purpose indicators based on person data.
        
        This is a simplified implementation that would be enhanced with 
        actual assessment data in a production environment.
        """
        # In a real implementation, this would use assessment data, chat history,
        # résumé analysis, or other sources to determine purpose indicators.
        # This is a placeholder implementation.
        
        # Example implementation using person ID to generate consistent results
        import hashlib
        import random
        
        # Use person ID to seed random for consistent results
        seed = int(hashlib.md5(str(person.id).encode()).hexdigest(), 16) % 10000
        random.seed(seed)
        
        # Select random categories and indicators
        categories = random.sample(self.PURPOSE_CATEGORIES, min(3, len(self.PURPOSE_CATEGORIES)))
        
        individual_purpose = {
            'primary_categories': categories,
            'indicators': {}
        }
        
        for category in categories:
            all_indicators = self._get_purpose_indicators()[category]
            # Select 1-2 indicators per category
            num_indicators = random.randint(1, min(2, len(all_indicators)))
            individual_purpose['indicators'][category] = random.sample(all_indicators, num_indicators)
        
        # Generate a purpose statement
        primary_category = categories[0] if categories else "Growth"
        secondary_category = categories[1] if len(categories) > 1 else "Excellence"
        
        individual_purpose['statement'] = f"Driven by {primary_category.lower()} and {secondary_category.lower()}, " \
                                         f"seeking to make a meaningful impact through " \
                                         f"{individual_purpose['indicators'][primary_category][0].lower()}"
        
        return individual_purpose
    
    def _calculate_purpose_alignment(self, individual_purpose: Dict, org_purpose: Dict) -> float:
        """Calculate alignment between individual and organizational purpose."""
        # Calculate overlap in categories
        individual_categories = set(individual_purpose.get('primary_categories', []))
        org_categories = set(org_purpose.get('categories', []))
        
        if not individual_categories or not org_categories:
            return 0.5  # Default alignment if no categories available
        
        # Calculate category overlap as a percentage
        category_overlap = len(individual_categories.intersection(org_categories)) / len(org_categories)
        
        # Calculate indicator alignment
        indicator_alignment = 0.0
        indicator_count = 0
        
        for category in individual_categories.intersection(org_categories):
            individual_indicators = set(individual_purpose.get('indicators', {}).get(category, []))
            org_indicators = set(org_purpose.get('indicators', {}).get(category, []))
            
            if individual_indicators and org_indicators:
                indicator_overlap = len(individual_indicators.intersection(org_indicators)) / len(org_indicators)
                indicator_alignment += indicator_overlap
                indicator_count += 1
        
        # Average indicator alignment
        avg_indicator_alignment = indicator_alignment / indicator_count if indicator_count > 0 else 0.5
        
        # Final alignment is weighted average of category and indicator alignment
        return round(0.6 * category_overlap + 0.4 * avg_indicator_alignment, 2)
    
    def _generate_purpose_insights(self, alignment_score: float, individual_purpose: Dict, 
                                  org_purpose: Dict, person: Person, 
                                  business_unit: Optional[BusinessUnit]) -> Dict:
        """Generate actionable insights based on purpose alignment."""
        insights = {
            'alignment_level': self._get_alignment_level(alignment_score),
            'strengths': [],
            'opportunities': [],
            'recommendations': []
        }
        
        # Identify strengths (categories in both individual and org purpose)
        individual_categories = set(individual_purpose.get('primary_categories', []))
        org_categories = set(org_purpose.get('categories', []))
        shared_categories = individual_categories.intersection(org_categories)
        
        for category in shared_categories:
            insights['strengths'].append(f"Strong alignment in {category} purpose orientation")
        
        # Identify opportunities (org categories not in individual purpose)
        opportunity_categories = org_categories - individual_categories
        for category in opportunity_categories:
            insights['opportunities'].append(f"Opportunity to develop {category} purpose orientation")
        
        # Generate recommendations based on alignment level
        if alignment_score >= 0.8:
            insights['recommendations'].append("Leverage strong purpose alignment in role definition")
            insights['recommendations'].append("Consider for purpose ambassador initiatives")
        elif alignment_score >= 0.6:
            insights['recommendations'].append("Highlight organizational purpose in career development discussions")
            insights['recommendations'].append("Connect individual motivations to organizational goals")
        else:
            insights['recommendations'].append("Explore purpose alignment in onboarding and development")
            insights['recommendations'].append("Consider purpose-focused mentoring")
        
        if business_unit:
            insights['recommendations'].append(f"Emphasize {business_unit.name} specific purpose in team activities")
        
        return insights
    
    def _get_alignment_level(self, alignment_score: float) -> str:
        """Convert numerical alignment score to descriptive level."""
        if alignment_score >= 0.8:
            return "High"
        elif alignment_score >= 0.6:
            return "Moderate"
        elif alignment_score >= 0.4:
            return "Partial"
        else:
            return "Low"
    
    def _get_default_result(self, error_message: str = "") -> Dict:
        """Return default result when analysis cannot be completed."""
        return {
            'status': 'error',
            'error': error_message or "Could not complete purpose analysis",
            'organizational_purpose': {},
            'individual_purpose': {},
            'alignment_score': 0,
            'insights': {}
        }
