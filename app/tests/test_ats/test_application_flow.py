import pytest
from app.models import Application, Vacante, Person, BusinessUnit, Interview
from datetime import datetime, timedelta

def create_test_data():
    # Crear datos de prueba
    business_unit = BusinessUnit.objects.create(name="test_bu")
    person = Person.objects.create(nombre="Test")
    
    # Crear vacante
    vacante = Vacante.objects.create(
        titulo="Test Position",
        empresa_id=1,
        business_unit=business_unit,
        fecha_publicacion=datetime.now()
    )
    
    return business_unit, person, vacante

@pytest.fixture
def test_data():
    return create_test_data()

def test_application_creation(test_data):
    """Test que verifica la creación de una aplicación"""
    business_unit, person, vacante = test_data
    
    application = Application.objects.create(
        user=person,
        vacancy=vacante,
        status="applied"
    )
    
    assert application.status == "applied"
    assert application.user == person

def test_interview_scheduling(test_data):
    """Test que verifica el agendamiento de entrevistas"""
    business_unit, person, vacante = test_data
    
    interview = Interview.objects.create(
        person=person,
        job=vacante.empresa,
        interview_date=datetime.now() + timedelta(days=1),
        interview_type="virtual"
    )
    
    assert interview.candidate_confirmed is False
    assert interview.location_verified is False

def test_application_status_changes(test_data):
    """Test que verifica los cambios de estado de la aplicación"""
    business_unit, person, vacante = test_data
    
    application = Application.objects.create(
        user=person,
        vacancy=vacante,
        status="applied"
    )
    
    # Cambiar a entrevista
    application.status = "interview"
    application.save()
    
    assert application.status == "interview"
    
    # Cambiar a contratado
    application.status = "hired"
    application.save()
    
    assert application.status == "hired"
