# /home/pablo/app/ml/analyzers/behavior_analyzer.py
"""
Behavior Analyzer module for Grupo huntRED® assessment system.

This module analyzes behavioral patterns in communication and engagement
to improve candidate interactions and optimize communication strategies.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from django.conf import settings
from django.core.cache import cache

from app.models import Person, BusinessUnit, EmailLog
from app.ml.analyzers.base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)

class BehaviorAnalyzer(BaseAnalyzer):
    """
    Analyzer for behavioral patterns in communication and engagement.
    
    Identifies communication preferences, response patterns, and engagement
    indicators to optimize interaction strategies.
    """
    
    def __init__(self):
        """Initialize the behavior analyzer with required configuration."""
        super().__init__()
        self.cache_timeout = 3600 * 24  # 24 hours (in seconds)
        self.open_threshold = 0.7  # 70% open rate is considered good
        self.response_threshold = 24  # 24 hours is standard response time threshold
        
    def get_required_fields(self) -> List[str]:
        """Get required fields for behavior analysis."""
        return ['person_id']
        
    def analyze(self, data: Dict, business_unit: Optional[BusinessUnit] = None) -> Dict:
        """
        Analyze behavioral patterns for a person.
        
        Args:
            data: Dictionary containing person_id
            business_unit: Business unit context for analysis
            
        Returns:
            Dict with behavioral insights and recommendations
        """
        try:
            # Check cache first
            person_id = data.get('person_id')
            cached_result = self.get_cached_result(data, "behavior_insights")
            if cached_result:
                return cached_result
                
            # Validate input
            is_valid, error_message = self.validate_input(data)
            if not is_valid:
                logger.warning(f"Invalid input for behavior analysis: {error_message}")
                return self.get_default_result(error_message)
                
            # Get person data
            person = self._get_person(person_id)
            if not person:
                return self.get_default_result("Person not found")
                
            # Analyze behavior patterns
            email_behavior = self.analyze_email_behavior(person)
            interaction_patterns = self._analyze_interaction_patterns(person)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(email_behavior, interaction_patterns)
            
            # Combine results
            result = {
                'status': 'success',
                'person_id': person_id,
                'email_behavior': email_behavior,
                'interaction_patterns': interaction_patterns,
                'recommendations': recommendations
            }
            
            # Cache and return results
            self.set_cached_result(data, result, "behavior_insights")
            return result
            
        except Exception as e:
            logger.error(f"Error in behavior analysis: {str(e)}", exc_info=True)
            return self.get_default_result(f"Analysis error: {str(e)}")
    
    def _get_person(self, person_id: int) -> Optional[Person]:
        """Get person object from database."""
        try:
            return Person.objects.get(id=person_id)
        except Person.DoesNotExist:
            logger.warning(f"Person with ID {person_id} not found")
            return None
    
    def analyze_email_behavior(self, person: Person) -> Dict:
        """
        Analyze email communication behavior.
        
        Args:
            person: Person object to analyze
            
        Returns:
            Dict with email behavior insights
        """
        try:
            # Get recent email logs
            logs = EmailLog.objects.filter(
                recipient=person,
                created_at__gte=datetime.now() - timedelta(days=7)
            ).order_by('-created_at')
            
            # Calculate metrics
            response_time = self.calculate_response_time(logs)
            open_rate = self.calculate_open_rate(logs)
            recommendation = self.get_recommendation(response_time, open_rate)
            
            return {
                'response_time': response_time,
                'open_rate': open_rate,
                'recommendation': recommendation,
                'last_email': logs.first().created_at if logs.exists() else None,
                'log_count': logs.count(),
                'response_level': self._get_response_level(response_time),
                'engagement_level': self._get_engagement_level(open_rate)
            }
            
        except Exception as e:
            logger.warning(f"Error analyzing email behavior: {str(e)}")
            return {
                'response_time': self.response_threshold,
                'open_rate': 0,
                'recommendation': 'error',
                'last_email': None,
                'log_count': 0,
                'response_level': 'unknown',
                'engagement_level': 'unknown'
            }
    
    def calculate_response_time(self, logs) -> float:
        """
        Calculate average response time in hours.
        
        Args:
            logs: QuerySet of EmailLog objects
            
        Returns:
            float: Average response time in hours
        """
        response_times = []
        for log in logs:
            if log.response_time:
                response_times.append(log.response_time.total_seconds() / 3600)
                
        return sum(response_times) / len(response_times) if response_times else self.response_threshold
    
    def calculate_open_rate(self, logs) -> float:
        """
        Calculate email open rate.
        
        Args:
            logs: QuerySet of EmailLog objects
            
        Returns:
            float: Open rate as decimal (0.0-1.0)
        """
        total = logs.count()
        if not total:
            return 0
            
        opened = sum(1 for log in logs if log.opened)
        return opened / total
    
    def get_recommendation(self, response_time: float, open_rate: float) -> str:
        """
        Generate recommendation based on behavior metrics.
        
        Args:
            response_time: Average response time in hours
            open_rate: Email open rate (0.0-1.0)
            
        Returns:
            str: Recommendation category
        """
        if response_time < self.response_threshold and open_rate > self.open_threshold:
            return 'high_engagement'
        elif response_time > self.response_threshold * 2:
            return 'slow_response'
        elif open_rate < self.open_threshold / 2:
            return 'low_open_rate'
            
        return 'normal'
    
    def _analyze_interaction_patterns(self, person: Person) -> Dict:
        """
        Analyze interaction patterns based on message history.
        
        In a production environment, this would analyze message logs,
        chat history, etc. This implementation provides a simulation.
        
        Args:
            person: Person object to analyze
            
        Returns:
            Dict with interaction pattern insights
        """
        # Simulated interaction pattern analysis
        # In a real implementation, this would use actual data from message logs
        import hashlib
        import random
        
        # Use hash of person ID for consistent results
        seed = int(hashlib.md5(str(person.id).encode()).hexdigest(), 16) % 10000
        random.seed(seed)
        
        # Preferred times of day for communication (24-hour format)
        preferred_times = []
        for _ in range(2):
            preferred_times.append(int(random.uniform(8, 22)))
        preferred_times.sort()
        
        # Preferred channels
        channels = ['email', 'whatsapp', 'phone', 'telegram', 'slack']
        weights = [random.random() for _ in range(len(channels))]
        total = sum(weights)
        normalized_weights = [w/total for w in weights]
        
        channel_preferences = {channels[i]: round(normalized_weights[i], 2) for i in range(len(channels))}
        preferred_channels = sorted(channel_preferences.items(), key=lambda x: x[1], reverse=True)
        
        # Communication frequency
        daily_activity = {
            'morning': round(random.uniform(0, 1), 2),
            'afternoon': round(random.uniform(0, 1), 2),
            'evening': round(random.uniform(0, 1), 2)
        }
        peak_activity = max(daily_activity.items(), key=lambda x: x[1])[0]
        
        return {
            'preferred_channels': [c for c, _ in preferred_channels[:2]],
            'channel_preferences': channel_preferences,
            'preferred_times': preferred_times,
            'daily_activity': daily_activity,
            'peak_activity': peak_activity,
            'response_consistency': round(random.uniform(0.5, 1.0), 2),
            'communication_frequency': round(random.uniform(0.2, 0.8), 2)
        }
    
    def _generate_recommendations(self, email_behavior: Dict, interaction_patterns: Dict) -> List[Dict]:
        """
        Generate actionable recommendations based on behavioral analysis.
        
        Args:
            email_behavior: Email behavior analysis results
            interaction_patterns: Interaction pattern analysis results
            
        Returns:
            List of recommendation dictionaries
        """
        recommendations = []
        
        # Recommendations based on email behavior
        email_recommendation = email_behavior.get('recommendation')
        if email_recommendation == 'high_engagement':
            recommendations.append({
                'type': 'communication',
                'title': 'Alto Compromiso de Comunicación',
                'description': 'Mantener la frecuencia actual de comunicación por email',
                'importance': 'medium'
            })
        elif email_recommendation == 'slow_response':
            recommendations.append({
                'type': 'communication',
                'title': 'Optimizar Tiempo de Respuesta',
                'description': 'Considerar comunicaciones más breves o usar canales más inmediatos',
                'importance': 'high'
            })
        elif email_recommendation == 'low_open_rate':
            recommendations.append({
                'type': 'communication',
                'title': 'Mejorar Tasa de Apertura',
                'description': 'Optimizar líneas de asunto o utilizar canales alternativos',
                'importance': 'high'
            })
        
        # Recommendations based on preferred channels
        preferred_channels = interaction_patterns.get('preferred_channels', [])
        if preferred_channels:
            primary_channel = preferred_channels[0]
            recommendations.append({
                'type': 'channel',
                'title': f'Priorizar {primary_channel.capitalize()}',
                'description': f'Utilizar {primary_channel} como canal principal de comunicación',
                'importance': 'high'
            })
        
        # Recommendations based on preferred times
        preferred_times = interaction_patterns.get('preferred_times', [])
        if preferred_times:
            time_range = f"{min(preferred_times):02d}:00 - {max(preferred_times):02d}:00"
            recommendations.append({
                'type': 'timing',
                'title': 'Horario Óptimo de Comunicación',
                'description': f'Programar comunicaciones importantes entre {time_range}',
                'importance': 'medium'
            })
        
        # Recommendations based on daily activity
        peak_activity = interaction_patterns.get('peak_activity')
        if peak_activity:
            recommendations.append({
                'type': 'timing',
                'title': f'Actividad Pico: {peak_activity.capitalize()}',
                'description': f'Mayor probabilidad de respuesta durante {peak_activity}',
                'importance': 'medium'
            })
        
        return recommendations
    
    def _get_response_level(self, response_time: float) -> str:
        """Categorize response time into a level."""
        if response_time < self.response_threshold / 2:
            return 'fast'
        elif response_time < self.response_threshold:
            return 'normal'
        elif response_time < self.response_threshold * 2:
            return 'slow'
        else:
            return 'very_slow'
    
    def _get_engagement_level(self, open_rate: float) -> str:
        """Categorize open rate into an engagement level."""
        if open_rate > 0.9:
            return 'very_high'
        elif open_rate > self.open_threshold:
            return 'high'
        elif open_rate > self.open_threshold / 2:
            return 'medium'
        elif open_rate > 0.2:
            return 'low'
        else:
            return 'very_low'
