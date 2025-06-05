# /home/pablo/app/views/ml_views.py
from app.tasks import train_ml_task
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.http import JsonResponse
#from ratelimit.decorators import ratelimit
from app.ml.core.models.base import MatchmakingLearningSystem, MatchmakingModel, TransitionModel, MarketAnalysisModel
from app.models import Person, BusinessUnit, Vacante
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.views.decorators.http import require_http_methods


@csrf_exempt
def train_ml_api(request):
    """
    Endpoint para iniciar el entrenamiento de modelos ML.
    """
    business_unit_id = request.POST.get('business_unit_id')
    cache_key = f'train_ml_task_{business_unit_id}' if business_unit_id else 'train_ml_task_all'

    if cache.get(cache_key):  # Verificar si la tarea ya está en cola
        return JsonResponse({"status": "error", "message": "La tarea ya está en cola."}, status=400)

    if business_unit_id:
        train_ml_task.delay(business_unit_id=int(business_unit_id))
        cache.set(cache_key, True, timeout=60 * 5)  # Cachear por 5 minutos
        return JsonResponse({"status": "success", "message": "Tarea de entrenamiento enviada para la BU específica."})
    else:
        train_ml_task.delay()
        return JsonResponse({"status": "success", "message": "Tarea de entrenamiento enviada para todas las BUs."})

async def predict_matches(request, user_id):
    """
    Predice matches para un usuario específico usando el sistema ML.
    """
    try:
        person = await sync_to_async(get_object_or_404)(Person, id=user_id)
        
        if not person.current_stage or not person.current_stage.business_unit:
            return JsonResponse({
                "error": "Usuario sin unidad de negocio asignada"
            }, status=400)
            
        matches = MatchmakingLearningSystem.predict_all_active_matches(person)
        
        return JsonResponse({
            "matches": matches,
            "user_id": user_id
        })
        
    except Exception as e:
        return JsonResponse({
            "error": str(e)
        }, status=500)

@require_http_methods(["GET"])
def predict_candidate_success(request, person_id, vacancy_id):
    try:
        person = Person.objects.get(id=person_id)
        vacancy = Vacante.objects.get(id=vacancy_id)
        
        model = MatchmakingModel(business_unit=vacancy.business_unit)
        prediction = model.predict_candidate_success(person, vacancy)
        
        return JsonResponse({
            'success': True,
            'prediction': prediction
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@require_http_methods(["GET"])
def predict_transition(request, person_id):
    try:
        person = Person.objects.get(id=person_id)
        
        model = TransitionModel(business_unit=person.current_stage.business_unit)
        prediction = model.predict_transition(person)
        
        return JsonResponse({
            'success': True,
            'prediction': prediction
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@require_http_methods(["GET"])
def analyze_market(request, business_unit):
    try:
        model = MarketAnalysisModel(business_unit=business_unit)
        analysis = model.analyze_market()
        
        return JsonResponse({
            'success': True,
            'analysis': analysis
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })