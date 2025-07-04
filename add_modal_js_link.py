#!/usr/bin/env python3
"""
Script para agregar el enlace al modal JS en la plantilla
"""

def add_modal_js_link():
    """Agregar enlace al modal JS en la plantilla"""
    
    # Leer el archivo
    with open('app/templates/proposals/proposal_template.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🔧 Agregando enlace al modal JS...")
    
    # Buscar la línea donde están los otros enlaces JS
    if '/static/js/proposal-summary-modal.js' not in content:
        # Agregar después del enlace de digital-signature.js
        content = content.replace(
            '<script src="/static/js/digital-signature.js"></script>',
            '<script src="/static/js/digital-signature.js"></script>\n<script src="/static/js/proposal-summary-modal.js"></script>'
        )
    
    # Escribir el archivo actualizado
    with open('app/templates/proposals/proposal_template.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Enlace al modal JS agregado exitosamente!")

if __name__ == "__main__":
    add_modal_js_link() 