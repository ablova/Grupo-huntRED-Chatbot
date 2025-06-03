from django.shortcuts import render
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta
from app.ats.pricing.models import ServiceCalculation, Payment
from app.ats.referrals.models import Referral
from app.ats.proposals.models import Proposal

def executive_dashboard(request):
    # Período de análisis
    now = timezone.now()
    last_month = now - timedelta(days=30)
    two_months_ago = now - timedelta(days=60)

    # Métricas generales
    current_revenue = Payment.objects.filter(
        status='received',
        created_at__gte=last_month
    ).aggregate(total=Sum('amount'))['total'] or 0

    previous_revenue = Payment.objects.filter(
        status='received',
        created_at__gte=two_months_ago,
        created_at__lt=last_month
    ).aggregate(total=Sum('amount'))['total'] or 0

    revenue_change = ((current_revenue - previous_revenue) / previous_revenue * 100) if previous_revenue else 0

    active_proposals = Proposal.objects.filter(status='active').count()
    previous_proposals = Proposal.objects.filter(
        created_at__gte=two_months_ago,
        created_at__lt=last_month
    ).count()
    proposals_change = ((active_proposals - previous_proposals) / previous_proposals * 100) if previous_proposals else 0

    # Tasa de éxito
    total_proposals = Proposal.objects.filter(created_at__gte=last_month).count()
    successful_proposals = Proposal.objects.filter(
        created_at__gte=last_month,
        status='completed'
    ).count()
    success_rate = (successful_proposals / total_proposals * 100) if total_proposals else 0

    previous_success_rate = Proposal.objects.filter(
        created_at__gte=two_months_ago,
        created_at__lt=last_month,
        status='completed'
    ).count() / Proposal.objects.filter(
        created_at__gte=two_months_ago,
        created_at__lt=last_month
    ).count() * 100 if Proposal.objects.filter(
        created_at__gte=two_months_ago,
        created_at__lt=last_month
    ).exists() else 0

    success_rate_change = success_rate - previous_success_rate

    # Tiempo promedio
    avg_time_to_fill = Proposal.objects.filter(
        status='completed',
        created_at__gte=last_month
    ).aggregate(avg_time=Avg('time_to_fill'))['avg_time'] or 0

    previous_avg_time = Proposal.objects.filter(
        status='completed',
        created_at__gte=two_months_ago,
        created_at__lt=last_month
    ).aggregate(avg_time=Avg('time_to_fill'))['avg_time'] or 0

    time_change = ((avg_time_to_fill - previous_avg_time) / previous_avg_time * 100) if previous_avg_time else 0

    # Top 5 puestos
    top_positions = Proposal.objects.filter(
        created_at__gte=last_month
    ).values('position__title').annotate(
        success_rate=Count('id', filter=models.Q(status='completed')) * 100.0 / Count('id'),
        avg_time=Avg('time_to_fill')
    ).order_by('-success_rate')[:5]

    # Top 5 clientes
    top_clients = ServiceCalculation.objects.filter(
        created_at__gte=last_month
    ).values('company__name').annotate(
        revenue=Sum('total_fee'),
        proposals=Count('id')
    ).order_by('-revenue')[:5]

    # Métricas de referidos
    total_referrals = Referral.objects.filter(
        created_at__gte=last_month
    ).count()

    successful_referrals = Referral.objects.filter(
        created_at__gte=last_month,
        status='converted'
    ).count()

    referral_conversion_rate = (successful_referrals / total_referrals * 100) if total_referrals else 0

    referral_revenue = ServiceCalculation.objects.filter(
        referral__created_at__gte=last_month,
        referral__status='converted'
    ).aggregate(total=Sum('total_fee'))['total'] or 0

    # Datos para gráficos
    months = []
    revenue_data = []
    for i in range(6):
        month = now - timedelta(days=30*i)
        months.insert(0, month.strftime('%b %Y'))
        month_revenue = Payment.objects.filter(
            status='received',
            created_at__year=month.year,
            created_at__month=month.month
        ).aggregate(total=Sum('amount'))['total'] or 0
        revenue_data.insert(0, month_revenue)

    position_labels = [p['position__title'] for p in top_positions]
    success_rate_data = [p['success_rate'] for p in top_positions]

    # Predicciones
    projected_months = []
    projected_data = []
    for i in range(3):
        month = now + timedelta(days=30*i)
        projected_months.append(month.strftime('%b %Y'))
        # Aquí podríamos implementar un modelo de predicción más sofisticado
        projected_data.append(current_revenue * (1 + (revenue_change/100))**(i+1))

    # Tendencias de mercado
    market_trends = [
        {
            'position': 'Desarrollador Full Stack',
            'demand': 15.5,
            'avg_salary': 85000
        },
        {
            'position': 'Data Scientist',
            'demand': 12.3,
            'avg_salary': 95000
        },
        {
            'position': 'DevOps Engineer',
            'demand': 10.8,
            'avg_salary': 90000
        }
    ]

    context = {
        'total_revenue': current_revenue,
        'revenue_change': revenue_change,
        'active_proposals': active_proposals,
        'proposals_change': proposals_change,
        'success_rate': success_rate,
        'success_rate_change': success_rate_change,
        'avg_time_to_fill': avg_time_to_fill,
        'time_change': time_change,
        'top_positions': top_positions,
        'top_clients': top_clients,
        'total_referrals': total_referrals,
        'referral_conversion_rate': referral_conversion_rate,
        'referral_revenue': referral_revenue,
        'revenue_labels': months,
        'revenue_data': revenue_data,
        'position_labels': position_labels,
        'success_rate_data': success_rate_data,
        'projected_labels': projected_months,
        'projected_data': projected_data,
        'market_trends': market_trends
    }

    return render(request, 'dashboard/executive.html', context) 