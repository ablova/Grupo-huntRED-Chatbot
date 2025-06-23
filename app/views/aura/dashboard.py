"""
Dashboard Ejecutivo AURA

- Muestra KPIs y recomendaciones ejecutivas usando AuraEngine
- Adapta el contenido según el rol y la BU
- Ejemplo de integración real para consultores, admins y clientes
"""

from .base import AuraBaseView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from app.ml.aura import AuraEngine

class ExecutiveDashboardView(AuraBaseView):
    """
    Vista de dashboard ejecutivo con integración AURA.
    """
    @method_decorator(csrf_exempt)
    def get(self, request, *args, **kwargs):
        context = self.get_aura_context(request)
        user = context['user']
        bu = context['business_unit']
        person = context['person']
        role = context['role']
        if not bu:
            return self.render_error('Unidad de negocio no seleccionada')
        # Instanciar motor AURA con contexto de BU
        aura_engine = AuraEngine(business_unit=bu)
        # Ejemplo: obtener KPIs y recomendaciones
        kpis = aura_engine.metrics.get_kpis_for_bu(bu)
        recommendations = aura_engine.recommendation_engine.get_recommendations_for_user(person) if person else []
        # Respuesta estructurada
        data = {
            'user': user.username,
            'role': role,
            'business_unit': bu.name,
            'kpis': kpis,
            'recommendations': recommendations
        }
        return self.render_response(data) 