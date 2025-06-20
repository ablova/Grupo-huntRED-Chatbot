"""
Vistas para el Sistema AURA

Integra AURA en el dashboard de huntRED para mostrar
insights de red profesional y análisis de aura.
"""

import logging
from typing import Dict, Any, Optional
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
import asyncio
import json

from app.models import Person, BusinessUnit
from app.ats.models import Candidate, Job
from app.ml.aura.integration_layer import AuraIntegrationLayer
from app.ml.aura.models.gnn_models import GNNAnalyzer
from app.ml.aura.graph_builder import ProfessionalNetworkBuilder

logger = logging.getLogger(__name__)

# Inicializar componentes de AURA
aura_integration = AuraIntegrationLayer()
gnn_analyzer = GNNAnalyzer()
network_builder = ProfessionalNetworkBuilder()

@login_required
def aura_dashboard(request):
    """
    Dashboard principal de AURA.
    
    Muestra métricas generales, insights de red y análisis de aura.
    """
    try:
        # Obtener métricas generales de AURA
        aura_metrics = asyncio.run(aura_integration.get_aura_metrics())
        
        # Obtener estado de salud del sistema
        health_status = asyncio.run(aura_integration.get_aura_health())
        
        # Obtener estadísticas básicas
        total_candidates = Candidate.objects.count()
        total_jobs = Job.objects.count()
        total_people = Person.objects.count()
        
        context = {
            'aura_metrics': aura_metrics,
            'health_status': health_status,
            'total_candidates': total_candidates,
            'total_jobs': total_jobs,
            'total_people': total_people,
            'page_title': 'AURA - Inteligencia Relacional',
            'active_tab': 'aura_dashboard'
        }
        
        return render(request, 'ats/aura/dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error en dashboard de AURA: {str(e)}")
        messages.error(request, f"Error cargando dashboard de AURA: {str(e)}")
        return render(request, 'ats/aura/error.html', {'error': str(e)})

@login_required
def person_aura_view(request, person_id: int):
    """
    Vista detallada del aura de una persona.
    
    Muestra análisis completo de aura, red profesional y insights.
    """
    try:
        # Obtener persona
        person = get_object_or_404(Person, id=person_id)
        
        # Obtener datos enriquecidos de AURA
        person_data = asyncio.run(aura_integration.get_enriched_person_data(person_id))
        
        # Generar insights de red
        network_insights = asyncio.run(aura_integration.generate_network_insights(person_id))
        
        # Obtener análisis GNN
        network_data = asyncio.run(network_builder.build_professional_network(person_id))
        gnn_analysis = gnn_analyzer.analyze_professional_network(network_data)
        
        context = {
            'person': person,
            'person_data': person_data,
            'network_insights': network_insights,
            'gnn_analysis': gnn_analysis,
            'aura_score': person_data.get('aura_metrics', {}).get('overall_score', 0),
            'page_title': f'AURA de {person.name}',
            'active_tab': 'person_aura'
        }
        
        return render(request, 'ats/aura/person_aura.html', context)
        
    except Exception as e:
        logger.error(f"Error obteniendo aura de persona {person_id}: {str(e)}")
        messages.error(request, f"Error analizando aura: {str(e)}")
        return render(request, 'ats/aura/error.html', {'error': str(e)})

@login_required
def candidate_aura_view(request, candidate_id: int):
    """
    Vista del aura de un candidato.
    
    Muestra análisis de compatibilidad y recomendaciones.
    """
    try:
        # Obtener candidato
        candidate = get_object_or_404(Candidate, id=candidate_id)
        
        # Parámetros opcionales
        job_id = request.GET.get('job_id')
        
        # Analizar aura del candidato
        aura_analysis = asyncio.run(aura_integration.analyze_candidate_aura(
            candidate_id, job_id
        ))
        
        # Obtener trabajo si se especifica
        job = None
        if job_id:
            job = get_object_or_404(Job, id=job_id)
        
        context = {
            'candidate': candidate,
            'job': job,
            'aura_analysis': aura_analysis,
            'aura_score': aura_analysis.get('aura_score', 0),
            'compatibility_factors': aura_analysis.get('compatibility_factors', {}),
            'recommendations': aura_analysis.get('recommendations', []),
            'risk_factors': aura_analysis.get('risk_factors', []),
            'page_title': f'AURA de Candidato: {candidate.person.name}',
            'active_tab': 'candidate_aura'
        }
        
        return render(request, 'ats/aura/candidate_aura.html', context)
        
    except Exception as e:
        logger.error(f"Error analizando aura de candidato {candidate_id}: {str(e)}")
        messages.error(request, f"Error analizando candidato: {str(e)}")
        return render(request, 'ats/aura/error.html', {'error': str(e)})

@login_required
def job_aura_matches_view(request, job_id: int):
    """
    Vista de matches de aura para un trabajo.
    
    Muestra candidatos con mejor aura para un trabajo específico.
    """
    try:
        # Obtener trabajo
        job = get_object_or_404(Job, id=job_id)
        
        # Parámetros
        max_candidates = int(request.GET.get('max_candidates', 10))
        
        # Encontrar matches de aura
        aura_matches = asyncio.run(aura_integration.find_aura_matches(
            job_id, max_candidates
        ))
        
        context = {
            'job': job,
            'aura_matches': aura_matches,
            'matches_count': len(aura_matches),
            'max_candidates': max_candidates,
            'top_match': aura_matches[0] if aura_matches else None,
            'average_aura_score': sum(match['aura_score'] for match in aura_matches) / len(aura_matches) if aura_matches else 0,
            'page_title': f'Matches AURA para: {job.title}',
            'active_tab': 'job_matches'
        }
        
        return render(request, 'ats/aura/job_matches.html', context)
        
    except Exception as e:
        logger.error(f"Error encontrando matches para trabajo {job_id}: {str(e)}")
        messages.error(request, f"Error encontrando matches: {str(e)}")
        return render(request, 'ats/aura/error.html', {'error': str(e)})

@login_required
def network_insights_view(request, person_id: int):
    """
    Vista de insights de red profesional.
    
    Muestra análisis detallado de la red profesional de una persona.
    """
    try:
        # Obtener persona
        person = get_object_or_404(Person, id=person_id)
        
        # Generar insights de red
        network_insights = asyncio.run(aura_integration.generate_network_insights(person_id))
        
        # Detectar comunidades
        network_data = asyncio.run(network_builder.build_professional_network(person_id))
        communities_analysis = gnn_analyzer.detect_communities(network_data)
        
        # Análisis de influencia
        influence_analysis = gnn_analyzer.analyze_influence(network_data)
        
        context = {
            'person': person,
            'network_insights': network_insights,
            'communities_analysis': communities_analysis,
            'influence_analysis': influence_analysis,
            'network_strength': network_insights.get('network_strength', 0),
            'reputation_score': network_insights.get('reputation_score', 0),
            'key_connections': network_insights.get('key_connections', []),
            'network_hubs': network_insights.get('network_hubs', []),
            'page_title': f'Red Profesional de {person.name}',
            'active_tab': 'network_insights'
        }
        
        return render(request, 'ats/aura/network_insights.html', context)
        
    except Exception as e:
        logger.error(f"Error generando insights de red para persona {person_id}: {str(e)}")
        messages.error(request, f"Error analizando red: {str(e)}")
        return render(request, 'ats/aura/error.html', {'error': str(e)})

@login_required
def aura_communities_view(request):
    """
    Vista de comunidades detectadas por AURA.
    
    Muestra todas las comunidades profesionales detectadas en el sistema.
    """
    try:
        # Obtener todas las personas
        people = Person.objects.all()[:50]  # Limitar para performance
        
        communities_data = []
        
        for person in people:
            try:
                # Construir red profesional
                network_data = asyncio.run(network_builder.build_professional_network(person.id))
                
                # Detectar comunidades
                communities_analysis = gnn_analyzer.detect_communities(network_data)
                
                if communities_analysis.get('communities'):
                    communities_data.append({
                        'person': person,
                        'communities': communities_analysis.get('communities', [])
                    })
                    
            except Exception as e:
                logger.warning(f"Error analizando comunidades de persona {person.id}: {str(e)}")
                continue
        
        context = {
            'communities_data': communities_data,
            'total_communities': sum(len(data['communities']) for data in communities_data),
            'page_title': 'Comunidades Profesionales - AURA',
            'active_tab': 'communities'
        }
        
        return render(request, 'ats/aura/communities.html', context)
        
    except Exception as e:
        logger.error(f"Error analizando comunidades: {str(e)}")
        messages.error(request, f"Error analizando comunidades: {str(e)}")
        return render(request, 'ats/aura/error.html', {'error': str(e)})

@login_required
def aura_influencers_view(request):
    """
    Vista de influenciadores detectados por AURA.
    
    Muestra los principales influenciadores y hubs de la red profesional.
    """
    try:
        # Obtener todas las personas
        people = Person.objects.all()[:50]  # Limitar para performance
        
        influencers_data = []
        
        for person in people:
            try:
                # Construir red profesional
                network_data = asyncio.run(network_builder.build_professional_network(person.id))
                
                # Análisis de influencia
                influence_analysis = gnn_analyzer.analyze_influence(network_data)
                
                if influence_analysis.get('top_influencers'):
                    influencers_data.append({
                        'person': person,
                        'influence_analysis': influence_analysis,
                        'top_influencers': influence_analysis.get('top_influencers', [])
                    })
                    
            except Exception as e:
                logger.warning(f"Error analizando influencia de persona {person.id}: {str(e)}")
                continue
        
        context = {
            'influencers_data': influencers_data,
            'total_influencers': len(influencers_data),
            'page_title': 'Influenciadores Profesionales - AURA',
            'active_tab': 'influencers'
        }
        
        return render(request, 'ats/aura/influencers.html', context)
        
    except Exception as e:
        logger.error(f"Error analizando influenciadores: {str(e)}")
        messages.error(request, f"Error analizando influenciadores: {str(e)}")
        return render(request, 'ats/aura/error.html', {'error': str(e)})

@login_required
@require_http_methods(["POST"])
def validate_experience_view(request):
    """
    Vista para validar experiencia laboral.
    
    Permite validar experiencia usando referencias cruzadas de AURA.
    """
    try:
        # Obtener datos del request
        data = json.loads(request.body)
        person_id = data.get('person_id')
        company = data.get('company')
        position = data.get('position')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        # Validar parámetros requeridos
        if not all([person_id, company, position, start_date]):
            return JsonResponse({
                'error': 'Faltan parámetros requeridos',
                'required': ['person_id', 'company', 'position', 'start_date']
            }, status=400)
        
        # Validar experiencia
        validation_result = asyncio.run(aura_integration.validate_experience_cross_reference(
            person_id, company, position, start_date, end_date
        ))
        
        if 'error' in validation_result:
            return JsonResponse(validation_result, status=404)
        
        # Mostrar mensaje de éxito
        messages.success(request, f"Experiencia validada con confianza: {validation_result.get('overall_confidence', 0):.2%}")
        
        return JsonResponse(validation_result)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'JSON inválido en el request body',
            'status': 'error'
        }, status=400)
    except Exception as e:
        logger.error(f"Error validando experiencia: {str(e)}")
        messages.error(request, f"Error validando experiencia: {str(e)}")
        return JsonResponse({
            'error': str(e),
            'status': 'error'
        }, status=500)

@login_required
def aura_settings_view(request):
    """
    Vista de configuración de AURA.
    
    Permite configurar parámetros y conectores de AURA.
    """
    try:
        # Obtener estado de salud del sistema
        health_status = asyncio.run(aura_integration.get_aura_health())
        
        # Obtener métricas
        aura_metrics = asyncio.run(aura_integration.get_aura_metrics())
        
        context = {
            'health_status': health_status,
            'aura_metrics': aura_metrics,
            'page_title': 'Configuración AURA',
            'active_tab': 'aura_settings'
        }
        
        return render(request, 'ats/aura/settings.html', context)
        
    except Exception as e:
        logger.error(f"Error en configuración de AURA: {str(e)}")
        messages.error(request, f"Error cargando configuración: {str(e)}")
        return render(request, 'ats/aura/error.html', {'error': str(e)}) 