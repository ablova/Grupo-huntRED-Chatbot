#!/usr/bin/env python
"""
Script de prueba para el canal SMS con TextBelt
"""
import os
import sys
import json
import django
from datetime import datetime
import asyncio

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Importar modelos y servicios
from app.models import BusinessUnit, MessageLog
from app.ats.integrations.notifications.channels.sms import SMSNotificationChannel

async def test_sms_channel(phone_number, message=None):
    """
    Prueba el envío de SMS usando el canal TextBelt
    
    Args:
        phone_number: Número al que enviar el SMS
        message: Mensaje personalizado (opcional)
    """
    print(f"[{datetime.now().isoformat()}] Iniciando prueba del canal SMS con TextBelt")
    
    # 1. Obtener o crear una unidad de negocio de prueba
    try:
        business_unit = BusinessUnit.objects.get(name="Test Business Unit")
        print(f"Usando unidad de negocio existente: {business_unit.name}")
    except BusinessUnit.DoesNotExist:
        business_unit = BusinessUnit.objects.create(
            name="Test Business Unit",
            description="Unidad de negocio para pruebas",
            active=True
        )
        print(f"Creada nueva unidad de negocio: {business_unit.name}")
    
    # 2. Crear instancia del canal SMS
    sms_channel = SMSNotificationChannel(business_unit)
    
    # 3. Preparar mensaje
    if not message:
        message = (
            f"¡Prueba de sistema de notificaciones SMS! "
            f"Enviado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. "
            "Este es un mensaje de prueba del sistema de Grupo huntRED."
        )
    
    # Opciones para el envío
    options = {
        'user_id': phone_number,
        'meta_pricing': {
            'model': 'service',
            'type': 'standard',
            'category': 'system_test'
        }
    }
    
    # 4. Enviar SMS
    print(f"Enviando SMS a {phone_number}...")
    try:
        result = await sms_channel.send_notification(
            message=message,
            options=options,
            priority=2  # Prioridad media (IMPORTANTE)
        )
        
        # 5. Mostrar resultado
        print("\nRESULTADO DEL ENVÍO:")
        print(json.dumps(result, indent=2, default=str))
        
        # 6. Generar reporte
        success = result.get('success', False)
        status = "EXITOSO" if success else "FALLIDO"
        error = result.get('error', 'Ninguno') if not success else 'Ninguno'
        quota = result.get('quota', 'N/A')
        
        report = f"""
        =========================================
        REPORTE DE PRUEBA DE ENVÍO SMS (TextBelt)
        =========================================
        Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        Destinatario: {phone_number}
        Status: {status}
        Message ID: {result.get('message_id', 'N/A')}
        Cuota restante: {quota}
        Error: {error}
        
        Mensaje enviado:
        "{message}"
        
        Notas:
        - TextBelt ofrece 1 SMS gratis por día por IP
        - Para uso en producción, adquirir créditos en textbelt.com
        =========================================
        """
        
        print(report)
        
        # 7. Verificar registro en MessageLog
        latest_log = MessageLog.objects.filter(
            phone=phone_number,
            channel='sms'
        ).order_by('-sent_at').first()
        
        if latest_log:
            print("\nRegistro en MessageLog confirmado:")
            print(f"ID: {latest_log.id}")
            print(f"Fecha: {latest_log.sent_at}")
            print(f"Status: {latest_log.status}")
            print(f"Canal: {latest_log.channel}")
            print(f"Modelo de pricing: {latest_log.meta_pricing_model}")
        else:
            print("\nADVERTENCIA: No se encontró registro en MessageLog")
            
        return success, report
            
    except Exception as e:
        error_msg = f"Error durante la prueba: {str(e)}"
        print(f"\n❌ ERROR: {error_msg}")
        return False, error_msg

if __name__ == "__main__":
    # Obtener número de teléfono de los args o usar el valor por defecto
    phone = sys.argv[1] if len(sys.argv) > 1 else "525518490291"
    
    # Mensaje personalizado (opcional)
    message = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Ejecutar prueba
    asyncio.run(test_sms_channel(phone, message))
