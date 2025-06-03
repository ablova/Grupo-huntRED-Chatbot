"""
Vistas para el módulo de verificación.

Este módulo implementa las vistas necesarias para:
1. Seleccionar paquetes de verificación
2. Previsualizar propuestas de verificación
3. Asignar verificaciones a candidatos
4. Ver el dashboard de verificaciones
"""

import json
import asyncio
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q, Count, Avg
from django.template.loader import render_to_string
from django.conf import settings
from asgiref.sync import sync_to_async
from weasyprint import HTML, CSS

from app.ats.decorators import (
    role_required, permission_required
)
from app.models import (
    Opportunity, Person, VerificationService, VerificationAddon,
    OpportunityVerificationPackage, PackageAddonDetail, CandidateVerification,
    CandidateServiceResult, SocialNetworkVerification, BusinessUnit
)
from app.ats.utils.proposal_generator import (
    generate_verification_proposal, calculate_verification_pricing,
    create_verification_package, assign_verification_to_candidates,
    get_verification_status
)

@login_required
@role_required(['super_admin', 'consultant_complete', 'consultant_division'])
def verification_dashboard(request, opportunity_id):
    """
    Dashboard principal para verificaciones de una oportunidad.
    Muestra estadísticas y estado de candidatos.
    """
    opportunity = get_object_or_404(Opportunity, id=opportunity_id)
    
    # Obtener paquetes de verificación para esta oportunidad
    packages = OpportunityVerificationPackage.objects.filter(
        opportunity=opportunity
    ).order_by('-created_at')
    
    # Obtener candidatos de la oportunidad
    candidates = Person.objects.filter(
        vacante__opportunity=opportunity
    ).distinct()
    
    # Obtener verificaciones activas
    verifications = CandidateVerification.objects.filter(
        package__opportunity=opportunity
    )
    
    # Estadísticas generales
    stats = {
        'total_candidates': candidates.count(),
        'verified_candidates': verifications.filter(status__in=['completed', 'in_progress']).values('candidate').distinct().count(),
        'pending_verifications': verifications.filter(status='pending').count(),
        'completed_verifications': verifications.filter(status='completed').count(),
        'in_progress_verifications': verifications.filter(status='in_progress').count(),
        'average_score': verifications.filter(overall_score__isnull=False).aggregate(Avg('overall_score'))['overall_score__avg'] or 0
    }
    
    # Obtener servicios disponibles para filtrar
    services = VerificationService.objects.filter(is_active=True)
    
    context = {
        'opportunity': opportunity,
        'packages': packages,
        'candidates': candidates,
        'verifications': verifications,
        'stats': stats,
        'services': services,
        'business_unit': opportunity.business_unit
    }
    
    return render(request, 'verification/dashboard.html', context)

@login_required
@role_required(['super_admin', 'consultant_complete'])
def package_selection(request, opportunity_id):
    """
    Vista para seleccionar addons de verificación para un paquete.
    """
    opportunity = get_object_or_404(Opportunity, id=opportunity_id)
    
    # Obtener servicios y addons disponibles
    services = VerificationService.objects.filter(is_active=True)
    addons = VerificationAddon.objects.filter(is_active=True).order_by('tier', 'price')
    
    # Organizar addons por tier para facilitar la selección
    addons_by_tier = {
        'basic': addons.filter(tier='basic'),
        'freemium': addons.filter(tier='freemium'),
        'premium': addons.filter(tier='premium')
    }
    
    # Obtener candidatos de la oportunidad
    candidates = Person.objects.filter(
        vacante__opportunity=opportunity
    ).distinct()
    
    context = {
        'opportunity': opportunity,
        'services': services,
        'addons_by_tier': addons_by_tier,
        'candidates': candidates,
        'business_unit': opportunity.business_unit
    }
    
    return render(request, 'verification/package_selection.html', context)

@login_required
@role_required(['super_admin', 'consultant_complete'])
def proposal_preview(request, opportunity_id):
    """
    Vista para previsualizar una propuesta de verificación.
    """
    if request.method == 'POST':
        opportunity = get_object_or_404(Opportunity, id=opportunity_id)
        
        # Obtener addons seleccionados del formulario
        selected_addons = request.POST.getlist('selected_addons')
        
        # Generar propuesta de manera asíncrona
        proposal = asyncio.run(generate_verification_proposal(opportunity_id, selected_addons))
        
        # Obtener candidatos de la oportunidad
        candidates = Person.objects.filter(
            vacante__opportunity=opportunity
        ).distinct()
        
        context = {
            'opportunity': opportunity,
            'proposal': proposal,
            'selected_addons': selected_addons,
            'candidates': candidates,
            'business_unit': opportunity.business_unit
        }
        
        return render(request, 'verification/proposal_preview.html', context)
    
    return redirect('package_selection', opportunity_id=opportunity_id)

@login_required
@role_required(['super_admin', 'consultant_complete'])
def purchase_package(request, opportunity_id):
    """
    Vista para finalizar la compra de un paquete de verificación.
    """
    if request.method == 'POST':
        opportunity = get_object_or_404(Opportunity, id=opportunity_id)
        
        # Obtener datos del formulario
        package_name = request.POST.get('package_name', f'Verificación para {opportunity.name}')
        selected_addons = request.POST.getlist('selected_addons')
        selected_candidates = request.POST.getlist('selected_candidates')
        
        # Crear paquete de manera asíncrona
        package = asyncio.run(create_verification_package(
            opportunity_id, package_name, selected_addons, request.user.id
        ))
        
        # Si se seleccionaron candidatos, asignar verificaciones
        if selected_candidates:
            asyncio.run(assign_verification_to_candidates(
                package['id'], selected_candidates, request.user.id
            ))
        
        return redirect('verification_dashboard', opportunity_id=opportunity_id)
    
    return redirect('package_selection', opportunity_id=opportunity_id)

