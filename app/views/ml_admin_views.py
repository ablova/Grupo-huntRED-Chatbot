import datetime
import json
import os
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_http_methods
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.core.cache import cache
from django.template.loader import render_to_string
from django.conf import settings

from app.ats.utilidades.decorators import rbac_required
from app.models import Vacante, Person, BusinessUnit
from app.ml.core.models.base import MatchmakingLearningSystem, MatchmakingModel, TransitionModel, MarketAnalysisModel
from app.ats.kanban.ml_integration import get_vacancy_recommendations, get_candidate_growth_data, analyze_skill_gaps

# Opcional: Importar weasyprint solo si está disponible (para generar PDFs)
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

class MLDashboardView(TemplateView):
    template_name = 'ml/admin/dashboard.html'
    
    @method_decorator(login_required)
    @method_decorator(rbac_required(["super_admin", "consultant_complete"]))
    def get(self, request, *args, **kwargs):
        # Optimizando chatbot workflow para BU-specific processing
        bu_param = request.GET.get('bu', 'all')
        
        # Usamos caché para optimizar rendimiento
        cache_key = f"ml_dashboard_{bu_param}"
        dashboard_data = cache.get(cache_key)
        
        if not dashboard_data:
            # Creando contexto con datos del modelo ML
            dashboard_data = {
                'total_active_vacancies': Vacante.objects.filter(estado='activa').count(),
                'total_active_applications': self._get_active_applications_count(bu_param),
                'high_potential_vacancies': self._get_high_potential_vacancies(bu_param),
                'candidates_growth': self._get_candidates_with_growth_potential(bu_param),
                'low_potential_vacancies': self._get_low_potential_vacancies(bu_param),
                'timestamp': datetime.datetime.now()
            }
            
            # Guardamos en caché por 30 minutos
            cache.set(cache_key, dashboard_data, 60 * 30)
        
        context = {
            'dashboard_data': dashboard_data,
            'business_unit': bu_param.upper() if bu_param != 'all' else 'Todas'
        }
        
        return self.render_to_response(context)
    
    def _get_active_applications_count(self, business_unit='all'):
        """Obtiene el número total de aplicaciones activas."""
        # Implementación real conectaría con el sistema de aplicaciones
        return 327  # Ejemplo, debería obtenerse de la base de datos
    
    def _get_high_potential_vacancies(self, business_unit='all'):
        """Obtiene vacantes con alta probabilidad de éxito basadas en ML."""
        # Ejemplo de datos para visualización, en producción se usaría el modelo real
        ml_system = MatchmakingLearningSystem()
        
        vacantes = Vacante.objects.filter(estado='activa')
        if business_unit != 'all':
            try:
                bu = BusinessUnit.objects.get(slug=business_unit)
                vacantes = vacantes.filter(business_unit=bu)
            except BusinessUnit.DoesNotExist:
                pass
        
        # Limitamos a 5 vacantes para el ejemplo
        vacantes = vacantes[:5]  
        
        high_potential = []
        for v in vacantes:
            # En producción, estas métricas vendrían del modelo ML
            vacancy_data = {
                'id': v.id,
                'titulo': v.titulo,
                'empresa': v.empresa,
                'success_probability': min(85, 60 + v.id % 30),  # Simulación
                'applications_count': min(25, 5 + v.id % 20),
                'avg_time_to_fill': 30 + v.id % 15,
                'required_skills': self._get_skills_from_vacancy(v)
            }
            high_potential.append(vacancy_data)
        
        # Ordenamos por probabilidad de éxito descendente
        return sorted(high_potential, key=lambda x: x['success_probability'], reverse=True)
    
    def _get_candidates_with_growth_potential(self, business_unit='all'):
        """Obtiene candidatos con potencial de crecimiento profesional."""
        # Ejemplo de datos para visualización
        candidates = Person.objects.all()[:5]  # Limitamos a 5 para el ejemplo
        
        potential_candidates = []
        for c in candidates:
            # En producción, estos datos vendrían del análisis ML
            candidate_data = {
                'id': c.id,
                'name': f"{c.nombre} {c.apellido}",
                'current_role': getattr(c, 'puesto_actual', 'Desarrollador') or 'Profesional',
                'current_match': 60 + c.id % 25,  # Simulación
                'growth_potential': 75 + c.id % 20,  # Simulación
                'missing_skills': self._get_example_skills(3 + c.id % 2)
            }
            potential_candidates.append(candidate_data)
        
        return sorted(potential_candidates, key=lambda x: x['growth_potential'], reverse=True)
    
    def _get_low_potential_vacancies(self, business_unit='all'):
        """Obtiene vacantes con problemas potenciales basadas en ML."""
        # Ejemplo similar al de high_potential pero con vacantes problemáticas
        vacantes = Vacante.objects.filter(estado='activa')
        if business_unit != 'all':
            try:
                bu = BusinessUnit.objects.get(slug=business_unit)
                vacantes = vacantes.filter(business_unit=bu)
            except BusinessUnit.DoesNotExist:
                pass
        
        # Limitamos a 5 vacantes para el ejemplo y excluimos las primeras que ya usamos
        vacantes = vacantes[5:10] if len(vacantes) > 10 else vacantes[:5]
        
        low_potential = []
        for v in vacantes:
            # En producción, estas métricas vendrían del modelo ML
            vacancy_data = {
                'id': v.id,
                'titulo': v.titulo,
                'empresa': v.empresa,
                'success_probability': max(20, 45 - v.id % 25),  # Simulación
                'applications_count': max(1, 5 - v.id % 4),
            }
            low_potential.append(vacancy_data)
        
        # Ordenamos por probabilidad de éxito ascendente
        return sorted(low_potential, key=lambda x: x['success_probability'])
    
    def _get_skills_from_vacancy(self, vacancy):
        """Extrae habilidades requeridas de una vacante."""
        skills = getattr(vacancy, 'skills_required', None)
        if not skills:
            return self._get_example_skills(4 + vacancy.id % 3)
        
        if isinstance(skills, str):
            try:
                return json.loads(skills)
            except:
                pass
        
        return skills if isinstance(skills, list) else self._get_example_skills(4 + vacancy.id % 3)
    
    def _get_example_skills(self, count=5):
        """Genera una lista de habilidades de ejemplo."""
        all_skills = [
            "Python", "Django", "React", "JavaScript", "AWS", 
            "Docker", "Kubernetes", "SQL", "NoSQL", "MongoDB", 
            "Redis", "REST APIs", "GraphQL", "CI/CD", "Git",
            "Flask", "FastAPI", "Node.js", "Express", "Vue.js",
            "Angular", "TypeScript", "Java", "Spring", "Hibernate",
            "PHP", "Laravel", "C#", ".NET", "Azure", 
            "GCP", "Terraform", "Ansible", "Jenkins", "GitHub Actions",
            "Scrum", "Kanban", "Agile", "TDD", "BDD",
            "Machine Learning", "Data Science", "Big Data", "Hadoop", "Spark"
        ]
        
        # Seleccionamos un subconjunto aleatorio basado en count
        return [all_skills[i % len(all_skills)] for i in range(count)]

