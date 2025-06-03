"""
Tests para el módulo TrajectoryAnalyzer.

Este módulo prueba las funcionalidades del analizador de trayectoria profesional,
verificando la predicción de rutas óptimas y análisis de carrera.
"""

import pytest
from unittest.mock import patch, MagicMock
import json
import asyncio
from datetime import datetime, date

from app.ats.talent.trajectory_analyzer import TrajectoryAnalyzer
from app.models import Person, Skill, Career, SkillAssessment

@pytest.mark.asyncio
async def test_predict_optimal_path_default():
    """Prueba el path predeterminado cuando no hay datos."""
    # Crear analizador con mock para que _get_person retorne None
    with patch('app.ats.talent.trajectory_analyzer.TrajectoryAnalyzer._get_person', return_value=None):
        analyzer = TrajectoryAnalyzer()
        result = await analyzer.predict_optimal_path(999)  # ID no existente
        
        # Verificar estructura básica del resultado predeterminado
        assert 'current_position' in result
        assert 'top_paths' in result
        assert 'critical_skills' in result
        assert isinstance(result['critical_skills'], list)
        assert 'financial_projection' in result
        assert 'analyzed_at' in result

@pytest.mark.asyncio
@patch('app.ats.talent.trajectory_analyzer.TrajectoryAnalyzer._get_person')
async def test_predict_optimal_path_basic(mock_get_person):
    """Prueba el análisis básico de trayectoria."""
    # Simular persona
    person = MagicMock()
    person.id = 1
    person.nombre = "Test User"
    person.current_position = "Analista"
    
    # Configurar mock
    mock_get_person.return_value = person
    
    # Patch adicionales para evitar llamadas a funciones no simuladas
    with patch('app.ats.utils.cv_generator.career_analyzer.CVCareerAnalyzer.analyze_career_potential') as mock_potential, \
         patch('app.ats.talent.trajectory_analyzer.TrajectoryAnalyzer._get_current_position') as mock_position, \
         patch('app.ats.talent.trajectory_analyzer.TrajectoryAnalyzer._generate_career_paths') as mock_paths, \
         patch('app.ats.talent.trajectory_analyzer.TrajectoryAnalyzer._calculate_financial_projection') as mock_financial, \
         patch('app.ats.talent.trajectory_analyzer.TrajectoryAnalyzer._predict_satisfaction') as mock_satisfaction, \
         patch('app.ats.talent.trajectory_analyzer.TrajectoryAnalyzer._analyze_market_demand') as mock_market, \
         patch('app.ats.talent.trajectory_analyzer.TrajectoryAnalyzer._calculate_development_difficulty') as mock_difficulty, \
         patch('app.ats.talent.trajectory_analyzer.TrajectoryAnalyzer._identify_critical_skills') as mock_skills, \
         patch('app.ats.talent.trajectory_analyzer.TrajectoryAnalyzer._recommend_mentors') as mock_mentors:
        
        # Configurar valores de retorno
        mock_potential.return_value = {}
        mock_position.return_value = "Analista"
        
        # Paths simulados para la carrera
        mock_paths.return_value = [
            [  # Path 1
                {'position': 'Analista', 'start_month': 0, 'end_month': 24, 'is_current': True},
                {'position': 'Analista Senior', 'start_month': 24, 'end_month': 48, 'is_current': False},
                {'position': 'Gerente', 'start_month': 48, 'end_month': 72, 'is_current': False}
            ]
        ]
        
        # Otras simulaciones
        mock_financial.return_value = {
            'initial_salary': 50000,
            'final_salary': 80000,
            'growth_amount': 30000,
            'growth_rate': 60,
            'projections': []
        }
        mock_satisfaction.return_value = 85
        mock_market.return_value = {'overall_demand': 80, 'position_demands': []}
        mock_difficulty.return_value = 65
        
        mock_skills.return_value = [
            {'name': 'Liderazgo', 'required_level': 85},
            {'name': 'Gestión de equipos', 'required_level': 80}
        ]
        
        mock_mentors.return_value = [
            {'name': 'Mentor 1', 'position': 'Gerente Senior', 'match_score': 85}
        ]
        
        # Ejecutar función a probar
        analyzer = TrajectoryAnalyzer()
        result = await analyzer.predict_optimal_path(1)
        
        # Verificar estructura y contenido del resultado
        assert result['person_id'] == 1
        assert result['current_position'] == 'Analista'
        assert len(result['top_paths']) > 0
        assert 'optimal_path' in result
        assert len(result['critical_skills']) == 2
        assert result['critical_skills'][0]['name'] == 'Liderazgo'
        assert 'financial_projection' in result
        assert result['financial_projection']['growth_rate'] == 60
        assert 'recommended_mentors' in result
        assert len(result['recommended_mentors']) == 1
        assert 'values_message' in result