@login_required
@role_required(['super_admin', 'consultant_complete', 'consultant_division'])
def candidate_verification_detail(request, verification_id):
    """
    Vista para ver detalles de verificación de un candidato.
    """
    verification = get_object_or_404(CandidateVerification, id=verification_id)
    
    # Obtener resultados de servicios
    service_results = CandidateServiceResult.objects.filter(verification=verification)
    
    # Obtener verificaciones de redes sociales
    social_verifications = SocialNetworkVerification.objects.filter(
        service_result__verification=verification
    )
    
    context = {
        'verification': verification,
        'service_results': service_results,
        'social_verifications': social_verifications,
        'opportunity': verification.package.opportunity,
        'business_unit': verification.package.opportunity.business_unit
    }
    
    return render(request, 'verification/candidate_detail.html', context)

@login_required
@role_required(['super_admin', 'consultant_complete'])
def assign_candidate_verification(request, package_id):
    """
    Vista para asignar verificaciones a candidatos para un paquete existente.
    """
    package = get_object_or_404(OpportunityVerificationPackage, id=package_id)
    
    if request.method == 'POST':
        # Obtener candidatos seleccionados
        selected_candidates = request.POST.getlist('selected_candidates')
        
        if selected_candidates:
            # Asignar verificaciones de manera asíncrona
            asyncio.run(assign_verification_to_candidates(
                package_id, selected_candidates, request.user.id
            ))
        
        return redirect('verification_dashboard', opportunity_id=package.opportunity.id)
    
    # Obtener candidatos de la oportunidad
    candidates = Person.objects.filter(
        vacante__opportunity=package.opportunity
    ).distinct()
    
    # Excluir candidatos que ya tienen verificación para este paquete
    existing_verifications = CandidateVerification.objects.filter(
        package=package
    ).values_list('candidate_id', flat=True)
    
    candidates = candidates.exclude(id__in=existing_verifications)
    
    context = {
        'package': package,
        'candidates': candidates,
        'opportunity': package.opportunity,
        'business_unit': package.opportunity.business_unit
    }
    
    return render(request, 'verification/assign_candidates.html', context)

@login_required
@role_required(['super_admin', 'consultant_complete'])
def verification_report(request, verification_id):
    """
    Genera un informe PDF de verificación para un candidato.
    """
    verification = get_object_or_404(CandidateVerification, id=verification_id)
    
    # Obtener resultados de servicios
    service_results = CandidateServiceResult.objects.filter(verification=verification)
    
    # Obtener verificaciones de redes sociales
    social_verifications = SocialNetworkVerification.objects.filter(
        service_result__verification=verification
    )
    
    context = {
        'verification': verification,
        'service_results': service_results,
        'social_verifications': social_verifications,
        'opportunity': verification.package.opportunity,
        'business_unit': verification.package.opportunity.business_unit,
        'generation_date': timezone.now(),
        'static_root': settings.STATIC_ROOT
    }
    
    # Renderizar template HTML
    html_string = render_to_string('verification/report_pdf.html', context)
    
    # Generar PDF
    pdf_file = HTML(string=html_string).write_pdf(
        stylesheets=[CSS(string='body { font-family: Arial; }')]
    )
    
    # Preparar respuesta
    response = HttpResponse(pdf_file, content_type='application/pdf')
    filename = f"verificacion_{verification.candidate.nombre}_{verification.candidate.apellido}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

@login_required
@role_required(['super_admin', 'consultant_complete'])
def ajax_calculate_price(request):
    """
    Endpoint AJAX para calcular el precio de verificación.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            opportunity_id = data.get('opportunity_id')
            selected_addons = data.get('selected_addons', [])
            
            # Calcular precio de manera asíncrona
            pricing = asyncio.run(calculate_verification_pricing(opportunity_id, selected_addons))
            
            return JsonResponse({'pricing': pricing})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@login_required
@role_required(['super_admin', 'consultant_complete', 'consultant_division'])
def ajax_verification_stats(request, opportunity_id):
    """
    Endpoint AJAX para obtener estadísticas actualizadas de verificación.
    """
    try:
        opportunity = get_object_or_404(Opportunity, id=opportunity_id)
        
        # Obtener verificaciones
        verifications = CandidateVerification.objects.filter(
            package__opportunity=opportunity
        )
        
        # Estadísticas generales
        stats = {
            'total_candidates': Person.objects.filter(vacante__opportunity=opportunity).distinct().count(),
            'verified_candidates': verifications.filter(status__in=['completed', 'in_progress']).values('candidate').distinct().count(),
            'pending_verifications': verifications.filter(status='pending').count(),
            'completed_verifications': verifications.filter(status='completed').count(),
            'in_progress_verifications': verifications.filter(status='in_progress').count(),
            'average_score': verifications.filter(overall_score__isnull=False).aggregate(Avg('overall_score'))['overall_score__avg'] or 0
        }
        
        return JsonResponse({'stats': stats})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
