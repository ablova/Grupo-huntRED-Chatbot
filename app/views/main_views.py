# /home/pablollh/app/views/main_views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from django.template.response import TemplateResponse
from django.middleware.csrf import get_token
from ratelimit.decorators import ratelimit

from app.models import (
    BusinessUnit, ChatState, Configuracion, Application, Vacante, Person
)
from app.chatbot.utils import analyze_text
from app.chatbot.gpt import GPTHandler
from app.chatbot.chatbot import ChatBotHandler

import json
import logging

logger = logging.getLogger(__name__)

@staff_member_required
def interacciones_por_unidad(request):
    """
    Vista para mostrar estadísticas de interacciones por unidad de negocio.
    """
    data = []
    units = BusinessUnit.objects.prefetch_related('chatstate_set').all()
    for unit in units:
        count = unit.chatstate_set.filter(platform__icontains=unit.name.lower()).count()
        data.append({'unidad': unit.name, 'interacciones': count})
    return render(request, 'admin/estadisticas/interacciones.html', {'data': data})

def index(request):
    """
    Vista para la página principal.
    """
    business_units = BusinessUnit.objects.all()
    config = Configuracion.objects.first()
    return render(request, "index.html", {'business_units': business_units, 'config': config})


def finalize_candidates(request, business_unit_id):
    """
    Finaliza el proceso de candidatos seleccionados y envía reportes.
    """
    if request.method == 'POST':
        # Supongamos que recibes una lista de IDs de candidatos a incluir
        candidates_ids = request.POST.getlist('candidates')
        recipient_email = request.POST.get('email')
        
        # Llama a la tarea de Celery
        send_final_candidate_report.delay(business_unit_id, candidates_ids, recipient_email)
        
        return redirect('success_page')
    
    # Renderiza la página de finalización si es GET
    return render(request, 'finalize_candidates.html')

def login_view(request):
    """
    Vista para autenticar a un usuario en WordPress desde la interfaz de Django.
    """
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        login_status = login(username, password)
        if login_status:
            return JsonResponse({"status": "success"})
        else:
            return JsonResponse({"status": "error", "message": "Login failed."})

def submit_application(request, job_id):
    """
    Vista para manejar la aplicación de un candidato a un trabajo específico.
    """
    if request.method == 'POST':
        # Lógica para procesar la aplicación
        data = request.POST
        person_id = data.get('person_id')
        vacancy = get_object_or_404(Vacante, id=job_id)
        person = get_object_or_404(Person, id=person_id)

        application = Application.objects.create(user=person, vacancy=vacancy)
        return JsonResponse({"status": "success", "application_id": application.id})

    return render(request, 'apply.html', {'job_id': job_id})

def home(request):
    return render(request, 'home.html')  # Asegúrate de que la plantilla exista