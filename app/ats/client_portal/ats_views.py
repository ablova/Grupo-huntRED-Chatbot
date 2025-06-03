# app/client_portal/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from django.contrib import messages
from datetime import timedelta

from app.ats.ats.models import Company, Proposal, Vacante
from app.ats.ats.pricing.models import ServiceCalculation, Payment
from app.ats.ats.referrals.models import Referral
from app.ats.ats.ml.models import Assessment, CareerPath, OrganizationAnalytics
from app.ats.ats.pricing.services.recommendation_service import RecommendationService
from app.ats.ats.ml.services.market_analytics import MarketAnalyticsService
from app.ats.ats.notifications.services.notification_service import NotificationService

from app.ats.ats.ats.client_portal.decorators import require_portal_feature
from app.ats.ats.ats.client_portal.models import ClientPortalAccess, PortalAddon, AddonRequest

@login_required
@require_portal_feature('basic_metrics')
def client_dashboard(request):
    company = request.user.company
    
    # Período de análisis
    now = timezone.now()
    last_month = now - timedelta(days=30)
    
    # Métricas generales
    active_vacancies = Vacante.objects.filter(
        company=company,
        status='active'
    ).count()
    
    total_placements = Vacante.objects.filter(
        company=company,
        status='filled'
    ).count()
    
    avg_time_to_fill = Vacante.objects.filter(
        company=company,
        status='filled'
    ).aggregate(avg_time=Avg('time_to_fill'))['avg_time'] or 0
    
    total_investment = ServiceCalculation.objects.filter(
        company=company
    ).aggregate(total=Sum('total_fee'))['total'] or 0
    
    # Vacantes activas
    active_vacancies_list = Vacante.objects.filter(
        company=company,
        status='active'
    ).select_related('proposal').order_by('-created_at')
    
    # Historial de contrataciones
    recent_placements = Vacante.objects.filter(
        company=company,
        status='filled'
    ).select_related('proposal').order_by('-filled_date')[:5]
    
    # Documentos pendientes
    pending_documents = ServiceCalculation.objects.filter(
        company=company,
        documents__isnull=True
    ).order_by('-created_at')
    
    # Métricas de satisfacción
    satisfaction_metrics = {
        'time_to_fill': avg_time_to_fill,
        'quality_score': company.quality_score or 0,
        'retention_rate': company.retention_rate or 0
    }
    
    # ROI por contratación
    roi_metrics = {
        'total_investment': total_investment,
        'total_placements': total_placements,
        'avg_investment_per_placement': total_investment / total_placements if total_placements else 0
    }
    
    # Obtener acceso al portal
    portal_access = ClientPortalAccess.objects.get(user=request.user)
    
    # Obtener addons disponibles
    available_addons = PortalAddon.objects.filter(
        is_active=True
    ).exclude(
        id__in=portal_access.addons.values_list('id', flat=True)
    )
    
    # Actualizar último acceso
    portal_access.last_access = now
    portal_access.save()
    
    context = {
        'company': company,
        'active_vacancies': active_vacancies,
        'total_placements': total_placements,
        'avg_time_to_fill': avg_time_to_fill,
        'total_investment': total_investment,
        'active_vacancies_list': active_vacancies_list,
        'recent_placements': recent_placements,
        'pending_documents': pending_documents,
        'satisfaction_metrics': satisfaction_metrics,
        'roi_metrics': roi_metrics,
        'portal_access': portal_access,
        'available_addons': available_addons
    }
    
    return render(request, 'client_portal/dashboard.html', context)

@login_required
@require_portal_feature('view_documents')
def client_documents(request):
    company = request.user.company
    
    # Documentos por tipo
    documents = {
        'contracts': ServiceCalculation.objects.filter(
            company=company
        ).exclude(contract__isnull=True).order_by('-created_at'),
        
        'invoices': Payment.objects.filter(
            service_calculation__company=company
        ).exclude(invoice__isnull=True).order_by('-created_at'),
        
        'assessments': Vacante.objects.filter(
            company=company,
            assessment__isnull=False
        ).order_by('-created_at')
    }
    
    return render(request, 'client_portal/documents.html', {'documents': documents})

@login_required
@require_portal_feature('feedback_system')
def client_feedback(request):
    company = request.user.company
    
    if request.method == 'POST':
        # Procesar feedback
        feedback_type = request.POST.get('type')
        rating = request.POST.get('rating')
        comments = request.POST.get('comments')
        
        # Guardar feedback
        company.feedback_set.create(
            type=feedback_type,
            rating=rating,
            comments=comments
        )
        
        return redirect('client_portal:dashboard')
    
    # Obtener historial de feedback
    feedback_history = company.feedback_set.all().order_by('-created_at')
    
    return render(request, 'client_portal/feedback.html', {
        'feedback_history': feedback_history
    })

