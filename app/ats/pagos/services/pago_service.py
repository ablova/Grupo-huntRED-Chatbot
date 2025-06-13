from typing import Dict, Any, Optional, List
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from app.ats.pagos.models import Pago, EstadoPago, TipoPago, MetodoPago
from app.ats.pagos.gateways import PayPalGateway, StripeGateway, MercadoPagoGateway
from app.models import Person, Vacante

class PagoService:
    """
    Servicio que maneja la lógica de negocio de pagos.
    """
    
    def __init__(self, business_unit: Optional[str] = None):
        """
        Inicializa el servicio de pagos.
        
        Args:
            business_unit: Unidad de negocio asociada (opcional)
        """
        self.business_unit = business_unit
        self.gateways = {
            MetodoPago.PAYPAL: PayPalGateway(business_unit),
            MetodoPago.STRIPE: StripeGateway(business_unit),
            MetodoPago.MERCADOPAGO: MercadoPagoGateway(business_unit)
        }
    
    def _validar_datos_pago(self, empleador_id: int, vacante_id: int, monto: float, 
                           moneda: str, metodo: str) -> Dict[str, Any]:
        """
        Valida los datos del pago antes de procesarlo.
        
        Args:
            empleador_id: ID del empleador
            vacante_id: ID de la vacante
            monto: Monto del pago
            moneda: Código de moneda
            metodo: Método de pago
            
        Returns:
            Dict con los objetos validados o error
        """
        try:
            # Validar empleador
            empleador = Person.objects.get(id=empleador_id)
            if not empleador.is_empleador:
                return {
                    'success': False,
                    'error': 'La persona especificada no es un empleador'
                }
            
            # Validar vacante
            vacante = Vacante.objects.get(id=vacante_id)
            if not vacante.activa:
                return {
                    'success': False,
                    'error': f'La vacante {vacante.titulo} no está activa'
                }
            
            # Validar monto
            if monto <= 0:
                return {
                    'success': False,
                    'error': 'El monto debe ser mayor a 0'
                }
            
            # Validar moneda
            if moneda not in ['MXN', 'USD']:
                return {
                    'success': False,
                    'error': 'Moneda no soportada'
                }
            
            # Validar método de pago
            if metodo not in self.gateways:
                return {
                    'success': False,
                    'error': f'Método de pago no soportado: {metodo}'
                }
            
            return {
                'success': True,
                'empleador': empleador,
                'vacante': vacante
            }
            
        except Person.DoesNotExist:
            return {
                'success': False,
                'error': 'Empleador no encontrado'
            }
        except Vacante.DoesNotExist:
            return {
                'success': False,
                'error': 'Vacante no encontrada'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @transaction.atomic
    def crear_pago(self, empleador_id: int, vacante_id: int, 
                   monto: float, moneda: str, metodo: str, 
                   tipo: str = TipoPago.MONOEDO, 
                   referencia_cliente: str = None, 
                   numero_contrato: str = None, 
                   **kwargs) -> Dict[str, Any]:
        """
        Crea un nuevo pago.
        
        Args:
            empleador_id: ID del empleador
            vacante_id: ID de la vacante
            monto: Monto del pago
            moneda: Código de moneda
            metodo: Método de pago
            tipo: Tipo de pago
            referencia_cliente: Referencia interna del cliente
            numero_contrato: Número de contrato
            **kwargs: Parámetros adicionales específicos del gateway
        """
        # Validar datos
        validacion = self._validar_datos_pago(
            empleador_id=empleador_id,
            vacante_id=vacante_id,
            monto=monto,
            moneda=moneda,
            metodo=metodo
        )
        
        if not validacion['success']:
            return validacion
        
        empleador = validacion['empleador']
        vacante = validacion['vacante']
        
        try:
            # Crear registro de pago
            pago = Pago.objects.create(
                empleador=empleador,
                vacante=vacante,
                business_unit=self.business_unit,
                monto=monto,
                monto_por_plaza=monto / vacante.numero_plazas,
                moneda=moneda,
                metodo=metodo,
                tipo=tipo,
                oportunidad_id=vacante.id,
                oportunidad_descripcion=vacante.descripcion,
                numero_plazas=vacante.numero_plazas,
                plazas_contratadas=0,
                referencia_cliente=referencia_cliente,
                numero_contrato=numero_contrato,
                metadata=kwargs
            )
            
            # Crear pago en el gateway
            gateway = self.gateways[metodo]
            response = gateway.create_payment(
                monto, 
                moneda, 
                f'Pago a Grupo huntRED® - {vacante.titulo}',
                **{
                    **kwargs,
                    'description': f'Servicios de reclutamiento para {vacante.titulo} - {vacante.numero_plazas} plazas',
                    'metadata': {
                        'business_unit': self.business_unit.name,
                        'vacancy_id': vacante.id,
                        'employer': empleador.email,
                        'oportunidad_id': pago.oportunidad_id,
                        'oportunidad_descripcion': pago.oportunidad_descripcion,
                        'numero_plazas': pago.numero_plazas,
                        'plazas_contratadas': pago.plazas_contratadas,
                        'referencia_cliente': pago.referencia_cliente,
                        'numero_contrato': pago.numero_contrato
                    }
                }
            )
            
            if response['success']:
                pago.id_transaccion = response.get('id')
                pago.url_webhook = response.get('webhook_url')
                pago.save()
                
                return {
                    'success': True,
                    'pago': pago,
                    'gateway_response': response
                }
            
            # Si falla, marcar como fallido
            pago.marcar_como_fallido(response.get('error'))
            return {
                'success': False,
                'error': response.get('error')
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @transaction.atomic
    def ejecutar_pago(self, pago_id: int, **kwargs) -> Dict[str, Any]:
        """
        Ejecuta un pago existente.
        
        Args:
            pago_id: ID del pago a ejecutar
            **kwargs: Parámetros adicionales específicos del gateway
        """
        try:
            pago = Pago.objects.get(id=pago_id)
            
            # Validar estado
            if pago.estado != EstadoPago.PENDIENTE:
                return {
                    'success': False,
                    'error': f'El pago no está pendiente (estado actual: {pago.estado})'
                }
            
            gateway = self.gateways[pago.metodo]
            response = gateway.execute_payment(pago.id_transaccion, **kwargs)
            
            if response['success']:
                pago.marcar_como_completado(response.get('id'))
                return {
                    'success': True,
                    'pago': pago,
                    'gateway_response': response
                }
            
            pago.marcar_como_fallido(response.get('error'))
            return {
                'success': False,
                'error': response.get('error')
            }
            
        except Pago.DoesNotExist:
            return {
                'success': False,
                'error': 'Pago no encontrado'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @transaction.atomic
    def crear_payout(self, pagos: List[Pago], **kwargs) -> Dict[str, Any]:
        """
        Crea un payout para múltiples pagos.
        
        Args:
            pagos: Lista de pagos a incluir en el payout
            **kwargs: Parámetros adicionales específicos del gateway
        """
        if not pagos:
            return {
                'success': False,
                'error': 'No se proporcionaron pagos'
            }
        
        try:
            # Verificar que todos los pagos usen el mismo método
            metodo = pagos[0].metodo
            if any(p.metodo != metodo for p in pagos):
                return {
                    'success': False,
                    'error': 'Todos los pagos deben usar el mismo método de pago'
                }
            
            # Verificar que todos los pagos estén completados
            if any(p.estado != EstadoPago.COMPLETADO for p in pagos):
                return {
                    'success': False,
                    'error': 'Todos los pagos deben estar completados'
                }
            
            gateway = self.gateways[metodo]
            response = gateway.create_payout([
                {
                    'monto': p.monto,
                    'moneda': p.moneda,
                    'empleado': p.empleado
                }
                for p in pagos
            ], **kwargs)
            
            if response['success']:
                for pago in pagos:
                    pago.id_transaccion = response.get('id')
                    pago.save()
                
                return {
                    'success': True,
                    'payout_id': response.get('id'),
                    'gateway_response': response
                }
            
            return {
                'success': False,
                'error': response.get('error')
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def procesar_webhook(self, request_body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa un webhook de pago.
        
        Args:
            request_body: Cuerpo de la solicitud webhook
        """
        try:
            # Identificar el gateway y verificar el webhook
            gateway_name = request_body.get('gateway')
            if not gateway_name or gateway_name not in self.gateways:
                return {
                    'success': False,
                    'error': 'Gateway no reconocido'
                }
            
            gateway = self.gateways[gateway_name]
            if not gateway.verify_webhook(request_body):
                return {
                    'success': False,
                    'error': 'Webhook no válido'
                }
            
            # Buscar el pago asociado
            pago = Pago.objects.get(id_transaccion=request_body.get('payment_id'))
            
            # Actualizar el estado del pago según el evento
            estado = request_body.get('status')
            if estado == 'completed':
                pago.marcar_como_completado(request_body.get('transaction_id'))
            elif estado in ['failed', 'rejected']:
                pago.marcar_como_fallido(request_body.get('reason'))
            
            # Guardar el payload del webhook
            pago.webhook_payload = request_body
            pago.save()
            
            return {
                'success': True,
                'pago': pago,
                'gateway_response': request_body
            }
            
        except Pago.DoesNotExist:
            return {
                'success': False,
                'error': 'Pago no encontrado'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            } 