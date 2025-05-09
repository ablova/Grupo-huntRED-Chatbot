from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone
from datetime import timedelta
from app.models import BusinessUnit, Proposal, Vacante, Opportunity, Vacancy, PricingBaseline, Addon, PaymentMilestone, Coupon


def calculate_pricing(proposal):
    """
    Calcula el pricing total y desglose para una propuesta.
    
    Args:
        proposal: Instancia de Proposal
        
    Returns:
        dict: Contiene el total y el desglose por vacante
    """
    pricing_details = {
        'total': Decimal('0.00'),
        'items': []
    }

    # Obtener configuración de pricing por BU
    bu_config = {}
    for bu in proposal.business_units.all():
        bu_config[bu.id] = {
            'base_rate': Decimal(bu.pricing_config.get('base_rate', '0.00')),
            'addons': bu.pricing_config.get('addons', {})
        }

    # Calcular pricing por vacante
    for vacancy in proposal.vacancies.all():
        bu_id = vacancy.business_unit_id
        bu = BusinessUnit.objects.get(id=bu_id)
        
        # Calcular base
        base = Decimal('0.00')
        if bu.pricing_config.get('base_type') == 'percentage':
            base = (Decimal(vacancy.salario) * 
                   Decimal(bu.pricing_config.get('base_rate', '0.00')) / 100)
        else:
            base = Decimal(bu.pricing_config.get('base_rate', '0.00'))

        # Calcular addons
        addons = []
        for addon_name, addon_config in bu_config[bu_id]['addons'].items():
            addon_price = Decimal('0.00')
            if addon_config.get('type') == 'percentage':
                addon_price = (base * Decimal(addon_config.get('rate', '0.00')) / 100)
            else:
                addon_price = Decimal(addon_config.get('amount', '0.00'))
            
            addons.append({
                'name': addon_name,
                'price': addon_price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            })

        # Calcular total
        total = base + sum(addon['price'] for addon in addons)
        
        # Agregar al desglose
        pricing_details['items'].append({
            'vacancy': vacancy,
            'bu': bu,
            'base': base.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'addons': addons,
            'total': total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        })
        
        # Actualizar total general
        pricing_details['total'] += total

    # Redondear el total final
    pricing_details['total'] = pricing_details['total'].quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP
    )

    return pricing_details


def calculate_pricing_opportunity(opportunity_id):
    """
    Calcula el pricing para una oportunidad.
    
    Args:
        opportunity_id: ID de la oportunidad
        
    Returns:
        dict: Detalles del pricing
    """
    from app.models import Opportunity, Vacancy, PricingBaseline, Addon
    
    # Obtener oportunidad y sus vacantes
    opportunity = Opportunity.objects.get(id=opportunity_id)
    vacancies = Vacancy.objects.filter(opportunity=opportunity)
    
    # Inicializar detalles del pricing
    pricing_details = {
        'total': Decimal('0.00'),
        'items': [],
        'addons': [],
        'milestones': []
    }
    
    # Obtener configuración base de pricing
    baseline = PricingBaseline.objects.get(bu=opportunity.business_unit)
    
    # Calcular pricing por vacante
    for vacancy in vacancies:
        item = {
            'vacancy': vacancy,
            'base_price': Decimal('0.00'),
            'addons': [],
            'total': Decimal('0.00')
        }
        
        # Calcular precio base
        if baseline.model == 'fixed':
            item['base_price'] = baseline.base_price
        else:
            item['base_price'] = (Decimal(vacancy.salary) * 
                               baseline.percentage / 100)
        
        # Agregar addons
        for addon in Addon.objects.filter(active=True):
            if addon.max_per_vacancy > 0:
                addon_price = addon.price
                item['addons'].append({
                    'name': addon.name,
                    'price': addon_price
                })
                
        # Calcular total de la vacante
        item['total'] = item['base_price'] + sum(
            addon['price'] for addon in item['addons']
        )
        
        pricing_details['items'].append(item)
        pricing_details['total'] += item['total']
    
    # Calcular hitos de pago
    milestones = generate_milestones(opportunity_id)
    pricing_details['milestones'] = milestones
    
    return pricing_details


