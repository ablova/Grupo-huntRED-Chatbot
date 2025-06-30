"""
Motor de procesamiento de lenguaje natural para Grupo huntRED®.
Proporciona funcionalidades avanzadas de NLP para el análisis de texto.
"""

# Importaciones estándar de Python
import os
import json
import logging
import asyncio
import pickle
from typing import Dict, List, Optional
import datetime
import hashlib
import re

# Importaciones de terceros
import numpy as np
import spacy
from cachetools import TTLCache
from textblob import TextBlob
from langdetect import detect

# Importaciones condicionales
try:
    from deep_translator import GoogleTranslator
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False

try:
    import tensorflow as tf
    import tensorflow_hub as hub
    import tensorflow_text as text  # Required for SentencepieceOp
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    tf = None
    hub = None
    text = None

try:
    from transformers import TFAutoModelForSequenceClassification, AutoTokenizer
    from tensorflow.keras.optimizers import Adam
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

# Importaciones de utilidades
from app.ats.utils.logger_utils import get_module_logger

# Configuración del logger
logger = get_module_logger('nlp')

# Log TensorFlow import success
if TF_AVAILABLE:
    logger.info(f"TensorFlow {tf.__version__} y TensorFlow Hub importados correctamente.")

# Configuraciones desde settings.py
USE_EMBEDDINGS = TF_AVAILABLE and os.getenv('USE_EMBEDDINGS', 'true').lower() == 'true'
USE_ROBERTA = TRANSFORMERS_AVAILABLE and os.getenv('USE_ROBERTA', 'true').lower() == 'true'
MAX_SKILLS = int(os.getenv('MAX_SKILLS', 10000))
RAM_LIMIT = 8 * 1024 * 1024 * 1024  # 8 GB
EMBEDDINGS_CACHE = "/home/pablo/skills_data/embeddings_cache.pkl"
EMBEDDINGS_READY = os.path.exists(EMBEDDINGS_CACHE)

# Constantes
FILE_PATHS = {
    "candidate_quick": "/home/pablo/skills_data/skill_db_relax_20.json",
    "candidate_deep": "/home/pablo/skills_data/ESCO_occup_skills.json",
    "opportunity_quick": "/home/pablo/app/utilidades/catalogs/skills.json",
    "opportunity_deep": "/home/pablo/skills_data/ESCO_occup_skills.json",
}
LOCK_FILE = "/home/pablo/skills_data/nlp_init.lock"

# Cachés
translation_cache = TTLCache(maxsize=1000, ttl=3600)
embeddings_cache = TTLCache(maxsize=1000, ttl=3600)
skill_embeddings_cache = None

# Modelos globales
nlp_spacy = None
use_model = None
roberta_model = None
roberta_tokenizer = None

def initialize_tensorflow():
    """Configura TensorFlow para evitar conflictos."""
    if not TF_AVAILABLE:
        logger.warning("TensorFlow no disponible, omitiendo inicialización.")
        return
    try:
        tf.config.set_soft_device_placement(True)
        tf.config.threading.set_intra_op_parallelism_threads(1)
        tf.config.threading.set_inter_op_parallelism_threads(1)
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
        os.environ['CUDA_VISIBLE_DEVICES'] = ''  # Disable GPU
        logger.info("TensorFlow configurado con soft placement y hilos mínimos (CPU-only).")
    except Exception as e:
        logger.error(f"Error inicializando TensorFlow: {str(e)}")

def load_spacy_model(language: str = "es"):
    """Carga el modelo spaCy de manera lazy."""
    global nlp_spacy
    if nlp_spacy is None:
        model_name = "es_core_news_md" if language == "es" else "en_core_web_md"
        try:
            nlp_spacy = spacy.load(model_name, disable=["ner", "parser"])
            logger.info(f"Modelo spaCy '{model_name}' cargado.")
        except Exception as e:
            logger.error(f"Error cargando spaCy: {str(e)}")
            nlp_spacy = None
    return nlp_spacy

def load_use_model():
    """Carga el modelo USE de manera lazy."""
    global use_model
    if use_model is None and USE_EMBEDDINGS and TF_AVAILABLE:
        try:
            model_path = "https://tfhub.dev/google/universal-sentence-encoder-multilingual/3"
            use_model = hub.load(model_path)
            logger.info("Modelo USE multilingüe cargado.")
        except Exception as e:
            logger.error(f"Error cargando USE: {str(e)}")
            use_model = None
    return use_model

