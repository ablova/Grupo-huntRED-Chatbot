# app/ml/aura/graph_builder.py
"""
Constructor de Grafos del Sistema Aura

basada en coincidencias temporales y organizacionales.
Este módulo implementa la construcción de la red de relaciones profesionales
"""

import logging
import networkx as nx
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime, date
from enum import Enum
import asyncio

from app.models import Person, BusinessUnit, Vacante

logger = logging.getLogger(__name__)

class ConnectionType(Enum):
    """Tipos de conexiones en la red profesional."""
    SAME_COMPANY = "same_company"
    SAME_DEPARTMENT = "same_department"
    SAME_ROLE = "same_role"
    SAME_PERIOD = "same_period"
    PROJECT_COLLABORATION = "project_collaboration"
    MENTORSHIP = "mentorship"
    REFERENCE = "reference"
    NETWORK = "network"

class ConnectionStrength(Enum):
    """Fuerza de las conexiones."""
    STRONG = "strong"      # Trabajaron juntos directamente
    MEDIUM = "medium"      # Mismo departamento/rol
    WEAK = "weak"          # Misma empresa/periodo
    VERY_WEAK = "very_weak" # Conexión indirecta

@dataclass
class ProfessionalConnection:
    """Conexión profesional entre dos personas."""
    person1_id: int
    person2_id: int
    connection_type: ConnectionType
    strength: ConnectionStrength
    start_date: Optional[date]
    end_date: Optional[date]
    company: Optional[str]
    department: Optional[str]
    role: Optional[str]
    project: Optional[str]
    evidence: List[str]
    confidence: float
    created_at: datetime

@dataclass
class NetworkNode:
    """Nodo en la red profesional."""
    person_id: int
    name: str
    current_company: Optional[str]
    current_role: Optional[str]
    skills: List[str]
    experience_years: int
    connections_count: int
    influence_score: float
    hub_score: float
    metadata: Dict[str, Any]

@dataclass
class NetworkInsight:
    """Insight de la red profesional."""
    insight_type: str
    description: str
    confidence: float
    recommendations: List[str]
    affected_nodes: List[int]
    metadata: Dict[str, Any]