def generate_milestones(opportunity_id):
    """
    Genera los hitos de pago para una oportunidad.
    
    Args:
        opportunity_id: ID de la oportunidad
        
    Returns:
        list: Lista de hitos de pago
    """
    from app.models import Opportunity, PaymentMilestone, BusinessUnit
    
    # Obtener oportunidad y su BU
    opportunity = Opportunity.objects.get(id=opportunity_id)
    bu = BusinessUnit.objects.get(name=opportunity.business_unit)
    
    # Obtener hitos configurados para el BU
    milestones = PaymentMilestone.objects.filter(bu=bu)
    
    # Calcular hitos
    milestone_list = []
    for milestone in milestones:
        milestone_list.append({
            'name': milestone.milestone_name,
            'percentage': milestone.percentage,
            'trigger_event': milestone.trigger_event,
            'due_date_offset': milestone.due_date_offset
        })
    
    return milestone_list


def apply_coupon(opportunity_id, coupon_code):
    """
    Aplica un cupón a una oportunidad.
    
    Args:
        opportunity_id: ID de la oportunidad
        coupon_code: Código del cupón
        
    Returns:
        dict: Pricing con descuento aplicado
    """
    from app.models import Coupon
    
    # Obtener cupón
    try:
        coupon = Coupon.objects.get(code=coupon_code)
        if not coupon.is_valid():
            raise ValueError("Cupón no válido o expirado")
            
        # Obtener pricing original
        pricing = calculate_pricing_opportunity(opportunity_id)
        
        # Aplicar descuento
        if coupon.type == 'fixed':
            discount = min(coupon.value, pricing['total'])
        else:
            discount = pricing['total'] * (coupon.value / 100)
            
        # Actualizar pricing
        pricing['total'] -= discount
        pricing['discount'] = {
            'type': coupon.type,
            'value': coupon.value,
            'amount': discount
        }
        
        # Incrementar uso del cupón
        coupon.used += 1
        coupon.save()
        
        return pricing
        
    except Coupon.DoesNotExist:
        raise ValueError("Cupón no encontrado")


def generate_proposal_pdf(proposal):
    """
    Genera un PDF con la propuesta.
    
    Args:
        proposal: Instancia de Proposal
        
    Returns:
        str: Path al archivo PDF generado
    """
    from django.template.loader import get_template
    from xhtml2pdf import pisa
    from io import BytesIO
    import os
    from django.conf import settings

    # Preparar contexto
    context = {
        'proposal': proposal,
        'pricing_details': proposal.pricing_details,
        'today': timezone.now().date(),
        'company': proposal.company
    }

    # Renderizar template
    template = get_template('pricing/proposal_pdf.html')
    html = template.render(context)

    # Generar PDF
    pdf_buffer = BytesIO()
    pisa.CreatePDF(html, dest=pdf_buffer)

    # Guardar PDF
    filename = f'proposal_{proposal.id}_{timezone.now().strftime("%Y%m%d")}.pdf'
    file_path = os.path.join(settings.MEDIA_ROOT, 'proposals', filename)
    
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, 'wb') as f:
        f.write(pdf_buffer.getvalue())

    # Actualizar propuesta con el path del PDF
    proposal.pdf_file = os.path.join('proposals', filename)
    proposal.save()

    return file_path


def create_payment_milestones(contract):
    """
    Crea los hitos de pago para un contrato basado en la configuración de la BU.
    
    Args:
        contract: Instancia de Contract
    """
    from app.models import PaymentMilestone
    
    # Obtener configuración de hitos de la primera BU
    bu = contract.proposal.business_units.first()
    milestones_config = bu.payment_milestones.all()

    for config in milestones_config:
        milestone = PaymentMilestone(
            contract=contract,
            name=config.name,
            description=config.description,
            percentage=config.percentage,
            trigger_event=config.trigger_event,
            due_date_offset=config.due_date_offset,
            status='PENDING'
        )
        
        # Calcular fecha estimada
        if config.trigger_event == 'CONTRACT_SIGNING':
            milestone.due_date = contract.signed_date + timedelta(days=config.due_date_offset)
        elif config.trigger_event == 'START_DATE':
            milestone.due_date = contract.start_date + timedelta(days=config.due_date_offset)
        elif config.trigger_event == 'MILESTONE_1':
            milestone.due_date = contract.start_date + timedelta(days=config.due_date_offset)
        
        milestone.save()
