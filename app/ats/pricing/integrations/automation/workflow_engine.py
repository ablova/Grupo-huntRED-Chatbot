# app/ats/pricing/integrations/automation/workflow_engine.py
"""
Integración con automatización y workflows para pricing y pagos.
"""
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from decimal import Decimal
import json
from enum import Enum
from dataclasses import dataclass

from app.models import BusinessUnit, Person
from app.ats.pricing.models.external_services import ExternalService, ExternalServiceInvoice
from app.ats.pricing.models.payments import ScheduledPayment, PaymentTransaction

logger = logging.getLogger(__name__)

class WorkflowStatus(Enum):
    """Estados de un workflow."""
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'

class TriggerType(Enum):
    """Tipos de triggers para workflows."""
    INVOICE_CREATED = 'invoice_created'
    INVOICE_DUE = 'invoice_due'
    PAYMENT_RECEIVED = 'payment_received'
    PAYMENT_FAILED = 'payment_failed'
    SERVICE_STARTED = 'service_started'
    SERVICE_COMPLETED = 'service_completed'
    CLIENT_RISK_HIGH = 'client_risk_high'
    SCHEDULED_PAYMENT_DUE = 'scheduled_payment_due'

@dataclass
class WorkflowStep:
    """Paso de un workflow."""
    name: str
    action: str
    parameters: Dict[str, Any]
    conditions: Optional[List[Dict[str, Any]]] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout: int = 300  # segundos

