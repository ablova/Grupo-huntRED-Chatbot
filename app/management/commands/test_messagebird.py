"""
Comando Django para probar la integración de MessageBird enviando un SMS real.

Este comando utiliza el canal SMS con MessageBird configurado en la aplicación
para enviar un mensaje de prueba a un número específico en México y generar
un informe detallado del resultado.
"""

import asyncio
import logging
import json
from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone

from app.models import BusinessUnit
from app.ats.integrations.notifications.channels.sms import SMSNotificationChannel

logger = logging.getLogger('chatbot')

class Command(BaseCommand):
    help = 'Envía un SMS de prueba usando MessageBird y genera un reporte detallado.'
    
    def add_arguments(self, parser):
        parser.add_argument('--phone', type=str, required=False, 
                            help='Número de teléfono destino (formato: 525518490291)')
        parser.add_argument('--message', type=str, required=False, 
                            help='Mensaje personalizado a enviar')
        parser.add_argument('--business_unit', type=str, required=False, 
                            help='Código de Business Unit a utilizar')
    
    async def send_test_sms(self, business_unit, phone, message):
        """Envía un SMS de prueba y retorna el resultado."""
        try:
            # Inicializar el canal SMS
            sms_channel = SMSNotificationChannel(business_unit)
            
            # Crear opciones para el envío
            options = {
                'user_id': phone,
                'meta_pricing': {
                    'model': 'service',
                    'type': 'test',
                    'category': 'technical'
                }
            }
            
            # Enviar la notificación
            self.stdout.write(self.style.WARNING(f"Enviando SMS de prueba a {phone}..."))
            result = await sms_channel.send_notification(message, options, priority=0)
            
            return result
            
        except Exception as e:
            logger.error(f"Error en prueba de SMS: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def handle(self, *args, **options):
        # Valores predeterminados
        phone = options.get('phone') or '525518490291'  # Número de México especificado
        message = options.get('message') or '¡Prueba de sistema SMS con MessageBird! Este es un mensaje automatizado de prueba.'
        business_unit_code = options.get('business_unit')
        
        # Obtener la Business Unit
        try:
            if business_unit_code:
                business_unit = BusinessUnit.objects.get(code=business_unit_code)
                self.stdout.write(f"Usando Business Unit: {business_unit.name}")
            else:
                # Usar la primera BU disponible
                business_unit = BusinessUnit.objects.first()
                self.stdout.write(f"Usando Business Unit por defecto: {business_unit.name}")
                
            if not business_unit:
                self.stdout.write(self.style.ERROR("No se encontró ninguna Business Unit"))
                return
                
            # Ejecutar la prueba asíncrona
            result = asyncio.run(self.send_test_sms(business_unit, phone, message))
            
            # Generar informe
            self.stdout.write("\n" + "="*50)
            self.stdout.write(f"INFORME DE PRUEBA SMS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.stdout.write("="*50)
            self.stdout.write(f"Business Unit: {business_unit.name}")
            self.stdout.write(f"Número destino: {phone}")
            self.stdout.write(f"Mensaje enviado: {message}")
            self.stdout.write(f"Resultado: {'ÉXITO' if result.get('success') else 'ERROR'}")
            
            # Mostrar detalles según el resultado
            if result.get('success'):
                self.stdout.write(f"ID del mensaje: {result.get('message_id', 'N/A')}")
                self.stdout.write(f"Estado: {result.get('status', 'enviado')}")
                self.stdout.write(f"Referencia: {result.get('reference', 'N/A')}")
                self.stdout.write(f"Timestamp: {result.get('timestamp', 'N/A')}")
            else:
                self.stdout.write(self.style.ERROR(f"Error: {result.get('error', 'Desconocido')}"))
                
                # Sugerencias de solución
                self.stdout.write("\nSugerencias:")
                if 'auth' in str(result.get('error', '')).lower():
                    self.stdout.write("- Verificar que la API key de MessageBird esté configurada correctamente")
                elif 'recipient' in str(result.get('error', '')).lower():
                    self.stdout.write("- Verificar que el número de teléfono tenga formato internacional (+52...)")
                else:
                    self.stdout.write("- Revisar la configuración de MessageBird en la Business Unit")
                    self.stdout.write("- Confirmar que el servicio de MessageBird esté activo")
                    
            # Conclusión
            self.stdout.write("\nRecomendaciones:")
            if result.get('success'):
                self.stdout.write(self.style.SUCCESS("✓ El canal SMS está funcionando correctamente"))
                self.stdout.write("- Verificar en el teléfono destino que el mensaje se haya recibido correctamente")
                self.stdout.write("- Revisar en el portal de MessageBird los detalles completos de entrega")
            else:
                self.stdout.write(self.style.ERROR("✗ El canal SMS presenta problemas"))
                self.stdout.write("- Ejecutar nuevamente con --phone y --business_unit para pruebas adicionales")
                self.stdout.write("- Revisar la configuración de MessageBird en la base de datos")
                
            # Información para auditoría
            logger.info(f"Prueba SMS completada: {json.dumps(result, default=str)}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error ejecutando prueba: {str(e)}"))
