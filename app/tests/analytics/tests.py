# /home/pablo/app/tests/analytics/tests.py
#
# Pruebas para el módulo. Verifica la correcta funcionalidad de componentes específicos.

from django.test import TestCase
from django.utils import timezone
from app.models import Opportunity, Contract, Vacancy, Person
from app.ats.analytics.reports import AnalyticsEngine
from app.ats.views.analytics import AnalyticsDashboardView
from datetime import timedelta

class AnalyticsEngineTests(TestCase):
    def setUp(self):
        self.analytics = AnalyticsEngine()
        
        # Crear datos de prueba
        self.company = Person.objects.create(
            name="Test Company",
            email="test@company.com",
            phone="1234567890"
        )
        
        self.opportunity = Opportunity.objects.create(
            company=self.company,
            title="Test Opportunity",
            industry="tech",
            location="Mexico City",
            salary_range=100000,
            source="scraping",
            status="active"
        )
        
        self.vacancy = Vacancy.objects.create(
            opportunity=self.opportunity,
            title="Test Vacancy",
            salary=100000,
            location="Mexico City",
            seniority_level="senior"
        )
        
    def test_opportunity_conversion_report(self):
        """
        Testea la generación del reporte de conversión.
        """
        # Crear contrato para la oportunidad
        contract = Contract.objects.create(
            proposal=self.opportunity,
            status="SIGNED"
        )
        
        report = self.analytics.generate_opportunity_conversion_report()
        
        self.assertIn('total_scraped', report)
        self.assertIn('total_converted', report)
        self.assertIn('conversion_rate', report)
        self.assertIn('average_conversion_time', report)
        
    def test_industry_trends(self):
        """
        Testea la generación de tendencias por industria.
        """
        report = self.analytics.generate_industry_trends()
        
        self.assertIn('by_industry', report)
        self.assertIn('total_opportunities', report)
        self.assertIn('total_vacancies', report)
        
    def test_location_heatmap(self):
        """
        Testea la generación del heatmap de ubicaciones.
        """
        report = self.analytics.generate_location_heatmap()
        
        self.assertIn('locations', report)
        self.assertIn('total_opportunities', report)
        
    def test_prediction_accuracy(self):
        """
        Testea la precisión de las predicciones.
        """
        # Crear oportunidad con características específicas
        opportunity = Opportunity.objects.create(
            company=self.company,
            title="Senior Developer",
            industry="tech",
            location="Mexico City",
            salary_range=150000,
            source="scraping",
            status="active"
        )
        
        probability = self.analytics.predict_conversion_probability(opportunity)
        
        self.assertGreaterEqual(probability, 0)
        self.assertLessEqual(probability, 1)
