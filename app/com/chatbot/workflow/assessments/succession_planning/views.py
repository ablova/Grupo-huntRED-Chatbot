from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
)
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Q, Count, Avg, F, Value, CharField
from django.db.models.functions import Concat
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

from app.models import (
    Person, 
    BusinessUnit, 
    Vacante,
    ProfessionalDNA, 
    SuccessionPlan, 
    SuccessionCandidate, 
    SuccessionReadinessAssessment
)
from .forms import (
    SuccessionPlanForm, 
    SuccessionCandidateForm, 
    ReadinessAssessmentForm
)


class SuccessionPlanListView(LoginRequiredMixin, ListView):
    model = SuccessionPlan
    template_name = 'succession_planning/plan_list.html'
    context_object_name = 'plans'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtros
        status = self.request.GET.get('status')
        business_unit = self.request.GET.get('business_unit')
        search = self.request.GET.get('search')
        
        if status:
            queryset = queryset.filter(status=status)
            
        if business_unit:
            queryset = queryset.filter(business_unit_id=business_unit)
            
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(position__titulo__icontains=search) |
                Q(position__empresa__name__icontains=search)
            )
        
        # Solo planes a los que el usuario tiene acceso
        if not self.request.user.is_superuser:
            queryset = queryset.filter(
                Q(created_by=self.request.user) |
                Q(business_unit__in=self.request.user.business_units.all())
            )
        
        return queryset.select_related('position', 'business_unit', 'created_by')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['business_units'] = BusinessUnit.objects.all()
        return context


class SuccessionPlanDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = SuccessionPlan
    template_name = 'succession_planning/plan_detail.html'
    context_object_name = 'plan'
    
    def test_func(self):
        plan = self.get_object()
        user = self.request.user
        return (
            user.is_superuser or 
            plan.created_by == user or 
            plan.business_unit in user.business_units.all()
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plan = self.object
        
        # Estadísticas de candidatos
        candidates = plan.candidates.all()
        readiness_stats = candidates.values('readiness_level').annotate(
            count=Count('id'),
            percentage=Count('id') * 100 / candidates.count() if candidates.count() > 0 else 0
        )
        
        context.update({
            'candidates': candidates.select_related('candidate'),
            'readiness_stats': readiness_stats,
            'candidate_form': SuccessionCandidateForm(
                initial={'plan': plan},
                user=self.request.user
            ),
            'assessment_form': ReadinessAssessmentForm(
                user=self.request.user
            )
        })
        return context


class SuccessionPlanCreateView(LoginRequiredMixin, CreateView):
    model = SuccessionPlan
    form_class = SuccessionPlanForm
    template_name = 'succession_planning/plan_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'Plan de sucesión creado exitosamente.')
        return response
    
    def get_success_url(self):
        return reverse('succession_planning:plan_detail', kwargs={'pk': self.object.pk})


class SuccessionPlanUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = SuccessionPlan
    form_class = SuccessionPlanForm
    template_name = 'succession_planning/plan_form.html'
    
    def test_func(self):
        plan = self.get_object()
        user = self.request.user
        return (
            user.is_superuser or 
            plan.created_by == user or 
            user.has_perm('succession_planning.change_successionplan')
        )
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Plan de sucesión actualizado exitosamente.')
        return response
    
    def get_success_url(self):
        return reverse('succession_planning:plan_detail', kwargs={'pk': self.object.pk})


class SuccessionPlanDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = SuccessionPlan
    template_name = 'succession_planning/plan_confirm_delete.html'
    success_url = reverse_lazy('succession_planning:plan_list')
    
    def test_func(self):
        plan = self.get_object()
        user = self.request.user
        return (
            user.is_superuser or 
            plan.created_by == user or 
            user.has_perm('succession_planning.delete_successionplan')
        )
    
    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(self.request, 'Plan de sucesión eliminado exitosamente.')
        return response


@login_required
def add_candidate_to_plan(request, plan_id):
    plan = get_object_or_404(SuccessionPlan, pk=plan_id)
    
    # Verificar permisos
    if not (request.user.is_superuser or 
            plan.created_by == request.user or 
            plan.business_unit in request.user.business_units.all()):
        return HttpResponseForbidden()
    
    if request.method == 'POST':
        form = SuccessionCandidateForm(request.POST, user=request.user, plan=plan)
        if form.is_valid():
            candidate = form.save(commit=False)
            candidate.plan = plan
            candidate.added_by = request.user
            candidate.save()
            messages.success(request, 'Candidato agregado al plan de sucesión.')
            return redirect('succession_planning:plan_detail', pk=plan_id)
    else:
        form = SuccessionCandidateForm(user=request.user, plan=plan)
    
    return render(request, 'succession_planning/partials/candidate_form.html', {
        'form': form,
        'plan': plan
    })


@login_required
def remove_candidate_from_plan(request, pk):
    candidate = get_object_or_404(SuccessionCandidate, pk=pk)
    plan = candidate.plan
    
    # Verificar permisos
    if not (request.user.is_superuser or 
            plan.created_by == request.user or 
            plan.business_unit in request.user.business_units.all()):
        return HttpResponseForbidden()
    
    if request.method == 'POST':
        candidate.delete()
        messages.success(request, 'Candidato eliminado del plan de sucesión.')
        return redirect('succession_planning:plan_detail', pk=plan.pk)
    
    return render(request, 'succession_planning/partials/candidate_confirm_delete.html', {
        'candidate': candidate,
        'plan': plan
    })


@login_required
def assess_candidate_readiness(request, candidate_id):
    candidate = get_object_or_404(SuccessionCandidate, pk=candidate_id)
    plan = candidate.plan
    
    # Verificar permisos
    if not (request.user.is_superuser or 
            plan.created_by == request.user or 
            plan.business_unit in request.user.business_units.all() or
            request.user == candidate.added_by):
        return HttpResponseForbidden()
    
    if request.method == 'POST':
        form = ReadinessAssessmentForm(request.POST, user=request.user, candidate=candidate)
        if form.is_valid():
            assessment = form.save(commit=False)
            assessment.candidate = candidate
            assessment.assessed_by = request.user
            assessment.save()
            
            # Actualizar el estado del candidato
            candidate.readiness_level = assessment.readiness_level
            candidate.readiness_score = assessment.readiness_score
            candidate.last_assessed = assessment.assessment_date
            candidate.save(update_fields=['readiness_level', 'readiness_score', 'last_assessed'])
            
            messages.success(request, 'Evaluación de preparación guardada exitosamente.')
            return redirect('succession_planning:plan_detail', pk=plan.pk)
    else:
        form = ReadinessAssessmentForm(user=request.user, candidate=candidate)
    
    return render(request, 'succession_planning/partials/assessment_form.html', {
        'form': form,
        'candidate': candidate,
        'plan': plan
    })


class CandidateAssessmentsView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = SuccessionReadinessAssessment
    template_name = 'succession_planning/candidate_assessments.html'
    context_object_name = 'assessments'
    paginate_by = 10
    
    def test_func(self):
        candidate = get_object_or_404(SuccessionCandidate, pk=self.kwargs['pk'])
        return (
            self.request.user.is_superuser or
            candidate.plan.created_by == self.request.user or
            candidate.plan.business_unit in self.request.user.business_units.all() or
            candidate.added_by == self.request.user
        )
    
    def get_queryset(self):
        candidate = get_object_or_404(SuccessionCandidate, pk=self.kwargs['pk'])
        return candidate.assessments.all().select_related('assessed_by').order_by('-assessment_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['candidate'] = get_object_or_404(SuccessionCandidate, pk=self.kwargs['pk'])
        return context


@login_required
@require_http_methods(['GET'])
def search_candidates(request):
    """API para buscar candidatos (AJAX)"""
    query = request.GET.get('q', '').strip()
    
    if not query:
        return JsonResponse({'results': []})
    
    # Buscar personas que coincidan con la consulta
    persons = Person.objects.filter(
        Q(nombre__icontains=query) |
        Q(email__icontains=query) |
        Q(phone__icontains=query)
    ).annotate(
        full_name=Concat('nombre', Value(' '), 'apellido_paterno', Value(' '), 'apellido_materno',
                        output_field=CharField())
    ).values('id', 'full_name', 'email', 'phone')[:10]
    
    return JsonResponse({'results': list(persons)})


@login_required
@require_http_methods(['GET'])
def search_positions(request):
    """API para buscar posiciones (AJAX)"""
    query = request.GET.get('q', '').strip()
    
    if not query:
        return JsonResponse({'results': []})
    
    # Buscar vacantes que coincidan con la consulta
    positions = Vacante.objects.filter(
        Q(titulo__icontains=query) |
        Q(descripcion__icontains=query) |
        Q(empresa__name__icontains=query)
    ).select_related('empresa').values(
        'id', 'titulo', 'empresa__name', 'modalidad'
    )[:10]
    
    return JsonResponse({'results': list(positions)})


class SuccessionDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'succession_planning/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Obtener planes de sucesión a los que el usuario tiene acceso
        if user.is_superuser:
            plans = SuccessionPlan.objects.all()
        else:
            plans = SuccessionPlan.objects.filter(
                Q(created_by=user) |
                Q(business_unit__in=user.business_units.all())
            )
        
        # Estadísticas generales
        total_plans = plans.count()
        active_plans = plans.filter(status='active').count()
        total_candidates = SuccessionCandidate.objects.filter(plan__in=plans).count()
        
        # Distribución por nivel de preparación
        readiness_distribution = SuccessionCandidate.objects.filter(
            plan__in=plans
        ).values('readiness_level').annotate(
            count=Count('id'),
            percentage=Count('id') * 100.0 / total_candidates if total_candidates > 0 else 0
        )
        
        # Planes por estado
        plans_by_status = plans.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        # Últimas evaluaciones
        recent_assessments = SuccessionReadinessAssessment.objects.filter(
            candidate__plan__in=plans
        ).select_related('candidate', 'candidate__candidate', 'assessed_by').order_by('-assessment_date')[:5]
        
        context.update({
            'total_plans': total_plans,
            'active_plans': active_plans,
            'total_candidates': total_candidates,
            'readiness_distribution': readiness_distribution,
            'plans_by_status': plans_by_status,
            'recent_assessments': recent_assessments,
            'plans': plans.select_related('position', 'business_unit')[:5],
        })
        
        return context


class ReadinessReportView(LoginRequiredMixin, TemplateView):
    template_name = 'succession_planning/reports/readiness.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Obtener planes de sucesión a los que el usuario tiene acceso
        if user.is_superuser:
            plans = SuccessionPlan.objects.all()
        else:
            plans = SuccessionPlan.objects.filter(
                Q(created_by=user) |
                Q(business_unit__in=user.business_units.all())
            )
        
        # Filtrar por parámetros
        business_unit_id = self.request.GET.get('business_unit')
        status = self.request.GET.get('status')
        
        if business_unit_id:
            plans = plans.filter(business_unit_id=business_unit_id)
        
        if status:
            plans = plans.filter(status=status)
        
        # Obtener todos los candidatos de los planes filtrados
        candidates = SuccessionCandidate.objects.filter(
            plan__in=plans
        ).select_related('candidate', 'plan', 'plan__business_unit')
        
        # Agrupar por plan
        plans_data = []
        for plan in plans:
            plan_candidates = candidates.filter(plan=plan)
            plan_data = {
                'plan': plan,
                'candidate_count': plan_candidates.count(),
                'readiness_stats': plan_candidates.values('readiness_level').annotate(
                    count=Count('id'),
                    percentage=Count('id') * 100.0 / plan_candidates.count() if plan_candidates.count() > 0 else 0
                ),
                'avg_readiness_score': plan_candidates.aggregate(
                    avg=Avg('readiness_score')
                )['avg'] or 0
            }
            plans_data.append(plan_data)
        
        context.update({
            'plans_data': plans_data,
            'business_units': BusinessUnit.objects.all(),
            'selected_business_unit': int(business_unit_id) if business_unit_id else None,
            'selected_status': status
        })
        
        return context


class GapAnalysisReportView(LoginRequiredMixin, TemplateView):
    template_name = 'succession_planning/reports/gap_analysis.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Obtener planes de sucesión a los que el usuario tiene acceso
        if user.is_superuser:
            plans = SuccessionPlan.objects.all()
        else:
            plans = SuccessionPlan.objects.filter(
                Q(created_by=user) |
                Q(business_unit__in=user.business_units.all())
            )
        
        # Filtrar por parámetros
        business_unit_id = self.request.GET.get('business_unit')
        plan_id = self.request.GET.get('plan')
        
        if business_unit_id:
            plans = plans.filter(business_unit_id=business_unit_id)
        
        if plan_id:
            plans = plans.filter(id=plan_id)
        
        # Obtener todos los candidatos de los planes filtrados
        candidates = SuccessionCandidate.objects.filter(
            plan__in=plans
        ).select_related('candidate', 'plan')
        
        # Analizar brechas comunes
        all_gaps = {}
        for candidate in candidates:
            for gap in candidate.key_gaps:
                if gap in all_gaps:
                    all_gaps[gap] += 1
                else:
                    all_gaps[gap] = 1
        
        # Ordenar brechas por frecuencia
        sorted_gaps = sorted(all_gaps.items(), key=lambda x: x[1], reverse=True)
        
        # Obtener las 10 principales brechas
        top_gaps = dict(sorted_gaps[:10])
        
        context.update({
            'top_gaps': top_gaps,
            'business_units': BusinessUnit.objects.all(),
            'plans': plans,
            'selected_business_unit': int(business_unit_id) if business_unit_id else None,
            'selected_plan': int(plan_id) if plan_id else None
        })
        
        return context
