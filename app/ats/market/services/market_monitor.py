from typing import Dict, Any, List
from datetime import datetime, timedelta
from app.models import BusinessUnit
from app.ats.pricing.models.addons import PremiumAddon
from app.ml.analyzers.market.salary_analyzer import SalaryAnalyzer
from app.ml.analyzers.market.demand_analyzer import DemandAnalyzer
from app.ats.integrations.notifications.process.market_alerts import MarketAlertService

class MarketMonitor:
    """Servicio de monitoreo de mercado optimizado"""
    
    def __init__(self):
        self.salary_analyzer = SalaryAnalyzer()
        self.demand_analyzer = DemandAnalyzer()
        self.alert_service = MarketAlertService()
    
    async def monitor_market(self, business_unit: BusinessUnit) -> None:
        """Monitoreo semanal de mercado"""
        try:
            # Verificar si es momento de análisis semanal
            if not self._should_run_weekly_analysis():
                return
            
            # Obtener addons activos
            active_addons = await self._get_active_addons(business_unit)
            
            # Análisis semanal
            for addon in active_addons:
                await self._analyze_addon_market(business_unit, addon)
            
            # Limpiar caché antigua
            await self._cleanup_old_cache()
            
        except Exception as e:
            self.logger.error(f"Error en monitoreo: {str(e)}")
    
    def _should_run_weekly_analysis(self) -> bool:
        """Verifica si debe ejecutarse el análisis semanal"""
        last_run = self._get_last_run_date()
        if not last_run:
            return True
        
        # Ejecutar cada lunes
        return (
            datetime.now().weekday() == 0 and  # Lunes
            (datetime.now() - last_run).days >= 7
        )
    
    async def _analyze_addon_market(
        self,
        business_unit: BusinessUnit,
        addon: PremiumAddon
    ) -> None:
        """Analiza mercado para un addon específico"""
        try:
            # Análisis de salarios (semanal)
            salary_data = await self.salary_analyzer.analyze_salaries(
                skill=addon.type,
                business_unit=business_unit.id
            )
            
            # Análisis de demanda (semanal)
            demand_data = await self.demand_analyzer.analyze_demand(
                skill=addon.type,
                location=business_unit.location
            )
            
            # Verificar cambios significativos
            if self._has_significant_changes(salary_data, demand_data):
                await self.alert_service.check_market_alerts(
                    business_unit=business_unit,
                    skills=[addon.type]
                )
            
            # Actualizar caché
            await self._update_cache(
                business_unit=business_unit,
                addon=addon,
                salary_data=salary_data,
                demand_data=demand_data
            )
            
        except Exception as e:
            self.logger.error(f"Error analizando addon {addon.id}: {str(e)}")
    
    def _has_significant_changes(
        self,
        salary_data: Dict[str, Any],
        demand_data: Dict[str, Any]
    ) -> bool:
        """Verifica si hay cambios significativos"""
        # Cambios en salarios (>5%)
        salary_change = abs(salary_data.get('trends', {}).get('growth_rate', 0))
        if salary_change > 5:
            return True
        
        # Cambios en demanda (>10%)
        demand_change = abs(demand_data.get('growth_rate', 0))
        if demand_change > 10:
            return True
        
        return False
    
    async def _update_cache(
        self,
        business_unit: BusinessUnit,
        addon: PremiumAddon,
        salary_data: Dict[str, Any],
        demand_data: Dict[str, Any]
    ) -> None:
        """Actualiza caché de datos"""
        cache_key = f"market_data_{business_unit.id}_{addon.id}"
        cache_data = {
            'salary_data': salary_data,
            'demand_data': demand_data,
            'updated_at': datetime.now()
        }
        await self.cache.set(cache_key, cache_data, timeout=604800)  # 7 días
    
    async def _cleanup_old_cache(self) -> None:
        """Limpia caché antigua"""
        # Implementar limpieza de caché
        pass
    
    async def _get_active_addons(
        self,
        business_unit: BusinessUnit
    ) -> List[PremiumAddon]:
        """Obtiene addons activos"""
        return await PremiumAddon.objects.filter(
            business_unit=business_unit,
            is_active=True
        )
    
    def _get_last_run_date(self) -> datetime:
        """Obtiene fecha del último análisis"""
        # Implementar obtención de última fecha
        return None 