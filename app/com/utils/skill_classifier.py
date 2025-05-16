# /home/pablo/app/com/utils/skill_classifier.py
import asyncio
from typing import List, Dict, Optional
import logging
import spacy
import re
import json
import hashlib
from typing import Dict, List, Optional
from django.conf import settings
from app.models import BusinessUnit

logger = logging.getLogger(__name__)

class SkillClassifier:
    def __init__(self, business_unit: BusinessUnit):
        """
        Inicializa el clasificador de habilidades.
        
        Args:
            business_unit: Unidad de negocio para el análisis
        """
        self.business_unit = business_unit
        self.cache = RedisCache()
        self.nlp = spacy.load("es_core_news_md")
        self.ontology = self._load_ontology()
        self._initialize_models()

    def _load_ontology(self) -> Dict:
        """Carga la ontología de habilidades específica por BU."""
        try:
            # Cargar ontología base
            with open("skills_ontology.json", "r") as f:
                base_ontology = json.load(f)
            
            # Añadir habilidades específicas por BU
            bu_specific = self._get_bu_specific_skills()
            
            # Combinar ontologías
            for category in bu_specific:
                if category not in base_ontology:
                    base_ontology[category] = bu_specific[category]
                else:
                    base_ontology[category].update(bu_specific[category])
            
            return base_ontology
            
        except FileNotFoundError:
            logger.warning("No se encontró archivo de ontología, usando ontología base")
            return self._get_default_ontology()

    def _get_bu_specific_skills(self) -> Dict:
        """Obtiene habilidades específicas por unidad de negocio."""
        bu_skills = {
            'amigro': {
                'technical': {
                    'migration': ['migración', 'relocalización', 'adaptación cultural'],
                    'languages': ['español', 'inglés', 'portugués', 'francés']
                },
                'soft': {
                    'adaptability': ['adaptabilidad', 'resiliencia', 'flexibilidad'],
                    'cultural_awareness': ['conciencia cultural', 'sensibilidad cultural']
                }
            },
            'huntu': {
                'technical': {
                    'academic': ['investigación', 'publicaciones', 'tesis', 'tesina'],
                    'projects': ['proyectos', 'investigación', 'publicaciones']
                },
                'soft': {
                    'academic': ['aprendizaje continuo', 'curiosidad académica']
                }
            },
            'huntred': {
                'technical': {
                    'management': ['gestión', 'liderazgo', 'estrategia'],
                    'digital': ['digitalización', 'transformación digital']
                },
                'soft': {
                    'leadership': ['liderazgo', 'gestión de equipos', 'visión estratégica']
                }
            },
            'huntred_executive': {
                'technical': {
                    'executive': ['c-suite', 'estrategia corporativa', 'governance'],
                    'board': ['gobierno corporativo', 'dirección']
                },
                'soft': {
                    'executive': ['visión estratégica', 'governance', 'leadership']
                }
            },
            'sexsi': {
                'technical': {
                    'intimacy': ['intimidad', 'relaciones', 'comunicación íntima'],
                    'health': ['salud sexual', 'educación sexual']
                },
                'soft': {
                    'emotional': ['inteligencia emocional', 'empatía', 'comunicación']
                }
            },
            'milkyleak': {
                'technical': {
                    'social_media': ['redes sociales', 'influencer', 'content creator'],
                    'digital': ['digital marketing', 'content creation']
                },
                'soft': {
                    'creativity': ['creatividad', 'innovación', 'originalidad']
                }
            }
        }
        
        return bu_skills.get(self.business_unit.name.lower(), {})

    def _get_default_ontology(self) -> Dict:
        """Obtiene la ontología base por defecto."""
        return {
            "technical": {
                "programming": ["python", "java", "javascript", "c++", "c#"],
                "frameworks": ["django", "react", "angular", "vue.js"],
                "databases": ["sql", "nosql", "mongodb", "postgresql"],
                "cloud": ["aws", "azure", "gcp"],
                "devops": ["docker", "kubernetes", "terraform"]
            },
            "soft": {
                "communication": ["communication", "teamwork", "leadership"],
                "problem_solving": ["problem solving", "analytical thinking"],
                "management": ["project management", "time management"]
            }
        }

    def _initialize_models(self):
        """Inicializa los modelos de clasificación."""
        self.models = {
            "technical": self._load_technical_model(),
            "soft": self._load_soft_model()
        }

    def _load_technical_model(self) -> Dict:
        """Carga el modelo de habilidades técnicas."""
        return {
            "patterns": self._load_patterns("technical"),
            "synonyms": self._load_synonyms("technical")
        }

    def _load_soft_model(self) -> Dict:
        """Carga el modelo de habilidades blandas."""
        return {
            "patterns": self._load_patterns("soft"),
            "synonyms": self._load_synonyms("soft")
        }

    def _load_patterns(self, category: str) -> List[str]:
        """Carga patrones específicos para una categoría."""
        base_patterns = [
            r"\b(?:python|java|sql|javascript|typescript|c\+\+|c#|ruby|php|go|rust|swift)\b",
            r"\b(?:machine\slearning|deep\slearning|ai|artificial\sintelligence)\b",
            r"\b(?:cloud|aws|azure|gcp|docker|kubernetes)\b",
            r"\b(?:devops|ci/cd|testing|qa)\b"
        ]
        
        # Añadir patrones específicos por BU
        bu_patterns = self._get_bu_specific_patterns(category)
        
        return base_patterns + bu_patterns

    def _get_bu_specific_patterns(self, category: str) -> List[str]:
        """Obtiene patrones específicos por BU para una categoría."""
        bu_patterns = {
            'amigro': {
                'technical': [r"\b(?:relocalización|migración)\b"],
                'soft': [r"\b(?:adaptabilidad|resiliencia)\b"]
            },
            'huntu': {
                'technical': [r"\b(?:tesis|tesina|investigación)\b"],
                'soft': [r"\b(?:aprendizaje\scontinuo)\b"]
            }
        }
        
        return bu_patterns.get(self.business_unit.name.lower(), {}).get(category, [])

    def _load_synonyms(self, category: str) -> Dict:
        """Carga sinónimos para una categoría."""
        return {
            "technical": {
                "python": ["pythonista", "python developer"],
                "java": ["java developer", "java engineer"],
                "sql": ["sql expert", "sql specialist"]
            },
            "soft": {
                "communication": ["comunicación", "comunicación efectiva"],
                "leadership": ["liderazgo", "gestión de equipos"]
            }
        }

    async def classify_skills(self, text: str) -> Dict:
        """
        Clasifica habilidades en el texto usando múltiples fuentes.
        
        Args:
            text: Texto a analizar
            
        Returns:
            Dict con habilidades clasificadas
        """
        try:
            # Verificar cache
            cache_key = f"skills_{hashlib.md5(text.encode()).hexdigest()}"
            cached = await self.cache.get(cache_key)
            if cached:
                return cached

            # Procesar con Spacy
            doc = self.nlp(text)
            
            # Extraer habilidades usando múltiples métodos
            skills = {
                "technical": await self._extract_technical_skills(doc, text),
                "soft": await self._extract_soft_skills(doc, text),
                "certifications": await self._extract_certifications(doc),
                "tools": await self._extract_tools(doc)
            }

            # Almacenar en cache
            await self.cache.set(cache_key, skills)
            return skills

        except Exception as e:
            logger.error(f"Error clasificando habilidades: {str(e)}")
            return {
                "technical": [],
                "soft": [],
                "certifications": [],
                "tools": []
            }

    async def _extract_technical_skills(self, doc, text: str) -> List[str]:
        """Extrae habilidades técnicas usando múltiples métodos."""
        skills = []
        
        # Método 1: Análisis de tokens
        for token in doc:
            if token.pos_ in ["NOUN", "ADJ"] and len(token.text) > 2:
                if self._is_technical_skill(token.text.lower()):
                    skills.append(token.text.lower())
        
        # Método 2: Patrones específicos
        for pattern in self.models["technical"]["patterns"]:
            matches = re.findall(pattern, text.lower())
            skills.extend(matches)
        
        # Método 3: Sinónimos
        for skill, synonyms in self.models["technical"]["synonyms"].items():
            for synonym in synonyms:
                if synonym.lower() in text.lower():
                    skills.append(skill)
        
        return list(set(skills))

    async def _extract_soft_skills(self, doc, text: str) -> List[str]:
        """Extrae habilidades blandas usando múltiples métodos."""
        skills = []
        
        # Método 1: Análisis de tokens
        for token in doc:
            if token.pos_ in ["NOUN", "ADJ"] and len(token.text) > 2:
                if self._is_soft_skill(token.text.lower()):
                    skills.append(token.text.lower())
        
        # Método 2: Patrones específicos
        for pattern in self.models["soft"]["patterns"]:
            matches = re.findall(pattern, text.lower())
            skills.extend(matches)
        
        # Método 3: Sinónimos
        for skill, synonyms in self.models["soft"]["synonyms"].items():
            for synonym in synonyms:
                if synonym.lower() in text.lower():
                    skills.append(skill)
        
        return list(set(skills))

    async def _extract_certifications(self, doc) -> List[str]:
        """Extrae certificaciones usando patrones y modelos."""
        # Implementación específica para certificaciones
        return []

    async def _extract_tools(self, doc) -> List[str]:
        """Extrae herramientas usando patrones y modelos."""
        # Implementación específica para herramientas
        return []

    def _is_technical_skill(self, skill: str) -> bool:
        """Verifica si una habilidad es técnica usando la ontología."""
        return any(
            skill in category_skills
            for category_skills in self.ontology.get("technical", {}).values()
        )

    def _is_soft_skill(self, skill: str) -> bool:
        """Verifica si una habilidad es blanda usando la ontología."""
        return any(
            skill in category_skills
            for category_skills in self.ontology.get("soft", {}).values()
        )
        # Implementar lógica para determinar la mejor clasificación
        return classifications
