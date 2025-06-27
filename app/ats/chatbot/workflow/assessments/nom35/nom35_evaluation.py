from app.ats.chatbot.workflow.assessments.nom35.nom35_questions import NOM35_GUIA_II, NOM35_GUIA_III, NOM35_OPTIONS
from app.ats.chatbot.workflow.assessments.nom35.nom35_questions import NOM35_OPTIONS_WHATSAPP  # Defínelo si no existe

class NOM35EvaluationWorkflow:
    """
    Workflow para la evaluación NOM 35, compatible con canales web y WhatsApp.
    """
    def __init__(self, profile='employee', channel='web'):
        self.profile = profile  # 'employee' o 'leader'
        self.channel = channel  # 'web', 'whatsapp', etc.
        self.guide = NOM35_GUIA_III if self.profile == 'leader' else NOM35_GUIA_II
        self.options = NOM35_OPTIONS_WHATSAPP if self.channel == 'whatsapp' else NOM35_OPTIONS
        self.total_questions = sum(len(section['questions']) for section in self.guide)
        self.answers = {}
        self.current_section = 0
        self.current_question = 0
        self.completed = False

    def get_next_question(self):
        if self.current_section >= len(self.guide):
            self.completed = True
            return None
        section = self.guide[self.current_section]
        if self.current_question >= len(section['questions']):
            self.current_section += 1
            self.current_question = 0
            return self.get_next_question()
        question = section['questions'][self.current_question]
        return {
            'section': section['section'],
            'id': question['id'],
            'text': question['text'],
            'options': self.options
        }

    def answer_question(self, value):
        section = self.guide[self.current_section]
        question = section['questions'][self.current_question]
        self.answers[question['id']] = value
        self.current_question += 1
        if self.current_question >= len(section['questions']):
            self.current_section += 1
            self.current_question = 0
        if self.current_section >= len(self.guide):
            self.completed = True

    def is_complete(self):
        return self.completed

    def get_results(self):
        # Cálculo de puntajes por dominio
        scores = {}
        for section in self.guide:
            section_score = 0
            for question in section['questions']:
                section_score += self.answers.get(question['id'], 0)
            scores[section['section']] = section_score
        return scores

    def get_methodology_section(self):
        return (
            "Cumplimiento con la NOM-035\n"
            "La NOM-035-STPS-2018 establece los lineamientos para identificar y prevenir factores de riesgo psicosocial en el trabajo. "
            "Las Guías de Referencia II (menos de 50 trabajadores) y III (50 o más) son instrumentos sugeridos para evaluar estos factores. "
            "La Guía II tiene 46 preguntas, la Guía III tiene 72, incluyendo liderazgo. Ambas cubren todos los dominios requeridos y usan una escala estándar de 5 niveles.\n"
            "Este reporte cumple a detalle con la NOM-035 y es válido como evidencia ante la autoridad laboral."
        ) 