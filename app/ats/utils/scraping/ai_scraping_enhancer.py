"""
SISTEMA DE IA PARA SCRAPING - Grupo huntRED®
Inteligencia artificial para optimizar scraping dinámicamente
"""

import asyncio
import json
import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib
import re

from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)

@dataclass
class ScrapingPattern:
    """Patrón de scraping identificado por IA"""
    platform: str
    success_rate: float
    avg_response_time: float
    blocking_risk: float
    optimal_config: Dict
    last_updated: datetime
    sample_size: int

@dataclass
class BlockingPrediction:
    """Predicción de riesgo de bloqueo"""
    risk_score: float
    confidence: float
    factors: List[str]
    recommendations: List[str]

class AIScrapingEnhancer:
    """
    Sistema de IA para optimizar scraping dinámicamente
    """
    
    def __init__(self):
        self.pattern_analyzer = PatternAnalyzer()
        self.blocking_predictor = BlockingPredictor()
        self.selector_optimizer = SelectorOptimizer()
        self.strategy_optimizer = StrategyOptimizer()
        self.learning_engine = LearningEngine()
        
        # Cache para patrones
        self.pattern_cache = {}
        self.prediction_cache = {}
        
        # Métricas de aprendizaje
        self.learning_metrics = {
            'total_predictions': 0,
            'accurate_predictions': 0,
            'improvements_made': 0,
            'last_optimization': None
        }
    
    async def predict_blocking_risk(self, url: str, platform: str, current_config: Dict) -> BlockingPrediction:
        """Predice probabilidad de bloqueo basado en patrones históricos"""
        cache_key = f"blocking_prediction:{hashlib.md5(f'{url}:{platform}'.encode()).hexdigest()}"
        
        # Verificar cache
        cached_prediction = cache.get(cache_key)
        if cached_prediction and (timezone.now() - cached_prediction['timestamp']).seconds < 300:
            return BlockingPrediction(**cached_prediction['data'])
        
        # Analizar patrones históricos
        historical_patterns = await self._get_historical_patterns(platform)
        
        # Analizar factores de riesgo
        risk_factors = await self._analyze_risk_factors(url, platform, current_config)
        
        # Calcular score de riesgo
        risk_score = await self._calculate_risk_score(risk_factors, historical_patterns)
        
        # Generar recomendaciones
        recommendations = await self._generate_recommendations(risk_score, risk_factors)
        
        # Crear predicción
        prediction = BlockingPrediction(
            risk_score=risk_score,
            confidence=await self._calculate_confidence(historical_patterns),
            factors=risk_factors,
            recommendations=recommendations
        )
        
        # Guardar en cache
        cache.set(cache_key, {
            'data': prediction.__dict__,
            'timestamp': timezone.now()
        }, 300)  # 5 minutos
        
        self.learning_metrics['total_predictions'] += 1
        
        return prediction
    
    async def optimize_selectors(self, platform: str, html_sample: str, current_selectors: Dict) -> Dict:
        """Optimiza selectores usando ML basado en cambios de la página"""
        # Analizar estructura HTML
        html_structure = await self._analyze_html_structure(html_sample)
        
        # Detectar cambios en selectores
        selector_changes = await self._detect_selector_changes(platform, html_structure)
        
        # Generar selectores alternativos
        alternative_selectors = await self._generate_alternative_selectors(html_structure, current_selectors)
        
        # Optimizar selectores
        optimized_selectors = await self._optimize_selector_priority(alternative_selectors, platform)
        
        return optimized_selectors
    
    async def adapt_strategy(self, platform: str, success_rate: float, recent_errors: List[str]) -> Dict:
        """Adapta estrategia de scraping en tiempo real"""
        # Analizar patrones recientes
        recent_patterns = await self._analyze_recent_patterns(platform, success_rate, recent_errors)
        
        # Identificar problemas
        issues = await self._identify_issues(recent_patterns)
        
        # Generar estrategia adaptativa
        adapted_strategy = await self._generate_adapted_strategy(platform, issues, recent_patterns)
        
        # Aplicar optimizaciones
        optimized_config = await self._apply_optimizations(adapted_strategy)
        
        return optimized_config
    
    async def learn_from_success(self, url: str, method: str, config: Dict, response_time: float):
        """Aprende de scraping exitoso"""
        await self.learning_engine.record_success(url, method, config, response_time)
        
        # Actualizar patrones de éxito
        await self._update_success_patterns(url, method, config, response_time)
        
        # Optimizar para futuras requests
        await self._optimize_for_success(url, method, config)
    
    async def learn_from_failure(self, url: str, error: str, config: Dict, platform: str):
        """Aprende de fallos para evitar repetirlos"""
        await self.learning_engine.record_failure(url, error, config, platform)
        
        # Analizar causa del fallo
        failure_cause = await self._analyze_failure_cause(error, config)
        
        # Actualizar estrategias
        await self._update_failure_patterns(url, error, config, failure_cause)
        
        # Ajustar parámetros
        await self._adjust_parameters_for_failure(platform, failure_cause)
    
    async def predict_optimal_config(self, url: str, platform: str) -> Dict:
        """Predice configuración óptima basada en aprendizaje"""
        # Obtener patrones históricos
        historical_patterns = await self._get_historical_patterns(platform)
        
        # Analizar hora del día y día de la semana
        temporal_factors = await self._analyze_temporal_factors()
        
        # Predecir configuración óptima
        optimal_config = await self._predict_config(historical_patterns, temporal_factors, url)
        
        return optimal_config
    
    # Métodos privados de análisis
    
    async def _get_historical_patterns(self, platform: str) -> List[ScrapingPattern]:
        """Obtiene patrones históricos de scraping"""
        cache_key = f"historical_patterns:{platform}"
        patterns = cache.get(cache_key)
        
        if not patterns:
            patterns = await self.learning_engine.get_patterns(platform)
            cache.set(cache_key, patterns, 1800)  # 30 minutos
        
        return patterns
    
    async def _analyze_risk_factors(self, url: str, platform: str, config: Dict) -> List[str]:
        """Analiza factores de riesgo para bloqueo"""
        factors = []
        
        # Analizar URL
        if 'linkedin.com' in url and config.get('rate_limit_requests', 0) > 10:
            factors.append('high_rate_limit_linkedin')
        
        # Analizar hora del día
        current_hour = timezone.now().hour
        if current_hour < 6 or current_hour > 22:
            factors.append('off_hours_activity')
        
        # Analizar configuración
        if not config.get('rotate_user_agents', True):
            factors.append('no_user_agent_rotation')
        
        if not config.get('use_proxy', False):
            factors.append('no_proxy_usage')
        
        # Analizar patrones recientes
        recent_failures = await self.learning_engine.get_recent_failures(platform)
        if len(recent_failures) > 5:
            factors.append('recent_failure_spike')
        
        return factors
    
    async def _calculate_risk_score(self, risk_factors: List[str], patterns: List[ScrapingPattern]) -> float:
        """Calcula score de riesgo basado en factores"""
        base_risk = 0.1
        
        # Factores de riesgo y sus pesos
        risk_weights = {
            'high_rate_limit_linkedin': 0.3,
            'off_hours_activity': 0.2,
            'no_user_agent_rotation': 0.25,
            'no_proxy_usage': 0.2,
            'recent_failure_spike': 0.4
        }
        
        # Calcular riesgo acumulado
        total_risk = base_risk
        for factor in risk_factors:
            total_risk += risk_weights.get(factor, 0.1)
        
        # Normalizar a 0-1
        return min(total_risk, 1.0)
    
    async def _generate_recommendations(self, risk_score: float, risk_factors: List[str]) -> List[str]:
        """Genera recomendaciones basadas en riesgo"""
        recommendations = []
        
        if risk_score > 0.7:
            recommendations.append("Considerar pausa de 30 minutos")
            recommendations.append("Rotar todos los proxies disponibles")
            recommendations.append("Reducir rate limit a la mitad")
        
        elif risk_score > 0.5:
            recommendations.append("Aumentar delay entre requests")
            recommendations.append("Rotar user agents más frecuentemente")
            recommendations.append("Usar proxies residenciales")
        
        elif risk_score > 0.3:
            recommendations.append("Monitorear métricas de éxito")
            recommendations.append("Preparar estrategias de fallback")
        
        # Recomendaciones específicas por factor
        if 'high_rate_limit_linkedin' in risk_factors:
            recommendations.append("Reducir requests a LinkedIn a máximo 10/min")
        
        if 'no_user_agent_rotation' in risk_factors:
            recommendations.append("Habilitar rotación de user agents")
        
        if 'no_proxy_usage' in risk_factors:
            recommendations.append("Configurar pool de proxies")
        
        return recommendations
    
    async def _calculate_confidence(self, patterns: List[ScrapingPattern]) -> float:
        """Calcula confianza de la predicción basada en datos históricos"""
        if not patterns:
            return 0.3
        
        # Calcular confianza basada en cantidad y calidad de datos
        total_samples = sum(p.sample_size for p in patterns)
        avg_success_rate = np.mean([p.success_rate for p in patterns])
        
        # Fórmula de confianza
        confidence = min(0.9, (total_samples / 1000) * avg_success_rate)
        
        return max(0.1, confidence)
    
    async def _analyze_html_structure(self, html: str) -> Dict:
        """Analiza estructura HTML para optimizar selectores"""
        structure = {
            'title_elements': [],
            'company_elements': [],
            'location_elements': [],
            'description_elements': [],
            'common_classes': defaultdict(int),
            'common_ids': defaultdict(int)
        }
        
        # Extraer elementos comunes
        import re
        
        # Buscar elementos de título
        title_patterns = [
            r'<h1[^>]*class="([^"]*)"[^>]*>',
            r'<h2[^>]*class="([^"]*)"[^>]*>',
            r'<h3[^>]*class="([^"]*)"[^>]*>'
        ]
        
        for pattern in title_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            structure['title_elements'].extend(matches)
        
        # Buscar clases comunes
        class_pattern = r'class="([^"]*)"'
        classes = re.findall(class_pattern, html)
        
        for class_list in classes:
            for class_name in class_list.split():
                structure['common_classes'][class_name] += 1
        
        # Buscar IDs comunes
        id_pattern = r'id="([^"]*)"'
        ids = re.findall(id_pattern, html)
        
        for id_name in ids:
            structure['common_ids'][id_name] += 1
        
        return structure
    
    async def _detect_selector_changes(self, platform: str, html_structure: Dict) -> List[str]:
        """Detecta cambios en selectores de la plataforma"""
        changes = []
        
        # Comparar con estructura esperada
        expected_structure = await self._get_expected_structure(platform)
        
        # Detectar cambios en clases comunes
        current_classes = set(html_structure['common_classes'].keys())
        expected_classes = set(expected_structure.get('common_classes', []))
        
        new_classes = current_classes - expected_classes
        removed_classes = expected_classes - current_classes
        
        if new_classes:
            changes.append(f"new_classes_detected: {list(new_classes)[:5]}")
        
        if removed_classes:
            changes.append(f"removed_classes_detected: {list(removed_classes)[:5]}")
        
        return changes
    
    async def _generate_alternative_selectors(self, html_structure: Dict, current_selectors: Dict) -> Dict:
        """Genera selectores alternativos basados en estructura HTML"""
        alternatives = {}
        
        # Generar alternativas para título
        if 'title' in current_selectors:
            title_alternatives = []
            
            # Basado en clases más comunes
            common_classes = sorted(html_structure['common_classes'].items(), 
                                  key=lambda x: x[1], reverse=True)
            
            for class_name, count in common_classes[:10]:
                if any(word in class_name.lower() for word in ['title', 'job', 'position']):
                    title_alternatives.append(f'.{class_name}')
            
            # Basado en estructura H1-H3
            for i in range(1, 4):
                title_alternatives.append(f'h{i}')
            
            alternatives['title'] = title_alternatives
        
        # Generar alternativas para empresa
        if 'company' in current_selectors:
            company_alternatives = []
            
            for class_name, count in common_classes[:10]:
                if any(word in class_name.lower() for word in ['company', 'employer', 'org']):
                    company_alternatives.append(f'.{class_name}')
            
            alternatives['company'] = company_alternatives
        
        return alternatives
    
    async def _optimize_selector_priority(self, alternatives: Dict, platform: str) -> Dict:
        """Optimiza prioridad de selectores basado en éxito histórico"""
        optimized = {}
        
        for field, selectors in alternatives.items():
            # Obtener éxito histórico de cada selector
            selector_scores = []
            
            for selector in selectors:
                success_rate = await self._get_selector_success_rate(selector, platform)
                selector_scores.append((selector, success_rate))
            
            # Ordenar por éxito histórico
            selector_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Tomar los 3 mejores
            optimized[field] = [selector for selector, _ in selector_scores[:3]]
        
        return optimized
    
    async def _analyze_recent_patterns(self, platform: str, success_rate: float, recent_errors: List[str]) -> Dict:
        """Analiza patrones recientes de scraping"""
        patterns = {
            'success_rate_trend': await self._calculate_success_trend(platform),
            'error_patterns': await self._analyze_error_patterns(recent_errors),
            'performance_metrics': await self._get_performance_metrics(platform),
            'blocking_indicators': await self._detect_blocking_indicators(recent_errors)
        }
        
        return patterns
    
    async def _identify_issues(self, patterns: Dict) -> List[str]:
        """Identifica problemas basados en patrones"""
        issues = []
        
        # Analizar tendencia de éxito
        if patterns['success_rate_trend'] < 0.8:
            issues.append('declining_success_rate')
        
        # Analizar patrones de error
        error_patterns = patterns['error_patterns']
        if error_patterns.get('blocking_errors', 0) > 3:
            issues.append('frequent_blocking')
        
        if error_patterns.get('rate_limit_errors', 0) > 2:
            issues.append('rate_limit_issues')
        
        # Analizar indicadores de bloqueo
        blocking_indicators = patterns['blocking_indicators']
        if blocking_indicators.get('captcha_frequency', 0) > 0.1:
            issues.append('captcha_increase')
        
        return issues
    
    async def _generate_adapted_strategy(self, platform: str, issues: List[str], patterns: Dict) -> Dict:
        """Genera estrategia adaptativa basada en problemas identificados"""
        strategy = {
            'rate_limit_adjustment': 1.0,
            'delay_adjustment': 1.0,
            'proxy_rotation_frequency': 1.0,
            'user_agent_rotation_frequency': 1.0,
            'method_priority': ['playwright', 'selenium', 'requests']
        }
        
        # Ajustar basado en problemas
        for issue in issues:
            if issue == 'declining_success_rate':
                strategy['rate_limit_adjustment'] *= 0.7
                strategy['delay_adjustment'] *= 1.5
            
            elif issue == 'frequent_blocking':
                strategy['proxy_rotation_frequency'] *= 2.0
                strategy['user_agent_rotation_frequency'] *= 1.5
                strategy['method_priority'] = ['selenium', 'playwright', 'requests']
            
            elif issue == 'rate_limit_issues':
                strategy['rate_limit_adjustment'] *= 0.5
                strategy['delay_adjustment'] *= 2.0
            
            elif issue == 'captcha_increase':
                strategy['method_priority'] = ['playwright', 'selenium', 'requests']
                strategy['delay_adjustment'] *= 1.3
        
        return strategy
    
    async def _apply_optimizations(self, strategy: Dict) -> Dict:
        """Aplica optimizaciones a la configuración"""
        optimized_config = {
            'max_retries': 3,
            'timeout': 30,
            'delay_between_requests': 2.0,
            'max_concurrent': 2,
            'use_proxy': True,
            'rotate_user_agents': True,
            'enable_anti_detection': True
        }
        
        # Aplicar ajustes de estrategia
        optimized_config['delay_between_requests'] *= strategy['delay_adjustment']
        
        # Ajustar rate limits
        if 'rate_limit_requests' in optimized_config:
            optimized_config['rate_limit_requests'] = int(
                optimized_config['rate_limit_requests'] * strategy['rate_limit_adjustment']
            )
        
        return optimized_config
    
    async def _analyze_temporal_factors(self) -> Dict:
        """Analiza factores temporales para optimización"""
        now = timezone.now()
        
        return {
            'hour_of_day': now.hour,
            'day_of_week': now.weekday(),
            'is_business_hours': 9 <= now.hour <= 17,
            'is_weekend': now.weekday() >= 5,
            'is_holiday': await self._is_holiday(now.date())
        }
    
    async def _predict_config(self, patterns: List[ScrapingPattern], temporal_factors: Dict, url: str) -> Dict:
        """Predice configuración óptima basada en patrones y factores temporales"""
        # Configuración base
        config = {
            'max_retries': 3,
            'timeout': 30,
            'delay_between_requests': 2.0,
            'max_concurrent': 2,
            'use_proxy': True,
            'rotate_user_agents': True,
            'enable_anti_detection': True
        }
        
        # Ajustar basado en patrones históricos
        if patterns:
            best_pattern = max(patterns, key=lambda p: p.success_rate)
            config.update(best_pattern.optimal_config)
        
        # Ajustar basado en factores temporales
        if temporal_factors['is_weekend']:
            config['delay_between_requests'] *= 1.5
            config['max_concurrent'] = max(1, config['max_concurrent'] - 1)
        
        if not temporal_factors['is_business_hours']:
            config['delay_between_requests'] *= 2.0
            config['max_concurrent'] = 1
        
        return config
    
    # Métodos auxiliares
    
    async def _is_holiday(self, date) -> bool:
        """Verifica si es día festivo"""
        # Lista básica de festivos mexicanos
        holidays = [
            (1, 1),   # Año nuevo
            (5, 1),   # Día del trabajo
            (9, 16),  # Independencia
            (11, 20), # Revolución
            (12, 25), # Navidad
        ]
        
        return (date.month, date.day) in holidays
    
    async def _get_expected_structure(self, platform: str) -> Dict:
        """Obtiene estructura esperada para la plataforma"""
        expected_structures = {
            'linkedin': {
                'common_classes': ['job-title', 'company-name', 'location', 'description']
            },
            'workday': {
                'common_classes': ['jobTitle', 'company', 'location', 'jobPostingDescription']
            },
            'indeed': {
                'common_classes': ['jobTitle', 'companyName', 'companyLocation', 'jobDescriptionText']
            }
        }
        
        return expected_structures.get(platform, {})
    
    async def _get_selector_success_rate(self, selector: str, platform: str) -> float:
        """Obtiene tasa de éxito histórica de un selector"""
        cache_key = f"selector_success:{platform}:{hashlib.md5(selector.encode()).hexdigest()}"
        
        success_rate = cache.get(cache_key, 0.5)  # Default 50%
        
        return success_rate
    
    async def _calculate_success_trend(self, platform: str) -> float:
        """Calcula tendencia de éxito reciente"""
        recent_success = await self.learning_engine.get_recent_success_rate(platform)
        return recent_success
    
    async def _analyze_error_patterns(self, errors: List[str]) -> Dict:
        """Analiza patrones de errores"""
        patterns = {
            'blocking_errors': 0,
            'rate_limit_errors': 0,
            'timeout_errors': 0,
            'network_errors': 0
        }
        
        for error in errors:
            error_lower = error.lower()
            
            if any(word in error_lower for word in ['blocked', 'captcha', 'suspicious']):
                patterns['blocking_errors'] += 1
            elif any(word in error_lower for word in ['rate limit', 'too many requests']):
                patterns['rate_limit_errors'] += 1
            elif any(word in error_lower for word in ['timeout', 'timed out']):
                patterns['timeout_errors'] += 1
            elif any(word in error_lower for word in ['network', 'connection']):
                patterns['network_errors'] += 1
        
        return patterns
    
    async def _get_performance_metrics(self, platform: str) -> Dict:
        """Obtiene métricas de performance"""
        return await self.learning_engine.get_performance_metrics(platform)
    
    async def _detect_blocking_indicators(self, errors: List[str]) -> Dict:
        """Detecta indicadores de bloqueo"""
        indicators = {
            'captcha_frequency': 0,
            'blocking_frequency': 0,
            'suspicious_activity_frequency': 0
        }
        
        total_errors = len(errors)
        if total_errors == 0:
            return indicators
        
        for error in errors:
            error_lower = error.lower()
            
            if 'captcha' in error_lower:
                indicators['captcha_frequency'] += 1
            elif 'blocked' in error_lower:
                indicators['blocking_frequency'] += 1
            elif 'suspicious' in error_lower:
                indicators['suspicious_activity_frequency'] += 1
        
        # Convertir a frecuencias
        for key in indicators:
            indicators[key] = indicators[key] / total_errors
        
        return indicators

