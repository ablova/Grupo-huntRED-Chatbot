from app.models import Opportunity, Proposal
from datetime import datetime, timedelta

class ProcessSimulator:
    def __init__(self):
        self.time_estimates = {
            'scraping': 1,  # días
            'matching': 2,
            'proposal': 3,
            'approval': 5,
            'hiring': 10
        }
        
    def calculate_costs(self, opportunity):
        """Calcula los costos estimados del proceso."""
        base_cost = opportunity.amount * 0.15  # 15% base
        
        # Ajustes por BU
        bu_adjustments = {
            'huntU': 0.9,
            'huntRED®': 1.0,
            'huntRED® Executive': 1.1
        }
        
        cost = base_cost * bu_adjustments.get(opportunity.business_unit, 1.0)
        
        return {
            'base_cost': base_cost,
            'adjusted_cost': cost,
            'bu_adjustment': bu_adjustments.get(opportunity.business_unit, 1.0)
        }
        
    def simulate_opportunity_flow(self, opportunity):
        """
        Simula el flujo completo de una oportunidad.
        
        Args:
            opportunity: Oportunidad a simular
            
        Returns:
            Dict con detalles de la simulación
        """
        # Calcular tiempos estimados
        estimated_times = {
            'scraping': self.time_estimates['scraping'],
            'matching': self.time_estimates['matching'],
            'proposal': self.time_estimates['proposal'],
            'approval': self.time_estimates['approval'],
            'hiring': self.time_estimates['hiring']
        }
        
        total_time = sum(estimated_times.values())
        
        # Calcular costos
        cost_breakdown = self.calculate_costs(opportunity)
        
        return {
            'estimated_time': total_time,
            'time_breakdown': estimated_times,
            'cost_breakdown': cost_breakdown,
            'start_date': datetime.now(),
            'end_date': datetime.now() + timedelta(days=total_time)
        }