class WorkflowEngine:
    """Motor de workflows para automatización de pricing y pagos."""
    
    def __init__(self, business_unit: BusinessUnit):
        self.business_unit = business_unit
        self.workflows = {}
        self.actions = {}
        self.triggers = {}
        
        # Registrar acciones por defecto
        self._register_default_actions()
        
        # Registrar workflows por defecto
        self._register_default_workflows()
    
    def register_action(self, name: str, action_func: Callable):
        """Registra una nueva acción."""
        self.actions[name] = action_func
        logger.info(f"Acción registrada: {name}")
    
    def create_workflow(
        self,
        name: str,
        description: str,
        trigger_type: TriggerType,
        steps: List[WorkflowStep],
        enabled: bool = True
    ) -> Dict[str, Any]:
        """
        Crea un nuevo workflow.
        
        Args:
            name: Nombre del workflow
            description: Descripción
            trigger_type: Tipo de trigger
            steps: Lista de pasos
            enabled: Si está habilitado
            
        Returns:
            Dict con información del workflow creado
        """
        try:
            workflow = {
                'id': f"{self.business_unit.id}_{name}",
                'name': name,
                'description': description,
                'trigger_type': trigger_type.value,
                'steps': [self._step_to_dict(step) for step in steps],
                'enabled': enabled,
                'created_at': datetime.now().isoformat(),
                'last_modified': datetime.now().isoformat()
            }
            
            self.workflows[workflow['id']] = workflow
            
            # Registrar trigger
            if trigger_type.value not in self.triggers:
                self.triggers[trigger_type.value] = []
            self.triggers[trigger_type.value].append(workflow['id'])
            
            logger.info(f"Workflow creado: {name}")
            
            return {
                'success': True,
                'workflow': workflow
            }
            
        except Exception as e:
            logger.error(f"Error creando workflow: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def execute_workflow(
        self,
        workflow_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Ejecuta un workflow.
        
        Args:
            workflow_id: ID del workflow
            context: Contexto de ejecución
            
        Returns:
            Dict con resultado de la ejecución
        """
        try:
            if workflow_id not in self.workflows:
                return {
                    'success': False,
                    'error': f'Workflow no encontrado: {workflow_id}'
                }
            
            workflow = self.workflows[workflow_id]
            
            if not workflow['enabled']:
                return {
                    'success': False,
                    'error': 'Workflow deshabilitado'
                }
            
            # Crear instancia de ejecución
            execution = {
                'id': f"{workflow_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'workflow_id': workflow_id,
                'status': WorkflowStatus.RUNNING.value,
                'context': context,
                'steps_executed': [],
                'started_at': datetime.now().isoformat(),
                'completed_at': None,
                'error': None
            }
            
            # Ejecutar pasos
            for step_data in workflow['steps']:
                step = self._dict_to_step(step_data)
                
                # Verificar condiciones
                if step.conditions and not self._evaluate_conditions(step.conditions, context):
                    logger.info(f"Condiciones no cumplidas para paso: {step.name}")
                    continue
                
                # Ejecutar paso
                step_result = self._execute_step(step, context, execution)
                
                if not step_result['success']:
                    execution['status'] = WorkflowStatus.FAILED.value
                    execution['error'] = step_result['error']
                    execution['completed_at'] = datetime.now().isoformat()
                    
                    logger.error(f"Workflow falló en paso {step.name}: {step_result['error']}")
                    return {
                        'success': False,
                        'execution': execution,
                        'error': step_result['error']
                    }
                
                execution['steps_executed'].append({
                    'step_name': step.name,
                    'result': step_result,
                    'executed_at': datetime.now().isoformat()
                })
                
                # Actualizar contexto con resultado del paso
                context.update(step_result.get('output', {}))
            
            # Workflow completado exitosamente
            execution['status'] = WorkflowStatus.COMPLETED.value
            execution['completed_at'] = datetime.now().isoformat()
            
            logger.info(f"Workflow completado exitosamente: {workflow_id}")
            
            return {
                'success': True,
                'execution': execution
            }
            
        except Exception as e:
            logger.error(f"Error ejecutando workflow: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def trigger_workflows(
        self,
        trigger_type: TriggerType,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Dispara workflows basados en un trigger.
        
        Args:
            trigger_type: Tipo de trigger
            context: Contexto del trigger
            
        Returns:
            Dict con resultados de ejecución
        """
        try:
            triggered_workflows = self.triggers.get(trigger_type.value, [])
            results = []
            
            for workflow_id in triggered_workflows:
                if workflow_id in self.workflows and self.workflows[workflow_id]['enabled']:
                    result = self.execute_workflow(workflow_id, context)
                    results.append({
                        'workflow_id': workflow_id,
                        'result': result
                    })
            
            return {
                'success': True,
                'trigger_type': trigger_type.value,
                'workflows_triggered': len(results),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error disparando workflows: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _register_default_actions(self):
        """Registra acciones por defecto."""
        
        # Acción: Enviar recordatorio de pago
        def send_payment_reminder(context):
            try:
                invoice = context.get('invoice')
                if not invoice:
                    return {'success': False, 'error': 'No se encontró factura en contexto'}
                
                # Importar aquí para evitar dependencias circulares
                from app.ats.pricing.integrations.whatsapp.whatsapp_notifications import WhatsAppNotifications
                
                whatsapp = WhatsAppNotifications(self.business_unit)
                result = whatsapp.send_payment_reminder(
                    invoice=invoice,
                    recipient=invoice.service.client,
                    days_overdue=context.get('days_overdue', 0)
                )
                
                return {
                    'success': result['success'],
                    'output': {'reminder_sent': result['success']},
                    'error': result.get('error')
                }
                
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        # Acción: Generar CFDI
        def generate_cfdi(context):
            try:
                invoice = context.get('invoice')
                if not invoice:
                    return {'success': False, 'error': 'No se encontró factura en contexto'}
                
                # Importar aquí para evitar dependencias circulares
                from app.ats.pricing.integrations.sat.sat_integration import SATIntegration
                
                # Obtener configuración PAC
                pac_config = self._get_pac_configuration()
                if not pac_config:
                    return {'success': False, 'error': 'No se encontró configuración PAC'}
                
                sat_integration = SATIntegration(self.business_unit, pac_config)
                result = sat_integration.generate_cfdi_4_0(invoice)
                
                return {
                    'success': result['success'],
                    'output': {'cfdi_generated': result['success'], 'uuid': result.get('uuid')},
                    'error': result.get('error')
                }
                
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        # Acción: Analizar riesgo de cliente
        def analyze_client_risk(context):
            try:
                client = context.get('client')
                if not client:
                    return {'success': False, 'error': 'No se encontró cliente en contexto'}
                
                # Importar aquí para evitar dependencias circulares
                from app.ats.pricing.integrations.ai.risk_analysis import AIRiskAnalysis
                
                risk_analyzer = AIRiskAnalysis(self.business_unit)
                result = risk_analyzer.analyze_client_risk(client)
                
                return {
                    'success': result['success'],
                    'output': {
                        'risk_score': result.get('risk_score'),
                        'risk_category': result.get('risk_category'),
                        'risk_factors': result.get('risk_factors', [])
                    },
                    'error': result.get('error')
                }
                
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        # Acción: Ejecutar pago programado
        def execute_scheduled_payment(context):
            try:
                scheduled_payment = context.get('scheduled_payment')
                if not scheduled_payment:
                    return {'success': False, 'error': 'No se encontró pago programado en contexto'}
                
                # Lógica para ejecutar pago
                payment_result = self._process_scheduled_payment(scheduled_payment)
                
                return {
                    'success': payment_result['success'],
                    'output': {
                        'payment_executed': payment_result['success'],
                        'transaction_id': payment_result.get('transaction_id')
                    },
                    'error': payment_result.get('error')
                }
                
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        # Acción: Enviar notificación
        def send_notification(context):
            try:
                notification_type = context.get('notification_type')
                recipient = context.get('recipient')
                message = context.get('message')
                
                if not all([notification_type, recipient, message]):
                    return {'success': False, 'error': 'Faltan parámetros de notificación'}
                
                # Lógica para enviar notificación
                notification_result = self._send_notification(notification_type, recipient, message)
                
                return {
                    'success': notification_result['success'],
                    'output': {'notification_sent': notification_result['success']},
                    'error': notification_result.get('error')
                }
                
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        # Registrar acciones
        self.register_action('send_payment_reminder', send_payment_reminder)
        self.register_action('generate_cfdi', generate_cfdi)
        self.register_action('analyze_client_risk', analyze_client_risk)
        self.register_action('execute_scheduled_payment', execute_scheduled_payment)
        self.register_action('send_notification', send_notification)
    
    def _register_default_workflows(self):
        """Registra workflows por defecto."""
        
        # Workflow: Factura vencida
        invoice_overdue_steps = [
            WorkflowStep(
                name='analyze_client_risk',
                action='analyze_client_risk',
                parameters={'client': '{{invoice.service.client}}'},
                conditions=[{'field': 'days_overdue', 'operator': '>', 'value': 7}]
            ),
            WorkflowStep(
                name='send_payment_reminder',
                action='send_payment_reminder',
                parameters={'invoice': '{{invoice}}', 'days_overdue': '{{days_overdue}}'}
            ),
            WorkflowStep(
                name='send_notification',
                action='send_notification',
                parameters={
                    'notification_type': 'payment_overdue',
                    'recipient': '{{invoice.service.client}}',
                    'message': 'Factura vencida - acción requerida'
                },
                conditions=[{'field': 'risk_category', 'operator': '==', 'value': 'ALTO'}]
            )
        ]
        
        self.create_workflow(
            name='invoice_overdue_workflow',
            description='Workflow para facturas vencidas',
            trigger_type=TriggerType.INVOICE_DUE,
            steps=invoice_overdue_steps
        )
        
        # Workflow: Pago recibido
        payment_received_steps = [
            WorkflowStep(
                name='generate_cfdi',
                action='generate_cfdi',
                parameters={'invoice': '{{invoice}}'}
            ),
            WorkflowStep(
                name='send_notification',
                action='send_notification',
                parameters={
                    'notification_type': 'payment_confirmation',
                    'recipient': '{{invoice.service.client}}',
                    'message': 'Pago confirmado - CFDI generado'
                }
            )
        ]
        
        self.create_workflow(
            name='payment_received_workflow',
            description='Workflow para pagos recibidos',
            trigger_type=TriggerType.PAYMENT_RECEIVED,
            steps=payment_received_steps
        )
        
        # Workflow: Cliente de alto riesgo
        high_risk_client_steps = [
            WorkflowStep(
                name='analyze_client_risk',
                action='analyze_client_risk',
                parameters={'client': '{{client}}'}
            ),
            WorkflowStep(
                name='send_notification',
                action='send_notification',
                parameters={
                    'notification_type': 'high_risk_client',
                    'recipient': '{{business_unit.admin_email}}',
                    'message': 'Cliente de alto riesgo detectado'
                },
                conditions=[{'field': 'risk_category', 'operator': '==', 'value': 'ALTO'}]
            )
        ]
        
        self.create_workflow(
            name='high_risk_client_workflow',
            description='Workflow para clientes de alto riesgo',
            trigger_type=TriggerType.CLIENT_RISK_HIGH,
            steps=high_risk_client_steps
        )
    
    def _execute_step(
        self,
        step: WorkflowStep,
        context: Dict[str, Any],
        execution: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Ejecuta un paso del workflow."""
        try:
            if step.action not in self.actions:
                return {
                    'success': False,
                    'error': f'Acción no encontrada: {step.action}'
                }
            
            # Resolver parámetros del contexto
            resolved_params = self._resolve_parameters(step.parameters, context)
            
            # Ejecutar acción
            action_func = self.actions[step.action]
            result = action_func(resolved_params)
            
            return result
            
        except Exception as e:
            logger.error(f"Error ejecutando paso {step.name}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _evaluate_conditions(
        self,
        conditions: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> bool:
        """Evalúa condiciones de un paso."""
        for condition in conditions:
            field = condition['field']
            operator = condition['operator']
            value = condition['value']
            
            # Obtener valor del campo desde el contexto
            field_value = self._get_field_value(field, context)
            
            # Evaluar condición
            if not self._evaluate_condition(field_value, operator, value):
                return False
        
        return True
    
    def _evaluate_condition(
        self,
        field_value: Any,
        operator: str,
        value: Any
    ) -> bool:
        """Evalúa una condición individual."""
        if operator == '==':
            return field_value == value
        elif operator == '!=':
            return field_value != value
        elif operator == '>':
            return field_value > value
        elif operator == '<':
            return field_value < value
        elif operator == '>=':
            return field_value >= value
        elif operator == '<=':
            return field_value <= value
        elif operator == 'in':
            return field_value in value
        elif operator == 'not_in':
            return field_value not in value
        else:
            return False
    
    def _resolve_parameters(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resuelve parámetros usando el contexto."""
        resolved = {}
        
        for key, value in parameters.items():
            if isinstance(value, str) and value.startswith('{{') and value.endswith('}}'):
                # Variable del contexto
                field_path = value[2:-2]  # Remover {{ }}
                resolved[key] = self._get_field_value(field_path, context)
            else:
                resolved[key] = value
        
        return resolved
    
    def _get_field_value(self, field_path: str, context: Dict[str, Any]) -> Any:
        """Obtiene valor de un campo del contexto."""
        try:
            # Soporte para campos anidados (ej: invoice.service.client.name)
            parts = field_path.split('.')
            value = context
            
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                elif hasattr(value, part):
                    value = getattr(value, part)
                else:
                    return None
            
            return value
        except Exception:
            return None
    
    def _step_to_dict(self, step: WorkflowStep) -> Dict[str, Any]:
        """Convierte WorkflowStep a dict."""
        return {
            'name': step.name,
            'action': step.action,
            'parameters': step.parameters,
            'conditions': step.conditions,
            'retry_count': step.retry_count,
            'max_retries': step.max_retries,
            'timeout': step.timeout
        }
    
    def _dict_to_step(self, step_data: Dict[str, Any]) -> WorkflowStep:
        """Convierte dict a WorkflowStep."""
        return WorkflowStep(
            name=step_data['name'],
            action=step_data['action'],
            parameters=step_data['parameters'],
            conditions=step_data.get('conditions'),
            retry_count=step_data.get('retry_count', 0),
            max_retries=step_data.get('max_retries', 3),
            timeout=step_data.get('timeout', 300)
        )
    
    def _get_pac_configuration(self):
        """Obtiene configuración PAC."""
        # Implementar lógica para obtener configuración PAC
        return None
    
    def _process_scheduled_payment(self, scheduled_payment: ScheduledPayment) -> Dict[str, Any]:
        """Procesa un pago programado."""
        # Implementar lógica para procesar pago programado
        return {'success': False, 'error': 'No implementado'}
    
    def _send_notification(
        self,
        notification_type: str,
        recipient: Person,
        message: str
    ) -> Dict[str, Any]:
        """Envía una notificación."""
        # Implementar lógica para enviar notificación
        return {'success': False, 'error': 'No implementado'}
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Obtiene el estado de un workflow.
        
        Args:
            workflow_id: ID del workflow
            
        Returns:
            Dict con estado del workflow
        """
        if workflow_id not in self.workflows:
            return {
                'success': False,
                'error': 'Workflow no encontrado'
            }
        
        workflow = self.workflows[workflow_id]
        
        return {
            'success': True,
            'workflow': workflow
        }
    
    def list_workflows(self) -> Dict[str, Any]:
        """
        Lista todos los workflows.
        
        Returns:
            Dict con lista de workflows
        """
        return {
            'success': True,
            'workflows': list(self.workflows.values())
        }
    
    def enable_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Habilita un workflow.
        
        Args:
            workflow_id: ID del workflow
            
        Returns:
            Dict con resultado
        """
        if workflow_id not in self.workflows:
            return {
                'success': False,
                'error': 'Workflow no encontrado'
            }
        
        self.workflows[workflow_id]['enabled'] = True
        self.workflows[workflow_id]['last_modified'] = datetime.now().isoformat()
        
        return {
            'success': True,
            'message': 'Workflow habilitado'
        }
    
    def disable_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Deshabilita un workflow.
        
        Args:
            workflow_id: ID del workflow
            
        Returns:
            Dict con resultado
        """
        if workflow_id not in self.workflows:
            return {
                'success': False,
                'error': 'Workflow no encontrado'
            }
        
        self.workflows[workflow_id]['enabled'] = False
        self.workflows[workflow_id]['last_modified'] = datetime.now().isoformat()
        
        return {
            'success': True,
            'message': 'Workflow deshabilitado'
        } 