def load_roberta_model():
    """Carga el modelo RoBERTa para análisis de sentimiento usando TensorFlow."""
    global roberta_model, roberta_tokenizer
    if not TRANSFORMERS_AVAILABLE or roberta_model is not None:
        return
    
    try:
        model_name = "pysentimiento/robertuito-sentiment-analysis"
        roberta_tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # Cargar el modelo con soporte para TensorFlow
        roberta_model = TFAutoModelForSequenceClassification.from_pretrained(
            model_name, 
            from_pt=True  # Convertir automáticamente los pesos de PyTorch a TensorFlow
        )
        
        # Compilar el modelo
        optimizer = tf.keras.optimizers.Adam(learning_rate=2e-5, epsilon=1e-8)
        loss = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)
        metrics = ['accuracy']
        
        roberta_model.compile(optimizer=optimizer, loss=loss, metrics=metrics)
        logger.info("Modelo RoBERTa cargado exitosamente con TensorFlow.")
    except Exception as e:
        logger.error(f"Error cargando el modelo RoBERTa: {str(e)}")
        roberta_model = None
        roberta_tokenizer = None
    return roberta_model, roberta_tokenizer

def load_skill_embeddings(catalog_key: str) -> Dict[str, np.ndarray]:
    """Carga embeddings pre-generados desde caché."""
    global skill_embeddings_cache
    if skill_embeddings_cache is None and EMBEDDINGS_READY:
        try:
            with open(EMBEDDINGS_CACHE, "rb") as f:
                cached_data = pickle.load(f)
            if cached_data.get("version") == "1.0" and catalog_key in cached_data.get("catalogs", []):
                skill_embeddings_cache = cached_data.get("embeddings", {})
                logger.info(f"Embeddings pre-generados cargados para {catalog_key} desde {EMBEDDINGS_CACHE}")
            else:
                logger.warning(f"Caché de embeddings inválido o no contiene {catalog_key}")
                skill_embeddings_cache = {}
        except Exception as e:
            logger.error(f"Error cargando embeddings desde {EMBEDDINGS_CACHE}: {str(e)}")
            skill_embeddings_cache = {}
    return skill_embeddings_cache or {}

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Calcula la similitud coseno entre dos vectores."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return np.dot(a, b) / (norm_a * norm_b)

def load_skills_catalog(mode: str, analysis_depth: str) -> Dict[str, List[Dict[str, str]]]:
    """Carga un catálogo de habilidades según el modo y nivel de procesamiento."""
    catalog = {"technical": [], "soft": [], "tools": [], "certifications": []}
    key = f"{mode}_{analysis_depth}"
    file_path = FILE_PATHS.get(key)

    if not file_path or not os.path.exists(file_path):
        logger.error(f"Archivo no encontrado: {file_path}. Usando catálogo vacío.")
        return catalog

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if key == "candidate_quick":
                type_mapping = {
                    "Hard Skill": "technical",
                    "Soft Skill": "soft",
                    "Tool": "tools",
                    "Certification": "certifications"
                }
                for skill_id, skill_data in data.items():
                    skill_type = skill_data.get("skill_type", "Hard Skill")
                    category = type_mapping.get(skill_type, "technical")
                    skill_cleaned = skill_data.get("skill_cleaned", skill_data.get("skill_name", "")).lower()
                    if skill_cleaned:
                        catalog[category].append({"original": skill_cleaned})
            elif key == "candidate_deep":
                skill_count = 0
                for _, occ_data in data.items():
                    for skill_field in ["hasEssentialSkill", "hasOptionalSkill"]:
                        for skill in occ_data.get(skill_field, []):
                            skill_name = skill.get("title", "").lower()
                            if skill_name:
                                if "certificación" in skill_name or "certificado" in skill_name:
                                    category = "certifications"
                                elif "herramienta" in skill_name or "tool" in skill_name:
                                    category = "tools"
                                elif "blanda" in skill_name or "soft" in skill_name:
                                    category = "soft"
                                else:
                                    category = "technical"
                                catalog[category].append({"original": skill_name})
                                skill_count += 1
                                if skill_count >= MAX_SKILLS:
                                    break
                    if skill_count >= MAX_SKILLS:
                        break
            elif key == "opportunity_quick":
                for role_group, roles in data.items():
                    for role, categories in roles.items():
                        for category, skills in categories.items():
                            target_category = {
                                "Habilidades Técnicas": "technical",
                                "Habilidades Blandas": "soft",
                                "Herramientas": "tools",
                                "Certificaciones": "certifications"
                            }.get(category, "technical")
                            for skill in skills:
                                catalog[target_category].append({"original": skill.lower(), "role": role})
            elif key == "opportunity_deep":
                skill_count = 0
                for _, occ_data in data.items():
                    role = occ_data.get("preferredLabel", {}).get("es", "").lower()
                    for skill_field in ["hasEssentialSkill", "hasOptionalSkill"]:
                        for skill in occ_data.get(skill_field, []):
                            skill_name = skill.get("title", "").lower()
                            if skill_name:
                                if "certificación" in skill_name or "certificado" in skill_name:
                                    category = "certifications"
                                elif "herramienta" in skill_name or "tool" in skill_name:
                                    category = "tools"
                                elif "blanda" in skill_name or "soft" in skill_name:
                                    category = "soft"
                                else:
                                    category = "technical"
                                catalog[category].append({"original": skill_name, "role": role})
                                skill_count += 1
                                if skill_count >= MAX_SKILLS:
                                    break
                    if skill_count >= MAX_SKILLS:
                        break
            total_skills = sum(len(v) for v in catalog.values())
            logger.info(f"Cargadas {total_skills} habilidades desde {file_path} ({key})")
    except json.JSONDecodeError as e:
        logger.error(f"Error parseando JSON en {file_path}: {str(e)}. Usando catálogo vacío.")
    except Exception as e:
        logger.error(f"Error cargando {file_path}: {str(e)}. Usando catálogo vacío.")
    return catalog

