import spacy
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Optional
import logging
from app.models import Person, Vacante, BusinessUnit

logger = logging.getLogger(__name__)

class NLPProcessor:
    def __init__(self, language: str = "es", mode: str = "opportunity", analysis_depth: str = "deep"):
        """
        Inicializa el procesador de NLP.
        
        Args:
            language: Idioma para el procesamiento ("es" o "en")
            mode: Modo de procesamiento ("opportunity" o "candidate")
            analysis_depth: Profundidad del análisis ("quick" o "deep")
        """
        self.language = language
        self.mode = mode
        self.analysis_depth = analysis_depth
        self.nlp = None
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self._initialize_nlp()
        self._initialize_models()

    def _initialize_models(self):
        """Inicializa modelos adicionales para análisis profundo."""
        if self.mode == "opportunity":
            self.job_classifier = JobClassifier()
            self.salary_estimator = SalaryEstimator()
        else:  # candidate
            self.education_extractor = EducationExtractor()
            self.experience_analyzer = ExperienceAnalyzer()

    async def analyze(self, text: str) -> Dict:
        """
        Analiza un texto y devuelve información relevante.
        
        Args:
            text: Texto a analizar
            
        Returns:
            Dict con el análisis realizado
        """
        try:
            doc = self.nlp(text)
            
            result = {
                "entities": self._extract_entities(doc),
                "sentiment": self._analyze_sentiment(text),
                "keywords": self._extract_keywords(text),
                "skills": await self._extract_skills(doc)
            }
            
            if self.analysis_depth == "deep":
                if self.mode == "opportunity":
                    result.update({
                        "job_classification": await self.job_classifier.classify(text),
                        "salary_estimate": await self.salary_estimator.estimate(text),
                        "requirements": await self._extract_requirements(doc)
                    })
                else:  # candidate
                    result.update({
                        "education": await self.education_extractor.extract(text),
                        "experience": await self.experience_analyzer.analyze(text),
                        "achievements": await self._extract_achievements(doc)
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"Error en análisis NLP: {str(e)}")
            return {
                "entities": [],
                "sentiment": {},
                "keywords": [],
                "skills": []
            }

    def _initialize_nlp(self):
        """Inicializa el modelo de spaCy."""
        try:
            if self.language == "es":
                self.nlp = spacy.load("es_core_news_sm")
            else:
                self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning(f"Modelo spaCy no encontrado para {self.language}")
            import sys
            if self.language == "es":
                sys.exit("Por favor, instala el modelo spaCy: python -m spacy download es_core_news_sm")
            else:
                sys.exit("Por favor, instala el modelo spaCy: python -m spacy download en_core_web_sm")

    async def analyze(self, text: str) -> Dict:
        """
        Analiza un texto y devuelve información relevante.
        
        Args:
            text: Texto a analizar
            
        Returns:
            Dict con el análisis realizado
        """
        try:
            doc = self.nlp(text)
            
            result = {
                "entities": self._extract_entities(doc),
                "sentiment": self._analyze_sentiment(text),
                "keywords": self._extract_keywords(text),
                "skills": self._extract_skills(doc)
            }
            
            if self.analysis_depth == "deep":
                result.update({
                    "intent": self._determine_intent(text),
                    "context": self._extract_context(doc)
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error en análisis NLP: {str(e)}")
            return {
                "entities": [],
                "sentiment": {},
                "keywords": [],
                "skills": []
            }

    def _extract_entities(self, doc) -> List[Dict]:
        """Extrae entidades nombradas del documento."""
        entities = []
        for ent in doc.ents:
            entities.append({
                "text": ent.text,
                "label": ent.label_,
                "confidence": 0.9  # Simulación de confianza
            })
        return entities

    def _analyze_sentiment(self, text: str) -> Dict:
        """Analiza el sentimiento del texto."""
        # Implementación básica de sentimiento
        positive_words = ["excelente", "bueno", "satisfactorio", "positivo"]
        negative_words = ["pobre", "malo", "insatisfactorio", "negativo"]
        
        words = text.lower().split()
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        return {
            "score": (positive_count - negative_count) / len(words) if words else 0,
            "magnitude": abs(positive_count - negative_count)
        }

    def _extract_keywords(self, text: str) -> List[str]:
        """Extrae palabras clave usando TF-IDF."""
        try:
            tfidf_matrix = self.vectorizer.fit_transform([text])
            feature_names = self.vectorizer.get_feature_names_out()
            
            keywords = []
            for i in tfidf_matrix.nonzero()[0]:
                keywords.append(feature_names[i])
            
            return keywords[:5]  # Top 5 keywords
            
        except Exception as e:
            logger.error(f"Error extrayendo keywords: {str(e)}")
            return []

    async def _extract_skills(self, doc) -> List[str]:
        """Extrae habilidades del documento usando múltiples fuentes."""
        skills = []
        for token in doc:
            if token.pos_ in ["NOUN", "ADJ"] and len(token.text) > 2:
                skills.append(token.text.lower())
        
        # Mejorar la detección de habilidades usando patrones
        skill_patterns = [
            r"\b(?:python|java|sql|javascript|typescript|c\+\+|c#|ruby|php|go|rust|swift)\b",
            r"\b(?:machine\slearning|deep\slearning|ai|artificial\sintelligence)\b",
            r"\b(?:cloud|aws|azure|gcp|docker|kubernetes)\b",
            r"\b(?:devops|ci/cd|testing|qa)\b"
        ]
        
        for pattern in skill_patterns:
            matches = re.findall(pattern, text.lower())
            skills.extend(matches)
        
        return list(set(skills))

    def _determine_intent(self, text: str) -> str:
        """Determina el intent del mensaje."""
        # Implementación básica de intents
        greetings = ["hola", "buenos días", "buenas tardes"]
        farewells = ["adiós", "hasta luego", "chau"]
        
        words = text.lower().split()
        
        if any(word in greetings for word in words):
            return "greeting"
        elif any(word in farewells for word in words):
            return "farewell"
        return "default"

    def _extract_context(self, doc) -> Dict:
        """Extrae contexto del documento."""
        context = {}
        for token in doc:
            if token.dep_ == "nsubj":
                context["subject"] = token.text
            elif token.dep_ == "dobj":
                context["object"] = token.text
        return context

    async def compare_texts(self, text1: str, text2: str) -> float:
        """
        Compara dos textos usando similitud del coseno.
        
        Args:
            text1: Primer texto
            text2: Segundo texto
            
        Returns:
            float: Puntaje de similitud (0-1)
        """
        try:
            tfidf_matrix = self.vectorizer.fit_transform([text1, text2])
            return cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        except Exception as e:
            logger.error(f"Error comparando textos: {str(e)}")
            return 0.0

    async def extract_job_requirements(self, job_description: str) -> Dict:
        """
        Extrae requisitos de una descripción de trabajo.
        
        Args:
            job_description: Descripción del trabajo
            
        Returns:
            Dict con requisitos extraídos
        """
        try:
            doc = self.nlp(job_description)
            
            requirements = {
                "skills": [],
                "experience": [],
                "education": [],
                "certifications": []
            }
            
            for token in doc:
                if token.pos_ == "NOUN" and token.text.lower() in ["python", "java", "sql"]:
                    requirements["skills"].append(token.text)
                elif token.text.lower() in ["años", "experiencia"]:
                    requirements["experience"].append(token.text)
                elif token.text.lower() in ["licenciatura", "maestría"]:
                    requirements["education"].append(token.text)
                elif token.text.lower() in ["certificado", "certificación"]:
                    requirements["certifications"].append(token.text)
            
            return requirements
            
        except Exception as e:
            logger.error(f"Error extrayendo requisitos: {str(e)}")
            return {
                "skills": [],
                "experience": [],
                "education": [],
                "certifications": []
            }

    async def analyze_candidate_profile(self, profile: Dict) -> Dict:
        """
        Analiza un perfil de candidato.
        
        Args:
            profile: Perfil del candidato
            
        Returns:
            Dict con análisis del perfil
        """
        try:
            skills_text = " ".join(profile.get("skills", []))
            experience_text = profile.get("experience", "")
            
            analysis = {
                "skills_analysis": await self.analyze(skills_text),
                "experience_analysis": await self.analyze(experience_text),
                "match_score": 0.0
            }
            
            if profile.get("vacancy"):
                vacancy_analysis = await self.analyze(profile["vacancy"])
                analysis["match_score"] = await self.compare_texts(
                    skills_text, 
                    profile["vacancy"]
                )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analizando perfil: {str(e)}")
            return {
                "skills_analysis": {},
                "experience_analysis": {},
                "match_score": 0.0
            }

    async def generate_response(self, text: str, context: Dict) -> str:
        """
        Genera una respuesta basada en el texto y contexto.
        
        Args:
            text: Texto del mensaje
            context: Contexto de la conversación
            
        Returns:
            str: Respuesta generada
        """
        try:
            analysis = await self.analyze(text)
            intent = analysis["intent"]
            
            if intent == "greeting":
                return "¡Hola! ¿Cómo estás? ¿En qué puedo ayudarte?"
            elif intent == "farewell":
                return "¡Adiós! ¡Que tengas un buen día!"
            
            # Respuesta por defecto
            return "No entendí bien, pero parece que dijiste \"{}\". ¿En qué más puedo ayudarte?".format(text)
            
        except Exception as e:
            logger.error(f"Error generando respuesta: {str(e)}")
            return "Lo siento, hubo un error al procesar tu mensaje. ¿Podrías reformularlo?"

    async def update_context(self, context: Dict, new_data: Dict) -> Dict:
        """
        Actualiza el contexto de la conversación.
        
        Args:
            context: Contexto actual
            new_data: Nuevos datos a agregar
            
        Returns:
            Dict: Contexto actualizado
        """
        try:
            # Implementación básica de actualización de contexto
            updated_context = context.copy()
            updated_context.update(new_data)
            return updated_context
            
        except Exception as e:
            logger.error(f"Error actualizando contexto: {str(e)}")
            return context

    async def validate_response(self, response: str, context: Dict) -> bool:
        """
        Valida si una respuesta es apropiada para el contexto.
        
        Args:
            response: Respuesta a validar
            context: Contexto de la conversación
            
        Returns:
            bool: True si la respuesta es válida, False en caso contrario
        """
        try:
            # Implementación básica de validación
            if "error" in response.lower():
                return False
            if len(response) < 5:  # Respuesta demasiado corta
                return False
            return True
            
        except Exception as e:
            logger.error(f"Error validando respuesta: {str(e)}")
            return False

    async def process_message(self, message: str, context: Dict) -> Dict:
        """
        Procesa un mensaje completo.
        
        Args:
            message: Mensaje del usuario
            context: Contexto de la conversación
            
        Returns:
            Dict con el resultado del procesamiento
        """
        try:
            analysis = await self.analyze(message)
            
            # Actualizar contexto
            context = await self.update_context(context, {
                "last_message": message,
                "last_analysis": analysis
            })
            
            # Generar respuesta
            response = await self.generate_response(message, context)
            
            # Validar respuesta
            if not await self.validate_response(response, context):
                response = "Lo siento, no pude procesar tu mensaje. ¿Podrías reformularlo?"
            
            return {
                "analysis": analysis,
                "response": response,
                "context": context
            }
            
        except Exception as e:
            logger.error(f"Error procesando mensaje: {str(e)}")
            return {
                "analysis": {},
                "response": "Lo siento, hubo un error al procesar tu mensaje.",
                "context": context
            }
