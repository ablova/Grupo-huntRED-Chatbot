# /home/pablo/app/views/dashboard_views.py

from django.shortcuts import render
#from ratelimit.decorators import ratelimit
from app.models import Person, ChatState, WorkflowStage
import logging
logger = logging.getLogger(__name__)



def dashboard_view(request):
    """
    Vista para el dashboard principal.
    """
    total_candidates = Person.objects.count()
    total_interactions = ChatState.objects.count()
    total_workflow_stages = WorkflowStage.objects.count()

    context = {
        'total_candidates': total_candidates,
        'total_interactions': total_interactions,
        'total_workflow_stages': total_workflow_stages,
    }
    return render(request, 'dashboard.html', context)