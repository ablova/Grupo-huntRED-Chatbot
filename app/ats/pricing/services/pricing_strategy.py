from typing import Dict, Any, List
from decimal import Decimal
from app.ats.pricing.models.addons import PremiumAddon
from app.ats.models.business_unit import BusinessUnit
from app.ats.market.services.market_monitor import MarketMonitor
from app.ats.pricing.models.discount import Discount
from app.ats.pricing.models.referral import ReferralFee

class PricingStrategy:
    """Servicio de estrategia de precios"""
    
    def __init__(self):
        self.market_monitor = MarketMonitor()
    
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
            return None
    
    async def _get_market_data(
        self,
        business_unit: BusinessUnit,
        addon: PremiumAddon
    ) -> Dict[str, Any]:
        """Obtiene datos de mercado"""
        return await self.market_monitor.get_market_data(
            business_unit=business_unit,
            addon=addon
        )
    
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
    
    async def _get_discount_strategy(
        self,
        addon: PremiumAddon,
        business_unit: BusinessUnit
    ) -> Dict[str, Any]:
        """Obtiene estrategia de descuentos"""
        discounts = await Discount.objects.filter(
            addon=addon,
            business_unit=business_unit,
            is_active=True
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
    
    async def _get_referral_strategy(
        self,
        addon: PremiumAddon,
        business_unit: BusinessUnit
    ) -> Dict[str, Any]:
        """Obtiene estrategia de referidos"""
        referral_fees = await ReferralFee.objects.filter(
            addon=addon,
            business_unit=business_unit,
            is_active=True
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
        for discount in discount_strategy['recommended_discounts']:
            base_price = self._apply_discount(base_price, discount)
        
        # Ajustar por referidos
        for fee in referral_strategy['recommended_fees']:
            base_price = self._adjust_for_referral(base_price, fee)
        
        return base_price
    
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
                        referral_strategy
                    ),
                    'timing': '30_days'
                },
                {
                    'phase': 'optimization',
                    'actions': self._get_optimization_actions(
                        base_strategy,
                        discount_strategy,
                        referral_strategy
                    ),
                    'timing': '90_days'
                }
            ],
            'success_criteria': self._define_success_criteria(
                base_strategy,
                discount_strategy,
                referral_strategy
            )
        }
    
    def _define_success_metrics(
        self,
        base_strategy: Dict[str, Any],
        discount_strategy: Dict[str, Any],
        referral_strategy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Define métricas de éxito"""
        return {
            'revenue_targets': self._calculate_revenue_targets(
                base_strategy['price_point'],
                discount_strategy,
                referral_strategy
            ),
            'adoption_metrics': self._define_adoption_metrics(
                base_strategy,
                discount_strategy
            ),
            'referral_metrics': self._define_referral_metrics(
                referral_strategy
            )
        } 