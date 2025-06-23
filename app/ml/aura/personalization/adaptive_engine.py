"""
AURA - Adaptive Engine
Motor de adaptación dinámica que ajusta la experiencia en tiempo real basado en comportamiento y contexto.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import numpy as np

logger = logging.getLogger(__name__)

class AdaptiveEngine:
    """
    Motor de adaptación dinámica para AURA:
    - Aprendizaje continuo del comportamiento del usuario
    - Adaptación de UI, contenido y funcionalidades
    - Optimización de experiencia basada en feedback
    - Integración con GNN para adaptación contextual
    - A/B testing automático de adaptaciones
    """
    
    def __init__(self):
        self.user_adaptations = {}
        self.learning_data = {}
        self.adaptation_rules = {}
        self.ab_tests = {}
        self.performance_metrics = {}
        
        # Configurar reglas de adaptación por defecto
        self._setup_default_rules()
        
    def _setup_default_rules(self):
        """Configura reglas de adaptación por defecto."""
        self.adaptation_rules = {
            'ui_complexity': {
                'executive': 'advanced',
                'junior': 'simple',
                'recruiter': 'intermediate',
                'student': 'simple',
                'default': 'intermediate'
            },
            'content_focus': {
                'executive': 'strategic',
                'junior': 'learning',
                'recruiter': 'operational',
                'student': 'educational',
                'default': 'balanced'
            },
            'interaction_style': {
                'executive': 'efficient',
                'junior': 'guided',
                'recruiter': 'analytical',
                'student': 'exploratory',
                'default': 'balanced'
            },
            'notification_frequency': {
                'executive': 'low',
                'junior': 'medium',
                'recruiter': 'high',
                'student': 'medium',
                'default': 'medium'
            }
        }
    
    def adapt_experience(self, user_id: str, user_profile: Dict[str, Any], 
                        context: Dict[str, Any], current_behavior: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adapta la experiencia del usuario basado en múltiples factores.
        
        Args:
            user_id: ID del usuario
            user_profile: Perfil del usuario
            context: Contexto actual de la interacción
            current_behavior: Comportamiento actual del usuario
            
        Returns:
            Dict con adaptaciones aplicadas
        """
        # Obtener segmento del usuario
        segment = user_profile.get('segment', 'default')
        
        # Analizar comportamiento actual
        behavior_analysis = self._analyze_behavior(user_id, current_behavior)
        
        # Generar adaptaciones
        adaptations = {
            'ui_config': self._adapt_ui(user_id, segment, context, behavior_analysis),
            'content_config': self._adapt_content(user_id, segment, context, behavior_analysis),
            'interaction_config': self._adapt_interactions(user_id, segment, context, behavior_analysis),
            'notification_config': self._adapt_notifications(user_id, segment, context, behavior_analysis),
            'feature_flags': self._adapt_features(user_id, segment, context, behavior_analysis)
        }
        
        # Aplicar A/B testing si está habilitado
        if self._should_apply_ab_test(user_id, adaptations):
            adaptations = self._apply_ab_test(user_id, adaptations)
        
        # Aprender de la adaptación
        self._learn_from_adaptation(user_id, adaptations, behavior_analysis)
        
        # Guardar adaptación
        self.user_adaptations[user_id] = {
            'adaptations': adaptations,
            'timestamp': datetime.now().isoformat(),
            'context': context,
            'behavior_analysis': behavior_analysis
        }
        
        return adaptations
    
    def _analyze_behavior(self, user_id: str, current_behavior: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza el comportamiento actual del usuario."""
        if user_id not in self.learning_data:
            self.learning_data[user_id] = {
                'interactions': [],
                'preferences': {},
                'performance': {}
            }
        
        # Analizar patrones de interacción
        interaction_patterns = self._analyze_interaction_patterns(user_id, current_behavior)
        
        # Analizar preferencias implícitas
        implicit_preferences = self._analyze_implicit_preferences(user_id, current_behavior)
        
        # Analizar rendimiento y engagement
        performance_metrics = self._analyze_performance_metrics(user_id, current_behavior)
        
        return {
            'interaction_patterns': interaction_patterns,
            'implicit_preferences': implicit_preferences,
            'performance_metrics': performance_metrics,
            'engagement_level': self._calculate_engagement_level(performance_metrics),
            'learning_style': self._infer_learning_style(interaction_patterns),
            'efficiency_preference': self._infer_efficiency_preference(interaction_patterns)
        }
    
    def _adapt_ui(self, user_id: str, segment: str, context: Dict[str, Any], 
                 behavior_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Adapta la configuración de UI."""
        base_complexity = self.adaptation_rules['ui_complexity'].get(segment, 'intermediate')
        
        # Ajustar complejidad basado en comportamiento
        if behavior_analysis['efficiency_preference'] == 'high':
            complexity = 'advanced'
        elif behavior_analysis['engagement_level'] == 'low':
            complexity = 'simple'
        else:
            complexity = base_complexity
        
        # Adaptar tema basado en contexto temporal
        theme = 'light'
        if context.get('temporal_context', {}).get('time_period') == 'night':
            theme = 'dark'
        
        # Adaptar layout basado en dispositivo
        layout = 'standard'
        if context.get('device_context', {}).get('device_type') == 'mobile':
            layout = 'mobile_optimized'
        
        return {
            'complexity': complexity,
            'theme': theme,
            'layout': layout,
            'widgets': self._get_adaptive_widgets(segment, behavior_analysis),
            'animations': behavior_analysis['engagement_level'] != 'low',
            'accessibility': self._get_accessibility_config(behavior_analysis)
        }
    
    def _adapt_content(self, user_id: str, segment: str, context: Dict[str, Any], 
                      behavior_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Adapta el contenido mostrado al usuario."""
        content_focus = self.adaptation_rules['content_focus'].get(segment, 'balanced')
        
        # Ajustar enfoque basado en comportamiento
        if behavior_analysis['learning_style'] == 'visual':
            content_format = 'visual_heavy'
        elif behavior_analysis['learning_style'] == 'textual':
            content_format = 'text_heavy'
        else:
            content_format = 'balanced'
        
        # Determinar nivel de detalle
        detail_level = 'standard'
        if segment == 'executive':
            detail_level = 'summary'
        elif behavior_analysis['efficiency_preference'] == 'high':
            detail_level = 'summary'
        
        return {
            'focus': content_focus,
            'format': content_format,
            'detail_level': detail_level,
            'language': self._get_adaptive_language(segment, context),
            'topics': self._get_adaptive_topics(segment, behavior_analysis),
            'recommendations_count': self._get_recommendations_count(behavior_analysis)
        }
    
    def _adapt_interactions(self, user_id: str, segment: str, context: Dict[str, Any], 
                          behavior_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Adapta el estilo de interacción."""
        interaction_style = self.adaptation_rules['interaction_style'].get(segment, 'balanced')
        
        # Ajustar estilo basado en comportamiento
        if behavior_analysis['efficiency_preference'] == 'high':
            interaction_style = 'efficient'
        elif behavior_analysis['engagement_level'] == 'low':
            interaction_style = 'guided'
        
        return {
            'style': interaction_style,
            'guidance_level': self._get_guidance_level(segment, behavior_analysis),
            'shortcuts_enabled': behavior_analysis['efficiency_preference'] == 'high',
            'auto_suggestions': behavior_analysis['engagement_level'] != 'low',
            'confirmation_dialogs': segment != 'executive',
            'tutorial_mode': behavior_analysis['engagement_level'] == 'low'
        }
    
    def _adapt_notifications(self, user_id: str, segment: str, context: Dict[str, Any], 
                           behavior_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Adapta la configuración de notificaciones."""
        base_frequency = self.adaptation_rules['notification_frequency'].get(segment, 'medium')
        
        # Ajustar frecuencia basado en comportamiento
        if behavior_analysis['engagement_level'] == 'high':
            frequency = 'high'
        elif behavior_analysis['engagement_level'] == 'low':
            frequency = 'low'
        else:
            frequency = base_frequency
        
        return {
            'frequency': frequency,
            'channels': self._get_notification_channels(segment, context),
            'priority_levels': self._get_priority_levels(segment),
            'quiet_hours': self._get_quiet_hours(context),
            'personalization': behavior_analysis['engagement_level'] != 'low'
        }
    
    def _adapt_features(self, user_id: str, segment: str, context: Dict[str, Any], 
                       behavior_analysis: Dict[str, Any]) -> Dict[str, bool]:
        """Adapta las funcionalidades disponibles."""
        features = {
            'advanced_analytics': segment in ['executive', 'recruiter'],
            'ai_assistant': True,
            'social_features': behavior_analysis['engagement_level'] != 'low',
            'learning_modules': segment in ['junior', 'student'],
            'networking_tools': True,
            'automation_features': segment in ['executive', 'recruiter'],
            'customization_options': behavior_analysis['engagement_level'] != 'low',
            'export_capabilities': segment in ['executive', 'recruiter'],
            'batch_operations': segment in ['executive', 'recruiter'],
            'real_time_updates': behavior_analysis['engagement_level'] != 'low'
        }
        
        # Ajustar basado en comportamiento
        if behavior_analysis['efficiency_preference'] == 'high':
            features['automation_features'] = True
            features['batch_operations'] = True
        
        return features
    
    def _analyze_interaction_patterns(self, user_id: str, current_behavior: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza patrones de interacción del usuario."""
        # Implementar análisis de patrones
        return {
            'click_patterns': 'standard',
            'navigation_style': 'exploratory',
            'feature_usage': 'balanced',
            'session_duration': 'medium'
        }
    
    def _analyze_implicit_preferences(self, user_id: str, current_behavior: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza preferencias implícitas del usuario."""
        # Implementar análisis de preferencias implícitas
        return {
            'content_type': 'mixed',
            'interaction_speed': 'medium',
            'detail_preference': 'standard',
            'social_interaction': 'moderate'
        }
    
    def _analyze_performance_metrics(self, user_id: str, current_behavior: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza métricas de rendimiento del usuario."""
        # Implementar análisis de métricas
        return {
            'task_completion_rate': 0.85,
            'error_rate': 0.05,
            'time_to_complete': 'medium',
            'feature_adoption': 'high'
        }
    
    def _calculate_engagement_level(self, performance_metrics: Dict[str, Any]) -> str:
        """Calcula el nivel de engagement del usuario."""
        completion_rate = performance_metrics.get('task_completion_rate', 0.5)
        error_rate = performance_metrics.get('error_rate', 0.2)
        adoption = performance_metrics.get('feature_adoption', 'medium')
        
        if completion_rate > 0.8 and error_rate < 0.1 and adoption == 'high':
            return 'high'
        elif completion_rate > 0.6 and error_rate < 0.2:
            return 'medium'
        else:
            return 'low'
    
    def _infer_learning_style(self, interaction_patterns: Dict[str, Any]) -> str:
        """Infiere el estilo de aprendizaje del usuario."""
        # Implementar inferencia de estilo de aprendizaje
        return 'balanced'
    
    def _infer_efficiency_preference(self, interaction_patterns: Dict[str, Any]) -> str:
        """Infiere la preferencia de eficiencia del usuario."""
        # Implementar inferencia de preferencia de eficiencia
        return 'medium'
    
    def _get_adaptive_widgets(self, segment: str, behavior_analysis: Dict[str, Any]) -> List[str]:
        """Obtiene widgets adaptativos para el dashboard."""
        base_widgets = ['network', 'skills', 'alerts']
        
        if segment == 'executive':
            base_widgets.extend(['kpi', 'market_trends'])
        elif segment == 'recruiter':
            base_widgets.extend(['candidate_pipeline', 'hiring_metrics'])
        elif segment in ['junior', 'student']:
            base_widgets.extend(['learning_progress', 'mentorship'])
        
        if behavior_analysis['engagement_level'] == 'high':
            base_widgets.append('advanced_analytics')
        
        return base_widgets
    
    def _get_accessibility_config(self, behavior_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene configuración de accesibilidad."""
        return {
            'high_contrast': False,
            'large_text': False,
            'screen_reader_support': True,
            'keyboard_navigation': True
        }
    
    def _get_adaptive_language(self, segment: str, context: Dict[str, Any]) -> str:
        """Obtiene el idioma adaptativo."""
        # Implementar lógica de idioma adaptativo
        return 'es'
    
    def _get_adaptive_topics(self, segment: str, behavior_analysis: Dict[str, Any]) -> List[str]:
        """Obtiene temas adaptativos para el contenido."""
        base_topics = ['career_development', 'networking']
        
        if segment == 'executive':
            base_topics.extend(['leadership', 'strategy'])
        elif segment == 'recruiter':
            base_topics.extend(['talent_acquisition', 'market_analysis'])
        elif segment in ['junior', 'student']:
            base_topics.extend(['skill_development', 'mentorship'])
        
        return base_topics
    
    def _get_recommendations_count(self, behavior_analysis: Dict[str, Any]) -> int:
        """Obtiene el número de recomendaciones a mostrar."""
        if behavior_analysis['engagement_level'] == 'high':
            return 5
        elif behavior_analysis['engagement_level'] == 'low':
            return 2
        else:
            return 3
    
    def _get_guidance_level(self, segment: str, behavior_analysis: Dict[str, Any]) -> str:
        """Obtiene el nivel de guía para el usuario."""
        if segment == 'executive':
            return 'minimal'
        elif behavior_analysis['engagement_level'] == 'low':
            return 'high'
        else:
            return 'medium'
    
    def _get_notification_channels(self, segment: str, context: Dict[str, Any]) -> List[str]:
        """Obtiene canales de notificación adaptativos."""
        channels = ['email']
        
        if segment == 'executive':
            channels.append('priority_email')
        else:
            channels.extend(['push', 'in_app'])
        
        return channels
    
    def _get_priority_levels(self, segment: str) -> Dict[str, str]:
        """Obtiene niveles de prioridad para notificaciones."""
        if segment == 'executive':
            return {
                'urgent': 'immediate',
                'important': 'within_hour',
                'normal': 'daily'
            }
        else:
            return {
                'urgent': 'within_hour',
                'important': 'daily',
                'normal': 'weekly'
            }
    
    def _get_quiet_hours(self, context: Dict[str, Any]) -> Dict[str, str]:
        """Obtiene horas de silencio para notificaciones."""
        temporal = context.get('temporal_context', {})
        
        if temporal.get('time_period') == 'night':
            return {'start': '22:00', 'end': '08:00'}
        else:
            return {'start': '23:00', 'end': '07:00'}
    
    def _should_apply_ab_test(self, user_id: str, adaptations: Dict[str, Any]) -> bool:
        """Determina si se debe aplicar A/B testing."""
        # Implementar lógica de A/B testing
        return False
    
    def _apply_ab_test(self, user_id: str, adaptations: Dict[str, Any]) -> Dict[str, Any]:
        """Aplica A/B testing a las adaptaciones."""
        # Implementar A/B testing
        return adaptations
    
    def _learn_from_adaptation(self, user_id: str, adaptations: Dict[str, Any], 
                              behavior_analysis: Dict[str, Any]):
        """Aprende de la adaptación aplicada."""
        if user_id not in self.learning_data:
            self.learning_data[user_id] = {'interactions': [], 'preferences': {}, 'performance': {}}
        
        # Guardar datos de aprendizaje
        self.learning_data[user_id]['interactions'].append({
            'timestamp': datetime.now().isoformat(),
            'adaptations': adaptations,
            'behavior': behavior_analysis
        })
        
        # Limitar historial
        if len(self.learning_data[user_id]['interactions']) > 1000:
            self.learning_data[user_id]['interactions'] = self.learning_data[user_id]['interactions'][-1000:]
    
    def get_user_adaptation_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Obtiene el historial de adaptaciones de un usuario."""
        if user_id in self.learning_data:
            return self.learning_data[user_id]['interactions']
        return []
    
    def update_adaptation_rule(self, rule_name: str, segment: str, value: Any):
        """Actualiza una regla de adaptación."""
        if rule_name in self.adaptation_rules:
            self.adaptation_rules[rule_name][segment] = value
            logger.info(f"Updated adaptation rule '{rule_name}' for segment '{segment}'")
    
    def get_adaptation_performance(self, user_id: str) -> Dict[str, Any]:
        """Obtiene métricas de rendimiento de las adaptaciones."""
        if user_id in self.performance_metrics:
            return self.performance_metrics[user_id]
        return {}
    
    def reset_user_adaptations(self, user_id: str):
        """Resetea las adaptaciones de un usuario."""
        if user_id in self.user_adaptations:
            del self.user_adaptations[user_id]
        if user_id in self.learning_data:
            del self.learning_data[user_id]
        if user_id in self.performance_metrics:
            del self.performance_metrics[user_id]
        logger.info(f"Reset adaptations for user '{user_id}'")

# Instancia global
adaptive_engine = AdaptiveEngine() 