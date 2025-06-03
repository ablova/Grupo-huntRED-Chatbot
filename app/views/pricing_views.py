# /home/pablo/app/views/pricing_views.py
#
# Vista para el módulo. Implementa la lógica de presentación y manejo de peticiones HTTP.

from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from app.ats.decorators import (
    super_admin_required, bu_complete_required, bu_division_required,
    business_unit_required, division_required, permission_required,
    verified_user_required, active_user_required
)
from app.models import (
    Proposal, Contract, PaymentMilestone, BusinessUnit, Company, Vacante
)
from app.ats.pricing.utils import calculate_pricing, generate_proposal_pdf, create_payment_milestones


class ProposalListView(View):
    @method_decorator(login_required)
    @method_decorator(permission_required('app.view_proposal'))
    def get(self, request):
        proposals = Proposal.objects.all().order_by('-created_at')
        context = {
            'proposals': proposals,
            'business_units': BusinessUnit.objects.all(),
            'companies': Company.objects.all()
        }
        return render(request, 'pricing/proposal_list.html', context)


class ProposalCreateView(View):
    @method_decorator(login_required)
    @method_decorator(permission_required('app.add_proposal'))
    def get(self, request):
        companies = Company.objects.all()
        business_units = BusinessUnit.objects.all()
        context = {
            'companies': companies,
            'business_units': business_units
        }
        return render(request, 'pricing/proposal_create.html', context)

    @method_decorator(login_required)
    @method_decorator(permission_required('app.add_proposal'))
    def post(self, request):
        company_id = request.POST.get('company')
        business_units = request.POST.getlist('business_units')
        vacancies = request.POST.getlist('vacancies')
        
        company = get_object_or_404(Company, id=company_id)
        proposal = Proposal.objects.create(company=company)
        
        for bu_id in business_units:
            proposal.business_units.add(bu_id)
        
        for vac_id in vacancies:
            proposal.vacancies.add(vac_id)
        
        # Calcular pricing
        pricing_details = calculate_pricing(proposal)
        proposal.pricing_details = pricing_details
        proposal.pricing_total = pricing_details['total']
        proposal.save()
        
        return redirect('proposal_detail', proposal_id=proposal.id)


class ProposalDetailView(View):
    @method_decorator(login_required)
    @method_decorator(permission_required('app.view_proposal'))
    def get(self, request, proposal_id):
        proposal = get_object_or_404(Proposal, id=proposal_id)
        context = {
            'proposal': proposal,
            'pricing_details': proposal.pricing_details
        }
        return render(request, 'pricing/proposal_detail.html', context)


class ProposalSendView(View):
    @method_decorator(login_required)
    @method_decorator(permission_required('app.change_proposal'))
    def post(self, request, proposal_id):
        proposal = get_object_or_404(Proposal, id=proposal_id)
        proposal.status = 'SENT'
        proposal.save()
        
        # Generar PDF y enviar por correo
        pdf_path = generate_proposal_pdf(proposal)
        
        return JsonResponse({'status': 'success'})


class ContractCreateView(View):
    @method_decorator(login_required)
    @method_decorator(permission_required('app.add_contract'))
    def post(self, request, proposal_id):
        proposal = get_object_or_404(Proposal, id=proposal_id)
        
        # Crear contrato
        contract = Contract.objects.create(
            proposal=proposal,
            start_date=proposal.start_date,
            end_date=proposal.end_date,
            status='PENDING_APPROVAL'
        )
        
        # Crear hitos de pago
        create_payment_milestones(contract)
        
        return redirect('contract_detail', contract_id=contract.id)


class ContractListView(View):
    @method_decorator(login_required)
    @method_decorator(permission_required('app.view_contract'))
    def get(self, request):
        contracts = Contract.objects.all().order_by('-created_at')
        context = {
            'contracts': contracts,
            'status_choices': CONTRATO_STATUS_CHOICES
        }
        return render(request, 'pricing/contract_list.html', context)


class ContractDetailView(View):
    @method_decorator(login_required)
    @method_decorator(permission_required('app.view_contract'))
    def get(self, request, contract_id):
        contract = get_object_or_404(Contract, id=contract_id)
        milestones = PaymentMilestone.objects.filter(contract=contract)
        context = {
            'contract': contract,
            'milestones': milestones,
            'status_choices': CONTRATO_STATUS_CHOICES,
            'event_choices': TRIGGER_EVENT_CHOICES
        }
        return render(request, 'pricing/contract_detail.html', context)


class ContractUpdateView(View):
    @method_decorator(login_required)
    @method_decorator(permission_required('app.change_contract'))
    def post(self, request, contract_id):
        contract = get_object_or_404(Contract, id=contract_id)
        
        # Actualizar estado del contrato
        status = request.POST.get('status')
        if status in dict(CONTRATO_STATUS_CHOICES):
            contract.status = status
            
            # Si el contrato es firmado, actualizar fechas de hitos
            if status == 'SIGNED':
                signed_date = timezone.now()
                contract.signed_date = signed_date
                
                # Actualizar fechas de hitos basados en la fecha de firma
                for milestone in contract.paymentmilestone_set.all():
                    if milestone.trigger_event == 'CONTRACT_SIGNING':
                        milestone.due_date = signed_date + timedelta(days=milestone.due_date_offset)
                        milestone.save()
            
            contract.save()
        
        return redirect('contract_detail', contract_id=contract.id)


class PaymentMilestoneUpdateView(View):
    @method_decorator(login_required)
    @method_decorator(permission_required('app.change_paymentmilestone'))
    def post(self, request, milestone_id):
        milestone = get_object_or_404(PaymentMilestone, id=milestone_id)
        
        # Actualizar estado del hito
        status = request.POST.get('status')
        if status in dict(PAYMENT_STATUS_CHOICES):
            milestone.status = status
            
            # Si el hito es pagado, actualizar fecha de pago
            if status == 'PAID':
                milestone.payment_date = timezone.now()
            
            milestone.save()
        
        return redirect('contract_detail', contract_id=milestone.contract.id)