@login_required
@require_portal_feature('advanced_metrics')
def client_assessments(request):
    company = request.user.company
    
    # Obtener todos los assessments de la compañía
    assessments = Assessment.objects.filter(
        company=company
    ).select_related('candidate', 'vacancy').order_by('-created_at')
    
    # Obtener career paths de los candidatos
    career_paths = CareerPath.objects.filter(
        candidate__assessment__company=company
    ).select_related('candidate').distinct()
    
    # Obtener análisis organizacionales
    org_analytics = OrganizationAnalytics.objects.filter(
        company=company
    ).order_by('-created_at')
    
    # Métricas de assessments
    assessment_metrics = {
        'total_assessments': assessments.count(),
        'avg_score': assessments.aggregate(avg=Avg('score'))['avg'] or 0,
        'top_skills': assessments.values('skills').annotate(
            count=Count('id')
        ).order_by('-count')[:5],
        'success_rate': (assessments.filter(status='hired').count() / 
                        assessments.count() * 100) if assessments.count() > 0 else 0
    }
    
    # Generar recomendaciones de servicios
    recommendation_service = RecommendationService()
    service_recommendations = {
        'assessments': recommendation_service.get_assessment_recommendations(company),
        'addons': recommendation_service.get_addon_recommendations(company),
        'search_models': recommendation_service.get_search_model_recommendations(company)
    }
    
    # Oportunidades de mejora basadas en assessments
    improvement_opportunities = []
    
    # Analizar gaps de skills
    skill_gaps = assessments.values('skills').annotate(
        avg_score=Avg('score')
    ).filter(avg_score__lt=7)
    
    if skill_gaps.exists():
        improvement_opportunities.append({
            'type': 'skill_gap',
            'title': 'Gaps de Skills Identificados',
            'description': 'Hemos identificado áreas de oportunidad en el desarrollo de skills clave.',
            'recommendation': 'Considerar nuestro programa de Assessment Continuo para monitorear y mejorar estas áreas.',
            'services': ['assessment_continuo', 'training_plan']
        })
    
    # Analizar retención
    retention_rate = company.retention_rate or 0
    if retention_rate < 80:
        improvement_opportunities.append({
            'type': 'retention',
            'title': 'Oportunidad de Mejora en Retención',
            'description': f'La tasa de retención actual ({retention_rate}%) puede mejorarse.',
            'recommendation': 'Implementar nuestro programa de Engagement y Retención.',
            'services': ['engagement_program', 'retention_analysis']
        })
    
    # Analizar tiempo de contratación
    avg_time = assessment_metrics.get('avg_time_to_fill', 0)
    if avg_time > 45:
        improvement_opportunities.append({
            'type': 'time_to_fill',
            'title': 'Optimización de Tiempo de Contratación',
            'description': f'El tiempo promedio de contratación ({avg_time} días) puede optimizarse.',
            'recommendation': 'Considerar nuestro servicio de Búsqueda Acelerada.',
            'services': ['accelerated_search', 'talent_pool']
        })
    
    # Obtener benchmarks del mercado
    market_analytics = MarketAnalyticsService()
    industry = company.industry or 'general'
    
    benchmarks = {
        'retention': {
            'company': company.retention_rate or 0,
            'industry': market_analytics.get_industry_retention_rate(industry),
            'top_performers': market_analytics.get_top_performers_retention_rate(industry)
        },
        'time_to_fill': {
            'company': avg_time_to_fill,
            'industry': market_analytics.get_industry_time_to_fill(industry),
            'top_performers': market_analytics.get_top_performers_time_to_fill(industry)
        },
        'cost_per_hire': {
            'company': total_investment / total_placements if total_placements else 0,
            'industry': market_analytics.get_industry_cost_per_hire(industry),
            'top_performers': market_analytics.get_top_performers_cost_per_hire(industry)
        },
        'assessment_scores': {
            'company': assessment_metrics['avg_score'],
            'industry': market_analytics.get_industry_assessment_scores(industry),
            'top_performers': market_analytics.get_top_performers_assessment_scores(industry)
        }
    }
    
    # Obtener tendencias del mercado
    market_trends = {
        'salary_trends': market_analytics.get_salary_trends(industry),
        'skill_demand': market_analytics.get_skill_demand_trends(industry),
        'hiring_velocity': market_analytics.get_hiring_velocity_trends(industry),
        'retention_factors': market_analytics.get_retention_factors(industry)
    }
    
    # Calcular ROI comparativo
    roi_comparison = {
        'company': {
            'investment': total_investment,
            'placements': total_placements,
            'retention_rate': company.retention_rate or 0,
            'avg_time_to_fill': avg_time_to_fill
        },
        'industry': market_analytics.get_industry_roi_metrics(industry),
        'top_performers': market_analytics.get_top_performers_roi_metrics(industry)
    }
    
    context = {
        'assessments': assessments,
        'career_paths': career_paths,
        'org_analytics': org_analytics,
        'metrics': assessment_metrics,
        'service_recommendations': service_recommendations,
        'improvement_opportunities': improvement_opportunities,
        'benchmarks': benchmarks,
        'market_trends': market_trends,
        'roi_comparison': roi_comparison,
        'industry': industry
    }
    
    return render(request, 'client_portal/assessments.html', context)

@login_required
@require_portal_feature('basic_metrics')
def request_addon(request, addon_id):
    """Maneja la solicitud de un addon."""
    if request.method == 'POST':
        try:
            addon = PortalAddon.objects.get(id=addon_id, is_active=True)
            portal_access = ClientPortalAccess.objects.get(user=request.user)
            
            # Verificar si ya tiene el addon
            if addon in portal_access.addons.all():
                messages.warning(request, 'Ya tienes este addon activo.')
                return redirect('client_portal:dashboard')
            
            # Crear solicitud de addon
            addon_request = AddonRequest.objects.create(
                portal_access=portal_access,
                addon=addon,
                status='pending',
                requested_by=request.user
            )
            
            # Notificar al equipo
            notification_service = NotificationService()
            notification_service.notify_addon_request(addon_request)
            
            messages.success(
                request,
                f'Solicitud de addon "{addon.name}" enviada correctamente. '
                'Te notificaremos cuando sea aprobada.'
            )
            
        except PortalAddon.DoesNotExist:
            messages.error(request, 'El addon solicitado no existe o no está disponible.')
        except Exception as e:
            messages.error(request, f'Error al procesar la solicitud: {str(e)}')
        
        return redirect('client_portal:dashboard')
    
    return redirect('client_portal:dashboard') 