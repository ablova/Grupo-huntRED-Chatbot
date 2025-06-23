"""
Recomendaciones Personalizadas AURA

- Devuelve recomendaciones personalizadas según el perfil y contexto
- Utiliza el motor de recomendaciones de AURA
- Adaptable a cualquier tipo de usuario
"""

from .base import AuraBaseView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from app.ml.aura import AuraEngine

class AuraRecommendationsView(AuraBaseView):
    """
    Vista para obtener recomendaciones personalizadas de AURA.
    """
    @method_decorator(csrf_exempt)
    def get(self, request, *args, **kwargs):
        context = self.get_aura_context(request)
        person = context['person']
        bu = context['business_unit']
        if not person or not bu:
            return self.render_error('Perfil o unidad de negocio no encontrados')
        aura_engine = AuraEngine(business_unit=bu)
        recommendations = aura_engine.recommendation_engine.get_recommendations_for_user(person)
        return self.render_response({'recommendations': recommendations}) 