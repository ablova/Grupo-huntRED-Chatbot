from app.models import Opportunity, AnalyticsReport
from datetime import datetime, timedelta

class DataProduct:
    def __init__(self):
        self.time_window = timedelta(days=30)
        
    def get_top_industries(self, opportunities):
        """Obtiene las industrias más populares."""
        industries = {}
        for opp in opportunities:
            if opp.industry in industries:
                industries[opp.industry] += 1
            else:
                industries[opp.industry] = 1
        
        return sorted(industries.items(), key=lambda x: x[1], reverse=True)[:5]
        
    def get_salary_trends(self, opportunities):
        """Analiza las tendencias salariales."""
        salaries = {}
        for opp in opportunities:
            if opp.industry not in salaries:
                salaries[opp.industry] = []
            salaries[opp.industry].append(opp.salary_range)
        
        trends = {}
        for industry, salary_list in salaries.items():
            trends[industry] = {
                'average': sum(salary_list) / len(salary_list) if salary_list else 0,
                'min': min(salary_list) if salary_list else 0,
                'max': max(salary_list) if salary_list else 0
            }
        
        return trends
        
    def generate_market_report(self):
        """
        Genera un reporte del mercado laboral.
        """
        opportunities = Opportunity.objects.filter(
            created_at__gte=datetime.now() - self.time_window
        )
        
        return {
            'total_opportunities': opportunities.count(),
            'top_industries': self.get_top_industries(opportunities),
            'salary_trends': self.get_salary_trends(opportunities),
            'created_at': datetime.now()
        }
