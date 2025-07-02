from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from app.ml.aura.upskilling.skill_gap_analyzer import SkillGapAnalyzer
from app.ml.aura.organizational.network_analyzer import NetworkAnalyzer
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from app.ml.aura.core import gpt  # Ajusta el import según la ubicación real de gpt.py
from app.ml.aura.analytics.gpt_usage_tracker import get_gpt_usage_stats  # Supón que existe o crea un tracker

User = get_user_model()

@login_required
def attrition_dashboard_view(request):
    analyzer = NetworkAnalyzer()
    # Lógica para análisis global por segmento
    result = analyzer.predict_turnover_risk()
    context = {
        'attrition_summary': result.get('summary', []),
        'attrition_metrics': result.get('risk_metrics', {}),
        'attrition_alerts': result.get('alerts', []),
        'attrition_recommendations': result.get('retention_strategies', []),
        'business_unit': request.user.business_unit.name if hasattr(request.user, 'business_unit') else 'Todas',
    }
    return render(request, 'aura/dashboard/attrition_dashboard.html', context)

@login_required
def skills_dashboard_view(request):
    analyzer = SkillGapAnalyzer()
    # Lógica para análisis global de skills emergentes
    # Aquí deberías agregar lógica para obtener datos agregados por segmento
    result = analyzer.analyze_global() if hasattr(analyzer, 'analyze_global') else {}
    context = {
        'skills_summary': result.get('summary', []),
        'skills_metrics': result.get('growth_metrics', {}),
        'skills_gap_metrics': result.get('gap_metrics', {}),
        'skills_decline': result.get('decline_skills', []),
        'skills_recommendations': result.get('recommendations', []),
        'business_unit': request.user.business_unit.name if hasattr(request.user, 'business_unit') else 'Todas',
    }
    return render(request, 'aura/dashboard/skills_dashboard.html', context)

@login_required
def user_attrition_dashboard_view(request, user_id=None):
    user = request.user if user_id is None else get_object_or_404(User, id=user_id)
    analyzer = NetworkAnalyzer()
    # Lógica para análisis individual
    result = analyzer.predict_turnover_risk(business_unit=user.business_unit.name if hasattr(user, 'business_unit') else None)
    user_result = next((e for e in result.get('at_risk_employees', []) if e['id'] == user.id), {})
    context = {
        'user_attrition': {
            'score': user_result.get('risk_score', 0),
            'risk_level': user_result.get('risk_level', 'N/A'),
            'risk_factors': user_result.get('risk_factors', []),
            'alerts': user_result.get('alerts', []),
            'recommendations': user_result.get('retention_strategies', []),
            'segment_avg': result.get('risk_metrics', {}).get('segment_avg', 0)
        }
    }
    return render(request, 'aura/dashboard/user_attrition_dashboard.html', context)

@login_required
def user_skills_dashboard_view(request, user_id=None):
    user = request.user if user_id is None else get_object_or_404(User, id=user_id)
    analyzer = SkillGapAnalyzer()
    # Define el perfil objetivo según lógica de negocio
    target_profile = {}  # Completa según lógica de negocio
    result = analyzer.analyze(user_id=str(user.id), target_profile=target_profile, notify=False, gamify=False)
    context = {
        'user_skills': {
            'gaps': [f"{k}: gap de {v['gap']}" for k, v in result.get('gaps', {}).items()],
            'recommendations': result.get('recommendations', []),
            'explainability': [v for v in result.get('explainability', {}).values()],
            'gap_score': sum(v['gap'] for v in result.get('gaps', {}).values()),
            'segment_avg': result.get('segment_avg', 0)
        }
    }
    return render(request, 'aura/dashboard/user_skills_dashboard.html', context)

# --- NUEVAS VISTAS INNOVADORAS (stubs para desarrollo incremental) ---

@login_required
def talent_copilot_view(request):
    """Vista para el Copiloto de Talento (AI Talent Copilot)"""
    # Aquí se integrará el chatbot avanzado y lógica de copiloto
    return render(request, 'aura/dashboard/talent_copilot.html', {})

@login_required
def whatif_simulator_view(request):
    """Vista para el Simulador de Decisiones What If"""
    # Aquí se integrará la lógica de simulación de escenarios
    return render(request, 'aura/dashboard/whatif_simulator.html', {})

@login_required
def opportunities_risks_panel_view(request):
    """Panel de Oportunidades y Riesgos en Tiempo Real"""
    # Aquí se mostrarán oportunidades, focos rojos y quick wins
    return render(request, 'aura/dashboard/opportunities_risks_panel.html', {})

@login_required
def storytelling_report_view(request):
    """Vista para Storytelling Automático y Reportes Narrativos"""
    # Aquí se generarán resúmenes automáticos y reportes en lenguaje natural
    return render(request, 'aura/dashboard/storytelling_report.html', {})

@login_required
def gamification_panel_view(request):
    """Panel de Gamificación Social y Retos"""
    # Aquí se mostrarán retos, logros, ranking y badges
    return render(request, 'aura/dashboard/gamification_panel.html', {})

@login_required
def cv_generator_view(request):
    """Generador de CVs, Cartas y Propuestas con IA"""
    # Aquí se integrará la IA generativa para documentos
    return render(request, 'aura/dashboard/cv_generator.html', {})

@login_required
def interactive_dei_panel_view(request):
    """Panel DEI Interactivo con simuladores de impacto"""
    # Aquí se mostrarán visualizaciones y simuladores de DEI
    return render(request, 'aura/dashboard/interactive_dei_panel.html', {})

@login_required
def api_webhooks_panel_view(request):
    """Panel/API para integración y webhooks"""
    # Aquí se documentará y gestionará la API y webhooks
    return render(request, 'aura/dashboard/api_webhooks_panel.html', {})

@login_required
def innovation_panel_view(request):
    """Panel de Innovación y Colaboración"""
    # Aquí se mostrarán métricas y visualizaciones de innovación
    return render(request, 'aura/dashboard/innovation_panel.html', {})

@login_required
def social_impact_panel_view(request):
    """Panel de Impacto Social y Sostenibilidad"""
    # Aquí se mostrarán métricas ESG y sugerencias de impacto
    return render(request, 'aura/dashboard/social_impact_panel.html', {})

@login_required
def cockpit_dashboard_view(request):
    """Vista centralizada del cockpit, con datos agregados y storytelling generado por GPT."""
    # 1. Llamar analyzers y servicios internos solo una vez
    analyzers_data = {
        'rotacion': NetworkAnalyzer().predict_turnover_risk(),
        'skills': SkillGapAnalyzer().analyze_global() if hasattr(SkillGapAnalyzer(), 'analyze_global') else {},
        # ...agrega más analyzers según necesidad
    }
    # 2. Preparar resumen para GPT
    resumen = {
        'rotacion': analyzers_data['rotacion'].get('summary', []),
        'skills': analyzers_data['skills'].get('summary', []),
        # ...otros resúmenes
    }
    # 3. Llamar a GPT.py solo una vez para storytelling
    storytelling = gpt.generate_storytelling(resumen)
    # 4. Obtener métricas de uso de GPT
    gpt_usage = get_gpt_usage_stats()  # Debe devolver dict con totales, por proveedor, canal, BU, cliente
    context = {
        'analyzers_data': analyzers_data,
        'storytelling': storytelling,
        'gpt_usage': gpt_usage,
        'business_unit': request.user.business_unit.name if hasattr(request.user, 'business_unit') else 'Todas',
    }
    return render(request, 'aura/dashboard/cockpit_dashboard.html', context) 