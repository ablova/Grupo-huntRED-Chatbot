"""
Vistas para el módulo de referencias.
"""

from typing import Dict, List, Optional
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from app.models import BusinessUnit, Reference
from app.ml.analyzers.reference_analyzer import ReferenceAnalyzer
from app.ats.chatbot.workflow.business_units.reference_config import get_reference_config

@login_required
def reference_dashboard(request):
    """
    Vista del dashboard de referencias.
    """
    # Obtener parámetros de filtro
    business_unit_code = request.GET.get('business_unit')
    date_range = request.GET.get('date_range')
    status = request.GET.get('status')
    
    # Filtrar referencias
    references = Reference.objects.all()
    
    if business_unit_code:
        references = references.filter(candidate__business_unit__code=business_unit_code)
    
    if status:
        references = references.filter(status=status)
    
    if date_range:
        start_date, end_date = date_range.split(' - ')
        references = references.filter(
            created_at__range=[start_date, end_date]
        )
    
    # Obtener unidades de negocio
    business_units = BusinessUnit.objects.all()
    
    # Analizar referencias
    analyzer = ReferenceAnalyzer()
    report = analyzer.generate_reference_report(
        business_unit=references.first().candidate.business_unit if references.exists() else None
    )
    
    # Preparar datos para el template
    context = {
        'business_units': business_units,
        'metrics': report['metrics'],
        'trends': report['trends'],
        'quality': report['quality'],
        'insights': report['insights'],
        'references': references.order_by('-created_at')[:10]  # Últimas 10 referencias
    }
    
    return render(request, 'dashboard/references.html', context)

@login_required
def reference_detail(request, reference_id: int):
    """
    Vista de detalle de una referencia.
    """
    try:
        reference = Reference.objects.get(id=reference_id)
        analyzer = ReferenceAnalyzer()
        
        # Analizar referencia
        analysis = analyzer.analyze_reference_quality(reference)
        
        context = {
            'reference': reference,
            'analysis': analysis,
            'config': get_reference_config(reference.candidate.business_unit.code)
        }
        
        return render(request, 'references/detail.html', context)
        
    except Reference.DoesNotExist:
        return JsonResponse({'error': 'Referencia no encontrada'}, status=404)

@login_required
def reference_api(request):
    """
    API para obtener datos de referencias.
    """
    try:
        # Obtener parámetros
        business_unit_code = request.GET.get('business_unit')
        date_range = request.GET.get('date_range')
        status = request.GET.get('status')
        
        # Filtrar referencias
        references = Reference.objects.all()
        
        if business_unit_code:
            references = references.filter(candidate__business_unit__code=business_unit_code)
        
        if status:
            references = references.filter(status=status)
        
        if date_range:
            start_date, end_date = date_range.split(' - ')
            references = references.filter(
                created_at__range=[start_date, end_date]
            )
        
        # Analizar referencias
        analyzer = ReferenceAnalyzer()
        report = analyzer.generate_reference_report(
            business_unit=references.first().candidate.business_unit if references.exists() else None
        )
        
        return JsonResponse({
            'success': True,
            'data': report
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500) 