# Clases auxiliares

class PatternAnalyzer:
    """Analizador de patrones de scraping"""
    
    def __init__(self):
        self.patterns = {}
    
    async def analyze_pattern(self, data: Dict) -> ScrapingPattern:
        """Analiza datos para crear patrón"""
        # Implementación del análisis de patrones
        pass

class BlockingPredictor:
    """Predictor de bloqueos"""
    
    def __init__(self):
        self.models = {}
    
    async def predict_blocking(self, features: Dict) -> float:
        """Predice probabilidad de bloqueo"""
        # Implementación de predicción
        pass

class SelectorOptimizer:
    """Optimizador de selectores"""
    
    def __init__(self):
        self.selector_history = {}
    
    async def optimize_selectors(self, html: str, current_selectors: Dict) -> Dict:
        """Optimiza selectores"""
        # Implementación de optimización
        pass

class StrategyOptimizer:
    """Optimizador de estrategias"""
    
    def __init__(self):
        self.strategies = {}
    
    async def optimize_strategy(self, platform: str, metrics: Dict) -> Dict:
        """Optimiza estrategia de scraping"""
        # Implementación de optimización
        pass

class LearningEngine:
    """Motor de aprendizaje"""
    
    def __init__(self):
        self.success_data = defaultdict(list)
        self.failure_data = defaultdict(list)
        self.patterns = defaultdict(list)
    
    async def record_success(self, url: str, method: str, config: Dict, response_time: float):
        """Registra éxito de scraping"""
        self.success_data[method].append({
            'url': url,
            'config': config,
            'response_time': response_time,
            'timestamp': timezone.now()
        })
    
    async def record_failure(self, url: str, error: str, config: Dict, platform: str):
        """Registra fallo de scraping"""
        self.failure_data[platform].append({
            'url': url,
            'error': error,
            'config': config,
            'timestamp': timezone.now()
        })
    
    async def get_patterns(self, platform: str) -> List[ScrapingPattern]:
        """Obtiene patrones de la plataforma"""
        return self.patterns[platform]
    
    async def get_recent_failures(self, platform: str) -> List[Dict]:
        """Obtiene fallos recientes"""
        now = timezone.now()
        recent_failures = [
            failure for failure in self.failure_data[platform]
            if (now - failure['timestamp']).seconds < 3600  # Última hora
        ]
        return recent_failures
    
    async def get_recent_success_rate(self, platform: str) -> float:
        """Obtiene tasa de éxito reciente"""
        now = timezone.now()
        
        # Obtener éxitos recientes
        recent_successes = []
        for method_data in self.success_data.values():
            recent_successes.extend([
                success for success in method_data
                if (now - success['timestamp']).seconds < 3600
            ])
        
        # Obtener fallos recientes
        recent_failures = await self.get_recent_failures(platform)
        
        total_attempts = len(recent_successes) + len(recent_failures)
        
        if total_attempts == 0:
            return 1.0
        
        return len(recent_successes) / total_attempts
    
    async def get_performance_metrics(self, platform: str) -> Dict:
        """Obtiene métricas de performance"""
        return {
            'avg_response_time': 1.5,
            'success_rate': 0.85,
            'error_rate': 0.15
        }

# Instancia global
ai_scraping_enhancer = AIScrapingEnhancer() 