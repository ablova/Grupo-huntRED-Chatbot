"""
Generador de Descripciones de Puestos para huntRED®

Este módulo implementa la generación inteligente de descripciones de puestos
usando el sistema ML existente y análisis de mercado.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio

from django.conf import settings
from django.core.cache import cache

from app.models import BusinessUnit, Vacante
from app.ml.aura import AuraEngine
from app.ml.analyzers.market_analyzer import MarketAnalyzer
from app.ml.analyzers.salary_analyzer import SalaryAnalyzer

logger = logging.getLogger(__name__)

class JobDescriptionGenerator:
    """
    Generador inteligente de descripciones de puestos para huntRED®.
    
    Funcionalidades específicas para reclutamiento:
    - Generación de descripciones basadas en análisis de mercado
    - Optimización para ATS y SEO
    - Personalización por unidad de negocio
    - Análisis de competencia y salarios
    - Integración con AURA para compatibilidad
    """
    
    def __init__(self, business_unit: BusinessUnit):
        """
        Inicializa el generador de descripciones.
        
        Args:
            business_unit: Unidad de negocio para personalización.
        """
        self.business_unit = business_unit
        self.logger = logging.getLogger('job_description_generator')
        
        # Inicializar componentes ML existentes
        self.aura_engine = AuraEngine()
        self.market_analyzer = MarketAnalyzer()
        self.salary_analyzer = SalaryAnalyzer()
        
        # Configuración
        self.cache_ttl = 3600  # 1 hora
        
    async def generate_job_description(self, 
                                     position: str,
                                     requirements: List[str],
                                     location: str,
                                     experience_level: str = 'mid',
                                     style: str = 'professional') -> Dict[str, Any]:
        """
        Genera descripción de puesto inteligente.
        
        Args:
            position: Título del puesto.
            requirements: Lista de requisitos.
            location: Ubicación del puesto.
            experience_level: Nivel de experiencia.
            style: Estilo de la descripción.
            
        Returns:
            Descripción generada con análisis de mercado.
        """
        try:
            # Verificar caché
            cache_key = self._generate_cache_key(position, requirements, location, experience_level)
            cached_description = cache.get(cache_key)
            if cached_description:
                return cached_description
            
            # Análisis de mercado
            market_analysis = await self._analyze_market_position(position, location)
            
            # Análisis de salarios
            salary_analysis = await self._analyze_salary_range(position, location, experience_level)
            
            # Generar descripción base
            description = await self._generate_base_description(
                position, requirements, location, experience_level, style
            )
            
            # Optimizar para ATS
            optimized_description = await self._optimize_for_ats(description, position, requirements)
            
            # Añadir análisis de mercado
            final_description = await self._add_market_insights(
                optimized_description, market_analysis, salary_analysis
            )
            
            # Crear resultado completo
            result = {
                'title': position,
                'description': final_description,
                'market_analysis': market_analysis,
                'salary_analysis': salary_analysis,
                'ats_optimization_score': await self._calculate_ats_score(final_description),
                'seo_keywords': await self._extract_seo_keywords(final_description),
                'estimated_applications': await self._estimate_applications(market_analysis),
                'generated_at': datetime.now().isoformat()
            }
            
            # Guardar en caché
            cache.set(cache_key, result, self.cache_ttl)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error generando descripción de puesto: {str(e)}")
            raise
    
    async def generate_multiple_variations(self, 
                                         position: str,
                                         requirements: List[str],
                                         location: str,
                                         num_variations: int = 3) -> List[Dict[str, Any]]:
        """
        Genera múltiples variaciones de una descripción.
        
        Args:
            position: Título del puesto.
            requirements: Lista de requisitos.
            location: Ubicación del puesto.
            num_variations: Número de variaciones.
            
        Returns:
            Lista de variaciones generadas.
        """
        try:
            variations = []
            styles = ['professional', 'modern', 'detailed', 'concise']
            
            for i in range(num_variations):
                style = styles[i % len(styles)]
                variation = await self.generate_job_description(
                    position, requirements, location, style=style
                )
                variations.append(variation)
            
            return variations
            
        except Exception as e:
            self.logger.error(f"Error generando variaciones: {str(e)}")
            raise
    
    async def optimize_existing_description(self, 
                                          existing_description: str,
                                          position: str,
                                          target_audience: str) -> Dict[str, Any]:
        """
        Optimiza una descripción existente.
        
        Args:
            existing_description: Descripción existente.
            position: Título del puesto.
            target_audience: Audiencia objetivo.
            
        Returns:
            Descripción optimizada con mejoras.
        """
        try:
            # Analizar descripción existente
            analysis = await self._analyze_existing_description(existing_description)
            
            # Generar mejoras
            improvements = await self._generate_improvements(
                existing_description, analysis, target_audience
            )
            
            # Aplicar mejoras
            optimized_description = await self._apply_improvements(
                existing_description, improvements
            )
            
            return {
                'original': existing_description,
                'optimized': optimized_description,
                'improvements': improvements,
                'analysis': analysis,
                'optimization_score': await self._calculate_optimization_score(improvements)
            }
            
        except Exception as e:
            self.logger.error(f"Error optimizando descripción: {str(e)}")
            raise
    
    # Métodos privados
    
    async def _analyze_market_position(self, position: str, location: str) -> Dict[str, Any]:
        """Analiza la posición en el mercado."""
        try:
            market_data = await self.market_analyzer.analyze_position_market(
                position=position,
                location=location,
                business_unit=self.business_unit
            )
            
            return {
                'demand_level': market_data.get('demand_level', 'medium'),
                'competition_level': market_data.get('competition_level', 'medium'),
                'trend': market_data.get('trend', 'stable'),
                'key_skills': market_data.get('key_skills', []),
                'market_insights': market_data.get('insights', [])
            }
            
        except Exception as e:
            self.logger.error(f"Error analizando mercado: {str(e)}")
            return {
                'demand_level': 'medium',
                'competition_level': 'medium',
                'trend': 'stable',
                'key_skills': [],
                'market_insights': []
            }
    
    async def _analyze_salary_range(self, position: str, location: str, experience_level: str) -> Dict[str, Any]:
        """Analiza el rango salarial."""
        try:
            salary_data = await self.salary_analyzer.analyze_position_salary(
                position=position,
                location=location,
                experience_level=experience_level
            )
            
            return {
                'min_salary': salary_data.get('min_salary', 0),
                'max_salary': salary_data.get('max_salary', 0),
                'avg_salary': salary_data.get('avg_salary', 0),
                'salary_trend': salary_data.get('trend', 'stable'),
                'benefits_insights': salary_data.get('benefits', [])
            }
            
        except Exception as e:
            self.logger.error(f"Error analizando salarios: {str(e)}")
            return {
                'min_salary': 0,
                'max_salary': 0,
                'avg_salary': 0,
                'salary_trend': 'stable',
                'benefits_insights': []
            }
    
    async def _generate_base_description(self, 
                                       position: str,
                                       requirements: List[str],
                                       location: str,
                                       experience_level: str,
                                       style: str) -> str:
        """Genera descripción base."""
        try:
            # Usar el sistema ML existente para generar contenido
            prompt = self._build_description_prompt(
                position, requirements, location, experience_level, style
            )
            
            # Aquí usaríamos el sistema de generación existente
            # Por ahora, simulamos la generación
            description = self._simulate_description_generation(prompt, style)
            
            return description
            
        except Exception as e:
            self.logger.error(f"Error generando descripción base: {str(e)}")
            raise
    
    async def _optimize_for_ats(self, description: str, position: str, requirements: List[str]) -> str:
        """Optimiza la descripción para ATS."""
        try:
            # Añadir palabras clave relevantes
            keywords = await self._extract_keywords(position, requirements)
            
            # Optimizar estructura
            optimized = self._restructure_for_ats(description, keywords)
            
            return optimized
            
        except Exception as e:
            self.logger.error(f"Error optimizando para ATS: {str(e)}")
            return description
    
    async def _add_market_insights(self, 
                                 description: str,
                                 market_analysis: Dict[str, Any],
                                 salary_analysis: Dict[str, Any]) -> str:
        """Añade insights de mercado a la descripción."""
        try:
            # Añadir información de mercado si es relevante
            if market_analysis.get('demand_level') == 'high':
                description += "\n\n💼 **Oportunidad de Mercado:** Esta posición está en alta demanda en el mercado actual."
            
            if salary_analysis.get('salary_trend') == 'increasing':
                description += "\n💰 **Salario Competitivo:** Ofrecemos un paquete salarial competitivo que refleja las tendencias del mercado."
            
            return description
            
        except Exception as e:
            self.logger.error(f"Error añadiendo insights: {str(e)}")
            return description
    
    def _build_description_prompt(self, 
                                position: str,
                                requirements: List[str],
                                location: str,
                                experience_level: str,
                                style: str) -> str:
        """Construye el prompt para generación."""
        prompt = f"Genera una descripción de puesto para: {position}\n"
        prompt += f"Ubicación: {location}\n"
        prompt += f"Nivel de experiencia: {experience_level}\n"
        prompt += f"Estilo: {style}\n"
        prompt += f"Requisitos: {', '.join(requirements)}\n"
        prompt += f"Unidad de negocio: {self.business_unit.name}\n"
        
        return prompt
    
    def _simulate_description_generation(self, prompt: str, style: str) -> str:
        """Simula generación de descripción."""
        # Esta es una simulación - en implementación real usaríamos el sistema ML existente
        
        base_description = f"""