class AuraGraphBuilder:
    """
    Constructor de la red de relaciones profesionales.
    
    Construye y mantiene un grafo de relaciones profesionales basado en
    coincidencias temporales y organizacionales entre personas.
    """
    
    def __init__(self):
        """Inicializa el constructor de grafos."""
        self.graph = nx.Graph()
        self.connection_weights = {
            ConnectionType.SAME_COMPANY: 0.3,
            ConnectionType.SAME_DEPARTMENT: 0.6,
            ConnectionType.SAME_ROLE: 0.5,
            ConnectionType.SAME_PERIOD: 0.4,
            ConnectionType.PROJECT_COLLABORATION: 0.8,
            ConnectionType.MENTORSHIP: 0.9,
            ConnectionType.REFERENCE: 0.7,
            ConnectionType.NETWORK: 0.2
        }
        
        self.strength_weights = {
            ConnectionStrength.STRONG: 1.0,
            ConnectionStrength.MEDIUM: 0.7,
            ConnectionStrength.WEAK: 0.4,
            ConnectionStrength.VERY_WEAK: 0.2
        }
        
        logger.info("Constructor de grafos Aura inicializado")
    
    async def build_professional_network(
        self,
        people_data: List[Dict[str, Any]],
        include_historical: bool = True
    ) -> nx.Graph:
        """
        Construye la red profesional completa.
        
        Args:
            people_data: Lista de datos de personas
            include_historical: Incluir datos históricos
            
        Returns:
            Grafo de la red profesional
        """
        try:
            # Limpiar grafo existente
            self.graph.clear()
            
            # Agregar nodos
            await self._add_nodes(people_data)
            
            # Construir conexiones
            await self._build_connections(people_data, include_historical)
            
            # Calcular métricas de red
            await self._calculate_network_metrics()
            
            logger.info(f"Red profesional construida: {self.graph.number_of_nodes()} nodos, {self.graph.number_of_edges()} conexiones")
            
            return self.graph
            
        except Exception as e:
            logger.error(f"Error construyendo red profesional: {str(e)}")
            return nx.Graph()
    
    async def find_connections(
        self,
        person_id: int,
        connection_types: Optional[List[ConnectionType]] = None,
        min_strength: Optional[ConnectionStrength] = None
    ) -> List[ProfessionalConnection]:
        """
        Encuentra conexiones de una persona específica.
        
        Args:
            person_id: ID de la persona
            connection_types: Tipos de conexión a buscar
            min_strength: Fuerza mínima de conexión
            
        Returns:
            Lista de conexiones encontradas
        """
        try:
            connections = []
            
            if person_id not in self.graph:
                return connections
            
            # Obtener vecinos en el grafo
            neighbors = list(self.graph.neighbors(person_id))
            
            for neighbor_id in neighbors:
                edge_data = self.graph.get_edge_data(person_id, neighbor_id)
                
                if not edge_data:
                    continue
                
                connection = edge_data.get('connection')
                if not connection:
                    continue
                
                # Filtrar por tipo de conexión
                if connection_types and connection.connection_type not in connection_types:
                    continue
                
                # Filtrar por fuerza mínima
                if min_strength:
                    strength_order = list(ConnectionStrength)
                    if strength_order.index(connection.strength) < strength_order.index(min_strength):
                        continue
                
                connections.append(connection)
            
            return connections
            
        except Exception as e:
            logger.error(f"Error encontrando conexiones: {str(e)}")
            return []
    
    async def detect_synergies(
        self,
        team_data: List[Dict[str, Any]],
        min_synergy_score: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Detecta sinergias entre equipos o personas.
        
        Args:
            team_data: Datos de los equipos/personas
            min_synergy_score: Score mínimo de sinergia
            
        Returns:
            Lista de sinergias detectadas
        """
        try:
            synergies = []
            
            # Analizar todas las combinaciones de equipos
            for i in range(len(team_data)):
                for j in range(i + 1, len(team_data)):
                    team1 = team_data[i]
                    team2 = team_data[j]
                    
                    synergy_score = await self._calculate_team_synergy(team1, team2)
                    
                    if synergy_score >= min_synergy_score:
                        synergy = {
                            'team1': team1,
                            'team2': team2,
                            'synergy_score': synergy_score,
                            'synergy_factors': await self._identify_synergy_factors(team1, team2),
                            'recommendations': await self._generate_synergy_recommendations(team1, team2, synergy_score)
                        }
                        synergies.append(synergy)
            
            # Ordenar por score de sinergia
            synergies.sort(key=lambda x: x['synergy_score'], reverse=True)
            
            return synergies
            
        except Exception as e:
            logger.error(f"Error detectando sinergias: {str(e)}")
            return []
    
    async def find_references(
        self,
        person_id: int,
        reference_type: str = "professional",
        min_connection_strength: ConnectionStrength = ConnectionStrength.MEDIUM
    ) -> List[Dict[str, Any]]:
        """
        Encuentra referencias válidas para una persona.
        
        Args:
            person_id: ID de la persona
            reference_type: Tipo de referencia
            min_connection_strength: Fuerza mínima de conexión
            
        Returns:
            Lista de referencias encontradas
        """
        try:
            references = []
            
            # Obtener conexiones fuertes
            connections = await self.find_connections(
                person_id,
                min_strength=min_connection_strength
            )
            
            for connection in connections:
                # Determinar el otro participante en la conexión
                other_person_id = connection.person2_id if connection.person1_id == person_id else connection.person1_id
                
                # Obtener datos de la otra persona
                other_person_data = await self._get_person_data(other_person_id)
                
                if not other_person_data:
                    continue
                
                # Calcular score de referencia
                reference_score = await self._calculate_reference_score(connection, other_person_data)
                
                reference = {
                    'reference_person_id': other_person_id,
                    'reference_person_name': other_person_data.get('name', ''),
                    'reference_person_role': other_person_data.get('current_role', ''),
                    'reference_person_company': other_person_data.get('current_company', ''),
                    'connection_type': connection.connection_type.value,
                    'connection_strength': connection.strength.value,
                    'connection_period': {
                        'start': connection.start_date.isoformat() if connection.start_date else None,
                        'end': connection.end_date.isoformat() if connection.end_date else None
                    },
                    'reference_score': reference_score,
                    'evidence': connection.evidence,
                    'confidence': connection.confidence
                }
                
                references.append(reference)
            
            # Ordenar por score de referencia
            references.sort(key=lambda x: x['reference_score'], reverse=True)
            
            return references
            
        except Exception as e:
            logger.error(f"Error encontrando referencias: {str(e)}")
            return []
    
    async def detect_hubs_and_influencers(
        self,
        min_hub_score: float = 0.7,
        min_influence_score: float = 0.6
    ) -> Dict[str, List[NetworkNode]]:
        """
        Detecta hubs e influencers en la red.
        
        Args:
            min_hub_score: Score mínimo para ser considerado hub
            min_influence_score: Score mínimo para ser considerado influencer
            
        Returns:
            Diccionario con hubs e influencers
        """
        try:
            hubs = []
            influencers = []
            
            for node_id in self.graph.nodes():
                node_data = self.graph.nodes[node_id]
                
                # Calcular métricas de red
                degree_centrality = nx.degree_centrality(self.graph).get(node_id, 0)
                betweenness_centrality = nx.betweenness_centrality(self.graph).get(node_id, 0)
                closeness_centrality = nx.closeness_centrality(self.graph).get(node_id, 0)
                
                # Calcular scores
                hub_score = (degree_centrality + betweenness_centrality) / 2
                influence_score = (closeness_centrality + degree_centrality) / 2
                
                # Crear nodo de red
                network_node = NetworkNode(
                    person_id=node_id,
                    name=node_data.get('name', ''),
                    current_company=node_data.get('current_company'),
                    current_role=node_data.get('current_role'),
                    skills=node_data.get('skills', []),
                    experience_years=node_data.get('experience_years', 0),
                    connections_count=len(list(self.graph.neighbors(node_id))),
                    influence_score=influence_score,
                    hub_score=hub_score,
                    metadata={
                        'degree_centrality': degree_centrality,
                        'betweenness_centrality': betweenness_centrality,
                        'closeness_centrality': closeness_centrality
                    }
                )
                
                # Clasificar como hub o influencer
                if hub_score >= min_hub_score:
                    hubs.append(network_node)
                
                if influence_score >= min_influence_score:
                    influencers.append(network_node)
            
            # Ordenar por scores
            hubs.sort(key=lambda x: x.hub_score, reverse=True)
            influencers.sort(key=lambda x: x.influence_score, reverse=True)
            
            return {
                'hubs': hubs,
                'influencers': influencers
            }
            
        except Exception as e:
            logger.error(f"Error detectando hubs e influencers: {str(e)}")
            return {'hubs': [], 'influencers': []}
    
    async def generate_network_insights(self) -> List[NetworkInsight]:
        """
        Genera insights de la red profesional.
        
        Returns:
            Lista de insights de la red
        """
        try:
            insights = []
            
            # Insight 1: Densidad de la red
            density = nx.density(self.graph)
            if density < 0.1:
                insights.append(NetworkInsight(
                    insight_type="low_network_density",
                    description=f"La red tiene baja densidad ({density:.2f}), lo que indica pocas conexiones entre miembros",
                    confidence=0.8,
                    recommendations=[
                        "Organizar eventos de networking",
                        "Fomentar colaboraciones entre departamentos",
                        "Implementar programas de mentoría"
                    ],
                    affected_nodes=list(self.graph.nodes()),
                    metadata={'density': density}
                ))
            
            # Insight 2: Componentes conectados
            components = list(nx.connected_components(self.graph))
            if len(components) > 1:
                insights.append(NetworkInsight(
                    insight_type="disconnected_components",
                    description=f"La red tiene {len(components)} componentes desconectados",
                    confidence=0.9,
                    recommendations=[
                        "Identificar puentes entre componentes",
                        "Fomentar conexiones entre grupos aislados",
                        "Crear proyectos interdepartamentales"
                    ],
                    affected_nodes=list(self.graph.nodes()),
                    metadata={'component_count': len(components)}
                ))
            
            # Insight 3: Hubs de conocimiento
            hubs_info = await self.detect_hubs_and_influencers()
            if hubs_info['hubs']:
                top_hubs = hubs_info['hubs'][:3]
                insights.append(NetworkInsight(
                    insight_type="knowledge_hubs",
                    description=f"Se identificaron {len(hubs_info['hubs'])} hubs de conocimiento en la red",
                    confidence=0.7,
                    recommendations=[
                        "Aprovechar los hubs para difundir conocimiento",
                        "Crear programas de mentoría con los hubs",
                        "Incluir hubs en proyectos estratégicos"
                    ],
                    affected_nodes=[hub.person_id for hub in top_hubs],
                    metadata={'hub_count': len(hubs_info['hubs'])}
                ))
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generando insights de red: {str(e)}")
            return []
    
    async def _add_nodes(self, people_data: List[Dict[str, Any]]) -> None:
        """Agrega nodos al grafo."""
        for person_data in people_data:
            person_id = person_data['id']
            
            # Agregar nodo con atributos
            self.graph.add_node(person_id, **person_data)
    
    async def _build_connections(
        self,
        people_data: List[Dict[str, Any]],
        include_historical: bool
    ) -> None:
        """Construye las conexiones entre nodos."""
        for i in range(len(people_data)):
            for j in range(i + 1, len(people_data)):
                person1 = people_data[i]
                person2 = people_data[j]
                
                # Buscar conexiones
                connections = await self._find_connections_between_persons(person1, person2, include_historical)
                
                # Agregar conexiones al grafo
                for connection in connections:
                    self.graph.add_edge(
                        connection.person1_id,
                        connection.person2_id,
                        connection=connection,
                        weight=self._calculate_edge_weight(connection)
                    )
    
    async def _find_connections_between_persons(
        self,
        person1: Dict[str, Any],
        person2: Dict[str, Any],
        include_historical: bool
    ) -> List[ProfessionalConnection]:
        """Encuentra conexiones entre dos personas."""
        connections = []
        
        # Conexión por empresa actual
        if person1.get('current_company') and person2.get('current_company'):
            if person1['current_company'] == person2['current_company']:
                connection = ProfessionalConnection(
                    person1_id=person1['id'],
                    person2_id=person2['id'],
                    connection_type=ConnectionType.SAME_COMPANY,
                    strength=ConnectionStrength.WEAK,
                    start_date=None,
                    end_date=None,
                    company=person1['current_company'],
                    department=None,
                    role=None,
                    project=None,
                    evidence=[f"Ambos trabajan en {person1['current_company']}"],
                    confidence=0.8,
                    created_at=datetime.now()
                )
                connections.append(connection)
        
        # Conexión por rol actual
        if person1.get('current_role') and person2.get('current_role'):
            if person1['current_role'] == person2['current_role']:
                connection = ProfessionalConnection(
                    person1_id=person1['id'],
                    person2_id=person2['id'],
                    connection_type=ConnectionType.SAME_ROLE,
                    strength=ConnectionStrength.MEDIUM,
                    start_date=None,
                    end_date=None,
                    company=person1.get('current_company'),
                    department=None,
                    role=person1['current_role'],
                    project=None,
                    evidence=[f"Ambos tienen el rol de {person1['current_role']}"],
                    confidence=0.7,
                    created_at=datetime.now()
                )
                connections.append(connection)
        
        # Conexión por habilidades compartidas
        skills1 = set(person1.get('skills', []))
        skills2 = set(person2.get('skills', []))
        shared_skills = skills1.intersection(skills2)
        
        if len(shared_skills) >= 3:  # Al menos 3 habilidades compartidas
            connection = ProfessionalConnection(
                person1_id=person1['id'],
                person2_id=person2['id'],
                connection_type=ConnectionType.NETWORK,
                strength=ConnectionStrength.VERY_WEAK,
                start_date=None,
                end_date=None,
                company=None,
                department=None,
                role=None,
                project=None,
                evidence=[f"Comparten {len(shared_skills)} habilidades: {', '.join(list(shared_skills)[:3])}"],
                confidence=0.5,
                created_at=datetime.now()
            )
            connections.append(connection)
        
        return connections
    
    def _calculate_edge_weight(self, connection: ProfessionalConnection) -> float:
        """Calcula el peso de una arista basado en la conexión."""
        base_weight = self.connection_weights.get(connection.connection_type, 0.5)
        strength_weight = self.strength_weights.get(connection.strength, 0.5)
        
        return base_weight * strength_weight * connection.confidence
    
    async def _calculate_network_metrics(self) -> None:
        """Calcula métricas de la red."""
        try:
            # Calcular centralidad para todos los nodos
            degree_centrality = nx.degree_centrality(self.graph)
            betweenness_centrality = nx.betweenness_centrality(self.graph)
            closeness_centrality = nx.closeness_centrality(self.graph)
            
            # Agregar métricas a los nodos
            for node_id in self.graph.nodes():
                self.graph.nodes[node_id]['degree_centrality'] = degree_centrality.get(node_id, 0)
                self.graph.nodes[node_id]['betweenness_centrality'] = betweenness_centrality.get(node_id, 0)
                self.graph.nodes[node_id]['closeness_centrality'] = closeness_centrality.get(node_id, 0)
                
        except Exception as e:
            logger.error(f"Error calculando métricas de red: {str(e)}")
    
    async def _calculate_team_synergy(self, team1: Dict[str, Any], team2: Dict[str, Any]) -> float:
        """Calcula la sinergia entre dos equipos."""
        try:
            # Factores de sinergia
            skill_complementarity = self._calculate_skill_complementarity(team1, team2)
            experience_diversity = self._calculate_experience_diversity(team1, team2)
            cultural_alignment = self._calculate_cultural_alignment(team1, team2)
            
            # Score final ponderado
            synergy_score = (
                skill_complementarity * 0.4 +
                experience_diversity * 0.3 +
                cultural_alignment * 0.3
            )
            
            return synergy_score
            
        except Exception as e:
            logger.error(f"Error calculando sinergia de equipos: {str(e)}")
            return 0.0
    
    def _calculate_skill_complementarity(self, team1: Dict[str, Any], team2: Dict[str, Any]) -> float:
        """Calcula la complementariedad de habilidades."""
        skills1 = set(team1.get('skills', []))
        skills2 = set(team2.get('skills', []))
        
        # Habilidades únicas de cada equipo
        unique_skills1 = skills1 - skills2
        unique_skills2 = skills2 - skills1
        
        # Score basado en complementariedad
        total_unique = len(unique_skills1) + len(unique_skills2)
        total_skills = len(skills1.union(skills2))
        
        if total_skills == 0:
            return 0.0
        
        return total_unique / total_skills
    
    def _calculate_experience_diversity(self, team1: Dict[str, Any], team2: Dict[str, Any]) -> float:
        """Calcula la diversidad de experiencia."""
        exp1 = team1.get('experience_years', 0)
        exp2 = team2.get('experience_years', 0)
        
        # Score basado en diferencia de experiencia
        diff = abs(exp1 - exp2)
        max_exp = max(exp1, exp2)
        
        if max_exp == 0:
            return 0.0
        
        return min(1.0, diff / max_exp)
    
    def _calculate_cultural_alignment(self, team1: Dict[str, Any], team2: Dict[str, Any]) -> float:
        """Calcula la alineación cultural."""
        # Implementación básica
        return 0.7
    
    async def _identify_synergy_factors(self, team1: Dict[str, Any], team2: Dict[str, Any]) -> List[str]:
        """Identifica factores de sinergia."""
        factors = []
        
        # Habilidades complementarias
        skills1 = set(team1.get('skills', []))
        skills2 = set(team2.get('skills', []))
        complementary_skills = skills1.symmetric_difference(skills2)
        
        if complementary_skills:
            factors.append(f"Habilidades complementarias: {', '.join(list(complementary_skills)[:3])}")
        
        # Experiencia diversa
        exp1 = team1.get('experience_years', 0)
        exp2 = team2.get('experience_years', 0)
        if abs(exp1 - exp2) > 5:
            factors.append("Experiencia diversa en años")
        
        return factors
    
    async def _generate_synergy_recommendations(
        self,
        team1: Dict[str, Any],
        team2: Dict[str, Any],
        synergy_score: float
    ) -> List[str]:
        """Genera recomendaciones de sinergia."""
        recommendations = []
        
        if synergy_score > 0.8:
            recommendations.append("Alta sinergia detectada - considerar colaboración directa")
            recommendations.append("Crear proyectos conjuntos para maximizar complementariedad")
        elif synergy_score > 0.6:
            recommendations.append("Sinergia moderada - explorar oportunidades de colaboración")
            recommendations.append("Compartir mejores prácticas entre equipos")
        else:
            recommendations.append("Sinergia baja - buscar áreas específicas de colaboración")
        
        return recommendations
    
    async def _calculate_reference_score(
        self,
        connection: ProfessionalConnection,
        reference_person_data: Dict[str, Any]
    ) -> float:
        """Calcula el score de referencia."""
        try:
            # Factores que contribuyen al score
            connection_strength = self.strength_weights.get(connection.strength, 0.5)
            connection_confidence = connection.confidence
            reference_experience = reference_person_data.get('experience_years', 0)
            reference_current_role = reference_person_data.get('current_role', '')
            
            # Score base
            base_score = connection_strength * connection_confidence
            
            # Bonus por experiencia del referente
            experience_bonus = min(0.2, reference_experience / 100)
            
            # Bonus por rol actual del referente
            role_bonus = 0.1 if reference_current_role else 0
            
            final_score = base_score + experience_bonus + role_bonus
            
            return min(1.0, final_score)
            
        except Exception as e:
            logger.error(f"Error calculando score de referencia: {str(e)}")
            return 0.5
    
    async def _get_person_data(self, person_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene datos de una persona."""
        try:
            if person_id in self.graph:
                return dict(self.graph.nodes[person_id])
            return None
        except Exception as e:
            logger.error(f"Error obteniendo datos de persona: {str(e)}")
            return None

    def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """
        Obtiene el contexto de red de un usuario.
        Método requerido por PersonalizationEngine.
        """
        try:
            # Convertir user_id a int si es necesario
            person_id = int(user_id) if user_id.isdigit() else None
            
            if not person_id or person_id not in self.graph:
                return {
                    "influencer_score": 0.0,
                    "suggested_connections": [],
                    "network_size": 0,
                    "hub_score": 0.0
                }
            
            # Obtener datos del nodo
            node_data = self.graph.nodes[person_id]
            
            # Calcular métricas de red
            connections = list(self.graph.neighbors(person_id))
            influence_score = node_data.get('influence_score', 0.0)
            hub_score = node_data.get('hub_score', 0.0)
            
            # Sugerir conexiones (primeros 5 vecinos)
            suggested_connections = connections[:5]
            
            return {
                "influencer_score": influence_score,
                "suggested_connections": suggested_connections,
                "network_size": len(connections),
                "hub_score": hub_score,
                "degree_centrality": node_data.get('degree_centrality', 0.0),
                "betweenness_centrality": node_data.get('betweenness_centrality', 0.0)
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo contexto de usuario {user_id}: {str(e)}")
            return {
                "influencer_score": 0.0,
                "suggested_connections": [],
                "network_size": 0,
                "hub_score": 0.0
            }

    def infer_segment(self, user_id: str) -> Optional[str]:
        """
        Infiere el segmento de un usuario basado en su contexto de red.
        Método requerido por PersonalizationEngine.
        """
        try:
            context = self.get_user_context(user_id)
            
            # Lógica de inferencia de segmento basada en métricas de red
            influencer_score = context.get('influencer_score', 0.0)
            hub_score = context.get('hub_score', 0.0)
            network_size = context.get('network_size', 0)
            
            # Segmentación basada en métricas de red
            if influencer_score > 0.8 or hub_score > 0.8:
                return "executive"
            elif network_size > 50:
                return "recruiter"
            elif network_size > 20:
                return "junior"
            else:
                return "student"
                
        except Exception as e:
            logger.error(f"Error infiriendo segmento para usuario {user_id}: {str(e)}")
            return None

# Alias global para mantener compatibilidad con código existente
GNNManager = AuraGraphBuilder 