@pytest.mark.asyncio
async def test_create_path_steps():
    """Prueba la creación de pasos en una trayectoria profesional."""
    analyzer = TrajectoryAnalyzer()
    current_position = "Analista"
    positions = ['Analista Senior', 'Gerente Junior', 'Gerente Senior']
    time_horizon = 60  # 5 años
    
    # Path estándar
    standard_path = analyzer._create_path_steps(
        current_position, 
        positions, 
        time_horizon
    )
    
    # Verificar estructura del path
    assert len(standard_path) == 4  # Posición actual + 3 futuras
    assert standard_path[0]['position'] == current_position
    assert standard_path[0]['is_current'] == True
    assert standard_path[-1]['position'] == positions[-1]
    
    # Path acelerado
    accelerated_path = analyzer._create_path_steps(
        current_position, 
        positions, 
        time_horizon,
        acceleration=0.7  # 30% más rápido
    )
    
    # Verificar que el path acelerado termina antes
    assert accelerated_path[-1]['end_month'] < standard_path[-1]['end_month']
    
    # Path especializado
    specialized_path = analyzer._create_path_steps(
        current_position,
        positions[:1],
        time_horizon,
        specialization=True
    )
    
    # Verificar que el path especializado tiene menos posiciones pero más tiempo en cada una
    assert len(specialized_path) <= len(standard_path)
    
@pytest.mark.asyncio
@patch('app.ats.talent.trajectory_analyzer.TrajectoryAnalyzer._get_person')
@patch('app.ats.talent.trajectory_analyzer.TrajectoryAnalyzer._get_person_skills')
async def test_identify_critical_skills(mock_get_skills, mock_get_person):
    """Prueba la identificación de habilidades críticas para una trayectoria."""
    # Configurar mocks
    mock_get_person.return_value = MagicMock()
    mock_get_skills.return_value = [
        {'name': 'Comunicación efectiva', 'level': 70},
        {'name': 'Análisis de datos', 'level': 65}
    ]
    
    # Path de ejemplo
    path = [
        {'position': 'Analista', 'start_month': 0, 'end_month': 24},
        {'position': 'Gerente', 'start_month': 24, 'end_month': 48}
    ]
    
    analyzer = TrajectoryAnalyzer()
    skills = await analyzer._identify_critical_skills(path, 1)
    
    # Verificar estructura y contenido
    assert isinstance(skills, list)
    assert len(skills) > 0
    
    # Verificar que las habilidades tienen los campos necesarios
    for skill in skills:
        assert 'name' in skill
        assert 'required_level' in skill
        assert isinstance(skill['required_level'], int)
        assert 0 <= skill['required_level'] <= 100
    
    # Verificar habilidades específicas para roles en el path
    skill_names = [skill['name'] for skill in skills]
    
    # Debe haber habilidades de liderazgo debido al rol de Gerente
    leadership_skills = ['Liderazgo', 'Gestión de equipos', 'Toma de decisiones']
    assert any(skill in skill_names for skill in leadership_skills)
    
    # Debe haber habilidades analíticas debido al rol de Analista
    analytical_skills = ['Análisis de datos', 'Atención al detalle']
    assert any(skill in skill_names for skill in analytical_skills)
