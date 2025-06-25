"""
Dashboard Consolidado para Consultores de Grupo huntRED®

Este módulo proporciona un dashboard completo para consultores con:
- Gestión de candidatos y chatbot
- Métricas de rendimiento personalizadas
- Insights de mercado en tiempo real
- Herramientas de productividad
- Análisis de competencia
- Recomendaciones inteligentes
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum, F
from django.core.cache import cache
from asgiref.sync import sync_to_async

from app.models import (
    Person, Application, Vacante, BusinessUnit, 
    Event, EventParticipant, Interview, ClientFeedback,
    ServiceCalculation, GamificationProfile, ChatState, 
    RecoveryAttempt, ConsultorInteraction
)
from app.ats.integrations.channels.whatsapp import WhatsAppService
from app.ats.analytics.market_analyzer import MarketAnalyzer
from app.ats.analytics.competitor_analyzer import CompetitorAnalyzer
from app.ats.ml.recommendation_engine import RecommendationEngine
from app.ats.utils.cache import cache_result
from app.aura.engine import AuraEngine  # Integración con AURA
from app.aura.insights import AuraInsights  # Insights de AURA

import logging
logger = logging.getLogger(__name__)

class ConsultantDashboard:
    """
    Dashboard consolidado para consultores con todas las funcionalidades.
    
    Combina:
    - Gestión de candidatos y chatbot (funcionalidad original)
    - Métricas de rendimiento personalizadas
    - Insights de mercado en tiempo real
    - Recomendaciones inteligentes
    - Análisis predictivo con AURA
    """
    
    def __init__(self, consultant_id: str, business_unit: Optional[BusinessUnit] = None):
        self.consultant_id = consultant_id
        self.business_unit = business_unit
        self.whatsapp_service = WhatsAppService()
        self.market_analyzer = MarketAnalyzer()
        self.competitor_analyzer = CompetitorAnalyzer()
        self.recommendation_engine = RecommendationEngine()
        self.aura_engine = AuraEngine()  # Motor de AURA
        self.aura_insights = AuraInsights()  # Insights de AURA
        
    # ============================================================================
    # FUNCIONALIDADES ORIGINALES (Gestión de Candidatos y Chatbot)
    # ============================================================================
    
    @sync_to_async
    def get_candidates_by_status(self, status: str = None, business_unit: str = None) -> List[Dict]:
        """
        Obtiene candidatos filtrados por estado y unidad de negocio.
        
        Args:
            status: Estado del candidato (opcional)
            business_unit: Unidad de negocio (opcional)
            
        Returns:
            Lista de diccionarios con información de los candidatos
        """
        try:
            query = ChatState.objects.all()
            
            if status:
                query = query.filter(state=status)
                
            if business_unit:
                query = query.filter(user__business_unit__name=business_unit)
            
            # Obtener los últimos 50 candidatos ordenados por última interacción
            candidates = query.select_related('user').order_by('-last_interaction')[:50]
            
            return [{
                'id': str(candidate.user.id),
                'name': candidate.user.get_full_name() or 'Sin nombre',
                'phone': candidate.user.phone,
                'email': candidate.user.email,
                'state': candidate.state,
                'last_interaction': candidate.last_interaction,
                'business_unit': candidate.user.business_unit.name if candidate.user.business_unit else 'Sin unidad'
            } for candidate in candidates]
            
        except Exception as e:
            logger.error(f"Error obteniendo candidatos: {str(e)}")
            return []
    
    @sync_to_async
    def get_recovery_attempts(self, days: int = 7) -> List[Dict]:
        """
        Obtiene los intentos de recuperación recientes.
        
        Args:
            days: Número de días hacia atrás para buscar
            
        Returns:
            Lista de intentos de recuperación
        """
        try:
            since = timezone.now() - timedelta(days=days)
            attempts = RecoveryAttempt.objects.filter(
                last_attempt__gte=since
            ).select_related('user').order_by('-last_attempt')
            
            return [{
                'user_id': str(attempt.user.id),
                'user_name': attempt.user.get_full_name() or 'Sin nombre',
                'attempts': attempt.attempts,
                'status': attempt.status,
                'last_attempt': attempt.last_attempt,
                'first_attempt': attempt.first_attempt
            } for attempt in attempts]
            
        except Exception as e:
            logger.error(f"Error obteniendo intentos de recuperación: {str(e)}")
            return []
    
    async def contact_candidate(self, candidate_id: str, message: str) -> bool:
        """
        Envía un mensaje directo a un candidato.
        
        Args:
            candidate_id: ID del candidato
            message: Mensaje a enviar
            
        Returns:
            bool: True si el mensaje se envió correctamente
        """
        try:
            # Obtener información del candidato
            candidate = await sync_to_async(Person.objects.get)(id=candidate_id)
            
            if not candidate.phone:
                logger.error(f"El candidato {candidate_id} no tiene número de teléfono")
                return False
            
            # Enviar mensaje a través del servicio de WhatsApp
            success = await self.whatsapp_service.send_message(
                to=candidate.phone,
                message=f"🤖 Mensaje de tu consultor huntRED:\n\n{message}"
            )
            
            if success:
                # Registrar la interacción
                await sync_to_async(self._log_consultant_interaction)(
                    consultor_id=self.consultant_id,
                    candidate_id=candidate_id,
                    action='direct_message',
                    details={'message': message[:500]}  # Limitar tamaño del mensaje
                )
            
            return success
            
        except Person.DoesNotExist:
            logger.error(f"Candidato {candidate_id} no encontrado")
            return False
        except Exception as e:
            logger.error(f"Error contactando al candidato {candidate_id}: {str(e)}")
            return False
    
    @sync_to_async
    def reset_conversation(self, candidate_id: str) -> bool:
        """
        Reinicia la conversación con un candidato.
        
        Args:
            candidate_id: ID del candidato
            
        Returns:
            bool: True si se reinició correctamente
        """
        try:
            # Obtener el estado del chat del candidato
            chat_state = ChatState.objects.get(user_id=candidate_id)
            
            # Reiniciar el estado a uno inicial
            chat_state.state = 'welcome'
            chat_state.context = {}
            chat_state.save()
            
            # Registrar la interacción
            self._log_consultant_interaction(
                consultor_id=self.consultant_id,
                candidate_id=candidate_id,
                action='reset_conversation',
                details={'previous_state': chat_state.state}
            )
            
            return True
            
        except ChatState.DoesNotExist:
            logger.error(f"No se encontró estado de chat para el candidato {candidate_id}")
            return False
        except Exception as e:
            logger.error(f"Error reiniciando conversación para {candidate_id}: {str(e)}")
            return False
    
    @sync_to_async
    def get_candidate_status(self, candidate_id: str) -> Optional[Dict]:
        """
        Obtiene el estado actual de un candidato.
        
        Args:
            candidate_id: ID del candidato
            
        Returns:
            Dict con el estado del candidato o None si no se encuentra
        """
        try:
            chat_state = ChatState.objects.get(user_id=candidate_id)
            return {
                'state': chat_state.state,
                'context': chat_state.context,
                'last_interaction': chat_state.last_interaction
            }
        except ChatState.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error obteniendo estado del candidato {candidate_id}: {str(e)}")
            return None
    
    def _log_consultant_interaction(self, consultor_id: str, candidate_id: str, action: str, details: dict):
        """
        Registra una interacción del consultor con un candidato.
        
        Args:
            consultor_id: ID del consultor
            candidate_id: ID del candidato
            action: Acción realizada (direct_message, reset_conversation, etc.)
            details: Detalles adicionales de la interacción
        """
        try:
            ConsultorInteraction.objects.create(
                consultor_id=consultor_id,
                candidate_id=candidate_id,
                action=action,
                details=details
            )
        except Exception as e:
            logger.error(f"Error registrando interacción: {str(e)}")
    
    # ============================================================================
    # NUEVAS FUNCIONALIDADES (Métricas y Analytics Avanzados)
    # ============================================================================
    
    @cache_result(ttl=300)  # 5 minutos
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Obtiene todos los datos del dashboard del consultor."""
        return {
            'candidate_management': await self.get_candidate_management_data(),
            'performance_metrics': await self.get_performance_metrics(),
            'market_insights': await self.get_market_insights(),
            'productivity_analytics': await self.get_productivity_analytics(),
            'competitor_analysis': await self.get_competitor_analysis(),
            'recommendations': await self.get_recommendations(),
            'recent_activities': await self.get_recent_activities(),
            'upcoming_tasks': await self.get_upcoming_tasks(),
            'aura_insights': await self.get_aura_insights(),  # Nuevo: Insights de AURA
            'predictive_analytics': await self.get_predictive_analytics()  # Nuevo: Analytics predictivo
        }
    
    async def get_candidate_management_data(self) -> Dict[str, Any]:
        """Obtiene datos de gestión de candidatos."""
        try:
            # Candidatos por estado
            candidates_by_status = await self.get_candidates_by_status()
            
            # Intentos de recuperación
            recovery_attempts = await self.get_recovery_attempts()
            
            # Estadísticas generales
            total_candidates = len(candidates_by_status)
            active_candidates = len([c for c in candidates_by_status if c['state'] != 'inactive'])
            recovery_needed = len(recovery_attempts)
            
            return {
                'total_candidates': total_candidates,
                'active_candidates': active_candidates,
                'recovery_needed': recovery_needed,
                'candidates_by_status': candidates_by_status,
                'recovery_attempts': recovery_attempts
            }
        except Exception as e:
            logger.error(f"Error obteniendo datos de gestión de candidatos: {str(e)}")
            return {}
    
    @cache_result(ttl=600)  # 10 minutos
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Métricas de rendimiento del consultor."""
        now = timezone.now()
        last_month = now - timedelta(days=30)
        
        # Obtener aplicaciones del consultor
        consultant_applications = Application.objects.filter(
            consultant_id=self.consultant_id,
            created_at__gte=last_month
        )
        
        # Métricas básicas
        total_applications = consultant_applications.count()
        successful_placements = consultant_applications.filter(
            status='hired'
        ).count()
        
        # Tiempo promedio de contratación
        avg_time_to_hire = consultant_applications.filter(
            status='hired'
        ).aggregate(
            avg_days=Avg(F('updated_at') - F('created_at'))
        )['avg_days'] or timedelta(days=0)
        
        # Tasa de conversión
        conversion_rate = (successful_placements / total_applications * 100) if total_applications > 0 else 0
        
        # Ingresos generados
        revenue_generated = ServiceCalculation.objects.filter(
            application__consultant_id=self.consultant_id,
            created_at__gte=last_month
        ).aggregate(total=Sum('total_fee'))['total'] or 0
        
        # Comparación con equipo
        team_metrics = await self._get_team_comparison()
        
        # Tendencias
        trends = await self._get_performance_trends()
        
        return {
            'total_applications': total_applications,
            'successful_placements': successful_placements,
            'conversion_rate': round(conversion_rate, 2),
            'avg_time_to_hire_days': avg_time_to_hire.days,
            'revenue_generated': revenue_generated,
            'team_comparison': team_metrics,
            'trends': trends,
            'performance_score': self._calculate_performance_score(
                conversion_rate, avg_time_to_hire.days, revenue_generated
            )
        }
    
    @cache_result(ttl=1800)  # 30 minutos
    async def get_market_insights(self) -> Dict[str, Any]:
        """Insights de mercado en tiempo real."""
        # Análisis de mercado por industria
        industry_insights = await self.market_analyzer.get_industry_insights()
        
        # Tendencias de demanda
        demand_trends = await self.market_analyzer.get_demand_trends()
        
        # Análisis de salarios
        salary_analysis = await self.market_analyzer.get_salary_analysis()
        
        # Oportunidades emergentes
        emerging_opportunities = await self.market_analyzer.get_emerging_opportunities()
        
        return {
            'industry_insights': industry_insights,
            'demand_trends': demand_trends,
            'salary_analysis': salary_analysis,
            'emerging_opportunities': emerging_opportunities,
            'market_score': self._calculate_market_score(industry_insights, demand_trends)
        }
    
    @cache_result(ttl=900)  # 15 minutos
    async def get_productivity_analytics(self) -> Dict[str, Any]:
        """Análisis de productividad del consultor."""
        now = timezone.now()
        last_week = now - timedelta(days=7)
        
        # Actividades diarias
        daily_activities = await self._get_daily_activities(last_week)
        
        # Tiempo de respuesta
        response_times = await self._get_response_times()
        
        # Eficiencia por canal
        channel_efficiency = await self._get_channel_efficiency()
        
        # Tareas completadas
        completed_tasks = await self._get_completed_tasks()
        
        # Métricas de engagement
        engagement_metrics = await self._get_engagement_metrics()
        
        return {
            'daily_activities': daily_activities,
            'response_times': response_times,
            'channel_efficiency': channel_efficiency,
            'completed_tasks': completed_tasks,
            'engagement_metrics': engagement_metrics,
            'productivity_score': self._calculate_productivity_score(
                daily_activities, response_times, channel_efficiency
            )
        }
    
    @cache_result(ttl=3600)  # 1 hora
    async def get_competitor_analysis(self) -> Dict[str, Any]:
        """Análisis de competencia."""
        # Análisis de competidores directos
        direct_competitors = await self.competitor_analyzer.get_direct_competitors()
        
        # Comparación de servicios
        service_comparison = await self.competitor_analyzer.compare_services()
        
        # Análisis de precios
        pricing_analysis = await self.competitor_analyzer.analyze_pricing()
        
        # Ventajas competitivas
        competitive_advantages = await self.competitor_analyzer.get_advantages()
        
        return {
            'direct_competitors': direct_competitors,
            'service_comparison': service_comparison,
            'pricing_analysis': pricing_analysis,
            'competitive_advantages': competitive_advantages,
            'threat_level': self._calculate_threat_level(direct_competitors, pricing_analysis)
        }
    
    @cache_result(ttl=1200)  # 20 minutos
    async def get_recommendations(self) -> List[Dict[str, Any]]:
        """Recomendaciones inteligentes para el consultor."""
        recommendations = []
        
        # Obtener métricas actuales
        performance_metrics = await self.get_performance_metrics()
        productivity_analytics = await self.get_productivity_analytics()
        
        # Recomendaciones basadas en rendimiento
        if performance_metrics['conversion_rate'] < 15:
            recommendations.append({
                'type': 'performance',
                'priority': 'high',
                'title': 'Mejorar tasa de conversión',
                'description': 'Tu tasa de conversión está por debajo del promedio del equipo. Considera mejorar el proceso de screening.',
                'action': 'Revisar criterios de evaluación',
                'impact': 'Alto',
                'effort': 'Medio'
            })
        
        # Recomendaciones basadas en productividad
        if productivity_analytics['response_times']['avg_response_time'] > 24:
            recommendations.append({
                'type': 'productivity',
                'priority': 'medium',
                'title': 'Reducir tiempo de respuesta',
                'description': 'El tiempo promedio de respuesta es superior a 24 horas. Considera automatizar respuestas iniciales.',
                'action': 'Configurar respuestas automáticas',
                'impact': 'Medio',
                'effort': 'Bajo'
            })
        
        # Recomendaciones de mercado
        market_insights = await self.get_market_insights()
        if market_insights['emerging_opportunities']:
            recommendations.append({
                'type': 'market',
                'priority': 'high',
                'title': 'Oportunidades emergentes',
                'description': f"Hay {len(market_insights['emerging_opportunities'])} oportunidades emergentes en el mercado.",
                'action': 'Explorar nuevas industrias',
                'impact': 'Alto',
                'effort': 'Alto'
            })
        
        return recommendations
    
    @cache_result(ttl=300)  # 5 minutos
    async def get_recent_activities(self) -> List[Dict[str, Any]]:
        """Actividades recientes del consultor."""
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        
        activities = []
        
        # Aplicaciones recientes
        recent_applications = Application.objects.filter(
            consultant_id=self.consultant_id,
            created_at__gte=last_24h
        ).select_related('candidate', 'vacancy')[:5]
        
        for app in recent_applications:
            activities.append({
                'type': 'application',
                'timestamp': app.created_at,
                'title': f'Nueva aplicación de {app.candidate.name}',
                'description': f'Para la posición: {app.vacancy.titulo}',
                'status': app.status,
                'priority': 'medium'
            })
        
        # Entrevistas programadas
        recent_interviews = Interview.objects.filter(
            consultant_id=self.consultant_id,
            scheduled_at__gte=last_24h
        ).select_related('candidate', 'vacancy')[:5]
        
        for interview in recent_interviews:
            activities.append({
                'type': 'interview',
                'timestamp': interview.scheduled_at,
                'title': f'Entrevista programada con {interview.candidate.name}',
                'description': f'Para: {interview.vacancy.titulo}',
                'status': interview.status,
                'priority': 'high'
            })
        
        # Feedback de clientes
        recent_feedback = ClientFeedback.objects.filter(
            consultant_id=self.consultant_id,
            created_at__gte=last_24h
        )[:3]
        
        for feedback in recent_feedback:
            activities.append({
                'type': 'feedback',
                'timestamp': feedback.created_at,
                'title': f'Feedback de cliente recibido',
                'description': f'Puntuación: {feedback.overall_rating}/5',
                'status': 'completed',
                'priority': 'medium'
            })
        
        # Ordenar por timestamp
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        return activities[:10]
    
    @cache_result(ttl=300)  # 5 minutos
    async def get_upcoming_tasks(self) -> List[Dict[str, Any]]:
        """Tareas próximas del consultor."""
        now = timezone.now()
        next_7_days = now + timedelta(days=7)
        
        tasks = []
        
        # Entrevistas próximas
        upcoming_interviews = Interview.objects.filter(
            consultant_id=self.consultant_id,
            scheduled_at__gte=now,
            scheduled_at__lte=next_7_days,
            status='scheduled'
        ).select_related('candidate', 'vacancy')
        
        for interview in upcoming_interviews:
            tasks.append({
                'type': 'interview',
                'due_date': interview.scheduled_at,
                'title': f'Entrevista con {interview.candidate.name}',
                'description': f'Posición: {interview.vacancy.titulo}',
                'priority': 'high',
                'estimated_duration': '60 min'
            })
        
        # Seguimientos pendientes
        pending_followups = Application.objects.filter(
            consultant_id=self.consultant_id,
            status='in_progress',
            updated_at__lte=now - timedelta(days=3)
        ).select_related('candidate', 'vacancy')[:5]
        
        for app in pending_followups:
            tasks.append({
                'type': 'followup',
                'due_date': now + timedelta(days=1),
                'title': f'Seguimiento: {app.candidate.name}',
                'description': f'Estado: {app.status} - {app.vacancy.titulo}',
                'priority': 'medium',
                'estimated_duration': '15 min'
            })
        
        # Ordenar por fecha de vencimiento
        tasks.sort(key=lambda x: x['due_date'])
        return tasks[:10]
    
    # Métodos auxiliares privados
    
    async def _get_team_comparison(self) -> Dict[str, Any]:
        """Comparación con el equipo."""
        # Implementar lógica de comparación con equipo
        return {
            'team_avg_conversion': 18.5,
            'team_avg_time_to_hire': 12,
            'team_avg_revenue': 25000,
            'consultant_rank': 3,
            'team_size': 8
        }
    
    async def _get_performance_trends(self) -> Dict[str, Any]:
        """Tendencias de rendimiento."""
        # Implementar análisis de tendencias
        return {
            'conversion_trend': 'up',
            'time_to_hire_trend': 'down',
            'revenue_trend': 'up',
            'growth_rate': 12.5
        }
    
    async def _get_daily_activities(self, since_date: datetime) -> List[Dict[str, Any]]:
        """Actividades diarias del consultor."""
        activities = []
        
        # Obtener aplicaciones por día
        applications_by_day = Application.objects.filter(
            consultant_id=self.consultant_id,
            created_at__gte=since_date
        ).extra(
            select={'day': 'date(created_at)'}
        ).values('day').annotate(count=Count('id'))
        
        for day_data in applications_by_day:
            activities.append({
                'date': day_data['day'],
                'applications': day_data['count'],
                'interviews': 0,  # Implementar lógica
                'placements': 0   # Implementar lógica
            })
        
        return activities
    
    async def _get_response_times(self) -> Dict[str, Any]:
        """Tiempos de respuesta del consultor."""
        # Implementar cálculo de tiempos de respuesta
        return {
            'avg_response_time': 18.5,  # horas
            'response_time_trend': 'improving',
            'best_response_time': 2.3,
            'worst_response_time': 48.0
        }
    
    async def _get_channel_efficiency(self) -> Dict[str, Any]:
        """Eficiencia por canal de comunicación."""
        return {
            'whatsapp': {'efficiency': 85, 'volume': 45},
            'email': {'efficiency': 72, 'volume': 30},
            'phone': {'efficiency': 90, 'volume': 15},
            'linkedin': {'efficiency': 78, 'volume': 10}
        }
    
    async def _get_completed_tasks(self) -> Dict[str, Any]:
        """Tareas completadas."""
        return {
            'total_tasks': 45,
            'completed_tasks': 38,
            'completion_rate': 84.4,
            'tasks_by_type': {
                'interviews': 15,
                'followups': 12,
                'client_meetings': 8,
                'candidate_screening': 3
            }
        }
    
    async def _get_engagement_metrics(self) -> Dict[str, Any]:
        """Métricas de engagement."""
        return {
            'candidate_engagement': 78.5,
            'client_engagement': 85.2,
            'response_rate': 92.1,
            'satisfaction_score': 4.6
        }
    
    def _calculate_performance_score(self, conversion_rate: float, time_to_hire: int, revenue: float) -> float:
        """Calcula score de rendimiento."""
        # Fórmula ponderada
        conversion_score = min(conversion_rate / 20, 1.0) * 40  # 40% peso
        time_score = max(0, (30 - time_to_hire) / 30) * 30      # 30% peso
        revenue_score = min(revenue / 50000, 1.0) * 30          # 30% peso
        
        return round(conversion_score + time_score + revenue_score, 1)
    
    def _calculate_market_score(self, industry_insights: Dict, demand_trends: Dict) -> float:
        """Calcula score de mercado."""
        # Implementar cálculo basado en insights de mercado
        return 78.5
    
    def _calculate_productivity_score(self, daily_activities: List, response_times: Dict, channel_efficiency: Dict) -> float:
        """Calcula score de productividad."""
        # Implementar cálculo basado en métricas de productividad
        return 82.3
    
    def _calculate_threat_level(self, competitors: List, pricing_analysis: Dict) -> str:
        """Calcula nivel de amenaza de competidores."""
        # Implementar lógica de amenaza
        return 'medium'
    
    @cache_result(ttl=1800)  # 30 minutos
    async def get_aura_insights(self) -> Dict[str, Any]:
        """Obtiene insights avanzados de AURA para el consultor."""
        try:
            # Obtener datos del consultor
            consultant = await sync_to_async(Person.objects.get)(id=self.consultant_id)
            
            # Análisis de red del consultor
            network_analysis = await self.aura_engine.analyze_consultant_network(consultant)
            
            # Predicciones de rendimiento
            performance_predictions = await self.aura_engine.predict_consultant_performance(consultant)
            
            # Oportunidades de mercado identificadas por AURA
            market_opportunities = await self.aura_engine.identify_market_opportunities(consultant)
            
            # Análisis de candidatos con alto potencial
            high_potential_candidates = await self.aura_engine.identify_high_potential_candidates(consultant)
            
            # Insights de comportamiento
            behavior_insights = await self.aura_insights.get_consultant_behavior_insights(consultant)
            
            return {
                'network_analysis': network_analysis,
                'performance_predictions': performance_predictions,
                'market_opportunities': market_opportunities,
                'high_potential_candidates': high_potential_candidates,
                'behavior_insights': behavior_insights,
                'aura_score': self._calculate_aura_score(network_analysis, performance_predictions)
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo insights de AURA: {str(e)}")
            return {}
    
    @cache_result(ttl=3600)  # 1 hora
    async def get_predictive_analytics(self) -> Dict[str, Any]:
        """Obtiene analytics predictivos usando AURA."""
        try:
            # Predicción de conversiones
            conversion_predictions = await self.aura_engine.predict_conversion_rates(self.consultant_id)
            
            # Predicción de tiempo de contratación
            time_to_hire_predictions = await self.aura_engine.predict_time_to_hire(self.consultant_id)
            
            # Predicción de ingresos
            revenue_predictions = await self.aura_engine.predict_revenue(self.consultant_id)
            
            # Análisis de riesgo
            risk_analysis = await self.aura_engine.analyze_recruitment_risks(self.consultant_id)
            
            # Recomendaciones predictivas
            predictive_recommendations = await self.aura_engine.generate_predictive_recommendations(self.consultant_id)
            
            return {
                'conversion_predictions': conversion_predictions,
                'time_to_hire_predictions': time_to_hire_predictions,
                'revenue_predictions': revenue_predictions,
                'risk_analysis': risk_analysis,
                'predictive_recommendations': predictive_recommendations,
                'confidence_level': self._calculate_prediction_confidence(conversion_predictions, time_to_hire_predictions)
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo analytics predictivos: {str(e)}")
            return {}
    
    async def get_aura_candidate_analysis(self, candidate_id: str) -> Dict[str, Any]:
        """Obtiene análisis detallado de un candidato usando AURA."""
        try:
            candidate = await sync_to_async(Person.objects.get)(id=candidate_id)
            
            # Análisis de red del candidato
            candidate_network = await self.aura_engine.analyze_candidate_network(candidate)
            
            # Predicción de éxito
            success_prediction = await self.aura_engine.predict_candidate_success(candidate)
            
            # Análisis de fit cultural
            cultural_fit = await self.aura_engine.analyze_cultural_fit(candidate, self.business_unit)
            
            # Recomendaciones personalizadas
            personalized_recommendations = await self.aura_engine.generate_candidate_recommendations(candidate)
            
            return {
                'candidate_network': candidate_network,
                'success_prediction': success_prediction,
                'cultural_fit': cultural_fit,
                'personalized_recommendations': personalized_recommendations,
                'aura_insights': await self.aura_insights.get_candidate_insights(candidate)
            }
            
        except Exception as e:
            logger.error(f"Error analizando candidato con AURA: {str(e)}")
            return {}
    
    async def get_aura_vacancy_analysis(self, vacancy_id: str) -> Dict[str, Any]:
        """Obtiene análisis de una vacante usando AURA."""
        try:
            vacancy = await sync_to_async(Vacante.objects.get)(id=vacancy_id)
            
            # Análisis de mercado para la vacante
            market_analysis = await self.aura_engine.analyze_vacancy_market(vacancy)
            
            # Predicción de dificultad de llenado
            fill_difficulty = await self.aura_engine.predict_fill_difficulty(vacancy)
            
            # Candidatos ideales identificados por AURA
            ideal_candidates = await self.aura_engine.identify_ideal_candidates(vacancy)
            
            # Estrategias de sourcing recomendadas
            sourcing_strategies = await self.aura_engine.recommend_sourcing_strategies(vacancy)
            
            return {
                'market_analysis': market_analysis,
                'fill_difficulty': fill_difficulty,
                'ideal_candidates': ideal_candidates,
                'sourcing_strategies': sourcing_strategies,
                'aura_recommendations': await self.aura_insights.get_vacancy_insights(vacancy)
            }
            
        except Exception as e:
            logger.error(f"Error analizando vacante con AURA: {str(e)}")
            return {}
    
    # Métodos auxiliares para AURA
    
    def _calculate_aura_score(self, network_analysis: Dict, performance_predictions: Dict) -> float:
        """Calcula score de AURA basado en análisis de red y predicciones."""
        try:
            # Score de red (40% peso)
            network_score = network_analysis.get('network_strength', 0) * 0.4
            
            # Score de predicciones (60% peso)
            prediction_score = performance_predictions.get('confidence', 0) * 0.6
            
            return round(network_score + prediction_score, 1)
        except Exception as e:
            logger.error(f"Error calculando AURA score: {str(e)}")
            return 0.0
    
    def _calculate_prediction_confidence(self, conversion_predictions: Dict, time_predictions: Dict) -> float:
        """Calcula nivel de confianza de las predicciones."""
        try:
            conversion_confidence = conversion_predictions.get('confidence', 0)
            time_confidence = time_predictions.get('confidence', 0)
            
            return round((conversion_confidence + time_confidence) / 2, 2)
        except Exception as e:
            logger.error(f"Error calculando confianza de predicciones: {str(e)}")
            return 0.0

"""
Dashboard específico para Consultores Senior con funcionalidades avanzadas pero limitadas.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class ConsultantSeniorDashboard:
    """
    Dashboard avanzado para consultores senior con acceso limitado pero potente.
    """
    
    def __init__(self, consultant_id: int):
        self.consultant_id = consultant_id
        self.consultant_name = self._get_consultant_name()
        self.business_unit = self._get_business_unit()
    
    def _get_consultant_name(self) -> str:
        """Obtiene el nombre del consultor."""
        # Simulación - en producción vendría de la base de datos
        return "María Rodríguez"
    
    def _get_business_unit(self) -> str:
        """Obtiene la unidad de negocio del consultor."""
        # Simulación - en producción vendría de la base de datos
        return "huntRED"
    
    def get_consultant_kanban_data(self, filters: Dict = None) -> Dict:
        """
        Kanban limitado para consultores - solo sus candidatos.
        """
        try:
            if not filters:
                filters = {
                    'period': 'month',
                    'status': 'all',
                    'priority': 'all'
                }
            
            kanban_data = {
                'consultant_info': {
                    'id': self.consultant_id,
                    'name': self.consultant_name,
                    'business_unit': self.business_unit
                },
                'filters': filters,
                'columns': self._get_consultant_kanban_columns(),
                'candidates': self._get_consultant_candidates(filters),
                'metrics': self._get_consultant_metrics(filters)
            }
            
            return kanban_data
            
        except Exception as e:
            logger.error(f"Error en kanban de consultor: {str(e)}")
            return {'error': str(e)}
    
    def _get_consultant_kanban_columns(self) -> Dict:
        """Columnas del kanban para consultores."""
        return {
            'sourcing': {
                'title': 'Sourcing',
                'icon': 'fas fa-search',
                'color': '#17a2b8',
                'count': 0
            },
            'screening': {
                'title': 'Screening',
                'icon': 'fas fa-filter',
                'color': '#ffc107',
                'count': 0
            },
            'interviewing': {
                'title': 'Entrevistando',
                'icon': 'fas fa-comments',
                'color': '#007bff',
                'count': 0
            },
            'references': {
                'title': 'Referencias',
                'icon': 'fas fa-phone',
                'color': '#6f42c1',
                'count': 0
            },
            'offer': {
                'title': 'Oferta',
                'icon': 'fas fa-file-contract',
                'color': '#fd7e14',
                'count': 0
            },
            'hired': {
                'title': 'Contratado',
                'icon': 'fas fa-check-circle',
                'color': '#28a745',
                'count': 0
            },
            'onboarding': {
                'title': 'Onboarding',
                'icon': 'fas fa-user-plus',
                'color': '#20c997',
                'count': 0
            }
        }
    
    def _get_consultant_candidates(self, filters: Dict) -> Dict:
        """Candidatos del consultor (limitado)."""
        # Simulación de candidatos del consultor
        candidates_data = {
            'sourcing': [
                {
                    'id': 1,
                    'name': 'Ana García López',
                    'position': 'Senior Developer',
                    'client': 'TechCorp',
                    'location': 'CDMX',
                    'experience': '5 años',
                    'salary_expectation': '$80,000 MXN',
                    'status': 'sourcing',
                    'priority': 'high',
                    'last_activity': '2024-01-15',
                    'match_score': 85,
                    'availability': 'Inmediata',
                    'notes': 'Candidata con experiencia en React y Node.js'
                }
            ],
            'interviewing': [
                {
                    'id': 4,
                    'name': 'Fernando Morales',
                    'position': 'Data Scientist',
                    'client': 'DataCorp',
                    'location': 'CDMX',
                    'experience': '4 años',
                    'salary_expectation': '$85,000 MXN',
                    'status': 'interviewing',
                    'priority': 'high',
                    'last_activity': '2024-01-17',
                    'match_score': 88,
                    'availability': 'Inmediata',
                    'interview_schedule': {
                        'next_interview': '2024-01-18 14:00',
                        'interviewer': 'Dr. Carlos Ruiz',
                        'type': 'Técnica'
                    }
                }
            ],
            'offer': [
                {
                    'id': 6,
                    'name': 'Miguel Ángel Ruiz',
                    'position': 'DevOps Engineer',
                    'client': 'CloudTech',
                    'location': 'Querétaro',
                    'experience': '5 años',
                    'salary_expectation': '$90,000 MXN',
                    'status': 'offer',
                    'priority': 'high',
                    'last_activity': '2024-01-17',
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
                    'location': 'CDMX',
                    'experience': '3 años',
                    'salary_expectation': '$70,000 MXN',
                    'status': 'hired',
                    'priority': 'medium',
                    'last_activity': '2024-01-10',
                    'match_score': 85,
                    'availability': 'Contratada',
                    'hiring_details': {
                        'hire_date': '2024-01-10',
                        'start_date': '2024-02-01',
                        'salary_final': '$72,000 MXN',
                        'contract_type': 'Indefinido'
                    }
                }
            ]
        }
        
        # Actualizar conteos
        for status, candidates in candidates_data.items():
            if status in self._get_consultant_kanban_columns():
                self._get_consultant_kanban_columns()[status]['count'] = len(candidates)
        
        return candidates_data
    
    def _get_consultant_metrics(self, filters: Dict) -> Dict:
        """Métricas del consultor (limitadas)."""
        return {
            'total_candidates': 25,
            'active_candidates': 18,
            'hired_this_period': 3,
            'avg_time_to_hire': '20 días',
            'conversion_rate': 75.0,
            'client_satisfaction': 4.8,
            'revenue_generated': '$450,000 MXN',
            'performance_rank': 2,  # Ranking entre consultores
            'by_status': {
                'sourcing': 8,
                'screening': 5,
                'interviewing': 3,
                'references': 2,
                'offer': 2,
                'hired': 3,
                'onboarding': 2
            }
        }
    
    def get_consultant_cv_data(self, candidate_id: int) -> Dict:
        """
        Datos de CV para consultor (limitado a sus candidatos).
        """
        try:
            # Verificar que el candidato pertenece al consultor
            if not self._candidate_belongs_to_consultant(candidate_id):
                return {'error': 'Acceso denegado'}
            
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
                    'super_admin': False  # No puede ver analytics de super admin
                },
                'export_options': {
                    'pdf': True,
                    'docx': True,
                    'html': False,  # Limitado
                    'txt': False    # Limitado
                },
                'cv_analytics': {
                    'total_views': 25,
                    'views_by_role': {
                        'candidate': 8,
                        'client': 12,
                        'consultant': 5
                    },
                    'downloads': 4,
                    'last_viewed': '2024-01-17 14:30'
                }
            }
            
            return cv_data
            
        except Exception as e:
            logger.error(f"Error en CV de consultor: {str(e)}")
            return {'error': str(e)}
    
    def get_consultant_reports_data(self, filters: Dict = None) -> Dict:
        """
        Reportes del consultor (limitados a su rendimiento).
        """
        try:
            if not filters:
                filters = {
                    'period': 'month',
                    'report_type': 'performance'
                }
            
            reports_data = {
                'consultant_info': {
                    'id': self.consultant_id,
                    'name': self.consultant_name,
                    'business_unit': self.business_unit
                },
                'filters': filters,
                'report_types': [
                    {
                        'id': 'performance',
                        'name': 'Mi Rendimiento',
                        'description': 'Métricas de productividad personal',
                        'icon': 'fas fa-user-tie'
                    },
                    {
                        'id': 'candidates',
                        'name': 'Mis Candidatos',
                        'description': 'Análisis de candidatos asignados',
                        'icon': 'fas fa-users'
                    },
                    {
                        'id': 'clients',
                        'name': 'Mis Clientes',
                        'description': 'Satisfacción y métricas de clientes',
                        'icon': 'fas fa-handshake'
                    }
                ],
                'performance_report': {
                    'summary': {
                        'candidates_managed': 25,
                        'hires_this_period': 3,
                        'conversion_rate': 75.0,
                        'avg_time_to_hire': '20 días',
                        'client_satisfaction': 4.8,
                        'revenue_generated': '$450,000 MXN'
                    },
                    'trends': {
                        'candidates_trend': [20, 22, 25, 23, 26, 25],
                        'hires_trend': [2, 1, 3, 2, 4, 3],
                        'satisfaction_trend': [4.5, 4.6, 4.7, 4.8, 4.8, 4.8]
                    },
                    'rankings': {
                        'conversion_rate_rank': 2,
                        'satisfaction_rank': 1,
                        'revenue_rank': 3
                    }
                },
                'candidates_report': {
                    'by_status': {
                        'sourcing': 8,
                        'screening': 5,
                        'interviewing': 3,
                        'references': 2,
                        'offer': 2,
                        'hired': 3,
                        'onboarding': 2
                    },
                    'by_priority': {
                        'high': 12,
                        'medium': 8,
                        'low': 5
                    },
                    'by_location': {
                        'CDMX': 15,
                        'Guadalajara': 5,
                        'Monterrey': 3,
                        'Otros': 2
                    }
                },
                'clients_report': {
                    'active_clients': 8,
                    'client_satisfaction': 4.8,
                    'repeat_clients': 6,
                    'top_clients': [
                        {
                            'name': 'TechCorp',
                            'candidates': 5,
                            'hires': 2,
                            'satisfaction': 5.0
                        },
                        {
                            'name': 'DataCorp',
                            'candidates': 3,
                            'hires': 1,
                            'satisfaction': 4.8
                        }
                    ]
                },
                'export_options': {
                    'formats': ['pdf', 'excel'],
                    'scheduling': True,
                    'automated_delivery': False,  # Limitado
                    'customization': True
                }
            }
            
            return reports_data
            
        except Exception as e:
            logger.error(f"Error en reportes de consultor: {str(e)}")
            return {'error': str(e)}
    
    def _candidate_belongs_to_consultant(self, candidate_id: int) -> bool:
        """Verifica si el candidato pertenece al consultor."""
        # Simulación - en producción verificaría en la base de datos
        consultant_candidates = [1, 4, 6, 7, 9]  # IDs de candidatos del consultor
        return candidate_id in consultant_candidates
    
    def get_consultant_dashboard_summary(self) -> Dict:
        """
        Resumen del dashboard para consultor senior.
        """
        try:
            return {
                'consultant_info': {
                    'id': self.consultant_id,
                    'name': self.consultant_name,
                    'business_unit': self.business_unit,
                    'role': 'Consultor Senior',
                    'access_level': 'Advanced'
                },
                'quick_stats': {
                    'active_candidates': 18,
                    'interviews_today': 2,
                    'offers_pending': 1,
                    'hires_this_month': 3
                },
                'recent_activities': [
                    {
                        'date': '2024-01-17',
                        'action': 'Entrevista programada con Fernando Morales',
                        'type': 'interview'
                    },
                    {
                        'date': '2024-01-16',
                        'action': 'Propuesta enviada a Miguel Ángel Ruiz',
                        'type': 'offer'
                    },
                    {
                        'date': '2024-01-15',
                        'action': 'Nuevo candidato agregado: Ana García López',
                        'type': 'candidate'
                    }
                ],
                'upcoming_tasks': [
                    {
                        'date': '2024-01-18',
                        'task': 'Entrevista técnica con Fernando Morales',
                        'priority': 'high'
                    },
                    {
                        'date': '2024-01-19',
                        'task': 'Seguimiento de propuesta Miguel Ángel Ruiz',
                        'priority': 'medium'
                    },
                    {
                        'date': '2024-01-20',
                        'task': 'Verificación de referencias Isabel Torres',
                        'priority': 'low'
                    }
                ]
            }
            
        except Exception as e:
            logger.error(f"Error en resumen de dashboard: {str(e)}")
            return {'error': str(e)} 