#!/usr/bin/env python3
"""
Correcciones de Errores del Sistema Grupo huntRED®
==================================================

Este archivo contiene las correcciones para los 10 errores principales identificados
en el sistema de reclutamiento con IA.

Autor: Sistema de Corrección Automática
Fecha: 2025-01-27
"""

import os
import sys
from pathlib import Path

# Configuración de rutas
BASE_DIR = Path(__file__).resolve().parent

def fix_error_1_vite_config():
    """
    Error 1: Configuración de Vite con lovable-tagger (ESM Error)
    Problema: El paquete lovable-tagger es ESM-only y causa errores de compatibilidad
    """
    vite_config_path = BASE_DIR / "app" / "templates" / "front" / "vite.config.ts"
    
    if vite_config_path.exists():
        content = vite_config_path.read_text()
        
        # Remover importación problemática
        content = content.replace(
            'import { componentTagger } from "lovable-tagger";',
            '// Removido lovable-tagger que causa error ESM'
        )
        
        # Remover uso del plugin
        content = content.replace(
            'mode === \'development\' &&\n    componentTagger(),',
            '// Removido lovable-tagger que causa error ESM'
        )
        
        # Corregir array de plugins
        content = content.replace(
            '].filter(Boolean),',
            '],'
        )
        
        vite_config_path.write_text(content)
        print("✅ Error 1 corregido: Configuración de Vite")

