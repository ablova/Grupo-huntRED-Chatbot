# /home/pablo/app/com/chatbot/workflow/core/services.py
#
# Módulo de servicios para el chatbot.
# Incluye funcionalidades para manejo de evaluaciones, menús y más.
# Optimizado para bajo uso de CPU, escalabilidad, y robustez frente a fallos.

from typing import Dict

class Services:
    async def handle_evaluations_menu(self, user_id: int, business_unit: str) -> Dict:
        """Maneja el menú de evaluaciones disponibles."""
        menu_items = [
            {
                "id": "generational",
                "title": "Análisis Generacional",
                "description": "Evaluación de perfil generacional y compatibilidad"
            },
            {
                "id": "motivational",
                "title": "Análisis Motivacional",
                "description": "Evaluación de patrones de motivación y engagement"
            },
            {
                "id": "work_style",
                "title": "Análisis de Estilos de Trabajo",
                "description": "Evaluación de preferencias de trabajo y colaboración"
            },
            {
                "id": "career",
                "title": "Análisis de Desarrollo Profesional",
                "description": "Evaluación de trayectoria y objetivos profesionales"
            },
            {
                "id": "adaptability",
                "title": "Análisis de Adaptabilidad",
                "description": "Evaluación de flexibilidad y manejo de cambios"
            }
        ]
        
        return {
            "type": "menu",
            "title": "Evaluaciones Disponibles",
            "description": "Selecciona el tipo de evaluación que deseas realizar:",
            "items": menu_items
        }

    async def handle_menu(self, user_id: int, business_unit: str) -> Dict:
        """Maneja el menú principal del chatbot."""
        menu_items = [
            {
                "id": "evaluations",
                "title": "Evaluaciones",
                "description": "Accede a diferentes tipos de evaluaciones"
            },
            {
                "id": "profile",
                "title": "Mi Perfil",
                "description": "Ver y actualizar mi información"
            },
            {
                "id": "opportunities",
                "title": "Oportunidades",
                "description": "Ver oportunidades laborales disponibles"
            },
            {
                "id": "support",
                "title": "Soporte",
                "description": "Obtener ayuda y soporte"
            }
        ]
        
        return {
            "type": "menu",
            "title": "Menú Principal",
            "description": "¿En qué puedo ayudarte hoy?",
            "items": menu_items
        } 