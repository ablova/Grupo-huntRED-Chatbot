#!/usr/bin/env python3
"""
Prueba simple del servicio MessageBird para SMS
Permite usar API key directa o intentar cargar desde Django si está disponible
"""

import requests
import json
from datetime import datetime

def send_sms_test(phone_number, message):
    """
    Envía un SMS de prueba usando directamente la API de MessageBird
    
    Args:
        phone_number: Número al que enviar el SMS (formato internacional, ej: 525518490291)
        message: Mensaje a enviar
        
    Returns:
        Diccionario con el resultado de la operación
    """
    print(f"\n[{datetime.now().isoformat()}] Enviando SMS a {phone_number}...")
    
    # URL de la API de MessageBird
    api_url = "https://rest.messagebird.com/messages"
    
    # API Key (es necesario obtener una key real de MessageBird para pruebas)
    # En una implementación real, debería estar en variables de entorno o settings
    api_key = "YOUR_MESSAGEBIRD_API_KEY"  # Reemplazar con una clave real
    
    # Cabeceras para autenticación
    headers = {
        'Authorization': f'AccessKey {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Generar referencia única para el mensaje
    reference = f'test-{int(datetime.now().timestamp())}'
    
    # Configuración del SMS
    payload = {
        'originator': 'huntRED',  # Remitente (puede ser alfanumérico)
        'recipients': [phone_number],
        'body': message,
        'reference': reference,
        'type': 'sms'
    }
    
    try:
        # Realizar solicitud HTTP POST
        response = requests.post(api_url, headers=headers, json=payload)
        result = response.json()
        
        # Generar reporte
        success = response.status_code == 201 and 'id' in result
        status = "EXITOSO" if success else "FALLIDO"
        message_id = result.get('id', 'N/A') if success else 'N/A'
        error = result.get('errors', [{'description': 'Ninguno'}])[0]['description'] if not success else 'Ninguno'
        
        # Imprimir resultado en consola
        print("\nRESULTADO RAW:")
        print(json.dumps(result, indent=2))
        
        # Generar reporte detallado
        # Extraer estado del recipiente si está disponible
        recipient_status = 'Pendiente'
        if success and 'recipients' in result and 'items' in result['recipients']:
            if len(result['recipients']['items']) > 0:
                recipient_status = result['recipients']['items'][0].get('status', 'Pendiente')
        
        report = f"""
=========================================
REPORTE DE PRUEBA DE ENVÍO SMS (MessageBird)
=========================================
Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Destinatario: {phone_number}
Status: {status}
Message ID: {message_id}
Estado recipiente: {recipient_status}
Referencia: {reference}
Error: {error}

Mensaje enviado:
"{message}"

Notas:
- MessageBird requiere una API key válida
- Ofrece mejores tasas de entrega en México que alternativas gratuitas
- Para uso en producción, adquirir créditos en messagebird.com
=========================================
"""
        print(report)
        return result, report
        
    except Exception as e:
        error_msg = f"Error durante la prueba: {str(e)}"
        print(f"\n❌ ERROR: {error_msg}")
        return {'success': False, 'error': error_msg}, error_msg

if __name__ == "__main__":
    # Número de teléfono a probar
    phone_number = "525518490291"  # Número solicitado para la prueba
    
    # Mensaje de prueba con timestamp para distinguirlo
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    message = (
        f"Reporte de sistema: Implementación de canal SMS con MessageBird completada exitosamente. "
        f"Esta es una prueba de la integración con MessageBird. "
        f"Hora: {current_time}"
    )
    
    # Ejecutar prueba
    result, report = send_sms_test(phone_number, message)
    
    # Guardar reporte en un archivo
    with open('sms_test_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)
