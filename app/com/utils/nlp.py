# /home/pablo/app/com/utils/nlp.py
import spacy
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Optional, Any, Union
import logging
import time
import functools
from django.core.cache import cache

from app.models import Person, Vacante, BusinessUnit

logger = logging.getLogger(__name__)

from app.com.utils.skills import create_skill_processor
from app.com.utils.skills.base import Skill, Competency

# Intenta importar psutil para monitoreo de recursos (opcional)
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    
# Caché global para modelos de spaCy para evitar carga repetida
SPACY_MODELS = {}

# Caché para embeddings y análisis
EMBEDDING_CACHE_TTL = 3600  # 1 hora
ANALYSIS_CACHE_TTL = 300    # 5 minutos

class NLPProcessor:
    def __init__(self, business_unit: BusinessUnit, language: str = "es", mode: str = "opportunity", analysis_depth: str = "deep"):
        """
        Inicializa el procesador de NLP híbrido (Spacy + Tabiya + SkillClassifier).
        
        Args:
            business_unit: Unidad de negocio para el análisis
            language: Idioma para el procesamiento ("es" o "en")
            mode: Modo de procesamiento ("opportunity" o "candidate")
            analysis_depth: Profundidad del análisis ("quick" o "deep")
        """
        self.business_unit = business_unit
        self.language = language
        self.mode = mode
        self.analysis_depth = analysis_depth
        
        # Inicializar procesadores
        self.spacy_model = self._load_spacy_model()
        self.skill_processor = create_skill_processor(
            business_unit.name,
            language=language,
            mode='executive' if business_unit.name == 'huntRED Executive' else 'technical'
        )
        
    async def analyze(self, text: str) -> Dict:
        """
        Analiza un texto usando el procesador de habilidades.
        
        Args:
            text: Texto a analizar
            
        Returns:
            Dict con el análisis realizado
        """
        if not text or len(text.strip()) == 0:
            return {
                "skills": [],
                "competencies": [],
                "skill_analysis": {},
                "competency_analysis": {},
                "mode": self.mode,
                "business_unit": self.business_unit.name,
                "cached": False
            }
            
        # Verificar caché
        cache_key = f"nlp:skills:{self.business_unit.id}:{self.mode}:{self.analysis_depth}:{hash(text[:200])}"
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.debug(f"Resultado obtenido de caché para BU '{self.business_unit.name}'")
            cached_result["cached"] = True
            return cached_result
            
        # Medir tiempo de ejecución
        start_time = time.time()
        
        try:
            # Extraer habilidades
            skills = await self._extract_skills(text)
            
            # Clasificar habilidades
            competencies = await self._classify_skills(skills)
            
            # Analizar habilidades y competencias
            analysis = await self.skill_processor.analyze_skills(skills)
            competency_analysis = await self.skill_processor.analyze_competencies(competencies)
            
            # Crear resultado
            result = {
                "skills": [skill.to_dict() for skill in skills],
                "competencies": [comp.to_dict() for comp in competencies],
                "skill_analysis": analysis,
                "competency_analysis": competency_analysis,
                "mode": self.mode,
                "business_unit": self.business_unit.name,
                "execution_time": time.time() - start_time,
                "cached": False
            }
            
            # Guardar en caché
            cache.set(cache_key, result, ANALYSIS_CACHE_TTL)
            
            return result
            
        except Exception as e:
            logger.error(f"Error en análisis de habilidades: {str(e)}")
            return {
                "skills": [],
                "competencies": [],
                "skill_analysis": {},
                "competency_analysis": {},
                "mode": self.mode,
                "business_unit": self.business_unit.name,
                "execution_time": time.time() - start_time,
                "error": str(e),
                "cached": False
            }
            
    async def _extract_skills(self, text: str) -> List[Skill]:
        """Extrae habilidades del texto usando el procesador apropiado."""
        if self.analysis_depth == "quick":
            extractor = SpacySkillExtractor(self.business_unit.name, self.language)
        else:
            extractor = TabiyaSkillExtractor(self.business_unit.name, self.language)
            
        return await extractor.extract_skills(text)
            
    async def _classify_skills(self, skills: List[Skill]) -> List[Competency]:
        """Clasifica habilidades en competencias."""
        if self.business_unit.name == 'huntRED Executive':
            classifier = ExecutiveSkillClassifier(self.business_unit.name)
        else:
            classifier = BaseSkillClassifier(self.business_unit.name)
            
        return await classifier.classify_skills(skills)
        
    def _load_spacy_model(self):
        """Carga el modelo de Spacy según el idioma, con caché global y monitoreo de recursos."""
        model_name = "es_core_news_md" if self.language == "es" else "en_core_web_md"
        
        # Verificar si ya está en caché global
        if model_name in SPACY_MODELS:
            logger.debug(f"Usando modelo {model_name} desde caché global")
            return SPACY_MODELS[model_name]
        
        # Monitorear recursos disponibles
        should_use_light_model = False
        if PSUTIL_AVAILABLE:
            # Si queda poca RAM disponible, usar modelo ligero
            mem = psutil.virtual_memory()
            if mem.available < 500 * 1024 * 1024:  # Menos de 500MB disponibles
                should_use_light_model = True
                logger.warning(f"Memoria baja ({mem.available/1024/1024:.1f}MB), usando modelo ligero")
        
        # Cambiar a modelo ligero si es necesario
        if should_use_light_model:
            model_name = model_name.replace("_md", "_sm")
        
        # Cargar modelo con componentes selectivos
        disabled_components = ["ner"] if self.analysis_depth == "quick" else []
        model = spacy.load(model_name, disable=disabled_components)
        
        # Guardar en caché global
        SPACY_MODELS[model_name] = model
        logger.info(f"Modelo {model_name} cargado y almacenado en caché global")
        
        return model
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
        Analiza un texto usando el procesador más apropiado según la profundidad.
        
        Args:
            text: Texto a analizar
            
        Returns:
            Dict con el análisis realizado
        """
        try:
            if self.analysis_depth == "quick":
                # Usar Spacy para análisis rápido
                return await self._analyze_with_spacy(text)
            else:
                # Usar Tabiya para análisis profundo
                return await self._analyze_with_tabiya(text)
                
        except Exception as e:
            logger.error(f"Error en análisis NLP: {str(e)}")
            return {
                "entities": [],
                "sentiment": {},
                "keywords": [],
                "skills": [],
                "experience": {},
                "culture": {},
                "requirements": [],
                "benefits": [],
                "education": [],
                "achievements": []
            }
            
    async def _analyze_with_spacy(self, text: str) -> Dict:
        """Analiza usando Spacy para análisis rápido."""
        try:
            doc = self.spacy_model(text)
            
            return {
                "entities": self._extract_entities(doc),
                "sentiment": self._analyze_sentiment(doc),
                "keywords": self._extract_keywords(doc),
                "skills": self._extract_skills(doc)
            }
            
        except Exception as e:
            logger.error(f"Error en análisis con Spacy: {str(e)}")
            return {
                "entities": [],
                "sentiment": {},
                "keywords": [],
                "skills": []
            }
            
    async def _analyze_with_tabiya(self, text: str) -> Dict:
        """Analiza usando Tabiya para análisis profundo."""
        try:
            # Usar Tabiya para análisis profundo
            result = await self.tabiya.analyze(text)
            
            # Añadir análisis adicionales
            if self.mode == "opportunity":
                result.update({
                    "requirements": await self._extract_requirements(text),
                    "benefits": await self._extract_benefits(text)
                })
            else:  # candidate
                result.update({
                    "education": await self._extract_education(text),
                    "achievements": await self._extract_achievements(text)
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error en análisis con Tabiya: {str(e)}")
            # Si falla Tabiya, caer a Spacy
            return await self._analyze_with_spacy(text)

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

    async def _extract_requirements(self, text: str) -> List[Dict]:
        """Extrae requisitos específicos del texto."""
        # Implementación específica para requisitos
        return []
        
    async def _extract_benefits(self, text: str) -> List[Dict]:
        """Extrae beneficios específicos del texto."""
        # Implementación específica para beneficios
        return []
        
    async def _extract_education(self, text: str) -> List[Dict]:
        """Extrae información de educación del texto."""
        # Implementación específica para educación
        return []
        
    async def _extract_achievements(self, text: str) -> List[Dict]:
        """Extrae logros y logros específicos del texto."""
        # Implementación específica para logros
        return []

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
        if not text1 or not text2:
            return 0.0
            
        # Verificar caché
        cache_key = f"nlp:similarity:{self.business_unit.id}:{hash(text1[:100])}:{hash(text2[:100])}"
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result
            
        try:
            if not self.spacy_model:
                self.spacy_model = self._load_spacy_model()
            
            # Usar versiones truncadas si son muy largas para ahorrar memoria
            if len(text1) > 5000 or len(text2) > 5000:
                text1 = text1[:5000]
                text2 = text2[:5000]
                logger.debug("Textos truncados para comparación (>5000 caracteres)")
                
            # Procesar textos
            doc1 = self.spacy_model(text1)
            doc2 = self.spacy_model(text2)
            
            # Calcular similitud
            similarity = doc1.similarity(doc2)
            
            # Guardar en caché
            cache.set(cache_key, similarity, EMBEDDING_CACHE_TTL)
            
            return similarity
        except Exception as e:
            logger.error(f"Error en comparación de textos: {str(e)}")
            return 0.0

    async def extract_job_requirements(self, job_description: str) -> Dict:
        """
        Extrae requisitos de una descripción de trabajo.
{{ ... }}
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