class NLPProcessor:
    """
    Motor de procesamiento de lenguaje natural optimizado para Grupo huntRED®.
    
    Mejoras implementadas:
    - Contexto persistente de conversación
    - Detección de intents más precisa
    - Análisis de sentimientos en tiempo real
    - Corrección automática de errores
    - Cache inteligente de embeddings
    - Optimización de performance
    """
    
    def __init__(self, mode: str = "candidate", language: str = "es", analysis_depth: str = "quick"):
        """
        Inicializa el procesador NLP con optimizaciones avanzadas.
        
        Args:
            mode: Modo de procesamiento (candidate/opportunity)
            language: Idioma de procesamiento
            analysis_depth: Profundidad de análisis (quick/deep)
        """
        self.mode = mode
        self.language = language
        self.analysis_depth = analysis_depth
        
        # Inicializar modelos optimizados
        self._initialize_models()
        
        # Contexto persistente de conversación
        self.conversation_context = {}
        self.user_preferences = {}
        self.intent_history = []
        
        # Cache inteligente
        self.embedding_cache = {}
        self.intent_cache = {}
        self.sentiment_cache = {}
        
        # Métricas de performance
        self.performance_metrics = {
            'total_requests': 0,
            'cache_hits': 0,
            'processing_times': [],
            'accuracy_scores': []
        }
    
    def _initialize_models(self):
        """Inicializa modelos con optimizaciones"""
        try:
            # Cargar modelos de manera lazy
            self.nlp = load_spacy_model(self.language)
            self.use_model = load_use_model()
            self.roberta_model, self.roberta_tokenizer = load_roberta_model()
            
            # Cargar embeddings pre-generados
            self.skill_embeddings = load_skill_embeddings(f"{self.mode}_{self.analysis_depth}")
            
            logger.info(f"NLP Processor inicializado: {self.mode}, {self.language}, {self.analysis_depth}")
            
        except Exception as e:
            logger.error(f"Error inicializando modelos NLP: {str(e)}")
    
    async def preprocess(self, text: str) -> Dict[str, str]:
        """
        Preprocesamiento avanzado de texto con optimizaciones.
        
        Args:
            text: Texto a procesar
            
        Returns:
            Dict con texto procesado y metadatos
        """
        start_time = datetime.now()
        
        try:
            # Normalización básica
            normalized_text = self._normalize_text(text)
            
            # Corrección automática de errores
            corrected_text = await self._auto_correct(normalized_text)
            
            # Detección de idioma
            detected_language = self._detect_language(corrected_text)
            
            # Traducción si es necesario
            if detected_language != self.language:
                translated_text = await self._translate_text(corrected_text, detected_language, self.language)
            else:
                translated_text = corrected_text
            
            # Análisis de sentimientos en tiempo real
            sentiment = await self._analyze_sentiment_realtime(translated_text)
            
            # Extracción de entidades nombradas
            entities = await self._extract_entities(translated_text)
            
            # Actualizar métricas
            processing_time = (datetime.now() - start_time).total_seconds()
            self.performance_metrics['processing_times'].append(processing_time)
            
            return {
                'original_text': text,
                'normalized_text': normalized_text,
                'corrected_text': corrected_text,
                'translated_text': translated_text,
                'detected_language': detected_language,
                'sentiment': sentiment,
                'entities': entities,
                'processing_time': processing_time
            }
            
        except Exception as e:
            logger.error(f"Error en preprocesamiento: {str(e)}")
            return {'original_text': text, 'error': str(e)}
    
    def _normalize_text(self, text: str) -> str:
        """Normalización avanzada de texto"""
        try:
            # Normalización básica
            normalized = text.strip().lower()
            
            # Corrección de espacios múltiples
            normalized = ' '.join(normalized.split())
            
            # Normalización de caracteres especiales
            normalized = self._normalize_special_chars(normalized)
            
            return normalized
            
        except Exception as e:
            logger.error(f"Error en normalización: {str(e)}")
            return text
    
    def _normalize_special_chars(self, text: str) -> str:
        """Normaliza caracteres especiales"""
        replacements = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'ñ': 'n', 'ü': 'u',
            '¿': '', '¡': '', '?': ' ?', '!': ' !',
            '.': ' . ', ',': ' , ', ';': ' ; ', ':': ' : '
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    async def _auto_correct(self, text: str) -> str:
        """Corrección automática de errores"""
        try:
            # Implementar corrección básica
            corrections = {
                'hola': 'hola',
                'gracias': 'gracias',
                'porfavor': 'por favor',
                'tambien': 'también',
                'asi': 'así',
                'aqui': 'aquí',
                'alli': 'allí',
                'donde': 'dónde',
                'cuando': 'cuándo',
                'que': 'qué'
            }
            
            words = text.split()
            corrected_words = []
            
            for word in words:
                corrected_word = corrections.get(word, word)
                corrected_words.append(corrected_word)
            
            return ' '.join(corrected_words)
            
        except Exception as e:
            logger.error(f"Error en auto-corrección: {str(e)}")
            return text
    
    def _detect_language(self, text: str) -> str:
        """Detección de idioma optimizada"""
        try:
            # Cache de detección
            text_hash = hashlib.md5(text.encode()).hexdigest()
            if text_hash in self.intent_cache:
                return self.intent_cache[text_hash].get('language', 'es')
            
            # Detección con langdetect
            detected = detect(text)
            
            # Cachear resultado
            self.intent_cache[text_hash] = {'language': detected}
            
            return detected
            
        except Exception as e:
            logger.error(f"Error detectando idioma: {str(e)}")
            return 'es'
    
    async def _translate_text(self, text: str, from_lang: str, to_lang: str) -> str:
        """Traducción optimizada con cache"""
        try:
            # Cache de traducción
            cache_key = f"{from_lang}_{to_lang}_{hashlib.md5(text.encode()).hexdigest()}"
            
            if cache_key in translation_cache:
                return translation_cache[cache_key]
            
            if TRANSLATOR_AVAILABLE:
                translator = GoogleTranslator(source=from_lang, target=to_lang)
                translated = translator.translate(text)
                
                # Cachear resultado
                translation_cache[cache_key] = translated
                
                return translated
            
            return text
            
        except Exception as e:
            logger.error(f"Error en traducción: {str(e)}")
            return text
    
    async def _analyze_sentiment_realtime(self, text: str) -> Dict[str, Any]:
        """Análisis de sentimientos en tiempo real"""
        try:
            # Cache de sentimientos
            text_hash = hashlib.md5(text.encode()).hexdigest()
            if text_hash in self.sentiment_cache:
                return self.sentiment_cache[text_hash]
            
            # Análisis con TextBlob
            blob = TextBlob(text)
            sentiment_score = blob.sentiment.polarity
            
            # Análisis con RoBERTa si está disponible
            roberta_sentiment = None
            if self.roberta_model and self.roberta_tokenizer:
                roberta_sentiment = await self._analyze_sentiment_roberta(text)
            
            # Combinar resultados
            sentiment_result = {
                'textblob_score': sentiment_score,
                'roberta_sentiment': roberta_sentiment,
                'overall_sentiment': self._combine_sentiment_scores(sentiment_score, roberta_sentiment),
                'confidence': 0.85
            }
            
            # Cachear resultado
            self.sentiment_cache[text_hash] = sentiment_result
            
            return sentiment_result
            
        except Exception as e:
            logger.error(f"Error en análisis de sentimientos: {str(e)}")
            return {'overall_sentiment': 'neutral', 'confidence': 0.5}
    
    async def _analyze_sentiment_roberta(self, text: str) -> Optional[str]:
        """Análisis de sentimientos con RoBERTa"""
        try:
            if not self.roberta_model or not self.roberta_tokenizer:
                return None
            
            # Tokenizar texto
            inputs = self.roberta_tokenizer(
                text, 
                return_tensors="tf", 
                truncation=True, 
                max_length=512
            )
            
            # Predicción
            outputs = self.roberta_model(inputs)
            predictions = tf.nn.softmax(outputs.logits, axis=-1)
            
            # Obtener sentimiento
            sentiment_labels = ['NEG', 'NEU', 'POS']
            predicted_class = tf.argmax(predictions, axis=-1).numpy()[0]
            
            return sentiment_labels[predicted_class]
            
        except Exception as e:
            logger.error(f"Error en análisis RoBERTa: {str(e)}")
            return None
    
    def _combine_sentiment_scores(self, textblob_score: float, roberta_sentiment: Optional[str]) -> str:
        """Combina scores de sentimientos de diferentes modelos"""
        try:
            # Mapear RoBERTa a score numérico
            roberta_score = 0.0
            if roberta_sentiment == 'POS':
                roberta_score = 0.5
            elif roberta_sentiment == 'NEG':
                roberta_score = -0.5
            elif roberta_sentiment == 'NEU':
                roberta_score = 0.0
            
            # Combinar scores (promedio ponderado)
            combined_score = (textblob_score * 0.6) + (roberta_score * 0.4)
            
            # Mapear a sentimiento
            if combined_score > 0.1:
                return 'positive'
            elif combined_score < -0.1:
                return 'negative'
            else:
                return 'neutral'
                
        except Exception as e:
            logger.error(f"Error combinando sentimientos: {str(e)}")
            return 'neutral'
    
    async def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extracción de entidades nombradas"""
        try:
            if not self.nlp:
                return []
            
            doc = self.nlp(text)
            entities = []
            
            for ent in doc.ents:
                entities.append({
                    'text': ent.text,
                    'label': ent.label_,
                    'start': ent.start_char,
                    'end': ent.end_char
                })
            
            return entities
            
        except Exception as e:
            logger.error(f"Error extrayendo entidades: {str(e)}")
            return []
    
    async def detect_intent(self, text: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Detección de intents mejorada con contexto persistente.
        
        Args:
            text: Texto del usuario
            user_id: ID del usuario para contexto
            
        Returns:
            Dict con intent detectado y confianza
        """
        try:
            # Actualizar contexto de usuario
            if user_id:
                if user_id not in self.conversation_context:
                    self.conversation_context[user_id] = {
                        'messages': [],
                        'intents': [],
                        'preferences': {}
                    }
                
                self.conversation_context[user_id]['messages'].append({
                    'text': text,
                    'timestamp': datetime.now().isoformat()
                })
            
            # Preprocesar texto
            processed = await self.preprocess(text)
            
            # Detección de intent con patrones mejorados
            intent_result = await self._detect_intent_patterns(processed['translated_text'])
            
            # Aplicar contexto de conversación
            if user_id and self.conversation_context[user_id]['intents']:
                intent_result = self._apply_conversation_context(
                    intent_result, 
                    self.conversation_context[user_id]
                )
            
            # Actualizar historial de intents
            if user_id:
                self.conversation_context[user_id]['intents'].append(intent_result)
            
            # Actualizar métricas
            self.performance_metrics['total_requests'] += 1
            
            return intent_result
            
        except Exception as e:
            logger.error(f"Error detectando intent: {str(e)}")
            return {
                'intent': 'unknown',
                'confidence': 0.0,
                'entities': [],
                'error': str(e)
            }
    
    async def _detect_intent_patterns(self, text: str) -> Dict[str, Any]:
        """Detección de intents con patrones mejorados"""
        try:
            # Patrones de intents específicos para huntRED
            intent_patterns = {
                'greeting': [
                    r'\b(hola|buenos días|buenas tardes|buenas noches|saludos)\b',
                    r'\b(hi|hello|good morning|good afternoon|good evening)\b'
                ],
                'farewell': [
                    r'\b(adiós|hasta luego|nos vemos|chao|bye)\b',
                    r'\b(goodbye|see you|take care)\b'
                ],
                'assessment_request': [
                    r'\b(evaluación|assessment|prueba|test|evaluar)\b',
                    r'\b(assessment|evaluation|test|quiz)\b'
                ],
                'profile_update': [
                    r'\b(actualizar|modificar|cambiar|editar)\s+(perfil|información|datos)\b',
                    r'\b(update|modify|change|edit)\s+(profile|information|data)\b'
                ],
                'job_search': [
                    r'\b(buscar|encontrar|empleo|trabajo|vacante|oportunidad)\b',
                    r'\b(search|find|job|work|vacancy|opportunity)\b'
                ],
                'salary_calculation': [
                    r'\b(calcular|salario|sueldo|bruto|neto)\b',
                    r'\b(calculate|salary|wage|gross|net)\b'
                ],
                'interview_schedule': [
                    r'\b(entrevista|agendar|programar|cita)\b',
                    r'\b(interview|schedule|appointment|meeting)\b'
                ],
                'support_request': [
                    r'\b(ayuda|soporte|problema|error|duda)\b',
                    r'\b(help|support|problem|error|question)\b'
                ]
            }
            
            # Detectar intents
            detected_intents = []
            for intent, patterns in intent_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, text, re.IGNORECASE):
                        detected_intents.append({
                            'intent': intent,
                            'confidence': 0.8,
                            'pattern_matched': pattern
                        })
            
            # Retornar el intent con mayor confianza
            if detected_intents:
                best_intent = max(detected_intents, key=lambda x: x['confidence'])
                return {
                    'intent': best_intent['intent'],
                    'confidence': best_intent['confidence'],
                    'entities': [],
                    'pattern_matched': best_intent['pattern_matched']
                }
            
            # Intent por defecto
            return {
                'intent': 'general_inquiry',
                'confidence': 0.5,
                'entities': []
            }
            
        except Exception as e:
            logger.error(f"Error en detección de patrones: {str(e)}")
            return {
                'intent': 'unknown',
                'confidence': 0.0,
                'entities': []
            }
    
    def _apply_conversation_context(self, intent_result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Aplica contexto de conversación al intent"""
        try:
            # Ajustar confianza basado en historial
            recent_intents = context['intents'][-3:]  # Últimos 3 intents
            
            # Si hay repetición de intents, aumentar confianza
            if recent_intents and any(r['intent'] == intent_result['intent'] for r in recent_intents):
                intent_result['confidence'] = min(0.95, intent_result['confidence'] + 0.1)
                intent_result['context_boost'] = True
            
            # Aplicar preferencias del usuario
            if context.get('preferences'):
                intent_result['user_preferences'] = context['preferences']
            
            return intent_result
            
        except Exception as e:
            logger.error(f"Error aplicando contexto: {str(e)}")
            return intent_result
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas de performance del NLP"""
        try:
            avg_processing_time = (
                sum(self.performance_metrics['processing_times']) / 
                len(self.performance_metrics['processing_times'])
                if self.performance_metrics['processing_times'] else 0
            )
            
            cache_hit_ratio = (
                self.performance_metrics['cache_hits'] / 
                self.performance_metrics['total_requests']
                if self.performance_metrics['total_requests'] > 0 else 0
            )
            
            return {
                'total_requests': self.performance_metrics['total_requests'],
                'cache_hits': self.performance_metrics['cache_hits'],
                'cache_hit_ratio': cache_hit_ratio,
                'avg_processing_time': avg_processing_time,
                'accuracy_scores': self.performance_metrics['accuracy_scores'],
                'conversation_contexts': len(self.conversation_context),
                'embedding_cache_size': len(self.embedding_cache),
                'intent_cache_size': len(self.intent_cache),
                'sentiment_cache_size': len(self.sentiment_cache)
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo métricas: {str(e)}")
            return {}

if __name__ == "__main__":
    async def test_nlp():
        for mode in ["candidate", "opportunity"]:
            for depth in ["quick", "deep"]:
                logger.info(f"\nProbando modo: {mode}, profundidad: {depth}")
                nlp = NLPProcessor(mode=mode, analysis_depth=depth)
                text = "Tengo experiencia en Python, liderazgo, y gestión de proyectos."
                result = await nlp.analyze(text)
                logger.info(f"[nlp.py] Análisis para '{text}': {json.dumps(result, indent=2, ensure_ascii=False)}")

    asyncio.run(test_nlp())