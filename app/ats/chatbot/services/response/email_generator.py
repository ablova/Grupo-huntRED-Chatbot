import openai
from app.ats.chatbot.services.data_enrichment import DataEnrichmentService
from app.models import Company, BusinessUnit
import json

class EmailGenerator:
    def __init__(self, company_id):
        self.enrichment_service = DataEnrichmentService()
        self.company_id = company_id

    def generate_email(self):
        """Genera un correo personalizado usando múltiples fuentes de datos"""
        enriched_data = self.enrichment_service.enrich_company_data(self.company_id)
        prompt = self._generate_prompt(enriched_data)
        email_content = self._process_with_gpt(prompt)
        
        return {
            'subject': self._generate_subject(enriched_data),
            'body': email_content,
            'metadata': {
                'company': enriched_data['company']['name'],
                'bu_relevant': self._identify_relevant_bu(enriched_data),
                'action_items': self._generate_action_items(enriched_data)
            }
        }

    def _generate_prompt(self, enriched_data):
        """Genera prompt para GPT usando datos enriquecidos"""
        data_json = json.dumps(enriched_data, indent=2)
        
        prompt = f"""
        Basado en los siguientes datos de la empresa:
        {data_json}

        Genera un correo electrónico profesional y personalizado que:
        1. Analice la situación actual de la empresa
        2. Identifique las necesidades específicas
        3. Presente las soluciones de Grupo huntRED® adaptadas a sus necesidades:
           - huntRED® Executive (C-level/Board)
           - huntRED® (Middle/Top Management)
           - huntU® (Undergraduates/Graduates)
           - Amigro® (Migrant Opportunities)
        4. Incluya una llamada a acción específica
        """
        return prompt

    def _process_with_gpt(self, prompt):
        """Procesa el prompt con GPT"""
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres un experto en redacción de propuestas de Grupo huntRED®"},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content

    def _generate_subject(self, data):
        """Genera el asunto del correo"""
        return f"[huntRED®] Solución Especializada para {data['company']['name']}"

    def _identify_relevant_bu(self, data):
        """Identifica las unidades de negocio relevantes"""
        relevant_bu = []
        company_size = data['company']['size']
        company_industry = data['company']['industry']
        
        if company_size == '501+':
            relevant_bu.append('huntRED® Executive')
        if company_size in ['100-500', '501+']:
            relevant_bu.append('huntRED®')
        if company_industry in ['Technology', 'Finance']:
            relevant_bu.append('huntU®')
        if company_industry in ['Manufacturing', 'Retail']:
            relevant_bu.append('Amigro®')
        
        return relevant_bu

    def _generate_action_items(self, data):
        """Genera acciones específicas basadas en el análisis"""
        actions = []
        if data['company']['integration_data']['linkedin']:
            actions.append("Programar reunión inicial")
        if data['company']['integration_data']['chatbot']:
            actions.append("Enviar caso de éxito relevante")
        return actions
