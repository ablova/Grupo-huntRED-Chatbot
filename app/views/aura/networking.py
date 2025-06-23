"""
Sugerencias de Networking AURA

- Devuelve sugerencias de conexiones estratégicas usando la GNN
- Utiliza el motor NetworkMatchmaker de AURA
- Adaptable a cualquier tipo de usuario
"""

from .base import AuraBaseView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from app.ml.aura import NetworkMatchmaker

class AuraNetworkingView(AuraBaseView):
    """
    Vista para obtener sugerencias de networking de AURA.
    """
    @method_decorator(csrf_exempt)
    def get(self, request, *args, **kwargs):
        context = self.get_aura_context(request)
        person = context['person']
        bu = context['business_unit']
        if not person or not bu:
            return self.render_error('Perfil o unidad de negocio no encontrados')
        matchmaker = NetworkMatchmaker()
        suggestions = matchmaker.suggest_connections(user_id=person.id, business_unit=bu.name)
        return self.render_response({'networking_suggestions': suggestions}) 