# /home/pablo/app/sexsi/views/preference_views.py
#
# Vista para el módulo. Implementa la lógica de presentación y manejo de peticiones HTTP.

"""
Vistas para manejo de preferencias de intimidad en SEXSI.
"""
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.decorators import login_required
from app.sexsi.config import PREFERENCE_CATEGORIES, PRACTICE_DICTIONARY, validate_preference
from app.models import ConsentAgreement, Preference

@method_decorator(login_required, name='dispatch')
class PreferenceSelectionView(View):
    """
    Vista para seleccionar preferencias de intimidad.
    """
    def get(self, request):
        """
        Muestra el formulario de selección de preferencias.
        """
        # Obtener las categorías y prácticas organizadas
        practices_by_category = {}
        for category_id, category in PREFERENCE_CATEGORIES.items():
            practices_by_category[category_id] = {
                practice_id: practice
                for practice_id, practice in PRACTICE_DICTIONARY.items()
                if practice['category'] == category_id
            }
            
        return render(request, 'sexsi/preference_selection.html', {
            'preference_categories': PREFERENCE_CATEGORIES,
            'practices_by_category': practices_by_category
        })

    def post(self, request):
        """
        Guarda las preferencias seleccionadas.
        """
        try:
            selected_practices = request.POST.getlist('selected_practices')
            
            # Validar las preferencias seleccionadas
            for practice_id in selected_practices:
                if not validate_preference({'code': practice_id}):
                    return JsonResponse({
                        'success': False,
                        'error': 'Práctica no válida'
                    }, status=400)
            
            # Guardar las preferencias en la base de datos
            agreement = ConsentAgreement.objects.create(
                creator=request.user,
                status='draft'
            )
            
            for practice_id in selected_practices:
                Preference.objects.create(
                    agreement=agreement,
                    practice_code=practice_id
                )
            
            return JsonResponse({
                'success': True,
                'message': 'Preferencias guardadas exitosamente'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

@method_decorator(login_required, name='dispatch')
class PreferenceUpdateView(View):
    """
    Vista para actualizar las preferencias de un acuerdo existente.
    """
    def post(self, request, agreement_id):
        """
        Actualiza las preferencias de un acuerdo.
        """
        try:
            agreement = ConsentAgreement.objects.get(id=agreement_id)
            
            # Verificar que el usuario tenga permiso para modificar
            if agreement.creator != request.user:
                return JsonResponse({
                    'success': False,
                    'error': 'No tienes permiso para modificar este acuerdo'
                }, status=403)
            
            # Verificar que el acuerdo no esté completado
            if agreement.status == 'completed':
                return JsonResponse({
                    'success': False,
                    'error': 'No se pueden modificar las preferencias de un acuerdo completado'
                }, status=400)
            
            selected_practices = request.POST.getlist('selected_practices')
            
            # Validar las nuevas preferencias
            for practice_id in selected_practices:
                if not validate_preference({'code': practice_id}):
                    return JsonResponse({
                        'success': False,
                        'error': 'Práctica no válida'
                    }, status=400)
            
            # Guardar las preferencias anteriores para comparación
            old_preferences = list(agreement.preferences.values_list('practice_code', flat=True))
            
            # Actualizar las preferencias
            agreement.preferences.all().delete()
            
            for practice_id in selected_practices:
                Preference.objects.create(
                    agreement=agreement,
                    practice_code=practice_id
                )
            
            # Verificar si hubo cambios en las preferencias
            new_preferences = set(selected_practices)
            old_preferences_set = set(old_preferences)
            
            if new_preferences != old_preferences_set:
                # Crear notificación para el anfitrión
                if agreement.invitee:
                    Notification.objects.create(
                        recipient=agreement.invitee,
                        agreement=agreement,
                        type='preference_update',
                        message='Se han actualizado las preferencias del acuerdo. Por favor, revisa los cambios.'
                    )
                
                # Actualizar el estado del acuerdo si ya estaba firmado
                if agreement.status == 'signed_by_creator':
                    agreement.status = 'pending'
                    agreement.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Preferencias actualizadas exitosamente'
            })
            
        except ConsentAgreement.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Acuerdo no encontrado'
            }, status=404)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
