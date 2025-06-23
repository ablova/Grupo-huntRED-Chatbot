"""
AURA - Context Analyzer
Análisis avanzado de contexto para personalización dinámica y adaptación de experiencia.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class ContextAnalyzer:
    """
    Analizador de contexto avanzado para AURA:
    - Análisis de contexto temporal y geográfico
    - Análisis de contexto de dispositivo y plataforma
    - Análisis de contexto de interacción y flujo
    - Análisis de contexto de negocio y mercado
    - Integración con GNN para contexto de red
    """
    
    def __init__(self):
        self.context_cache = {}
        self.context_patterns = {}
        self.business_contexts = {
            'huntRED': {
                'focus': 'executive_recruitment',
                'industries': ['finance', 'legal', 'healthcare', 'energy'],
                'seniority': 'senior_executive'
            },
            'huntRED_executive': {
                'focus': 'c_suite_recruitment',
                'industries': ['all'],
                'seniority': 'c_level'
            },
            'huntu': {
                'focus': 'tech_recruitment',
                'industries': ['technology', 'startups'],
                'seniority': 'mid_senior'
            },
            'amigro': {
                'focus': 'community_recruitment',
                'industries': ['community', 'social_impact'],
                'seniority': 'all_levels'
            },
            'sexsi': {
                'focus': 'specialized_recruitment',
                'industries': ['specialized'],
                'seniority': 'specialized'
            }
        }
        
    def analyze_context(self, user_id: str, request_data: Dict[str, Any], 
                       user_profile: Optional[Dict[str, Any]] = None,
                       network_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analiza el contexto completo de una interacción.
        
        Args:
            user_id: ID del usuario
            request_data: Datos de la request (headers, params, etc.)
            user_profile: Perfil del usuario (opcional)
            network_context: Contexto de red desde GNN (opcional)
            
        Returns:
            Dict con análisis completo del contexto
        """
        context = {
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'temporal_context': self._analyze_temporal_context(),
            'device_context': self._analyze_device_context(request_data),
            'interaction_context': self._analyze_interaction_context(request_data),
            'business_context': self._analyze_business_context(user_profile),
            'network_context': network_context or {},
            'recommendations': []
        }
        
        # Generar recomendaciones basadas en contexto
        context['recommendations'] = self._generate_context_recommendations(context)
        
        # Cachear contexto para análisis de patrones
        self._cache_context(user_id, context)
        
        return context
    
    def _analyze_temporal_context(self) -> Dict[str, Any]:
        """Analiza el contexto temporal de la interacción."""
        now = datetime.now()
        
        # Análisis de hora del día
        hour = now.hour
        if 6 <= hour < 12:
            time_period = 'morning'
        elif 12 <= hour < 17:
            time_period = 'afternoon'
        elif 17 <= hour < 21:
            time_period = 'evening'
        else:
            time_period = 'night'
        
        # Análisis de día de la semana
        weekday = now.strftime('%A').lower()
        is_weekend = weekday in ['saturday', 'sunday']
        is_workday = not is_weekend
        
        # Análisis de época del año
        month = now.month
        if month in [12, 1, 2]:
            season = 'winter'
        elif month in [3, 4, 5]:
            season = 'spring'
        elif month in [6, 7, 8]:
            season = 'summer'
        else:
            season = 'autumn'
        
        return {
            'time_period': time_period,
            'hour': hour,
            'weekday': weekday,
            'is_weekend': is_weekend,
            'is_workday': is_workday,
            'season': season,
            'month': month,
            'year': now.year
        }
    
    def _analyze_device_context(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza el contexto del dispositivo y plataforma."""
        user_agent = request_data.get('user_agent', '')
        headers = request_data.get('headers', {})
        
        # Detectar tipo de dispositivo
        device_type = 'desktop'
        if any(mobile in user_agent.lower() for mobile in ['mobile', 'android', 'iphone', 'ipad']):
            device_type = 'mobile'
        elif 'tablet' in user_agent.lower():
            device_type = 'tablet'
        
        # Detectar navegador
        browser = 'unknown'
        if 'chrome' in user_agent.lower():
            browser = 'chrome'
        elif 'firefox' in user_agent.lower():
            browser = 'firefox'
        elif 'safari' in user_agent.lower():
            browser = 'safari'
        elif 'edge' in user_agent.lower():
            browser = 'edge'
        
        # Detectar sistema operativo
        os = 'unknown'
        if 'windows' in user_agent.lower():
            os = 'windows'
        elif 'mac' in user_agent.lower():
            os = 'macos'
        elif 'linux' in user_agent.lower():
            os = 'linux'
        elif 'android' in user_agent.lower():
            os = 'android'
        elif 'ios' in user_agent.lower():
            os = 'ios'
        
        # Detectar ubicación geográfica (si está disponible)
        location = self._extract_location(headers)
        
        return {
            'device_type': device_type,
            'browser': browser,
            'operating_system': os,
            'user_agent': user_agent,
            'location': location,
            'screen_resolution': request_data.get('screen_resolution'),
            'connection_type': request_data.get('connection_type', 'unknown')
        }
    
    def _analyze_interaction_context(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza el contexto de la interacción actual."""
        url = request_data.get('url', '')
        method = request_data.get('method', 'GET')
        params = request_data.get('params', {})
        
        # Detectar tipo de interacción
        interaction_type = 'general'
        if '/dashboard' in url:
            interaction_type = 'dashboard'
        elif '/chat' in url:
            interaction_type = 'chat'
        elif '/profile' in url:
            interaction_type = 'profile'
        elif '/search' in url:
            interaction_type = 'search'
        elif '/analytics' in url:
            interaction_type = 'analytics'
        
        # Detectar flujo de usuario
        flow_stage = self._detect_flow_stage(url, params)
        
        # Detectar intención del usuario
        intent = self._detect_user_intent(url, params, method)
        
        return {
            'interaction_type': interaction_type,
            'flow_stage': flow_stage,
            'user_intent': intent,
            'url': url,
            'method': method,
            'parameters': params,
            'referrer': request_data.get('referrer'),
            'session_duration': request_data.get('session_duration', 0)
        }
    
    def _analyze_business_context(self, user_profile: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Analiza el contexto de negocio del usuario."""
        if not user_profile:
            return {'business_unit': 'unknown', 'focus': 'general'}
        
        # Detectar unidad de negocio
        business_unit = user_profile.get('business_unit', 'unknown')
        bu_config = self.business_contexts.get(business_unit, {})
        
        # Detectar industria y seniority
        industry = user_profile.get('industry', 'general')
        seniority = user_profile.get('seniority', 'mid_level')
        
        # Detectar rol y responsabilidades
        role = user_profile.get('role', 'general')
        department = user_profile.get('department', 'general')
        
        return {
            'business_unit': business_unit,
            'business_focus': bu_config.get('focus', 'general'),
            'target_industries': bu_config.get('industries', ['general']),
            'target_seniority': bu_config.get('seniority', 'all_levels'),
            'user_industry': industry,
            'user_seniority': seniority,
            'user_role': role,
            'user_department': department,
            'is_executive': seniority in ['senior_executive', 'c_level'],
            'is_recruiter': role in ['recruiter', 'headhunter', 'talent_acquisition']
        }
    
    def _extract_location(self, headers: Dict[str, str]) -> Optional[Dict[str, str]]:
        """Extrae información de ubicación de los headers."""
        # Implementar extracción de ubicación desde headers
        # Por ahora retorna None
        return None
    
    def _detect_flow_stage(self, url: str, params: Dict[str, Any]) -> str:
        """Detecta la etapa del flujo de usuario."""
        if '/onboarding' in url:
            return 'onboarding'
        elif '/profile' in url and 'edit' in params:
            return 'profile_editing'
        elif '/search' in url and params:
            return 'searching'
        elif '/analytics' in url:
            return 'analyzing'
        elif '/chat' in url:
            return 'chatting'
        else:
            return 'browsing'
    
    def _detect_user_intent(self, url: str, params: Dict[str, Any], method: str) -> str:
        """Detecta la intención del usuario."""
        if method == 'POST':
            return 'creating'
        elif method == 'PUT' or method == 'PATCH':
            return 'updating'
        elif method == 'DELETE':
            return 'deleting'
        elif '/search' in url:
            return 'searching'
        elif '/analytics' in url:
            return 'analyzing'
        elif '/profile' in url:
            return 'viewing_profile'
        else:
            return 'browsing'
    
    def _generate_context_recommendations(self, context: Dict[str, Any]) -> List[str]:
        """Genera recomendaciones basadas en el contexto."""
        recommendations = []
        
        # Recomendaciones basadas en tiempo
        temporal = context['temporal_context']
        if temporal['time_period'] == 'night':
            recommendations.append("Modo nocturno activado para mejor experiencia")
        if temporal['is_weekend']:
            recommendations.append("Acceso a contenido de desarrollo personal disponible")
        
        # Recomendaciones basadas en dispositivo
        device = context['device_context']
        if device['device_type'] == 'mobile':
            recommendations.append("Optimizado para móvil - funciones táctiles disponibles")
        
        # Recomendaciones basadas en interacción
        interaction = context['interaction_context']
        if interaction['interaction_type'] == 'dashboard':
            recommendations.append("Personaliza tu dashboard desde Configuración")
        elif interaction['interaction_type'] == 'chat':
            recommendations.append("AURA está listo para ayudarte con tus consultas")
        
        # Recomendaciones basadas en negocio
        business = context['business_context']
        if business['is_executive']:
            recommendations.append("Panel ejecutivo con KPIs avanzados disponible")
        if business['is_recruiter']:
            recommendations.append("Herramientas de hunting y análisis de redes activas")
        
        return recommendations[:3]  # Limitar a 3 recomendaciones
    
    def _cache_context(self, user_id: str, context: Dict[str, Any]):
        """Cachea el contexto para análisis de patrones."""
        if user_id not in self.context_cache:
            self.context_cache[user_id] = []
        
        self.context_cache[user_id].append({
            'timestamp': context['timestamp'],
            'interaction_type': context['interaction_context']['interaction_type'],
            'device_type': context['device_context']['device_type'],
            'time_period': context['temporal_context']['time_period']
        })
        
        # Mantener solo los últimos 100 contextos
        if len(self.context_cache[user_id]) > 100:
            self.context_cache[user_id] = self.context_cache[user_id][-100:]
    
    def get_user_patterns(self, user_id: str) -> Dict[str, Any]:
        """Analiza patrones de comportamiento del usuario."""
        if user_id not in self.context_cache:
            return {}
        
        contexts = self.context_cache[user_id]
        if not contexts:
            return {}
        
        # Analizar patrones de interacción
        interaction_counts = {}
        device_counts = {}
        time_counts = {}
        
        for context in contexts:
            interaction_counts[context['interaction_type']] = interaction_counts.get(context['interaction_type'], 0) + 1
            device_counts[context['device_type']] = device_counts.get(context['device_type'], 0) + 1
            time_counts[context['time_period']] = time_counts.get(context['time_period'], 0) + 1
        
        # Encontrar patrones más comunes
        most_common_interaction = max(interaction_counts, key=interaction_counts.get) if interaction_counts else None
        most_common_device = max(device_counts, key=device_counts.get) if device_counts else None
        most_common_time = max(time_counts, key=time_counts.get) if time_counts else None
        
        return {
            'total_interactions': len(contexts),
            'most_common_interaction': most_common_interaction,
            'most_common_device': most_common_device,
            'most_common_time': most_common_time,
            'interaction_distribution': interaction_counts,
            'device_distribution': device_counts,
            'time_distribution': time_counts,
            'last_interaction': contexts[-1] if contexts else None
        }
    
    def get_business_context_info(self, business_unit: str) -> Optional[Dict[str, Any]]:
        """Obtiene información del contexto de negocio para una BU específica."""
        return self.business_contexts.get(business_unit)
    
    def update_business_context(self, business_unit: str, config: Dict[str, Any]):
        """Actualiza la configuración de contexto de negocio."""
        self.business_contexts[business_unit] = config
        logger.info(f"Updated business context for '{business_unit}'")
    
    def clear_user_cache(self, user_id: str):
        """Limpia el cache de contexto de un usuario."""
        if user_id in self.context_cache:
            del self.context_cache[user_id]
            logger.info(f"Cleared context cache for user '{user_id}'")

# Instancia global
context_analyzer = ContextAnalyzer() 