"""
Tests para el módulo TeamSynergyAnalyzer.

Este módulo prueba las funcionalidades del analizador de sinergia de equipos,
verificando análisis de composición de habilidades, personalidades y generaciones.
"""

import pytest
from unittest.mock import patch, MagicMock
import json
import asyncio
from datetime import datetime, date
import numpy as np

from app.com.talent.team_synergy import TeamSynergyAnalyzer
from app.models import Person, Skill, SkillAssessment, BusinessUnit

@pytest.mark.asyncio
async def test_analyze_team_synergy_empty():
    """Prueba el análisis con equipo vacío."""
    analyzer = TeamSynergyAnalyzer()
    result = await analyzer.analyze_team_synergy([])
    
    assert result['team_size'] == 0
    assert result['synergy_score'] == 50
    assert 'skills_analysis' in result
    assert 'personality_analysis' in result
    assert 'generation_analysis' in result
    assert 'purpose_analysis' in result
    assert 'analyzed_at' in result

@pytest.mark.asyncio
@patch('app.com.talent.team_synergy.TeamSynergyAnalyzer._get_team_members_data')
async def test_analyze_team_synergy_basic(mock_get_data):
    """Prueba el análisis básico de sinergia."""
    # Simular miembros del equipo
    mock_get_data.return_value = [
        {
            'id': 1,
            'name': 'Ana García',
            'position': 'Gerente',
            'personality': {'type': 'Director'},
            'skills': [
                {'name': 'Liderazgo', 'level': 85, 'category': 'Soft Skills'},
                {'name': 'Gestión de equipos', 'level': 80, 'category': 'Management'}
            ],
            'generation': 'Generación X',
            'purpose': {'primary_values': ['Innovación', 'Liderazgo'], 'primary_purpose': ['Profesional']}
        },
        {
            'id': 2,
            'name': 'Carlos López',
            'position': 'Analista',
            'personality': {'type': 'Analítico'},
            'skills': [
                {'name': 'Análisis de datos', 'level': 90, 'category': 'Technical'},
                {'name': 'Resolución de problemas', 'level': 85, 'category': 'Soft Skills'}
            ],
            'generation': 'Millennial',
            'purpose': {'primary_values': ['Crecimiento', 'Impacto'], 'primary_purpose': ['Profesional', 'Social']}
        }
    ]
    
    analyzer = TeamSynergyAnalyzer()
    result = await analyzer.analyze_team_synergy([1, 2])
    
    assert result['team_size'] == 2
    assert 'synergy_score' in result
    assert 'personality_analysis' in result
    assert 'generation_analysis' in result
    assert len(result['recommendations']) > 0

@pytest.mark.asyncio
@patch('app.com.talent.team_synergy.TeamSynergyAnalyzer._get_person')
async def test_get_team_members_data(mock_get_person):
    """Prueba la obtención de datos de miembros del equipo."""
    # Simular persona
    person = MagicMock()
    person.id = 1
    person.first_name = "Test"
    person.last_name = "User"
    person.current_position = "Analista"
    person.birth_date = date(1990, 1, 1)
    
    # Configurar el mock
    mock_get_person.return_value = person
    
    # Patch adicionales para evitar llamadas a funciones no simuladas
    with patch('app.com.talent.team_synergy.TeamSynergyAnalyzer._get_personality') as mock_personality, \
         patch('app.com.talent.team_synergy.TeamSynergyAnalyzer._get_person_skills') as mock_skills, \
         patch('app.com.talent.team_synergy.TeamSynergyAnalyzer._get_professional_purpose') as mock_purpose:
        
        # Configurar valores de retorno
        mock_personality.return_value = {'type': 'Analítico'}
        mock_skills.return_value = [{'name': 'Python', 'level': 85}]
        mock_purpose.return_value = {'primary_values': ['Crecimiento']}
        
        # Ejecutar función a probar
        analyzer = TeamSynergyAnalyzer()
        result = await analyzer._get_team_members_data([1])
        
        # Verificar resultados
        assert len(result) == 1
        assert result[0]['id'] == 1
        assert result[0]['name'] == "Test User"
        assert result[0]['generation'] == "Millennial"
        assert result[0]['personality']['type'] == 'Analítico'

@pytest.mark.asyncio
async def test_analyze_skill_composition():
    """Prueba el análisis de composición de habilidades."""
    # Datos de prueba
    members_data = [
        {
            'id': 1,
            'skills': [
                {'name': 'Liderazgo', 'level': 85, 'category': 'Soft Skills'},
                {'name': 'Comunicación', 'level': 80, 'category': 'Soft Skills'}
            ]
        },
        {
            'id': 2,
            'skills': [
                {'name': 'Análisis de datos', 'level': 90, 'category': 'Technical'},
                {'name': 'Programación', 'level': 85, 'category': 'Technical'}
            ]
        }
    ]
    
    analyzer = TeamSynergyAnalyzer()
    result = await analyzer._analyze_skill_composition(members_data)
    
    # Verificar estructura del resultado
    assert 'coverage_score' in result
    assert 'balance_score' in result
    assert 'skill_gaps' in result
    
    # Verificar que se detecten las categorías correctamente
    assert 'category_distribution' in result
    assert len(result['category_distribution']) == 2  # Soft Skills y Technical
    assert 'Technical' in result['category_distribution']
    assert 'Soft Skills' in result['category_distribution']
    
    # Test con lista vacía
    empty_result = await analyzer._analyze_skill_composition([])
    assert empty_result['coverage_score'] == 0
    assert empty_result['balance_score'] == 0
    assert empty_result['skill_gaps'] == []

@pytest.mark.asyncio
async def test_identify_decision_points():
    """Prueba la identificación de puntos de decisión en una trayectoria."""
    # Crear trayectoria de prueba
    path = [
        {'position': 'Analista', 'start_month': 0, 'end_month': 24, 'is_current': True},
        {'position': 'Analista Senior', 'start_month': 24, 'end_month': 48, 'is_current': False},
        {'position': 'Gerente', 'start_month': 48, 'end_month': 72, 'is_current': False}
    ]
    
    analyzer = TeamSynergyAnalyzer()
    # Usamos la misma lógica que en trajectory_analyzer ya que ambos usan la misma estructura
    from app.com.talent.trajectory_analyzer import TrajectoryAnalyzer
    trajectory_analyzer = TrajectoryAnalyzer()
    
    decision_points = trajectory_analyzer._identify_decision_points(path)
    
    # Verificar puntos de decisión
    assert len(decision_points) == 2  # Debe haber 2 puntos de decisión (transiciones)
    assert decision_points[0]['month'] == 21  # 3 meses antes del cambio
    assert decision_points[0]['current_position'] == 'Analista'
    assert decision_points[0]['next_position'] == 'Analista Senior'
    assert decision_points[1]['month'] == 45  # 3 meses antes del cambio
    assert decision_points[1]['next_position'] == 'Gerente'
    
    # Verificar que cada punto tiene opciones y actividades
    for point in decision_points:
        assert 'options' in point
        assert 'preparation_activities' in point
        assert len(point['options']) > 0
        assert len(point['preparation_activities']) > 0
