# /home/amigro/app/nlp.py

import logging
import spacy
from spacy.matcher import Matcher
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import skillner
from app.catalogs import DIVISION_SKILLS

logger = logging.getLogger(__name__)

# Inicializar SkillNer con el modelo base de spaCy
sn = skillner.SkillNER(model="es_core_news_sm")  # Asegúrate de tener el modelo de spaCy en español

# Añadir habilidades personalizadas
for division, skills in DIVISION_SKILLS.items():
    for skill in skills:
        sn.add_skill(skill, division=division)

class NLPProcessor:
    def __init__(self):
        try:
            # Carga el modelo de spaCy en español
            self.nlp = spacy.load("es_core_news_sm")
        except Exception as e:
            logger.error(f"Error cargando modelo spaCy: {e}", exc_info=True)
            raise e

        # Inicializar Matcher
        self.matcher = Matcher(self.nlp.vocab)
        self.define_intent_patterns()

        # Inicializar analizador de sentimiento
        nltk.download('vader_lexicon', quiet=True)
        self.sia = SentimentIntensityAnalyzer()

    def define_intent_patterns(self):
        """
        Define patrones de intenciones usando el Matcher de spaCy.
        Cada patrón es una lista de diccionarios con condiciones sobre los tokens.
        """

        # Ejemplo de patrones por intención
        # Nota: Usamos LOWER para detectar en minúsculas.
        # Puedes agregar más palabras clave según necesites.

        # Saludo
        saludo_patterns = [[{"LOWER": {"IN": ["hola", "buenos días", "buenas tardes", "buenas noches"]}}]]
        self.matcher.add("saludo", saludo_patterns)

        # Despedida
        despedida_patterns = [[{"LOWER": {"IN": ["adiós", "hasta luego", "nos vemos", "chao", "ciao"]}}]]
        self.matcher.add("despedida", despedida_patterns)

        # Iniciar conversacion
        iniciar_conversacion_patterns = [[{"LOWER": {"IN": ["reiniciar", "reset", "empezar", "empezar de nuevo"]}}]]
        self.matcher.add("iniciar_conversacion", iniciar_conversacion_patterns)

        # Menu
        menu_patterns = [[{"LOWER": {"IN": ["menu", "menú", "main", "menú principal"]}}]]
        self.matcher.add("menu", menu_patterns)

        # Consultar estatus
        # Podríamos buscar palabras clave como "estatus", "estado", "aplicación"
        consultar_estatus_patterns = [
            [{"LEMMA": "consultar"}, {"LOWER": {"IN": ["estatus", "estado"]}}, {"LOWER": {"IN": ["aplicación", "aplicacion"]}}]
        ]
        self.matcher.add("consultar_estatus", consultar_estatus_patterns)

        # Solicitar ayuda postulación
        # Buscar frases como "ayuda con la postulación", "asistencia para postular"
        solicitar_ayuda_postulacion_patterns = [
            [{"LEMMA": {"IN": ["necesitar", "ayuda", "asistencia"]}}, {"LOWER": {"IN": ["postular", "postulación", "aplicar"]}}]
        ]
        self.matcher.add("solicitar_ayuda_postulacion", solicitar_ayuda_postulacion_patterns)

        # Travel in group (amigro)
        travel_in_group_patterns = [
            [{"LOWER": {"IN": ["viajando", "caravana", "grupo", "familia"]}}, {"LOWER": {"IN": ["grupo", "familia", "migrantes"]}}]
        ]
        self.matcher.add("travel_in_group", travel_in_group_patterns)

        # Ver vacantes
        ver_vacantes_patterns = [
            [{"LOWER": {"IN": ["ver", "mostrar", "necesito"]}}, {"LOWER": {"IN": ["vacantes", "empleos", "oportunidades"]}}]
        ]
        self.matcher.add("ver_vacantes", ver_vacantes_patterns)

        # Negacion (ej para el caso de invitaciones)
        negacion_patterns = [[{"LOWER": {"IN": ["no", "no gracias"]}}]]
        self.matcher.add("negacion", negacion_patterns)

        # Agradecimiento
        agradecimiento_patterns = [[{"LOWER": {"IN": ["gracias", "te agradezco", "muy amable"]}}]]
        self.matcher.add("agradecimiento", agradecimiento_patterns)

        # Impacto social (huntU)
        impacto_social_patterns = [
            [{"LOWER": {"IN": ["impacto", "social", "propósito", "proposito"]}}, {"LOWER": {"IN": ["trabajo", "empleo"]}}]
        ]
        self.matcher.add("busqueda_impacto", impacto_social_patterns)

        # Solicitar información de la empresa
        solicitar_informacion_empresa_patterns = [
            [{"LOWER": "información"}, {"LOWER": "empresa"}],
            [{"LOWER": "háblame"}, {"LOWER": "empresa"}]
        ]
        self.matcher.add("solicitar_informacion_empresa", solicitar_informacion_empresa_patterns)

        # Solicitar tips entrevista
        tips_entrevista_patterns = [
            [{"LOWER": {"IN": ["consejos", "tips"]}}, {"LOWER": {"IN": ["entrevista", "entrevistas"]}}]
        ]
        self.matcher.add("solicitar_tips_entrevista", tips_entrevista_patterns)
        
        # Consultar sueldo de mercado
        consultar_sueldo_patterns = [
            [{"LOWER": {"IN": ["rango", "salario", "promedio"]}}, {"LOWER": {"IN": ["mercado", "mercado laboral"]}}]
        ]
        self.matcher.add("consultar_sueldo_mercado", consultar_sueldo_patterns)

        # Actualizar perfil
        actualizar_perfil_patterns = [
            [{"LOWER": {"IN": ["actualizar", "cambiar"]}}, {"LOWER": {"IN": ["perfil", "datos"]}}]
        ]
        self.matcher.add("actualizar_perfil", actualizar_perfil_patterns)

    def analyze(self, text: str) -> dict:
        """
        Procesa el texto: detecta intenciones, entidades y sentimiento.
        Retorna un dict con "intents", "entities", "sentiment".
        """
        doc = self.nlp(text.lower())

        # Detectar Intents con Matcher
        matches = self.matcher(doc)
        detected_intents = []
        for match_id, start, end in matches:
            intent = self.nlp.vocab.strings[match_id]
            if intent not in detected_intents:
                detected_intents.append(intent)

        # Extraer entidades nombradas
        entities = [(ent.text, ent.label_) for ent in doc.ents]

        # Analizar sentimiento (con NLTK VADER)
        sentiment = self.sia.polarity_scores(text)

        return {
            "intents": detected_intents,
            "entities": entities,
            "sentiment": sentiment
        }
    
    def infer_gender(self, name: str) -> str:
        """
        Infiera el género basado en el nombre.
        """
        GENDER_DICT = {"jose": "M", "maria": "F", "andrea": "O"}  # Ejemplo
        gender_count = {"M": 0, "F": 0}
        for part in name.lower().split():
            gender_count[GENDER_DICT.get(part, "O")] += 1
        return "M" if gender_count["M"] > gender_count["F"] else "F" if gender_count["F"] > gender_count["M"] else "O"