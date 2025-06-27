from typing import Dict, Any, List
from decimal import Decimal
import logging
from django.utils import timezone
from app.ats.pricing.models import PricingStrategy, DiscountRule, ReferralFee
from app.models import BusinessUnit, PremiumAddon
from app.ats.market.services.market_monitor import MarketMonitor

class PricingService:
    """Servicio para manejar la lógica de precios"""
    
    def __init__(self):
        self.market_monitor = MarketMonitor()
        self.logger = logging.getLogger(__name__)
    
    async def get_pricing_strategy(
        self,
        addon: PremiumAddon,
        business_unit: BusinessUnit
    ) -> Dict[str, Any]:
        """Obtiene estrategia de precios"""
        try:
            # Datos de mercado
            market_data = await self._get_market_data(business_unit, addon)
            
            # Análisis de ciclicidad
            cycle_data = await self._analyze_cycle(business_unit, addon)
            
            # Estrategia base
            base_strategy = self._get_base_strategy(market_data, cycle_data)
            
            # Ajustes por descuentos
            discount_strategy = await self._get_discount_strategy(addon, business_unit)
            
            # Ajustes por referidos
            referral_strategy = await self._get_referral_strategy(addon, business_unit)
            
            return {
                'base_price': addon.price,
                'market_data': market_data,
                'cycle_data': cycle_data,
                'base_strategy': base_strategy,
                'discount_strategy': discount_strategy,
                'referral_strategy': referral_strategy,
                'final_strategy': self._combine_strategies(
                    base_strategy,
                    discount_strategy,
                    referral_strategy
                )
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estrategia: {str(e)}")
            return {}
    
    async def _get_market_data(
        self,
        business_unit: BusinessUnit,
        addon: PremiumAddon
    ) -> Dict[str, Any]:
        """Obtiene datos de mercado"""
        try:
            return await self.market_monitor.get_market_data(
                business_unit=business_unit,
                addon=addon
            )
        except AttributeError:
            # Fallback si el método no existe
            return {
                'market_trend': 'stable',
                'competition_level': 'medium',
                'demand_level': 'normal'
            }
    
    async def _analyze_cycle(
        self,
        business_unit: BusinessUnit,
        addon: PremiumAddon
    ) -> Dict[str, Any]:
        """Analiza ciclicidad del mercado"""
        return {
            'season': self._get_current_season(),
            'market_phase': self._get_market_phase(),
            'trend_direction': self._get_trend_direction(),
            'recommended_actions': self._get_cycle_recommendations()
        }
    
    def _get_current_season(self) -> str:
        """Obtiene la temporada actual"""
        month = timezone.now().month
        if month in [12, 1, 2]:
            return 'winter'
        elif month in [3, 4, 5]:
            return 'spring'
        elif month in [6, 7, 8]:
            return 'summer'
        else:
            return 'fall'
    
    def _get_market_phase(self) -> str:
        """Obtiene la fase del mercado"""
        return 'growth'  # Valor por defecto
    
    def _get_trend_direction(self) -> str:
        """Obtiene la dirección de la tendencia"""
        return 'upward'  # Valor por defecto
    
    def _get_cycle_recommendations(self) -> List[str]:
        """Obtiene recomendaciones del ciclo"""
        return ['maintain_pricing', 'focus_on_value']
    
    def _get_base_strategy(
        self,
        market_data: Dict[str, Any],
        cycle_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Obtiene estrategia base"""
        return {
            'price_point': self._calculate_price_point(market_data),
            'activation_strategy': self._get_activation_strategy(cycle_data),
            'timing': self._get_strategy_timing(cycle_data),
            'expected_impact': self._get_expected_impact(market_data, cycle_data)
        }
    
    def _calculate_price_point(self, market_data: Dict[str, Any]) -> Decimal:
        """Calcula el punto de precio"""
        return Decimal('100.00')  # Valor por defecto
    
    def _get_activation_strategy(self, cycle_data: Dict[str, Any]) -> str:
        """Obtiene estrategia de activación"""
        return 'gradual'  # Valor por defecto
    
    def _get_strategy_timing(self, cycle_data: Dict[str, Any]) -> str:
        """Obtiene timing de la estrategia"""
        return 'immediate'  # Valor por defecto
    
    def _get_expected_impact(self, market_data: Dict[str, Any], cycle_data: Dict[str, Any]) -> str:
        """Obtiene impacto esperado"""
        return 'moderate'  # Valor por defecto
    
    async def _get_discount_strategy(
        self,
        addon: PremiumAddon,
        business_unit: BusinessUnit
    ) -> Dict[str, Any]:
        """Obtiene estrategia de descuentos"""
        discounts = await DiscountRule.objects.filter(
            is_active=True,
            valid_from__lte=timezone.now(),
            valid_to__isnull=True
        )
        
        return {
            'available_discounts': [
                {
                    'type': discount.type,
                    'value': discount.value,
                    'conditions': discount.conditions
                }
                for discount in discounts
            ],
            'recommended_discounts': self._get_recommended_discounts(discounts)
        }
    
    def _get_recommended_discounts(self, discounts) -> List[Dict[str, Any]]:
        """Obtiene descuentos recomendados"""
        return []  # Valor por defecto
    
    async def _get_referral_strategy(
        self,
        addon: PremiumAddon,
        business_unit: BusinessUnit
    ) -> Dict[str, Any]:
        """Obtiene estrategia de referidos"""
        referral_fees = await ReferralFee.objects.filter(
            is_active=True,
            valid_from__lte=timezone.now(),
            valid_to__isnull=True
        )
        
        return {
            'referral_fees': [
                {
                    'type': fee.type,
                    'value': fee.value,
                    'conditions': fee.conditions
                }
                for fee in referral_fees
            ],
            'recommended_fees': self._get_recommended_fees(referral_fees)
        }
    
    def _get_recommended_fees(self, fees) -> List[Dict[str, Any]]:
        """Obtiene comisiones recomendadas"""
        return []  # Valor por defecto
    
    def _combine_strategies(
        self,
        base_strategy: Dict[str, Any],
        discount_strategy: Dict[str, Any],
        referral_strategy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Combina todas las estrategias"""
        return {
            'final_price': self._calculate_final_price(
                base_strategy['price_point'],
                discount_strategy,
                referral_strategy
            ),
            'activation_plan': self._create_activation_plan(
                base_strategy,
                discount_strategy,
                referral_strategy
            ),
            'success_metrics': self._define_success_metrics(
                base_strategy,
                discount_strategy,
                referral_strategy
            )
        }
    
    def _calculate_final_price(
        self,
        base_price: Decimal,
        discount_strategy: Dict[str, Any],
        referral_strategy: Dict[str, Any]
    ) -> Decimal:
        """Calcula precio final"""
        # Aplicar descuentos
        for discount in discount_strategy.get('recommended_discounts', []):
            base_price = self._apply_discount(base_price, discount)
        
        # Ajustar por referidos
        for fee in referral_strategy.get('recommended_fees', []):
            base_price = self._adjust_for_referral(base_price, fee)
        
        return base_price
    
    def _apply_discount(self, price: Decimal, discount: Dict[str, Any]) -> Decimal:
        """Aplica un descuento al precio"""
        if discount.get('type') == 'percentage':
            discount_amount = price * (discount.get('value', 0) / 100)
            return price - discount_amount
        return price
    
    def _adjust_for_referral(self, price: Decimal, fee: Dict[str, Any]) -> Decimal:
        """Ajusta el precio por comisión de referido"""
        if fee.get('type') == 'percentage':
            fee_amount = price * (fee.get('value', 0) / 100)
            return price + fee_amount
        return price
    
    def _create_activation_plan(
        self,
        base_strategy: Dict[str, Any],
        discount_strategy: Dict[str, Any],
        referral_strategy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Crea plan de activación"""
        return {
            'phases': [
                {
                    'phase': 'initial',
                    'actions': self._get_initial_actions(
                        base_strategy,
                        discount_strategy
                    ),
                    'timing': 'immediate'
                },
                {
                    'phase': 'growth',
                    'actions': self._get_growth_actions(
                        base_strategy,
                        discount_strategy
                    ),
                    'timing': '1_week'
                },
                {
                    'phase': 'optimization',
                    'actions': self._get_optimization_actions(
                        base_strategy,
                        discount_strategy
                    ),
                    'timing': '1_month'
                }
            ],
            'success_criteria': self._define_success_criteria(
                base_strategy,
                discount_strategy,
                referral_strategy
            )
        }
    
    def _get_initial_actions(
        self,
        base_strategy: Dict[str, Any],
        discount_strategy: Dict[str, Any]
    ) -> List[str]:
        """Obtiene acciones iniciales"""
        return ['launch_campaign', 'activate_discounts']
    
    def _get_growth_actions(
        self,
        base_strategy: Dict[str, Any],
        discount_strategy: Dict[str, Any]
    ) -> List[str]:
        """Obtiene acciones de crecimiento"""
        return ['expand_reach', 'optimize_conversion']
    
    def _get_optimization_actions(
        self,
        base_strategy: Dict[str, Any],
        discount_strategy: Dict[str, Any]
    ) -> List[str]:
        """Obtiene acciones de optimización"""
        return ['analyze_performance', 'adjust_strategy']
    
    def _define_success_criteria(
        self,
        base_strategy: Dict[str, Any],
        discount_strategy: Dict[str, Any],
        referral_strategy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Define criterios de éxito"""
        return {
            'revenue_targets': self._calculate_revenue_targets(
                base_strategy,
                discount_strategy
            ),
            'adoption_metrics': self._define_adoption_metrics(
                base_strategy,
                discount_strategy
            ),
            'referral_metrics': self._define_referral_metrics(
                referral_strategy
            )
        }
    
    def _calculate_revenue_targets(
        self,
        base_strategy: Dict[str, Any],
        discount_strategy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calcula objetivos de ingresos"""
        return {
            'monthly_target': 10000,
            'quarterly_target': 30000,
            'annual_target': 120000
        }
    
    def _define_adoption_metrics(
        self,
        base_strategy: Dict[str, Any],
        discount_strategy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Define métricas de adopción"""
        return {
            'target_conversion_rate': 0.15,
            'target_retention_rate': 0.85
        }
    
    def _define_referral_metrics(
        self,
        referral_strategy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Define métricas de referidos"""
        return {
            'target_referral_rate': 0.10,
            'target_referral_value': 500
        }
    
    def _define_success_metrics(
        self,
        base_strategy: Dict[str, Any],
        discount_strategy: Dict[str, Any],
        referral_strategy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Define métricas de éxito"""
        return {
            'kpis': [
                'revenue_growth',
                'customer_acquisition_cost',
                'lifetime_value',
                'churn_rate'
            ],
            'targets': {
                'revenue_growth': 0.20,
                'customer_acquisition_cost': 100,
                'lifetime_value': 1000,
                'churn_rate': 0.05
            }
        } 