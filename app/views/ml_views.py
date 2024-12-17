# /home/amigro/app/views/ml_views.py
from app.tasks import train_ml_task
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def train_ml_api(request):
    """
    Endpoint para iniciar el entrenamiento de modelos ML.
    """
    business_unit_id = request.POST.get('business_unit_id')
    if business_unit_id:
        train_ml_task.delay(business_unit_id=int(business_unit_id))
        return JsonResponse({"status": "success", "message": "Tarea de entrenamiento enviada para la BU específica."})
    else:
        train_ml_task.delay()
        return JsonResponse({"status": "success", "message": "Tarea de entrenamiento enviada para todas las BUs."})