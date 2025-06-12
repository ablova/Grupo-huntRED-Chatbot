# /home/pablo/app/com/pricing/utils.py

from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone
from datetime import timedelta
from typing import List, Dict, Optional, Union, Any
from ai_huntred.utils.lazy_imports import (
    BusinessUnit, Proposal, Vacante, Opportunity, Vacancy,
    PricingBaseline, Addon, PaymentMilestone, Coupon
)

def calculate_price(base_price: Decimal, addons: List[Addon], coupon: Optional[Coupon] = None) -> Decimal:
    """
    Calcula el precio final considerando addons y cupones.
    
    Args:
        base_price: Precio base
        addons: Lista de addons aplicados
        coupon: Cupón opcional
        
    Returns:
        Precio final calculado
    """
    final_price = base_price
    
    # Aplicar addons
    for addon in addons:
        if addon.percentage:
            final_price += (base_price * addon.value / 100)
        else:
            final_price += addon.value
            
    # Aplicar cupón si existe
    if coupon:
        if coupon.percentage:
            final_price -= (final_price * coupon.value / 100)
        else:
            final_price -= coupon.value
            
    return final_price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def calculate_milestone_payment(
    proposal: Proposal,
    milestone: PaymentMilestone,
    current_date: Optional[timezone.datetime] = None
) -> Decimal:
    """
    Calcula el pago para un hito específico.
    
    Args:
        proposal: Propuesta
        milestone: Hito de pago
        current_date: Fecha actual (opcional)
        
    Returns:
        Monto a pagar
    """
    if current_date is None:
        current_date = timezone.now()
        
    # Verificar si el hito está vencido
    if milestone.due_date < current_date:
        return Decimal('0.00')
        
    # Calcular monto base
    base_amount = proposal.total_amount * (milestone.percentage / 100)
    
    # Aplicar ajustes por retraso
    if milestone.due_date < current_date:
        days_late = (current_date - milestone.due_date).days
        late_fee = base_amount * Decimal('0.01') * days_late  # 1% por día
        base_amount += late_fee
        
    return base_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def get_business_unit_pricing(business_unit: BusinessUnit) -> Dict[str, Any]:
    """
    Obtiene la configuración de precios para una unidad de negocio.
    
    Args:
        business_unit: Unidad de negocio
        
    Returns:
        Diccionario con configuración de precios
    """
    try:
        baseline = PricingBaseline.objects.get(business_unit=business_unit)
        return {
            'base_price': baseline.base_price,
            'currency': baseline.currency,
            'payment_terms': baseline.payment_terms,
            'addons': list(baseline.addons.all()),
            'discounts': list(baseline.discounts.all())
        }
    except PricingBaseline.DoesNotExist:
        return {
            'base_price': Decimal('0.00'),
            'currency': 'USD',
            'payment_terms': [],
            'addons': [],
            'discounts': []
        }

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


# Registro global de servicios addon
_REGISTERED_ADDONS = {}


def register_addon_service(addon_id, name, description, model_class, pricing_class, template_name):
    """
    Registra un servicio addon en el sistema global de addons.
    
    Esta función permite que nuevos tipos de servicios addon (como el Análisis de Talento 360°)
    se registren dinámicamente en el sistema de pricing y propuestas.
    
    Args:
        addon_id: Identificador único del addon
        name: Nombre visible del servicio
        description: Descripción breve del servicio
        model_class: Clase del modelo Django para este addon
        pricing_class: Clase que implementa la lógica de pricing
        template_name: Nombre de la plantilla HTML para propuestas
    """
    global _REGISTERED_ADDONS
    
    _REGISTERED_ADDONS[addon_id] = {
        'id': addon_id,
        'name': name,
        'description': description,
        'model': model_class,
        'pricing': pricing_class,
        'template': template_name,
        'registered_at': timezone.now()
    }
    
    # Log registro exitoso
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Addon '{name}' (ID: {addon_id}) registrado exitosamente.")


def get_registered_addon(addon_id):
    """
    Obtiene la información de un addon registrado por su ID.
    
    Args:
        addon_id: ID del addon a obtener
        
    Returns:
        dict: Información del addon o None si no existe
    """
    return _REGISTERED_ADDONS.get(addon_id)


def get_all_registered_addons():
    """
    Obtiene todos los addons registrados en el sistema.
    
    Returns:
        dict: Mapa de addon_id a información de addon
    """
    return _REGISTERED_ADDONS


def calculate_addon_pricing(addon_id, **kwargs):
    """
    Calcula el precio de un addon específico.
    
    Args:
        addon_id: ID del addon
        **kwargs: Parámetros específicos para el cálculo de precio
        
    Returns:
        dict: Datos de pricing calculados
    """
    addon_info = get_registered_addon(addon_id)
    if not addon_info:
        raise ValueError(f"Addon '{addon_id}' no registrado en el sistema.")
        
    pricing_class = addon_info['pricing']
    if hasattr(pricing_class, 'calculate_total'):
        return pricing_class.calculate_total(**kwargs)
    
    raise NotImplementedError(f"La clase de pricing para '{addon_id}' no implementa calculate_total().")


def generate_addon_proposal(addon_id, **kwargs):
    """
    Genera los datos para una propuesta de addon.
    
    Args:
        addon_id: ID del addon
        **kwargs: Datos necesarios para la propuesta
        
    Returns:
        dict: Datos completos para la propuesta
    """
    addon_info = get_registered_addon(addon_id)
    if not addon_info:
        raise ValueError(f"Addon '{addon_id}' no registrado en el sistema.")
        
    pricing_class = addon_info['pricing']
    if hasattr(pricing_class, 'generate_proposal_data'):
        return pricing_class.generate_proposal_data(**kwargs)
    
    # Fallback a un cálculo básico
    pricing_data = calculate_addon_pricing(addon_id, **kwargs)
    return {
        'addon': addon_info,
        'pricing': pricing_data,
        'template': addon_info['template']
    }