# Vista para el análisis detallado de vacantes
@login_required
@rbac_required(["super_admin", "consultant_complete"])
def vacancy_analysis_view(request, vacancy_id):
    """Análisis detallado para una vacante específica."""
    vacancy = get_object_or_404(Vacante, id=vacancy_id)
    
    # Preparando análisis de la vacante
    analysis = {
        'vacancy': vacancy,
        'candidates_analysis': _get_candidates_for_vacancy(vacancy),
        'predicted_time_to_fill': 35 + vacancy.id % 15,  # Simulación
        'success_references': _get_similar_successful_vacancies(vacancy),
        'recommended_actions': _get_recommended_actions_for_vacancy(vacancy),
        'description_suggestions': _get_description_suggestions(vacancy)
    }
    
    return render(request, 'ml/admin/vacancy_analysis.html', {
        'analysis': analysis
    })

# Vista para el plan de crecimiento de candidatos
@login_required
@rbac_required(["super_admin", "consultant_complete"])
def candidate_growth_plan_view(request, candidate_id):
    """Plan de desarrollo profesional para un candidato."""
    candidate = get_object_or_404(Person, id=candidate_id)
    
    # Determinar la audiencia objetivo del plan de crecimiento
    audience = request.GET.get('audience', 'consultant')
    if audience not in ['consultant', 'client', 'candidate']:
        audience = 'consultant'
    
    # Flag para indicar si es para compartir con candidato (usado en la plantilla)
    for_candidate = audience == 'candidate' or request.GET.get('for_candidate') == 'true'
    
    # Obtener datos para el plan de crecimiento según audiencia
    growth_data = get_candidate_growth_data(candidate, audience_type=audience)
    
    template = 'ml/admin/candidate_growth_plan.html'
    if for_candidate and audience == 'candidate':
        template = 'ml/candidate/growth_plan.html'
    
    return render(request, template, {
        'candidate': growth_data,
        'audience': audience,
        'for_candidate': for_candidate,
        'timestamp': datetime.datetime.now()
    })

