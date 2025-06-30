"""
Servicio para generar y gestionar Gantt charts interactivos de ejecución de campañas.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q, Count, Avg
from django.core.cache import cache

from app.ats.publish.models import (
    MarketingCampaign, CampaignExecutionPhase, CampaignTask,
    CampaignMilestone, CampaignGanttView
)

logger = logging.getLogger(__name__)

class GanttChartService:
    """
    Servicio para generar y gestionar Gantt charts de ejecución de campañas.
    """
    
    def __init__(self):
        self.cache_timeout = 1800  # 30 minutos
    
    async def create_campaign_gantt(self, campaign_id: int) -> Dict[str, Any]:
        """
        Crea un Gantt chart completo para una campaña específica.
        """
        try:
            campaign = await MarketingCampaign.objects.aget(id=campaign_id)
            
            # Generar fases de ejecución
            phases = await self._generate_execution_phases(campaign)
            
            # Generar tareas para cada fase
            tasks = await self._generate_phase_tasks(phases)
            
            # Generar hitos
            milestones = await self._generate_campaign_milestones(campaign)
            
            # Crear datos del Gantt
            gantt_data = await self._build_gantt_data(phases, tasks, milestones)
            
            return {
                'success': True,
                'campaign_name': campaign.name,
                'gantt_data': gantt_data,
                'summary': await self._generate_gantt_summary(phases, tasks, milestones)
            }
            
        except Exception as e:
            logger.error(f"Error creando Gantt chart para campaña {campaign_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_gantt_view(self, view_id: int) -> Dict[str, Any]:
        """
        Obtiene una vista específica del Gantt chart.
        """
        try:
            gantt_view = await CampaignGanttView.objects.aget(id=view_id)
            gantt_data = gantt_view.get_gantt_data()
            
            return {
                'success': True,
                'view_name': gantt_view.name,
                'view_type': gantt_view.view_type,
                'gantt_data': gantt_data,
                'filters': gantt_view.filters,
                'color_scheme': gantt_view.color_scheme
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo vista Gantt {view_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def update_task_progress(self, task_id: int, progress: float, status: str = None) -> Dict[str, Any]:
        """
        Actualiza el progreso de una tarea específica.
        """
        try:
            task = await CampaignTask.objects.aget(id=task_id)
            
            # Actualizar progreso
            task.progress_percentage = min(progress, 100)
            
            if status:
                task.status = status
            
            # Actualizar fechas si es necesario
            if status == 'in_progress' and not task.actual_start:
                task.actual_start = timezone.now()
            
            if status == 'completed':
                task.actual_end = timezone.now()
                task.progress_percentage = 100
            
            await task.asave()
            
            # Actualizar progreso de la fase
            await self._update_phase_progress(task.phase)
            
            return {
                'success': True,
                'task_updated': True,
                'new_progress': task.progress_percentage,
                'new_status': task.status
            }
            
        except Exception as e:
            logger.error(f"Error actualizando progreso de tarea {task_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_campaign_timeline(self, campaign_id: int) -> Dict[str, Any]:
        """
        Obtiene la línea de tiempo completa de una campaña.
        """
        try:
            cache_key = f"campaign_timeline_{campaign_id}_{timezone.now().date()}"
            cached_data = cache.get(cache_key)
            
            if cached_data:
                return cached_data
            
            campaign = await MarketingCampaign.objects.aget(id=campaign_id)
            
            # Obtener fases
            phases = await CampaignExecutionPhase.objects.filter(
                campaign=campaign
            ).order_by('execution_order').all()
            
            # Obtener hitos
            milestones = await CampaignMilestone.objects.filter(
                campaign=campaign
            ).order_by('target_date').all()
            
            # Construir timeline
            timeline = {
                'campaign_name': campaign.name,
                'start_date': campaign.start_date,
                'end_date': campaign.end_date,
                'phases': [],
                'milestones': [],
                'critical_path': await self._calculate_critical_path(phases)
            }
            
            # Agregar fases al timeline
            for phase in phases:
                phase_data = {
                    'id': phase.id,
                    'name': phase.name,
                    'type': phase.phase_type,
                    'start_date': phase.planned_start,
                    'end_date': phase.planned_end,
                    'status': phase.status,
                    'progress': float(phase.progress_percentage),
                    'is_delayed': phase.is_delayed()
                }
                timeline['phases'].append(phase_data)
            
            # Agregar hitos al timeline
            for milestone in milestones:
                milestone_data = {
                    'id': milestone.id,
                    'name': milestone.name,
                    'type': milestone.milestone_type,
                    'target_date': milestone.target_date,
                    'status': milestone.status,
                    'is_achieved': milestone.is_achieved(),
                    'is_missed': milestone.is_missed()
                }
                timeline['milestones'].append(milestone_data)
            
            cache.set(cache_key, timeline, self.cache_timeout)
            return {
                'success': True,
                'timeline': timeline
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo timeline de campaña {campaign_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def generate_execution_plan(self, campaign_id: int) -> Dict[str, Any]:
        """
        Genera un plan de ejecución detallado para una campaña.
        """
        try:
            campaign = await MarketingCampaign.objects.aget(id=campaign_id)
            
            # Generar plan de ejecución
            execution_plan = await self._create_execution_plan(campaign)
            
            # Aplicar optimizaciones
            optimized_plan = await self._optimize_execution_plan(execution_plan)
            
            return {
                'success': True,
                'campaign_name': campaign.name,
                'execution_plan': optimized_plan,
                'estimated_duration': await self._calculate_estimated_duration(optimized_plan),
                'resource_requirements': await self._calculate_resource_requirements(optimized_plan)
            }
            
        except Exception as e:
            logger.error(f"Error generando plan de ejecución para campaña {campaign_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # ===== MÉTODOS PRIVADOS =====
    
    async def _generate_execution_phases(self, campaign: MarketingCampaign) -> List[CampaignExecutionPhase]:
        """Genera fases de ejecución para una campaña."""
        phases = []
        
        # Definir fases estándar
        standard_phases = [
            {
                'name': 'Planificación y Preparación',
                'description': 'Definir estrategia, objetivos y recursos',
                'phase_type': 'planning',
                'duration_days': 7,
                'execution_order': 1
            },
            {
                'name': 'Creación de Contenido',
                'description': 'Desarrollar contenido y materiales',
                'phase_type': 'preparation',
                'duration_days': 10,
                'execution_order': 2
            },
            {
                'name': 'Lanzamiento de Campaña',
                'description': 'Ejecutar campaña en canales seleccionados',
                'phase_type': 'execution',
                'duration_days': 14,
                'execution_order': 3
            },
            {
                'name': 'Monitoreo y Optimización',
                'description': 'Seguir métricas y optimizar rendimiento',
                'phase_type': 'monitoring',
                'duration_days': 7,
                'execution_order': 4
            },
            {
                'name': 'Análisis y Seguimiento',
                'description': 'Analizar resultados y planificar seguimiento',
                'phase_type': 'analysis',
                'duration_days': 5,
                'execution_order': 5
            }
        ]
        
        current_date = campaign.start_date
        
        for phase_data in standard_phases:
            phase = await CampaignExecutionPhase.objects.acreate(
                campaign=campaign,
                name=phase_data['name'],
                description=phase_data['description'],
                phase_type=phase_data['phase_type'],
                planned_start=current_date,
                planned_end=current_date + timedelta(days=phase_data['duration_days']),
                execution_order=phase_data['execution_order']
            )
            
            phases.append(phase)
            current_date = phase.planned_end
        
        return phases
    
    async def _generate_phase_tasks(self, phases: List[CampaignExecutionPhase]) -> List[CampaignTask]:
        """Genera tareas específicas para cada fase."""
        tasks = []
        
        for phase in phases:
            phase_tasks = await self._get_tasks_for_phase(phase)
            
            for i, task_data in enumerate(phase_tasks):
                task = await CampaignTask.objects.acreate(
                    phase=phase,
                    title=task_data['title'],
                    description=task_data['description'],
                    task_type=task_data['task_type'],
                    priority=task_data['priority'],
                    planned_start=task_data['planned_start'],
                    planned_end=task_data['planned_end'],
                    estimated_hours=task_data['estimated_hours'],
                    task_order=i + 1
                )
                
                tasks.append(task)
        
        return tasks
    
    async def _get_tasks_for_phase(self, phase: CampaignExecutionPhase) -> List[Dict[str, Any]]:
        """Obtiene tareas específicas para una fase."""
        if phase.phase_type == 'planning':
            return [
                {
                    'title': 'Definir Objetivos de Campaña',
                    'description': 'Establecer KPIs y métricas de éxito',
                    'task_type': 'coordination',
                    'priority': 'high',
                    'planned_start': phase.planned_start,
                    'planned_end': phase.planned_start + timedelta(days=2),
                    'estimated_hours': 8
                },
                {
                    'title': 'Identificar Audiencia Objetivo',
                    'description': 'Definir segmentos y criterios de targeting',
                    'task_type': 'analysis',
                    'priority': 'high',
                    'planned_start': phase.planned_start + timedelta(days=1),
                    'planned_end': phase.planned_start + timedelta(days=3),
                    'estimated_hours': 12
                },
                {
                    'title': 'Seleccionar Canales de Distribución',
                    'description': 'Elegir canales más efectivos para la audiencia',
                    'task_type': 'coordination',
                    'priority': 'medium',
                    'planned_start': phase.planned_start + timedelta(days=2),
                    'planned_end': phase.planned_start + timedelta(days=4),
                    'estimated_hours': 6
                }
            ]
        
        elif phase.phase_type == 'preparation':
            return [
                {
                    'title': 'Crear Contenido Principal',
                    'description': 'Desarrollar contenido base de la campaña',
                    'task_type': 'content_creation',
                    'priority': 'high',
                    'planned_start': phase.planned_start,
                    'planned_end': phase.planned_start + timedelta(days=5),
                    'estimated_hours': 20
                },
                {
                    'title': 'Diseñar Materiales Visuales',
                    'description': 'Crear gráficos, imágenes y videos',
                    'task_type': 'design',
                    'priority': 'medium',
                    'planned_start': phase.planned_start + timedelta(days=2),
                    'planned_end': phase.planned_start + timedelta(days=7),
                    'estimated_hours': 16
                },
                {
                    'title': 'Configurar Herramientas de Publicación',
                    'description': 'Preparar plataformas y programar contenido',
                    'task_type': 'scheduling',
                    'priority': 'medium',
                    'planned_start': phase.planned_start + timedelta(days=5),
                    'planned_end': phase.planned_start + timedelta(days=8),
                    'estimated_hours': 10
                }
            ]
        
        elif phase.phase_type == 'execution':
            return [
                {
                    'title': 'Lanzar Campaña en Canales Principales',
                    'description': 'Publicar contenido en canales seleccionados',
                    'task_type': 'publishing',
                    'priority': 'high',
                    'planned_start': phase.planned_start,
                    'planned_end': phase.planned_start + timedelta(days=2),
                    'estimated_hours': 8
                },
                {
                    'title': 'Monitorear Rendimiento Inicial',
                    'description': 'Seguir métricas de engagement y conversión',
                    'task_type': 'monitoring',
                    'priority': 'high',
                    'planned_start': phase.planned_start + timedelta(days=1),
                    'planned_end': phase.planned_start + timedelta(days=14),
                    'estimated_hours': 24
                },
                {
                    'title': 'Gestionar Comentarios y Respuestas',
                    'description': 'Responder comentarios y mensajes',
                    'task_type': 'communication',
                    'priority': 'medium',
                    'planned_start': phase.planned_start + timedelta(days=1),
                    'planned_end': phase.planned_start + timedelta(days=14),
                    'estimated_hours': 16
                }
            ]
        
        elif phase.phase_type == 'monitoring':
            return [
                {
                    'title': 'Analizar Métricas de Rendimiento',
                    'description': 'Revisar KPIs y métricas clave',
                    'task_type': 'analysis',
                    'priority': 'high',
                    'planned_start': phase.planned_start,
                    'planned_end': phase.planned_start + timedelta(days=3),
                    'estimated_hours': 12
                },
                {
                    'title': 'Implementar Optimizaciones',
                    'description': 'Ajustar campaña basado en resultados',
                    'task_type': 'optimization',
                    'priority': 'high',
                    'planned_start': phase.planned_start + timedelta(days=2),
                    'planned_end': phase.planned_start + timedelta(days=6),
                    'estimated_hours': 16
                }
            ]
        
        else:  # analysis phase
            return [
                {
                    'title': 'Compilar Reporte Final',
                    'description': 'Crear reporte completo de resultados',
                    'task_type': 'analysis',
                    'priority': 'high',
                    'planned_start': phase.planned_start,
                    'planned_end': phase.planned_start + timedelta(days=3),
                    'estimated_hours': 12
                },
                {
                    'title': 'Planificar Seguimiento',
                    'description': 'Definir acciones de seguimiento y nurturing',
                    'task_type': 'coordination',
                    'priority': 'medium',
                    'planned_start': phase.planned_start + timedelta(days=2),
                    'planned_end': phase.planned_start + timedelta(days=5),
                    'estimated_hours': 8
                }
            ]
    
    async def _generate_campaign_milestones(self, campaign: MarketingCampaign) -> List[CampaignMilestone]:
        """Genera hitos importantes para la campaña."""
        milestones = []
        
        # Hito de inicio
        kickoff_milestone = await CampaignMilestone.objects.acreate(
            campaign=campaign,
            name='Inicio de Campaña',
            description='Campaña oficialmente iniciada',
            milestone_type='kickoff',
            target_date=campaign.start_date
        )
        milestones.append(kickoff_milestone)
        
        # Hito de contenido listo
        content_ready_milestone = await CampaignMilestone.objects.acreate(
            campaign=campaign,
            name='Contenido Listo',
            description='Todo el contenido de la campaña está preparado',
            milestone_type='content_ready',
            target_date=campaign.start_date + timedelta(days=10)
        )
        milestones.append(content_ready_milestone)
        
        # Hito de lanzamiento
        launch_milestone = await CampaignMilestone.objects.acreate(
            campaign=campaign,
            name='Lanzamiento',
            description='Campaña lanzada en todos los canales',
            milestone_type='launch',
            target_date=campaign.start_date + timedelta(days=12)
        )
        milestones.append(launch_milestone)
        
        # Hito de primeros resultados
        first_results_milestone = await CampaignMilestone.objects.acreate(
            campaign=campaign,
            name='Primeros Resultados',
            description='Primeros resultados de la campaña disponibles',
            milestone_type='first_results',
            target_date=campaign.start_date + timedelta(days=19)
        )
        milestones.append(first_results_milestone)
        
        # Hito de finalización
        completion_milestone = await CampaignMilestone.objects.acreate(
            campaign=campaign,
            name='Finalización',
            description='Campaña completada',
            milestone_type='completion',
            target_date=campaign.end_date
        )
        milestones.append(completion_milestone)
        
        return milestones
    
    async def _build_gantt_data(self, phases: List[CampaignExecutionPhase], 
                               tasks: List[CampaignTask], 
                               milestones: List[CampaignMilestone]) -> Dict[str, Any]:
        """Construye los datos para el Gantt chart."""
        gantt_data = {
            'phases': [],
            'tasks': [],
            'milestones': [],
            'dependencies': []
        }
        
        # Agregar fases
        for phase in phases:
            phase_data = {
                'id': f"phase_{phase.id}",
                'name': phase.name,
                'description': phase.description,
                'start': phase.planned_start.isoformat(),
                'end': phase.planned_end.isoformat(),
                'progress': float(phase.progress_percentage),
                'status': phase.status,
                'type': phase.phase_type
            }
            gantt_data['phases'].append(phase_data)
        
        # Agregar tareas
        for task in tasks:
            task_data = {
                'id': f"task_{task.id}",
                'name': task.title,
                'description': task.description,
                'start': task.planned_start.isoformat(),
                'end': task.planned_end.isoformat(),
                'progress': float(task.progress_percentage),
                'status': task.status,
                'priority': task.priority,
                'phase_id': f"phase_{task.phase.id}",
                'assigned_to': task.assigned_to.username if task.assigned_to else None
            }
            gantt_data['tasks'].append(task_data)
        
        # Agregar hitos
        for milestone in milestones:
            milestone_data = {
                'id': f"milestone_{milestone.id}",
                'name': milestone.name,
                'description': milestone.description,
                'date': milestone.target_date.isoformat(),
                'status': milestone.status,
                'type': milestone.milestone_type
            }
            gantt_data['milestones'].append(milestone_data)
        
        return gantt_data
    
    async def _generate_gantt_summary(self, phases: List[CampaignExecutionPhase], 
                                    tasks: List[CampaignTask], 
                                    milestones: List[CampaignMilestone]) -> Dict[str, Any]:
        """Genera un resumen del Gantt chart."""
        total_phases = len(phases)
        total_tasks = len(tasks)
        total_milestones = len(milestones)
        
        completed_phases = len([p for p in phases if p.status == 'completed'])
        completed_tasks = len([t for t in tasks if t.status == 'completed'])
        achieved_milestones = len([m for m in milestones if m.is_achieved()])
        
        total_hours = sum([float(t.estimated_hours) for t in tasks])
        completed_hours = sum([float(t.actual_hours) for t in tasks if t.actual_hours])
        
        return {
            'total_phases': total_phases,
            'completed_phases': completed_phases,
            'phase_progress': (completed_phases / total_phases * 100) if total_phases > 0 else 0,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'task_progress': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            'total_milestones': total_milestones,
            'achieved_milestones': achieved_milestones,
            'milestone_progress': (achieved_milestones / total_milestones * 100) if total_milestones > 0 else 0,
            'total_hours': total_hours,
            'completed_hours': completed_hours,
            'hours_progress': (completed_hours / total_hours * 100) if total_hours > 0 else 0
        }
    
    async def _update_phase_progress(self, phase: CampaignExecutionPhase):
        """Actualiza el progreso de una fase basado en sus tareas."""
        tasks = await CampaignTask.objects.filter(phase=phase).all()
        
        if not tasks:
            return
        
        total_progress = sum([float(task.progress_percentage) for task in tasks])
        average_progress = total_progress / len(tasks)
        
        phase.progress_percentage = average_progress
        
        # Actualizar estado de la fase
        if average_progress >= 100:
            phase.status = 'completed'
        elif average_progress > 0:
            phase.status = 'in_progress'
        
        await phase.asave()
    
    async def _calculate_critical_path(self, phases: List[CampaignExecutionPhase]) -> List[str]:
        """Calcula la ruta crítica del proyecto."""
        critical_path = []
        
        for phase in phases:
            if phase.status in ['not_started', 'in_progress']:
                critical_path.append(f"phase_{phase.id}")
        
        return critical_path
    
    async def _create_execution_plan(self, campaign: MarketingCampaign) -> Dict[str, Any]:
        """Crea un plan de ejecución detallado."""
        execution_plan = {
            'campaign_name': campaign.name,
            'start_date': campaign.start_date,
            'end_date': campaign.end_date,
            'phases': [],
            'resource_allocation': {},
            'risk_assessment': {}
        }
        
        # Obtener fases existentes
        phases = await CampaignExecutionPhase.objects.filter(campaign=campaign).all()
        
        for phase in phases:
            tasks = await CampaignTask.objects.filter(phase=phase).all()
            
            phase_plan = {
                'phase_name': phase.name,
                'phase_type': phase.phase_type,
                'start_date': phase.planned_start,
                'end_date': phase.planned_end,
                'tasks': [
                    {
                        'task_name': task.title,
                        'task_type': task.task_type,
                        'priority': task.priority,
                        'estimated_hours': float(task.estimated_hours),
                        'assigned_to': task.assigned_to.username if task.assigned_to else None
                    }
                    for task in tasks
                ]
            }
            
            execution_plan['phases'].append(phase_plan)
        
        return execution_plan
    
    async def _optimize_execution_plan(self, execution_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Optimiza el plan de ejecución."""
        # Aquí se aplicarían optimizaciones basadas en AURA
        # Por ahora, retornamos el plan sin cambios
        return execution_plan
    
    async def _calculate_estimated_duration(self, execution_plan: Dict[str, Any]) -> int:
        """Calcula la duración estimada del plan."""
        if not execution_plan.get('phases'):
            return 0
        
        start_date = execution_plan['phases'][0]['start_date']
        end_date = execution_plan['phases'][-1]['end_date']
        
        return (end_date - start_date).days
    
    async def _calculate_resource_requirements(self, execution_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula los requerimientos de recursos."""
        total_hours = 0
        resource_hours = {}
        
        for phase in execution_plan.get('phases', []):
            for task in phase.get('tasks', []):
                hours = task.get('estimated_hours', 0)
                total_hours += hours
                
                assigned_to = task.get('assigned_to')
                if assigned_to:
                    if assigned_to not in resource_hours:
                        resource_hours[assigned_to] = 0
                    resource_hours[assigned_to] += hours
        
        return {
            'total_hours': total_hours,
            'resource_hours': resource_hours,
            'estimated_cost': total_hours * 50  # Costo estimado por hora
        } 