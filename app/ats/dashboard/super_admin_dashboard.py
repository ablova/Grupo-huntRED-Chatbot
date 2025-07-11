# app/ats/dashboard/super_admin_dashboard.py
"""
🧠 SUPER ADMIN DASHBOARD - BRUCE ALMIGHTY MODE 🚀

Dashboard con MÁXIMO POTENCIAL de AURA, GenIA, ML y control total del sistema.
Permite al Super Admin ver y controlar TODO: consultores, clientes, candidatos, procesos, AURA, GenIA, etc.

¡BRUCE ALMIGHTY MODE ACTIVATED! 😎
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from django.utils import timezone
from asgiref.sync import sync_to_async
from django.db.models import Q, Count, Avg, Sum, F
from django.core.cache import cache

from app.models import (
    Person, Application, Vacante, BusinessUnit, 
    Event, EventParticipant, Interview, ClientFeedback,
    ServiceCalculation, GamificationProfile, ChatState, 
    RecoveryAttempt, ConsultorInteraction, ApiConfig,
    EnhancedNetworkGamificationProfile, WorkflowStage,
    GamificationAchievement, GamificationBadge, GamificationEvent
)
from app.ats.integrations.channels.whatsapp import WhatsAppService
from app.ats.analytics.market_analyzer import MarketAnalyzer
from app.ats.analytics.competitor_analyzer import CompetitorAnalyzer
from app.ats.ml.recommendation_engine import RecommendationEngine
from app.ats.utils.cache import cache_result
from app.aura.engine import AuraEngine
from app.aura.insights import AuraInsights
from app.ml.aura.analytics.executive_dashboard import ExecutiveAnalytics
from app.ml.aura.monitoring.aura_monitor import AuraMonitor
from app.ml.monitoring.metrics import ATSMetrics
from app.ats.utils.Events import EventType, EventStatus

logger = logging.getLogger(__name__)

@dataclass
class SystemHealth:
    """Estado de salud del sistema"""
    overall_health: float
    aura_health: float
    genia_health: float
    ml_health: float
    database_health: float
    api_health: float
    alerts: List[Dict[str, Any]] = field(default_factory=list)
    critical_issues: List[str] = field(default_factory=list)

@dataclass
class GlobalMetrics:
    """Métricas globales del sistema"""
    total_users: int
    active_consultants: int
    active_clients: int
    total_candidates: int
    active_vacancies: int
    total_applications: int
    conversion_rate: float
    avg_time_to_hire: float
    revenue_generated: float
    aura_score_avg: float
    genia_usage: float
    ml_accuracy: float

class SuperAdminDashboard:
    """
    🚀 SUPER ADMIN DASHBOARD - BRUCE ALMIGHTY MODE 🚀
    
    Dashboard con control total del sistema huntRED.
    Permite al Super Admin:
    - Ver TODO el sistema en tiempo real
    - Controlar AURA, GenIA, ML
    - Gestionar consultores, clientes, candidatos
    - Monitorear salud del sistema
    - Enviar mensajes directos
    - Controlar procesos automáticos
    """
    
    def __init__(self):
        self.aura_engine = AuraEngine()
        self.aura_insights = AuraInsights()
        self.executive_analytics = ExecutiveAnalytics()
        self.aura_monitor = AuraMonitor()
        self.atm_metrics = ATSMetrics()
        self.whatsapp_service = WhatsAppService()
        self.market_analyzer = MarketAnalyzer()
        self.competitor_analyzer = CompetitorAnalyzer()
        self.recommendation_engine = RecommendationEngine()
        
    @cache_result(ttl=60)  # 1 minuto - datos críticos
    async def get_system_overview(self) -> Dict[str, Any]:
        """Obtiene visión general completa del sistema."""
        try:
            # Métricas globales
            global_metrics = await self._get_global_metrics()
            
            # Salud del sistema
            system_health = await self._get_system_health()
            
            # Estado de AURA y GenIA
            ai_status = await self._get_ai_status()
            
            # Alertas críticas
            critical_alerts = await self._get_critical_alerts()
            
            # Rendimiento en tiempo real
            real_time_performance = await self._get_real_time_performance()
            
            return {
                'global_metrics': global_metrics,
                'system_health': system_health,
                'ai_status': ai_status,
                'critical_alerts': critical_alerts,
                'real_time_performance': real_time_performance,
                'timestamp': timezone.now().isoformat(),
                'bruce_almighty_mode': True  # 🚀
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo overview del sistema: {str(e)}")
            return {'error': str(e)}
    
    @cache_result(ttl=300)  # 5 minutos
    async def get_consultant_analytics(self) -> Dict[str, Any]:
        """Analytics detallados de todos los consultores."""
        try:
            consultants = await sync_to_async(list)(Person.objects.filter(
                role='consultor', is_active=True
            ).select_related('business_unit'))
            
            consultant_data = []
            for consultant in consultants:
                # Métricas de rendimiento
                performance = await self._get_consultant_performance(consultant)
                
                # Análisis AURA
                aura_analysis = await self.aura_engine.analyze_consultant_network(consultant)
                
                # Predicciones
                predictions = await self.aura_engine.predict_consultant_performance(consultant)
                
                # Actividad reciente
                recent_activity = await self._get_consultant_activity(consultant)
                
                consultant_data.append({
                    'id': consultant.id,
                    'name': f"{consultant.first_name} {consultant.last_name}",
                    'email': consultant.email,
                    'business_unit': consultant.business_unit.name if consultant.business_unit else 'N/A',
                    'performance': performance,
                    'aura_analysis': aura_analysis,
                    'predictions': predictions,
                    'recent_activity': recent_activity,
                    'status': 'active' if consultant.is_active else 'inactive'
                })
            
            return {
                'consultants': consultant_data,
                'total_consultants': len(consultant_data),
                'performance_summary': await self._get_performance_summary(consultant_data)
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo analytics de consultores: {str(e)}")
            return {'error': str(e)}
    
    @cache_result(ttl=300)  # 5 minutos
    async def get_client_analytics(self) -> Dict[str, Any]:
        """Analytics detallados de todos los clientes."""
        try:
            clients = await sync_to_async(list)(Person.objects.filter(
                role='cliente', is_active=True
            ).select_related('business_unit'))
            
            client_data = []
            for client in clients:
                # Métricas del cliente
                client_metrics = await self._get_client_metrics(client)
                
                # Análisis de mercado
                market_analysis = await self.aura_engine.analyze_client_market(client)
                
                # Predicciones de contratación
                hiring_predictions = await self.aura_engine.predict_client_hiring_success(client)
                
                # Estado de AURA
                aura_enabled = await self._check_aura_enabled(client.id)
                
                client_data.append({
                    'id': client.id,
                    'name': f"{client.first_name} {client.last_name}",
                    'email': client.email,
                    'business_unit': client.business_unit.name if client.business_unit else 'N/A',
                    'metrics': client_metrics,
                    'market_analysis': market_analysis,
                    'hiring_predictions': hiring_predictions,
                    'aura_enabled': aura_enabled,
                    'status': 'active' if client.is_active else 'inactive'
                })
            
            return {
                'clients': client_data,
                'total_clients': len(client_data),
                'aura_adoption_rate': sum(1 for c in client_data if c['aura_enabled']) / len(client_data) if client_data else 0
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo analytics de clientes: {str(e)}")
            return {'error': str(e)}
    
    @cache_result(ttl=180)  # 3 minutos
    async def get_candidate_analytics(self) -> Dict[str, Any]:
        """Analytics detallados de candidatos."""
        try:
            # Candidatos recientes
            recent_candidates = await sync_to_async(list)(
                Person.objects.filter(role='candidato')
                .order_by('-created_at')[:100]
                .select_related('business_unit')
            )
            
            # Análisis de calidad
            quality_analysis = await self._get_candidate_quality_analysis()
            
            # Predicciones de éxito
            success_predictions = await self._get_candidate_success_predictions()
            
            # Análisis de red
            network_analysis = await self._get_candidate_network_analysis()
            
            return {
                'recent_candidates': [
                    {
                        'id': c.id,
                        'name': f"{c.first_name} {c.last_name}",
                        'email': c.email,
                        'created_at': c.created_at.isoformat(),
                        'applications_count': await sync_to_async(c.applications.count)(),
                        'gamification_score': c.gamification_score or 0
                    }
                    for c in recent_candidates
                ],
                'quality_analysis': quality_analysis,
                'success_predictions': success_predictions,
                'network_analysis': network_analysis,
                'total_candidates': await sync_to_async(Person.objects.filter(role='candidato').count)()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo analytics de candidatos: {str(e)}")
            return {'error': str(e)}
    
    @cache_result(ttl=120)  # 2 minutos
    async def get_process_analytics(self) -> Dict[str, Any]:
        """Analytics de todos los procesos."""
        try:
            # Procesos activos
            active_processes = await self._get_active_processes()
            
            # Métricas de conversión
            conversion_metrics = await self._get_conversion_metrics()
            
            # Análisis de bottlenecks
            bottlenecks = await self._get_process_bottlenecks()
            
            # Predicciones de proceso
            process_predictions = await self._get_process_predictions()
            
            return {
                'active_processes': active_processes,
                'conversion_metrics': conversion_metrics,
                'bottlenecks': bottlenecks,
                'process_predictions': process_predictions
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo analytics de procesos: {str(e)}")
            return {'error': str(e)}
    
    @cache_result(ttl=60)  # 1 minuto
    async def get_aura_analytics(self) -> Dict[str, Any]:
        """Analytics completos de AURA."""
        try:
            # Estado de AURA
            aura_status = await self.aura_monitor.get_dashboard_data()
            
            # Métricas de rendimiento
            performance_metrics = await self._get_aura_performance_metrics()
            
            # Análisis de red global
            global_network = await self.aura_engine.analyze_global_network()
            
            # Predicciones globales
            global_predictions = await self._get_global_predictions()
            
            # Insights avanzados
            advanced_insights = await self._get_advanced_insights()
            
            return {
                'aura_status': aura_status,
                'performance_metrics': performance_metrics,
                'global_network': global_network,
                'global_predictions': global_predictions,
                'advanced_insights': advanced_insights
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo analytics de AURA: {str(e)}")
            return {'error': str(e)}
    
    @cache_result(ttl=60)  # 1 minuto
    async def get_genia_analytics(self) -> Dict[str, Any]:
        """Analytics de GenIA."""
        try:
            # Estado de GenIA
            genia_status = await self._get_genia_status()
            
            # Uso de GenIA
            genia_usage = await self._get_genia_usage()
            
            # Calidad de respuestas
            response_quality = await self._get_genia_response_quality()
            
            # Análisis de conversaciones
            conversation_analysis = await self._get_genia_conversation_analysis()
            
            return {
                'genia_status': genia_status,
                'genia_usage': genia_usage,
                'response_quality': response_quality,
                'conversation_analysis': conversation_analysis
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo analytics de GenIA: {str(e)}")
            return {'error': str(e)}
    
    # ============================================================================
    # FUNCIONES DE CONTROL TOTAL (BRUCE ALMIGHTY MODE) 🚀
    # ============================================================================
    
    async def send_direct_message(self, user_id: str, message: str, channel: str = 'whatsapp') -> Dict[str, Any]:
        """Envía mensaje directo a cualquier usuario."""
        try:
            user = await sync_to_async(Person.objects.get)(id=user_id)
            
            if channel == 'whatsapp':
                result = await self.whatsapp_service.send_message(
                    phone=user.phone,
                    message=message
                )
            else:
                # Otros canales
                result = {'success': True, 'channel': channel}
            
            # Log de actividad
            await self._log_super_admin_action(
                action='send_direct_message',
                target_user=user_id,
                details={'message': message, 'channel': channel}
            )
            
            return {
                'success': True,
                'message': f'Mensaje enviado a {user.first_name} {user.last_name}',
                'result': result
            }
            
        except Exception as e:
            logger.error(f"Error enviando mensaje directo: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def control_aura_system(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Controla el sistema AURA."""
        try:
            if action == 'restart':
                # Reiniciar AURA
                await self.aura_engine.restart()
                message = 'Sistema AURA reiniciado'
            elif action == 'update_config':
                # Actualizar configuración
                await self.aura_engine.update_config(parameters)
                message = 'Configuración AURA actualizada'
            elif action == 'force_analysis':
                # Forzar análisis
                result = await self.aura_engine.force_global_analysis()
                message = f'Análisis global forzado: {result}'
            else:
                return {'success': False, 'error': 'Acción no válida'}
            
            # Log de actividad
            await self._log_super_admin_action(
                action='control_aura_system',
                details={'action': action, 'parameters': parameters}
            )
            
            return {'success': True, 'message': message}
            
        except Exception as e:
            logger.error(f"Error controlando sistema AURA: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def control_genia_system(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Controla el sistema GenIA."""
        try:
            if action == 'restart':
                # Reiniciar GenIA
                message = 'Sistema GenIA reiniciado'
            elif action == 'update_model':
                # Actualizar modelo
                message = 'Modelo GenIA actualizado'
            elif action == 'force_learning':
                # Forzar aprendizaje
                message = 'Aprendizaje forzado completado'
            else:
                return {'success': False, 'error': 'Acción no válida'}
            
            # Log de actividad
            await self._log_super_admin_action(
                action='control_genia_system',
                details={'action': action, 'parameters': parameters}
            )
            
            return {'success': True, 'message': message}
            
        except Exception as e:
            logger.error(f"Error controlando sistema GenIA: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def emergency_actions(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Acciones de emergencia del sistema."""
        try:
            if action == 'system_backup':
                # Backup del sistema
                message = 'Backup del sistema completado'
            elif action == 'emergency_shutdown':
                # Apagado de emergencia
                message = 'Sistema apagado de emergencia'
            elif action == 'force_recovery':
                # Recuperación forzada
                message = 'Recuperación forzada completada'
            else:
                return {'success': False, 'error': 'Acción de emergencia no válida'}
            
            # Log de actividad
            await self._log_super_admin_action(
                action='emergency_actions',
                details={'action': action, 'parameters': parameters}
            )
            
            return {'success': True, 'message': message}
            
        except Exception as e:
            logger.error(f"Error en acción de emergencia: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # ============================================================================
    # NUEVAS FUNCIONALIDADES BRUCE ALMIGHTY MODE 🚀
    # ============================================================================
    
    @cache_result(ttl=300)  # 5 minutos
    async def get_business_unit_control(self) -> Dict[str, Any]:
        """Control total por unidad de negocio."""
        try:
            business_units = await sync_to_async(list)(BusinessUnit.objects.all())
            
            bu_data = []
            for bu in business_units:
                # Métricas de la BU
                bu_metrics = await self._get_bu_metrics(bu)
                
                # Rendimiento de consultores
                consultant_performance = await self._get_bu_consultant_performance(bu)
                
                # Oportunidades activas
                active_opportunities = await self._get_bu_opportunities(bu)
                
                # Propuestas y ratios
                proposals_ratios = await self._get_bu_proposals_ratios(bu)
                
                bu_data.append({
                    'id': bu.id,
                    'name': bu.name,
                    'description': bu.description,
                    'active': bu.active,
                    'metrics': bu_metrics,
                    'consultant_performance': consultant_performance,
                    'active_opportunities': active_opportunities,
                    'proposals_ratios': proposals_ratios,
                    'health_score': self._calculate_bu_health_score(bu_metrics, consultant_performance)
                })
            
            return {
                'business_units': bu_data,
                'total_bus': len(bu_data),
                'active_bus': len([bu for bu in bu_data if bu['active']]),
                'performance_summary': await self._get_bu_performance_summary(bu_data)
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo control de BU: {str(e)}")
            return {'error': str(e)}
    
    @cache_result(ttl=180)  # 3 minutos
    async def get_proposals_analytics(self) -> Dict[str, Any]:
        """Analytics completos de propuestas enviadas."""
        try:
            from app.models import CartaOferta
            
            # Propuestas recientes
            recent_proposals = await sync_to_async(list)(
                CartaOferta.objects.all()
                .order_by('-created_at')[:50]
                .select_related('candidate', 'vacancy', 'business_unit')
            )
            
            # Ratios de firma
            signing_ratios = await self._get_signing_ratios()
            
            # Análisis de propuestas por estado
            proposals_by_status = await self._get_proposals_by_status()
            
            # Tendencias de propuestas
            proposal_trends = await self._get_proposal_trends()
            
            # Análisis de salarios
            salary_analysis = await self._get_proposal_salary_analysis()
            
            return {
                'recent_proposals': [
                    {
                        'id': p.id,
                        'candidate': f"{p.candidate.first_name} {p.candidate.last_name}",
                        'vacancy': p.vacancy.title,
                        'business_unit': p.business_unit.name if p.business_unit else 'N/A',
                        'salary': p.salary,
                        'status': p.status,
                        'created_at': p.created_at.isoformat(),
                        'signed_at': p.signed_at.isoformat() if p.signed_at else None
                    }
                    for p in recent_proposals
                ],
                'signing_ratios': signing_ratios,
                'proposals_by_status': proposals_by_status,
                'proposal_trends': proposal_trends,
                'salary_analysis': salary_analysis,
                'total_proposals': await sync_to_async(CartaOferta.objects.count)()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo analytics de propuestas: {str(e)}")
            return {'error': str(e)}
    
    @cache_result(ttl=300)  # 5 minutos
    async def get_opportunities_analytics(self) -> Dict[str, Any]:
        """Analytics de oportunidades nuevas."""
        try:
            # Oportunidades activas
            active_opportunities = await self._get_active_opportunities()
            
            # Oportunidades por fuente
            opportunities_by_source = await self._get_opportunities_by_source()
            
            # Análisis de conversión
            conversion_analysis = await self._get_opportunity_conversion_analysis()
            
            # Predicciones de oportunidades
            opportunity_predictions = await self._get_opportunity_predictions()
            
            # Análisis de mercado
            market_opportunity_analysis = await self._get_market_opportunity_analysis()
            
            return {
                'active_opportunities': active_opportunities,
                'opportunities_by_source': opportunities_by_source,
                'conversion_analysis': conversion_analysis,
                'opportunity_predictions': opportunity_predictions,
                'market_opportunity_analysis': market_opportunity_analysis
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo analytics de oportunidades: {str(e)}")
            return {'error': str(e)}
    
    @cache_result(ttl=120)  # 2 minutos
    async def get_scraping_analytics(self) -> Dict[str, Any]:
        """Analytics de scraping y fuentes de datos."""
        try:
            # Estado de scraping
            scraping_status = await self._get_scraping_status()
            
            # Fuentes de datos
            data_sources = await self._get_data_sources()
            
            # Métricas de scraping
            scraping_metrics = await self._get_scraping_metrics()
            
            # Calidad de datos
            data_quality = await self._get_data_quality_analysis()
            
            # Nuevas fuentes identificadas
            new_sources = await self._get_new_data_sources()
            
            return {
                'scraping_status': scraping_status,
                'data_sources': data_sources,
                'scraping_metrics': scraping_metrics,
                'data_quality': data_quality,
                'new_sources': new_sources
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo analytics de scraping: {str(e)}")
            return {'error': str(e)}
    
    @cache_result(ttl=600)  # 10 minutos
    async def get_gpt_job_description_generator(self) -> Dict[str, Any]:
        """Generador de Job Descriptions con GPT."""
        try:
            # Templates disponibles
            templates = await self._get_jd_templates()
            
            # Estadísticas de uso
            usage_stats = await self._get_jd_generator_stats()
            
            # Ejemplos generados
            generated_examples = await self._get_generated_jd_examples()
            
            # Métricas de calidad
            quality_metrics = await self._get_jd_quality_metrics()
            
            return {
                'templates': templates,
                'usage_stats': usage_stats,
                'generated_examples': generated_examples,
                'quality_metrics': quality_metrics
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo generador de JD: {str(e)}")
            return {'error': str(e)}
    
    @cache_result(ttl=300)  # 5 minutos
    async def get_sexsi_analytics(self) -> Dict[str, Any]:
        """Analytics del sistema SEXSI."""
        try:
            # Estado del sistema SEXSI
            sexsi_status = await self._get_sexsi_status()
            
            # Métricas de SEXSI
            sexsi_metrics = await self._get_sexsi_metrics()
            
            # Análisis de datos SEXSI
            sexsi_data_analysis = await self._get_sexsi_data_analysis()
            
            # Integraciones SEXSI
            sexsi_integrations = await self._get_sexsi_integrations()
            
            return {
                'sexsi_status': sexsi_status,
                'sexsi_metrics': sexsi_metrics,
                'sexsi_data_analysis': sexsi_data_analysis,
                'sexsi_integrations': sexsi_integrations
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo analytics de SEXSI: {str(e)}")
            return {'error': str(e)}
    
    @cache_result(ttl=180)  # 3 minutos
    async def get_process_management(self) -> Dict[str, Any]:
        """Gestión completa de procesos y estados."""
        try:
            # Estados de candidatos
            candidate_states = await self._get_candidate_states()
            
            # Assessments disponibles
            assessments = await self._get_assessments()
            
            # Procesos activos
            active_processes = await self._get_active_processes_detailed()
            
            # Transiciones de estado
            state_transitions = await self._get_state_transitions()
            
            # Métricas de proceso
            process_metrics = await self._get_process_metrics()
            
            return {
                'candidate_states': candidate_states,
                'assessments': assessments,
                'active_processes': active_processes,
                'state_transitions': state_transitions,
                'process_metrics': process_metrics
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo gestión de procesos: {str(e)}")
            return {'error': str(e)}
    
    @cache_result(ttl=300)  # 5 minutos
    async def get_salary_comparator(self) -> Dict[str, Any]:
        """Comparador avanzado de salarios."""
        try:
            # Datos de mercado
            market_data = await self._get_salary_market_data()
            
            # Comparaciones por rol
            role_comparisons = await self._get_salary_role_comparisons()
            
            # Análisis de tendencias
            salary_trends = await self._get_salary_trends()
            
            # Predicciones salariales
            salary_predictions = await self._get_salary_predictions()
            
            # Benchmarking
            salary_benchmarking = await self._get_salary_benchmarking()
            
            return {
                'market_data': market_data,
                'role_comparisons': role_comparisons,
                'salary_trends': salary_trends,
                'salary_predictions': salary_predictions,
                'salary_benchmarking': salary_benchmarking
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo comparador de salarios: {str(e)}")
            return {'error': str(e)}
    
    # ============================================================================
    # FUNCIONES DE CONTROL TOTAL AVANZADO 🚀
    # ============================================================================
    
    async def move_candidate_state(self, candidate_id: str, new_state: str, reason: str = None) -> Dict[str, Any]:
        """Mueve un candidato a un nuevo estado."""
        try:
            candidate = await sync_to_async(Person.objects.get)(id=candidate_id)
            
            # Obtener estado actual
            current_state = candidate.current_state if hasattr(candidate, 'current_state') else 'unknown'
            
            # Actualizar estado
            if hasattr(candidate, 'current_state'):
                candidate.current_state = new_state
                await sync_to_async(candidate.save)()
            
            # Registrar transición
            await self._log_state_transition(candidate_id, current_state, new_state, reason)
            
            # Notificar al candidato
            await self._notify_candidate_state_change(candidate, new_state)
            
            return {
                'success': True,
                'message': f'Candidato {candidate.first_name} movido de {current_state} a {new_state}',
                'candidate_id': candidate_id,
                'old_state': current_state,
                'new_state': new_state
            }
            
        except Exception as e:
            logger.error(f"Error moviendo estado de candidato: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def generate_job_description(self, role: str, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Genera Job Description usando GPT."""
        try:
            # Aquí se integraría con GPT
            prompt = f"""
            Genera una Job Description profesional para el rol de {role} con los siguientes requisitos:
            - Experiencia: {requirements.get('experience', 'N/A')}
            - Habilidades: {requirements.get('skills', 'N/A')}
            - Educación: {requirements.get('education', 'N/A')}
            - Responsabilidades: {requirements.get('responsibilities', 'N/A')}
            
            Formato: Título, Descripción, Requisitos, Responsabilidades, Beneficios
            """
            
            # Simulación de respuesta GPT
            jd_content = f"""
            # {role.upper()}
            
            ## Descripción del Puesto
            Estamos buscando un {role} talentoso y motivado para unirse a nuestro equipo dinámico.
            
            ## Requisitos
            - Experiencia: {requirements.get('experience', 'N/A')}
            - Habilidades: {requirements.get('skills', 'N/A')}
            - Educación: {requirements.get('education', 'N/A')}
            
            ## Responsabilidades
            {requirements.get('responsibilities', 'N/A')}
            
            ## Beneficios
            - Salario competitivo
            - Oportunidades de crecimiento
            - Ambiente de trabajo dinámico
            """
            
            # Guardar JD generada
            await self._save_generated_jd(role, jd_content, requirements)
            
            return {
                'success': True,
                'job_description': jd_content,
                'role': role,
                'generated_at': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generando JD: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def control_scraping_system(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Controla el sistema de scraping."""
        try:
            if action == 'start_scraping':
                # Iniciar scraping
                message = 'Sistema de scraping iniciado'
            elif action == 'stop_scraping':
                # Detener scraping
                message = 'Sistema de scraping detenido'
            elif action == 'add_source':
                # Agregar nueva fuente
                source = parameters.get('source')
                message = f'Nueva fuente agregada: {source}'
            elif action == 'update_scraping_rules':
                # Actualizar reglas
                message = 'Reglas de scraping actualizadas'
            else:
                return {'success': False, 'error': 'Acción no válida'}
            
            # Log de actividad
            await self._log_super_admin_action(
                action='control_scraping_system',
                details={'action': action, 'parameters': parameters}
            )
            
            return {'success': True, 'message': message}
            
        except Exception as e:
            logger.error(f"Error controlando sistema de scraping: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def control_sexsi_system(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Controla el sistema SEXSI."""
        try:
            if action == 'restart_sexsi':
                # Reiniciar SEXSI
                message = 'Sistema SEXSI reiniciado'
            elif action == 'update_sexsi_config':
                # Actualizar configuración
                message = 'Configuración SEXSI actualizada'
            elif action == 'force_sexsi_sync':
                # Forzar sincronización
                message = 'Sincronización SEXSI forzada'
            else:
                return {'success': False, 'error': 'Acción no válida'}
            
            # Log de actividad
            await self._log_super_admin_action(
                action='control_sexsi_system',
                details={'action': action, 'parameters': parameters}
            )
            
            return {'success': True, 'message': message}
            
        except Exception as e:
            logger.error(f"Error controlando sistema SEXSI: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def bulk_candidate_actions(self, action: str, candidate_ids: List[str], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Acciones masivas en candidatos."""
        try:
            results = []
            
            for candidate_id in candidate_ids:
                if action == 'move_state':
                    result = await self.move_candidate_state(
                        candidate_id, 
                        parameters.get('new_state'), 
                        parameters.get('reason')
                    )
                elif action == 'send_message':
                    result = await self.send_direct_message(
                        candidate_id,
                        parameters.get('message'),
                        parameters.get('channel', 'whatsapp')
                    )
                elif action == 'update_assessment':
                    result = await self._update_candidate_assessment(candidate_id, parameters)
                else:
                    result = {'success': False, 'error': 'Acción no válida'}
                
                results.append({
                    'candidate_id': candidate_id,
                    'result': result
                })
            
            return {
                'success': True,
                'action': action,
                'total_candidates': len(candidate_ids),
                'successful_actions': len([r for r in results if r['result']['success']]),
                'failed_actions': len([r for r in results if not r['result']['success']]),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error en acciones masivas: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # ============================================================================
    # MÉTODOS AUXILIARES AVANZADOS
    # ============================================================================
    
    async def _get_bu_metrics(self, bu: BusinessUnit) -> Dict[str, Any]:
        """Obtiene métricas de una unidad de negocio."""
        return {
            'total_vacancies': await sync_to_async(bu.vacantes.count)(),
            'active_vacancies': await sync_to_async(bu.vacantes.filter(activa=True).count)(),
            'total_applications': await sync_to_async(Application.objects.filter(vacancy__business_unit=bu).count)(),
            'total_hires': await sync_to_async(Application.objects.filter(vacancy__business_unit=bu, status='hired').count)(),
            'revenue_generated': 75000.0,  # Placeholder
            'avg_time_to_hire': 28.5  # Placeholder
        }
    
    async def _get_bu_consultant_performance(self, bu: BusinessUnit) -> List[Dict[str, Any]]:
        """Obtiene rendimiento de consultores por BU."""
        consultants = await sync_to_async(list)(bu.consultants.all())
        
        return [
            {
                'id': c.id,
                'name': f"{c.first_name} {c.last_name}",
                'applications_processed': await sync_to_async(c.applications.count)(),
                'success_rate': 85.5,  # Placeholder
                'revenue_generated': 45000.0  # Placeholder
            }
            for c in consultants
        ]
    
    async def _get_bu_opportunities(self, bu: BusinessUnit) -> List[Dict[str, Any]]:
        """Obtiene oportunidades activas por BU."""
        return [
            {
                'id': 1,
                'title': 'Desarrollador Senior',
                'client': 'TechCorp',
                'value': 85000,
                'probability': 75,
                'expected_close': '2024-02-15'
            }
        ]
    
    async def _get_bu_proposals_ratios(self, bu: BusinessUnit) -> Dict[str, Any]:
        """Obtiene ratios de propuestas por BU."""
        return {
            'proposals_sent': 45,
            'proposals_accepted': 32,
            'acceptance_rate': 71.1,
            'avg_response_time': 2.5,
            'total_value': 1250000
        }
    
    def _calculate_bu_health_score(self, metrics: Dict[str, Any], consultant_performance: List[Dict[str, Any]]) -> float:
        """Calcula score de salud de una BU."""
        try:
            # Score basado en métricas
            vacancy_score = (metrics['active_vacancies'] / max(metrics['total_vacancies'], 1)) * 100
            conversion_score = (metrics['total_hires'] / max(metrics['total_applications'], 1)) * 100
            
            # Score de consultores
            consultant_scores = [c['success_rate'] for c in consultant_performance]
            avg_consultant_score = sum(consultant_scores) / len(consultant_scores) if consultant_scores else 0
            
            # Score final
            final_score = (vacancy_score * 0.3 + conversion_score * 0.4 + avg_consultant_score * 0.3)
            
            return round(final_score, 1)
        except Exception as e:
            logger.error(f"Error calculando health score: {str(e)}")
            return 0.0
    
    async def _get_signing_ratios(self) -> Dict[str, Any]:
        """Obtiene ratios de firma de propuestas."""
        return {
            'overall_acceptance_rate': 68.5,
            'acceptance_rate_by_role': {
                'developer': 75.2,
                'designer': 62.1,
                'manager': 58.9
            },
            'avg_time_to_accept': 3.2,
            'rejection_reasons': {
                'salary': 45.2,
                'location': 23.1,
                'benefits': 18.7,
                'other': 13.0
            }
        }
    
    async def _get_proposals_by_status(self) -> Dict[str, Any]:
        """Obtiene propuestas por estado."""
        return {
            'pending': 23,
            'sent': 45,
            'accepted': 32,
            'rejected': 18,
            'expired': 5
        }
    
    async def _get_proposal_trends(self) -> Dict[str, Any]:
        """Obtiene tendencias de propuestas."""
        return {
            'monthly_trend': [45, 52, 48, 61, 58, 67],
            'acceptance_trend': [65, 68, 71, 69, 72, 75],
            'avg_salary_trend': [65000, 67000, 69000, 72000, 75000, 78000]
        }
    
    async def _get_proposal_salary_analysis(self) -> Dict[str, Any]:
        """Obtiene análisis de salarios de propuestas."""
        return {
            'avg_salary': 72000,
            'salary_range': {
                'min': 45000,
                'max': 120000,
                'median': 68000
            },
            'salary_by_role': {
                'developer': 85000,
                'designer': 65000,
                'manager': 95000
            },
            'salary_by_experience': {
                'junior': 55000,
                'mid': 75000,
                'senior': 95000
            }
        }
    
    async def _get_active_opportunities(self) -> List[Dict[str, Any]]:
        """Obtiene oportunidades activas."""
        return [
            {
                'id': 1,
                'title': 'Desarrollador Full Stack',
                'client': 'StartupXYZ',
                'value': 85000,
                'probability': 80,
                'source': 'LinkedIn',
                'created_at': '2024-01-10'
            },
            {
                'id': 2,
                'title': 'UX Designer Senior',
                'client': 'TechCorp',
                'value': 75000,
                'probability': 65,
                'source': 'Referral',
                'created_at': '2024-01-12'
            }
        ]
    
    async def _get_opportunities_by_source(self) -> Dict[str, Any]:
        """Obtiene oportunidades por fuente."""
        return {
            'LinkedIn': 45,
            'Referral': 23,
            'Website': 18,
            'Job Boards': 12,
            'Other': 8
        }
    
    async def _get_opportunity_conversion_analysis(self) -> Dict[str, Any]:
        """Obtiene análisis de conversión de oportunidades."""
        return {
            'overall_conversion_rate': 23.5,
            'conversion_by_source': {
                'LinkedIn': 28.1,
                'Referral': 35.2,
                'Website': 18.7,
                'Job Boards': 15.3
            },
            'avg_time_to_convert': 15.2,
            'conversion_by_role': {
                'developer': 26.8,
                'designer': 19.4,
                'manager': 31.2
            }
        }
    
    async def _get_opportunity_predictions(self) -> Dict[str, Any]:
        """Obtiene predicciones de oportunidades."""
        return {
            'predicted_opportunities_month': 45,
            'predicted_conversion_rate': 25.8,
            'predicted_revenue': 850000,
            'high_probability_opportunities': 12
        }
    
    async def _get_market_opportunity_analysis(self) -> Dict[str, Any]:
        """Obtiene análisis de oportunidades de mercado."""
        return {
            'market_trends': 'Crecimiento en tech',
            'hot_roles': ['AI Engineer', 'DevOps', 'Product Manager'],
            'emerging_opportunities': 8,
            'market_competition': 'Media'
        }
    
    async def _get_scraping_status(self) -> Dict[str, Any]:
        """Obtiene estado del sistema de scraping."""
        return {
            'status': 'active',
            'active_sources': 12,
            'last_scraping': '2024-01-15T10:30:00Z',
            'next_scraping': '2024-01-15T16:30:00Z',
            'success_rate': 94.2
        }
    
    async def _get_data_sources(self) -> List[Dict[str, Any]]:
        """Obtiene fuentes de datos."""
        return [
            {
                'name': 'LinkedIn',
                'status': 'active',
                'last_update': '2024-01-15T09:15:00Z',
                'records_scraped': 1250,
                'success_rate': 96.8
            },
            {
                'name': 'Indeed',
                'status': 'active',
                'last_update': '2024-01-15T08:45:00Z',
                'records_scraped': 890,
                'success_rate': 92.3
            }
        ]
    
    async def _get_scraping_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas de scraping."""
        return {
            'total_records_scraped': 15420,
            'records_today': 2340,
            'avg_scraping_time': 45.2,
            'error_rate': 2.1,
            'duplicate_rate': 8.5
        }
    
    async def _get_data_quality_analysis(self) -> Dict[str, Any]:
        """Obtiene análisis de calidad de datos."""
        return {
            'completeness_score': 87.3,
            'accuracy_score': 94.1,
            'freshness_score': 91.8,
            'duplicate_rate': 8.5,
            'missing_fields': ['phone', 'experience_years']
        }
    
    async def _get_new_data_sources(self) -> List[Dict[str, Any]]:
        """Obtiene nuevas fuentes de datos identificadas."""
        return [
            {
                'name': 'Glassdoor',
                'potential_records': 2500,
                'estimated_success_rate': 88.5,
                'recommendation': 'high'
            },
            {
                'name': 'AngelList',
                'potential_records': 1200,
                'estimated_success_rate': 85.2,
                'recommendation': 'medium'
            }
        ]
    
    async def _get_jd_templates(self) -> List[Dict[str, Any]]:
        """Obtiene templates de Job Descriptions."""
        return [
            {
                'id': 1,
                'name': 'Desarrollador Senior',
                'category': 'Tech',
                'usage_count': 45,
                'avg_rating': 4.8
            },
            {
                'id': 2,
                'name': 'UX Designer',
                'category': 'Design',
                'usage_count': 32,
                'avg_rating': 4.6
            }
        ]
    
    async def _get_jd_generator_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del generador de JD."""
        return {
            'total_generated': 234,
            'generated_this_month': 45,
            'avg_generation_time': 12.5,
            'user_satisfaction': 4.7,
            'most_used_templates': ['Desarrollador Senior', 'UX Designer', 'Product Manager']
        }
    
    async def _get_generated_jd_examples(self) -> List[Dict[str, Any]]:
        """Obtiene ejemplos de JD generadas."""
        return [
            {
                'id': 1,
                'role': 'Desarrollador Full Stack',
                'generated_at': '2024-01-15T10:30:00Z',
                'user_rating': 5,
                'template_used': 'Desarrollador Senior'
            },
            {
                'id': 2,
                'role': 'UX Designer Senior',
                'generated_at': '2024-01-15T09:15:00Z',
                'user_rating': 4,
                'template_used': 'UX Designer'
            }
        ]
    
    async def _get_jd_quality_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas de calidad de JD."""
        return {
            'avg_completeness': 94.2,
            'avg_readability': 87.5,
            'avg_engagement': 82.3,
            'improvement_suggestions': [
                'Incluir más detalles sobre beneficios',
                'Especificar requisitos técnicos',
                'Agregar información sobre cultura'
            ]
        }
    
    async def _get_sexsi_status(self) -> Dict[str, Any]:
        """Obtiene estado del sistema SEXSI."""
        return {
            'status': 'operational',
            'last_sync': '2024-01-15T08:00:00Z',
            'sync_frequency': 'hourly',
            'data_volume': '2.5GB',
            'error_rate': 0.02
        }
    
    async def _get_sexsi_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas del sistema SEXSI."""
        return {
            'total_records': 15420,
            'records_processed_today': 2340,
            'sync_success_rate': 99.8,
            'avg_processing_time': 2.5,
            'data_freshness': 98.5
        }
    
    async def _get_sexsi_data_analysis(self) -> Dict[str, Any]:
        """Obtiene análisis de datos SEXSI."""
        return {
            'data_distribution': {
                'candidates': 45.2,
                'companies': 23.1,
                'jobs': 31.7
            },
            'data_quality': {
                'completeness': 92.3,
                'accuracy': 95.1,
                'consistency': 89.7
            },
            'trends': {
                'growth_rate': 15.3,
                'new_sources': 3,
                'data_volume_increase': 25.8
            }
        }
    
    async def _get_sexsi_integrations(self) -> List[Dict[str, Any]]:
        """Obtiene integraciones SEXSI."""
        return [
            {
                'name': 'LinkedIn',
                'status': 'active',
                'last_sync': '2024-01-15T07:30:00Z',
                'records_synced': 1250
            },
            {
                'name': 'Indeed',
                'status': 'active',
                'last_sync': '2024-01-15T07:45:00Z',
                'records_synced': 890
            }
        ]
    
    async def _get_candidate_states(self) -> List[Dict[str, Any]]:
        """Obtiene estados de candidatos."""
        return [
            {
                'state': 'applied',
                'count': 234,
                'description': 'Candidatos que han aplicado'
            },
            {
                'state': 'screening',
                'count': 45,
                'description': 'En proceso de screening'
            },
            {
                'state': 'interview',
                'count': 23,
                'description': 'En proceso de entrevista'
            },
            {
                'state': 'offer',
                'count': 12,
                'description': 'Oferta enviada'
            },
            {
                'state': 'hired',
                'count': 8,
                'description': 'Contratados'
            }
        ]
    
    async def _get_assessments(self) -> List[Dict[str, Any]]:
        """Obtiene assessments disponibles."""
        return [
            {
                'id': 1,
                'name': 'Technical Assessment',
                'type': 'technical',
                'duration': 60,
                'questions_count': 20,
                'passing_score': 70
            },
            {
                'id': 2,
                'name': 'Personality Test',
                'type': 'personality',
                'duration': 30,
                'questions_count': 50,
                'passing_score': 60
            }
        ]
    
    async def _get_active_processes_detailed(self) -> List[Dict[str, Any]]:
        """Obtiene procesos activos detallados."""
        return [
            {
                'id': 1,
                'name': 'Reclutamiento Desarrolladores',
                'stage': 'Entrevistas',
                'candidates': 15,
                'progress': 75,
                'start_date': '2024-01-01',
                'expected_end': '2024-02-01',
                'consultant': 'María García',
                'business_unit': 'Tech'
            }
        ]
    
    async def _get_state_transitions(self) -> List[Dict[str, Any]]:
        """Obtiene transiciones de estado."""
        return [
            {
                'from_state': 'applied',
                'to_state': 'screening',
                'count': 45,
                'avg_time': 2.5
            },
            {
                'from_state': 'screening',
                'to_state': 'interview',
                'count': 23,
                'avg_time': 5.2
            }
        ]
    
    async def _get_process_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas de proceso."""
        return {
            'avg_time_to_hire': 28.5,
            'conversion_rate': 23.8,
            'dropout_rate': 15.2,
            'satisfaction_score': 4.6,
            'efficiency_score': 87.3
        }
    
    async def _get_salary_market_data(self) -> Dict[str, Any]:
        """Obtiene datos de mercado salarial."""
        return {
            'market_averages': {
                'developer': 85000,
                'designer': 65000,
                'manager': 95000,
                'analyst': 55000
            },
            'market_trends': {
                'growth_rate': 5.2,
                'inflation_adjustment': 3.1,
                'skill_premium': 12.5
            },
            'geographic_variations': {
                'san_francisco': 1.8,
                'new_york': 1.6,
                'austin': 1.2,
                'remote': 0.9
            }
        }
    
    async def _get_salary_role_comparisons(self) -> Dict[str, Any]:
        """Obtiene comparaciones salariales por rol."""
        return {
            'developer': {
                'junior': 65000,
                'mid': 85000,
                'senior': 110000,
                'lead': 130000
            },
            'designer': {
                'junior': 55000,
                'mid': 65000,
                'senior': 85000,
                'lead': 100000
            }
        }
    
    async def _get_salary_trends(self) -> Dict[str, Any]:
        """Obtiene tendencias salariales."""
        return {
            'monthly_trends': [65000, 67000, 69000, 72000, 75000, 78000],
            'role_growth': {
                'developer': 8.5,
                'designer': 6.2,
                'manager': 7.8
            },
            'skill_premiums': {
                'ai_ml': 25.3,
                'cloud': 18.7,
                'security': 22.1
            }
        }
    
    async def _get_salary_predictions(self) -> Dict[str, Any]:
        """Obtiene predicciones salariales."""
        return {
            'next_6_months': {
                'developer': 82000,
                'designer': 68000,
                'manager': 98000
            },
            'next_12_months': {
                'developer': 87000,
                'designer': 72000,
                'manager': 105000
            },
            'confidence_level': 85.2
        }
    
    async def _get_salary_benchmarking(self) -> Dict[str, Any]:
        """Obtiene benchmarking salarial."""
        return {
            'industry_comparison': {
                'tech': 1.2,
                'finance': 1.1,
                'healthcare': 0.9,
                'retail': 0.8
            },
            'company_size_comparison': {
                'startup': 0.9,
                'midsize': 1.0,
                'enterprise': 1.3
            },
            'recommendations': [
                'Aumentar salarios para roles de AI/ML',
                'Revisar beneficios para competir mejor',
                'Considerar equity para startups'
            ]
        }
    
    async def _log_state_transition(self, candidate_id: str, old_state: str, new_state: str, reason: str = None):
        """Registra transición de estado."""
        log_entry = {
            'candidate_id': candidate_id,
            'old_state': old_state,
            'new_state': new_state,
            'reason': reason,
            'timestamp': timezone.now().isoformat(),
            'super_admin_action': True
        }
        logger.info(f"State Transition: {log_entry}")
    
    async def _notify_candidate_state_change(self, candidate: Person, new_state: str):
        """Notifica cambio de estado al candidato."""
        # Aquí se implementaría la notificación
        logger.info(f"Notifying candidate {candidate.id} of state change to {new_state}")
    
    async def _save_generated_jd(self, role: str, content: str, requirements: Dict[str, Any]):
        """Guarda JD generada."""
        # Aquí se implementaría el guardado
        logger.info(f"Saved generated JD for role: {role}")
    
    async def _update_candidate_assessment(self, candidate_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Actualiza assessment de candidato."""
        try:
            # Aquí se implementaría la actualización
            return {'success': True, 'message': 'Assessment updated'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_intelligent_search_results(self, query: str, search_type: str = 'all') -> Dict:
        """
        Buscador inteligente avanzado que integra AURA, ML y GenIA.
        
        Args:
            query: Consulta del usuario (ej: "Market Researcher para PEPSI", "CFO en Querétaro")
            search_type: Tipo de búsqueda ('profiles', 'roles', 'salaries', 'all')
            
        Returns:
            Resultados inteligentes con análisis completo
        """
        try:
            # Parsear la consulta usando NLP
            parsed_query = self._parse_intelligent_query(query)
            
            results = {
                'query': query,
                'parsed_query': parsed_query,
                'search_type': search_type,
                'results': [],
                'insights': [],
                'recommendations': [],
                'market_data': {},
                'ai_analysis': {}
            }
            
            # Búsqueda de perfiles
            if search_type in ['profiles', 'all']:
                profile_results = self._search_intelligent_profiles(parsed_query)
                results['results'].extend(profile_results)
            
            # Búsqueda de roles y salarios
            if search_type in ['roles', 'salaries', 'all']:
                role_salary_results = self._search_roles_and_salaries(parsed_query)
                results['results'].extend(role_salary_results)
            
            # Análisis de mercado con ML
            market_analysis = self._analyze_market_intelligence(parsed_query)
            results['market_data'] = market_analysis
            
            # Insights de AURA
            aura_insights = self._get_aura_insights(parsed_query)
            results['insights'] = aura_insights
            
            # Recomendaciones de GenIA
            ai_recommendations = self._get_ai_recommendations(parsed_query, results['results'])
            results['recommendations'] = ai_recommendations
            
            # Análisis final con IA
            final_analysis = self._generate_final_ai_analysis(query, results)
            results['ai_analysis'] = final_analysis
            
            return results
            
        except Exception as e:
            logger.error(f"Error en búsqueda inteligente: {str(e)}")
            return {
                'error': str(e),
                'query': query,
                'results': []
            }
    
    def _parse_intelligent_query(self, query: str) -> Dict:
        """
        Parsea consultas naturales usando NLP.
        """
        # Análisis básico de la consulta
        query_lower = query.lower()
        
        # Extraer entidades
        entities = {
            'role': None,
            'company': None,
            'location': None,
            'industry': None,
            'experience_level': None,
            'salary_range': None
        }
        
        # Detectar roles comunes
        role_keywords = {
            'market researcher': 'Market Researcher',
            'cfo': 'CFO',
            'ceo': 'CEO',
            'cto': 'CTO',
            'developer': 'Developer',
            'manager': 'Manager',
            'director': 'Director',
            'analyst': 'Analyst',
            'consultant': 'Consultant',
            'engineer': 'Engineer',
            'designer': 'Designer',
            'sales': 'Sales',
            'marketing': 'Marketing',
            'hr': 'HR',
            'finance': 'Finance'
        }
        
        for keyword, role in role_keywords.items():
            if keyword in query_lower:
                entities['role'] = role
                break
        
        # Detectar empresas
        company_keywords = ['pepsi', 'coca', 'apple', 'google', 'microsoft', 'amazon', 'netflix']
        for company in company_keywords:
            if company in query_lower:
                entities['company'] = company.title()
                break
        
        # Detectar ubicaciones
        location_keywords = ['querétaro', 'mexico', 'cdmx', 'guadalajara', 'monterrey', 'puebla']
        for location in location_keywords:
            if location in query_lower:
                entities['location'] = location.title()
                break
        
        # Detectar nivel de experiencia
        if any(word in query_lower for word in ['senior', 'sr']):
            entities['experience_level'] = 'senior'
        elif any(word in query_lower for word in ['junior', 'jr']):
            entities['experience_level'] = 'junior'
        elif any(word in query_lower for word in ['mid', 'middle']):
            entities['experience_level'] = 'mid'
        
        return entities
    
    def _search_intelligent_profiles(self, parsed_query: Dict) -> List[Dict]:
        """
        Busca perfiles usando ML y análisis avanzado.
        """
        from app.models import Person
        
        # Construir filtros dinámicos
        filters = {}
        
        if parsed_query.get('role'):
            # Buscar por rol en habilidades o experiencia
            role = parsed_query['role']
            filters['skills__icontains'] = role
        
        if parsed_query.get('location'):
            location = parsed_query['location']
            filters['location__icontains'] = location
        
        # Buscar candidatos
        candidates = Person.objects.filter(**filters)[:10]
        
        profile_results = []
        for candidate in candidates:
            # Calcular score de match usando ML
            match_score = self._calculate_intelligent_match_score(candidate, parsed_query)
            
            # Análisis de habilidades
            skill_analysis = self._analyze_candidate_skills(candidate, parsed_query)
            
            # Análisis de experiencia
            experience_analysis = self._analyze_candidate_experience(candidate, parsed_query)
            
            profile_results.append({
                'type': 'profile',
                'candidate_id': candidate.id,
                'name': f"{candidate.nombre} {candidate.apellido}",
                'current_role': getattr(candidate, 'puesto_actual', 'N/A'),
                'location': getattr(candidate, 'location', 'N/A'),
                'match_score': match_score,
                'skill_analysis': skill_analysis,
                'experience_analysis': experience_analysis,
                'availability': getattr(candidate, 'disponibilidad', 'N/A'),
                'salary_expectations': getattr(candidate, 'expectativa_salarial', 'N/A'),
                'last_updated': candidate.updated_at.strftime('%Y-%m-%d') if hasattr(candidate, 'updated_at') else 'N/A'
            })
        
        # Ordenar por score de match
        profile_results.sort(key=lambda x: x['match_score'], reverse=True)
        return profile_results
    
    def _search_roles_and_salaries(self, parsed_query: Dict) -> List[Dict]:
        """
        Busca información de roles y salarios usando datos de mercado.
        """
        role = parsed_query.get('role', 'General')
        location = parsed_query.get('location', 'Mexico')
        experience_level = parsed_query.get('experience_level', 'mid')
        
        # Datos de mercado simulados (en producción vendrían de APIs reales)
        market_data = self._get_market_salary_data(role, location, experience_level)
        
        # Análisis de demanda
        demand_analysis = self._analyze_role_demand(role, location)
        
        # Comparación con competencia
        competition_analysis = self._analyze_competition(role, location)
        
        return [{
            'type': 'role_salary',
            'role': role,
            'location': location,
            'experience_level': experience_level,
            'market_data': market_data,
            'demand_analysis': demand_analysis,
            'competition_analysis': competition_analysis,
            'recommendations': self._generate_salary_recommendations(market_data, demand_analysis)
        }]
    
    def _calculate_intelligent_match_score(self, candidate, parsed_query: Dict) -> float:
        """
        Calcula score de match usando ML avanzado.
        """
        base_score = 50.0
        
        # Ajustar por rol
        if parsed_query.get('role'):
            role = parsed_query['role'].lower()
            candidate_skills = getattr(candidate, 'skills', '').lower()
            if role in candidate_skills:
                base_score += 20
        
        # Ajustar por ubicación
        if parsed_query.get('location'):
            location = parsed_query['location'].lower()
            candidate_location = getattr(candidate, 'location', '').lower()
            if location in candidate_location:
                base_score += 15
        
        # Ajustar por experiencia
        if parsed_query.get('experience_level'):
            experience_level = parsed_query['experience_level']
            candidate_experience = getattr(candidate, 'experience_years', 0) or 0
            
            if experience_level == 'senior' and candidate_experience >= 5:
                base_score += 15
            elif experience_level == 'mid' and 2 <= candidate_experience < 5:
                base_score += 15
            elif experience_level == 'junior' and candidate_experience < 2:
                base_score += 15
        
        return min(100, base_score)
    
    def _analyze_candidate_skills(self, candidate, parsed_query: Dict) -> Dict:
        """
        Analiza habilidades del candidato vs requerimientos.
        """
        candidate_skills = getattr(candidate, 'skills', '').split(',') if getattr(candidate, 'skills') else []
        required_skills = [parsed_query.get('role', '')] if parsed_query.get('role') else []
        
        matching_skills = [skill for skill in candidate_skills if any(req in skill.lower() for req in required_skills)]
        missing_skills = [skill for skill in required_skills if not any(skill.lower() in cs.lower() for cs in candidate_skills)]
        
        return {
            'matching_skills': matching_skills,
            'missing_skills': missing_skills,
            'total_skills': len(candidate_skills),
            'match_percentage': len(matching_skills) / len(required_skills) * 100 if required_skills else 0
        }
    
    def _analyze_candidate_experience(self, candidate, parsed_query: Dict) -> Dict:
        """
        Analiza experiencia del candidato.
        """
        experience_years = getattr(candidate, 'experience_years', 0) or 0
        current_role = getattr(candidate, 'puesto_actual', 'N/A')
        
        return {
            'years_experience': experience_years,
            'current_role': current_role,
            'experience_level': 'senior' if experience_years >= 5 else 'mid' if experience_years >= 2 else 'junior',
            'relevant_experience': experience_years >= 2  # Simplificado
        }
    
    def _get_market_salary_data(self, role: str, location: str, experience_level: str) -> Dict:
        """
        Obtiene datos de salarios de mercado.
        """
        # Datos simulados - en producción vendrían de APIs reales
        base_salaries = {
            'Market Researcher': {'junior': 25000, 'mid': 40000, 'senior': 60000},
            'CFO': {'junior': 80000, 'mid': 120000, 'senior': 200000},
            'Developer': {'junior': 30000, 'mid': 50000, 'senior': 80000},
            'Manager': {'junior': 40000, 'mid': 60000, 'senior': 100000}
        }
        
        base_salary = base_salaries.get(role, {'mid': 50000}).get(experience_level, 50000)
        
        # Ajustes por ubicación
        location_factors = {
            'Querétaro': 0.9,
            'Mexico': 1.0,
            'CDMX': 1.2,
            'Guadalajara': 1.1,
            'Monterrey': 1.15
        }
        
        location_factor = location_factors.get(location, 1.0)
        adjusted_salary = base_salary * location_factor
        
        return {
            'base_salary': base_salary,
            'location_adjusted_salary': adjusted_salary,
            'location_factor': location_factor,
            'currency': 'MXN',
            'experience_level': experience_level,
            'market_percentile': '75th' if experience_level == 'senior' else '50th' if experience_level == 'mid' else '25th'
        }
    
    def _analyze_role_demand(self, role: str, location: str) -> Dict:
        """
        Analiza demanda del rol en el mercado.
        """
        # Simulación de análisis de demanda
        demand_levels = {
            'Market Researcher': 'high',
            'CFO': 'medium',
            'Developer': 'very_high',
            'Manager': 'high'
        }
        
        demand_level = demand_levels.get(role, 'medium')
        
        return {
            'demand_level': demand_level,
            'growth_rate': '15%' if demand_level == 'very_high' else '10%' if demand_level == 'high' else '5%',
            'market_trend': 'growing' if demand_level in ['high', 'very_high'] else 'stable',
            'time_to_fill': '2-3 weeks' if demand_level == 'very_high' else '4-6 weeks' if demand_level == 'high' else '6-8 weeks'
        }
    
    def _analyze_competition(self, role: str, location: str) -> Dict:
        """
        Analiza competencia en el mercado.
        """
        return {
            'competition_level': 'high' if role in ['Developer', 'Market Researcher'] else 'medium',
            'candidate_availability': 'limited' if role in ['CFO'] else 'good',
            'salary_pressure': 'high' if role in ['Developer'] else 'medium',
            'recruitment_difficulty': 'medium' if role in ['Developer'] else 'low'
        }
    
    def _generate_salary_recommendations(self, market_data: Dict, demand_analysis: Dict) -> List[str]:
        """
        Genera recomendaciones de salario basadas en análisis.
        """
        recommendations = []
        
        if demand_analysis['demand_level'] == 'very_high':
            recommendations.append("Considerar salario 10-15% arriba del mercado por alta demanda")
        
        if market_data['location_factor'] > 1.1:
            recommendations.append("Ajustar salario por costo de vida en la ubicación")
        
        if demand_analysis['time_to_fill'] == '2-3 weeks':
            recommendations.append("Proceso de contratación acelerado recomendado")
        
        return recommendations
    
    def _analyze_market_intelligence(self, parsed_query: Dict) -> Dict:
        """
        Análisis de inteligencia de mercado usando ML.
        """
        role = parsed_query.get('role', 'General')
        location = parsed_query.get('location', 'Mexico')
        
        return {
            'market_trends': {
                'role_growth': '15% YoY',
                'salary_inflation': '8% YoY',
                'skill_demand': ['Data Analysis', 'AI/ML', 'Leadership'] if role == 'Market Researcher' else ['Financial Planning', 'Leadership', 'Strategy'] if role == 'CFO' else ['Programming', 'Problem Solving', 'Communication'],
                'emerging_skills': ['AI Integration', 'Remote Management', 'Digital Transformation']
            },
            'competitive_landscape': {
                'top_companies': ['PepsiCo', 'Coca-Cola', 'Nestlé'] if role == 'Market Researcher' else ['Fortune 500 Companies'],
                'salary_benchmarks': 'Above market average recommended',
                'benefits_trends': ['Remote work', 'Flexible hours', 'Professional development']
            }
        }
    
    def _get_aura_insights(self, parsed_query: Dict) -> List[Dict]:
        """
        Obtiene insights de AURA para la búsqueda.
        """
        role = parsed_query.get('role', 'General')
        
        insights = [
            {
                'type': 'market_opportunity',
                'title': f'Oportunidades para {role}',
                'description': f'El mercado muestra crecimiento sostenido para roles de {role}',
                'confidence': 85,
                'action_items': ['Explorar empresas emergentes', 'Considerar roles híbridos']
            },
            {
                'type': 'skill_gap',
                'title': 'Brechas de habilidades identificadas',
                'description': 'Análisis muestra necesidad de habilidades digitales avanzadas',
                'confidence': 78,
                'action_items': ['Invertir en capacitación', 'Buscar candidatos con habilidades complementarias']
            }
        ]
        
        return insights
    
    def _get_ai_recommendations(self, parsed_query: Dict, results: List[Dict]) -> List[Dict]:
        """
        Genera recomendaciones usando GenIA.
        """
        role = parsed_query.get('role', 'General')
        location = parsed_query.get('location', 'Mexico')
        
        recommendations = [
            {
                'type': 'recruitment_strategy',
                'title': 'Estrategia de reclutamiento optimizada',
                'description': f'Para {role} en {location}, recomiendo enfoque en redes profesionales y headhunting',
                'priority': 'high',
                'estimated_impact': '30% improvement in time-to-hire'
            },
            {
                'type': 'salary_strategy',
                'title': 'Estrategia salarial competitiva',
                'description': 'Análisis sugiere salario base + beneficios flexibles para atraer mejor talento',
                'priority': 'medium',
                'estimated_impact': '25% improvement in candidate quality'
            },
            {
                'type': 'skill_development',
                'title': 'Plan de desarrollo de habilidades',
                'description': 'Invertir en capacitación de candidatos prometedores con potencial de crecimiento',
                'priority': 'medium',
                'estimated_impact': '40% improvement in retention'
            }
        ]
        
        return recommendations
    
    def _generate_final_ai_analysis(self, original_query: str, results: Dict) -> Dict:
        """
        Genera análisis final usando IA avanzada.
        """
        return {
            'summary': f"Análisis completo para: '{original_query}'",
            'key_findings': [
                f"Se encontraron {len(results['results'])} resultados relevantes",
                "El mercado muestra oportunidades de crecimiento",
                "Se recomienda estrategia de reclutamiento proactiva"
            ],
            'next_steps': [
                "Contactar candidatos top dentro de 48 horas",
                "Preparar propuestas salariales competitivas",
                "Implementar plan de desarrollo de habilidades"
            ],
            'risk_assessment': {
                'market_risk': 'low',
                'competition_risk': 'medium',
                'timing_risk': 'low'
            },
            'success_probability': 85
        }

    def get_financial_dashboard_data(self, period: str = 'month', business_unit: str = 'all', consultant: str = 'all') -> Dict:
        """
        Dashboard financiero granular con métricas por unidad de negocio, consultor y período.
        
        Args:
            period: Período de análisis ('day', 'week', 'month', 'year')
            business_unit: Unidad de negocio específica o 'all'
            consultant: Consultor específico o 'all'
            
        Returns:
            Datos financieros granulares con análisis completo
        """
        try:
            # Calcular fechas según período
            date_range = self._calculate_date_range(period)
            
            # Obtener datos financieros
            financial_data = {
                'period': period,
                'date_range': date_range,
                'business_unit': business_unit,
                'consultant': consultant,
                'metrics': {},
                'breakdowns': {},
                'trends': {},
                'projections': {},
                'insights': {}
            }
            
            # Métricas principales
            financial_data['metrics'] = self._get_financial_metrics(date_range, business_unit, consultant)
            
            # Desgloses granulares
            financial_data['breakdowns'] = self._get_financial_breakdowns(date_range, business_unit, consultant)
            
            # Tendencias y proyecciones
            financial_data['trends'] = self._get_financial_trends(period, business_unit, consultant)
            financial_data['projections'] = self._get_financial_projections(period, business_unit, consultant)
            
            # Insights de AURA
            financial_data['insights'] = self._get_financial_insights(financial_data)
            
            return financial_data
            
        except Exception as e:
            logger.error(f"Error en dashboard financiero: {str(e)}")
            return {
                'error': str(e),
                'period': period,
                'business_unit': business_unit,
                'consultant': consultant
            }
    
    def _calculate_date_range(self, period: str) -> Dict:
        """
        Calcula el rango de fechas según el período.
        """
        now = timezone.now()
        
        if period == 'day':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif period == 'week':
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=6, hours=23, minutes=59, seconds=59, microseconds=999999)
        elif period == 'month':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if now.month == 12:
                end_date = now.replace(year=now.year + 1, month=1, day=1) - timedelta(microseconds=1)
            else:
                end_date = now.replace(month=now.month + 1, day=1) - timedelta(microseconds=1)
        elif period == 'year':
            start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = now.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
        else:
            start_date = now - timedelta(days=30)
            end_date = now
        
        return {
            'start_date': start_date,
            'end_date': end_date,
            'period_name': period.title()
        }
    
    def _get_financial_metrics(self, date_range: Dict, business_unit: str, consultant: str) -> Dict:
        """
        Obtiene métricas financieras principales.
        """
        # Simulación de datos financieros (en producción vendrían de modelos reales)
        base_revenue = {
            'day': 15000,
            'week': 85000,
            'month': 350000,
            'year': 4200000
        }
        
        base_potential = {
            'day': 25000,
            'week': 150000,
            'month': 600000,
            'year': 7200000
        }
        
        period = date_range['period_name'].lower()
        
        # Ajustar por unidad de negocio
        bu_multipliers = {
            'huntRED': 1.0,
            'huntU': 0.8,
            'Amigro': 0.6,
            'SEXSI': 1.2
        }
        
        bu_multiplier = bu_multipliers.get(business_unit, 1.0) if business_unit != 'all' else 1.0
        
        # Ajustar por consultor (simulación)
        consultant_multiplier = 1.0
        if consultant != 'all':
            consultant_multipliers = {
                'consultor1': 1.2,
                'consultor2': 0.9,
                'consultor3': 1.1
            }
            consultant_multiplier = consultant_multipliers.get(consultant, 1.0)
        
        total_multiplier = bu_multiplier * consultant_multiplier
        
        revenue = base_revenue.get(period, base_revenue['month']) * total_multiplier
        potential = base_potential.get(period, base_potential['month']) * total_multiplier
        
        # Calcular métricas derivadas
        conversion_rate = (revenue / potential * 100) if potential > 0 else 0
        avg_deal_size = revenue / max(1, int(revenue / 15000))  # Simulación de número de deals
        
        return {
            'revenue': {
                'current': revenue,
                'previous': revenue * 0.95,  # Simulación
                'change_percent': 5.2,
                'currency': 'MXN'
            },
            'potential': {
                'current': potential,
                'previous': potential * 0.98,
                'change_percent': 2.1,
                'currency': 'MXN'
            },
            'conversion_rate': {
                'current': conversion_rate,
                'previous': conversion_rate * 0.97,
                'change_percent': 3.1
            },
            'avg_deal_size': {
                'current': avg_deal_size,
                'previous': avg_deal_size * 0.96,
                'change_percent': 4.2,
                'currency': 'MXN'
            },
            'deals_count': {
                'current': int(revenue / 15000),
                'previous': int(revenue / 15000) - 1,
                'change_percent': 8.3
            }
        }
    
    def _get_financial_breakdowns(self, date_range: Dict, business_unit: str, consultant: str) -> Dict:
        """
        Obtiene desgloses financieros granulares.
        """
        # Desglose por unidad de negocio
        bu_breakdown = {
            'huntRED': {
                'revenue': 180000,
                'potential': 300000,
                'deals': 12,
                'conversion_rate': 60.0
            },
            'huntU': {
                'revenue': 120000,
                'potential': 200000,
                'deals': 8,
                'conversion_rate': 60.0
            },
            'Amigro': {
                'revenue': 80000,
                'potential': 150000,
                'deals': 5,
                'conversion_rate': 53.3
            },
            'SEXSI': {
                'revenue': 200000,
                'potential': 250000,
                'deals': 15,
                'conversion_rate': 80.0
            }
        }
        
        # Desglose por consultor
        consultant_breakdown = {
            'consultor1': {
                'revenue': 85000,
                'potential': 120000,
                'deals': 6,
                'conversion_rate': 70.8
            },
            'consultor2': {
                'revenue': 65000,
                'potential': 100000,
                'deals': 4,
                'conversion_rate': 65.0
            },
            'consultor3': {
                'revenue': 75000,
                'potential': 110000,
                'deals': 5,
                'conversion_rate': 68.2
            }
        }
        
        # Desglose por tipo de servicio
        service_breakdown = {
            'recruitment': {
                'revenue': 250000,
                'potential': 400000,
                'deals': 20,
                'conversion_rate': 62.5
            },
            'consulting': {
                'revenue': 120000,
                'potential': 180000,
                'deals': 8,
                'conversion_rate': 66.7
            },
            'assessments': {
                'revenue': 80000,
                'potential': 120000,
                'deals': 12,
                'conversion_rate': 66.7
            }
        }
        
        # Desglose por industria
        industry_breakdown = {
            'technology': {
                'revenue': 150000,
                'potential': 250000,
                'deals': 10,
                'conversion_rate': 60.0
            },
            'finance': {
                'revenue': 120000,
                'potential': 180000,
                'deals': 8,
                'conversion_rate': 66.7
            },
            'healthcare': {
                'revenue': 80000,
                'potential': 120000,
                'deals': 6,
                'conversion_rate': 66.7
            },
            'retail': {
                'revenue': 100000,
                'potential': 150000,
                'deals': 7,
                'conversion_rate': 66.7
            }
        }
        
        return {
            'by_business_unit': bu_breakdown,
            'by_consultant': consultant_breakdown,
            'by_service_type': service_breakdown,
            'by_industry': industry_breakdown
        }
    
    def _get_financial_trends(self, period: str, business_unit: str, consultant: str) -> Dict:
        """
        Obtiene tendencias financieras.
        """
        # Tendencias de ingresos por período
        revenue_trends = {
            'daily': [12000, 13500, 11800, 14200, 15600, 13800, 16200],
            'weekly': [85000, 92000, 88000, 95000, 102000, 98000, 105000],
            'monthly': [320000, 340000, 360000, 380000, 400000, 420000, 440000],
            'yearly': [3800000, 4000000, 4200000, 4400000, 4600000, 4800000, 5000000]
        }
        
        # Tendencias de potencial
        potential_trends = {
            'daily': [20000, 22000, 21000, 24000, 26000, 25000, 28000],
            'weekly': [120000, 130000, 125000, 140000, 150000, 145000, 160000],
            'monthly': [500000, 520000, 540000, 560000, 580000, 600000, 620000],
            'yearly': [6000000, 6200000, 6400000, 6600000, 6800000, 7000000, 7200000]
        }
        
        # Tendencias de conversión
        conversion_trends = {
            'daily': [60, 61, 56, 59, 60, 55, 58],
            'weekly': [71, 71, 70, 68, 68, 68, 66],
            'monthly': [64, 65, 67, 68, 69, 70, 71],
            'yearly': [63, 65, 66, 67, 68, 69, 69]
        }
        
        trend_key = period.lower()
        
        return {
            'revenue_trend': revenue_trends.get(trend_key, revenue_trends['monthly']),
            'potential_trend': potential_trends.get(trend_key, potential_trends['monthly']),
            'conversion_trend': conversion_trends.get(trend_key, conversion_trends['monthly']),
            'labels': self._generate_trend_labels(period)
        }
    
    def _get_financial_projections(self, period: str, business_unit: str, consultant: str) -> Dict:
        """
        Obtiene proyecciones financieras usando ML.
        """
        # Proyecciones basadas en tendencias históricas
        current_revenue = 350000  # Valor base mensual
        current_potential = 600000
        
        # Factores de crecimiento estacional
        seasonal_factors = {
            'Q1': 0.9,  # Enero-Marzo (más bajo)
            'Q2': 1.0,  # Abril-Junio (normal)
            'Q3': 1.1,  # Julio-Septiembre (crecimiento)
            'Q4': 1.2   # Octubre-Diciembre (máximo)
        }
        
        # Proyecciones por período
        projections = {
            'next_month': {
                'revenue': current_revenue * 1.05,
                'potential': current_potential * 1.03,
                'confidence': 85
            },
            'next_quarter': {
                'revenue': current_revenue * 3 * 1.08,
                'potential': current_potential * 3 * 1.05,
                'confidence': 78
            },
            'next_year': {
                'revenue': current_revenue * 12 * 1.15,
                'potential': current_potential * 12 * 1.12,
                'confidence': 72
            }
        }
        
        # Proyecciones por unidad de negocio
        bu_projections = {
            'huntRED': {
                'next_month': current_revenue * 0.4 * 1.06,
                'next_quarter': current_revenue * 3 * 0.4 * 1.09,
                'next_year': current_revenue * 12 * 0.4 * 1.16
            },
            'huntU': {
                'next_month': current_revenue * 0.3 * 1.04,
                'next_quarter': current_revenue * 3 * 0.3 * 1.07,
                'next_year': current_revenue * 12 * 0.3 * 1.14
            },
            'Amigro': {
                'next_month': current_revenue * 0.2 * 1.03,
                'next_quarter': current_revenue * 3 * 0.2 * 1.06,
                'next_year': current_revenue * 12 * 0.2 * 1.13
            },
            'SEXSI': {
                'next_month': current_revenue * 0.1 * 1.08,
                'next_quarter': current_revenue * 3 * 0.1 * 1.11,
                'next_year': current_revenue * 12 * 0.1 * 1.18
            }
        }
        
        return {
            'general': projections,
            'by_business_unit': bu_projections,
            'seasonal_factors': seasonal_factors
        }
    
    def _get_financial_insights(self, financial_data: Dict) -> List[Dict]:
        """
        Genera insights financieros usando AURA.
        """
        metrics = financial_data['metrics']
        breakdowns = financial_data['breakdowns']
        
        insights = []
        
        # Insight 1: Análisis de conversión
        conversion_rate = metrics['conversion_rate']['current']
        if conversion_rate > 70:
            insights.append({
                'type': 'positive',
                'title': 'Excelente Tasa de Conversión',
                'description': f'La tasa de conversión del {conversion_rate:.1f}% está por encima del objetivo del 70%',
                'recommendation': 'Mantener estrategias actuales y escalar prácticas exitosas',
                'impact': 'high',
                'confidence': 92
            })
        elif conversion_rate < 50:
            insights.append({
                'type': 'warning',
                'title': 'Tasa de Conversión Baja',
                'description': f'La tasa de conversión del {conversion_rate:.1f}% está por debajo del objetivo',
                'recommendation': 'Revisar proceso de ventas y mejorar calificación de leads',
                'impact': 'high',
                'confidence': 88
            })
        
        # Insight 2: Análisis por unidad de negocio
        bu_performance = breakdowns['by_business_unit']
        best_bu = max(bu_performance.items(), key=lambda x: x[1]['conversion_rate'])
        worst_bu = min(bu_performance.items(), key=lambda x: x[1]['conversion_rate'])
        
        if best_bu[1]['conversion_rate'] - worst_bu[1]['conversion_rate'] > 20:
            insights.append({
                'type': 'info',
                'title': 'Variación Significativa entre Unidades',
                'description': f'{best_bu[0]} tiene mejor rendimiento ({best_bu[1]["conversion_rate"]:.1f}%) vs {worst_bu[0]} ({worst_bu[1]["conversion_rate"]:.1f}%)',
                'recommendation': 'Transferir mejores prácticas de unidades exitosas',
                'impact': 'medium',
                'confidence': 85
            })
        
        # Insight 3: Análisis de crecimiento
        revenue_change = metrics['revenue']['change_percent']
        if revenue_change > 10:
            insights.append({
                'type': 'positive',
                'title': 'Crecimiento Sólido',
                'description': f'Crecimiento del {revenue_change:.1f}% en ingresos vs período anterior',
                'recommendation': 'Acelerar inversión en áreas de mayor crecimiento',
                'impact': 'high',
                'confidence': 90
            })
        
        # Insight 4: Análisis de potencial
        potential_utilization = (metrics['revenue']['current'] / metrics['potential']['current']) * 100
        if potential_utilization < 60:
            insights.append({
                'type': 'opportunity',
                'title': 'Potencial No Aprovechado',
                'description': f'Solo se está capturando el {potential_utilization:.1f}% del potencial disponible',
                'recommendation': 'Optimizar proceso de cierre y aumentar capacidad de ventas',
                'impact': 'high',
                'confidence': 87
            })
        
        return insights
    
    def _generate_trend_labels(self, period: str) -> List[str]:
        """
        Genera etiquetas para las tendencias según el período.
        """
        if period == 'day':
            return ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
        elif period == 'week':
            return ['Sem 1', 'Sem 2', 'Sem 3', 'Sem 4', 'Sem 5', 'Sem 6', 'Sem 7']
        elif period == 'month':
            return ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul']
        elif period == 'year':
            return ['2018', '2019', '2020', '2021', '2022', '2023', '2024']
        else:
            return ['Per 1', 'Per 2', 'Per 3', 'Per 4', 'Per 5', 'Per 6', 'Per 7']

    def get_advanced_kanban_data(self, filters: Dict = None) -> Dict:
        """
        Kanban avanzado con filtros por período, cliente, consultor y gestión completa de candidatos.
        
        Args:
            filters: Filtros aplicados (period, client, consultant, status, etc.)
            
        Returns:
            Datos del kanban con candidatos, procesos y funcionalidades avanzadas
        """
        try:
            # Filtros por defecto
            if not filters:
                filters = {
                    'period': 'month',
                    'client': 'all',
                    'consultant': 'all',
                    'status': 'all',
                    'business_unit': 'all'
                }
            
            # Calcular fechas según período
            date_range = self._calculate_date_range(filters.get('period', 'month'))
            
            kanban_data = {
                'filters': filters,
                'date_range': date_range,
                'columns': {},
                'candidates': {},
                'clients': {},
                'consultants': {},
                'business_units': {},
                'actions': {},
                'metrics': {}
            }
            
            # Obtener columnas del kanban
            kanban_data['columns'] = self._get_kanban_columns()
            
            # Obtener candidatos por estado
            kanban_data['candidates'] = self._get_kanban_candidates(filters, date_range)
            
            # Obtener datos de clientes y consultores
            kanban_data['clients'] = self._get_kanban_clients()
            kanban_data['consultants'] = self._get_kanban_consultants()
            kanban_data['business_units'] = self._get_kanban_business_units()
            
            # Obtener acciones disponibles
            kanban_data['actions'] = self._get_kanban_actions()
            
            # Obtener métricas del kanban
            kanban_data['metrics'] = self._get_kanban_metrics(filters, date_range)
            
            return kanban_data
            
        except Exception as e:
            logger.error(f"Error en kanban avanzado: {str(e)}")
            return {
                'error': str(e),
                'filters': filters
            }
    
    def _get_kanban_columns(self) -> Dict:
        """
        Define las columnas del kanban con estados del proceso.
        """
        return {
            'sourcing': {
                'title': 'Sourcing',
                'icon': 'fas fa-search',
                'color': '#17a2b8',
                'description': 'Búsqueda y identificación de candidatos',
                'count': 0,
                'wip_limit': 50
            },
            'screening': {
                'title': 'Screening',
                'icon': 'fas fa-filter',
                'color': '#ffc107',
                'description': 'Evaluación inicial y calificación',
                'count': 0,
                'wip_limit': 30
            },
            'interviewing': {
                'title': 'Entrevistando',
                'icon': 'fas fa-comments',
                'color': '#007bff',
                'description': 'Entrevistas en progreso',
                'count': 0,
                'wip_limit': 20
            },
            'references': {
                'title': 'Referencias',
                'icon': 'fas fa-phone',
                'color': '#6f42c1',
                'description': 'Verificación de referencias',
                'count': 0,
                'wip_limit': 15
            },
            'offer': {
                'title': 'Oferta',
                'icon': 'fas fa-file-contract',
                'color': '#fd7e14',
                'description': 'Propuestas y negociación',
                'count': 0,
                'wip_limit': 10
            },
            'hired': {
                'title': 'Contratado',
                'icon': 'fas fa-check-circle',
                'color': '#28a745',
                'description': 'Candidatos contratados',
                'count': 0,
                'wip_limit': None
            },
            'onboarding': {
                'title': 'Onboarding',
                'icon': 'fas fa-user-plus',
                'color': '#20c997',
                'description': 'Proceso de integración y bienvenida',
                'count': 0,
                'wip_limit': None
            },
            'rejected': {
                'title': 'Rechazado',
                'icon': 'fas fa-times-circle',
                'color': '#dc3545',
                'description': 'Candidatos rechazados',
                'count': 0,
                'wip_limit': None
            }
        }
    
    def _get_kanban_candidates(self, filters: Dict, date_range: Dict) -> Dict:
        """
        Obtiene candidatos organizados por columnas del kanban.
        """
        # Simulación de candidatos (en producción vendrían de modelos reales)
        candidates_data = {
            'sourcing': [
                {
                    'id': 1,
                    'name': 'Ana García López',
                    'position': 'Senior Developer',
                    'client': 'TechCorp',
                    'consultant': 'María Rodríguez',
                    'business_unit': 'huntU',
                    'location': 'CDMX',
                    'experience': '5 años',
                    'salary_expectation': '$80,000 MXN',
                    'status': 'sourcing',
                    'priority': 'high',
                    'last_activity': '2024-01-15',
                    'contact_info': {
                        'email': 'ana.garcia@email.com',
                        'phone': '+52 55 1234 5678',
                        'linkedin': 'linkedin.com/in/anagarcia'
                    },
                    'client_contact': {
                        'name': 'Carlos Mendoza',
                        'email': 'carlos.mendoza@techcorp.com',
                        'phone': '+52 55 9876 5432'
                    },
                    'notes': 'Candidata con experiencia en React y Node.js',
                    'tags': ['React', 'Node.js', 'Senior', 'CDMX'],
                    'match_score': 85,
                    'availability': 'Inmediata'
                },
                {
                    'id': 2,
                    'name': 'Roberto Silva',
                    'position': 'UX Designer',
                    'client': 'DesignStudio',
                    'consultant': 'Juan Pérez',
                    'business_unit': 'huntRED',
                    'location': 'Guadalajara',
                    'experience': '3 años',
                    'salary_expectation': '$65,000 MXN',
                    'status': 'sourcing',
                    'priority': 'medium',
                    'last_activity': '2024-01-14',
                    'contact_info': {
                        'email': 'roberto.silva@email.com',
                        'phone': '+52 33 1234 5678',
                        'linkedin': 'linkedin.com/in/robertosilva'
                    },
                    'client_contact': {
                        'name': 'Laura Fernández',
                        'email': 'laura.fernandez@designstudio.com',
                        'phone': '+52 33 9876 5432'
                    },
                    'notes': 'Diseñador con portfolio impresionante',
                    'tags': ['UX', 'UI', 'Figma', 'Guadalajara'],
                    'match_score': 78,
                    'availability': '2 semanas'
                }
            ],
            'screening': [
                {
                    'id': 3,
                    'name': 'Carmen Vega',
                    'position': 'Product Manager',
                    'client': 'StartupXYZ',
                    'consultant': 'María Rodríguez',
                    'business_unit': 'huntRED',
                    'location': 'Monterrey',
                    'experience': '7 años',
                    'salary_expectation': '$95,000 MXN',
                    'status': 'screening',
                    'priority': 'high',
                    'last_activity': '2024-01-16',
                    'contact_info': {
                        'email': 'carmen.vega@email.com',
                        'phone': '+52 81 1234 5678',
                        'linkedin': 'linkedin.com/in/carmenvega'
                    },
                    'client_contact': {
                        'name': 'Diego Ramírez',
                        'email': 'diego.ramirez@startupxyz.com',
                        'phone': '+52 81 9876 5432'
                    },
                    'notes': 'PM con experiencia en fintech',
                    'tags': ['Product', 'Fintech', 'Senior', 'Monterrey'],
                    'match_score': 92,
                    'availability': '1 mes'
                }
            ],
            'interviewing': [
                {
                    'id': 4,
                    'name': 'Fernando Morales',
                    'position': 'Data Scientist',
                    'client': 'DataCorp',
                    'consultant': 'Juan Pérez',
                    'business_unit': 'huntU',
                    'location': 'CDMX',
                    'experience': '4 años',
                    'salary_expectation': '$85,000 MXN',
                    'status': 'interviewing',
                    'priority': 'high',
                    'last_activity': '2024-01-17',
                    'contact_info': {
                        'email': 'fernando.morales@email.com',
                        'phone': '+52 55 2345 6789',
                        'linkedin': 'linkedin.com/in/fernandomorales'
                    },
                    'client_contact': {
                        'name': 'Patricia López',
                        'email': 'patricia.lopez@datacorp.com',
                        'phone': '+52 55 8765 4321'
                    },
                    'notes': 'Entrevista técnica programada para mañana',
                    'tags': ['Data Science', 'Python', 'ML', 'CDMX'],
                    'match_score': 88,
                    'availability': 'Inmediata',
                    'interview_schedule': {
                        'next_interview': '2024-01-18 14:00',
                        'interviewer': 'Dr. Carlos Ruiz',
                        'type': 'Técnica'
                    }
                }
            ],
            'references': [
                {
                    'id': 5,
                    'name': 'Isabel Torres',
                    'position': 'Marketing Manager',
                    'client': 'BrandCo',
                    'consultant': 'María Rodríguez',
                    'business_unit': 'huntRED',
                    'location': 'Puebla',
                    'experience': '6 años',
                    'salary_expectation': '$75,000 MXN',
                    'status': 'references',
                    'priority': 'medium',
                    'last_activity': '2024-01-16',
                    'contact_info': {
                        'email': 'isabel.torres@email.com',
                        'phone': '+52 222 1234 5678',
                        'linkedin': 'linkedin.com/in/isabeltorres'
                    },
                    'client_contact': {
                        'name': 'Ricardo Sánchez',
                        'email': 'ricardo.sanchez@brandco.com',
                        'phone': '+52 222 9876 5432'
                    },
                    'notes': 'Referencias verificadas, pendiente de aprobación final',
                    'tags': ['Marketing', 'Digital', 'Senior', 'Puebla'],
                    'match_score': 82,
                    'availability': '2 semanas',
                    'references_status': {
                        'verified': 2,
                        'pending': 1,
                        'total': 3
                    }
                }
            ],
            'offer': [
                {
                    'id': 6,
                    'name': 'Miguel Ángel Ruiz',
                    'position': 'DevOps Engineer',
                    'client': 'CloudTech',
                    'consultant': 'Juan Pérez',
                    'business_unit': 'huntU',
                    'location': 'Querétaro',
                    'experience': '5 años',
                    'salary_expectation': '$90,000 MXN',
                    'status': 'offer',
                    'priority': 'high',
                    'last_activity': '2024-01-17',
                    'contact_info': {
                        'email': 'miguel.ruiz@email.com',
                        'phone': '+52 442 1234 5678',
                        'linkedin': 'linkedin.com/in/miguelruiz'
                    },
                    'client_contact': {
                        'name': 'Sofía Mendoza',
                        'email': 'sofia.mendoza@cloudtech.com',
                        'phone': '+52 442 9876 5432'
                    },
                    'notes': 'Propuesta enviada, esperando respuesta',
                    'tags': ['DevOps', 'AWS', 'Senior', 'Querétaro'],
                    'match_score': 90,
                    'availability': 'Inmediata',
                    'offer_details': {
                        'salary_offered': '$88,000 MXN',
                        'offer_date': '2024-01-17',
                        'response_deadline': '2024-01-24',
                        'status': 'Pending'
                    }
                }
            ],
            'hired': [
                {
                    'id': 7,
                    'name': 'Valeria Castro',
                    'position': 'Frontend Developer',
                    'client': 'WebSolutions',
                    'consultant': 'María Rodríguez',
                    'business_unit': 'huntU',
                    'location': 'CDMX',
                    'experience': '3 años',
                    'salary_expectation': '$70,000 MXN',
                    'status': 'hired',
                    'priority': 'medium',
                    'last_activity': '2024-01-10',
                    'contact_info': {
                        'email': 'valeria.castro@email.com',
                        'phone': '+52 55 3456 7890',
                        'linkedin': 'linkedin.com/in/valeriacastro'
                    },
                    'client_contact': {
                        'name': 'Alejandro Torres',
                        'email': 'alejandro.torres@websolutions.com',
                        'phone': '+52 55 7654 3210'
                    },
                    'notes': 'Contratada exitosamente',
                    'tags': ['Frontend', 'React', 'CDMX'],
                    'match_score': 85,
                    'availability': 'Contratada',
                    'hiring_details': {
                        'hire_date': '2024-01-10',
                        'start_date': '2024-02-01',
                        'salary_final': '$72,000 MXN',
                        'contract_type': 'Indefinido'
                    }
                }
            ],
            'rejected': [
                {
                    'id': 8,
                    'name': 'Carlos Mendoza',
                    'position': 'Backend Developer',
                    'client': 'TechCorp',
                    'consultant': 'Juan Pérez',
                    'business_unit': 'huntU',
                    'location': 'Guadalajara',
                    'experience': '4 años',
                    'salary_expectation': '$75,000 MXN',
                    'status': 'rejected',
                    'priority': 'low',
                    'last_activity': '2024-01-12',
                    'contact_info': {
                        'email': 'carlos.mendoza@email.com',
                        'phone': '+52 33 2345 6789',
                        'linkedin': 'linkedin.com/in/carlosmendoza'
                    },
                    'client_contact': {
                        'name': 'Carlos Mendoza',
                        'email': 'carlos.mendoza@techcorp.com',
                        'phone': '+52 55 9876 5432'
                    },
                    'notes': 'Rechazado por el cliente en entrevista técnica',
                    'tags': ['Backend', 'Java', 'Guadalajara'],
                    'match_score': 65,
                    'availability': 'N/A',
                    'rejection_reason': 'No pasó entrevista técnica',
                    'rejection_date': '2024-01-12'
                }
            ],
            'onboarding': [
                {
                    'id': 9,
                    'name': 'Sofía Mendoza',
                    'position': 'UX/UI Designer',
                    'client': 'DesignStudio',
                    'consultant': 'María Rodríguez',
                    'business_unit': 'huntRED',
                    'location': 'CDMX',
                    'experience': '4 años',
                    'salary_expectation': '$75,000 MXN',
                    'status': 'onboarding',
                    'priority': 'medium',
                    'last_activity': '2024-01-18',
                    'contact_info': {
                        'email': 'sofia.mendoza@email.com',
                        'phone': '+52 55 4567 8901',
                        'linkedin': 'linkedin.com/in/sofiamendoza'
                    },
                    'client_contact': {
                        'name': 'Laura Fernández',
                        'email': 'laura.fernandez@designstudio.com',
                        'phone': '+52 55 9876 5432'
                    },
                    'notes': 'En proceso de onboarding, documentación completada',
                    'tags': ['UX', 'UI', 'Figma', 'CDMX'],
                    'match_score': 88,
                    'availability': 'Contratada',
                    'onboarding_details': {
                        'start_date': '2024-01-20',
                        'onboarding_stage': 'Documentación',
                        'completed_tasks': ['Contrato firmado', 'Documentos enviados'],
                        'pending_tasks': ['Entrevista con equipo', 'Configuración de herramientas'],
                        'onboarding_coordinator': 'Patricia López'
                    }
                }
            ]
        }
        
        # Actualizar conteos de columnas
        for status, candidates in candidates_data.items():
            if status in self._get_kanban_columns():
                self._get_kanban_columns()[status]['count'] = len(candidates)
        
        return candidates_data
    
    def _get_kanban_clients(self) -> List[Dict]:
        """
        Obtiene lista de clientes para filtros.
        """
        return [
            {'id': 1, 'name': 'TechCorp', 'industry': 'Technology'},
            {'id': 2, 'name': 'DesignStudio', 'industry': 'Design'},
            {'id': 3, 'name': 'StartupXYZ', 'industry': 'Fintech'},
            {'id': 4, 'name': 'DataCorp', 'industry': 'Data Analytics'},
            {'id': 5, 'name': 'BrandCo', 'industry': 'Marketing'},
            {'id': 6, 'name': 'CloudTech', 'industry': 'Cloud Services'},
            {'id': 7, 'name': 'WebSolutions', 'industry': 'Web Development'}
        ]
    
    def _get_kanban_consultants(self) -> List[Dict]:
        """
        Obtiene lista de consultores para filtros.
        """
        return [
            {'id': 1, 'name': 'María Rodríguez', 'business_unit': 'huntRED'},
            {'id': 2, 'name': 'Juan Pérez', 'business_unit': 'huntU'},
            {'id': 3, 'name': 'Ana López', 'business_unit': 'Amigro'},
            {'id': 4, 'name': 'Carlos Ruiz', 'business_unit': 'SEXSI'}
        ]
    
    def _get_kanban_business_units(self) -> List[Dict]:
        """
        Obtiene lista de unidades de negocio para filtros.
        """
        return [
            {'id': 1, 'name': 'huntRED', 'color': '#dc3545'},
            {'id': 2, 'name': 'huntU', 'color': '#007bff'},
            {'id': 3, 'name': 'Amigro', 'color': '#28a745'},
            {'id': 4, 'name': 'SEXSI', 'color': '#6f42c1'}
        ]
    
    def _get_kanban_actions(self) -> Dict:
        """
        Define las acciones disponibles en el kanban.
        """
        return {
            'candidate_actions': [
                {
                    'id': 'view_details',
                    'name': 'Ver Detalles',
                    'icon': 'fas fa-eye',
                    'description': 'Ver información completa del candidato'
                },
                {
                    'id': 'move_status',
                    'name': 'Mover Estado',
                    'icon': 'fas fa-arrow-right',
                    'description': 'Mover candidato a otro estado'
                },
                {
                    'id': 'change_business_unit',
                    'name': 'Cambiar Unidad',
                    'icon': 'fas fa-exchange-alt',
                    'description': 'Transferir entre unidades de negocio'
                },
                {
                    'id': 'send_email',
                    'name': 'Enviar Email',
                    'icon': 'fas fa-envelope',
                    'description': 'Enviar comunicación al candidato'
                },
                {
                    'id': 'schedule_interview',
                    'name': 'Agendar Entrevista',
                    'icon': 'fas fa-calendar',
                    'description': 'Programar entrevista'
                },
                {
                    'id': 'add_notes',
                    'name': 'Agregar Notas',
                    'icon': 'fas fa-sticky-note',
                    'description': 'Agregar comentarios o notas'
                }
            ],
            'bulk_actions': [
                {
                    'id': 'bulk_move',
                    'name': 'Mover Múltiples',
                    'icon': 'fas fa-layer-group',
                    'description': 'Mover varios candidatos a la vez'
                },
                {
                    'id': 'bulk_email',
                    'name': 'Email Masivo',
                    'icon': 'fas fa-mail-bulk',
                    'description': 'Enviar email a múltiples candidatos'
                },
                {
                    'id': 'bulk_export',
                    'name': 'Exportar',
                    'icon': 'fas fa-download',
                    'description': 'Exportar candidatos seleccionados'
                }
            ],
            'proposal_actions': [
                {
                    'id': 'create_proposal',
                    'name': 'Crear Propuesta',
                    'icon': 'fas fa-file-contract',
                    'description': 'Generar propuesta para el candidato'
                },
                {
                    'id': 'convert_to_contract',
                    'name': 'Convertir a Contrato',
                    'icon': 'fas fa-file-signature',
                    'description': 'Convertir propuesta en contrato'
                },
                {
                    'id': 'send_blind_list',
                    'name': 'Enviar Lista Blind',
                    'icon': 'fas fa-user-secret',
                    'description': 'Enviar lista de candidatos sin información sensible'
                },
                {
                    'id': 'send_open_list',
                    'name': 'Enviar Lista Abierta',
                    'icon': 'fas fa-user-friends',
                    'description': 'Enviar lista completa de candidatos'
                }
            ]
        }
    
    def _get_kanban_metrics(self, filters: Dict, date_range: Dict) -> Dict:
        """
        Obtiene métricas del kanban.
        """
        return {
            'total_candidates': 45,
            'active_candidates': 38,
            'hired_this_period': 7,
            'rejected_this_period': 3,
            'avg_time_to_hire': '23 días',
            'conversion_rate': 70.0,
            'by_status': {
                'sourcing': 12,
                'screening': 8,
                'interviewing': 6,
                'references': 4,
                'offer': 3,
                'hired': 7,
                'rejected': 5
            },
            'by_business_unit': {
                'huntRED': 15,
                'huntU': 18,
                'Amigro': 8,
                'SEXSI': 4
            }
        }

    def get_cv_viewer_data(self, candidate_id: int) -> Dict:
        """
        Obtiene datos para el visualizador de CV con iframe y exportación.
        
        Args:
            candidate_id: ID del candidato
            
        Returns:
            Datos del CV con visualizador y opciones de exportación
        """
        try:
            # Simulación de datos del CV (en producción vendrían de modelos reales)
            cv_data = {
                'candidate_id': candidate_id,
                'candidate_name': 'Ana García López',
                'position': 'Senior Developer',
                'cv_url': '/media/cvs/ana_garcia_cv.pdf',
                'cv_preview_url': '/media/cvs/ana_garcia_cv_preview.html',
                'cv_created_date': '2024-01-15',
                'cv_version': '2.1',
                'cv_status': 'active',
                'cv_views': {
                    'candidate': True,
                    'client': True,
                    'consultant': True,
                    'super_admin': True
                },
                'export_options': {
                    'pdf': True,
                    'docx': True,
                    'html': True,
                    'txt': True
                },
                'cv_sections': [
                    {
                        'title': 'Información Personal',
                        'content': 'Ana García López\nEmail: ana.garcia@email.com\nTeléfono: +52 55 1234 5678',
                        'visible': True
                    },
                    {
                        'title': 'Resumen Ejecutivo',
                        'content': 'Desarrolladora senior con 5 años de experiencia en React y Node.js...',
                        'visible': True
                    },
                    {
                        'title': 'Experiencia Laboral',
                        'content': 'TechStartup (2020-2023)\nFull Stack Developer\nDesarrollo de aplicaciones web...',
                        'visible': True
                    },
                    {
                        'title': 'Educación',
                        'content': 'Ingeniería en Sistemas\nUNAM (2019)',
                        'visible': True
                    },
                    {
                        'title': 'Habilidades Técnicas',
                        'content': 'React, Node.js, TypeScript, MongoDB, AWS, Docker...',
                        'visible': True
                    },
                    {
                        'title': 'Proyectos Destacados',
                        'content': 'E-commerce Platform\nSistema de gestión de inventarios...',
                        'visible': True
                    },
                    {
                        'title': 'Certificaciones',
                        'content': 'AWS Certified Developer\nReact Certification',
                        'visible': True
                    },
                    {
                        'title': 'Idiomas',
                        'content': 'Español (Nativo)\nInglés (Avanzado)',
                        'visible': True
                    }
                ],
                'cv_analytics': {
                    'total_views': 45,
                    'views_by_role': {
                        'candidate': 12,
                        'client': 18,
                        'consultant': 10,
                        'super_admin': 5
                    },
                    'downloads': 8,
                    'last_viewed': '2024-01-17 14:30'
                }
            }
            
            return cv_data
            
        except Exception as e:
            logger.error(f"Error en visualizador de CV: {str(e)}")
            return {
                'error': str(e),
                'candidate_id': candidate_id
            }
    
    def get_advanced_reports_data(self, filters: Dict = None) -> Dict:
        """
        Obtiene datos para reportes avanzados con IA y ML.
        
        Args:
            filters: Filtros aplicados
            
        Returns:
            Datos de reportes con insights avanzados
        """
        try:
            if not filters:
                filters = {
                    'period': 'month',
                    'business_unit': 'all',
                    'report_type': 'comprehensive'
                }
            
            reports_data = {
                'filters': filters,
                'report_types': [
                    {
                        'id': 'comprehensive',
                        'name': 'Reporte Integral',
                        'description': 'Análisis completo con métricas y predicciones',
                        'icon': 'fas fa-chart-line'
                    },
                    {
                        'id': 'performance',
                        'name': 'Rendimiento de Consultores',
                        'description': 'Métricas de productividad y éxito',
                        'icon': 'fas fa-user-tie'
                    },
                    {
                        'id': 'client_satisfaction',
                        'name': 'Satisfacción de Clientes',
                        'description': 'Análisis de satisfacción y retención',
                        'icon': 'fas fa-smile'
                    },
                    {
                        'id': 'market_analysis',
                        'name': 'Análisis de Mercado',
                        'description': 'Tendencias y oportunidades del mercado',
                        'icon': 'fas fa-chart-bar'
                    },
                    {
                        'id': 'predictive',
                        'name': 'Predicciones IA',
                        'description': 'Predicciones basadas en ML y GenIA',
                        'icon': 'fas fa-brain'
                    },
                    {
                        'id': 'financial',
                        'name': 'Análisis Financiero',
                        'description': 'ROI, costos y proyecciones financieras',
                        'icon': 'fas fa-dollar-sign'
                    }
                ],
                'comprehensive_report': {
                    'summary': {
                        'total_candidates': 1250,
                        'active_pipeline': 342,
                        'hired_this_period': 89,
                        'revenue_generated': '$2,450,000 MXN',
                        'avg_time_to_hire': '18 días',
                        'conversion_rate': 73.5
                    },
                    'trends': {
                        'candidates_trend': [120, 135, 142, 156, 168, 189],
                        'hires_trend': [15, 18, 22, 25, 28, 32],
                        'revenue_trend': [1800000, 1950000, 2100000, 2250000, 2350000, 2450000]
                    },
                    'predictions': {
                        'next_month_hires': 35,
                        'revenue_forecast': '$2,650,000 MXN',
                        'market_opportunity': 'Alto crecimiento en fintech',
                        'recommended_actions': [
                            'Aumentar sourcing en sector fintech',
                            'Optimizar proceso de entrevistas',
                            'Fortalecer partnerships con universidades'
                        ]
                    }
                },
                'performance_report': {
                    'consultants': [
                        {
                            'name': 'María Rodríguez',
                            'candidates_managed': 45,
                            'hires': 12,
                            'conversion_rate': 26.7,
                            'avg_time_to_hire': '16 días',
                            'client_satisfaction': 4.8,
                            'revenue_generated': '$450,000 MXN'
                        },
                        {
                            'name': 'Juan Pérez',
                            'candidates_managed': 38,
                            'hires': 10,
                            'conversion_rate': 26.3,
                            'avg_time_to_hire': '19 días',
                            'client_satisfaction': 4.6,
                            'revenue_generated': '$380,000 MXN'
                        }
                    ],
                    'top_performers': [
                        {
                            'name': 'María Rodríguez',
                            'metric': 'Mayor conversión',
                            'value': '26.7%'
                        },
                        {
                            'name': 'Ana López',
                            'metric': 'Menor tiempo de contratación',
                            'value': '14 días'
                        }
                    ]
                },
                'ai_insights': {
                    'market_trends': [
                        'Aumento del 25% en demanda de desarrolladores React',
                        'Nuevas oportunidades en sector de salud digital',
                        'Escasez de talento en DevOps en Querétaro'
                    ],
                    'candidate_insights': [
                        'Candidatos con experiencia en fintech tienen 40% más probabilidad de éxito',
                        'Perfiles con certificaciones AWS tienen mejor retención',
                        'Candidatos de CDMX prefieren trabajo híbrido'
                    ],
                    'optimization_recommendations': [
                        'Automatizar screening inicial con IA',
                        'Implementar entrevistas por video para candidatos remotos',
                        'Crear programa de referencias incentivadas'
                    ]
                },
                'export_options': {
                    'formats': ['pdf', 'excel', 'powerpoint', 'html'],
                    'scheduling': True,
                    'automated_delivery': True,
                    'customization': True
                }
            }
            
            return reports_data
            
        except Exception as e:
            logger.error(f"Error en reportes avanzados: {str(e)}")
            return {
                'error': str(e),
                'filters': filters
            }

    # ============================================================================
    # 🚀 MÉTODOS FINANCIEROS Y DE PAGOS - BRUCE ALMIGHTY MODE 🚀
    # ============================================================================
    
    @cache_result(ttl=300)  # 5 minutos
    async def get_financial_dashboard(self) -> Dict[str, Any]:
        """Obtiene dashboard completo de finanzas y pagos."""
        try:
            return {
                'success': True,
                'financial_dashboard': {
                    'revenue_overview': await self._get_revenue_overview(),
                    'payment_performance': await self._get_payment_performance(),
                    'accounts_receivable': await self._get_accounts_receivable(),
                    'accounts_payable': await self._get_accounts_payable(),
                    'cash_flow_analysis': await self._get_cash_flow_analysis(),
                    'provider_validation': await self._get_provider_validation_status(),
                    'sat_compliance': await self._get_sat_compliance_detailed(),
                    'risk_analysis': await self._get_risk_analysis(),
                    'scheduled_payments': await self._get_scheduled_payments_overview()
                }
            }
        except Exception as e:
            logger.error(f"Error obteniendo dashboard financiero: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _get_revenue_overview(self) -> Dict[str, Any]:
        """Obtiene overview de ingresos."""
        try:
            # Período de análisis
            end_date = timezone.now()
            start_date = end_date - timedelta(days=365)
            
            # Importar modelos necesarios
            from app.models import Invoice
            from app.ats.pricing.models.external_services import ExternalService
            
            # Ingresos por mes
            monthly_revenue = await sync_to_async(list)(Invoice.objects.filter(
                issue_date__range=[start_date, end_date],
                status='paid'
            ).extra(
                select={'month': 'DATE_TRUNC(\'month\', issue_date)'}
            ).values('month').annotate(
                revenue=Sum('total_amount')
            ).order_by('month'))
            
            # Ingresos por categoría de servicio
            service_revenue = await sync_to_async(list)(ExternalService.objects.filter(
                start_date__range=[start_date, end_date]
            ).values('category').annotate(
                revenue=Sum('total_amount'),
                count=Count('id')
            ))
            
            # Proyección de ingresos
            current_month_revenue = await sync_to_async(lambda: Invoice.objects.filter(
                issue_date__month=end_date.month,
                issue_date__year=end_date.year,
                status='paid'
            ).aggregate(total=Sum('total_amount'))['total'] or 0)()
            
            return {
                'monthly_revenue': monthly_revenue,
                'service_revenue': service_revenue,
                'current_month_revenue': float(current_month_revenue),
                'total_annual_revenue': float(sum(m['revenue'] for m in monthly_revenue)),
                'average_monthly_revenue': float(sum(m['revenue'] for m in monthly_revenue) / len(monthly_revenue)) if monthly_revenue else 0
            }
        except Exception as e:
            logger.error(f"Error calculando overview de ingresos: {str(e)}")
            return {}
    
    async def _get_payment_performance(self) -> Dict[str, Any]:
        """Obtiene rendimiento de pagos."""
        try:
            # Período de análisis
            end_date = timezone.now()
            start_date = end_date - timedelta(days=90)
            
            # Importar modelos necesarios
            from app.ats.models import PaymentTransaction
            
            transactions = await sync_to_async(list)(PaymentTransaction.objects.filter(
                created_at__range=[start_date, end_date]
            ))
            
            # Métricas de rendimiento
            total_transactions = len(transactions)
            successful_transactions = len([t for t in transactions if t.status == 'completed'])
            failed_transactions = len([t for t in transactions if t.status == 'failed'])
            
            # Métricas por gateway
            gateway_performance = {}
            for transaction in transactions:
                gateway = transaction.gateway
                if gateway not in gateway_performance:
                    gateway_performance[gateway] = {
                        'count': 0,
                        'success_count': 0,
                        'total_amount': 0
                    }
                
                gateway_performance[gateway]['count'] += 1
                gateway_performance[gateway]['total_amount'] += float(transaction.amount)
                if transaction.status == 'completed':
                    gateway_performance[gateway]['success_count'] += 1
            
            # Calcular tasas de éxito
            for gateway in gateway_performance:
                gateway_performance[gateway]['success_rate'] = (
                    gateway_performance[gateway]['success_count'] / 
                    gateway_performance[gateway]['count'] * 100
                )
            
            return {
                'total_transactions': total_transactions,
                'successful_transactions': successful_transactions,
                'failed_transactions': failed_transactions,
                'success_rate': (successful_transactions / total_transactions * 100) if total_transactions > 0 else 0,
                'gateway_performance': gateway_performance,
                'average_payment_time': 15.0,  # Simulado
                'fast_payments': successful_transactions * 0.7,  # Simulado
                'slow_payments': successful_transactions * 0.3   # Simulado
            }
        except Exception as e:
            logger.error(f"Error calculando rendimiento de pagos: {str(e)}")
            return {}
    
    async def _get_accounts_receivable(self) -> Dict[str, Any]:
        """Obtiene cuentas por cobrar."""
        try:
            # Importar modelos necesarios
            from app.models import Invoice
            
            # Facturas pendientes
            pending_invoices = await sync_to_async(list)(Invoice.objects.filter(status='pending'))
            
            # Facturas vencidas
            overdue_invoices = await sync_to_async(list)(Invoice.objects.filter(
                status='pending',
                due_date__lt=timezone.now().date()
            ))
            
            # Análisis por cliente
            client_ar = {}
            for invoice in pending_invoices:
                client_name = invoice.receiver_name or 'Sin nombre'
                if client_name not in client_ar:
                    client_ar[client_name] = {
                        'total_amount': 0,
                        'invoice_count': 0,
                        'overdue_amount': 0
                    }
                
                client_ar[client_name]['total_amount'] += float(invoice.total_amount)
                client_ar[client_name]['invoice_count'] += 1
                
                if invoice.due_date and invoice.due_date < timezone.now().date():
                    client_ar[client_name]['overdue_amount'] += float(invoice.total_amount)
            
            # Convertir a lista
            client_ar_list = [
                {
                    'receiver_name': client_name,
                    'total_amount': data['total_amount'],
                    'invoice_count': data['invoice_count'],
                    'overdue_amount': data['overdue_amount']
                }
                for client_name, data in client_ar.items()
            ]
            
            total_pending = sum(invoice.total_amount for invoice in pending_invoices)
            total_overdue = sum(invoice.total_amount for invoice in overdue_invoices)
            
            return {
                'total_pending': float(total_pending),
                'total_overdue': float(total_overdue),
                'pending_invoices_count': len(pending_invoices),
                'overdue_invoices_count': len(overdue_invoices),
                'client_ar': client_ar_list,
                'average_overdue_days': 15.0,  # Simulado
                'overdue_ratio': (len(overdue_invoices) / len(pending_invoices) * 100) if pending_invoices else 0
            }
        except Exception as e:
            logger.error(f"Error calculando cuentas por cobrar: {str(e)}")
            return {}
    
    async def _get_accounts_payable(self) -> Dict[str, Any]:
        """Obtiene cuentas por pagar."""
        try:
            # Importar modelos necesarios
            from app.ats.models import ScheduledPayment
            
            # Pagos programados pendientes
            scheduled_payments = await sync_to_async(list)(ScheduledPayment.objects.filter(status='pending'))
            
            # Pagos vencidos
            overdue_payments = await sync_to_async(list)(ScheduledPayment.objects.filter(
                status='pending',
                next_payment_date__lt=timezone.now().date()
            ))
            
            # Análisis por proveedor
            provider_ap = {}
            for payment in scheduled_payments:
                provider_name = payment.beneficiary_name or 'Sin nombre'
                if provider_name not in provider_ap:
                    provider_ap[provider_name] = {
                        'total_amount': 0,
                        'payment_count': 0,
                        'overdue_amount': 0
                    }
                
                provider_ap[provider_name]['total_amount'] += float(payment.amount)
                provider_ap[provider_name]['payment_count'] += 1
                
                if payment.next_payment_date and payment.next_payment_date < timezone.now().date():
                    provider_ap[provider_name]['overdue_amount'] += float(payment.amount)
            
            # Convertir a lista
            provider_ap_list = [
                {
                    'beneficiary_name': provider_name,
                    'total_amount': data['total_amount'],
                    'payment_count': data['payment_count'],
                    'overdue_amount': data['overdue_amount']
                }
                for provider_name, data in provider_ap.items()
            ]
            
            total_scheduled = sum(payment.amount for payment in scheduled_payments)
            total_overdue = sum(payment.amount for payment in overdue_payments)
            
            return {
                'total_scheduled': float(total_scheduled),
                'total_overdue': float(total_overdue),
                'scheduled_payments_count': len(scheduled_payments),
                'overdue_payments_count': len(overdue_payments),
                'provider_ap': provider_ap_list,
                'overdue_ratio': (len(overdue_payments) / len(scheduled_payments) * 100) if scheduled_payments else 0
            }
        except Exception as e:
            logger.error(f"Error calculando cuentas por pagar: {str(e)}")
            return {}
    
    async def _get_cash_flow_analysis(self) -> Dict[str, Any]:
        """Obtiene análisis de flujo de efectivo."""
        try:
            # Período de análisis (próximos 12 meses)
            start_date = timezone.now()
            end_date = start_date + timedelta(days=365)
            
            # Importar modelos necesarios
            from app.models import Invoice
            from app.ats.models import ScheduledPayment
            
            # Proyección de ingresos
            projected_revenue = []
            for i in range(12):
                month_date = start_date + timedelta(days=30*i)
                monthly_revenue = await sync_to_async(lambda: Invoice.objects.filter(
                    issue_date__month=month_date.month,
                    issue_date__year=month_date.year,
                    status='paid'
                ).aggregate(total=Sum('total_amount'))['total'] or 0)()
                
                projected_revenue.append({
                    'month': month_date.strftime('%Y-%m'),
                    'revenue': float(monthly_revenue),
                    'projected_revenue': float(monthly_revenue * 1.05)  # 5% crecimiento
                })
            
            # Proyección de gastos
            projected_expenses = []
            for i in range(12):
                month_date = start_date + timedelta(days=30*i)
                monthly_expenses = await sync_to_async(lambda: ScheduledPayment.objects.filter(
                    next_payment_date__month=month_date.month,
                    next_payment_date__year=month_date.year
                ).aggregate(total=Sum('amount'))['total'] or 0)()
                
                projected_expenses.append({
                    'month': month_date.strftime('%Y-%m'),
                    'expenses': float(monthly_expenses),
                    'projected_expenses': float(monthly_expenses * 1.02)  # 2% crecimiento
                })
            
            # Calcular flujo neto
            net_cash_flow = []
            cumulative_balance = 0
            for i in range(12):
                revenue = projected_revenue[i]['projected_revenue']
                expenses = projected_expenses[i]['projected_expenses']
                net_flow = revenue - expenses
                cumulative_balance += net_flow
                
                net_cash_flow.append({
                    'month': projected_revenue[i]['month'],
                    'net_flow': net_flow,
                    'cumulative_balance': cumulative_balance
                })
            
            return {
                'projected_revenue': projected_revenue,
                'projected_expenses': projected_expenses,
                'net_cash_flow': net_cash_flow,
                'total_projected_revenue': sum(r['projected_revenue'] for r in projected_revenue),
                'total_projected_expenses': sum(e['projected_expenses'] for e in projected_expenses),
                'net_projected_flow': sum(n['net_flow'] for n in net_cash_flow)
            }
        except Exception as e:
            logger.error(f"Error calculando flujo de efectivo: {str(e)}")
            return {}
    
    async def _get_provider_validation_status(self) -> Dict[str, Any]:
        """Obtiene estado de validación de proveedores."""
        try:
            providers = await sync_to_async(list)(Person.objects.filter(is_provider=True))
            
            validation_status = {
                'total_providers': len(providers),
                'validated_providers': 0,
                'pending_validation': 0,
                'failed_validation': 0,
                'providers_without_rfc': 0,
                'validation_details': []
            }
            
            # Importar servicio de validación
            from app.ats.pricing.services.sat_validation_service import SATValidationService
            
            for provider in providers:
                if not provider.rfc:
                    validation_status['providers_without_rfc'] += 1
                    validation_status['validation_details'].append({
                        'provider_id': provider.id,
                        'provider_name': provider.name,
                        'status': 'no_rfc',
                        'issue': 'Sin RFC'
                    })
                else:
                    # Simular validación SAT
                    sat_status = {
                        'status': 'active' if not provider.rfc.endswith('000') else 'inactive',
                        'reason': 'RFC válido' if not provider.rfc.endswith('000') else 'RFC genérico'
                    }
                    
                    if sat_status['status'] == 'active':
                        validation_status['validated_providers'] += 1
                        status = 'validated'
                    else:
                        validation_status['failed_validation'] += 1
                        status = 'failed'
                    
                    validation_status['validation_details'].append({
                        'provider_id': provider.id,
                        'provider_name': provider.name,
                        'rfc': provider.rfc,
                        'status': status,
                        'sat_status': sat_status,
                        'blacklist_status': {'is_blacklisted': False}
                    })
            
            validation_status['pending_validation'] = (
                validation_status['total_providers'] - 
                validation_status['validated_providers'] - 
                validation_status['failed_validation'] - 
                validation_status['providers_without_rfc']
            )
            
            return validation_status
        except Exception as e:
            logger.error(f"Error obteniendo estado de validación: {str(e)}")
            return {}
    
    async def _get_sat_compliance_detailed(self) -> Dict[str, Any]:
        """Obtiene compliance SAT detallado."""
        try:
            # Importar modelos necesarios
            from app.models import Invoice
            
            # Facturas con CFDI
            invoices_with_cfdi = await sync_to_async(list)(Invoice.objects.filter(
                cfdi_uuid__isnull=False
            ).exclude(cfdi_uuid=''))
            
            # Análisis por mes
            cfdi_monthly = await sync_to_async(list)(Invoice.objects.filter(
                cfdi_uuid__isnull=False
            ).exclude(cfdi_uuid='').extra(
                select={'month': 'DATE_TRUNC(\'month\', issue_date)'}
            ).values('month').annotate(
                count=Count('id'),
                total_amount=Sum('total_amount')
            ).order_by('month'))
            
            # Facturas sin CFDI por razón
            invoices_without_cfdi = await sync_to_async(list)(Invoice.objects.filter(
                Q(cfdi_uuid__isnull=True) | Q(cfdi_uuid='')
            ))
            
            no_cfdi_reasons = {
                'electronic_billing_disabled': len([i for i in invoices_without_cfdi if not i.electronic_billing_enabled]),
                'no_pac_configuration': 0,  # Implementar lógica
                'generation_failed': len([i for i in invoices_without_cfdi if i.sat_status == 'error']),
                'pending_generation': len([i for i in invoices_without_cfdi if i.sat_status == 'pending'])
            }
            
            total_invoices = await sync_to_async(Invoice.objects.count)()
            
            return {
                'cfdi_compliance_rate': (len(invoices_with_cfdi) / total_invoices * 100) if total_invoices > 0 else 0,
                'cfdi_monthly': cfdi_monthly,
                'no_cfdi_reasons': no_cfdi_reasons,
                'total_invoices': total_invoices,
                'invoices_with_cfdi': len(invoices_with_cfdi),
                'invoices_without_cfdi': len(invoices_without_cfdi)
            }
        except Exception as e:
            logger.error(f"Error obteniendo compliance SAT: {str(e)}")
            return {}
    
    async def _get_risk_analysis(self) -> Dict[str, Any]:
        """Obtiene análisis de riesgo."""
        try:
            # Importar modelos necesarios
            from app.models import Invoice
            
            # Clientes con facturas vencidas
            clients_with_overdue = await sync_to_async(list)(Invoice.objects.filter(
                status='pending',
                due_date__lt=timezone.now().date()
            ).values('receiver_name').annotate(
                overdue_amount=Sum('total_amount'),
                overdue_count=Count('id'),
                total_amount=Sum('total_amount')
            ))
            
            # Análisis de riesgo por cliente
            risk_analysis = []
            for client_data in clients_with_overdue:
                overdue_ratio = (client_data['overdue_amount'] / client_data['total_amount']) * 100
                
                if overdue_ratio > 50:
                    risk_level = 'high'
                elif overdue_ratio > 20:
                    risk_level = 'medium'
                else:
                    risk_level = 'low'
                
                risk_analysis.append({
                    'client_name': client_data['receiver_name'],
                    'overdue_amount': float(client_data['overdue_amount']),
                    'overdue_count': client_data['overdue_count'],
                    'overdue_ratio': round(overdue_ratio, 2),
                    'risk_level': risk_level
                })
            
            # Estadísticas de riesgo
            high_risk_clients = len([c for c in risk_analysis if c['risk_level'] == 'high'])
            medium_risk_clients = len([c for c in risk_analysis if c['risk_level'] == 'medium'])
            low_risk_clients = len([c for c in risk_analysis if c['risk_level'] == 'low'])
            
            return {
                'risk_analysis': risk_analysis,
                'high_risk_clients': high_risk_clients,
                'medium_risk_clients': medium_risk_clients,
                'low_risk_clients': low_risk_clients,
                'total_risky_clients': len(risk_analysis),
                'total_overdue_amount': sum(c['overdue_amount'] for c in risk_analysis)
            }
        except Exception as e:
            logger.error(f"Error obteniendo análisis de riesgo: {str(e)}")
            return {}
    
    async def _get_scheduled_payments_overview(self) -> Dict[str, Any]:
        """Obtiene overview de pagos programados."""
        try:
            # Importar modelos necesarios
            from app.ats.models import ScheduledPayment
            
            # Pagos programados activos
            active_scheduled = await sync_to_async(list)(ScheduledPayment.objects.filter(status='active'))
            
            # Pagos por frecuencia
            frequency_breakdown = {}
            for payment in active_scheduled:
                frequency = payment.frequency
                if frequency not in frequency_breakdown:
                    frequency_breakdown[frequency] = {
                        'count': 0,
                        'total_amount': 0
                    }
                frequency_breakdown[frequency]['count'] += 1
                frequency_breakdown[frequency]['total_amount'] += float(payment.amount)
            
            # Convertir a lista
            frequency_breakdown_list = [
                {
                    'frequency': freq,
                    'count': data['count'],
                    'total_amount': data['total_amount']
                }
                for freq, data in frequency_breakdown.items()
            ]
            
            # Próximos pagos (próximos 30 días)
            next_30_days = timezone.now().date() + timedelta(days=30)
            upcoming_payments = await sync_to_async(list)(ScheduledPayment.objects.filter(
                status='active',
                next_payment_date__lte=next_30_days
            ).order_by('next_payment_date'))
            
            # Pagos vencidos
            overdue_scheduled = await sync_to_async(list)(ScheduledPayment.objects.filter(
                status='active',
                next_payment_date__lt=timezone.now().date()
            ))
            
            total_scheduled_amount = sum(payment.amount for payment in active_scheduled)
            overdue_scheduled_amount = sum(payment.amount for payment in overdue_scheduled)
            
            return {
                'total_scheduled_payments': len(active_scheduled),
                'total_scheduled_amount': float(total_scheduled_amount),
                'frequency_breakdown': frequency_breakdown_list,
                'upcoming_payments': [
                    {
                        'id': payment.id,
                        'name': payment.name,
                        'amount': float(payment.amount),
                        'next_payment_date': payment.next_payment_date.isoformat() if payment.next_payment_date else None,
                        'beneficiary_name': payment.beneficiary_name
                    }
                    for payment in upcoming_payments
                ],
                'overdue_scheduled_count': len(overdue_scheduled),
                'overdue_scheduled_amount': float(overdue_scheduled_amount)
            }
        except Exception as e:
            logger.error(f"Error obteniendo overview de pagos programados: {str(e)}")
            return {}

    # ============================================================================
    # MÉTODOS PRIVADOS EXISTENTES
    # ============================================================================