# Vista para generar un plan de crecimiento para candidatos (versión para candidatos)
@login_required
def candidate_growth_plan_pdf_view(request, candidate_id):
    """Genera un PDF con el plan de desarrollo profesional para compartir con el candidato."""
    candidate = get_object_or_404(Person, id=candidate_id)
    
    # Determinar audiencia objetivo (por defecto candidato para PDF)
    audience = request.GET.get('audience', 'candidate')
    
    # Obtener datos para el plan de crecimiento según audiencia
    growth_data = get_candidate_growth_data(candidate, audience_type=audience)
    
    # Flag para indicar que se generará un PDF
    for_pdf = True
    
    # Renderizar la plantilla HTML
    template = 'ml/candidate/growth_plan.html' if audience == 'candidate' else 'ml/admin/candidate_growth_plan.html'
    html_string = render_to_string(template, {
        'candidate': growth_data,
        'audience': audience,
        'for_pdf': for_pdf,
        'for_candidate': audience == 'candidate',
        'timestamp': datetime.datetime.now()
    })
    
    # Generar nombre de archivo para el PDF
    filename = f"Plan_Desarrollo_{candidate.nombre}_{candidate.apellido}.pdf"
    
    # Si weasyprint está disponible, generar PDF
    if WEASYPRINT_AVAILABLE:
        # Crear directorio temporal si no existe
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        # Ruta del archivo PDF
        pdf_file = os.path.join(temp_dir, filename)
        
        # Generar PDF
        HTML(string=html_string).write_pdf(pdf_file)
        
        # Devolver el PDF como respuesta
        with open(pdf_file, 'rb') as pdf:
            response = HttpResponse(pdf.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
    else:
        # Si weasyprint no está disponible, redirigir a la versión HTML
        return redirect(f'/ml/candidate/{candidate_id}/growth/?audience={audience}&for_candidate=true')

# API para datos de gráficos del dashboard
@require_GET
@login_required
@rbac_required(["super_admin", "consultant_complete"])
def dashboard_charts_api_view(request):
    """API endpoint para proporcionar datos de gráficos para el dashboard de ML."""
    # Obtener la unidad de negocio seleccionada
    bu_param = request.GET.get('bu', 'all')
    
    # Caché para optimizar rendimiento
    cache_key = f"ml_dashboard_charts_{bu_param}"
    chart_data = cache.get(cache_key)
    
    if not chart_data:
        # Preparar datos para los gráficos
        chart_data = {
            'skills_demand': _get_skills_demand_data(bu_param),
            'time_to_fill': _get_time_to_fill_data(bu_param)
        }
        
        # Guardar en caché por 1 hora
        cache.set(cache_key, chart_data, 60 * 60)
    
    return JsonResponse(chart_data)

# Funciones auxiliares
def _get_candidates_for_vacancy(vacancy):
    """Analiza candidatos para una vacante específica."""
    # Simulación de datos para la visualización
    candidates = Person.objects.all()[:4]  # Limitamos a 4 para el ejemplo
    
    candidates_analysis = []
    for idx, c in enumerate(candidates):
        # Simulamos análisis para la visualización
        match_score = 85 - (idx * 15)  # 85%, 70%, 55%, 40%
        
        candidates_analysis.append({
            'candidate_id': c.id,
            'name': f"{c.nombre} {c.apellido}",
            'application_date': (datetime.datetime.now() - datetime.timedelta(days=idx*3)).strftime('%Y-%m-%d'),
            'match_score': match_score,
            'missing_skills': _get_example_skills(2 + idx),
            'extra_skills': _get_example_skills(1 + idx),
            'development_potential': max(0.2, 0.9 - (idx * 0.15)),
            'development_time': 3 + (idx * 2)
        })
    
    return candidates_analysis

def _get_similar_successful_vacancies(vacancy):
    """Encuentra vacantes similares exitosas como referencia."""
    # Simulación para la visualización
    return [
        {
            'titulo': f"Vacante similar {i+1} a {vacancy.titulo}",
            'time_to_fill': 25 + (i * 5),
            'applications_count': 15 + (i * 3)
        } for i in range(3)
    ]

def _get_recommended_actions_for_vacancy(vacancy):
    """Genera recomendaciones para mejorar una vacante."""
    # Estas recomendaciones podrían generarse con NLP en producción
    return [
        "Ajustar el rango salarial para alinearlo mejor con el mercado actual.",
        "Simplificar los requisitos técnicos para atraer más candidatos calificados.",
        "Destacar los beneficios de desarrollo profesional en la descripción.",
        "Incluir información sobre la cultura de la empresa y el ambiente de trabajo."
    ]

def _get_description_suggestions(vacancy):
    """Sugiere mejoras para la descripción de la vacante."""
    # Estas sugerencias podrían generarse con NLP en producción
    return [
        "Agregar información más específica sobre responsabilidades diarias.",
        "Incluir tecnologías específicas para atraer candidatos más calificados.",
        "Añadir información sobre la cultura de la empresa y oportunidades de crecimiento.",
        "Especificar los beneficios y compensaciones de manera más detallada."
    ]

def _generate_candidate_growth_plan(candidate, for_candidate=False):
    """Genera un plan de crecimiento profesional para un candidato."""
    # En producción, estos datos vendrían del sistema ML
    current_skills = _get_example_skills(5 + (candidate.id % 3))
    target_skills = _get_example_skills(7 + (candidate.id % 4))
    
    # Calculamos las habilidades que faltan (diferencia entre target y current)
    skill_gaps = [skill for skill in target_skills if skill not in current_skills]
    
    # Simulamos una ruta de desarrollo profesional
    development_path = [
        {
            'title': 'Adquisición de Habilidades Fundamentales',
            'timeframe': '1-3 meses',
            'description': 'Enfoque en adquirir conocimientos básicos en las tecnologías principales requeridas.',
            'skills': skill_gaps[:2] if skill_gaps else [],
            'status': 'completed'
        },
        {
            'title': 'Desarrollo de Competencias Avanzadas',
            'timeframe': '3-6 meses',
            'description': 'Profundizar en habilidades específicas y aplicarlas en contextos prácticos.',
            'skills': skill_gaps[2:4] if len(skill_gaps) > 2 else [],
            'status': 'current'
        },
        {
            'title': 'Especialización y Aplicación Práctica',
            'timeframe': '6-12 meses',
            'description': 'Consolidar conocimientos y desarrollar un área de especialización.',
            'skills': skill_gaps[4:] if len(skill_gaps) > 4 else [],
            'status': 'future'
        }
    ]
    
    # Simulamos recursos recomendados para el aprendizaje
    recommended_resources = [
        {
            'type': 'course',
            'title': f"Masterclass en {skill_gaps[0] if skill_gaps else 'Desarrollo Profesional'}",
            'provider': 'Udemy',
            'description': f"Curso completo que cubre todos los aspectos de {skill_gaps[0] if skill_gaps else 'desarrollo profesional'}.",
            'duration': '40 horas',
            'rating': 4.7,
            'reviews': 1243,
            'skills': skill_gaps[:2] if skill_gaps else [],
            'url': '#'
        },
        {
            'type': 'certification',
            'title': f"Certificación Profesional en {skill_gaps[1] if len(skill_gaps) > 1 else 'Tecnologías Emergentes'}",
            'provider': 'Coursera',
            'description': 'Programa de certificación reconocido en la industria.',
            'duration': '3 meses',
            'rating': 4.9,
            'reviews': 856,
            'skills': skill_gaps[1:3] if len(skill_gaps) > 1 else [],
            'url': '#'
        },
        {
            'type': 'book',
            'title': f"Guía Completa de {skill_gaps[2] if len(skill_gaps) > 2 else 'Desarrollo de Carrera'}",
            'provider': 'O\'Reilly Media',
            'description': 'Libro de referencia con ejemplos prácticos y casos de estudio.',
            'duration': 'N/A',
            'rating': 4.5,
            'reviews': 412,
            'skills': skill_gaps[2:4] if len(skill_gaps) > 2 else [],
            'url': '#'
        }
    ]
    
    # Proyección de carrera profesional
    career_path = [
        {
            'title': 'Senior Developer',
            'timeframe': '1-2 años',
            'match': 85,
            'badge_class': 'success'
        },
        {
            'title': 'Tech Lead',
            'timeframe': '2-4 años',
            'match': 70,
            'badge_class': 'primary'
        },
        {
            'title': 'Engineering Manager',
            'timeframe': '4-6 años',
            'match': 60,
            'badge_class': 'info'
        }
    ]
    
    # Si es para el candidato, ajustamos la información
    if for_candidate:
        # Eliminamos datos sensibles o internos
        recommended_resources = recommended_resources[:2]  # Menos recursos
        career_path = career_path[:2]  # Trayectoria más corta
    
    # Datos completos del plan de crecimiento
    return {
        'id': candidate.id,
        'name': f"{candidate.nombre} {candidate.apellido}",
        'current_role': getattr(candidate, 'puesto_actual', 'Desarrollador') or 'Profesional',
        'current_company': getattr(candidate, 'empresa_actual', 'Empresa') or 'Empresa',
        'last_updated': datetime.datetime.now().strftime('%Y-%m-%d'),
        'experience_years': 3 + (candidate.id % 5),
        'current_match': 75,
        'growth_potential': 90,
        'current_skills': current_skills,
        'target_skills': target_skills,
        'skill_gaps': skill_gaps,
        'development_path': development_path,
        'recommended_resources': recommended_resources,
        'career_path': career_path,
        'recommended_vacancies': _get_recommended_vacancies_for_candidate(candidate),
        'personalized_recommendations': _get_personalized_recommendations(candidate)
    }

def _get_recommended_vacancies_for_candidate(candidate):
    """Obtiene vacantes recomendadas para un candidato."""
    # Simulamos vacantes recomendadas
    vacantes = Vacante.objects.filter(estado='activa')[:3]  # Limitamos a 3
    
    return [
        {
            'id': v.id,
            'title': v.titulo,
            'company': v.empresa,
            'match': 90 - (i * 8)  # 90%, 82%, 74%
        } for i, v in enumerate(vacantes)
    ]

def _get_personalized_recommendations(candidate):
    """Genera recomendaciones personalizadas para el candidato."""
    # Estas recomendaciones podrían generarse con ML en producción
    return [
        {
            'title': 'Enfoque en Habilidades Técnicas',
            'description': 'Basado en tu perfil, fortalecer tus habilidades en Cloud Computing y DevOps te daría una ventaja competitiva significativa.'
        },
        {
            'title': 'Certificaciones Recomendadas',
            'description': 'Considera obtener certificaciones en AWS o Azure para validar tus conocimientos y mejorar tu empleabilidad.'
        },
        {
            'title': 'Redes Profesionales',
            'description': 'Amplía tu red profesional participando en eventos y comunidades relacionadas con tu campo.'
        }
    ]

def _get_skills_demand_data(business_unit='all'):
    """Obtiene las habilidades más demandadas basadas en las vacantes activas."""
    # Para simplificar, usamos datos de ejemplo
    skills_data = {
        'labels': [
            'JavaScript', 'Python', 'React', 'AWS', 'DevOps',
            'Node.js', 'SQL', 'Docker', 'Git', 'Agile'
        ],
        'data': [85, 78, 72, 65, 60, 55, 52, 48, 45, 40]
    }
    
    return skills_data

def _get_time_to_fill_data(business_unit='all'):
    """Obtiene el tiempo promedio para llenar vacantes por categoría."""
    # Datos de ejemplo para la visualización
    time_data = {
        'labels': ['Tecnología', 'Ventas', 'Marketing', 'Finanzas', 'Recursos Humanos'],
        'data': [45, 30, 35, 40, 25]
    }
    
    return time_data

def _get_example_skills(count=5):
    """Genera una lista de habilidades de ejemplo."""
    all_skills = [
        "Python", "Django", "React", "JavaScript", "AWS", 
        "Docker", "Kubernetes", "SQL", "NoSQL", "MongoDB", 
        "Redis", "REST APIs", "GraphQL", "CI/CD", "Git",
        "Flask", "FastAPI", "Node.js", "Express", "Vue.js",
        "Angular", "TypeScript", "Java", "Spring", "Hibernate",
        "PHP", "Laravel", "C#", ".NET", "Azure", 
        "GCP", "Terraform", "Ansible", "Jenkins", "GitHub Actions",
        "Scrum", "Kanban", "Agile", "TDD", "BDD",
        "Machine Learning", "Data Science", "Big Data", "Hadoop", "Spark"
    ]
    
    # Seleccionamos un subconjunto aleatorio basado en count
    import random
    random.seed(count)  # Para consistencia
    return [all_skills[i % len(all_skills)] for i in range(count)]

@require_http_methods(["POST"])
def train_matchmaking_model(request, business_unit):
    try:
        model = MatchmakingModel(business_unit=business_unit)
        data = model.prepare_training_data()
        model.train_model(data)
        
        return JsonResponse({
            'success': True,
            'message': f'Modelo de matchmaking entrenado para {business_unit}'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@require_http_methods(["POST"])
def train_transition_model(request, business_unit):
    try:
        model = TransitionModel(business_unit=business_unit)
        data = model.prepare_training_data()
        model.train_model(data)
        
        return JsonResponse({
            'success': True,
            'message': f'Modelo de transición entrenado para {business_unit}'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@require_http_methods(["POST"])
def train_market_model(request, business_unit):
    try:
        model = MarketAnalysisModel(business_unit=business_unit)
        data = model.prepare_training_data()
        model.train_model(data)
        
        return JsonResponse({
            'success': True,
            'message': f'Modelo de análisis de mercado entrenado para {business_unit}'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@require_http_methods(["GET"])
def model_status(request):
    try:
        business_units = BusinessUnit.objects.all()
        status = {}
        
        for bu in business_units:
            matchmaking_model = MatchmakingModel(business_unit=bu.name)
            transition_model = TransitionModel(business_unit=bu.name)
            market_model = MarketAnalysisModel(business_unit=bu.name)
            
            status[bu.name] = {
                'matchmaking': matchmaking_model.is_trained(),
                'transition': transition_model.is_trained(),
                'market': market_model.is_trained()
            }
        
        return JsonResponse({
            'success': True,
            'status': status
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
