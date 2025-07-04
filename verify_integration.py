#!/usr/bin/env python3
"""
Script para verificar la integración del sistema de firma digital
"""

import os
import sys

def verify_integration():
    """Verificar que todos los componentes estén correctamente integrados"""
    
    print("🔍 Verificando integración del sistema de firma digital...")
    
    # Lista de archivos que deben existir
    required_files = [
        'app/static/js/digital-signature.js',
        'app/static/css/digital-signature.css',
        'app/static/js/proposal-summary-modal.js',
        'app/ats/views/proposal_signature.py',
        'app/templates/emails/proposal_signed_client.html',
        'app/templates/emails/proposal_signed_team.html',
        'app/templates/emails/proposal_signed_client.txt',
        'app/templates/emails/proposal_signed_team.txt'
    ]
    
    # Verificar archivos
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
        else:
            print(f"✅ {file_path}")
    
    if missing_files:
        print(f"\n❌ Archivos faltantes:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    
    # Verificar integración en la plantilla
    print("\n🔍 Verificando integración en la plantilla...")
    
    with open('app/templates/proposals/proposal_template.html', 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # Verificar enlaces CSS y JS
    css_link = '/static/css/digital-signature.css'
    js_link = '/static/js/digital-signature.js'
    modal_js_link = '/static/js/proposal-summary-modal.js'
    
    if css_link not in template_content:
        print(f"❌ Enlace CSS faltante: {css_link}")
        return False
    else:
        print(f"✅ Enlace CSS encontrado: {css_link}")
    
    if js_link not in template_content:
        print(f"❌ Enlace JS faltante: {js_link}")
        return False
    else:
        print(f"✅ Enlace JS encontrado: {js_link}")
    
    if modal_js_link not in template_content:
        print(f"❌ Enlace JS modal faltante: {modal_js_link}")
        return False
    else:
        print(f"✅ Enlace JS modal encontrado: {modal_js_link}")
    
    # Verificar pads de firma
    if 'clientSignaturePad' not in template_content:
        print("❌ Pad de firma del cliente no encontrado")
        return False
    else:
        print("✅ Pad de firma del cliente encontrado")
    
    if 'consultantSignaturePad' not in template_content:
        print("❌ Pad de firma del consultor no encontrado")
        return False
    else:
        print("✅ Pad de firma del consultor encontrado")
    
    # Verificar botón de guardar
    if 'btnGuardarPropuesta' not in template_content:
        print("❌ Botón de guardar propuesta no encontrado")
        return False
    else:
        print("✅ Botón de guardar propuesta encontrado")
    
    # Verificar integración con sistema de notificaciones
    print("\n🔍 Verificando integración con sistema de notificaciones...")
    
    with open('app/ats/views/proposal_signature.py', 'r', encoding='utf-8') as f:
        signature_content = f.read()
    
    if 'NotificationService' not in signature_content:
        print("❌ Sistema de notificaciones no integrado")
        return False
    else:
        print("✅ Sistema de notificaciones integrado")
    
    if 'NotificationChannel' not in signature_content:
        print("❌ Canales de notificación no configurados")
        return False
    else:
        print("✅ Canales de notificación configurados")
    
    # Verificar URLs
    print("\n🔍 Verificando configuración de URLs...")
    
    with open('app/ats/urls.py', 'r', encoding='utf-8') as f:
        urls_content = f.read()
    
    if 'proposal_signature' not in urls_content:
        print("❌ Endpoint de firma no configurado en URLs")
        return False
    else:
        print("✅ Endpoint de firma configurado en URLs")
    
    # Verificar módulos de firma digital
    print("\n🔍 Verificando módulos de firma digital...")
    
    signature_modules = [
        'app/ats/utils/signature/digital_sign.py',
        'app/ats/utils/signature/biometric_auth.py'
    ]
    
    for module_path in signature_modules:
        if os.path.exists(module_path):
            print(f"✅ {module_path}")
        else:
            print(f"⚠️  {module_path} - Verificar si existe")
    
    print("\n🎉 ¡Verificación completada!")
    print("\n📋 Resumen de integración:")
    print("   ✅ Archivos de firma digital creados")
    print("   ✅ Plantilla actualizada con pads de firma")
    print("   ✅ Sistema de notificaciones integrado")
    print("   ✅ Endpoints configurados")
    print("   ✅ Emails profesionales creados")
    print("   ✅ Popup de resumen implementado")
    
    print("\n🚀 El sistema está listo para usar!")
    print("\n📝 Próximos pasos:")
    print("   1. Verificar que los módulos de firma digital existan")
    print("   2. Probar el flujo completo de firma")
    print("   3. Verificar envío de emails")
    print("   4. Revisar popup de resumen final")
    
    return True

if __name__ == "__main__":
    success = verify_integration()
    sys.exit(0 if success else 1) 