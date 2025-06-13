# /home/pablo/app/ats/pricing/services/recommendation_service.py
from typing import Dict, List, Optional
from django.db.models import Avg, Count, Q
from django.utils import timezone
from datetime import timedelta
from app.models import Proposal, Vacante, Company, BusinessUnit
from app.ats.pricing.models import (
    PricingStrategy,
    PricePoint,
    DiscountRule,
    ReferralFee,
    PricingCalculation,
    PricingPayment,
    PricingProposal
)

class RecommendationService:
    def __init__(self):
        self.success_threshold = 80  # Tasa de éxito mínima para recomendaciones
        self.min_positions = 5  # Mínimo de posiciones para considerar métricas

    def get_recommendations(self, business_unit, service_type, market_data=None, historical_data=None):
        """
        Genera recomendaciones de pricing basadas en datos históricos y de mercado
        
        Args:
            business_unit: Unidad de negocio
            service_type: Tipo de servicio
            market_data: Datos de mercado (opcional)
            historical_data: Datos históricos (opcional)
            
        Returns:
            dict: Recomendaciones de pricing
        """
        recommendations = {
            'price_points': self._get_price_point_recommendations(business_unit, service_type),
            'discounts': self._get_discount_recommendations(business_unit, service_type),
            'referral_fees': self._get_referral_fee_recommendations(business_unit, service_type),
            'market_analysis': self._analyze_market_data(market_data) if market_data else None,
            'historical_analysis': self._analyze_historical_data(historical_data) if historical_data else None
        }
        
        return recommendations
    
    def _get_price_point_recommendations(self, business_unit, service_type):
        """Obtiene recomendaciones de puntos de precio"""
        # Obtener puntos de precio existentes
        existing_price_points = PricePoint.objects.filter(
            business_unit=business_unit,
            service_type=service_type
        )
        
        # Obtener propuestas exitosas
        successful_proposals = PricingProposal.objects.filter(
            oportunidad__business_unit=business_unit,
            estado='APROBADA',
            secciones__tipo='PRECIO'
        ).values('monto_total').annotate(
            count=Count('id'),
            avg_amount=Avg('monto_total')
        ).order_by('-count')
        
        recommendations = {
            'existing_price_points': list(existing_price_points.values()),
            'successful_price_points': list(successful_proposals),
            'suggested_price_points': self._calculate_suggested_price_points(
                existing_price_points,
                successful_proposals
            )
        }
        
        return recommendations
    
    def _get_discount_recommendations(self, business_unit, service_type):
        """Obtiene recomendaciones de descuentos"""
        # Obtener reglas de descuento existentes
        existing_discounts = DiscountRule.objects.filter(
            business_unit=business_unit,
            service_type=service_type
        )
        
        # Analizar efectividad de descuentos
        discount_effectiveness = PricingProposal.objects.filter(
            oportunidad__business_unit=business_unit,
            estado='APROBADA',
            metadata__has_key='discount_applied'
        ).values('metadata__discount_applied').annotate(
            count=Count('id'),
            avg_amount=Avg('monto_total')
        ).order_by('-count')
        
        recommendations = {
            'existing_discounts': list(existing_discounts.values()),
            'effective_discounts': list(discount_effectiveness),
            'suggested_discounts': self._calculate_suggested_discounts(
                existing_discounts,
                discount_effectiveness
            )
        }
        
        return recommendations
    
    def _get_referral_fee_recommendations(self, business_unit, service_type):
        """Obtiene recomendaciones de comisiones por referidos"""
        # Obtener comisiones existentes
        existing_fees = ReferralFee.objects.filter(
            business_unit=business_unit,
            service_type=service_type
        )
        
        # Analizar efectividad de comisiones
        fee_effectiveness = PricingProposal.objects.filter(
            oportunidad__business_unit=business_unit,
            estado='APROBADA',
            metadata__has_key='referral_fee'
        ).values('metadata__referral_fee').annotate(
            count=Count('id'),
            avg_amount=Avg('monto_total')
        ).order_by('-count')
        
        recommendations = {
            'existing_fees': list(existing_fees.values()),
            'effective_fees': list(fee_effectiveness),
            'suggested_fees': self._calculate_suggested_fees(
                existing_fees,
                fee_effectiveness
            )
        }
        
        return recommendations
    
    def _analyze_market_data(self, market_data):
        """Analiza datos de mercado"""
        # Implementar análisis de datos de mercado
        return {
            'market_average': self._calculate_market_average(market_data),
            'market_trends': self._identify_market_trends(market_data),
            'competitive_analysis': self._analyze_competition(market_data)
        }
    
    def _analyze_historical_data(self, historical_data):
        """Analiza datos históricos"""
        # Implementar análisis de datos históricos
        return {
            'historical_average': self._calculate_historical_average(historical_data),
            'historical_trends': self._identify_historical_trends(historical_data),
            'seasonal_patterns': self._analyze_seasonal_patterns(historical_data)
        }
    
    def _calculate_suggested_price_points(self, existing_price_points, successful_proposals):
        """Calcula puntos de precio sugeridos"""
        # Implementar lógica de sugerencia de puntos de precio
        return []
    
    def _calculate_suggested_discounts(self, existing_discounts, discount_effectiveness):
        """Calcula descuentos sugeridos"""
        # Implementar lógica de sugerencia de descuentos
        return []
    
    def _calculate_suggested_fees(self, existing_fees, fee_effectiveness):
        """Calcula comisiones sugeridas"""
        # Implementar lógica de sugerencia de comisiones
        return []
    
    def _calculate_market_average(self, market_data):
        """Calcula promedio de mercado"""
        # Implementar cálculo de promedio de mercado
        return 0
    
    def _identify_market_trends(self, market_data):
        """Identifica tendencias de mercado"""
        # Implementar identificación de tendencias
        return []
    
    def _analyze_competition(self, market_data):
        """Analiza competencia"""
        # Implementar análisis de competencia
        return {}
    
    def _calculate_historical_average(self, historical_data):
        """Calcula promedio histórico"""
        # Implementar cálculo de promedio histórico
        return 0
    
    def _identify_historical_trends(self, historical_data):
        """Identifica tendencias históricas"""
        # Implementar identificación de tendencias
        return []
    
    def _analyze_seasonal_patterns(self, historical_data):
        """Analiza patrones estacionales"""
        # Implementar análisis de patrones estacionales
        return {}

    def _get_success_metrics(self, vacancy: Vacante) -> Dict:
        """
        Obtiene métricas de éxito para puestos similares.
        
        Args:
            vacancy: Instancia de Vacante
            
        Returns:
            Dict: Métricas de éxito
        """
        # Buscar puestos similares en los últimos 6 meses
        similar_positions = Vacante.objects.filter(
            title__icontains=vacancy.title,
            created_at__gte=timezone.now() - timedelta(days=180)
        ).exclude(id=vacancy.id)
        
        if not similar_positions.exists():
            return {
                'success_rate': 0,
                'avg_time_to_fill': 0,
                'total_positions': 0
            }
        
        # Calcular métricas
        total_positions = similar_positions.count()
        filled_positions = similar_positions.filter(status='filled').count()
        avg_time_to_fill = similar_positions.filter(
            status='filled'
        ).aggregate(
            avg_time=Avg('time_to_fill')
        )['avg_time'] or 0
        
        return {
            'success_rate': (filled_positions / total_positions) * 100,
            'avg_time_to_fill': avg_time_to_fill,
            'total_positions': total_positions
        }

    def _get_pricing_recommendations(
        self, company: Company, vacancy: Vacante, metrics: Dict
    ) -> Dict:
        """
        Genera recomendaciones de pricing basadas en métricas.
        
        Args:
            company: Instancia de Company
            vacancy: Instancia de Vacante
            metrics: Métricas de éxito
            
        Returns:
            Dict: Recomendaciones de pricing
        """
        # Obtener historial de pricing de la empresa
        company_history = PricingCalculation.objects.filter(
            company=company,
            created_at__gte=timezone.now() - timedelta(days=365)
        )
        
        # Calcular promedio de honorarios
        avg_fee = company_history.aggregate(
            avg_fee=Avg('total_fee')
        )['avg_fee'] or 0
        
        # Ajustar según métricas de éxito
        if metrics['success_rate'] > self.success_threshold:
            recommended_fee = avg_fee * 1.1  # Aumentar 10%
        elif metrics['success_rate'] < 50:
            recommended_fee = avg_fee * 0.9  # Reducir 10%
        else:
            recommended_fee = avg_fee
        
        return {
            'recommended_fee': recommended_fee,
            'avg_fee': avg_fee,
            'adjustment_factor': recommended_fee / avg_fee if avg_fee else 1
        }

    def _get_payment_recommendations(
        self, company: Company, vacancy: Vacante, metrics: Dict
    ) -> Dict:
        """
        Genera recomendaciones de estructura de pago.
        
        Args:
            company: Instancia de Company
            vacancy: Instancia de Vacante
            metrics: Métricas de éxito
            
        Returns:
            Dict: Recomendaciones de estructura de pago
        """
        # Obtener historial de estructuras de pago
        payment_history = PricingCalculation.objects.filter(
            company=company,
            created_at__gte=timezone.now() - timedelta(days=365)
        ).values('payment_structure').annotate(
            count=Count('id')
        ).order_by('-count')
        
        if not payment_history.exists():
            return {
                'recommended_structure': 'standard',
                'confidence': 0
            }
        
        # Obtener estructura más común
        most_common = payment_history.first()
        
        # Calcular confianza basada en métricas
        confidence = min(metrics['success_rate'] / 100, 1)
        
        return {
            'recommended_structure': most_common['payment_structure'],
            'confidence': confidence
        }

    def _get_addon_recommendations(
        self, company: Company, vacancy: Vacante, metrics: Dict
    ) -> List[Dict]:
        """
        Genera recomendaciones de addons.
        
        Args:
            company: Instancia de Company
            vacancy: Instancia de Vacante
            metrics: Métricas de éxito
            
        Returns:
            List[Dict]: Lista de recomendaciones de addons
        """
        # Obtener addons más comunes para puestos similares
        similar_positions = Vacante.objects.filter(
            title__icontains=vacancy.title,
            created_at__gte=timezone.now() - timedelta(days=180)
        )
        
        addon_recommendations = []
        
        # Analizar cada tipo de addon
        for addon_type in ['assessment', 'team_evaluation', 'background_check']:
            # Calcular tasa de uso
            usage_rate = similar_positions.filter(
                addons__contains=addon_type
            ).count() / similar_positions.count() if similar_positions.exists() else 0
            
            # Recomendar si la tasa de uso es alta
            if usage_rate > 0.5:
                addon_recommendations.append({
                    'type': addon_type,
                    'usage_rate': usage_rate,
                    'recommended': True
                })
        
        return addon_recommendations 