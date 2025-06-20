"""
AURA - AR Network Viewer (FASE 3)
Visualización de redes profesionales en realidad aumentada
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import json
import cv2
from datetime import datetime
import math

logger = logging.getLogger(__name__)

# CONFIGURACIÓN: DESHABILITADO POR DEFECTO
ENABLED = False  # Cambiar a True para habilitar


@dataclass
class ARNode:
    """Nodo en realidad aumentada"""
    id: str
    name: str
    position: Tuple[float, float, float]  # x, y, z en espacio 3D
    size: float
    color: Tuple[int, int, int]  # RGB
    type: str
    data: Dict[str, Any]
    visible: bool = True
    selected: bool = False


@dataclass
class AREdge:
    """Conexión en realidad aumentada"""
    id: str
    from_node: str
    to_node: str
    strength: float
    color: Tuple[int, int, int]
    visible: bool = True
    animated: bool = False


@dataclass
class AROverlay:
    """Overlay de información en AR"""
    id: str
    content: str
    position: Tuple[float, float, float]
    type: str  # 'info', 'alert', 'highlight'
    duration: float  # segundos
    created_at: datetime = field(default_factory=datetime.now)


class ARNetworkViewer:
    """
    Visualizador de redes profesionales en realidad aumentada
    """
    
    def __init__(self):
        self.enabled = ENABLED
        if not self.enabled:
            logger.info("ARNetworkViewer: DESHABILITADO")
            return
        
        self.nodes = {}
        self.edges = {}
        self.overlays = {}
        self.camera_position = (0, 0, 0)
        self.camera_rotation = (0, 0, 0)
        self.scale_factor = 1.0
        self.interaction_mode = "view"  # 'view', 'select', 'edit'
        
        # Configuración de AR
        self.ar_config = {
            "node_size_range": (0.1, 0.5),
            "edge_width_range": (0.01, 0.05),
            "max_distance": 10.0,
            "fade_distance": 8.0,
            "animation_speed": 1.0,
            "interaction_distance": 2.0
        }
        
        logger.info("ARNetworkViewer: Inicializado")
    
    def load_network_data(self, network_data: Dict[str, Any]) -> bool:
        """
        Carga datos de red para visualización AR
        """
        if not self.enabled:
            return self._get_mock_load_result()
        
        try:
            # Limpiar datos existentes
            self.nodes.clear()
            self.edges.clear()
            self.overlays.clear()
            
            # Cargar nodos
            for node_data in network_data.get("nodes", []):
                node = self._create_ar_node(node_data)
                self.nodes[node.id] = node
            
            # Cargar conexiones
            for edge_data in network_data.get("edges", []):
                edge = self._create_ar_edge(edge_data)
                self.edges[edge.id] = edge
            
            # Posicionar nodos en espacio 3D
            self._position_nodes_3d()
            
            logger.info(f"ARNetworkViewer: Cargados {len(self.nodes)} nodos y {len(self.edges)} conexiones")
            return True
            
        except Exception as e:
            logger.error(f"Error loading network data for AR: {e}")
            return False
    
    def _create_ar_node(self, node_data: Dict[str, Any]) -> ARNode:
        """Crea nodo AR desde datos"""
        node_id = str(node_data.get("id"))
        
        # Calcular tamaño basado en influencia
        influence = node_data.get("influence_score", 0.5)
        size = self.ar_config["node_size_range"][0] + (
            influence * (self.ar_config["node_size_range"][1] - self.ar_config["node_size_range"][0])
        )
        
        # Calcular color basado en tipo
        node_type = node_data.get("type", "regular")
        color = self._get_node_color(node_type)
        
        return ARNode(
            id=node_id,
            name=node_data.get("name", "Unknown"),
            position=(0, 0, 0),  # Se posicionará después
            size=size,
            color=color,
            type=node_type,
            data=node_data
        )
    
    def _create_ar_edge(self, edge_data: Dict[str, Any]) -> AREdge:
        """Crea conexión AR desde datos"""
        edge_id = f"{edge_data.get('from')}_{edge_data.get('to')}"
        
        # Calcular color basado en fuerza de conexión
        strength = edge_data.get("strength", 0.5)
        color = self._get_edge_color(strength)
        
        return AREdge(
            id=edge_id,
            from_node=str(edge_data.get("from")),
            to_node=str(edge_data.get("to")),
            strength=strength,
            color=color
        )
    
    def _position_nodes_3d(self):
        """Posiciona nodos en espacio 3D"""
        if not self.nodes:
            return
        
        # Usar algoritmo de posicionamiento 3D
        positions = self._calculate_3d_positions()
        
        for i, (node_id, node) in enumerate(self.nodes.items()):
            if i < len(positions):
                node.position = positions[i]
    
    def _calculate_3d_positions(self) -> List[Tuple[float, float, float]]:
        """Calcula posiciones 3D para nodos"""
        num_nodes = len(self.nodes)
        positions = []
        
        if num_nodes <= 1:
            return [(0, 0, 0)]
        
        # Distribuir en esfera
        phi = math.pi * (3 - math.sqrt(5))  # Ángulo dorado
        
        for i in range(num_nodes):
            y = 1 - (i / (num_nodes - 1)) * 2  # y va de 1 a -1
            radius = math.sqrt(1 - y * y)  # radio en x-z
            
            theta = phi * i  # ángulo áureo
            
            x = math.cos(theta) * radius
            z = math.sin(theta) * radius
            
            # Escalar por distancia máxima
            scale = self.ar_config["max_distance"] * 0.8
            positions.append((x * scale, y * scale, z * scale))
        
        return positions
    
    def _get_node_color(self, node_type: str) -> Tuple[int, int, int]:
        """Obtiene color para tipo de nodo"""
        colors = {
            "influencer": (255, 68, 68),    # Rojo
            "connector": (245, 158, 11),    # Naranja
            "regular": (99, 102, 241),      # Azul
            "community": (16, 185, 129),    # Verde
            "default": (107, 114, 128)      # Gris
        }
        return colors.get(node_type, colors["default"])
    
    def _get_edge_color(self, strength: float) -> Tuple[int, int, int]:
        """Obtiene color para conexión basado en fuerza"""
        # Interpolar entre azul débil y azul fuerte
        base_color = (99, 102, 241)  # Azul base
        intensity = int(100 + strength * 155)  # 100-255
        return (base_color[0], base_color[1], intensity)
    
    def update_camera(self, position: Tuple[float, float, float], 
                     rotation: Tuple[float, float, float]):
        """
        Actualiza posición y rotación de la cámara
        """
        if not self.enabled:
            return
        
        self.camera_position = position
        self.camera_rotation = rotation
        
        # Actualizar visibilidad de elementos basado en distancia
        self._update_visibility()
    
    def _update_visibility(self):
        """Actualiza visibilidad de elementos basado en distancia de cámara"""
        for node in self.nodes.values():
            distance = self._calculate_distance(self.camera_position, node.position)
            
            if distance > self.ar_config["max_distance"]:
                node.visible = False
            elif distance > self.ar_config["fade_distance"]:
                # Fade out gradual
                fade_factor = 1.0 - (distance - self.ar_config["fade_distance"]) / (
                    self.ar_config["max_distance"] - self.ar_config["fade_distance"]
                )
                node.visible = fade_factor > 0.1
            else:
                node.visible = True
        
        # Actualizar visibilidad de conexiones
        for edge in self.edges.values():
            from_node = self.nodes.get(edge.from_node)
            to_node = self.nodes.get(edge.to_node)
            
            if from_node and to_node:
                edge.visible = from_node.visible and to_node.visible
    
    def _calculate_distance(self, pos1: Tuple[float, float, float], 
                          pos2: Tuple[float, float, float]) -> float:
        """Calcula distancia entre dos puntos 3D"""
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(pos1, pos2)))
    
    def handle_gesture(self, gesture_type: str, position: Tuple[float, float, float]) -> Dict[str, Any]:
        """
        Maneja gestos del usuario en AR
        """
        if not self.enabled:
            return self._get_mock_gesture_response(gesture_type)
        
        try:
            response = {
                "gesture_type": gesture_type,
                "position": position,
                "action": "none",
                "data": None
            }
            
            if gesture_type == "tap":
                # Buscar nodo cercano
                nearest_node = self._find_nearest_node(position)
                if nearest_node:
                    response["action"] = "select_node"
                    response["data"] = self._get_node_info(nearest_node)
                    self._select_node(nearest_node.id)
            
            elif gesture_type == "swipe":
                # Rotar vista
                response["action"] = "rotate_view"
                response["data"] = {"direction": self._detect_swipe_direction(position)}
            
            elif gesture_type == "pinch":
                # Zoom
                response["action"] = "zoom"
                response["data"] = {"scale": self._detect_pinch_scale(position)}
            
            elif gesture_type == "hold":
                # Mostrar menú contextual
                response["action"] = "show_context_menu"
                response["data"] = {"position": position}
            
            return response
            
        except Exception as e:
            logger.error(f"Error handling gesture: {e}")
            return {"gesture_type": gesture_type, "action": "error", "data": str(e)}
    
    def _find_nearest_node(self, position: Tuple[float, float, float]) -> Optional[ARNode]:
        """Encuentra el nodo más cercano a una posición"""
        nearest_node = None
        min_distance = float('inf')
        
        for node in self.nodes.values():
            if not node.visible:
                continue
            
            distance = self._calculate_distance(position, node.position)
            if distance < min_distance and distance < self.ar_config["interaction_distance"]:
                min_distance = distance
                nearest_node = node
        
        return nearest_node
    
    def _get_node_info(self, node: ARNode) -> Dict[str, Any]:
        """Obtiene información detallada de un nodo"""
        return {
            "id": node.id,
            "name": node.name,
            "type": node.type,
            "position": node.position,
            "data": node.data,
            "connections": self._get_node_connections(node.id)
        }
    
    def _get_node_connections(self, node_id: str) -> List[Dict[str, Any]]:
        """Obtiene conexiones de un nodo"""
        connections = []
        for edge in self.edges.values():
            if edge.from_node == node_id:
                to_node = self.nodes.get(edge.to_node)
                if to_node:
                    connections.append({
                        "node_id": edge.to_node,
                        "node_name": to_node.name,
                        "strength": edge.strength
                    })
            elif edge.to_node == node_id:
                from_node = self.nodes.get(edge.from_node)
                if from_node:
                    connections.append({
                        "node_id": edge.from_node,
                        "node_name": from_node.name,
                        "strength": edge.strength
                    })
        return connections
    
    def _select_node(self, node_id: str):
        """Selecciona un nodo"""
        # Deseleccionar todos los nodos
        for node in self.nodes.values():
            node.selected = False
        
        # Seleccionar nodo específico
        if node_id in self.nodes:
            self.nodes[node_id].selected = True
            
            # Crear overlay de información
            self._create_node_overlay(node_id)
    
    def _create_node_overlay(self, node_id: str):
        """Crea overlay de información para nodo seleccionado"""
        node = self.nodes.get(node_id)
        if not node:
            return
        
        # Crear contenido del overlay
        content = f"""
        <div class="ar-node-info">
            <h3>{node.name}</h3>
            <p><strong>Tipo:</strong> {node.type}</p>
            <p><strong>Influencia:</strong> {node.data.get('influence_score', 0):.2f}</p>
            <p><strong>Conexiones:</strong> {len(self._get_node_connections(node_id))}</p>
        </div>
        """
        
        overlay = AROverlay(
            id=f"node_info_{node_id}",
            content=content,
            position=node.position,
            type="info",
            duration=10.0
        )
        
        self.overlays[overlay.id] = overlay
    
    def _detect_swipe_direction(self, position: Tuple[float, float, float]) -> str:
        """Detecta dirección del swipe"""
        # Implementación simplificada
        return "right"  # Por defecto
    
    def _detect_pinch_scale(self, position: Tuple[float, float, float]) -> float:
        """Detecta escala del pinch"""
        # Implementación simplificada
        return 1.0  # Por defecto
    
    def add_ar_overlay(self, content: str, position: Tuple[float, float, float], 
                      overlay_type: str = "info", duration: float = 5.0) -> str:
        """
        Añade overlay de información en AR
        """
        if not self.enabled:
            return "mock_overlay_id"
        
        overlay_id = f"overlay_{len(self.overlays)}"
        overlay = AROverlay(
            id=overlay_id,
            content=content,
            position=position,
            type=overlay_type,
            duration=duration
        )
        
        self.overlays[overlay_id] = overlay
        return overlay_id
    
    def remove_ar_overlay(self, overlay_id: str) -> bool:
        """
        Remueve overlay de AR
        """
        if not self.enabled:
            return True
        
        if overlay_id in self.overlays:
            del self.overlays[overlay_id]
            return True
        return False
    
    def get_ar_scene_data(self) -> Dict[str, Any]:
        """
        Obtiene datos de la escena AR para renderizado
        """
        if not self.enabled:
            return self._get_mock_scene_data()
        
        try:
            # Filtrar elementos visibles
            visible_nodes = [
                {
                    "id": node.id,
                    "name": node.name,
                    "position": node.position,
                    "size": node.size,
                    "color": node.color,
                    "type": node.type,
                    "selected": node.selected
                }
                for node in self.nodes.values()
                if node.visible
            ]
            
            visible_edges = [
                {
                    "id": edge.id,
                    "from_position": self.nodes.get(edge.from_node, ARNode("", "", (0,0,0), 0, (0,0,0), "")).position,
                    "to_position": self.nodes.get(edge.to_node, ARNode("", "", (0,0,0), 0, (0,0,0), "")).position,
                    "color": edge.color,
                    "strength": edge.strength,
                    "animated": edge.animated
                }
                for edge in self.edges.values()
                if edge.visible
            ]
            
            active_overlays = [
                {
                    "id": overlay.id,
                    "content": overlay.content,
                    "position": overlay.position,
                    "type": overlay.type,
                    "age": (datetime.now() - overlay.created_at).total_seconds()
                }
                for overlay in self.overlays.values()
                if (datetime.now() - overlay.created_at).total_seconds() < overlay.duration
            ]
            
            return {
                "camera": {
                    "position": self.camera_position,
                    "rotation": self.camera_rotation
                },
                "nodes": visible_nodes,
                "edges": visible_edges,
                "overlays": active_overlays,
                "interaction_mode": self.interaction_mode,
                "scale_factor": self.scale_factor,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting AR scene data: {e}")
            return self._get_mock_scene_data()
    
    def animate_network(self, animation_type: str = "pulse") -> bool:
        """
        Anima la red en AR
        """
        if not self.enabled:
            return True
        
        try:
            if animation_type == "pulse":
                # Animación de pulso para nodos
                for node in self.nodes.values():
                    # Simular animación de pulso
                    pass
            
            elif animation_type == "flow":
                # Animación de flujo para conexiones
                for edge in self.edges.values():
                    edge.animated = True
            
            elif animation_type == "highlight":
                # Resaltar nodos importantes
                for node in self.nodes.values():
                    if node.data.get("influence_score", 0) > 0.8:
                        node.selected = True
            
            return True
            
        except Exception as e:
            logger.error(f"Error animating network: {e}")
            return False
    
    def export_ar_scene(self, format: str = "json") -> str:
        """
        Exporta escena AR
        """
        if not self.enabled:
            return "mock_export_data"
        
        try:
            scene_data = self.get_ar_scene_data()
            
            if format == "json":
                return json.dumps(scene_data, indent=2)
            elif format == "gltf":
                # Convertir a formato GLTF para 3D
                return self._convert_to_gltf(scene_data)
            else:
                return json.dumps(scene_data, indent=2)
                
        except Exception as e:
            logger.error(f"Error exporting AR scene: {e}")
            return "error"
    
    def _convert_to_gltf(self, scene_data: Dict[str, Any]) -> str:
        """Convierte datos de escena a formato GLTF"""
        # Implementación simplificada
        return json.dumps({
            "asset": {"version": "2.0"},
            "scene": 0,
            "scenes": [{"nodes": []}],
            "nodes": [],
            "meshes": [],
            "materials": []
        })
    
    def _get_mock_load_result(self) -> bool:
        """Resultado simulado de carga"""
        return True
    
    def _get_mock_gesture_response(self, gesture_type: str) -> Dict[str, Any]:
        """Respuesta simulada de gesto"""
        return {
            "gesture_type": gesture_type,
            "action": "mock_action",
            "data": {"message": "AR viewer disabled"}
        }
    
    def _get_mock_scene_data(self) -> Dict[str, Any]:
        """Datos de escena simulados"""
        return {
            "camera": {
                "position": (0, 0, 0),
                "rotation": (0, 0, 0)
            },
            "nodes": [
                {
                    "id": "mock_node",
                    "name": "Mock Node",
                    "position": (0, 0, 0),
                    "size": 0.2,
                    "color": (99, 102, 241),
                    "type": "regular",
                    "selected": False
                }
            ],
            "edges": [],
            "overlays": [],
            "interaction_mode": "view",
            "scale_factor": 1.0,
            "timestamp": datetime.now().isoformat()
        }


# Instancia global del visualizador AR
ar_network_viewer = ARNetworkViewer() 