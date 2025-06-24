"""
URLs para la API de ATS de Grupo huntRED®
"""

from django.urls import path
from .pricing_api import (
    get_pricing_plans,
    get_pricing_addons,
    get_pricing_business_units,
    get_pricing_assessments,
    calculate_pricing_api,
    get_pricing_strategies,
    get_pricing_proposal,
    send_proposal_email,
    track_share
)

app_name = 'ats_api'

urlpatterns = [
    # Pricing API endpoints
    path('pricing/plans/', get_pricing_plans, name='pricing_plans'),
    path('pricing/addons/', get_pricing_addons, name='pricing_addons'),
    path('pricing/business-units/', get_pricing_business_units, name='pricing_business_units'),
    path('pricing/assessments/', get_pricing_assessments, name='pricing_assessments'),
    path('pricing/calculate/', calculate_pricing_api, name='pricing_calculate'),
    path('pricing/strategies/', get_pricing_strategies, name='pricing_strategies'),
    path('pricing/proposals/<int:proposal_id>/', get_pricing_proposal, name='pricing_proposal'),
    path('pricing/send-proposal/', send_proposal_email, name='send_proposal'),
    path('pricing/track-share/', track_share, name='track_share'),
] 