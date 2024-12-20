# app/views/workflow_views.py

from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from app.models import WorkflowStage, BusinessUnit
from app.forms import WorkflowStageForm
import logging

logger = logging.getLogger(__name__)

@method_decorator(cache_page(60 * 15), name='dispatch')  # Cache por 15 minutos
class WorkflowStageListView(LoginRequiredMixin, View):
    """
    Lista todas las etapas del workflow para una Unidad de Negocio específica.
    """
    def get(self, request, business_unit_id):
        business_unit = get_object_or_404(BusinessUnit, id=business_unit_id)
        stages = business_unit.workflow_stages.all()
        return JsonResponse({'stages': list(stages.values())})

class WorkflowStageCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Crea una nueva etapa en el workflow.
    """
    def test_func(self):
        return self.request.user.is_staff

    def get(self, request, business_unit_id):
        form = WorkflowStageForm()
        return render(request, 'workflow/create_stage.html', {'form': form})

    def post(self, request, business_unit_id):
        form = WorkflowStageForm(request.POST)
        business_unit = get_object_or_404(BusinessUnit, id=business_unit_id)
        if form.is_valid():
            stage = form.save(commit=False)
            stage.business_unit = business_unit
            stage.save()
            logger.info(f"Creada nueva etapa: {stage.name} para unidad de negocio: {business_unit.name}")
            return redirect('workflow_stage_list', business_unit_id=business_unit.id)
        else:
            logger.warning(f"Error al crear etapa: {form.errors}")
        return render(request, 'workflow/create_stage.html', {'form': form})

class WorkflowStageUpdateView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Actualiza una etapa existente en el workflow.
    """
    def test_func(self):
        return self.request.user.is_staff

    def get(self, request, business_unit_id, stage_id):
        stage = get_object_or_404(WorkflowStage, id=stage_id, business_unit_id=business_unit_id)
        form = WorkflowStageForm(instance=stage)
        return render(request, 'workflow/update_stage.html', {'form': form, 'stage': stage})

    def post(self, request, business_unit_id, stage_id):
        stage = get_object_or_404(WorkflowStage, id=stage_id, business_unit_id=business_unit_id)
        form = WorkflowStageForm(request.POST, instance=stage)
        if form.is_valid():
            form.save()
            logger.info(f"Actualizada etapa: {stage.name} para unidad de negocio: {stage.business_unit.name}")
            return redirect('workflow_stage_list', business_unit_id=business_unit_id)
        return render(request, 'workflow/update_stage.html', {'form': form, 'stage': stage})

class WorkflowStageDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Elimina una etapa del workflow.
    """
    def test_func(self):
        return self.request.user.is_staff

    def post(self, request, business_unit_id, stage_id):
        stage = get_object_or_404(WorkflowStage, id=stage_id, business_unit_id=business_unit_id)
        stage.delete()
        logger.info(f"Eliminada etapa: {stage.name} de la unidad de negocio: {stage.business_unit.name}")
        return redirect('workflow_stage_list', business_unit_id=business_unit_id)