"""
Servicio para gestión de servicios externos de huntRED®.
"""
import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from datetime import datetime, timedelta

from app.models import BusinessUnit, Person
from app.ats.pricing.models import (
    ExternalServiceType,
    ExternalService,
    ExternalServiceMilestone,
    ExternalServiceInvoice,
    ExternalServiceActivity
)

logger = logging.getLogger(__name__)

class ExternalServiceService:
    """Servicio para gestionar servicios externos de huntRED®."""
    
    def __init__(self, business_unit: BusinessUnit):
        self.business_unit = business_unit
    
    def create_service_type(
        self,
        name: str,
        category: str,
        description: str,
        base_price: Decimal,
        price_type: str = 'fixed',
        billing_frequency: str = 'one_time'
    ) -> ExternalServiceType:
        """
        Crea un nuevo tipo de servicio externo.
        
        Args:
            name: Nombre del tipo de servicio
            category: Categoría del servicio
            description: Descripción del servicio
            base_price: Precio base
            price_type: Tipo de precio
            billing_frequency: Frecuencia de facturación
            
        Returns:
            ExternalServiceType creado
        """
        return ExternalServiceType.objects.create(
            name=name,
            category=category,
            description=description,
            base_price=base_price,
            price_type=price_type,
            billing_frequency=billing_frequency
        )
    
    def create_external_service(
        self,
        title: str,
        description: str,
        service_type: ExternalServiceType,
        client: Person,
        responsible: Person,
        estimated_amount: Decimal,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        priority: str = 'medium',
        billing_structure: str = 'upon_completion',
        requirements: List[str] = None,
        deliverables: List[str] = None,
        assigned_team: List[Person] = None,
        created_by: Optional[Person] = None
    ) -> ExternalService:
        """
        Crea un nuevo servicio externo.
        
        Args:
            title: Título del servicio
            description: Descripción del servicio
            service_type: Tipo de servicio
            client: Cliente
            responsible: Responsable
            estimated_amount: Monto estimado
            start_date: Fecha de inicio
            end_date: Fecha de fin (opcional)
            priority: Prioridad
            billing_structure: Estructura de facturación
            requirements: Lista de requisitos
            deliverables: Lista de entregables
            assigned_team: Equipo asignado
            created_by: Creador del servicio
            
        Returns:
            ExternalService creado
        """
        with transaction.atomic():
            service = ExternalService.objects.create(
                title=title,
                description=description,
                service_type=service_type,
                business_unit=self.business_unit,
                client=client,
                responsible=responsible,
                estimated_amount=estimated_amount,
                start_date=start_date,
                end_date=end_date,
                priority=priority,
                billing_structure=billing_structure,
                requirements=requirements or [],
                deliverables=deliverables or [],
                created_by=created_by
            )
            
            # Asignar equipo si se proporciona
            if assigned_team:
                service.assigned_team.set(assigned_team)
            
            # Crear actividad inicial
            ExternalServiceActivity.objects.create(
                service=service,
                activity_type='proposal',
                title='Servicio creado',
                description=f'Servicio externo "{title}" creado para {client.name}',
                created_by=responsible
            )
            
            logger.info(f"Servicio externo creado: {service.service_id}")
            return service
    
    def add_milestone(
        self,
        service: ExternalService,
        title: str,
        description: str,
        due_date: datetime,
        amount: Optional[Decimal] = None
    ) -> ExternalServiceMilestone:
        """
        Agrega un hito al servicio.
        
        Args:
            service: Servicio al que agregar el hito
            title: Título del hito
            description: Descripción del hito
            due_date: Fecha límite
            amount: Monto asociado (opcional)
            
        Returns:
            ExternalServiceMilestone creado
        """
        milestone = service.add_milestone(title, description, due_date, amount)
        
        # Crear actividad
        ExternalServiceActivity.objects.create(
            service=service,
            activity_type='milestone',
            title=f'Hito agregado: {title}',
            description=f'Hito "{title}" agregado con fecha límite {due_date.strftime("%Y-%m-%d")}',
            created_by=service.responsible
        )
        
        logger.info(f"Hito agregado al servicio {service.service_id}: {title}")
        return milestone
    
    def complete_milestone(self, milestone: ExternalServiceMilestone) -> bool:
        """
        Marca un hito como completado.
        
        Args:
            milestone: Hito a completar
            
        Returns:
            True si se completó exitosamente
        """
        try:
            milestone.complete_milestone()
            
            # Crear actividad
            ExternalServiceActivity.objects.create(
                service=milestone.service,
                activity_type='milestone',
                title=f'Hito completado: {milestone.title}',
                description=f'Hito "{milestone.title}" marcado como completado',
                created_by=milestone.service.responsible
            )
            
            logger.info(f"Hito completado: {milestone.service.service_id} - {milestone.title}")
            return True
            
        except Exception as e:
            logger.error(f"Error completando hito: {str(e)}")
            return False
    
    def create_invoice(
        self,
        service: ExternalService,
        subtotal: Decimal,
        tax_amount: Decimal = Decimal('0.00'),
        description: str = '',
        due_date: Optional[datetime] = None,
        created_by: Optional[Person] = None
    ) -> ExternalServiceInvoice:
        """
        Crea una factura para el servicio.
        
        Args:
            service: Servicio para el cual crear la factura
            subtotal: Subtotal de la factura
            tax_amount: Monto de impuestos
            description: Descripción de la factura
            due_date: Fecha de vencimiento
            created_by: Creador de la factura
            
        Returns:
            ExternalServiceInvoice creada
        """
        total_amount = subtotal + tax_amount
        
        invoice = ExternalServiceInvoice.objects.create(
            service=service,
            subtotal=subtotal,
            tax_amount=tax_amount,
            total_amount=total_amount,
            description=description or f'Factura por servicios de {service.title}',
            due_date=due_date or (timezone.now() + timedelta(days=30)),
            created_by=created_by
        )
        
        # Crear actividad
        ExternalServiceActivity.objects.create(
            service=service,
            activity_type='delivery',
            title=f'Factura creada: {invoice.invoice_number}',
            description=f'Factura por ${total_amount} MXN creada',
            created_by=created_by or service.responsible
        )
        
        logger.info(f"Factura creada: {invoice.invoice_number} para servicio {service.service_id}")
        return invoice
    
    def add_activity(
        self,
        service: ExternalService,
        activity_type: str,
        title: str,
        description: str,
        participants: List[Person] = None,
        duration_minutes: Optional[int] = None,
        outcome: str = '',
        next_actions: str = '',
        created_by: Optional[Person] = None
    ) -> ExternalServiceActivity:
        """
        Agrega una actividad al servicio.
        
        Args:
            service: Servicio al que agregar la actividad
            activity_type: Tipo de actividad
            title: Título de la actividad
            description: Descripción de la actividad
            participants: Participantes
            duration_minutes: Duración en minutos
            outcome: Resultado de la actividad
            next_actions: Próximas acciones
            created_by: Creador de la actividad
            
        Returns:
            ExternalServiceActivity creada
        """
        activity = ExternalServiceActivity.objects.create(
            service=service,
            activity_type=activity_type,
            title=title,
            description=description,
            duration_minutes=duration_minutes,
            outcome=outcome,
            next_actions=next_actions,
            created_by=created_by or service.responsible
        )
        
        # Agregar participantes si se proporcionan
        if participants:
            activity.participants.set(participants)
        
        logger.info(f"Actividad agregada: {activity_type} - {title} para servicio {service.service_id}")
        return activity
    
    def update_service_progress(
        self,
        service: ExternalService,
        progress_percentage: Decimal,
        notes: str = ''
    ) -> bool:
        """
        Actualiza el progreso del servicio.
        
        Args:
            service: Servicio a actualizar
            progress_percentage: Porcentaje de progreso
            notes: Notas adicionales
            
        Returns:
            True si se actualizó exitosamente
        """
        try:
            service.update_progress(progress_percentage)
            
            if notes:
                service.notes = notes
                service.save()
            
            # Crear actividad de seguimiento
            ExternalServiceActivity.objects.create(
                service=service,
                activity_type='follow_up',
                title=f'Progreso actualizado: {progress_percentage}%',
                description=f'Progreso del servicio actualizado a {progress_percentage}%',
                created_by=service.responsible
            )
            
            logger.info(f"Progreso actualizado: {service.service_id} - {progress_percentage}%")
            return True
            
        except Exception as e:
            logger.error(f"Error actualizando progreso: {str(e)}")
            return False
    
    def get_service_summary(self, service: ExternalService) -> Dict[str, Any]:
        """
        Obtiene un resumen completo del servicio.
        
        Args:
            service: Servicio del cual obtener el resumen
            
        Returns:
            Dict con el resumen del servicio
        """
        return {
            'service_id': service.service_id,
            'title': service.title,
            'status': service.status,
            'priority': service.priority,
            'progress_percentage': float(service.progress_percentage),
            'estimated_amount': float(service.estimated_amount),
            'actual_amount': float(service.actual_amount),
            'total_billed': float(service.get_total_billed()),
            'pending_amount': float(service.get_pending_amount()),
            'client': {
                'name': service.client.name,
                'email': service.client.email
            },
            'responsible': {
                'name': service.responsible.name,
                'email': service.responsible.email
            },
            'milestones': [
                {
                    'title': milestone.title,
                    'status': milestone.status,
                    'due_date': milestone.due_date.isoformat(),
                    'amount': float(milestone.amount) if milestone.amount else None
                }
                for milestone in service.milestones.all()
            ],
            'invoices': [
                {
                    'invoice_number': invoice.invoice_number,
                    'status': invoice.status,
                    'total_amount': float(invoice.total_amount),
                    'due_date': invoice.due_date.isoformat()
                }
                for invoice in service.invoices.all()
            ],
            'recent_activities': [
                {
                    'activity_type': activity.activity_type,
                    'title': activity.title,
                    'date': activity.activity_date.isoformat()
                }
                for activity in service.activities.all()[:5]
            ]
        }
    
    def get_business_unit_services(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[ExternalService]:
        """
        Obtiene servicios del business unit con filtros.
        
        Args:
            status: Filtrar por estado
            priority: Filtrar por prioridad
            start_date: Fecha de inicio
            end_date: Fecha de fin
            
        Returns:
            Lista de servicios filtrados
        """
        queryset = ExternalService.objects.filter(business_unit=self.business_unit)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if priority:
            queryset = queryset.filter(priority=priority)
        
        if start_date:
            queryset = queryset.filter(start_date__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(start_date__lte=end_date)
        
        return queryset.order_by('-created_at')
    
    def get_overdue_invoices(self) -> List[ExternalServiceInvoice]:
        """Obtiene facturas vencidas del business unit."""
        return ExternalServiceInvoice.objects.filter(
            service__business_unit=self.business_unit,
            status__in=['sent', 'draft']
        ).filter(due_date__lt=timezone.now())
    
    def get_upcoming_milestones(
        self,
        days_ahead: int = 7
    ) -> List[ExternalServiceMilestone]:
        """
        Obtiene hitos próximos a vencer.
        
        Args:
            days_ahead: Días hacia adelante para buscar
            
        Returns:
            Lista de hitos próximos
        """
        future_date = timezone.now() + timedelta(days=days_ahead)
        return ExternalServiceMilestone.objects.filter(
            service__business_unit=self.business_unit,
            status='pending',
            due_date__lte=future_date
        ).order_by('due_date')
    
    def get_service_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de servicios del business unit.
        
        Returns:
            Dict con estadísticas
        """
        services = ExternalService.objects.filter(business_unit=self.business_unit)
        
        total_services = services.count()
        active_services = services.filter(status__in=['active', 'in_progress']).count()
        completed_services = services.filter(status='completed').count()
        
        total_revenue = services.aggregate(
            total=models.Sum('actual_amount')
        )['total'] or Decimal('0.00')
        
        total_billed = ExternalServiceInvoice.objects.filter(
            service__business_unit=self.business_unit,
            status='paid'
        ).aggregate(
            total=models.Sum('total_amount')
        )['total'] or Decimal('0.00')
        
        overdue_invoices = self.get_overdue_invoices().count()
        
        return {
            'total_services': total_services,
            'active_services': active_services,
            'completed_services': completed_services,
            'total_revenue': float(total_revenue),
            'total_billed': float(total_billed),
            'pending_amount': float(total_revenue - total_billed),
            'overdue_invoices': overdue_invoices,
            'completion_rate': (completed_services / total_services * 100) if total_services > 0 else 0
        } 