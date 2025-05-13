"""
Test para la integración de ML con Kanban y planes de desarrollo profesional.

Este módulo de pruebas verifica la correcta funcionalidad de la integración de ML
con el sistema Kanban, incluyendo la generación de planes de desarrollo.
"""

import pytest
import json
from unittest import mock
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.http import HttpResponse
from django.conf import settings

from app.models import Person, Vacante, BusinessUnit
from app.views.ml_admin_views import candidate_growth_plan_view, candidate_growth_plan_pdf_view
from app.kanban.ml_integration import (
    get_candidate_growth_data, 
    analyze_skill_gaps,
    get_vacancy_recommendations,
    _categorize_match_for_client,
    _categorize_potential_for_client,
    _calculate_development_complexity
)


@pytest.mark.django_db
class TestMLKanbanIntegration:
    """Pruebas para la integración de ML con Kanban."""
    
    @classmethod
    def setup_class(cls):
        """Configuración inicial para todas las pruebas."""
        # Establecer flag de características ML en True para tests
        settings.ENABLE_ML_FEATURES = True

    @pytest.fixture
    def sample_person(self):
        """Fixture para crear una persona de ejemplo."""
        business_unit = BusinessUnit.objects.create(
            nombre="huntRED",
            slug="huntred"
        )
        
        person = Person.objects.create(
            nombre="Test",
            apellido="Candidate",
            email="test@example.com",
            business_unit=business_unit
        )
        return person
    
    @pytest.fixture
    def sample_vacancy(self):
        """Fixture para crear una vacante de ejemplo."""
        business_unit = BusinessUnit.objects.get_or_create(
            nombre="huntRED",
            slug="huntred"
        )[0]
        
        vacancy = Vacante.objects.create(
            titulo="Test Developer",
            descripcion="Test description with Python, Django, and React skills",
            business_unit=business_unit,
            estado="activa"
        )
        return vacancy
    
    def test_analyze_skill_gaps(self, sample_person, sample_vacancy):
        """Prueba la función de análisis de brechas de habilidades."""
        # Ejecutar la función
        skill_gaps = analyze_skill_gaps(sample_person, sample_vacancy)
        
        # Verificaciones
        assert isinstance(skill_gaps, dict)
        assert 'candidate_skills' in skill_gaps
        assert 'required_skills' in skill_gaps
        assert 'missing_skills' in skill_gaps
        assert 'match_percentage' in skill_gaps
        assert isinstance(skill_gaps['match_percentage'], int)
        assert 0 <= skill_gaps['match_percentage'] <= 100
    
    def test_get_vacancy_recommendations(self, sample_person):
        """Prueba la función de recomendaciones de vacantes."""
        # Ejecutar la función
        recommendations = get_vacancy_recommendations(sample_person)
        
        # Verificaciones
        assert isinstance(recommendations, list)
        if recommendations:  # Si hay recomendaciones
            assert 'vacancy_id' in recommendations[0]
            assert 'title' in recommendations[0]
            assert 'match_score' in recommendations[0]
            assert 0 <= recommendations[0]['match_score'] <= 100
    
    def test_get_candidate_growth_data_consultant(self, sample_person):
        """Prueba la generación de plan de desarrollo para consultores."""
        # Ejecutar la función con audiencia consultor
        growth_data = get_candidate_growth_data(sample_person, audience_type='consultant')
        
        # Verificaciones para datos específicos de consultor
        assert isinstance(growth_data, dict)
        assert 'id' in growth_data
        assert 'name' in growth_data
        assert 'current_skills' in growth_data
        assert 'target_skills' in growth_data
        assert 'skill_gaps' in growth_data
        assert 'development_complexity' in growth_data
        assert 'market_demand' in growth_data
        assert 'salary_impact' in growth_data
        assert isinstance(growth_data['development_complexity'], dict)
    
    def test_get_candidate_growth_data_client(self, sample_person):
        """Prueba la generación de plan de desarrollo para clientes."""
        # Ejecutar la función con audiencia cliente
        growth_data = get_candidate_growth_data(sample_person, audience_type='client')
        
        # Verificaciones para datos específicos de cliente
        assert isinstance(growth_data, dict)
        assert 'id' in growth_data
        assert 'name' in growth_data
        assert 'current_match' in growth_data
        assert 'growth_potential' in growth_data
        assert 'strengths' in growth_data
        assert 'development_areas' in growth_data
        assert 'time_to_proficiency' in growth_data
        assert 'organizational_fit' in growth_data
        # Verificar que no contiene datos sensibles
        assert 'development_complexity' not in growth_data
        assert 'salary_impact' not in growth_data
    
    def test_get_candidate_growth_data_candidate(self, sample_person):
        """Prueba la generación de plan de desarrollo para candidatos."""
        # Ejecutar la función con audiencia candidato
        growth_data = get_candidate_growth_data(sample_person, audience_type='candidate')
        
        # Verificaciones para datos específicos de candidato
        assert isinstance(growth_data, dict)
        assert 'id' in growth_data
        assert 'name' in growth_data
        assert 'current_skills' in growth_data
        assert 'target_skills' in growth_data
        assert 'development_path' in growth_data
        assert 'recommended_resources' in growth_data
        assert 'strengths' in growth_data
        assert 'personalized_recommendations' in growth_data
        # Verificar que no contiene datos sensibles
        assert 'development_complexity' not in growth_data
        assert 'salary_impact' not in growth_data
    
    def test_helper_functions(self):
        """Prueba las funciones auxiliares de categorización."""
        # Probar categorización de match para cliente
        assert _categorize_match_for_client(95) == "Excelente"
        assert _categorize_match_for_client(85) == "Muy bueno"
        assert _categorize_match_for_client(75) == "Bueno"
        assert _categorize_match_for_client(65) == "Aceptable"
        assert _categorize_match_for_client(55) == "Requiere desarrollo"
        
        # Probar categorización de potencial para cliente
        assert _categorize_potential_for_client(90) == "Alto potencial"
        assert _categorize_potential_for_client(75) == "Buen potencial"
        assert _categorize_potential_for_client(60) == "Potencial moderado"
        assert _categorize_potential_for_client(45) == "Potencial limitado"
        
        # Probar cálculo de complejidad de desarrollo
        skill_gaps = {
            'missing_skills': ['Python', 'Django', 'React', 'Docker', 'AWS'],
            'match_percentage': 65
        }
        complexity = _calculate_development_complexity(skill_gaps)
        assert isinstance(complexity, dict)
        assert 'level' in complexity
        assert 'score' in complexity
        assert 'description' in complexity


