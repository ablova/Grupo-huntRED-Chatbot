"""
BaseView para vistas de AURA

- Maneja contexto de usuario y unidad de negocio (BU)
- Detección de rol y permisos
- Respuesta estructurada y reutilizable

Ejemplo de uso:
    class MiDashboardView(AuraBaseView):
        def get(self, request, *args, **kwargs):
            context = self.get_aura_context(request)
            # Lógica de negocio...
            return self.render_response(data)
"""

from django.views import View
from django.http import JsonResponse
from app.models import Person, BusinessUnit
from django.contrib.auth.mixins import LoginRequiredMixin

class AuraBaseView(LoginRequiredMixin, View):
    """
    Base para todas las vistas de AURA.
    Provee utilidades para obtener contexto de usuario, BU y permisos.
    """
    def get_aura_context(self, request):
        user = request.user
        # Detectar BU activa (puedes adaptar esto según tu lógica)
        bu_id = request.GET.get('bu_id') or request.session.get('active_bu')
        bu_obj = None
        if bu_id:
            try:
                bu_obj = BusinessUnit.objects.get(id=bu_id)
            except BusinessUnit.DoesNotExist:
                bu_obj = None
        # Obtener perfil extendido si aplica
        try:
            person = Person.objects.get(email=user.email)
        except Person.DoesNotExist:
            person = None
        # Detectar rol
        role = getattr(user, 'role', 'user')
        return {
            'user': user,
            'person': person,
            'business_unit': bu_obj,
            'role': role
        }

    def render_response(self, data, status=200):
        """Devuelve respuesta JSON estructurada."""
        return JsonResponse({'status': 'ok', 'data': data}, status=status)

    def render_error(self, message, status=400):
        return JsonResponse({'status': 'error', 'message': message}, status=status) 