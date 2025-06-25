from app.models import (
    Person, Application, Vacante, BusinessUnit, 
    Event, EventParticipant, Interview, ClientFeedback,
    ServiceCalculation, GamificationProfile, ChatState, 
    RecoveryAttempt, ConsultorInteraction, ApiConfig
)
from app.ats.integrations.channels.whatsapp import WhatsAppService
from app.ats.analytics.market_analyzer import MarketAnalyzer
from app.ats.analytics.competitor_analyzer import CompetitorAnalyzer
from app.ats.ml.recommendation_engine import RecommendationEngine
from app.ats.utils.cache import cache_result
from app.aura.engine import AuraEngine  # Integración con AURA
from app.aura.insights import AuraInsights  # Insights de AURA

class ClientDashboard:
    """
    Dashboard para clientes con funcionalidades avanzadas.
    
    Incluye:
    - Gestión de vacantes y candidatos
    - Analytics de contratación
    - Insights de mercado
    - Integración condicional con AURA (si está habilitada)
    """
    
    def __init__(self, client_id: str, business_unit: Optional[BusinessUnit] = None):
        self.client_id = client_id
        self.business_unit = business_unit
        self.whatsapp_service = WhatsAppService()
        self.market_analyzer = MarketAnalyzer()
        self.competitor_analyzer = CompetitorAnalyzer()
        self.recommendation_engine = RecommendationEngine()
        
        # Verificar si el cliente tiene AURA habilitado
        self.aura_enabled = self._check_aura_enabled()
        if self.aura_enabled:
            self.aura_engine = AuraEngine()
            self.aura_insights = AuraInsights()
        else:
            self.aura_engine = None
            self.aura_insights = None
    
    def _check_aura_enabled(self) -> bool:
        """Verifica si el cliente tiene AURA habilitado en su cuenta."""
        try:
            # Verificar en ApiConfig si el cliente tiene AURA
            api_config = ApiConfig.objects.filter(
                client_id=self.client_id,
                feature='aura',
                is_active=True
            ).first()
            
            if api_config:
                return True
            
            # Verificar en el modelo Person si tiene flag de AURA
            client = Person.objects.filter(id=self.client_id).first()
            if client and hasattr(client, 'aura_enabled'):
                return client.aura_enabled
            
            return False
            
        except Exception as e:
            logger.error(f"Error verificando AURA para cliente {self.client_id}: {str(e)}")
            return False
    
    @cache_result(ttl=300)  # 5 minutos
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Obtiene todos los datos del dashboard del cliente."""
        base_data = {
            'vacancy_management': await self.get_vacancy_management_data(),
            'candidate_analytics': await self.get_candidate_analytics(),
            'hiring_metrics': await self.get_hiring_metrics(),
            'market_insights': await self.get_market_insights(),
            'performance_analytics': await self.get_performance_analytics(),
            'recent_activities': await self.get_recent_activities(),
            'upcoming_interviews': await self.get_upcoming_interviews(),
            'aura_enabled': self.aura_enabled  # Informar si AURA está habilitado
        }
        
        # Agregar datos de AURA si está habilitado
        if self.aura_enabled:
            base_data.update({
                'aura_insights': await self.get_aura_insights(),
                'predictive_analytics': await self.get_predictive_analytics(),
                'ai_recommendations': await self.get_ai_recommendations()
            })
        
        return base_data
    
    @cache_result(ttl=1800)  # 30 minutos
    async def get_aura_insights(self) -> Dict[str, Any]:
        """Obtiene insights de AURA para el cliente (solo si está habilitado)."""
        if not self.aura_enabled:
            return {'enabled': False, 'message': 'AURA no está habilitado para esta cuenta'}
        
        try:
            # Obtener datos del cliente
            client = await sync_to_async(Person.objects.get)(id=self.client_id)
            
            # Análisis de mercado específico del cliente
            client_market_analysis = await self.aura_engine.analyze_client_market(client)
            
            # Predicciones de contratación
            hiring_predictions = await self.aura_engine.predict_client_hiring_success(client)
            
            # Análisis de competencia
            competitor_analysis = await self.aura_engine.analyze_client_competitors(client)
            
            # Oportunidades de mejora
            improvement_opportunities = await self.aura_engine.identify_client_improvements(client)
            
            # Insights de candidatos
            candidate_insights = await self.aura_insights.get_client_candidate_insights(client)
            
            return {
                'enabled': True,
                'client_market_analysis': client_market_analysis,
                'hiring_predictions': hiring_predictions,
                'competitor_analysis': competitor_analysis,
                'improvement_opportunities': improvement_opportunities,
                'candidate_insights': candidate_insights,
                'aura_score': self._calculate_client_aura_score(client_market_analysis, hiring_predictions)
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo insights de AURA para cliente: {str(e)}")
            return {'enabled': True, 'error': str(e)}
    
    @cache_result(ttl=3600)  # 1 hora
    async def get_predictive_analytics(self) -> Dict[str, Any]:
        """Obtiene analytics predictivos usando AURA (solo si está habilitado)."""
        if not self.aura_enabled:
            return {'enabled': False, 'message': 'AURA no está habilitado para esta cuenta'}
        
        try:
            # Predicción de tiempo de contratación
            time_to_hire_predictions = await self.aura_engine.predict_client_time_to_hire(self.client_id)
            
            # Predicción de calidad de contratación
            quality_predictions = await self.aura_engine.predict_hiring_quality(self.client_id)
            
            # Predicción de retención
            retention_predictions = await self.aura_engine.predict_employee_retention(self.client_id)
            
            # Análisis de riesgo de contratación
            hiring_risks = await self.aura_engine.analyze_client_hiring_risks(self.client_id)
            
            # Recomendaciones predictivas
            predictive_recommendations = await self.aura_engine.generate_client_predictive_recommendations(self.client_id)
            
            return {
                'enabled': True,
                'time_to_hire_predictions': time_to_hire_predictions,
                'quality_predictions': quality_predictions,
                'retention_predictions': retention_predictions,
                'hiring_risks': hiring_risks,
                'predictive_recommendations': predictive_recommendations,
                'confidence_level': self._calculate_client_prediction_confidence(
                    time_to_hire_predictions, quality_predictions, retention_predictions
                )
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo analytics predictivos para cliente: {str(e)}")
            return {'enabled': True, 'error': str(e)}
    
    @cache_result(ttl=1800)  # 30 minutos
    async def get_ai_recommendations(self) -> Dict[str, Any]:
        """Obtiene recomendaciones de IA usando AURA (solo si está habilitado)."""
        if not self.aura_enabled:
            return {'enabled': False, 'message': 'AURA no está habilitado para esta cuenta'}
        
        try:
            # Recomendaciones de mejora de proceso
            process_recommendations = await self.aura_engine.recommend_process_improvements(self.client_id)
            
            # Recomendaciones de sourcing
            sourcing_recommendations = await self.aura_engine.recommend_sourcing_channels(self.client_id)
            
            # Recomendaciones de employer branding
            branding_recommendations = await self.aura_engine.recommend_employer_branding(self.client_id)
            
            # Recomendaciones de compensación
            compensation_recommendations = await self.aura_engine.recommend_compensation_strategies(self.client_id)
            
            return {
                'enabled': True,
                'process_recommendations': process_recommendations,
                'sourcing_recommendations': sourcing_recommendations,
                'branding_recommendations': branding_recommendations,
                'compensation_recommendations': compensation_recommendations,
                'priority_score': self._calculate_recommendation_priority(
                    process_recommendations, sourcing_recommendations, 
                    branding_recommendations, compensation_recommendations
                )
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo recomendaciones de IA para cliente: {str(e)}")
            return {'enabled': True, 'error': str(e)}
    
    async def get_aura_vacancy_analysis(self, vacancy_id: str) -> Dict[str, Any]:
        """Obtiene análisis de una vacante usando AURA (solo si está habilitado)."""
        if not self.aura_enabled:
            return {'enabled': False, 'message': 'AURA no está habilitado para esta cuenta'}
        
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
            
            # Análisis de competencia salarial
            salary_analysis = await self.aura_engine.analyze_salary_competition(vacancy)
            
            return {
                'enabled': True,
                'market_analysis': market_analysis,
                'fill_difficulty': fill_difficulty,
                'ideal_candidates': ideal_candidates,
                'sourcing_strategies': sourcing_strategies,
                'salary_analysis': salary_analysis,
                'aura_recommendations': await self.aura_insights.get_vacancy_insights(vacancy)
            }
            
        except Exception as e:
            logger.error(f"Error analizando vacante con AURA para cliente: {str(e)}")
            return {'enabled': True, 'error': str(e)}
    
    async def get_aura_candidate_analysis(self, candidate_id: str) -> Dict[str, Any]:
        """Obtiene análisis detallado de un candidato usando AURA (solo si está habilitado)."""
        if not self.aura_enabled:
            return {'enabled': False, 'message': 'AURA no está habilitado para esta cuenta'}
        
        try:
            candidate = await sync_to_async(Person.objects.get)(id=candidate_id)
            
            # Análisis de red del candidato
            candidate_network = await self.aura_engine.analyze_candidate_network(candidate)
            
            # Predicción de éxito
            success_prediction = await self.aura_engine.predict_candidate_success(candidate)
            
            # Análisis de fit cultural
            cultural_fit = await self.aura_engine.analyze_cultural_fit(candidate, self.business_unit)
            
            # Análisis de riesgo
            risk_analysis = await self.aura_engine.analyze_candidate_risk(candidate)
            
            # Recomendaciones personalizadas
            personalized_recommendations = await self.aura_engine.generate_candidate_recommendations(candidate)
            
            return {
                'enabled': True,
                'candidate_network': candidate_network,
                'success_prediction': success_prediction,
                'cultural_fit': cultural_fit,
                'risk_analysis': risk_analysis,
                'personalized_recommendations': personalized_recommendations,
                'aura_insights': await self.aura_insights.get_candidate_insights(candidate)
            }
            
        except Exception as e:
            logger.error(f"Error analizando candidato con AURA para cliente: {str(e)}")
            return {'enabled': True, 'error': str(e)}
    
    # Métodos auxiliares para AURA
    
    def _calculate_client_aura_score(self, market_analysis: Dict, hiring_predictions: Dict) -> float:
        """Calcula score de AURA para el cliente."""
        try:
            # Score de mercado (50% peso)
            market_score = market_analysis.get('market_position', 0) * 0.5
            
            # Score de predicciones (50% peso)
            prediction_score = hiring_predictions.get('confidence', 0) * 0.5
            
            return round(market_score + prediction_score, 1)
        except Exception as e:
            logger.error(f"Error calculando AURA score para cliente: {str(e)}")
            return 0.0
    
    def _calculate_client_prediction_confidence(self, time_predictions: Dict, quality_predictions: Dict, retention_predictions: Dict) -> float:
        """Calcula nivel de confianza de las predicciones para el cliente."""
        try:
            time_confidence = time_predictions.get('confidence', 0)
            quality_confidence = quality_predictions.get('confidence', 0)
            retention_confidence = retention_predictions.get('confidence', 0)
            
            return round((time_confidence + quality_confidence + retention_confidence) / 3, 2)
        except Exception as e:
            logger.error(f"Error calculando confianza de predicciones para cliente: {str(e)}")
            return 0.0
    
    def _calculate_recommendation_priority(self, process_recs: Dict, sourcing_recs: Dict, branding_recs: Dict, comp_recs: Dict) -> float:
        """Calcula prioridad de las recomendaciones."""
        try:
            priorities = [
                process_recs.get('priority', 0),
                sourcing_recs.get('priority', 0),
                branding_recs.get('priority', 0),
                comp_recs.get('priority', 0)
            ]
            
            return round(sum(priorities) / len(priorities), 2)
        except Exception as e:
            logger.error(f"Error calculando prioridad de recomendaciones: {str(e)}")
            return 0.0 