# app/chatbot/handlers/generational_handler.py
from ..core.base_handler import BaseHandler
from ...analytics.generational_processor import GenerationalAnalytics

class GenerationalHandler(BaseHandler):
    def __init__(self):
        super().__init__()
        self.analytics = GenerationalAnalytics()
        
    def handle_generational_analysis(self, user_data, context):
        """Maneja solicitudes de análisis generacional"""
        insights = self.analytics.process_generational_data(user_data)
        recommendations = self.analytics.generate_recommendations(insights)
        
        response = {
            'type': 'generational_analysis',
            'data': {
                'insights': insights,
                'recommendations': recommendations
            }
        }
        
        return self.format_response(response)
    
    def handle_team_compatibility(self, user_data, team_data, context):
        """Maneja solicitudes de compatibilidad de equipo"""
        compatibility = self.analytics.calculate_generational_compatibility(user_data, team_data)
        team_insights = self.analytics.generate_team_insights(team_data)
        
        response = {
            'type': 'team_compatibility',
            'data': {
                'compatibility': compatibility,
                'team_insights': team_insights
            }
        }
        
        return self.format_response(response)
    
    def handle_motivational_analysis(self, user_data, context):
        """Maneja solicitudes de análisis motivacional"""
        insights = self.analytics.process_generational_data(user_data)
        motivational_insights = insights['motivational']
        
        response = {
            'type': 'motivational_analysis',
            'data': {
                'motivational_profile': motivational_insights,
                'recommendations': self.analytics.generate_recommendations(insights)
            }
        }
        
        return self.format_response(response)
    
    def format_response(self, response):
        """Formatea la respuesta para el chatbot"""
        if response['type'] == 'generational_analysis':
            return self._format_generational_response(response['data'])
        elif response['type'] == 'team_compatibility':
            return self._format_team_response(response['data'])
        elif response['type'] == 'motivational_analysis':
            return self._format_motivational_response(response['data'])
        
        return "Lo siento, no pude procesar tu solicitud."
    
    def _format_generational_response(self, data):
        """Formatea respuesta de análisis generacional"""
        insights = data['insights']
        recommendations = data['recommendations']
        
        response = f"Basado en tu perfil generacional ({insights['generational']['generation']}), "
        response += "he identificado las siguientes características:\n\n"
        
        # Añadir insights principales
        response += "Preferencias Laborales:\n"
        for pref, value in insights['generational']['work_preferences'].items():
            response += f"- {pref}: {value}%\n"
        
        # Añadir recomendaciones
        response += "\nRecomendaciones:\n"
        for rec in recommendations:
            response += f"- {rec['title']}: {rec['description']}\n"
        
        return response
    
    def _format_team_response(self, data):
        """Formatea respuesta de compatibilidad de equipo"""
        compatibility = data['compatibility']
        team_insights = data['team_insights']
        
        response = f"Análisis de Compatibilidad del Equipo:\n\n"
        response += f"Compatibilidad Promedio: {compatibility['average_compatibility']}%\n\n"
        
        # Añadir insights del equipo
        response += "Diversidad Generacional:\n"
        for gen, count in team_insights['diversity'].items():
            response += f"- {gen}: {count} miembros\n"
        
        return response
    
    def _format_motivational_response(self, data):
        """Formatea respuesta de análisis motivacional"""
        profile = data['motivational_profile']
        recommendations = data['recommendations']
        
        response = "Tu Perfil Motivacional:\n\n"
        
        # Añadir motivadores intrínsecos
        response += "Motivadores Intrínsecos:\n"
        for motivator, value in profile['intrinsic'].items():
            response += f"- {motivator}: {value}%\n"
        
        # Añadir motivadores extrínsecos
        response += "\nMotivadores Extrínsecos:\n"
        for motivator, value in profile['extrinsic'].items():
            response += f"- {motivator}: {value}%\n"
        
        # Añadir recomendaciones
        response += "\nRecomendaciones:\n"
        for rec in recommendations:
            response += f"- {rec['title']}: {rec['description']}\n"
        
        return response 