"""
Vistas administrativas para el módulo ML.
Proporciona interfaces para analítica avanzada, predicciones y recomendaciones
basadas en los modelos de machine learning.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.db.models import Count, Avg, F, Q, Sum, Case, When, Value, IntegerField
from django.utils import timezone
from django.core.cache import cache
from asgiref.sync import sync_to_async

import logging
import json
import pandas as pd
import numpy as np
from datetime import timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.models import (
    Person, Vacante, Application, BusinessUnit, WorkflowStage
)
from app.models import (
    KanbanBoard, KanbanColumn, KanbanCard
)
from app.ml.ml_model import MatchmakingLearningSystem
from app.com.utils.logger_utils import get_module_logger

# Configurar logger
logger = get_module_logger('ml_admin')

# Función auxiliar para verificar permisos administrativos
def is_consultant_or_admin(user):
    """Verifica si el usuario es consultor o administrador."""
    if user.is_superuser:
        return True
    if hasattr(user, 'role'):
        return user.role in ['super_admin', 'consultant_complete']
    return False

@login_required
@user_passes_test(is_consultant_or_admin)
def ml_dashboard(request):
    """
    Dashboard principal de analítica predictiva ML.
    Muestra métricas clave, predicciones y recomendaciones.
    """
    # Obtener unidad de negocio del usuario actual (si aplica)
    business_unit = None
    if hasattr(request.user, 'business_unit'):
        business_unit = request.user.business_unit
    
    # Inicializar sistema ML
    ml_system = MatchmakingLearningSystem(business_unit=business_unit)
    
    # Obtener métricas clave - usando cache para optimizar rendimiento
    cache_key = f"ml_dashboard_metrics_{business_unit.id if business_unit else 'all'}"
    dashboard_data = cache.get(cache_key)
    
    if not dashboard_data:
        # Obtener vacantes activas
        if business_unit:
            vacantes_activas = Vacante.objects.filter(
                business_unit=business_unit,
                status='activa'
            )
        else:
            vacantes_activas = Vacante.objects.filter(status='activa')
        
        # Analizar vacantes por probabilidad de éxito
        vacantes_analizadas = []
        high_potential_vacancies = []
        low_potential_vacancies = []
        
        # Para cada vacante activa, calcular métricas clave
        for vacante in vacantes_activas[:50]:  # Limitar para rendimiento
            try:
                # Obtener candidatos que han aplicado
                applications = Application.objects.filter(vacancy=vacante)
                app_count = applications.count()
                
                # Calcular éxito histórico
                historical_success = Application.objects.filter(
                    vacancy__titulo__icontains=vacante.titulo,
                    status='contratado'
                ).count() / max(Application.objects.filter(
                    vacancy__titulo__icontains=vacante.titulo
                ).count(), 1)
                
                # Calcular tiempo promedio de llenado
                avg_time_to_fill = Application.objects.filter(
                    vacancy__titulo__icontains=vacante.titulo,
                    status='contratado'
                ).aggregate(
                    avg_days=Avg(F('updated_at') - F('applied_at'))
                )['avg_days'] or timedelta(days=30)
                
                # Calcular probabilidad de éxito
                success_probability = min(0.9, (app_count / 10) * historical_success)
                
                # Calcular vacantes similares
                similar_vacancies = []
                # Placeholder: aquí iría la lógica para encontrar vacantes similares
                
                vacancy_data = {
                    'id': vacante.id,
                    'titulo': vacante.titulo,
                    'empresa': vacante.empresa.nombre if hasattr(vacante, 'empresa') else 'N/A',
                    'salario': vacante.salario or 0,
                    'applications_count': app_count,
                    'success_probability': success_probability,
                    'avg_time_to_fill': avg_time_to_fill.days,
                    'similar_vacancies': similar_vacancies,
                    'required_skills': vacante.required_skills or []
                }
                vacantes_analizadas.append(vacancy_data)
                
                # Clasificar vacantes según potencial
                if success_probability > 0.7:
                    high_potential_vacancies.append(vacancy_data)
                elif success_probability < 0.3:
                    low_potential_vacancies.append(vacancy_data)
                
            except Exception as e:
                logger.error(f"Error procesando vacante {vacante.id}: {e}")
        
        # Obtener candidatos con posibilidades de crecimiento
        # Análisis de brecha de habilidades
        candidatos_con_potencial = []
        
        # Lógica simplificada - idealmente se haría con análisis más complejo
        recent_applications = Application.objects.all().order_by('-applied_at')[:100]
        
        for application in recent_applications:
            try:
                # Calcular score básico
                from app.ml.ml_model import calculate_match_percentage
                hard_skills_score = calculate_match_percentage(
                    application.user.skills, 
                    application.vacancy.required_skills
                )
                
                # Si el score es medio, podría haber potencial de crecimiento
                if 0.4 <= hard_skills_score <= 0.7:
                    # Identificar habilidades faltantes
                    missing_skills = [
                        skill for skill in application.vacancy.required_skills 
                        if skill not in application.user.skills
                    ]
                    
                    # Estimar tiempo de aprendizaje para cada habilidad
                    learning_paths = []
                    for skill in missing_skills[:3]:  # Limitar a 3 habilidades principales
                        # Placeholder: aquí iría un modelo más sofisticado
                        learning_paths.append({
                            'skill': skill,
                            'learning_time': "2-3 meses",
                            'resources': ["Cursos online", "Mentorías"]
                        })
                    
                    # Calcular potencial de crecimiento
                    growth_potential = min(0.9, hard_skills_score + 0.2)
                    
                    candidatos_con_potencial.append({
                        'id': application.user.id,
                        'name': f"{application.user.nombre} {application.user.apellido_paterno}",
                        'current_role': application.vacancy.titulo,
                        'current_match': hard_skills_score,
                        'growth_potential': growth_potential,
                        'missing_skills': missing_skills,
                        'learning_paths': learning_paths
                    })
            except Exception as e:
                logger.error(f"Error procesando candidato {application.user.id}: {e}")
        
        # Preparar datos para el dashboard
        dashboard_data = {
            'vacantes_analizadas': vacantes_analizadas,
            'high_potential_vacancies': high_potential_vacancies,
            'low_potential_vacancies': low_potential_vacancies,
            'candidates_growth': candidatos_con_potencial,
            'total_active_vacancies': vacantes_activas.count(),
            'total_active_applications': Application.objects.filter(
                vacancy__in=vacantes_activas).count(),
            'timestamp': timezone.now().isoformat()
        }
        
        # Guardar en caché para evitar recálculos frecuentes (15 minutos)
        cache.set(cache_key, dashboard_data, 900)
    
    # Contexto para la plantilla
    context = {
        'dashboard_data': dashboard_data,
        'page_title': 'Dashboard de Analítica Predictiva',
        'business_unit': business_unit.name if business_unit else 'Todas'
    }
    
    return render(request, 'ml/admin/dashboard.html', context)

@login_required
@user_passes_test(is_consultant_or_admin)
def vacancy_analysis(request, vacancy_id):
    """
    Análisis detallado de una vacante específica con predicciones.
    """
    vacancy = get_object_or_404(Vacante, id=vacancy_id)
    
    # Verificar permisos
    if hasattr(request.user, 'business_unit') and vacancy.business_unit != request.user.business_unit:
        if not request.user.is_superuser:
            return redirect('ml_dashboard')
    
    # Obtener análisis de la vacante - usando cache
    cache_key = f"ml_vacancy_analysis_{vacancy_id}"
    analysis_data = cache.get(cache_key)
    
    if not analysis_data:
        # Inicializar sistema ML
        ml_system = MatchmakingLearningSystem()
        
        # Obtener aplicaciones para esta vacante
        applications = Application.objects.filter(vacancy=vacancy)
        
        # Analizar candidatos que han aplicado
        candidates_analysis = []
        for app in applications:
            try:
                # Calcular score de ML
                score = ml_system.predict_candidate_success(app.user, vacancy)
                
                # Análisis de brecha
                current_skills = app.user.skills.split(',') if app.user.skills else []
                required_skills = vacancy.required_skills or []
                
                # Calcular habilidades faltantes y excedentes
                missing_skills = [s for s in required_skills if s not in current_skills]
                extra_skills = [s for s in current_skills if s not in required_skills]
                
                # Estimar tiempo de desarrollo para cerrar brecha
                development_time = len(missing_skills) * 1.5  # Estimación básica: 1.5 meses por habilidad
                
                candidates_analysis.append({
                    'candidate_id': app.user.id,
                    'name': f"{app.user.nombre} {app.user.apellido_paterno}",
                    'match_score': score,
                    'missing_skills': missing_skills,
                    'extra_skills': extra_skills[:5],  # Limitar a 5 para la UI
                    'development_time': development_time,
                    'development_potential': 0.8 if development_time < 6 else 0.5,
                    'application_date': app.applied_at.strftime('%Y-%m-%d')
                })
            except Exception as e:
                logger.error(f"Error analizando candidato {app.user.id}: {e}")
        
        # Ordenar por score de coincidencia (mejores primero)
        candidates_analysis = sorted(candidates_analysis, key=lambda x: x['match_score'], reverse=True)
        
        # Sugerir mejoras para la descripción de la vacante
        description_suggestions = []
        
        # Análisis básico de la descripción
        if len(vacancy.descripcion or "") < 500:
            description_suggestions.append("La descripción es muy corta, considere agregar más detalles.")
        
        if not vacancy.required_skills or len(vacancy.required_skills) < 3:
            description_suggestions.append("Especifique más habilidades requeridas para atraer candidatos calificados.")
        
        if not vacancy.salario:
            description_suggestions.append("Agregar un rango salarial puede aumentar las aplicaciones en un 30%.")
        
        # Buscar vacantes similares exitosas como referencia
        similar_successful_vacancies = Vacante.objects.filter(
            Q(titulo__icontains=vacancy.titulo.split()[0]) &
            Q(status='cerrada') &
            Q(application__status='contratado')
        ).distinct()[:5]
        
        success_references = []
        for ref in similar_successful_vacancies:
            success_references.append({
                'id': ref.id,
                'titulo': ref.titulo,
                'time_to_fill': (ref.fecha_cierre - ref.fecha_publicacion).days if ref.fecha_cierre and ref.fecha_publicacion else 30,
                'applications_count': ref.applications.count()
            })
        
        # Crear datos de análisis
        analysis_data = {
            'vacancy': {
                'id': vacancy.id,
                'titulo': vacancy.titulo,
                'empresa': vacancy.empresa.nombre if hasattr(vacancy, 'empresa') else 'N/A',
                'fecha_publicacion': vacancy.fecha_publicacion.strftime('%Y-%m-%d') if vacancy.fecha_publicacion else 'N/A',
                'salario': vacancy.salario or 'No especificado',
                'applications_count': applications.count()
            },
            'candidates_analysis': candidates_analysis,
            'description_suggestions': description_suggestions,
            'success_references': success_references,
            'predicted_time_to_fill': 30,  # Placeholder: aquí iría un modelo más sofisticado
            'recommended_actions': [
                "Contactar proactivamente a los 3 candidatos con mejor score",
                "Considerar ajustar las habilidades requeridas para ampliar el pool",
                "Promover la vacante en redes especializadas"
            ]
        }
        
        # Guardar en caché (30 minutos)
        cache.set(cache_key, analysis_data, 1800)
    
    # Contexto para la plantilla
    context = {
        'analysis': analysis_data,
        'page_title': f'Análisis de Vacante: {vacancy.titulo}'
    }
    
    return render(request, 'ml/admin/vacancy_analysis.html', context)

@login_required
@user_passes_test(is_consultant_or_admin)
def candidate_growth_plan(request, person_id):
    """
    Genera un plan de crecimiento para un candidato basado en análisis de brechas.
    """
    person = get_object_or_404(Person, id=person_id)
    
    # Verificar permisos
    if hasattr(request.user, 'business_unit') and hasattr(person, 'business_unit'):
        if person.business_unit != request.user.business_unit and not request.user.is_superuser:
            return redirect('ml_dashboard')
    
    # Obtener plan de crecimiento - usando cache
    cache_key = f"ml_growth_plan_{person_id}"
    growth_plan = cache.get(cache_key)
    
    if not growth_plan:
        # Inicializar sistema ML
        ml_system = MatchmakingLearningSystem()
        
        # Obtener aplicaciones recientes del candidato
        applications = Application.objects.filter(user=person).order_by('-applied_at')[:5]
        
        # Si no hay aplicaciones, redireccionar
        if not applications.exists():
            return redirect('ml_dashboard')
        
        # Obtener habilidades actuales del candidato
        current_skills = person.skills.split(',') if person.skills else []
        
        # Analizar brechas de habilidades con vacantes a las que aplicó
        skill_gaps = {}
        for app in applications:
            vacancy_skills = app.vacancy.required_skills or []
            for skill in vacancy_skills:
                if skill not in current_skills:
                    if skill in skill_gaps:
                        skill_gaps[skill] += 1
                    else:
                        skill_gaps[skill] = 1
        
        # Ordenar habilidades por frecuencia
        priority_skills = sorted(skill_gaps.items(), key=lambda x: x[1], reverse=True)
        
        # Generar plan de aprendizaje
        learning_paths = []
        for skill, frequency in priority_skills[:5]:  # Top 5 habilidades
            difficulty = "Alta" if skill in ["Machine Learning", "Data Science", "Blockchain"] else "Media"
            learning_paths.append({
                'skill': skill,
                'frequency': frequency,
                'difficulty': difficulty,
                'estimated_time': "3-6 meses" if difficulty == "Alta" else "1-3 meses",
                'resources': [
                    "Cursos online especializados",
                    "Proyectos prácticos",
                    "Mentoría con expertos"
                ]
            })
        
        # Buscar roles potenciales con las habilidades actuales
        potential_roles = []
        current_skills_set = set(current_skills)
        
        # Buscar vacantes donde el candidato tenga al menos 60% de match
        potential_vacancies = Vacante.objects.filter(status='activa')[:50]  # Limitar para rendimiento
        
        for vacancy in potential_vacancies:
            required_skills = set(vacancy.required_skills or [])
            if not required_skills:
                continue
                
            match_percentage = len(current_skills_set.intersection(required_skills)) / len(required_skills)
            
            if match_percentage >= 0.6:
                potential_roles.append({
                    'vacancy_id': vacancy.id,
                    'title': vacancy.titulo,
                    'company': vacancy.empresa.nombre if hasattr(vacancy, 'empresa') else 'N/A',
                    'match_percentage': match_percentage * 100,
                    'missing_skills': list(required_skills - current_skills_set)
                })
        
        # Ordenar roles potenciales por porcentaje de match
        potential_roles = sorted(potential_roles, key=lambda x: x['match_percentage'], reverse=True)
        
        # Calcular tiempo estimado para alcanzar roles superiores
        career_projection = []
        
        # Simplificado: esto podría ser mucho más sofisticado con un modelo real
        if applications.exists():
            current_role = applications.first().vacancy.titulo
            current_level = 1
            
            # Determinar nivel actual aproximado
            if "Senior" in current_role:
                current_level = 3
            elif "Semi-senior" in current_role or "Middle" in current_role:
                current_level = 2
            
            # Proyectar crecimiento
            if current_level < 3:
                career_projection.append({
                    'target_level': "Senior" if current_level == 2 else "Semi-senior",
                    'estimated_time': "1-2 años" if current_level == 2 else "2-3 años",
                    'key_skills_to_develop': priority_skills[:3] if priority_skills else ["Liderazgo", "Gestión de proyectos"]
                })
            
            # Proyección para roles gerenciales
            career_projection.append({
                'target_level': "Gerencial",
                'estimated_time': "3-5 años",
                'key_skills_to_develop': ["Liderazgo de equipos", "Gestión estratégica", "Negociación"]
            })
        
        # Crear plan de crecimiento
        growth_plan = {
            'person': {
                'id': person.id,
                'name': f"{person.nombre} {person.apellido_paterno}",
                'current_skills': current_skills,
                'current_role': applications.first().vacancy.titulo if applications.exists() else "No especificado"
            },
            'skill_gaps': dict(priority_skills),
            'learning_paths': learning_paths,
            'potential_roles': potential_roles[:5],  # Top 5 roles
            'career_projection': career_projection,
            'recommendations': [
                "Enfocarse en desarrollar primero las habilidades técnicas de alta frecuencia",
                "Complementar con habilidades blandas (comunicación, trabajo en equipo)",
                "Considerar certificaciones relevantes para validar conocimientos"
            ]
        }
        
        # Guardar en caché (1 hora)
        cache.set(cache_key, growth_plan, 3600)
    
    # Contexto para la plantilla
    context = {
        'growth_plan': growth_plan,
        'page_title': f'Plan de Crecimiento: {person.nombre} {person.apellido_paterno}'
    }
    
    return render(request, 'ml/admin/candidate_growth_plan.html', context)

# API para obtener datos para gráficos interactivos
@login_required
@user_passes_test(is_consultant_or_admin)
def api_dashboard_charts(request):
    """API para obtener datos para gráficos del dashboard."""
    # Obtener unidad de negocio del usuario
    business_unit = None
    if hasattr(request.user, 'business_unit'):
        business_unit = request.user.business_unit
    
    # Obtener datos de caché
    cache_key = f"ml_dashboard_charts_{business_unit.id if business_unit else 'all'}"
    chart_data = cache.get(cache_key)
    
    if not chart_data:
        # Filtrar por unidad de negocio si es necesario
        vacancies_filter = Q(status='activa')
        if business_unit:
            vacancies_filter &= Q(business_unit=business_unit)
        
        # Obtener datos para gráficos
        vacancies = Vacante.objects.filter(vacancies_filter)
        
        # 1. Distribución de vacantes por probabilidad de éxito
        success_prob_data = {
            'labels': ['Alta (>70%)', 'Media (40-70%)', 'Baja (<40%)'],
            'data': [0, 0, 0]  # Placeholder
        }
        
        # 2. Habilidades más demandadas
        skills_demand = {}
        for vacancy in vacancies:
            for skill in (vacancy.required_skills or []):
                if skill in skills_demand:
                    skills_demand[skill] += 1
                else:
                    skills_demand[skill] = 1
        
        top_skills = sorted(skills_demand.items(), key=lambda x: x[1], reverse=True)[:10]
        skills_chart_data = {
            'labels': [skill for skill, count in top_skills],
            'data': [count for skill, count in top_skills]
        }
        
        # 3. Tiempo promedio para llenar vacantes por nivel
        time_to_fill = {
            'labels': ['Junior', 'Semi-senior', 'Senior', 'Gerencial'],
            'data': [20, 35, 45, 60]  # Placeholder
        }
        
        # Combinar datos
        chart_data = {
            'success_probability': success_prob_data,
            'skills_demand': skills_chart_data,
            'time_to_fill': time_to_fill
        }
        
        # Guardar en caché (30 minutos)
        cache.set(cache_key, chart_data, 1800)
    
    return JsonResponse(chart_data)
