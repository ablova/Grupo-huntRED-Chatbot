from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from app.models import Person, Application, Vacante, EnhancedNetworkGamificationProfile
import logging

logger = logging.getLogger(__name__)

@login_required
def list_candidatos(request):
    """
    Vista para listar candidatos con procesos activos.
    """
    candidatos = Person.objects.prefetch_related('applications__vacancy').all()
    data = [
        {
            "nombre": candidato.nombre,
            "apellido_paterno": candidato.apellido_paterno,
            "email": candidato.email,
            "procesos": [
                {
                    "vacante": app.vacancy.titulo,
                    "estado": app.status,
                    "fecha_aplicacion": app.applied_at
                }
                for app in candidato.applications.all()
            ]
        }
        for candidato in candidatos
    ]
    return JsonResponse(data, safe=False)

@csrf_exempt
def add_application(request):
    """
    Añadir un candidato a un proceso de reclutamiento.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            person = get_object_or_404(Person, id=data['person_id'])
            vacancy = get_object_or_404(Vacante, id=data['vacancy_id'])

            application, created = Application.objects.get_or_create(
                user=person,
                vacancy=vacancy,
                defaults={'status': 'applied'}
            )

            return JsonResponse({
                "status": "success",
                "message": "Candidato añadido al proceso.",
                "application_id": application.id,
                "created": created
            })
        except Exception as e:
            logger.error(f"Error añadiendo aplicación: {e}", exc_info=True)
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

@login_required
def candidato_details(request, candidato_id):
    """
    Vista para mostrar los detalles de un candidato específico.
    """
    candidato = get_object_or_404(Person, id=candidato_id)
    data = {
        "nombre": candidato.nombre,
        "email": candidato.email,
        "procesos": [
            {
                "vacante": app.vacancy.titulo,
                "estado": app.status,
                "fecha_aplicacion": app.applied_at
            }
            for app in candidato.applications.all()
        ],
        "skills": candidato.skills,
        "experiencia": candidato.experience_data,
        "metadata": candidato.metadata,
    }
    return JsonResponse(data)

def generate_challenges(request, user_id):
    """
    Genera retos personalizados para un usuario.
    """
    profile = EnhancedNetworkGamificationProfile.objects.get(user_id=user_id)
    challenges = profile.generate_networking_challenges()
    return JsonResponse(challenges, safe=False)