# /home/pablo/app/com/pricing/progressive_billing.py
"""
Módulo de facturación progresiva para Grupo huntRED®.

Este módulo gestiona la facturación por hitos de pago para diferentes tipos de servicios,
siguiendo los valores de Apoyo, Solidaridad y Sinergia de Grupo huntRED®.
"""

from decimal import Decimal, ROUND_HALF_UP
from django.db import models
from django.utils import timezone
from datetime import timedelta
from app.models import BusinessUnit, Contract, PaymentMilestone


class ProgressiveBilling:
    """
    Sistema de facturación progresiva basado en hitos para los servicios de huntRED.
    
    Permite configurar planes de pago flexibles según BusinessUnit, tipo de servicio
    y valor total del contrato.
    """
    
    # Configuraciones de hitos por Business Unit
    MILESTONE_CONFIGS = {
        'huntRED': [
            {'name': 'Firma de contrato', 'percentage': Decimal('30.00'), 'trigger': 'CONTRACT_SIGNING', 'days_offset': 0},
            {'name': 'Presentación de candidatos', 'percentage': Decimal('40.00'), 'trigger': 'CANDIDATES_PRESENTATION', 'days_offset': 15},
            {'name': 'Contratación', 'percentage': Decimal('30.00'), 'trigger': 'HIRING', 'days_offset': 30}
        ],
        'huntRED_Executive': [
            {'name': 'Firma de contrato', 'percentage': Decimal('40.00'), 'trigger': 'CONTRACT_SIGNING', 'days_offset': 0},
            {'name': 'Presentación de candidatos', 'percentage': Decimal('30.00'), 'trigger': 'CANDIDATES_PRESENTATION', 'days_offset': 20},
            {'name': 'Contratación', 'percentage': Decimal('30.00'), 'trigger': 'HIRING', 'days_offset': 40}
        ],
        'huntU': [
            {'name': 'Firma de contrato', 'percentage': Decimal('50.00'), 'trigger': 'CONTRACT_SIGNING', 'days_offset': 0},
            {'name': 'Contratación', 'percentage': Decimal('50.00'), 'trigger': 'HIRING', 'days_offset': 20}
        ],
        'Amigro': [
            {'name': 'Firma de contrato', 'percentage': Decimal('25.00'), 'trigger': 'CONTRACT_SIGNING', 'days_offset': 0},
            {'name': 'Primer grupo de candidatos', 'percentage': Decimal('25.00'), 'trigger': 'FIRST_CANDIDATES', 'days_offset': 7},
            {'name': 'Segundo grupo de candidatos', 'percentage': Decimal('25.00'), 'trigger': 'SECOND_CANDIDATES', 'days_offset': 14},
            {'name': 'Contratación completa', 'percentage': Decimal('25.00'), 'trigger': 'HIRING_COMPLETE', 'days_offset': 21}
        ],
        'SEXSI': [
            {'name': 'Firma de contrato', 'percentage': Decimal('100.00'), 'trigger': 'CONTRACT_SIGNING', 'days_offset': 0}
        ]
    }
    
    # Configuraciones especiales para contratos grandes
    LARGE_CONTRACT_CONFIGS = {
        'standard': [
            {'min_amount': Decimal('0.00'), 'max_amount': Decimal('100000.00'), 'milestones_key': None},
            {'min_amount': Decimal('100000.01'), 'max_amount': Decimal('300000.00'), 'milestones_key': '_large'},
            {'min_amount': Decimal('300000.01'), 'max_amount': Decimal('999999999.99'), 'milestones_key': '_enterprise'}
        ]
    }
    
    # Configuraciones para contratos grandes (+ de 100k)
    MILESTONE_CONFIGS.update({
        'huntRED_large': [
            {'name': 'Firma de contrato', 'percentage': Decimal('20.00'), 'trigger': 'CONTRACT_SIGNING', 'days_offset': 0},
            {'name': 'Inicio del proceso', 'percentage': Decimal('20.00'), 'trigger': 'START_PROCESS', 'days_offset': 7},
            {'name': 'Presentación de candidatos', 'percentage': Decimal('30.00'), 'trigger': 'CANDIDATES_PRESENTATION', 'days_offset': 20},
            {'name': 'Contratación', 'percentage': Decimal('30.00'), 'trigger': 'HIRING', 'days_offset': 35}
        ],
        'huntRED_enterprise': [
            {'name': 'Firma de contrato', 'percentage': Decimal('10.00'), 'trigger': 'CONTRACT_SIGNING', 'days_offset': 0},
            {'name': 'Inicio del proceso', 'percentage': Decimal('15.00'), 'trigger': 'START_PROCESS', 'days_offset': 7},
            {'name': 'Primer filtro', 'percentage': Decimal('15.00'), 'trigger': 'FIRST_FILTER', 'days_offset': 15},
            {'name': 'Presentación inicial', 'percentage': Decimal('20.00'), 'trigger': 'INITIAL_PRESENTATION', 'days_offset': 25},
            {'name': 'Ronda final', 'percentage': Decimal('20.00'), 'trigger': 'FINAL_ROUND', 'days_offset': 35},
            {'name': 'Contratación', 'percentage': Decimal('20.00'), 'trigger': 'HIRING', 'days_offset': 45}
        ]
    })
    
    @classmethod
    def get_milestone_config(cls, business_unit_name, contract_amount=None, service_type=None):
        """
        Obtiene la configuración de hitos de pago para una BU específica.
        
        Args:
            business_unit_name: Nombre de la BusinessUnit
            contract_amount: Monto total del contrato (para determinar si aplican reglas especiales)
            service_type: Tipo de servicio (opcional, para configuraciones específicas)
            
        Returns:
            list: Lista de configuraciones de hitos de pago
        """
        if business_unit_name not in cls.MILESTONE_CONFIGS:
            raise ValueError(f"Business unit '{business_unit_name}' no tiene configuración de hitos")
            
        # Verificar si aplican reglas especiales por monto
        milestones_key = business_unit_name
        
        if contract_amount is not None:
            # Buscar configuración específica para el monto
            for tier in cls.LARGE_CONTRACT_CONFIGS.get('standard', []):
                if tier['min_amount'] <= contract_amount <= tier['max_amount'] and tier['milestones_key'] is not None:
                    special_key = f"{business_unit_name}{tier['milestones_key']}"
                    if special_key in cls.MILESTONE_CONFIGS:
                        milestones_key = special_key
                        break
                        
        # Configuración específica por servicio (si existe)
        service_specific_key = f"{business_unit_name}_{service_type}" if service_type else None
        if service_specific_key in cls.MILESTONE_CONFIGS:
            milestones_key = service_specific_key
            
        return cls.MILESTONE_CONFIGS[milestones_key]
        
    @classmethod
    def generate_payment_schedule(cls, business_unit_name, start_date, contract_amount, 
                                 service_type=None, custom_milestones=None):
        """
        Genera un calendario de pagos basado en hitos para un contrato.
        
        Args:
            business_unit_name: Nombre de la BusinessUnit
            start_date: Fecha de inicio del contrato
            contract_amount: Monto total del contrato
            service_type: Tipo de servicio (opcional)
            custom_milestones: Configuración personalizada de hitos (opcional)
            
        Returns:
            dict: Calendario detallado de pagos con montos y fechas estimadas
        """
        # Usar hitos personalizados o configuración predeterminada
        milestones = custom_milestones or cls.get_milestone_config(
            business_unit_name, contract_amount, service_type
        )
        
        # Verificar que los porcentajes sumen 100%
        total_percentage = sum(m['percentage'] for m in milestones)
        if total_percentage != Decimal('100.00'):
            raise ValueError(f"Los porcentajes de hitos deben sumar 100%, suma actual: {total_percentage}%")
            
        # Generar calendario de pagos
        payment_schedule = []
        subtotal = contract_amount / Decimal('1.16')  # Quitar IVA para cálculos
        
        for milestone in milestones:
            milestone_amount = (subtotal * milestone['percentage'] / Decimal('100.00')).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            milestone_iva = milestone_amount * Decimal('0.16')
            milestone_total = milestone_amount + milestone_iva
            
            estimated_date = start_date + timedelta(days=milestone['days_offset'])
            
            payment_schedule.append({
                'name': milestone['name'],
                'trigger_event': milestone['trigger'],
                'percentage': milestone['percentage'],
                'amount': milestone_amount,
                'iva': milestone_iva,
                'total': milestone_total,
                'estimated_date': estimated_date.strftime('%d/%m/%Y'),
                'days_offset': milestone['days_offset']
            })
            
        # Calcular totales
        total_before_tax = sum(p['amount'] for p in payment_schedule)
        total_iva = sum(p['iva'] for p in payment_schedule)
        total_with_tax = sum(p['total'] for p in payment_schedule)
        
        result = {
            'business_unit': business_unit_name,
            'contract_amount': contract_amount,
            'start_date': start_date.strftime('%d/%m/%Y'),
            'payment_schedule': payment_schedule,
            'total_before_tax': total_before_tax,
            'total_iva': total_iva,
            'total_with_tax': total_with_tax,
            'currency': 'MXN'
        }
        
        return result
        
    @classmethod
    def create_payment_milestones(cls, contract, custom_milestones=None):
        """
        Crea registros de PaymentMilestone para un contrato.
        
        Args:
            contract: Instancia de Contract
            custom_milestones: Configuración personalizada de hitos (opcional)
            
        Returns:
            list: Lista de instancias de PaymentMilestone creadas
        """
        business_unit = contract.proposal.business_units.first()
        payment_schedule = cls.generate_payment_schedule(
            business_unit_name=business_unit.name,
            start_date=contract.signed_date,
            contract_amount=contract.total_amount,
            service_type=getattr(contract, 'service_type', None),
            custom_milestones=custom_milestones
        )
        
        milestones_created = []
        
        for milestone_data in payment_schedule['payment_schedule']:
            milestone = PaymentMilestone(
                contract=contract,
                name=milestone_data['name'],
                description=f"Hito de pago: {milestone_data['name']}",
                percentage=milestone_data['percentage'],
                trigger_event=milestone_data['trigger_event'],
                amount=milestone_data['total'],  # Monto con IVA
                due_date=contract.signed_date + timedelta(days=milestone_data['days_offset']),
                status='PENDING'
            )
            
            milestone.save()
            milestones_created.append(milestone)
            
        return milestones_created
