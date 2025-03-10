# 📌 Ubicación en servidor: /home/pablo/app/chatbot/nlp.py

# /home/pablo/app/chatbot/nlp.py

import spacy
import logging
import os
import json
from transformers import pipeline, AutoModelForTokenClassification, AutoTokenizer
from cachetools import TTLCache, cachedmethod

import requests
import shutil

logger = logging.getLogger(__name__)

CONFIG = {
    "DATA_DIR": "/home/pablo/skills_data/",
    "COMBINED_SKILLS_PATH": "/home/pablo/skills_data/combined_skills.json"
}

MODEL_LANGUAGES = {
    "es": "es_core_news_md",
    "en": "en_core_web_md",
}

class NLPProcessor:
    def __init__(self, language='es'):
        self.language = language
        self.ensure_data_dir()
        self.nlp = spacy.load(MODEL_LANGUAGES.get(language, 'es_core_news_md'))
        self.skillner_pipeline = self.load_or_download_model("ihk/skillner")
        self.linkedin_pipeline = self.load_or_download_model("algiraldohe/lm-ner-linkedin-skills-recognition")
        self.skill_cache = TTLCache(maxsize=5000, ttl=7200)

    def ensure_data_dir(self):
        if not os.path.exists(CONFIG["DATA_DIR"]):
            os.makedirs(CONFIG["DATA_DIR"])
            logger.info(f"Directorio creado: {CONFIG['DATA_DIR']}")

    def load_or_download_model(self, model_name):
        local_path = os.path.join(CONFIG["DATA_DIR"], model_name.replace("/", "_"))
        if not os.path.exists(local_path):
            logger.info(f"Descargando modelo {model_name}...")
            model = AutoModelForTokenClassification.from_pretrained(model_name)
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model.save_pretrained(local_path)
            tokenizer.save_pretrained(local_path)
        else:
            logger.info(f"Modelo {model_name} ya descargado.")
        return pipeline('ner', model=local_path, aggregation_strategy='simple')

    @cachedmethod(lambda self: self.skill_cache)
    def extract_skills(self, text: str):
        from app.chatbot.utils import clean_text
        text = clean_text(text)
        skills = set()

        # Pipeline SkillNER
        entities_skillner = self.skillner_pipeline(text)
        for ent in entities_skillner:
            if ent['entity_group'].upper() == 'SKILL':
                skills.add(ent['word'].lower())

        # Pipeline LinkedIn
        entities_linkedin = self.linkedin_pipeline(text)
        for ent in entities_linkedin:
            if ent['entity_group'].upper() == 'SKILL':
                skills.add(ent['word'].lower())

        return {"skills": list(skills)}

    def analyze(self, text: str):
        skills = self.extract_skills(text)['skills']
        sentiment = self.get_sentiment(text)
        job_classification = self.classify_job(text)

        return {
            "skills": skills,
            "sentiment": sentiment,
            "job_classification": job_classification
        }

    def get_sentiment(self, text):
        sentiment_pipeline = pipeline(
            'sentiment-analysis', 
            model='cardiffnlp/twitter-roberta-base-sentiment-latest',
            aggregation_strategy='simple'
        )
        result = sentiment_pipeline(text)
        return result[0]['label'] if result else "neutral"

    def classify_job(self, text: str):
        tabiya_classifier = TabiyaJobClassifier()
        return tabiya_classifier.classify(text)


class TabiyaJobClassifier:
    def __init__(self):
        from tabiya_livelihoods_classifier.inference.linker import EntityLinker
        self.linker = EntityLinker()

    def classify(self, text):
        return self.linker.link_text(text)

class RoBertASentimentAnalyzer:
    def __init__(self, model_name="cardiffnlp/twitter-roberta-base-sentiment-latest"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)

    def analyze_sentiment(self, text):
        """Analiza el sentimiento del texto."""
        inputs = self.tokenizer(text, return_tensors="pt")
        with torch.no_grad():
            outputs = self.model(**inputs)
            predicted_class = torch.argmax(outputs.logits, dim=1).item()
        return ["negative", "neutral", "positive"][predicted_class]
    