# {prompt.split('para: ')[1].split('\n')[0]}

## Descripción del Puesto

Estamos buscando un profesional talentoso para unirse a nuestro equipo en {self.business_unit.name}. Esta es una oportunidad emocionante para crecer profesionalmente en un entorno dinámico e innovador.

## Responsabilidades Principales

- Desarrollar e implementar estrategias efectivas
- Colaborar con equipos multidisciplinarios
- Mantener altos estándares de calidad
- Contribuir al crecimiento de la organización

## Requisitos

- Experiencia relevante en el campo
- Habilidades de comunicación excepcionales
- Capacidad de trabajo en equipo
- Orientación a resultados

## Beneficios

- Salario competitivo
- Oportunidades de crecimiento
- Ambiente de trabajo dinámico
- Beneficios adicionales
        """
        
        return base_description.strip()
    
    async def _extract_keywords(self, position: str, requirements: List[str]) -> List[str]:
        """Extrae palabras clave relevantes."""
        keywords = [position.lower()]
        keywords.extend([req.lower() for req in requirements])
        
        # Añadir palabras clave comunes del mercado
        common_keywords = ['experiencia', 'habilidades', 'responsabilidades', 'crecimiento']
        keywords.extend(common_keywords)
        
        return list(set(keywords))
    
    def _restructure_for_ats(self, description: str, keywords: List[str]) -> str:
        """Reestructura la descripción para optimizar ATS."""
        # Asegurar que las palabras clave estén presentes
        for keyword in keywords[:5]:  # Top 5 keywords
            if keyword not in description.lower():
                description = f"{keyword.title()}: {description}"
        
        return description
    
    async def _calculate_ats_score(self, description: str) -> float:
        """Calcula score de optimización para ATS."""
        # Lógica simple de scoring
        score = 0.7  # Base score
        
        # Añadir puntos por elementos clave
        if 'responsabilidades' in description.lower():
            score += 0.1
        if 'requisitos' in description.lower():
            score += 0.1
        if 'beneficios' in description.lower():
            score += 0.1
        
        return min(1.0, score)
    
    async def _extract_seo_keywords(self, description: str) -> List[str]:
        """Extrae palabras clave para SEO."""
        # Palabras clave comunes en reclutamiento
        seo_keywords = [
            'trabajo', 'empleo', 'carrera', 'oportunidad',
            'profesional', 'experiencia', 'habilidades',
            'crecimiento', 'desarrollo', 'equipo'
        ]
        
        return seo_keywords
    
    async def _estimate_applications(self, market_analysis: Dict[str, Any]) -> str:
        """Estima el número de aplicaciones esperadas."""
        demand_level = market_analysis.get('demand_level', 'medium')
        
        estimates = {
            'high': '50-100 aplicaciones',
            'medium': '25-50 aplicaciones',
            'low': '10-25 aplicaciones'
        }
        
        return estimates.get(demand_level, '25-50 aplicaciones')
    
    async def _analyze_existing_description(self, description: str) -> Dict[str, Any]:
        """Analiza una descripción existente."""
        return {
            'length': len(description),
            'has_responsibilities': 'responsabilidades' in description.lower(),
            'has_requirements': 'requisitos' in description.lower(),
            'has_benefits': 'beneficios' in description.lower(),
            'ats_friendly': await self._calculate_ats_score(description)
        }
    
    async def _generate_improvements(self, 
                                   description: str,
                                   analysis: Dict[str, Any],
                                   target_audience: str) -> List[str]:
        """Genera sugerencias de mejora."""
        improvements = []
        
        if not analysis.get('has_responsibilities'):
            improvements.append("Añadir sección de responsabilidades principales")
        
        if not analysis.get('has_requirements'):
            improvements.append("Incluir requisitos específicos del puesto")
        
        if not analysis.get('has_benefits'):
            improvements.append("Destacar beneficios y oportunidades de crecimiento")
        
        if analysis.get('ats_friendly', 0) < 0.8:
            improvements.append("Optimizar para sistemas ATS con palabras clave relevantes")
        
        return improvements
    
    async def _apply_improvements(self, description: str, improvements: List[str]) -> str:
        """Aplica mejoras a la descripción."""
        # Implementar lógica de mejora
        improved_description = description
        
        for improvement in improvements:
            if "responsabilidades" in improvement.lower():
                improved_description += "\n\n## Responsabilidades Principales\n- [Añadir responsabilidades específicas]"
            elif "requisitos" in improvement.lower():
                improved_description += "\n\n## Requisitos\n- [Añadir requisitos específicos]"
            elif "beneficios" in improvement.lower():
                improved_description += "\n\n## Beneficios\n- [Añadir beneficios específicos]"
        
        return improved_description
    
    async def _calculate_optimization_score(self, improvements: List[str]) -> float:
        """Calcula score de optimización."""
        base_score = 0.7
        improvement_bonus = len(improvements) * 0.05
        
        return min(1.0, base_score + improvement_bonus)
    
    def _generate_cache_key(self, position: str, requirements: List[str], location: str, experience_level: str) -> str:
        """Genera clave de caché."""
        key_data = {
            'position': position,
            'requirements': requirements,
            'location': location,
            'experience_level': experience_level,
            'business_unit': self.business_unit.id
        }
        return f"job_description:{hash(str(key_data))}" 