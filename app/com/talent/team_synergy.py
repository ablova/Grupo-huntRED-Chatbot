"""
Analizador de Sinergia de Equipos.

Este módulo analiza la composición óptima de equipos basándose en múltiples 
factores como habilidades, personalidad, generación, y propósito profesional.
Proporciona visualizaciones y recomendaciones para maximizar el rendimiento del equipo.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.figure import Figure
import networkx as nx
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.colors as mcolors
from asgiref.sync import sync_to_async
from django.db.models import Q, Count, Avg, F

from app.models import Person, BusinessUnit, Skill, SkillAssessment
from app.com.chatbot.workflow.personality import PersonalityAnalyzer
from app.com.utils.cv_generator.career_analyzer import CVCareerAnalyzer
from app.com.chatbot.core.values import ValuesPrinciples

logger = logging.getLogger(__name__)

class TeamSynergyAnalyzer:
    """
    Analizador de sinergia y rendimiento potencial de equipos basado en múltiples factores.
    
    Proporciona análisis visual y recomendaciones para optimizar la composición
    de equipos y maximizar tanto el rendimiento como la satisfacción.
    """
    
    # Mapeo de generaciones por año de nacimiento
    GENERATION_MAPPING = {
        (1946, 1964): "Baby Boomer",
        (1965, 1980): "Generación X",
        (1981, 1996): "Millennial",
        (1997, 2012): "Generación Z",
        (2013, 2025): "Generación Alpha"
    }
    
    # Colores para visualizaciones por BU
    BU_COLORS = {
        "huntRED": "#D62839",  # Rojo huntRED
        "huntU": "#4361EE",    # Azul huntU
        "Amigro": "#4F772D",   # Verde Amigro
        "SEXSI": "#9B5DE5",    # Morado SEXSI
        "MilkyLeak": "#F9C80E" # Amarillo MilkyLeak
    }
    
    # Tipos de personalidad y sus complementariedades
    PERSONALITY_SYNERGY = {
        "Analítico": ["Colaborativo", "Innovador"],
        "Colaborativo": ["Analítico", "Director"],
        "Director": ["Colaborativo", "Innovador"],
        "Innovador": ["Analítico", "Director"]
    }
    
    def __init__(self):
        """Inicializa el analizador de sinergia de equipos."""
        self.personality_analyzer = PersonalityAnalyzer()
        self.values_principles = ValuesPrinciples()
        self.career_analyzer = CVCareerAnalyzer()
        
        # Configuración de visualización
        plt.style.use('seaborn-v0_8-whitegrid')
        sns.set_palette("deep")
        
        # Crear mapa de colores personalizado para huntRED
        colors = [(0.839, 0.157, 0.224), (0.98, 0.584, 0.298), (0.267, 0.384, 0.933)]  # Rojo, Naranja, Azul
        self.huntred_cmap = LinearSegmentedColormap.from_list('huntred', colors, N=100)
    
    async def analyze_team_synergy(self, 
                                 team_members: List[int], 
                                 business_unit: str = None) -> Dict:
        """
        Analiza la sinergia de un equipo existente o propuesto.
        
        Args:
            team_members: Lista de IDs de personas en el equipo
            business_unit: Unidad de negocio (opcional)
            
        Returns:
            Dict con análisis de sinergia, visualizaciones y recomendaciones
        """
        try:
            if not team_members:
                logger.error("No se proporcionaron miembros del equipo")
                return self._get_default_analysis()
            
            # Obtener información detallada de los miembros
            members_data = await self._get_team_members_data(team_members)
            if not members_data:
                return self._get_default_analysis()
            
            # Analizar composición de habilidades
            skills_analysis = await self._analyze_skill_composition(members_data)
            
            # Analizar distribución de personalidades
            personality_analysis = await self._analyze_personality_distribution(members_data)
            
            # Analizar diversidad generacional
            generation_analysis = await self._analyze_generation_diversity(members_data)
            
            # Analizar alineación de propósito
            purpose_analysis = await self._analyze_purpose_alignment(members_data)
            
            # Calcular puntuación de sinergia global
            synergy_score = self._calculate_synergy_score(
                skills_analysis,
                personality_analysis,
                generation_analysis,
                purpose_analysis
        )
            
            # Generar red de conexiones del equipo
            connection_network = await self._generate_connection_network(members_data)
            
            # Generar recomendaciones
            recommendations = self._generate_team_recommendations(
                members_data,
                skills_analysis,
                personality_analysis,
                generation_analysis,
                purpose_analysis,
                synergy_score
        )
            
            # Crear visualizaciones
            visualizations = await self._create_team_visualizations(
                members_data,
                skills_analysis,
                personality_analysis,
                generation_analysis,
                purpose_analysis,
                connection_network
        )
            
        return {
                'team_size': len(members_data),
                'business_unit': business_unit,
                'synergy_score': synergy_score,
                'skills_analysis': skills_analysis,
                'personality_analysis': personality_analysis,
                'generation_analysis': generation_analysis,
                'purpose_analysis': purpose_analysis,
                'connection_network': connection_network,
                'recommendations': recommendations,
                'visualizations': visualizations,
            'analyzed_at': datetime.now().isoformat()
        }
            
        except Exception as e:
            logger.error(f"Error analizando sinergia de equipo: {str(e)}")
            return self._get_default_analysis()
    
    async def _get_team_members_data(self, member_ids: List[int]) -> List[Dict]:
        """Obtiene datos completos de los miembros del equipo."""
        members_data = []
        
        for person_id in member_ids:
            try:
                # Obtener información básica de la persona
                person = await self._get_person(person_id)
                if not person:
                    continue
                
                # Obtener análisis de personalidad
                personality = await self._get_personality(person_id)
                
                # Obtener habilidades
                skills = await self._get_person_skills(person_id)
                
                # Determinar generación
                generation = self._determine_generation(person.birth_date.year if hasattr(person, 'birth_date') else 1985)
                
                # Obtener propósito profesional y valores
                purpose = await self._get_professional_purpose(person_id)
                
                members_data.append({
                    'id': person_id,
                    'name': f"{person.first_name} {person.last_name}" if hasattr(person, 'first_name') else f"Person {person_id}",
                    'position': getattr(person, 'current_position', 'Profesional'),
                    'personality': personality,
                    'skills': skills,
                    'generation': generation,
                    'purpose': purpose,
                    'years_experience': getattr(person, 'years_experience', 5)
            })
            except Exception as e:
                logger.error(f"Error obteniendo datos para persona {person_id}: {str(e)}")
        
        return members_data
    
    async def _get_person(self, person_id: int) -> Optional[Person]:
        """Obtiene la persona por ID."""
        try:
            from app.models import Person
            return await sync_to_async(Person.objects.get)(id=person_id)
        except Exception as e:
            logger.error(f"Error obteniendo Person: {str(e)}")
            return None
    
    async def _get_personality(self, person_id: int) -> Dict:
        """Obtiene análisis de personalidad para la persona."""
        try:
            # Integración con el analizador de personalidad existente
            personality_result = await self.personality_analyzer.analyze_personality(person_id)
            
            # Simplificar tipos para análisis de sinergia
            personality_type = self._simplify_personality_type(personality_result.get('type', 'Equilibrado'))
            
        return {
                'type': personality_type,
                'traits': personality_result.get('traits', {}),
                'communication_style': personality_result.get('communication_style', 'Directo')
        }
        except Exception as e:
            logger.error(f"Error obteniendo personalidad: {str(e)}")
        return {
                'type': 'Equilibrado',
                'traits': {},
                'communication_style': 'Directo'
        }
    
    def _simplify_personality_type(self, personality_type: str) -> str:
        """Simplifica tipos de personalidad a 4 tipos básicos para análisis de equipo."""
        # Mapear tipos complejos a categorías simples
        if any(keyword in personality_type.lower() for keyword in ['analítico', 'lógico', 'detallista', 'pensador']):
            return 'Analítico'
        elif any(keyword in personality_type.lower() for keyword in ['colaborativo', 'relacional', 'armonizador', 'diplomático']):
            return 'Colaborativo'
        elif any(keyword in personality_type.lower() for keyword in ['director', 'dominante', 'decisivo', 'ejecutor']):
            return 'Director'
        elif any(keyword in personality_type.lower() for keyword in ['innovador', 'creativo', 'visionario', 'imaginativo']):
            return 'Innovador'
        else:
            return 'Equilibrado'
    
    async def _get_person_skills(self, person_id: int) -> List[Dict]:
        """Obtiene las habilidades de la persona con sus niveles."""
        try:
            from app.models import SkillAssessment
            
            person = await self._get_person(person_id)
            if not person:
                return []
            
            # Obtener evaluaciones de habilidades
            assessments = await sync_to_async(list)(
                SkillAssessment.objects.filter(person=person).select_related('skill')
        )
            
            return [
                {
                    'name': assessment.skill.name,
                    'level': assessment.score,
                    'category': assessment.skill.category
            }
                for assessment in assessments
        ]
        except Exception as e:
            logger.error(f"Error obteniendo habilidades: {str(e)}")
            return []
    
    def _determine_generation(self, birth_year: int) -> str:
        """Determina la generación basada en el año de nacimiento."""
        for year_range, generation_name in self.GENERATION_MAPPING.items():
            if year_range[0] <= birth_year <= year_range[1]:
                return generation_name
        
        # Default para años fuera de rangos definidos
        return "Generación Desconocida"
    
    async def _get_professional_purpose(self, person_id: int) -> Dict:
        """Obtiene el propósito profesional y valores."""
        try:
            # En un sistema real, esto extraería datos de encuestas o evaluaciones
            # Para este ejemplo, usaremos datos simulados
            
            # Valores posibles (podrían venir de una taxonomía real)
            possible_values = [
                "Impacto social", "Crecimiento profesional", "Innovación", 
                "Estabilidad", "Balance vida-trabajo", "Liderazgo", 
                "Autonomía", "Creatividad", "Servicio", "Excelencia"
        ]
            
            # Simular propósito con factores aleatorios pero estables por ID
            import hashlib
            import random
            
            # Usar hash del ID para generar seed y obtener resultados consistentes
            seed = int(hashlib.md5(str(person_id).encode()).hexdigest(), 16) % 10000
            random.seed(seed)
            
            # Seleccionar valores principales (3-5)
            num_values = random.randint(3, 5)
            primary_values = random.sample(possible_values, num_values)
            
            # Generar factores de motivación
            motivations = {
                "económicos": random.randint(1, 10),
                "crecimiento": random.randint(1, 10),
                "impacto": random.randint(1, 10),
                "reconocimiento": random.randint(1, 10),
                "social": random.randint(1, 10)
        }
            
            # Determinar área de propósito principal
            purpose_areas = ["Profesional", "Social", "Económico", "Innovación", "Liderazgo"]
            primary_purpose = random.sample(purpose_areas, 2)
            
        return {
                'primary_values': primary_values,
                'motivations': motivations,
                'primary_purpose': primary_purpose,
                'alignment_score': random.randint(60, 95)  # Simulación
        }
            
        except Exception as e:
            logger.error(f"Error obteniendo propósito profesional: {str(e)}")
        return {
                'primary_values': ["Crecimiento profesional", "Impacto social"],
                'motivations': {"económicos": 7, "crecimiento": 8, "impacto": 6, "reconocimiento": 5, "social": 7},
                'primary_purpose': ["Profesional", "Social"],
                'alignment_score': 75
        }
    
    async def _analyze_skill_composition(self, members_data: List[Dict]) -> Dict:
        """Analiza la composición de habilidades del equipo."""
        if not members_data:
        return {'coverage_score': 0, 'balance_score': 0, 'skill_gaps': []}
        
        # Recopilar todas las habilidades
        all_skills = {}
        skill_categories = set()
        
        for member in members_data:
            for skill in member.get('skills', []):
                skill_name = skill['name']
                skill_level = skill['level']
                skill_category = skill.get('category', 'General')
                
                if skill_name not in all_skills:
                    all_skills[skill_name] = {
                        'levels': [],
                        'category': skill_category
                }
                
                all_skills[skill_name]['levels'].append(skill_level)
                skill_categories.add(skill_category)
        
        # Calcular niveles promedio y distribución
        skill_analysis = {}
        for skill_name, data in all_skills.items():
            levels = data['levels']
            avg_level = sum(levels) / len(levels)
            coverage = len(levels) / len(members_data)  # % del equipo con esta habilidad
            
            skill_analysis[skill_name] = {
                'average_level': avg_level,
                'coverage': coverage,
                'category': data['category'],
                'distribution': levels
        }
        
        # Identificar brechas de habilidades críticas
        # En un sistema real, esto usaría una lista de habilidades críticas por rol/industria
        critical_skills = [
            "Liderazgo", "Comunicación efectiva", "Resolución de problemas",
            "Análisis de datos", "Trabajo en equipo", "Adaptabilidad",
            "Gestión del tiempo", "Pensamiento crítico", "Innovación",
            "Negociación", "Gestión de proyectos"
        ]
        
        skill_gaps = [
            skill for skill in critical_skills 
            if skill not in all_skills or 
               all_skills[skill]['levels'] < 0.3 * len(members_data) or  # Menos del 30% del equipo
               sum(all_skills.get(skill, {}).get('levels', [0])) / max(1, len(all_skills.get(skill, {}).get('levels', [1]))) < 7  # Promedio < 7/10
        ]
        
        # Calcular balance por categorías
        category_counts = {}
        for skill_name, data in skill_analysis.items():
            category = data['category']
            if category not in category_counts:
                category_counts[category] = 0
            category_counts[category] += data['coverage']
        
        # Normalizar conteos por categoría
        total_categories = len(category_counts)
        for category in category_counts:
            category_counts[category] /= total_categories
        
        # Calcular puntuaciones
        coverage_score = min(100, (len(all_skills) / (len(critical_skills) * 0.7)) * 100)
        
        # Balance de habilidades (uniformidad de distribución)
        if category_counts:
            balance_values = list(category_counts.values())
            balance_score = min(100, (1 - np.std(balance_values) / np.mean(balance_values)) * 100)
        else:
            balance_score = 50  # Valor predeterminado
        
        # Top habilidades del equipo
        top_skills = sorted(
            [(name, data['average_level']) for name, data in skill_analysis.items()],
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            'coverage_score': coverage_score,
            'balance_score': balance_score,
            'top_skills': top_skills,
            'skill_gaps': skill_gaps,
            'skill_details': skill_analysis,
            'category_distribution': category_counts
        }

    async def _analyze_personality_distribution(self, members_data: List[Dict]) -> Dict:
        """Analiza la distribución de personalidades en el equipo."""
        # Contar tipos de personalidad
        personality_counts = {}
        for member in members_data:
            personality = member.get('personality', {}).get('type', 'Equilibrado')
            if personality not in personality_counts:
                personality_counts[personality] = 0
            personality_counts[personality] += 1
            
        # Calcular porcentajes y diversidad
        team_size = len(members_data)
        personality_distribution = {
            p_type: count / team_size * 100 
            for p_type, count in personality_counts.items()
        }
            
        # Encontrar personalidad dominante
        dominant_personality = max(personality_counts.items(), key=lambda x: x[1])[0]
            
        # Calcular diversidad (basada en distribución uniforme)
        diversity_score = min(100, 100 - np.var(list(personality_distribution.values())))
            
        return {
            'diversity_score': diversity_score,
            'dominant_personality': dominant_personality,
            'distribution': personality_distribution,
            'ideal_additions': self._get_ideal_personality_additions(personality_distribution)
        }
        
    async def _analyze_generation_diversity(self, members_data: List[Dict]) -> Dict:
        """Analiza la diversidad generacional del equipo."""
        # Contar generaciones
        generation_counts = {}
        for member in members_data:
            generation = member.get('generation', 'Desconocida')
            if generation not in generation_counts:
                generation_counts[generation] = 0
            generation_counts[generation] += 1
            
        # Calcular porcentajes y diversidad
        team_size = len(members_data)
        generation_distribution = {
            gen: count / team_size * 100 
            for gen, count in generation_counts.items()
        }
            
        # Calcular puntuación de diversidad
        diversity_score = min(100, 50 + (len(generation_counts) - 1) * 15)
            
        return {
            'diversity_score': diversity_score,
            'distribution': generation_distribution,
            'advantages': ["Diversidad de perspectivas"] if len(generation_counts) > 1 else ["Cohesión generacional"]
        }
        
    async def _analyze_purpose_alignment(self, members_data: List[Dict]) -> Dict:
        """Analiza la alineación de propósito y valores del equipo."""
        # Recopilar valores y propósitos
        all_values = []
        all_purposes = []
            
        for member in members_data:
            purpose_data = member.get('purpose', {})
            all_values.extend(purpose_data.get('primary_values', []))
            all_purposes.extend(purpose_data.get('primary_purpose', []))
            
        # Encontrar valores comunes y divergentes
        value_counts = {}
        for value in all_values:
            if value not in value_counts:
                value_counts[value] = 0
            value_counts[value] += 1
            
        # Valores compartidos por la mayoría
        threshold = len(members_data) * 0.5
        common_values = [
            value for value, count in value_counts.items()
            if count >= threshold
        ]
            
        # Calcular alineación
        alignment_score = min(100, len(common_values) * 20)
            
        return {
            'alignment_score': alignment_score,
            'common_values': common_values,
            'dominant_purpose': max(all_purposes, key=all_purposes.count) if all_purposes else None
        }
        
    async def _create_team_visualizations(self, members_data: List[Dict], skills_analysis: Dict, personality_analysis: Dict, generation_analysis: Dict, purpose_analysis: Dict, connection_network: Dict) -> Dict:
        """Crea visualizaciones para el análisis del equipo."""
        # Generar visualizaciones como gráficos de red, radar charts, etc.
        visualizations = {
            'skill_radar': self._create_skill_radar_chart(skills_analysis),
            'personality_distribution': self._create_personality_donut(personality_analysis),
            'generation_distribution': self._create_generation_bar_chart(generation_analysis),
            'team_network': self._create_network_visualization(connection_network),
            'synergy_matrix': self._create_synergy_matrix(members_data)
        }
            
        return visualizations
        
    def _calculate_synergy_score(self, skills_analysis: Dict, personality_analysis: Dict, generation_analysis: Dict, purpose_analysis: Dict) -> float:
        """Calcula la puntuación global de sinergia del equipo."""
        # Ponderación de factores
        weights = {
            'skills': 0.3,
            'personality': 0.25,
            'generation': 0.15,
            'purpose': 0.3
        }
            
        # Componentes individuales
        skill_score = (skills_analysis['coverage_score'] + skills_analysis['balance_score']) / 2
        personality_score = personality_analysis['diversity_score']
        generation_score = generation_analysis['diversity_score']
        purpose_score = purpose_analysis['alignment_score']
            
        # Cálculo ponderado
        synergy_score = (
            skill_score * weights['skills'] +
            personality_score * weights['personality'] +
            generation_score * weights['generation'] +
            purpose_score * weights['purpose']
        )
            
        return min(100, synergy_score)
        
    def _generate_team_recommendations(self, members_data: List[Dict], skills_analysis: Dict, personality_analysis: Dict, generation_analysis: Dict, purpose_analysis: Dict, synergy_score: float) -> List[Dict]:
        """Genera recomendaciones para mejorar la sinergia del equipo."""
        recommendations = []
            
        # Recomendaciones sobre habilidades
        if skills_analysis['skill_gaps']:
            recommendations.append({
                'area': 'skills',
                'title': 'Cubrir brechas de habilidades',
                'description': f"El equipo necesita reforzar: {', '.join(skills_analysis['skill_gaps'][:3])}",
                'actions': [f"Capacitar al equipo en {skill}" for skill in skills_analysis['skill_gaps'][:2]]
            })
            
        # Recomendaciones sobre personalidad
        if personality_analysis['diversity_score'] < 70:
            recommendations.append({
                'area': 'personality',
                'title': 'Equilibrar tipos de personalidad',
                'description': f"Incorporar personas con perfil: {', '.join(personality_analysis['ideal_additions'])}",
                'actions': ["Evaluar perfil de personalidad en nuevas contrataciones"]
            })
            
        # Recomendaciones sobre propósito
        if purpose_analysis['alignment_score'] < 70:
            recommendations.append({
                'area': 'purpose',
                'title': 'Alinear propósitos y valores',
                'description': "El equipo necesita mayor alineación en propósito profesional",
                'actions': ["Realizar taller de alineación de valores", "Definir propósito compartido del equipo"]
            })
            
        return recommendations
        
    def _get_default_analysis(self) -> Dict:
        """Retorna un análisis predeterminado vacío."""
        return {
            'team_size': 0,
            'synergy_score': 50,
            'skills_analysis': {'coverage_score': 0, 'balance_score': 0, 'skill_gaps': []},
            'personality_analysis': {'diversity_score': 0, 'distribution': {}},
            'generation_analysis': {'diversity_score': 0, 'distribution': {}},
            'purpose_analysis': {'alignment_score': 0, 'common_values': []},
            'recommendations': [],
            'visualizations': {},
            'analyzed_at': datetime.now().isoformat()
        }
