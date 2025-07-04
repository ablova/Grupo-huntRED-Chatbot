"""
Sistema de Matching con Grafos de Conocimiento
Matching inteligente usando ontologías y relaciones semánticas
"""

import networkx as nx
import numpy as np
from typing import Dict, List, Tuple, Set, Optional
from collections import defaultdict
import logging
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity
import asyncio

logger = logging.getLogger(__name__)


class KnowledgeGraphMatcher:
    """Sistema de matching basado en grafos de conocimiento"""
    
    def __init__(self):
        self.knowledge_graph = nx.DiGraph()
        self.skill_ontology = self._build_skill_ontology()
        self.industry_taxonomy = self._build_industry_taxonomy()
        self.role_hierarchy = self._build_role_hierarchy()
        self.semantic_embeddings = {}
        
    def build_candidate_subgraph(self, candidate_data: Dict) -> nx.DiGraph:
        """Construye subgrafo de conocimiento para un candidato"""
        subgraph = nx.DiGraph()
        
        # Nodo central del candidato
        candidate_id = f"candidate_{candidate_data['id']}"
        subgraph.add_node(candidate_id, type='candidate', **candidate_data)
        
        # Agregar habilidades
        for skill in candidate_data.get('skills', []):
            skill_id = f"skill_{skill['name']}"
            subgraph.add_node(skill_id, type='skill', **skill)
            subgraph.add_edge(candidate_id, skill_id, 
                            relation='has_skill', 
                            proficiency=skill.get('level', 5))
            
            # Conectar con habilidades relacionadas
            related_skills = self._get_related_skills(skill['name'])
            for related in related_skills:
                related_id = f"skill_{related['name']}"
                if related_id not in subgraph:
                    subgraph.add_node(related_id, type='skill', **related)
                subgraph.add_edge(skill_id, related_id, 
                                relation='related_to',
                                similarity=related['similarity'])
        
        # Agregar experiencia laboral
        for exp in candidate_data.get('experiences', []):
            company_id = f"company_{exp['company']}"
            role_id = f"role_{exp['role']}"
            
            subgraph.add_node(company_id, type='company', name=exp['company'])
            subgraph.add_node(role_id, type='role', title=exp['role'])
            
            subgraph.add_edge(candidate_id, company_id, 
                            relation='worked_at',
                            duration=exp.get('duration', 0))
            subgraph.add_edge(candidate_id, role_id,
                            relation='performed_role',
                            level=exp.get('level', 'mid'))
            
            # Conectar con industria
            industry = self._infer_industry(exp['company'])
            if industry:
                industry_id = f"industry_{industry}"
                subgraph.add_node(industry_id, type='industry', name=industry)
                subgraph.add_edge(company_id, industry_id, relation='belongs_to')
        
        # Agregar educación
        for edu in candidate_data.get('education', []):
            degree_id = f"degree_{edu['degree']}"
            institution_id = f"institution_{edu['institution']}"
            
            subgraph.add_node(degree_id, type='degree', name=edu['degree'])
            subgraph.add_node(institution_id, type='institution', name=edu['institution'])
            
            subgraph.add_edge(candidate_id, degree_id, 
                            relation='has_degree',
                            year=edu.get('year'))
            subgraph.add_edge(degree_id, institution_id,
                            relation='obtained_from')
        
        return subgraph
    
    def build_job_subgraph(self, job_data: Dict) -> nx.DiGraph:
        """Construye subgrafo de conocimiento para una vacante"""
        subgraph = nx.DiGraph()
        
        # Nodo central de la vacante
        job_id = f"job_{job_data['id']}"
        subgraph.add_node(job_id, type='job', **job_data)
        
        # Requisitos de habilidades
        for skill_req in job_data.get('required_skills', []):
            skill_id = f"skill_{skill_req['name']}"
            subgraph.add_node(skill_id, type='skill', **skill_req)
            subgraph.add_edge(job_id, skill_id,
                            relation='requires_skill',
                            importance=skill_req.get('importance', 5),
                            min_level=skill_req.get('min_level', 3))
        
        # Industria y dominio
        industry_id = f"industry_{job_data['industry']}"
        subgraph.add_node(industry_id, type='industry', name=job_data['industry'])
        subgraph.add_edge(job_id, industry_id, relation='in_industry')
        
        # Jerarquía de roles
        role_hierarchy = self._get_role_hierarchy(job_data['title'])
        for i, role in enumerate(role_hierarchy):
            role_id = f"role_{role}"
            subgraph.add_node(role_id, type='role', title=role, level=i)
            if i > 0:
                prev_role_id = f"role_{role_hierarchy[i-1]}"
                subgraph.add_edge(prev_role_id, role_id, relation='promotes_to')
        
        return subgraph
    
    def calculate_semantic_match(self, candidate_subgraph: nx.DiGraph,
                               job_subgraph: nx.DiGraph) -> Dict[str, float]:
        """Calcula match semántico entre candidato y vacante"""
        
        # Combinar grafos para análisis
        combined_graph = nx.compose(candidate_subgraph, job_subgraph)
        
        # Análisis de caminos y conectividad
        match_scores = {
            'skill_match': self._calculate_skill_match(candidate_subgraph, job_subgraph),
            'experience_relevance': self._calculate_experience_relevance(candidate_subgraph, job_subgraph),
            'industry_alignment': self._calculate_industry_alignment(candidate_subgraph, job_subgraph),
            'role_progression': self._calculate_role_progression(candidate_subgraph, job_subgraph),
            'knowledge_transfer': self._calculate_knowledge_transfer_potential(combined_graph),
            'hidden_connections': self._discover_hidden_connections(combined_graph)
        }
        
        # Score compuesto ponderado
        weights = {
            'skill_match': 0.35,
            'experience_relevance': 0.25,
            'industry_alignment': 0.15,
            'role_progression': 0.15,
            'knowledge_transfer': 0.05,
            'hidden_connections': 0.05
        }
        
        total_score = sum(score * weights[key] for key, score in match_scores.items())
        
        return {
            'total_score': total_score,
            'breakdown': match_scores,
            'insights': self._generate_match_insights(combined_graph, match_scores)
        }
    
    def discover_talent_communities(self, candidates: List[Dict]) -> Dict[str, List[int]]:
        """Descubre comunidades de talento usando detección de comunidades en grafos"""
        
        # Construir grafo completo de candidatos
        talent_graph = nx.Graph()
        
        for candidate in candidates:
            cand_id = candidate['id']
            talent_graph.add_node(cand_id, **candidate)
            
            # Conectar candidatos similares
            for other in candidates:
                if other['id'] != cand_id:
                    similarity = self._calculate_candidate_similarity(candidate, other)
                    if similarity > 0.7:  # Umbral de similitud
                        talent_graph.add_edge(cand_id, other['id'], weight=similarity)
        
        # Detectar comunidades usando algoritmo de Louvain
        import community
        communities = community.best_partition(talent_graph)
        
        # Agrupar candidatos por comunidad
        community_groups = defaultdict(list)
        for node, comm_id in communities.items():
            community_groups[f"community_{comm_id}"].append(node)
        
        # Caracterizar cada comunidad
        community_profiles = {}
        for comm_name, members in community_groups.items():
            profile = self._profile_community(members, candidates)
            community_profiles[comm_name] = {
                'members': members,
                'profile': profile,
                'cohesion_score': self._calculate_community_cohesion(members, talent_graph)
            }
        
        return community_profiles
    
    def predict_career_paths(self, candidate_subgraph: nx.DiGraph) -> List[Dict]:
        """Predice posibles trayectorias profesionales usando el grafo"""
        
        career_paths = []
        candidate_node = [n for n, d in candidate_subgraph.nodes(data=True) 
                         if d.get('type') == 'candidate'][0]
        
        # Obtener rol actual
        current_roles = [n for n in candidate_subgraph.neighbors(candidate_node)
                        if candidate_subgraph.nodes[n].get('type') == 'role']
        
        for role in current_roles:
            # Explorar caminos de progresión
            role_title = candidate_subgraph.nodes[role].get('title')
            progressions = self._get_career_progressions(role_title)
            
            for prog in progressions:
                path = {
                    'current_role': role_title,
                    'next_role': prog['next_role'],
                    'required_skills': prog['skill_gaps'],
                    'estimated_time': prog['typical_duration'],
                    'probability': prog['success_probability'],
                    'recommended_actions': prog['recommendations']
                }
                career_paths.append(path)
        
        # Ordenar por probabilidad de éxito
        career_paths.sort(key=lambda x: x['probability'], reverse=True)
        
        return career_paths[:5]  # Top 5 caminos
    
    def _calculate_skill_match(self, candidate_graph: nx.DiGraph, 
                             job_graph: nx.DiGraph) -> float:
        """Calcula coincidencia de habilidades usando el grafo"""
        
        # Extraer habilidades del candidato
        candidate_skills = {
            n: d for n, d in candidate_graph.nodes(data=True)
            if d.get('type') == 'skill'
        }
        
        # Extraer habilidades requeridas
        job_skills = {
            n: d for n, d in job_graph.nodes(data=True)
            if d.get('type') == 'skill'
        }
        
        if not job_skills:
            return 1.0  # Si no hay requisitos, match perfecto
        
        total_match = 0
        total_importance = 0
        
        for job_skill_id, job_skill_data in job_skills.items():
            skill_name = job_skill_data.get('name')
            importance = job_skill_data.get('importance', 5)
            min_level = job_skill_data.get('min_level', 3)
            
            # Buscar coincidencia directa o similar
            best_match = 0
            for cand_skill_id, cand_skill_data in candidate_skills.items():
                if cand_skill_data.get('name') == skill_name:
                    # Coincidencia exacta
                    level = cand_skill_data.get('level', 5)
                    best_match = min(level / min_level, 1.0)
                else:
                    # Verificar similitud semántica
                    similarity = self._calculate_skill_similarity(
                        skill_name, 
                        cand_skill_data.get('name')
                    )
                    if similarity > 0.8:
                        level = cand_skill_data.get('level', 5) * similarity
                        best_match = max(best_match, min(level / min_level, 1.0))
            
            total_match += best_match * importance
            total_importance += importance
        
        return total_match / max(total_importance, 1)
    
    def _build_skill_ontology(self) -> nx.DiGraph:
        """Construye ontología de habilidades"""
        ontology = nx.DiGraph()
        
        # Categorías principales
        categories = {
            'technical': ['programming', 'data_science', 'cloud', 'security'],
            'soft': ['leadership', 'communication', 'teamwork', 'problem_solving'],
            'domain': ['finance', 'healthcare', 'retail', 'manufacturing']
        }
        
        for category, subcategories in categories.items():
            ontology.add_node(category, type='category')
            for subcat in subcategories:
                ontology.add_node(subcat, type='subcategory')
                ontology.add_edge(category, subcat, relation='has_subcategory')
        
        return ontology
    
    def _calculate_candidate_similarity(self, cand1: Dict, cand2: Dict) -> float:
        """Calcula similitud entre dos candidatos"""
        
        # Vectorizar características
        features1 = self._vectorize_candidate(cand1)
        features2 = self._vectorize_candidate(cand2)
        
        # Similitud del coseno
        similarity = cosine_similarity([features1], [features2])[0][0]
        
        return float(similarity)
    
    def _generate_match_insights(self, combined_graph: nx.DiGraph, 
                               scores: Dict[str, float]) -> List[str]:
        """Genera insights sobre el match"""
        insights = []
        
        if scores['skill_match'] > 0.8:
            insights.append("Excelente coincidencia de habilidades técnicas")
        elif scores['skill_match'] < 0.5:
            insights.append("Requiere desarrollo significativo de habilidades")
        
        if scores['hidden_connections'] > 0:
            insights.append("Se encontraron conexiones no obvias que podrían ser ventajosas")
        
        if scores['role_progression'] > 0.7:
            insights.append("La progresión de carrera del candidato está bien alineada")
        
        return insights