@pytest.mark.django_db
class TestMLViews(TestCase):
    """Pruebas para las vistas relacionadas con ML."""
    
    def setUp(self):
        """Configuración inicial para cada prueba."""
        self.factory = RequestFactory()
        self.business_unit = BusinessUnit.objects.create(
            nombre="huntRED",
            slug="huntred"
        )
        self.person = Person.objects.create(
            nombre="Test",
            apellido="Candidate",
            email="test@example.com",
            business_unit=self.business_unit
        )
    
    @mock.patch('app.views.ml_admin_views._generate_candidate_growth_plan')
    def test_candidate_growth_plan_view(self, mock_generate_plan):
        """Prueba la vista del plan de desarrollo de candidato."""
        # Configurar el mock
        mock_generate_plan.return_value = {
            'id': self.person.id,
            'name': f"{self.person.nombre} {self.person.apellido}",
            'current_skills': ['Python', 'Django'],
            'target_skills': ['Python', 'Django', 'React'],
        }
        
        # Crear request
        url = reverse('ml_candidate_growth_plan', args=[self.person.id])
        request = self.factory.get(url)
        
        # Ejecutar vista
        response = candidate_growth_plan_view(request, self.person.id)
        
        # Verificaciones
        assert response.status_code == 200
        mock_generate_plan.assert_called_once()
    
    @mock.patch('app.views.ml_admin_views._generate_candidate_growth_plan')
    @mock.patch('app.views.ml_admin_views.HTML')
    @mock.patch('app.views.ml_admin_views.WEASYPRINT_AVAILABLE', True)
    def test_candidate_growth_plan_pdf_view(self, mock_html, mock_generate_plan):
        """Prueba la vista de generación de PDF del plan de desarrollo."""
        # Configurar los mocks
        mock_generate_plan.return_value = {
            'id': self.person.id,
            'name': f"{self.person.nombre} {self.person.apellido}",
            'current_skills': ['Python', 'Django'],
            'target_skills': ['Python', 'Django', 'React'],
        }
        
        mock_pdf = mock.MagicMock()
        mock_html.return_value.write_pdf.return_value = b'PDF content'
        mock_html.return_value = mock_pdf
        
        # Crear request
        url = reverse('ml_candidate_growth_plan_pdf', args=[self.person.id])
        request = self.factory.get(url)
        
        # Ejecutar vista
        response = candidate_growth_plan_pdf_view(request, self.person.id)
        
        # Verificaciones
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/pdf'
        assert 'attachment; filename=' in response['Content-Disposition']
        mock_generate_plan.assert_called_once()
        mock_html.assert_called_once()
        mock_pdf.write_pdf.assert_called_once()
