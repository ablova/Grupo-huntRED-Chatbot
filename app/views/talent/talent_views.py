"""
Vistas para el módulo de Talent de Grupo huntRED®.

Este módulo implementa las vistas para todas las funcionalidades
de análisis de talento, siguiendo el patrón asíncrono y respetando
la seguridad basada en roles.
"""

import logging
import json
import asyncio
from datetime import datetime

from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.template.loader import get_template
from django.conf import settings
from asgiref.sync import sync_to_async

from app.com.talent.trajectory_analyzer import TrajectoryAnalyzer
from app.com.talent.team_synergy import TeamSynergyAnalyzer
from app.com.talent.cultural_fit import CulturalFitAnalyzer
from app.com.talent.learning_engine import LearningEngine
from app.com.talent.mentor_matcher import MentorMatcher
from app.models import Person, BusinessUnit, Role
from app.utils.decorators import check_role_access

logger = logging.getLogger(__name__)

@login_required
@require_http_methods(["POST"])
@check_role_access(["Super Admin", "Consultant BU Complete", "Consultant BU Division"])
async def analyze_team_synergy(request):
    """
    API para analizar sinergia de equipo.
    
    Analiza la sinergia entre los miembros de un equipo existente o propuesto,
    considerando habilidades, personalidad, generación y propósito.
    """
    try:
        data = json.loads(request.body)
        team_members = data.get('team_members', [])
        business_unit = data.get('business_unit')
        
        # Verificar acceso a la unidad de negocio específica
        if not await check_bu_access(request.user, business_unit):
            return JsonResponse({
                'error': 'No tienes permisos para acceder a esta unidad de negocio'
            }, status=403)
        
        # Verificar que los miembros existan
        if not await validate_team_members(team_members):
            return JsonResponse({
                'error': 'Uno o más miembros del equipo no existen'
            }, status=400)
        
        analyzer = TeamSynergyAnalyzer()
        result = await analyzer.analyze_team_synergy(team_members, business_unit)
        
        # Registrar actividad para auditoría
        await log_activity(
            request.user.id, 
            'analyze_team_synergy', 
            f"Análisis de sinergia para {len(team_members)} miembros en {business_unit}"
        )
        
        return JsonResponse(result)
    except Exception as e:
        logger.error(f"Error en analyze_team_synergy: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["GET"])
@check_role_access(["Super Admin", "Consultant BU Complete", "Consultant BU Division"])
async def analyze_career_trajectory(request, person_id):
    """
    API para analizar trayectoria profesional.
    
    Predice la trayectoria profesional óptima para un candidato,
    incluyendo posiciones futuras, habilidades críticas y
    puntos de decisión clave.
    """
    try:
        business_unit = request.GET.get('business_unit')
        time_horizon = int(request.GET.get('time_horizon', 60))
        
        # Verificar acceso a la unidad de negocio específica
        if not await check_bu_access(request.user, business_unit):
            return JsonResponse({
                'error': 'No tienes permisos para acceder a esta unidad de negocio'
            }, status=403)
        
        # Verificar que la persona exista
        if not await person_exists(person_id):
            return JsonResponse({
                'error': 'La persona no existe'
            }, status=404)
        
        analyzer = TrajectoryAnalyzer(business_unit)
        result = await analyzer.predict_optimal_path(
            person_id,
            time_horizon=time_horizon
        )
        
        # Registrar actividad para auditoría
        await log_activity(
            request.user.id, 
            'analyze_career_trajectory', 
            f"Análisis de trayectoria para persona {person_id} en {business_unit}"
        )
        
        return JsonResponse(result)
    except Exception as e:
        logger.error(f"Error en analyze_career_trajectory: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
@check_role_access(["Super Admin", "Consultant BU Complete", "Consultant BU Division"])
async def analyze_cultural_fit(request):
    """
    API para analizar compatibilidad cultural.
    
    Evalúa la compatibilidad cultural entre un candidato y una empresa,
    considerando valores, dimensiones culturales y prácticas organizacionales.
    """
    try:
        data = json.loads(request.body)
        person_id = data.get('person_id')
        company_id = data.get('company_id')
        business_unit = data.get('business_unit')
        
        # Verificación de acceso y existencia
        if not await check_bu_access(request.user, business_unit):
            return JsonResponse({
                'error': 'No tienes permisos para acceder a esta unidad de negocio'
            }, status=403)
        
        if not await person_exists(person_id):
            return JsonResponse({'error': 'La persona no existe'}, status=404)
        
        # Realizar análisis
        analyzer = CulturalFitAnalyzer()
        result = await analyzer.analyze_cultural_fit(
            person_id, 
            company_id,
            business_unit
        )
        
        # Registrar actividad
        await log_activity(
            request.user.id, 
            'analyze_cultural_fit', 
            f"Análisis de fit cultural entre persona {person_id} y empresa {company_id}"
        )
        
        return JsonResponse(result)
    except Exception as e:
        logger.error(f"Error en analyze_cultural_fit: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["GET"])
@check_role_access(["Super Admin", "Consultant BU Complete", "Consultant BU Division"])
async def generate_learning_plan(request, person_id):
    """
    API para generar plan de aprendizaje personalizado.
    
    Crea una secuencia personalizada de aprendizaje basada en
    brechas de habilidades, preferencias y objetivos profesionales.
    """
    try:
        context = request.GET.get('context', 'job_search')
        business_unit = request.GET.get('business_unit')
        
        # Verificaciones
        if not await check_bu_access(request.user, business_unit):
            return JsonResponse({
                'error': 'No tienes permisos para acceder a esta unidad de negocio'
            }, status=403)
        
        if not await person_exists(person_id):
            return JsonResponse({'error': 'La persona no existe'}, status=404)
        
        # Generar plan
        engine = LearningEngine()
        result = await engine.generate_learning_sequence(
            person_id,
            context=context
        )
        
        # Registrar actividad
        await log_activity(
            request.user.id, 
            'generate_learning_plan', 
            f"Plan de aprendizaje para persona {person_id} en contexto {context}"
        )
        
        return JsonResponse(result)
    except Exception as e:
        logger.error(f"Error en generate_learning_plan: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["GET"])
@check_role_access(["Super Admin", "Consultant BU Complete", "Consultant BU Division"])
async def find_mentors(request, person_id):
    """
    API para encontrar mentores óptimos.
    
    Encuentra los mentores más compatibles para un candidato,
    basándose en objetivos profesionales, personalidad y áreas de expertise.
    """
    try:
        goal = request.GET.get('goal')
        business_unit = request.GET.get('business_unit')
        mentoring_type = request.GET.get('mentoring_type')
        limit = int(request.GET.get('limit', 5))
        
        # Verificaciones
        if not await check_bu_access(request.user, business_unit):
            return JsonResponse({
                'error': 'No tienes permisos para acceder a esta unidad de negocio'
            }, status=403)
        
        if not await person_exists(person_id):
            return JsonResponse({'error': 'La persona no existe'}, status=404)
        
        # Buscar mentores
        matcher = MentorMatcher()
        result = await matcher.find_optimal_mentors(
            person_id,
            goal=goal,
            business_unit=business_unit,
            mentoring_type=mentoring_type,
            limit=limit
        )
        
        # Registrar actividad
        await log_activity(
            request.user.id, 
            'find_mentors', 
            f"Búsqueda de mentores para persona {person_id} con objetivo {goal}"
        )
        
        return JsonResponse(result)
    except Exception as e:
        logger.error(f"Error en find_mentors: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["GET"])
@check_role_access(["Super Admin", "Consultant BU Complete"])
async def generate_talent_report(request, analysis_type, entity_id):
    """
    API para generar informes en PDF.
    
    Genera informes profesionales en PDF basados en los diferentes
    análisis de talento disponibles en el sistema.
    
    Args:
        analysis_type: Tipo de análisis ('team_synergy', 'career', 'cultural_fit', etc.)
        entity_id: ID de la entidad analizada (equipo, persona, etc.)
    """
    try:
        business_unit = request.GET.get('business_unit')
        include_graphics = request.GET.get('include_graphics', 'true').lower() == 'true'
        
        # Verificaciones
        if not await check_bu_access(request.user, business_unit):
            return JsonResponse({
                'error': 'No tienes permisos para acceder a esta unidad de negocio'
            }, status=403)
        
        # Obtener datos del análisis según el tipo
        analysis_data = await get_analysis_data(analysis_type, entity_id, business_unit)
        if not analysis_data:
            return JsonResponse({'error': 'No se encontraron datos del análisis'}, status=404)
        
        # Generar PDF
        pdf_content = await generate_pdf_report(
            analysis_type,
            analysis_data,
            include_graphics
        )
        
        # Crear respuesta con el PDF
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="talent_report_{analysis_type}_{entity_id}.pdf"'
        
        # Registrar actividad
        await log_activity(
            request.user.id, 
            'generate_talent_report', 
            f"Generación de informe {analysis_type} para {entity_id}"
        )
        
        return response
    except Exception as e:
        logger.error(f"Error en generate_talent_report: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

# Funciones auxiliares

async def check_bu_access(user, business_unit):
    """Verifica si el usuario tiene acceso a una unidad de negocio específica."""
    from app.models import UserRole
    
    if not business_unit:
        return True  # Si no se especifica BU, se asume acceso
        
    try:
        # Obtener roles del usuario
        user_roles = await sync_to_async(list)(
            UserRole.objects.filter(user=user).select_related('role')
        )
        
        # Super Admin tiene acceso a todo
        if any(ur.role.name == "Super Admin" for ur in user_roles):
            return True
            
        # Consultant BU Complete tiene acceso a su BU completa
        for ur in user_roles:
            if ur.role.name == "Consultant BU Complete" and ur.business_unit.name == business_unit:
                return True
                
        # Consultant BU Division tiene acceso a sus divisiones dentro de la BU
        for ur in user_roles:
            if ur.role.name == "Consultant BU Division" and ur.business_unit.name == business_unit:
                # Verificar división específica - omitido para simplicidad
                return True
                
        return False
    except Exception as e:
        logger.error(f"Error verificando acceso a BU: {str(e)}")
        return False

async def person_exists(person_id):
    """Verifica si una persona existe en la base de datos."""
    try:
        from app.models import Person
        return await sync_to_async(Person.objects.filter(id=person_id).exists)()
    except Exception as e:
        logger.error(f"Error verificando existencia de persona: {str(e)}")
        return False

async def validate_team_members(member_ids):
    """Verifica que todos los miembros del equipo existan."""
    try:
        for member_id in member_ids:
            if not await person_exists(member_id):
                return False
        return True
    except Exception as e:
        logger.error(f"Error validando miembros del equipo: {str(e)}")
        return False

async def log_activity(user_id, activity_type, description):
    """Registra una actividad en el sistema para auditoría."""
    try:
        from app.models import ActivityLog
        
        await sync_to_async(ActivityLog.objects.create)(
            user_id=user_id,
            activity_type=activity_type,
            description=description,
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error registrando actividad: {str(e)}")

async def get_analysis_data(analysis_type, entity_id, business_unit=None):
    """Obtiene los datos de un análisis específico según su tipo."""
    try:
        if analysis_type == 'team_synergy':
            # Obtener IDs de miembros del equipo
            from app.models import Team, TeamMember
            
            team = await sync_to_async(Team.objects.get)(id=entity_id)
            team_members = await sync_to_async(list)(
                TeamMember.objects.filter(team=team).values_list('person_id', flat=True)
            )
            
            # Realizar análisis
            analyzer = TeamSynergyAnalyzer()
            return await analyzer.analyze_team_synergy(team_members, business_unit)
            
        elif analysis_type == 'career':
            # Análisis de carrera
            analyzer = TrajectoryAnalyzer(business_unit)
            return await analyzer.predict_optimal_path(entity_id)
            
        elif analysis_type == 'cultural_fit':
            # Extraer IDs de candidato y empresa
            person_id, company_id = entity_id.split('_')
            
            # Análisis de fit cultural
            analyzer = CulturalFitAnalyzer()
            return await analyzer.analyze_cultural_fit(
                int(person_id), 
                int(company_id),
                business_unit
            )
            
        # Otros tipos de análisis...
        
        return None
    except Exception as e:
        logger.error(f"Error obteniendo datos de análisis: {str(e)}")
        return None

async def generate_pdf_report(analysis_type, analysis_data, include_graphics=True):
    """
    Genera un informe en PDF basado en los datos del análisis.
    
    Utiliza las plantillas HTML existentes y WeasyPrint para
    generar informes profesionales con gráficos y visualizaciones.
    """
    try:
        from weasyprint import HTML, CSS
        from django.template.loader import render_to_string
        import tempfile
        import os
        
        # Determinar plantilla según tipo de análisis
        template_mapping = {
            'team_synergy': 'reports/team_synergy_report.html',
            'career': 'reports/career_trajectory_report.html',
            'cultural_fit': 'reports/cultural_fit_report.html',
            'learning_plan': 'reports/learning_plan_report.html',
            'mentor_match': 'reports/mentor_match_report.html'
        }
        
        template_name = template_mapping.get(analysis_type, 'reports/general_report.html')
        
        # Preparar contexto para la plantilla
        context = {
            'analysis_data': analysis_data,
            'report_type': analysis_type,
            'include_graphics': include_graphics,
            'generated_at': datetime.now().strftime('%d-%m-%Y %H:%M'),
            'business_unit': analysis_data.get('business_unit', 'huntRED')
        }
        
        # Renderizar plantilla HTML
        html_string = render_to_string(template_name, context)
        
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as temp_file:
            temp_filename = temp_file.name
            temp_file.write(html_string.encode('utf-8'))
        
        # Configurar CSS para el PDF
        css = CSS(string='''
            @page {
                size: letter;
                margin: 1.5cm;
                @bottom-right {
                    content: "Página " counter(page) " de " counter(pages);
                    font-size: 10pt;
                }
            }
            body {
                font-family: 'Helvetica', 'Arial', sans-serif;
                line-height: 1.5;
            }
            .header-logo {
                width: 200px;
                height: auto;
            }
            .section {
                margin-top: 20px;
                margin-bottom: 20px;
            }
            .chart-container {
                width: 100%;
                height: 300px;
                margin: 20px 0;
            }
            table {
                width: 100%;
                border-collapse: collapse;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }
            th {
                background-color: #f2f2f2;
            }
        ''')
        
        # Generar PDF
        pdf = HTML(filename=temp_filename).write_pdf(stylesheets=[css])
        
        # Limpiar archivo temporal
        os.unlink(temp_filename)
        
        return pdf
    except Exception as e:
        logger.error(f"Error generando PDF: {str(e)}")
        # Devolver un PDF básico en caso de error
        return b'%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Resources<<>>/Contents 4 0 R/Parent 2 0 R>>endobj 4 0 obj<</Length 23>>stream\nBT /F1 12 Tf 100 700 Td (Error generating report) Tj ET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000015 00000 n \n0000000061 00000 n \n0000000114 00000 n \n0000000212 00000 n \ntrailer<</Size 5/Root 1 0 R>>\nstartxref\n287\n%%EOF'
