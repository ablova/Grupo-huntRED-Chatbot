from typing import List, Dict, Any
import os

class AssessmentDataProvider:
    def __init__(self):
        self.assessments_dir = os.path.dirname(os.path.abspath(__file__))
        self.assessment_types = {
            'professional_dna': {
                'name': 'Professional DNA',
                'icon': 'fa-dna',
                'description': 'Evaluación completa del perfil profesional y competencias.',
                'duration': '25-30 min'
            },
            'cultural': {
                'name': 'Análisis Cultural',
                'icon': 'fa-users',
                'description': 'Evaluación de la cultura organizacional y valores.',
                'duration': '20-25 min'
            },
            'talent': {
                'name': 'Evaluación de Talento',
                'icon': 'fa-star',
                'description': 'Análisis de potencial y plan de carrera.',
                'duration': '20-35 min'
            },
            'compensation': {
                'name': 'Evaluación de Compensación',
                'icon': 'fa-money-bill-wave',
                'description': 'Análisis de estructura salarial y beneficios.',
                'duration': '15-20 min'
            },
            'personality': {
                'name': 'Evaluación de Personalidad',
                'icon': 'fa-user-circle',
                'description': 'Análisis de rasgos de personalidad y comportamiento.',
                'duration': '15-20 min'
            }
        }

    def get_available_assessments(self) -> List[Dict[str, Any]]:
        """Retorna la lista de evaluaciones disponibles."""
        return [
            {
                'name': data['name'],
                'icon': data['icon'],
                'description': data['description'],
                'duration': data['duration']
            }
            for assessment_type, data in self.assessment_types.items()
            if os.path.exists(os.path.join(self.assessments_dir, assessment_type))
        ]

    def get_additional_services(self) -> List[Dict[str, Any]]:
        """Retorna la lista de servicios adicionales relacionados con las evaluaciones."""
        return [
            {
                'name': 'Reportes Personalizados',
                'icon': 'fa-file-alt',
                'description': 'Generación de reportes detallados y personalizados basados en las evaluaciones.',
                'features': [
                    'Análisis comparativo',
                    'Recomendaciones personalizadas',
                    'Visualizaciones interactivas'
                ]
            },
            {
                'name': 'Consultoría Especializada',
                'icon': 'fa-handshake',
                'description': 'Asesoramiento experto para implementar mejoras basadas en los resultados.',
                'features': [
                    'Sesiones de consultoría',
                    'Plan de acción personalizado',
                    'Seguimiento continuo'
                ]
            },
            {
                'name': 'Capacitación y Desarrollo',
                'icon': 'fa-graduation-cap',
                'description': 'Programas de capacitación basados en los resultados de las evaluaciones.',
                'features': [
                    'Talleres personalizados',
                    'Material de capacitación',
                    'Seguimiento de progreso'
                ]
            }
        ] 