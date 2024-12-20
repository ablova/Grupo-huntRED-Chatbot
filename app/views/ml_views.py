# /home/pablollh/app/views/ml_views.py
from app.tasks import train_ml_task
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache

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