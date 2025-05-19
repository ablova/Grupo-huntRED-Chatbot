"""
Analizador de Fit Cultural.

Este módulo analiza la compatibilidad cultural entre candidatos y empresas,
evaluando valores, propósito y prácticas organizacionales.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

import numpy as np
from asgiref.sync import sync_to_async
from django.db.models import Q

from app.models import Person, BusinessUnit, CompanyValues, CandidateValues
from app.com.talent.team_synergy import TeamSynergyAnalyzer
from app.com.chatbot.core.values import ValuesPrinciples

logger = logging.getLogger(__name__)

class CulturalFitAnalyzer:
    """
    Analizador de compatibilidad cultural entre candidatos y organizaciones.
    
    Proporciona métricas de alineación cultural, compatibilidad de valores
    y recomendaciones para mejorar la integración cultural.
    """
    
    # Dimensiones culturales evaluadas
    CULTURAL_DIMENSIONS = [
        "Jerarquía vs. Horizontalidad",
        "Individualismo vs. Colectivismo",
        "Orientación a Resultados vs. Orientación a Procesos", 
        "Enfoque a Corto Plazo vs. Enfoque a Largo Plazo",
        "Estabilidad vs. Innovación",
        "Formalidad vs. Informalidad"
    ]
    
    def __init__(self):
        """Inicializa el analizador de fit cultural."""
        self.values_principles = ValuesPrinciples()
        self.team_analyzer = TeamSynergyAnalyzer()
        
    async def analyze_cultural_fit(self, 
                                 person_id: int, 
                                 company_id: int,
                                 business_unit: str = None) -> Dict:
        """
        Analiza la compatibilidad cultural entre un candidato y una empresa.
        
        Args:
            person_id: ID del candidato
            company_id: ID de la empresa
            business_unit: Unidad de negocio (opcional)
            
        Returns:
            Dict con análisis de compatibilidad, áreas de alineación/desalineación
            y recomendaciones
        """
        try:
            # Obtener datos del candidato y la empresa
            person_data = await self._get_person_data(person_id)
            if not person_data:
                return self._get_default_analysis()
                
            company_data = await self._get_company_data(company_id)
            if not company_data:
                return self._get_default_analysis()
            
            # Análisis de valores
            values_analysis = await self._analyze_values_alignment(
                person_data.get('values', {}), 
                company_data.get('values', {})
            )
            
            # Análisis de dimensiones culturales
            cultural_dimensions = await self._analyze_cultural_dimensions(
                person_data.get('cultural_preferences', {}),
                company_data.get('cultural_dimensions', {})
            )
            
            # Análisis de prácticas específicas
            practices_alignment = await self._analyze_practices_alignment(
                person_id, 
                company_id
            )
            
            # Cálculo de puntuación general de compatibilidad
            compatibility_score = self._calculate_compatibility_score(
                values_analysis,
                cultural_dimensions,
                practices_alignment
            )
            
            # Generar recomendaciones
            recommendations = self._generate_cultural_recommendations(
                person_data,
                company_data,
                values_analysis,
                cultural_dimensions,
                compatibility_score
            )
            
            return {
                'person_id': person_id,
                'company_id': company_id,
                'business_unit': business_unit,
                'compatibility_score': compatibility_score,
                'values_alignment': values_analysis,
                'cultural_dimensions': cultural_dimensions,
                'practices_alignment': practices_alignment,
                'recommendations': recommendations,
                'analyzed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analizando fit cultural: {str(e)}")
            return self._get_default_analysis()
    
    async def _get_person_data(self, person_id: int) -> Optional[Dict]:
        """Obtiene datos del candidato relevantes para análisis cultural."""
        try:
            from app.models import Person, CandidateValues
            
            person = await sync_to_async(Person.objects.get)(id=person_id)
            
            # Intentar obtener valores del candidato
            try:
                values = await sync_to_async(CandidateValues.objects.get)(person=person)
                person_values = {
                    'primary_values': values.primary_values,
                    'secondary_values': values.secondary_values,
                    'approach_to_work': values.approach_to_work,
                    'personal_mission': values.personal_mission
                }
            except CandidateValues.DoesNotExist:
                # Si no hay valores registrados, usar simulación
                person_values = self._simulate_candidate_values(person_id)
            
            # Simular preferencias culturales
            # En un sistema real, esto vendría de entrevistas o cuestionarios
            cultural_preferences = self._simulate_cultural_preferences(person_id)
                
            return {
                'id': person_id,
                'name': f"{person.first_name} {person.last_name}",
                'values': person_values,
                'cultural_preferences': cultural_preferences,
                'generation': self._determine_generation(getattr(person, 'birth_date', None))
            }
        except Exception as e:
            logger.error(f"Error obteniendo datos de candidato: {str(e)}")
            return None
    
    async def _get_company_data(self, company_id: int) -> Optional[Dict]:
        """Obtiene datos de la empresa relevantes para análisis cultural."""
        try:
            from app.models import Company, CompanyValues
            
            company = await sync_to_async(Company.objects.get)(id=company_id)
            
            # Intentar obtener valores de la empresa
            try:
                values = await sync_to_async(CompanyValues.objects.get)(company=company)
                company_values = {
                    'stated_values': values.stated_values,
                    'mission': values.mission,
                    'vision': values.vision,
                    'practices': values.key_practices
                }
            except CompanyValues.DoesNotExist:
                # Si no hay valores registrados, usar simulación
                company_values = self._simulate_company_values(company_id)
            
            # Simular dimensiones culturales
            # En un sistema real, esto vendría de datos reales
            cultural_dimensions = self._simulate_cultural_dimensions(company_id)
                
            return {
                'id': company_id,
                'name': company.name,
                'values': company_values,
                'cultural_dimensions': cultural_dimensions,
                'industry': getattr(company, 'industry', 'Technology')
            }
        except Exception as e:
            logger.error(f"Error obteniendo datos de empresa: {str(e)}")
            return None
    
    def _determine_generation(self, birth_date) -> str:
        """Determina la generación basado en fecha de nacimiento."""
        if not birth_date:
            return "Desconocida"
            
        birth_year = birth_date.year
        
        if 1946 <= birth_year <= 1964:
            return "Baby Boomer"
        elif 1965 <= birth_year <= 1980:
            return "Generación X"
        elif 1981 <= birth_year <= 1996:
            return "Millennial"
        elif 1997 <= birth_year <= 2012:
            return "Generación Z"
        elif 2013 <= birth_year <= 2025:
            return "Generación Alpha"
        else:
            return "Otra"
    
    def _simulate_candidate_values(self, person_id: int) -> Dict:
        """Simula valores de candidato para demostración/desarrollo."""
        # Usar ID para crear valores consistentes pero simulados
        import hashlib
        import random
        
        # Valores posibles
        possible_values = [
            "Autonomía", "Impacto", "Creatividad", "Seguridad", 
            "Crecimiento", "Colaboración", "Innovación", "Liderazgo",
            "Balance", "Reconocimiento", "Contribución", "Integridad"
        ]
        
        # Enfoques posibles
        possible_approaches = [
            "Orientado a resultados", "Orientado a personas", 
            "Orientado a procesos", "Orientado a innovación", 
            "Orientado a aprendizaje", "Orientado a impacto"
        ]
        
        # Misiones posibles
        possible_missions = [
            "Crear impacto positivo en la sociedad",
            "Desarrollar soluciones innovadoras",
            "Liderar equipos de alto desempeño",
            "Crear valor económico sostenible",
            "Promover el cambio organizacional",
            "Transformar la forma de trabajar"
        ]
        
        # Crear valores consistentes basados en el ID
        seed = int(hashlib.md5(str(person_id).encode()).hexdigest(), 16) % 10000
        random.seed(seed)
        
        return {
            'primary_values': random.sample(possible_values, 3),
            'secondary_values': random.sample([v for v in possible_values if v not in random.sample(possible_values, 3)], 2),
            'approach_to_work': random.choice(possible_approaches),
            'personal_mission': random.choice(possible_missions)
        }
    
    def _simulate_company_values(self, company_id: int) -> Dict:
        """Simula valores de empresa para demostración/desarrollo."""
        # Usar ID para crear valores consistentes pero simulados
        import hashlib
        import random
        
        # Valores posibles
        possible_values = [
            "Innovación", "Integridad", "Excelencia", "Colaboración", 
            "Sostenibilidad", "Diversidad", "Responsabilidad", "Compromiso",
            "Enfoque al cliente", "Calidad", "Transparencia", "Adaptabilidad"
        ]
        
        # Misiones posibles
        possible_missions = [
            "Transformar la industria con soluciones innovadoras",
            "Crear valor sostenible para todos los stakeholders",
            "Empoderar a personas y organizaciones",
            "Liderar la transformación digital",
            "Mejorar la vida de las personas a través de la tecnología",
            "Ofrecer productos y servicios de la más alta calidad"
        ]
        
        # Visiones posibles
        possible_visions = [
            "Ser líder indiscutible en nuestro sector",
            "Ser la organización más innovadora del mercado",
            "Ser referente en prácticas sostenibles y responsables",
            "Ser el empleador preferido en nuestra industria",
            "Ser reconocidos por nuestra excelencia operativa",
            "Ser agentes de cambio positivo en la sociedad"
        ]
        
        # Prácticas clave
        possible_practices = [
            "Feedback continuo", "Horario flexible", "Teletrabajo",
            "Desarrollo profesional personalizado", "Mentoría", 
            "Innovación participativa", "Gestión por objetivos",
            "Equipos autogestionados", "Transparencia financiera"
        ]
        
        # Crear valores consistentes basados en el ID
        seed = int(hashlib.md5(str(company_id).encode()).hexdigest(), 16) % 10000
        random.seed(seed)
        
        return {
            'stated_values': random.sample(possible_values, 4),
            'mission': random.choice(possible_missions),
            'vision': random.choice(possible_visions),
            'practices': random.sample(possible_practices, 3)
        }
    
    def _simulate_cultural_preferences(self, person_id: int) -> Dict:
        """Simula preferencias culturales del candidato."""
        import hashlib
        import random
        
        # Crear preferencias consistentes basadas en el ID
        seed = int(hashlib.md5(str(person_id).encode()).hexdigest(), 16) % 10000
        random.seed(seed)
        
        # Preferencias para cada dimensión cultural (0-10)
        # 0: extremo izquierdo, 10: extremo derecho
        preferences = {}
        for dimension in self.CULTURAL_DIMENSIONS:
            preferences[dimension] = random.randint(2, 8)
        
        return preferences
    
    def _simulate_cultural_dimensions(self, company_id: int) -> Dict:
        """Simula dimensiones culturales de la empresa."""
        import hashlib
        import random
        
        # Crear dimensiones consistentes basadas en el ID
        seed = int(hashlib.md5(str(company_id).encode()).hexdigest(), 16) % 10000
        random.seed(seed)
        
        # Perfil para cada dimensión cultural (0-10)
        # 0: extremo izquierdo, 10: extremo derecho
        dimensions = {}
        for dimension in self.CULTURAL_DIMENSIONS:
            dimensions[dimension] = random.randint(2, 8)
            
        return dimensions
    
    async def _analyze_values_alignment(self, person_values: Dict, company_values: Dict) -> Dict:
        """Analiza la alineación de valores entre candidato y empresa."""
        # Extraer valores
        person_primary = set(person_values.get('primary_values', []))
        person_secondary = set(person_values.get('secondary_values', []))
        company_stated = set(company_values.get('stated_values', []))
        
        # Calcular intersección
        matching_primary = person_primary.intersection(company_stated)
        matching_secondary = person_secondary.intersection(company_stated)
        
        # Calcular puntuación de alineación
        # Valores primarios tienen más peso
        primary_score = len(matching_primary) / max(1, len(person_primary)) * 100
        secondary_score = len(matching_secondary) / max(1, len(person_secondary)) * 100
        
        alignment_score = primary_score * 0.7 + secondary_score * 0.3
        
        # Analizar alineación de misión/propósito
        person_mission = person_values.get('personal_mission', '')
        company_mission = company_values.get('mission', '')
        
        # En un sistema real, usaríamos un modelo de NLP aquí
        # Para esta demo, usamos una comparación simplificada
        mission_alignment = self._calculate_text_alignment(person_mission, company_mission)
        
        return {
            'alignment_score': alignment_score,
            'matching_values': list(matching_primary) + list(matching_secondary),
            'mission_alignment': mission_alignment,
            'person_unique_values': list(person_primary.union(person_secondary) - company_stated),
            'company_unique_values': list(company_stated - person_primary.union(person_secondary))
        }
    
    def _calculate_text_alignment(self, text1: str, text2: str) -> float:
        """Calcula alineación entre dos textos (simplificada)."""
        if not text1 or not text2:
            return 0.0
            
        # Normalizar textos
        t1 = text1.lower()
        t2 = text2.lower()
        
        # Tokenizar
        words1 = set(t1.split())
        words2 = set(t2.split())
        
        # Calcular similitud Jaccard
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return (intersection / union) * 100 if union > 0 else 0
    
    async def _analyze_cultural_dimensions(self, person_preferences: Dict, company_dimensions: Dict) -> Dict:
        """Analiza la alineación en dimensiones culturales."""
        alignment_by_dimension = {}
        total_distance = 0
        
        for dimension in self.CULTURAL_DIMENSIONS:
            person_value = person_preferences.get(dimension, 5)  # Default centro
            company_value = company_dimensions.get(dimension, 5)  # Default centro
            
            # Distancia normalizada (0-1)
            distance = abs(person_value - company_value) / 10
            alignment = 100 - (distance * 100)
            
            alignment_by_dimension[dimension] = {
                'person_preference': person_value,
                'company_culture': company_value,
                'alignment': alignment
            }
            
            total_distance += distance
        
        # Calcular alineación general
        avg_distance = total_distance / len(self.CULTURAL_DIMENSIONS)
        overall_alignment = 100 - (avg_distance * 100)
        
        # Identificar dimensiones con mayor/menor alineación
        sorted_dimensions = sorted(
            alignment_by_dimension.items(),
            key=lambda x: x[1]['alignment']
        )
        
        top_alignments = sorted_dimensions[-3:]
        bottom_alignments = sorted_dimensions[:3]
        
        return {
            'overall_alignment': overall_alignment,
            'by_dimension': alignment_by_dimension,
            'top_alignments': [item[0] for item in top_alignments],
            'bottom_alignments': [item[0] for item in bottom_alignments]
        }
    
    async def _analyze_practices_alignment(self, person_id: int, company_id: int) -> Dict:
        """Analiza la alineación en prácticas organizacionales específicas."""
        # En un sistema real, esto analizaría prácticas específicas
        # Para esta demo, usamos datos simulados
        
        # Prácticas relevantes para análisis
        key_practices = [
            "Horario flexible",
            "Trabajo remoto",
            "Retroalimentación continua",
            "Desarrollo profesional",
            "Toma de decisiones",
            "Comunicación",
            "Equilibrio vida-trabajo",
            "Reconocimiento"
        ]
        
        # Simular preferencias y prácticas
        import hashlib
        import random
        
        seed1 = int(hashlib.md5(str(person_id).encode()).hexdigest(), 16) % 10000
        seed2 = int(hashlib.md5(str(company_id).encode()).hexdigest(), 16) % 10000
        
        random.seed(seed1)
        person_preferences = {
            practice: random.randint(1, 10) for practice in key_practices
        }
        
        random.seed(seed2)
        company_practices = {
            practice: random.randint(1, 10) for practice in key_practices
        }
        
        # Calcular alineación
        practice_alignment = {}
        total_alignment = 0
        
        for practice in key_practices:
            person_value = person_preferences.get(practice, 5)
            company_value = company_practices.get(practice, 5)
            
            # Distancia normalizada
            distance = abs(person_value - company_value) / 9  # Rango 1-10
            alignment = 100 - (distance * 100)
            
            practice_alignment[practice] = {
                'person_preference': person_value,
                'company_practice': company_value,
                'alignment': alignment
            }
            
            total_alignment += alignment
        
        # Promediar alineación
        average_alignment = total_alignment / len(key_practices)
        
        # Identificar prácticas con mayor/menor alineación
        sorted_practices = sorted(
            practice_alignment.items(),
            key=lambda x: x[1]['alignment']
        )
        
        top_alignments = sorted_practices[-3:]
        bottom_alignments = sorted_practices[:3]
        
        return {
            'overall_alignment': average_alignment,
            'by_practice': practice_alignment,
            'top_alignments': [item[0] for item in top_alignments],
            'bottom_alignments': [item[0] for item in bottom_alignments]
        }
    
    def _calculate_compatibility_score(self, values_analysis: Dict, cultural_dimensions: Dict, practices_alignment: Dict) -> float:
        """Calcula la puntuación global de compatibilidad cultural."""
        # Ponderación de componentes
        weights = {
            'values': 0.4,
            'cultural_dimensions': 0.4,
            'practices': 0.2
        }
        
        # Puntuaciones individuales
        values_score = values_analysis['alignment_score']
        dimensions_score = cultural_dimensions['overall_alignment']
        practices_score = practices_alignment['overall_alignment']
        
        # Cálculo ponderado
        compatibility_score = (
            values_score * weights['values'] +
            dimensions_score * weights['cultural_dimensions'] +
            practices_score * weights['practices']
        )
        
        return min(100, compatibility_score)
    
    def _generate_cultural_recommendations(self, person_data: Dict, company_data: Dict, 
                                         values_analysis: Dict, cultural_dimensions: Dict, 
                                         compatibility_score: float) -> List[Dict]:
        """Genera recomendaciones para mejorar la compatibilidad cultural."""
        recommendations = []
        
        # Recomendaciones basadas en valores
        if values_analysis['alignment_score'] < 70:
            values_rec = {
                'area': 'values',
                'title': 'Alineación de Valores',
                'description': "Hay una brecha significativa entre los valores personales y organizacionales",
                'actions': [
                    "Explorar cómo los valores personales pueden manifestarse en el contexto de la empresa",
                    f"Preguntar durante la entrevista sobre cómo se viven los valores: {', '.join(company_data['values'].get('stated_values', ['']))}"
                ]
            }
            recommendations.append(values_rec)
        
        # Recomendaciones basadas en dimensiones culturales
        if cultural_dimensions['overall_alignment'] < 70:
            dimensions_rec = {
                'area': 'cultural_dimensions',
                'title': 'Adaptación a Dimensiones Culturales',
                'description': f"Hay diferencias significativas en: {', '.join(cultural_dimensions['bottom_alignments'][:2])}",
                'actions': [
                    "Evaluar flexibilidad personal en estas dimensiones",
                    "Buscar exposición previa a estos entornos culturales"
                ]
            }
            recommendations.append(dimensions_rec)
        
        # Recomendación general si la compatibilidad es baja
        if compatibility_score < 60:
            recommendations.append({
                'area': 'general',
                'title': 'Potencial Desajuste Cultural',
                'description': "La compatibilidad cultural general es baja, lo que podría afectar la satisfacción y rendimiento",
                'actions': [
                    "Considerar si estás dispuesto/a a adaptarte a una cultura significativamente diferente",
                    "Preguntar sobre programas de onboarding y asimilación cultural",
                    "Explorar si puedes aportar diversidad valiosa a la organización"
                ]
            })
        
        # Recomendación positiva si la compatibilidad es alta
        if compatibility_score > 80:
            recommendations.append({
                'area': 'general',
                'title': 'Alta Compatibilidad Cultural',
                'description': "Hay un excelente ajuste cultural entre tus preferencias y la organización",
                'actions': [
                    "Destacar en entrevistas la alineación con los valores y cultura",
                    "Explorar oportunidades para ser embajador/a cultural",
                    "Preguntar sobre oportunidades de desarrollo alineadas con valores compartidos"
                ]
            })
        
        return recommendations
    
    def _get_default_analysis(self) -> Dict:
        """Retorna un análisis predeterminado vacío."""
        return {
            'compatibility_score': 50,
            'values_alignment': {
                'alignment_score': 50,
                'matching_values': [],
                'mission_alignment': 50,
                'person_unique_values': [],
                'company_unique_values': []
            },
            'cultural_dimensions': {
                'overall_alignment': 50,
                'by_dimension': {},
                'top_alignments': [],
                'bottom_alignments': []
            },
            'practices_alignment': {
                'overall_alignment': 50,
                'by_practice': {},
                'top_alignments': [],
                'bottom_alignments': []
            },
            'recommendations': [],
            'analyzed_at': datetime.now().isoformat()
        }
