# /home/pablo/app/views/dashboard.py
#
# Vista para el módulo. Implementa la lógica de presentación y manejo de peticiones HTTP.

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, F
from django.utils import timezone
from datetime import timedelta, datetime
from calendar import monthrange
from .models import (
    Person, Vacante, Application, Interview, CartaOferta,
    ChatState, IntentPattern, StateTransition, ConfiguracionBU
)

@login_required
def dashboard(request):
    # Obtener el período de filtrado (por defecto semana)
    period = request.GET.get('period', 'week')
    
    # Función para obtener fechas según el período
    def get_period_dates(period):
        today = timezone.now()
        if period == 'week':
            start_date = today - timedelta(days=7)
            end_date = today
        elif period == 'month':
            _, days_in_month = monthrange(today.year, today.month)
            start_date = today.replace(day=1)
            end_date = today.replace(day=days_in_month)
        elif period == 'year':
            start_date = today.replace(month=1, day=1)
            end_date = today.replace(month=12, day=31)
        return start_date, end_date

    # Obtener fechas para el período seleccionado
    start_date, end_date = get_period_dates(period)

    # Obtener datos de métricas
    metrics = {
        "total_users": Person.objects.count(),
        "active_chats": ChatState.objects.filter(
            last_transition__gte=timezone.now() - timedelta(hours=24)
        ).count(),
        "new_applications": Application.objects.filter(
            applied_at__gte=start_date,
            applied_at__lte=end_date
        ).count(),
        "pending_interviews": Interview.objects.filter(
            resultado='pendiente',
            fecha__gte=timezone.now()
        ).count()
    }

    # Obtener datos para gráficos
    # Preparar datos para el gráfico de aplicaciones
    applications_data = Application.objects.filter(
        applied_at__gte=start_date,
        applied_at__lte=end_date
    ).annotate(
        date=F('applied_at__date')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')

    # Preparar datos para el gráfico de entrevistas
    interviews_data = Interview.objects.filter(
        fecha__gte=start_date,
        fecha__lte=end_date
    ).values('resultado').annotate(
        count=Count('id')
    )

    # Obtener datos de chatbot
    chatbot_data = {
        "states": ChatState.objects.filter(
            last_transition__gte=start_date,
            last_transition__lte=end_date
        )[:5],
        "pending_transitions": StateTransition.objects.filter(
            Q(current_state='PROFILE') | Q(current_state='SEARCH'),
            created_at__gte=start_date,
            created_at__lte=end_date
        )[:5]
    }

    # Obtener datos de propuestas
    proposals_data = {
        "recent": CartaOferta.objects.filter(
            status__in=['pending', 'sent'],
            created_at__gte=start_date,
            created_at__lte=end_date
        ).order_by('-created_at')[:5]
    }

    # Preparar datos para el template
    context = {
        'metrics': metrics,
        'period': period,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'chatbot_data': chatbot_data,
        'proposals_data': proposals_data,
        'applications_data': applications_data,
        'interviews_data': interviews_data
    }

    return render(request, 'dashboard.html', context)
