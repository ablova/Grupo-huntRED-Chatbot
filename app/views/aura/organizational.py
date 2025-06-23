"""
Análisis Organizacional AURA

- Devuelve insights organizacionales usando OrganizationalAnalytics
- Ideal para consultores y admins
- Incluye análisis de silos, influencers y movilidad interna
"""

from .base import AuraBaseView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from app.ml.aura import OrganizationalAnalytics

class AuraOrganizationalView(AuraBaseView):
    """
    Vista para obtener análisis organizacional de AURA.
    """
    @method_decorator(csrf_exempt)
    def get(self, request, *args, **kwargs):
        context = self.get_aura_context(request)
        bu = context['business_unit']
        if not bu:
            return self.render_error('Unidad de negocio no seleccionada')
        org_analytics = OrganizationalAnalytics()
        insights = org_analytics.analyze_organization(business_unit=bu.name)
        return self.render_response({'organizational_insights': insights}) 