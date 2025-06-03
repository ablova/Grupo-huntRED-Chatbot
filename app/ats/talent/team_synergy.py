# /home/pablo/app/com/talent/team_synergy.py
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
from collections import defaultdict
import random
import hashlib

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
from django.core.exceptions import ObjectDoesNotExist

from app.models import Person, BusinessUnit, Skill, SkillAssessment
from app.ml.analyzers.personality_analyzer import PersonalityAnalyzer
from app.ats.utils.cv_generator.career_analyzer import CVCareerAnalyzer
from app.ats.chatbot.values.principles import ValuesPrinciples

# Configurar logger una sola vez
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Importar el nuevo analizador si está disponible
try:
    from app.ml.analyzers.team_analyzer import TeamAnalyzerImpl
    USE_NEW_ANALYZER = True
except ImportError:
    USE_NEW_ANALYZER = False
    logger.warning("TeamAnalyzerImpl no encontrado, usando implementación original")

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
        
        # Inicializar el nuevo analizador si está disponible
        if USE_NEW_ANALYZER:
            self.analyzer = TeamAnalyzerImpl()
    
    async def analyze_team_synergy(self, team_members: List[int], business_unit: str = None) -> Dict:
        """
        Analiza la sinergia de un equipo existente o propuesto.
        
        Args:
            team_members: Lista de IDs de personas en el equipo
            business_unit: Unidad de negocio (opcional)
            
        Returns:
            Dict con análisis de sinergia, visualizaciones y recomendaciones
        """
        # Validar entrada
        if not team_members or not isinstance(team_members, list):
            logger.error("Lista de miembros inválida o vacía")
            return self._get_default_analysis()
        
        # Eliminar duplicados y validar IDs
        team_members = list(set(team_members))
        if any(not isinstance(id, int) or id <= 0 for id in team_members):
            logger.error("IDs de miembros inválidos")
            return self._get_default_analysis()
        
        # Validar business_unit
        bu_obj = None
        if business_unit:
            try:
                bu_obj = await sync_to_async(BusinessUnit.objects.get)(name=business_unit)
            except ObjectDoesNotExist:
                logger.warning(f"Unidad de negocio no encontrada: {business_unit}")
                business_unit = None
        
        # Usar el nuevo analizador si está disponible
        if hasattr(self, 'analyzer') and USE_NEW_ANALYZER:
            try:
                data = {'team_members': team_members}
                result = await self.analyzer.analyze(data, bu_obj)
                return result
            except Exception as e:
                logger.error(f"Error en nuevo analizador: {str(e)}. Usando implementación original")
        
        try:
            # Obtener información detallada de los miembros
            members_data = await self._get_team_members_data(team_members)
            if not members_data:
                logger.warning("No se obtuvieron datos de miembros")
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
                'synergy_score': round(synergy_score, 2),
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
            logger.error(f"Error analizando sinergia del equipo: {str(e)}")
            return self._get_default_analysis()
    
    async def _get_team_members_data(self, member_ids: List[int]) -> List[Dict]:
        """Obtiene datos completos de los miembros del equipo."""
        members_data = []
        
        for person_id in member_ids:
            try:
                # Obtener información básica de la persona
                person = await self._get_person(person_id)
                if not person:
                    logger.warning(f"Persona no encontrada: {person_id}")
                    continue
                
                # Obtener análisis de personalidad
                personality = await self._get_personality(person_id)
                
                # Obtener habilidades
                skills = await self._get_person_skills(person_id)
                
                # Determinar generación
                birth_year = getattr(person, 'birth_date', None)
                generation = self._determine_generation(birth_year.year if birth_year else 1985)
                
                # Obtener propósito profesional y valores
                purpose = await self._get_professional_purpose(person_id)
                
                members_data.append({
                    'id': person_id,
                    'name': f"{getattr(person, 'first_name', '')} {getattr(person, 'last_name', '')}".strip() or f"Person {person_id}",
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
            return await sync_to_async(Person.objects.get)(id=person_id)
        except ObjectDoesNotExist:
            logger.error(f"Persona no encontrada: {person_id}")
            return None
        except Exception as e:
            logger.error(f"Error obteniendo persona {person_id}: {str(e)}")
            return None
    
    async def _get_personality(self, person_id: int) -> Dict:
        """Obtiene análisis de personalidad para la persona."""
        try:
            personality_result = await self.personality_analyzer.analyze_personality(person_id)
            personality_type = self._simplify_personality_type(personality_result.get('type', 'Equilibrado'))
            return {
                'type': personality_type,
                'traits': personality_result.get('traits', {}),
                'communication_style': personality_result.get('communication_style', 'Directo')
            }
        except Exception as e:
            logger.error(f"Error obteniendo personalidad para persona {person_id}: {str(e)}")
            return {
                'type': 'Equilibrado',
                'traits': {},
                'communication_style': 'Directo'
            }
    
    def _simplify_personality_type(self, personality_type: str) -> str:
        """Simplifica tipos de personalidad a 4 tipos básicos para análisis de equipo."""
        personality_type = personality_type.lower()
        if any(keyword in personality_type for keyword in ['analítico', 'lógico', 'detallista', 'pensador']):
            return 'Analítico'
        elif any(keyword in personality_type for keyword in ['colaborativo', 'relacional', 'armonizador', 'diplomático']):
            return 'Colaborativo'
        elif any(keyword in personality_type for keyword in ['director', 'dominante', 'decisivo', 'ejecutor']):
            return 'Director'
        elif any(keyword in personality_type for keyword in ['innovador', 'creativo', 'visionario', 'imaginativo']):
            return 'Innovador'
        return 'Equilibrado'
    
    async def _get_person_skills(self, person_id: int) -> List[Dict]:
        """Obtiene las habilidades de la persona con sus niveles."""
        try:
            person = await self._get_person(person_id)
            if not person:
                return []
            
            assessments = await sync_to_async(list)(
                SkillAssessment.objects.filter(person=person).select_related('skill').prefetch_related('skill__category')
            )
            
            return [
                {
                    'name': assessment.skill.name,
                    'level': assessment.score,
                    'category': getattr(assessment.skill, 'category', 'General')
                }
                for assessment in assessments
            ]
        except Exception as e:
            logger.error(f"Error obteniendo habilidades para persona {person_id}: {str(e)}")
            return []
    
    def _determine_generation(self, birth_year: int) -> str:
        """Determina la generación basada en el año de nacimiento."""
        for year_range, generation_name in self.GENERATION_MAPPING.items():
            if year_range[0] <= birth_year <= year_range[1]:
                return generation_name
        return "Generación Desconocida"
    
    async def _get_professional_purpose(self, person_id: int) -> Dict:
        """Obtiene el propósito profesional y valores."""
        try:
            possible_values = [
                "Impacto social", "Crecimiento profesional", "Innovación", 
                "Estabilidad", "Balance vida-trabajo", "Liderazgo", 
                "Autonomía", "Creatividad", "Servicio", "Excelencia"
            ]
            
            # Guardar estado del generador aleatorio
            random_state = random.getstate()
            try:
                # Usar un hash simple para consistencia
                seed = int(str(person_id)[:8]) % 10000
                random.seed(seed)
                
                num_values = random.randint(3, 5)
                primary_values = random.sample(possible_values, num_values)
                
                motivations = {
                    "económicos": random.randint(1, 10),
                    "crecimiento": random.randint(1, 10),
                    "impacto": random.randint(1, 10),
                    "reconocimiento": random.randint(1, 10),
                    "social": random.randint(1, 10)
                }
                
                purpose_areas = ["Profesional", "Social", "Económico", "Innovación", "Liderazgo"]
                primary_purpose = random.sample(purpose_areas, 2)
                
                return {
                    'primary_values': primary_values,
                    'motivations': motivations,
                    'primary_purpose': primary_purpose,
                    'alignment_score': random.randint(60, 95)
                }
            finally:
                # Restaurar estado del generador
                random.setstate(random_state)
        except Exception as e:
            logger.error(f"Error obteniendo propósito profesional para persona {person_id}: {str(e)}")
            return {
                'primary_values': ["Crecimiento profesional", "Impacto social"],
                'motivations': {"económicos": 7, "crecimiento": 8, "impacto": 6, "reconocimiento": 5, "social": 7},
                'primary_purpose': ["Profesional", "Social"],
                'alignment_score': 75
            }
    
    def _analyze_skill_composition(self, members_data: List[Dict]) -> Dict:
        """Analiza la composición de habilidades del equipo."""
        if not members_data:
            return {'coverage_score': 0, 'balance_score': 0, 'skill_gaps': [], 'skill_details': {}, 'category_distribution': {}}
        
        all_skills = defaultdict(lambda: {'levels': [], 'category': 'General'})
        skill_categories = set()
        
        for member in members_data:
            for skill in member.get('skills', []):
                skill_name = skill['name']
                skill_level = skill['level']
                skill_category = skill.get('category', 'General')
                
                all_skills[skill_name]['levels'].append(skill_level)
                all_skills[skill_name]['category'] = skill_category
                skill_categories.add(skill_category)
        
        skill_analysis = {}
        for skill_name, data in all_skills.items():
            levels = data['levels']
            avg_level = sum(levels) / len(levels) if levels else 0
            coverage = len(levels) / len(members_data)
            
            skill_analysis[skill_name] = {
                'average_level': round(avg_level, 2),
                'coverage': round(coverage, 2),
                'category': data['category'],
                'distribution': levels
            }
        
        critical_skills = [
            "Liderazgo", "Comunicación efectiva", "Resolución de problemas",
            "Análisis de datos", "Trabajo en equipo", "Adaptabilidad",
            "Gestión del tiempo", "Pensamiento crítico", "Innovación",
            "Negociación", "Gestión de proyectos"
        ]
        
        skill_gaps = [
            skill for skill in critical_skills 
            if skill not in all_skills or 
            len(all_skills[skill]['levels']) < 0.3 * len(members_data) or
            (sum(all_skills[skill]['levels']) / len(all_skills[skill]['levels']) < 7 if all_skills[skill]['levels'] else True)
        ]
        
        category_counts = defaultdict(float)
        for skill_name, data in skill_analysis.items():
            category_counts[data['category']] += data['coverage']
        
        total_categories = len(category_counts) or 1
        category_counts = {k: v / total_categories for k, v in category_counts.items()}
        
        coverage_score = min(100, (len(all_skills) / (len(critical_skills) * 0.7)) * 100)
        balance_values = list(category_counts.values())
        balance_score = min(100, (1 - np.std(balance_values) / (np.mean(balance_values) or 1)) * 100) if balance_values else 50
        
        top_skills = sorted(
            [(name, data['average_level']) for name, data in skill_analysis.items()],
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            'coverage_score': round(coverage_score, 2),
            'balance_score': round(balance_score, 2),
            'top_skills': top_skills,
            'skill_gaps': skill_gaps,
            'skill_details': skill_analysis,
            'category_distribution': category_counts
        }
    
    def _analyze_personality_distribution(self, members_data: List[Dict]) -> Dict:
        """Analiza la distribución de personalidades en el equipo."""
        personality_counts = defaultdict(int)
        for member in members_data:
            personality = member.get('personality', {}).get('type', 'Equilibrado')
            personality_counts[personality] += 1
        
        team_size = len(members_data) or 1
        personality_distribution = {
            p_type: count / team_size * 100 
            for p_type, count in personality_counts.items()
        }
        
        dominant_personality = max(personality_counts.items(), key=lambda x: x[1])[0] if personality_counts else 'Equilibrado'
        diversity_score = min(100, 100 - np.var(list(personality_distribution.values())) if personality_distribution else 0)
        
        return {
            'diversity_score': round(diversity_score, 2),
            'dominant_personality': dominant_personality,
            'distribution': personality_distribution,
            'ideal_additions': self._get_ideal_personality_additions(personality_distribution)
        }
    
    def _get_ideal_personality_additions(self, distribution: Dict) -> List[str]:
        """Determina tipos de personalidad ideales para complementar el equipo."""
        all_types = ['Analítico', 'Colaborativo', 'Director', 'Innovador']
        underrepresented = [ptype for ptype in all_types if distribution.get(ptype, 0) < 20]
        return underrepresented or ['Cualquier tipo para mantener equilibrio']
    
    def _analyze_generation_diversity(self, members_data: List[Dict]) -> Dict:
        """Analiza la diversidad generacional del equipo."""
        generation_counts = defaultdict(int)
        for member in members_data:
            generation = member.get('generation', 'Desconocida')
            generation_counts[generation] += 1
        
        team_size = len(members_data) or 1
        generation_distribution = {
            gen: count / team_size * 100 
            for gen, count in generation_counts.items()
        }
        
        diversity_score = min(100, 50 + (len(generation_counts) - 1) * 15) if generation_counts else 0
        
        return {
            'diversity_score': round(diversity_score, 2),
            'distribution': generation_distribution,
            'advantages': ["Diversidad de perspectivas"] if len(generation_counts) > 1 else ["Cohesión generacional"]
        }
    
    def _analyze_purpose_alignment(self, members_data: List[Dict]) -> Dict:
        """Analiza la alineación de propósito y valores del equipo."""
        all_values = []
        all_purposes = []
        
        for member in members_data:
            purpose_data = member.get('purpose', {})
            all_values.extend(purpose_data.get('primary_values', []))
            all_purposes.extend(purpose_data.get('primary_purpose', []))
        
        value_counts = defaultdict(int)
        for value in all_values:
            value_counts[value] += 1
        
        threshold = len(members_data) * 0.5
        common_values = [value for value, count in value_counts.items() if count >= threshold]
        
        alignment_score = min(100, len(common_values) * 20)
        
        return {
            'alignment_score': round(alignment_score, 2),
            'common_values': common_values,
            'dominant_purpose': max(all_purposes, key=all_purposes.count) if all_purposes else None
        }
    
    async def _generate_connection_network(self, members_data: List[Dict]) -> Dict:
        """Genera una red de conexiones entre miembros del equipo."""
        try:
            G = nx.Graph()
            for member in members_data:
                G.add_node(member['id'], label=member['name'], personality=member['personality']['type'])
            
            # Simular conexiones basadas en personalidad
            for i, member1 in enumerate(members_data):
                for member2 in members_data[i+1:]:
                    if member2['personality']['type'] in self.PERSONALITY_SYNERGY.get(member1['personality']['type'], []):
                        G.add_edge(member1['id'], member2['id'], weight=0.8)
                    else:
                        G.add_edge(member1['id'], member2['id'], weight=0.3)
            
            return {
                'nodes': list(G.nodes(data=True)),
                'edges': list(G.edges(data=True)),
                'density': nx.density(G)
            }
        except Exception as e:
            logger.error(f"Error generando red de conexiones: {str(e)}")
            return {'nodes': [], 'edges': [], 'density': 0}
    
    async def _create_team_visualizations(self, members_data: List[Dict], skills_analysis: Dict, personality_analysis: Dict, generation_analysis: Dict, purpose_analysis: Dict, connection_network: Dict) -> Dict:
        """Crea visualizaciones para el análisis del equipo."""
        try:
            visualizations = {
                'skill_radar': self._create_skill_radar_chart(skills_analysis),
                'personality_distribution': self._create_personality_donut(personality_analysis),
                'generation_distribution': self._create_generation_bar_chart(generation_analysis),
                'team_network': self._create_network_visualization(connection_network),
                'synergy_matrix': self._create_synergy_matrix(members_data)
            }
            return visualizations
        except Exception as e:
            logger.error(f"Error creando visualizaciones: {str(e)}")
            return {}
    
    def _create_skill_radar_chart(self, skills_analysis: Dict) -> Dict:
        """Crea un radar chart para habilidades."""
        try:
            categories = list(skills_analysis['category_distribution'].keys())
            values = list(skills_analysis['category_distribution'].values())
            
            # Normalizar para radar
            angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
            values += values[:1]
            angles += angles[:1]
            
            fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
            ax.fill(angles, values, color=self.BU_COLORS.get('huntRED', '#D62839'), alpha=0.25)
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(categories)
            ax.set_title("Distribución de Habilidades por Categoría")
            
            # Convertir a base64 para API
            import io
            import base64
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            img_str = base64.b64encode(buf.read()).decode('utf-8')
            plt.close()
            
            return {'type': 'radar', 'data': img_str}
        except Exception as e:
            logger.error(f"Error creando radar chart: {str(e)}")
            return {'type': 'radar', 'data': ''}

    def _create_personality_donut(self, personality_analysis: Dict) -> Dict:
        """Crea un donut chart para distribución de personalidades."""
        try:
            labels = list(personality_analysis['distribution'].keys())
            sizes = list(personality_analysis['distribution'].values())
            
            fig, ax = plt.subplots(figsize=(6, 6))
            wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=sns.color_palette('deep'))
            centre_circle = plt.Circle((0, 0), 0.70, fc='white')
            fig.gca().add_artist(centre_circle)
            ax.set_title("Distribución de Personalidades")
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            img_str = base64.b64encode(buf.read()).decode('utf-8')
            plt.close()
            
            return {'type': 'donut', 'data': img_str}
        except Exception as e:
            logger.error(f"Error creando donut chart: {str(e)}")
            return {'type': 'donut', 'data': ''}

    def _create_generation_bar_chart(self, generation_analysis: Dict) -> Dict:
        """Crea un bar chart para distribución generacional."""
        try:
            labels = list(generation_analysis['distribution'].keys())
            values = list(generation_analysis['distribution'].values())
            
            fig, ax = plt.subplots(figsize=(8, 5))
            sns.barplot(x=values, y=labels, palette='deep')
            ax.set_title("Distribución Generacional")
            ax.set_xlabel("Porcentaje")
            ax.set_ylabel("Generación")
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            img_str = base64.b64encode(buf.read()).decode('utf-8')
            plt.close()
            
            return {'type': 'bar', 'data': img_str}
        except Exception as e:
            logger.error(f"Error creando bar chart: {str(e)}")
            return {'type': 'bar', 'data': ''}

    def _create_network_visualization(self, connection_network: Dict) -> Dict:
        """Crea una visualización de red de conexiones."""
        try:
            G = nx.Graph()
            for node, data in connection_network['nodes']:
                G.add_node(node, **data)
            for u, v, data in connection_network['edges']:
                G.add_edge(u, v, **data)
            
            pos = nx.spring_layout(G)
            fig, ax = plt.subplots(figsize=(8, 6))
            nx.draw(G, pos, with_labels=True, node_color=self.BU_COLORS.get('huntRED', '#D62839'), 
                    edge_color='gray', node_size=500, font_size=10, ax=ax)
            ax.set_title("Red de Conexiones del Equipo")
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            img_str = base64.b64encode(buf.read()).decode('utf-8')
            plt.close()
            
            return {'type': 'network', 'data': img_str}
        except Exception as e:
            logger.error(f"Error creando visualización de red: {str(e)}")
            return {'type': 'network', 'data': ''}

    def _create_synergy_matrix(self, members_data: List[Dict]) -> Dict:
        """Crea una matriz de sinergia entre miembros."""
        try:
            n = len(members_data)
            matrix = np.zeros((n, n))
            names = [m['name'] for m in members_data]
            
            for i, m1 in enumerate(members_data):
                for j, m2 in enumerate(members_data):
                    if i != j:
                        score = 0.5  # Base
                        if m2['personality']['type'] in self.PERSONALITY_SYNERGY.get(m1['personality']['type'], []):
                            score += 0.3
                        matrix[i, j] = score
            
            fig, ax = plt.subplots(figsize=(8, 8))
            sns.heatmap(matrix, annot=True, xticklabels=names, yticklabels=names, cmap=self.huntred_cmap, ax=ax)
            ax.set_title("Matriz de Sinergia del Equipo")
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            img_str = base64.b64encode(buf.read()).decode('utf-8')
            plt.close()
            
            return {'type': 'heatmap', 'data': img_str}
        except Exception as e:
            logger.error(f"Error creando matriz de sinergia: {str(e)}")
            return {'type': 'heatmap', 'data': ''}

    def _calculate_synergy_score(self, skills_analysis: Dict, personality_analysis: Dict, generation_analysis: Dict, purpose_analysis: Dict) -> float:
        """Calcula la puntuación global de sinergia del equipo."""
        weights = {
            'skills': 0.3,
            'personality': 0.25,
            'generation': 0.15,
            'purpose': 0.3
        }
        
        skill_score = (skills_analysis.get('coverage_score', 0) + skills_analysis.get('balance_score', 0)) / 2
        personality_score = personality_analysis.get('diversity_score', 0)
        generation_score = generation_analysis.get('diversity_score', 0)
        purpose_score = purpose_analysis.get('alignment_score', 0)
        
        synergy_score = (
            skill_score * weights['skills'] +
            personality_score * weights['personality'] +
            generation_score * weights['generation'] +
            purpose_score * weights['purpose']
        )
        
        return min(100, max(0, synergy_score))
    
    def _generate_team_recommendations(self, members_data: List[Dict], skills_analysis: Dict, personality_analysis: Dict, generation_analysis: Dict, purpose_analysis: Dict, synergy_score: float) -> List[Dict]:
        """Genera recomendaciones para mejorar la sinergia del equipo."""
        recommendations = []
        
        if skills_analysis.get('skill_gaps', []):
            recommendations.append({
                'area': 'skills',
                'title': 'Cubrir brechas de habilidades',
                'description': f"El equipo necesita reforzar: {', '.join(skills_analysis['skill_gaps'][:3])}",
                'actions': [f"Capacitar al equipo en {skill}" for skill in skills_analysis['skill_gaps'][:2]]
            })
        
        if personality_analysis.get('diversity_score', 0) < 70:
            recommendations.append({
                'area': 'personality',
                'title': 'Equilibrar tipos de personalidad',
                'description': f"Incorporar personas con perfil: {', '.join(personality_analysis['ideal_additions'])}",
                'actions': ["Evaluar perfil de personalidad en nuevas contrataciones"]
            })
        
        if purpose_analysis.get('alignment_score', 0) < 70:
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
            'skills_analysis': {'coverage_score': 0, 'balance_score': 0, 'skill_gaps': [], 'skill_details': {}, 'category_distribution': {}},
            'personality_analysis': {'diversity_score': 0, 'distribution': {}, 'dominant_personality': 'Equilibrado', 'ideal_additions': []},
            'generation_analysis': {'diversity_score': 0, 'distribution': {}, 'advantages': []},
            'purpose_analysis': {'alignment_score': 0, 'common_values': [], 'dominant_purpose': None},
            'connection_network': {'nodes': [], 'edges': [], 'density': 0},
            'recommendations': [],
            'visualizations': {},
            'analyzed_at': datetime.now().isoformat()
        }