"""
Motor de Workflows Inteligente con Auto-Optimización
Sistema que aprende y mejora workflows automáticamente
"""

import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


@dataclass
class WorkflowNode:
    """Nodo de workflow con capacidades de aprendizaje"""
    id: str
    type: str  # 'action', 'decision', 'parallel', 'loop', 'ai_decision'
    name: str
    config: Dict[str, Any]
    performance_metrics: Dict[str, float]
    optimization_history: List[Dict]
    ml_model: Optional[Any] = None


class IntelligentWorkflowEngine:
    """Motor de workflows con IA que se auto-optimiza"""
    
    def __init__(self):
        self.workflows = {}
        self.execution_history = defaultdict(list)
        self.performance_cache = {}
        self.optimization_models = {}
        self.real_time_metrics = defaultdict(dict)
        
    async def create_adaptive_workflow(self, name: str, 
                                     initial_config: Dict) -> str:
        """Crea un workflow que se adapta y mejora con el tiempo"""
        
        workflow_id = f"wf_{name}_{datetime.now().timestamp()}"
        
        # Analizar configuración inicial
        optimized_config = await self._optimize_initial_config(initial_config)
        
        # Construir grafo de workflow
        workflow_graph = self._build_workflow_graph(optimized_config)
        
        # Añadir nodos de IA para decisiones inteligentes
        enhanced_graph = self._enhance_with_ai_nodes(workflow_graph)
        
        # Configurar monitoreo y optimización continua
        self._setup_continuous_optimization(workflow_id, enhanced_graph)
        
        self.workflows[workflow_id] = {
            'name': name,
            'graph': enhanced_graph,
            'config': optimized_config,
            'created_at': datetime.now(),
            'optimization_enabled': True,
            'performance_baseline': None
        }
        
        return workflow_id
    
    async def execute_intelligent_workflow(self, workflow_id: str,
                                         context: Dict) -> Dict[str, Any]:
        """Ejecuta workflow con decisiones inteligentes en tiempo real"""
        
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow = self.workflows[workflow_id]
        execution_id = f"exec_{datetime.now().timestamp()}"
        
        # Contexto de ejecución enriquecido
        execution_context = {
            'workflow_id': workflow_id,
            'execution_id': execution_id,
            'start_time': datetime.now(),
            'initial_context': context,
            'decisions_made': [],
            'performance_metrics': {},
            'ai_insights': []
        }
        
        try:
            # Predecir ruta óptima basada en contexto
            optimal_path = await self._predict_optimal_path(workflow, context)
            
            # Ejecutar workflow con monitoreo en tiempo real
            result = await self._execute_with_monitoring(
                workflow['graph'],
                execution_context,
                optimal_path
            )
            
            # Analizar rendimiento y aprender
            await self._analyze_and_learn(workflow_id, execution_context, result)
            
            # Auto-optimizar si es necesario
            if self._should_optimize(workflow_id):
                await self._auto_optimize_workflow(workflow_id)
            
            return {
                'status': 'completed',
                'result': result,
                'execution_time': (datetime.now() - execution_context['start_time']).total_seconds(),
                'optimizations_applied': execution_context.get('optimizations', []),
                'ai_decisions': execution_context['decisions_made'],
                'performance_improvement': self._calculate_improvement(workflow_id)
            }
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            await self._handle_failure(workflow_id, execution_context, e)
            raise
    
    async def _execute_with_monitoring(self, graph: Dict, 
                                     context: Dict,
                                     optimal_path: List[str]) -> Any:
        """Ejecuta workflow con monitoreo y decisiones en tiempo real"""
        
        current_node_id = 'start'
        result = None
        path_index = 0
        
        while current_node_id != 'end':
            node = graph['nodes'][current_node_id]
            
            # Registrar métricas de nodo
            node_start = datetime.now()
            
            # Ejecutar según tipo de nodo
            if node.type == 'action':
                result = await self._execute_action_node(node, context)
                
            elif node.type == 'ai_decision':
                # Decisión inteligente basada en ML
                decision = await self._make_ai_decision(node, context, result)
                context['decisions_made'].append({
                    'node': node.id,
                    'decision': decision,
                    'confidence': decision.get('confidence', 0),
                    'reasoning': decision.get('reasoning', '')
                })
                current_node_id = decision['next_node']
                
            elif node.type == 'parallel':
                # Ejecutar ramas en paralelo
                results = await self._execute_parallel_branches(node, context)
                result = self._merge_parallel_results(results)
                
            elif node.type == 'loop':
                # Loop inteligente con condición de salida dinámica
                result = await self._execute_intelligent_loop(node, context)
            
            # Registrar rendimiento del nodo
            node_duration = (datetime.now() - node_start).total_seconds()
            self._record_node_performance(node.id, node_duration, result)
            
            # Siguiente nodo (si no es decisión de IA)
            if node.type != 'ai_decision':
                if path_index < len(optimal_path) - 1:
                    current_node_id = optimal_path[path_index + 1]
                    path_index += 1
                else:
                    current_node_id = self._get_next_node(graph, current_node_id)
        
        return result
    
    async def _make_ai_decision(self, node: WorkflowNode, 
                              context: Dict, 
                              current_result: Any) -> Dict:
        """Toma decisión inteligente usando ML"""
        
        # Preparar features para el modelo
        features = self._extract_decision_features(context, current_result)
        
        # Obtener o crear modelo para este nodo
        if node.id not in self.optimization_models:
            self.optimization_models[node.id] = self._create_decision_model(node)
        
        model = self.optimization_models[node.id]
        
        # Predecir mejor camino
        prediction = model.predict(features)
        confidence = model.predict_proba(features).max()
        
        # Obtener explicación de la decisión
        reasoning = self._explain_decision(model, features, prediction)
        
        # Mapear predicción a siguiente nodo
        next_node = node.config['branches'][int(prediction)]
        
        return {
            'next_node': next_node,
            'confidence': float(confidence),
            'reasoning': reasoning,
            'features_considered': features
        }
    
    async def _auto_optimize_workflow(self, workflow_id: str):
        """Auto-optimiza el workflow basado en aprendizaje"""
        
        workflow = self.workflows[workflow_id]
        history = self.execution_history[workflow_id]
        
        # Analizar patrones en historial
        patterns = self._analyze_execution_patterns(history)
        
        # Identificar cuellos de botella
        bottlenecks = self._identify_bottlenecks(workflow['graph'], history)
        
        # Generar optimizaciones
        optimizations = []
        
        # 1. Optimizar nodos lentos
        for bottleneck in bottlenecks:
            optimization = self._generate_node_optimization(bottleneck, patterns)
            if optimization:
                optimizations.append(optimization)
        
        # 2. Optimizar rutas de decisión
        decision_optimizations = self._optimize_decision_paths(workflow['graph'], patterns)
        optimizations.extend(decision_optimizations)
        
        # 3. Añadir paralelización donde sea posible
        parallel_opportunities = self._find_parallelization_opportunities(workflow['graph'])
        for opportunity in parallel_opportunities:
            optimizations.append({
                'type': 'parallelize',
                'nodes': opportunity['nodes'],
                'expected_improvement': opportunity['improvement']
            })
        
        # Aplicar optimizaciones
        for optimization in optimizations:
            await self._apply_optimization(workflow_id, optimization)
        
        # Actualizar timestamp de optimización
        workflow['last_optimized'] = datetime.now()
        workflow['optimizations_applied'] = len(optimizations)
        
        logger.info(f"Applied {len(optimizations)} optimizations to workflow {workflow_id}")
    
    def _create_decision_model(self, node: WorkflowNode):
        """Crea modelo ML para decisiones de nodo"""
        # Simplificado para el ejemplo - en producción usaría sklearn/tensorflow
        class SimpleDecisionModel:
            def __init__(self):
                self.history = []
                
            def predict(self, features):
                # Lógica simple basada en reglas
                if features.get('load', 0) > 0.8:
                    return 1  # Ruta alternativa para alta carga
                return 0  # Ruta principal
                
            def predict_proba(self, features):
                import numpy as np
                # Simulación de probabilidades
                if features.get('load', 0) > 0.8:
                    return np.array([[0.2, 0.8]])
                return np.array([[0.8, 0.2]])
                
            def fit(self, X, y):
                self.history.extend(zip(X, y))
        
        return SimpleDecisionModel()
    
    def _should_optimize(self, workflow_id: str) -> bool:
        """Determina si el workflow necesita optimización"""
        
        workflow = self.workflows[workflow_id]
        history = self.execution_history[workflow_id]
        
        if len(history) < 10:
            return False  # Necesita más datos
        
        # Verificar degradación de rendimiento
        recent_performance = [h['performance_metrics'] for h in history[-5:]]
        older_performance = [h['performance_metrics'] for h in history[-10:-5]]
        
        recent_avg = sum(p.get('duration', 0) for p in recent_performance) / 5
        older_avg = sum(p.get('duration', 0) for p in older_performance) / 5
        
        # Optimizar si el rendimiento se degradó más del 20%
        return recent_avg > older_avg * 1.2
    
    async def generate_workflow_insights(self, workflow_id: str) -> Dict:
        """Genera insights inteligentes sobre el workflow"""
        
        workflow = self.workflows[workflow_id]
        history = self.execution_history[workflow_id]
        
        insights = {
            'performance_trends': self._analyze_performance_trends(history),
            'decision_patterns': self._analyze_decision_patterns(history),
            'optimization_opportunities': self._identify_optimization_opportunities(workflow),
            'predicted_improvements': self._predict_improvements(workflow),
            'anomalies': self._detect_anomalies(history),
            'recommendations': self._generate_recommendations(workflow, history)
        }
        
        return insights