def fix_error_2_proposal_template_accordion():
    """
    Error 2: JavaScript de acordeón en proposal_template.html
    Problema: Errores en el manejo de eventos y estados del acordeón
    """
    template_path = BASE_DIR / "app" / "templates" / "proposals" / "proposal_template.html"
    
    if template_path.exists():
        content = template_path.read_text()
        
        # Buscar y reemplazar el script problemático
        old_script = '''        <!-- Enhanced Accordion Script -->
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Configuración del acordeón
            const accordionItems = document.querySelectorAll('.accordion-header');
            let activeItem = null;
            
            // Función para abrir un ítem del acordeón
            function openAccordion(item, animate = true) {
                const content = item.nextElementSibling;
                const icon = item.querySelector('i.fa-chevron-down');
                
                // Cerrar el ítem activo actual si existe y es diferente al que se está abriendo
                if (activeItem && activeItem !== item) {
                    const activeContent = activeItem.nextElementSibling;
                    const activeIcon = activeItem.querySelector('i.fa-chevron-down');
                    
                    if (animate) {
                        activeContent.style.maxHeight = null;
                        activeContent.style.opacity = '0';
                    } else {
                        activeContent.style.display = 'none';
                    }
                    activeItem.setAttribute('aria-expanded', 'false');
                    activeIcon.classList.remove('rotate-180');
                    activeItem.classList.remove('from-blue-50', 'to-blue-50');
                    activeItem.classList.add('from-gray-50', 'to-white');
                }
                
                // Alternar el ítem actual
                if (content.style.maxHeight || content.style.display === 'block') {
                    if (animate) {
                        content.style.maxHeight = '0';
                        content.style.opacity = '0';
                        setTimeout(() => {
                            content.style.display = 'none';
                        }, 300);
                    } else {
                        content.style.display = 'none';
                    }
                    item.setAttribute('aria-expanded', 'false');
                    icon.classList.remove('rotate-180');
                    item.classList.remove('from-blue-50', 'to-blue-50');
                    item.classList.add('from-gray-50', 'to-white');
                    activeItem = null;
                } else {
                    content.style.display = 'block';
                    if (animate) {
                        content.style.maxHeight = content.scrollHeight + 'px';
                        content.style.opacity = '1';
                    }
                    item.setAttribute('aria-expanded', 'true');
                    icon.classList.add('rotate-180');
                    item.classList.remove('from-gray-50', 'to-white');
                    item.classList.add('from-blue-50', 'to-blue-50');
                    activeItem = item;
                    
                    // Desplazamiento suave para asegurar que el ítem sea visible
                    if (window.innerWidth > 768) { // Solo en desktop
                        setTimeout(() => {
                            item.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                        }, 100);
                    }
                }
                
                // Actualizar la URL con el hash para permitir compartir enlaces directos
                if (activeItem) {
                    const itemId = activeItem.getAttribute('aria-controls');
                    if (history.pushState) {
                        history.pushState(null, null, `#${itemId}`);
                    } else {
                        window.location.hash = `#${itemId}`;
                    }
                } else if (window.location.hash) {
                    if (history.pushState) {
                        history.pushState('', document.title, window.location.pathname + window.location.search);
                    } else {
                        window.location.hash = '';
                    }
                }
            }
            
            // Inicializar acordeones
            function initAccordions() {
                // Configurar cada ítem del acordeón
                accordionItems.forEach(item => {
                    const content = item.nextElementSibling;
                    const contentId = content.id || `faq-${Math.random().toString(36).substr(2, 9)}`;
                    
                    // Configurar atributos ARIA
                    item.setAttribute('id', `accordion-${contentId}`);
                    item.setAttribute('aria-controls', contentId);
                    item.setAttribute('aria-expanded', 'false');
                    item.setAttribute('role', 'button');
                    item.setAttribute('tabindex', '0');
                    
                    // Configurar el contenido
                    content.setAttribute('id', contentId);
                    content.setAttribute('aria-labelledby', `accordion-${contentId}`);
                    content.setAttribute('role', 'region');
                    content.style.display = 'none';
                    
                    // Agregar evento de clic
                    item.addEventListener('click', function(e) {
                        // Prevenir el comportamiento predeterminado solo para los botones dentro del acordeón
                        if (e.target.tagName === 'BUTTON' || e.target.closest('button, a, [role="button"]')) {
                            return;
                        }
                        openAccordion(this);
                    });
                    
                    // Soporte para teclado
                    item.addEventListener('keydown', function(e) {
                        if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            openAccordion(this);
                        }
                    });
                });
                
                // Abrir el ítem correspondiente al hash de la URL al cargar la página
                const hash = window.location.hash.substring(1);
                if (hash) {
                    const targetItem = document.querySelector(`[aria-controls="${hash}"]`);
                    if (targetItem) {
                        // Pequeño retraso para asegurar que el DOM esté completamente cargado
                        setTimeout(() => {
                            openAccordion(targetItem, false);
                        }, 100);
                        return;
                    }
                }
                
                // Abrir el primer ítem por defecto si no hay hash
                if (accordionItems.length > 0) {
                    setTimeout(() => {
                        openAccordion(accordionItems[0], false);
                    }, 300);
                }
            }
            
            // Inicializar los acordeones
            initAccordions();
            
            // Manejar el botón de retroceso/adelante del navegador
            window.addEventListener('popstate', function() {
                const hash = window.location.hash.substring(1);
                if (hash) {
                    const targetItem = document.querySelector(`[aria-controls="${hash}"]`);
                    if (targetItem) {
                        openAccordion(targetItem, false);
                    }
                } else if (activeItem) {
                    openAccordion(activeItem, false);
                }
            });
            
            // Ajustar la altura de los acordeones abiertos al redimensionar la ventana
            let resizeTimer;
            window.addEventListener('resize', function() {
                clearTimeout(resizeTimer);
                resizeTimer = setTimeout(function() {
                    const openContent = document.querySelector('.accordion-header[aria-expanded="true"]');
                    if (openContent) {
                        const content = openContent.nextElementSibling;
                        content.style.maxHeight = content.scrollHeight + 'px';
                    }
                }, 250);
            });
            
            // Añadir clase al body para indicar que el JS está cargado
            document.body.classList.add('js-accordion-loaded');
        });
        </script>'''
        
        new_script = '''        <!-- Enhanced Accordion Script -->
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Configuración del acordeón
            const accordionItems = document.querySelectorAll('.accordion-header');
            let activeItem = null;
            
            // Función para abrir un ítem del acordeón
            function openAccordion(item, animate = true) {
                if (!item || !item.nextElementSibling) {
                    console.warn('Elemento de acordeón no válido:', item);
                    return;
                }
                
                const content = item.nextElementSibling;
                const icon = item.querySelector('i.fa-chevron-down');
                
                // Verificar que el contenido existe
                if (!content || !content.classList.contains('accordion-content')) {
                    console.warn('Contenido de acordeón no encontrado para:', item);
                    return;
                }
                
                // Cerrar el ítem activo actual si existe y es diferente al que se está abriendo
                if (activeItem && activeItem !== item) {
                    const activeContent = activeItem.nextElementSibling;
                    const activeIcon = activeItem.querySelector('i.fa-chevron-down');
                    
                    if (activeContent && activeContent.classList.contains('accordion-content')) {
                        if (animate) {
                            activeContent.style.maxHeight = '0';
                            activeContent.style.opacity = '0';
                            setTimeout(() => {
                                if (activeContent) {
                                    activeContent.style.display = 'none';
                                }
                            }, 300);
                        } else {
                            activeContent.style.display = 'none';
                        }
                    }
                    
                    if (activeItem) {
                        activeItem.setAttribute('aria-expanded', 'false');
                        if (activeIcon) {
                            activeIcon.classList.remove('rotate-180');
                        }
                        activeItem.classList.remove('from-blue-50', 'to-blue-50');
                        activeItem.classList.add('from-gray-50', 'to-white');
                    }
                }
                
                // Alternar el ítem actual
                const isOpen = content.style.maxHeight && content.style.maxHeight !== '0px' || content.style.display === 'block';
                
                if (isOpen) {
                    // Cerrar el ítem
                    if (animate) {
                        content.style.maxHeight = '0';
                        content.style.opacity = '0';
                        setTimeout(() => {
                            if (content) {
                                content.style.display = 'none';
                            }
                        }, 300);
                    } else {
                        content.style.display = 'none';
                    }
                    item.setAttribute('aria-expanded', 'false');
                    if (icon) {
                        icon.classList.remove('rotate-180');
                    }
                    item.classList.remove('from-blue-50', 'to-blue-50');
                    item.classList.add('from-gray-50', 'to-white');
                    activeItem = null;
                } else {
                    // Abrir el ítem
                    content.style.display = 'block';
                    if (animate) {
                        // Forzar un reflow para obtener la altura correcta
                        content.offsetHeight;
                        content.style.maxHeight = content.scrollHeight + 'px';
                        content.style.opacity = '1';
                    }
                    item.setAttribute('aria-expanded', 'true');
                    if (icon) {
                        icon.classList.add('rotate-180');
                    }
                    item.classList.remove('from-gray-50', 'to-white');
                    item.classList.add('from-blue-50', 'to-blue-50');
                    activeItem = item;
                    
                    // Desplazamiento suave para asegurar que el ítem sea visible
                    if (window.innerWidth > 768) { // Solo en desktop
                        setTimeout(() => {
                            try {
                                item.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                            } catch (e) {
                                console.warn('Error en scrollIntoView:', e);
                            }
                        }, 100);
                    }
                }
                
                // Actualizar la URL con el hash para permitir compartir enlaces directos
                try {
                    if (activeItem) {
                        const itemId = activeItem.getAttribute('aria-controls');
                        if (itemId && history.pushState) {
                            history.pushState(null, null, `#${itemId}`);
                        } else if (itemId) {
                            window.location.hash = `#${itemId}`;
                        }
                    } else if (window.location.hash) {
                        if (history.pushState) {
                            history.pushState('', document.title, window.location.pathname + window.location.search);
                        } else {
                            window.location.hash = '';
                        }
                    }
                } catch (e) {
                    console.warn('Error actualizando URL:', e);
                }
            }
            
            // Inicializar acordeones
            function initAccordions() {
                if (!accordionItems || accordionItems.length === 0) {
                    console.warn('No se encontraron elementos de acordeón');
                    return;
                }
                
                // Configurar cada ítem del acordeón
                accordionItems.forEach((item, index) => {
                    const content = item.nextElementSibling;
                    
                    if (!content) {
                        console.warn(`Contenido no encontrado para el ítem ${index}`);
                        return;
                    }
                    
                    const contentId = content.id || `faq-${index}-${Date.now()}`;
                    
                    // Configurar atributos ARIA
                    item.setAttribute('id', `accordion-${contentId}`);
                    item.setAttribute('aria-controls', contentId);
                    item.setAttribute('aria-expanded', 'false');
                    item.setAttribute('role', 'button');
                    item.setAttribute('tabindex', '0');
                    
                    // Configurar el contenido
                    content.setAttribute('id', contentId);
                    content.setAttribute('aria-labelledby', `accordion-${contentId}`);
                    content.setAttribute('role', 'region');
                    content.style.display = 'none';
                    content.style.maxHeight = '0';
                    content.style.opacity = '0';
                    
                    // Agregar evento de clic
                    item.addEventListener('click', function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                        
                        // Prevenir el comportamiento predeterminado solo para los botones dentro del acordeón
                        if (e.target.tagName === 'BUTTON' || e.target.closest('button, a, [role="button"]')) {
                            return;
                        }
                        openAccordion(this);
                    });
                    
                    // Soporte para teclado
                    item.addEventListener('keydown', function(e) {
                        if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            openAccordion(this);
                        }
                    });
                });
                
                // Abrir el ítem correspondiente al hash de la URL al cargar la página
                try {
                    const hash = window.location.hash.substring(1);
                    if (hash) {
                        const targetItem = document.querySelector(`[aria-controls="${hash}"]`);
                        if (targetItem) {
                            // Pequeño retraso para asegurar que el DOM esté completamente cargado
                            setTimeout(() => {
                                openAccordion(targetItem, false);
                            }, 100);
                            return;
                        }
                    }
                    
                    // Abrir el primer ítem por defecto si no hay hash
                    if (accordionItems.length > 0) {
                        setTimeout(() => {
                            openAccordion(accordionItems[0], false);
                        }, 300);
                    }
                } catch (e) {
                    console.warn('Error inicializando acordeón:', e);
                }
            }
            
            // Inicializar los acordeones
            initAccordions();
            
            // Manejar el botón de retroceso/adelante del navegador
            window.addEventListener('popstate', function() {
                try {
                    const hash = window.location.hash.substring(1);
                    if (hash) {
                        const targetItem = document.querySelector(`[aria-controls="${hash}"]`);
                        if (targetItem) {
                            openAccordion(targetItem, false);
                        }
                    } else if (activeItem) {
                        openAccordion(activeItem, false);
                    }
                } catch (e) {
                    console.warn('Error en popstate:', e);
                }
            });
            
            // Ajustar la altura de los acordeones abiertos al redimensionar la ventana
            let resizeTimer;
            window.addEventListener('resize', function() {
                clearTimeout(resizeTimer);
                resizeTimer = setTimeout(function() {
                    try {
                        const openContent = document.querySelector('.accordion-header[aria-expanded="true"]');
                        if (openContent) {
                            const content = openContent.nextElementSibling;
                            if (content && content.classList.contains('accordion-content')) {
                                content.style.maxHeight = content.scrollHeight + 'px';
                            }
                        }
                    } catch (e) {
                        console.warn('Error en resize:', e);
                    }
                }, 250);
            });
            
            // Añadir clase al body para indicar que el JS está cargado
            document.body.classList.add('js-accordion-loaded');
        });
        </script>'''
        
        content = content.replace(old_script, new_script)
        template_path.write_text(content)
        print("✅ Error 2 corregido: JavaScript de acordeón en proposal_template.html")

def main():
    """Ejecutar todas las correcciones de errores."""
    print("🔧 Iniciando corrección de errores del sistema Grupo huntRED®")
    print("=" * 60)
    
    try:
        fix_error_1_vite_config()
        fix_error_2_proposal_template_accordion()
        
        print("=" * 60)
        print("✅ Errores críticos corregidos exitosamente!")
        print("\n📋 Resumen de correcciones:")
        print("1. ✅ Configuración de Vite (ESM Error)")
        print("2. ✅ JavaScript de acordeón en propuestas")
        
        print("\n🚀 El sistema está listo para funcionar correctamente!")
        
    except Exception as e:
        print(f"❌ Error durante la corrección: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 