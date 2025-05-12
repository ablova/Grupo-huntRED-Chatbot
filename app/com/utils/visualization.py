import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import List, Dict, Optional
import logging
from app.models import Person, Vacante, BusinessUnit, Application

logger = logging.getLogger(__name__)

class FlowVisualization:
    def __init__(self):
        """
        Inicializa el visualizador de flujos.
        """
        self.processes = {}
        self.states = set()
        self.transitions = {}
        self.metrics = {
            "total_processes": 0,
            "active_processes": 0,
            "completed_processes": 0,
            "average_duration": 0,
            "success_rate": 0
        }

    def add_process(self, process_id: str, business_unit: BusinessUnit, candidate: Person):
        """
        Agrega un proceso al visualizador.
        
        Args:
            process_id: Identificador único del proceso
            business_unit: Unidad de negocio
            candidate: Candidato
        """
        self.processes[process_id] = {
            "business_unit": business_unit,
            "candidate": candidate,
            "states": [],
            "timestamps": [],
            "metrics": {
                "duration": 0,
                "success": False,
                "errors": []
            }
        }
        self.metrics["total_processes"] += 1

    def add_state(self, process_id: str, state: str, timestamp: float):
        """
        Agrega un estado a un proceso.
        
        Args:
            process_id: Identificador del proceso
            state: Nombre del estado
            timestamp: Timestamp del cambio de estado
        """
        if process_id in self.processes:
            self.processes[process_id]["states"].append(state)
            self.processes[process_id]["timestamps"].append(timestamp)
            self.states.add(state)
            self._update_metrics(process_id)

    def add_transition(self, from_state: str, to_state: str, count: int = 1):
        """
        Agrega una transición entre estados.
        
        Args:
            from_state: Estado origen
            to_state: Estado destino
            count: Número de transiciones
        """
        if from_state not in self.transitions:
            self.transitions[from_state] = {}
        if to_state not in self.transitions[from_state]:
            self.transitions[from_state][to_state] = 0
        self.transitions[from_state][to_state] += count

    def _update_metrics(self, process_id: str):
        """
        Actualiza las métricas del proceso.
        
        Args:
            process_id: Identificador del proceso
        """
        process = self.processes[process_id]
        if len(process["states"]) > 0:
            process["metrics"]["duration"] = process["timestamps"][-1] - process["timestamps"][0]
            if process["states"][-1] == "completed":
                process["metrics"]["success"] = True
                self.metrics["completed_processes"] += 1

    def get_metrics(self) -> Dict:
        """
        Obtiene las métricas del visualizador.
        
        Returns:
            Dict: Métricas del visualizador
        """
        if self.metrics["total_processes"] > 0:
            self.metrics["success_rate"] = (self.metrics["completed_processes"] / 
                                          self.metrics["total_processes"] * 100)
        return self.metrics

    def generate_process_flow(self) -> go.Figure:
        """
        Genera un gráfico de flujo de procesos.
        
        Returns:
            go.Figure: Gráfico de flujo
        """
        try:
            nodes = list(self.states)
            edges = []
            for from_state, transitions in self.transitions.items():
                for to_state, count in transitions.items():
                    edges.append((from_state, to_state, count))

            # Crear gráfico de flujo
            fig = go.Figure()

            # Agregar nodos
            for node in nodes:
                fig.add_trace(go.Scatter(
                    x=[nodes.index(node)],
                    y=[0],
                    mode='markers',
                    marker=dict(size=20, color='blue'),
                    text=node,
                    name=node
                ))

            # Agregar bordes
            for edge in edges:
                fig.add_trace(go.Scatter(
                    x=[nodes.index(edge[0]), nodes.index(edge[1])],
                    y=[0, 0],
                    mode='lines',
                    line=dict(width=edge[2] * 2, color='gray'),
                    text=f"{edge[2]} transitions",
                    hoverinfo='text'
                ))

            fig.update_layout(
                title="Proceso de Flujo",
                showlegend=False,
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
            )

            return fig

        except Exception as e:
            logger.error(f"Error generando gráfico de flujo: {str(e)}")
            raise

    def generate_state_distribution(self) -> go.Figure:
        """
        Genera un gráfico de distribución de estados.
        
        Returns:
            go.Figure: Gráfico de distribución
        """
        try:
            state_counts = {}
            for process in self.processes.values():
                if len(process["states"]) > 0:
                    current_state = process["states"][-1]
                    state_counts[current_state] = state_counts.get(current_state, 0) + 1

            fig = go.Figure(data=[go.Pie(
                labels=list(state_counts.keys()),
                values=list(state_counts.values()),
                textinfo='label+percent',
                insidetextorientation='radial'
            )])

            fig.update_layout(
                title="Distribución de Estados",
                showlegend=True
            )

            return fig

        except Exception as e:
            logger.error(f"Error generando distribución de estados: {str(e)}")
            raise

    def generate_duration_histogram(self) -> go.Figure:
        """
        Genera un histograma de duraciones.
        
        Returns:
            go.Figure: Histograma de duraciones
        """
        try:
            durations = []
            for process in self.processes.values():
                if len(process["states"]) > 0:
                    durations.append(process["metrics"]["duration"])

            fig = go.Figure(data=[go.Histogram(
                x=durations,
                nbinsx=20,
                marker_color='blue'
            )])

            fig.update_layout(
                title="Distribución de Duraciones",
                xaxis_title="Duración (segundos)",
                yaxis_title="Número de Procesos"
            )

            return fig

        except Exception as e:
            logger.error(f"Error generando histograma de duraciones: {str(e)}")
            raise

    def generate_business_unit_dashboard(self, business_units: List[BusinessUnit]) -> go.Figure:
        """
        Genera un dashboard por unidad de negocio.
        
        Args:
            business_units: Lista de unidades de negocio
            
        Returns:
            go.Figure: Dashboard
        """
        try:
            bu_metrics = []
            for bu in business_units:
                bu_processes = [p for p in self.processes.values() 
                              if p["business_unit"] == bu]
                bu_metrics.append({
                    "business_unit": bu.name,
                    "total_processes": len(bu_processes),
                    "completed_processes": sum(1 for p in bu_processes 
                                            if p["metrics"]["success"]),
                    "average_duration": (sum(p["metrics"]["duration"] 
                                          for p in bu_processes) / 
                                        len(bu_processes) if bu_processes else 0),
                    "success_rate": (sum(1 for p in bu_processes 
                                        if p["metrics"]["success"]) / 
                                    len(bu_processes) * 100 if bu_processes else 0)
                })

            fig = go.Figure()

            # Agregar métricas
            for metric in ["total_processes", "completed_processes", 
                         "average_duration", "success_rate"]:
                fig.add_trace(go.Bar(
                    x=[m["business_unit"] for m in bu_metrics],
                    y=[m[metric] for m in bu_metrics],
                    name=metric.replace("_", " ").title(),
                    text=[m[metric] for m in bu_metrics],
                    textposition='auto'
                ))

            fig.update_layout(
                title="Dashboard por Unidad de Negocio",
                barmode='group',
                xaxis_title="Unidad de Negocio",
                yaxis_title="Valor",
                showlegend=True
            )

            return fig

        except Exception as e:
            logger.error(f"Error generando dashboard: {str(e)}")
            raise

    def generate_candidate_flow(self, candidate: Person) -> go.Figure:
        """
        Genera un gráfico de flujo para un candidato.
        
        Args:
            candidate: Candidato
            
        Returns:
            go.Figure: Gráfico de flujo
        """
        try:
            candidate_processes = [p for p in self.processes.values() 
                                 if p["candidate"] == candidate]
            
            if not candidate_processes:
                return None

            states = set()
            for process in candidate_processes:
                states.update(process["states"])

            nodes = list(states)
            edges = []
            for process in candidate_processes:
                for i in range(len(process["states"]) - 1):
                    edges.append((process["states"][i], process["states"][i+1]))

            fig = go.Figure()

            # Agregar nodos
            for node in nodes:
                fig.add_trace(go.Scatter(
                    x=[nodes.index(node)],
                    y=[0],
                    mode='markers',
                    marker=dict(size=20, color='blue'),
                    text=node,
                    name=node
                ))

            # Agregar bordes
            for edge in edges:
                fig.add_trace(go.Scatter(
                    x=[nodes.index(edge[0]), nodes.index(edge[1])],
                    y=[0, 0],
                    mode='lines',
                    line=dict(width=2, color='gray'),
                    text="transition",
                    hoverinfo='text'
                ))

            fig.update_layout(
                title=f"Flujo de Proceso para {candidate.nombre}",
                showlegend=False,
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
            )

            return fig

        except Exception as e:
            logger.error(f"Error generando flujo de candidato: {str(e)}")
            raise

    def generate_state_transition_matrix(self) -> go.Figure:
        """
        Genera una matriz de transiciones de estados.
        
        Returns:
            go.Figure: Matriz de transiciones
        """
        try:
            states = list(self.states)
            matrix = np.zeros((len(states), len(states)))

            for from_state, transitions in self.transitions.items():
                for to_state, count in transitions.items():
                    matrix[states.index(from_state)][states.index(to_state)] = count

            fig = go.Figure(data=go.Heatmap(
                z=matrix,
                x=states,
                y=states,
                colorscale='Blues'
            ))

            fig.update_layout(
                title="Matriz de Transiciones de Estados",
                xaxis_title="Estado Destino",
                yaxis_title="Estado Origen"
            )

            return fig

        except Exception as e:
            logger.error(f"Error generando matriz de transiciones: {str(e)}")
            raise

    def generate_business_unit_stats(self, business_unit: BusinessUnit) -> Dict:
        """
        Genera estadísticas para una unidad de negocio.
        
        Args:
            business_unit: Unidad de negocio
            
        Returns:
            Dict: Estadísticas
        """
        try:
            bu_processes = [p for p in self.processes.values() 
                          if p["business_unit"] == business_unit]
            
            if not bu_processes:
                return {
                    "status": "warning",
                    "message": "No se encontraron procesos para esta unidad de negocio"
                }

            stats = {
                "total_processes": len(bu_processes),
                "completed_processes": sum(1 for p in bu_processes 
                                        if p["metrics"]["success"]),
                "average_duration": (sum(p["metrics"]["duration"] 
                                      for p in bu_processes) / 
                                    len(bu_processes) if bu_processes else 0),
                "success_rate": (sum(1 for p in bu_processes 
                                    if p["metrics"]["success"]) / 
                                len(bu_processes) * 100 if bu_processes else 0),
                "current_states": {},
                "state_transitions": {}
            }

            # Contar estados actuales
            for process in bu_processes:
                if len(process["states"]) > 0:
                    current_state = process["states"][-1]
                    stats["current_states"][current_state] = \
                        stats["current_states"].get(current_state, 0) + 1

            # Contar transiciones
            for process in bu_processes:
                for i in range(len(process["states"]) - 1):
                    from_state = process["states"][i]
                    to_state = process["states"][i+1]
                    if from_state not in stats["state_transitions"]:
                        stats["state_transitions"][from_state] = {}
                    if to_state not in stats["state_transitions"][from_state]:
                        stats["state_transitions"][from_state][to_state] = 0
                    stats["state_transitions"][from_state][to_state] += 1

            return {
                "business_unit": business_unit.name,
                "stats": stats,
                "status": "success"
            }

        except Exception as e:
            logger.error(f"Error generando estadísticas: {str(e)}")
            return {
                "status": "error",
                "message": f"Error generando estadísticas: {str(e)}"
            }

    def generate_candidate_stats(self, candidate: Person) -> Dict:
        """
        Genera estadísticas para un candidato.
        
        Args:
            candidate: Candidato
            
        Returns:
            Dict: Estadísticas
        """
        try:
            candidate_processes = [p for p in self.processes.values() 
                                 if p["candidate"] == candidate]
            
            if not candidate_processes:
                return {
                    "status": "warning",
                    "message": "No se encontraron procesos para este candidato"
                }

            stats = {
                "total_processes": len(candidate_processes),
                "completed_processes": sum(1 for p in candidate_processes 
                                        if p["metrics"]["success"]),
                "average_duration": (sum(p["metrics"]["duration"] 
                                      for p in candidate_processes) / 
                                    len(candidate_processes) if candidate_processes else 0),
                "success_rate": (sum(1 for p in candidate_processes 
                                    if p["metrics"]["success"]) / 
                                len(candidate_processes) * 100 if candidate_processes else 0),
                "current_states": {},
                "state_transitions": {}
            }

            # Contar estados actuales
            for process in candidate_processes:
                if len(process["states"]) > 0:
                    current_state = process["states"][-1]
                    stats["current_states"][current_state] = \
                        stats["current_states"].get(current_state, 0) + 1

            # Contar transiciones
            for process in candidate_processes:
                for i in range(len(process["states"]) - 1):
                    from_state = process["states"][i]
                    to_state = process["states"][i+1]
                    if from_state not in stats["state_transitions"]:
                        stats["state_transitions"][from_state] = {}
                    if to_state not in stats["state_transitions"][from_state]:
                        stats["state_transitions"][from_state][to_state] = 0
                    stats["state_transitions"][from_state][to_state] += 1

            return {
                "candidate": candidate.nombre,
                "stats": stats,
                "status": "success"
            }

        except Exception as e:
            logger.error(f"Error generando estadísticas: {str(e)}")
            return {
                "status": "error",
                "message": f"Error generando estadísticas: {str(e)}"
            }

    def generate_system_metrics(self) -> Dict:
        """
        Genera métricas generales del sistema.
        
        Returns:
            Dict: Métricas del sistema
        """
        try:
            stats = {
                "total_processes": self.metrics["total_processes"],
                "active_processes": self.metrics["active_processes"],
                "completed_processes": self.metrics["completed_processes"],
                "average_duration": self.metrics["average_duration"],
                "success_rate": self.metrics["success_rate"],
                "current_states": {},
                "state_transitions": {}
            }

            # Contar estados actuales
            for process in self.processes.values():
                if len(process["states"]) > 0:
                    current_state = process["states"][-1]
                    stats["current_states"][current_state] = \
                        stats["current_states"].get(current_state, 0) + 1

            # Contar transiciones
            for process in self.processes.values():
                for i in range(len(process["states"]) - 1):
                    from_state = process["states"][i]
                    to_state = process["states"][i+1]
                    if from_state not in stats["state_transitions"]:
                        stats["state_transitions"][from_state] = {}
                    if to_state not in stats["state_transitions"][from_state]:
                        stats["state_transitions"][from_state][to_state] = 0
                    stats["state_transitions"][from_state][to_state] += 1

            return {
                "system": "Process Flow",
                "stats": stats,
                "status": "success"
            }

        except Exception as e:
            logger.error(f"Error generando métricas: {str(e)}")
            return {
                "status": "error",
                "message": f"Error generando métricas: {str(e)}"
            }

    def generate_process_timeline(self, process_id: str) -> go.Figure:
        """
        Genera un gráfico de línea temporal para un proceso.
        
        Args:
            process_id: Identificador del proceso
            
        Returns:
            go.Figure: Gráfico de línea temporal
        """
        try:
            process = self.processes.get(process_id)
            if not process:
                return None

            fig = go.Figure()

            # Agregar estados
            for i in range(len(process["states"])):
                fig.add_trace(go.Scatter(
                    x=[process["timestamps"][i]],
                    y=[process["states"][i]],
                    mode='markers',
                    marker=dict(size=10, color='blue'),
                    text=process["states"][i],
                    name=process["states"][i]
                ))

            # Agregar líneas de conexión
            for i in range(len(process["states"]) - 1):
                fig.add_trace(go.Scatter(
                    x=[process["timestamps"][i], process["timestamps"][i+1]],
                    y=[process["states"][i], process["states"][i+1]],
                    mode='lines',
                    line=dict(width=2, color='gray'),
                    text="transition",
                    hoverinfo='text'
                ))

            fig.update_layout(
                title=f"Timeline del Proceso {process_id}",
                xaxis_title="Timestamp",
                yaxis_title="Estado",
                showlegend=False
            )

            return fig

        except Exception as e:
            logger.error(f"Error generando timeline: {str(e)}")
            raise

    def generate_business_unit_timeline(self, business_unit: BusinessUnit) -> go.Figure:
        """
        Genera un gráfico de línea temporal para una unidad de negocio.
        
        Args:
            business_unit: Unidad de negocio
            
        Returns:
            go.Figure: Gráfico de línea temporal
        """
        try:
            bu_processes = [p for p in self.processes.values() 
                          if p["business_unit"] == business_unit]
            
            if not bu_processes:
                return None

            fig = go.Figure()

            # Agregar estados para cada proceso
            for process in bu_processes:
                for i in range(len(process["states"])):
                    fig.add_trace(go.Scatter(
                        x=[process["timestamps"][i]],
                        y=[process["states"][i]],
                        mode='markers',
                        marker=dict(size=10, color='blue'),
                        text=f"Proceso {process["states"][i]}",
                        name=f"Proceso {process["states"][i]}"
                    ))

                # Agregar líneas de conexión
                for i in range(len(process["states"]) - 1):
                    fig.add_trace(go.Scatter(
                        x=[process["timestamps"][i], process["timestamps"][i+1]],
                        y=[process["states"][i], process["states"][i+1]],
                        mode='lines',
                        line=dict(width=2, color='gray'),
                        text="transition",
                        hoverinfo='text'
                    ))

            fig.update_layout(
                title=f"Timeline para {business_unit.name}",
                xaxis_title="Timestamp",
                yaxis_title="Estado",
                showlegend=False
            )

            return fig

        except Exception as e:
            logger.error(f"Error generando timeline: {str(e)}")
            raise

    def generate_candidate_timeline(self, candidate: Person) -> go.Figure:
        """
        Genera un gráfico de línea temporal para un candidato.
        
        Args:
            candidate: Candidato
            
        Returns:
            go.Figure: Gráfico de línea temporal
        """
        try:
            candidate_processes = [p for p in self.processes.values() 
                                 if p["candidate"] == candidate]
            
            if not candidate_processes:
                return None

            fig = go.Figure()

            # Agregar estados para cada proceso
            for process in candidate_processes:
                for i in range(len(process["states"])):
                    fig.add_trace(go.Scatter(
                        x=[process["timestamps"][i]],
                        y=[process["states"][i]],
                        mode='markers',
                        marker=dict(size=10, color='blue'),
                        text=f"Proceso {process["states"][i]}",
                        name=f"Proceso {process["states"][i]}"
                    ))

                # Agregar líneas de conexión
                for i in range(len(process["states"]) - 1):
                    fig.add_trace(go.Scatter(
                        x=[process["timestamps"][i], process["timestamps"][i+1]],
                        y=[process["states"][i], process["states"][i+1]],
                        mode='lines',
                        line=dict(width=2, color='gray'),
                        text="transition",
                        hoverinfo='text'
                    ))

            fig.update_layout(
                title=f"Timeline para {candidate.nombre}",
                xaxis_title="Timestamp",
                yaxis_title="Estado",
                showlegend=False
            )

            return fig

        except Exception as e:
            logger.error(f"Error generando timeline: {str(e)}")
            raise

    def generate_system_timeline(self) -> go.Figure:
        """
        Genera un gráfico de línea temporal para todo el sistema.
        
        Returns:
            go.Figure: Gráfico de línea temporal
        """
        try:
            fig = go.Figure()

            # Agregar estados para cada proceso
            for process in self.processes.values():
                for i in range(len(process["states"])):
                    fig.add_trace(go.Scatter(
                        x=[process["timestamps"][i]],
                        y=[process["states"][i]],
                        mode='markers',
                        marker=dict(size=10, color='blue'),
                        text=f"Proceso {process["states"][i]}",
                        name=f"Proceso {process["states"][i]}"
                    ))

                # Agregar líneas de conexión
                for i in range(len(process["states"]) - 1):
                    fig.add_trace(go.Scatter(
                        x=[process["timestamps"][i], process["timestamps"][i+1]],
                        y=[process["states"][i], process["states"][i+1]],
                        mode='lines',
                        line=dict(width=2, color='gray'),
                        text="transition",
                        hoverinfo='text'
                    ))

            fig.update_layout(
                title="Timeline del Sistema",
                xaxis_title="Timestamp",
                yaxis_title="Estado",
                showlegend=False
            )

            return fig

        except Exception as e:
            logger.error(f"Error generando timeline: {str(e)}")
            raise
