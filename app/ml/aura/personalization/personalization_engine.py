"""
AURA - Personalization Engine
Personalización dinámica por usuario/segmento con aprendizaje continuo, integración con GNN y adaptación de experiencia.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
import random

# Suponiendo que existe un GNNManager en app/ml/aura/graph_builder.py
from app.ml.aura.graph_builder import GNNManager
from app.ml.aura.analytics.executive_dashboard import ExecutiveAnalytics

ENABLED = True

logger = logging.getLogger(__name__)

SEGMENTS = [
    "executive", "junior", "recruiter", "student", "entrepreneur", "tech", "hr", "sales"
]

class PersonalizationEngine:
    """
    Motor de personalización avanzada de AURA.
    Aprende del comportamiento, preferencias, soft skills, motivaciones, etc.
    Adapta recomendaciones, dashboards, tono y funcionalidades en tiempo real.
    Integra datos de la GNN para personalización contextual y networking inteligente.
    """
    def __init__(self):
        self.enabled = ENABLED
        self.user_segments = {}  # user_id -> segment
        self.user_history = {}   # user_id -> historial de acciones
        self.user_preferences = {}  # user_id -> preferencias
        self.learning_data = {}  # user_id -> datos de aprendizaje
        self.gnn = GNNManager()
        self.executive_analytics = ExecutiveAnalytics()

    def personalize(self, user_id: str, user_profile: Optional[Dict[str, Any]] = None, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Personaliza la experiencia del usuario en AURA.
        - Detecta segmento y rol usando perfil y GNN.
        - Adapta dashboards, widgets y recomendaciones.
        - Aprende de cada interacción y ajusta preferencias.
        - Integra insights de la red y benchmarking ejecutivo si aplica.
        """
        if not self.enabled:
            return self._get_mock_personalization(user_id, user_profile)

        # 1. Detectar segmento y rol
        segment = self._detect_segment(user_id, user_profile)
        # 2. Analizar contexto de red (GNN)
        network_context = self.gnn.get_user_context(user_id)
        # 3. Adaptar mensaje de bienvenida/contexto
        name = user_profile.get("name", "Usuario") if user_profile else "Usuario"
        welcome_message = self._get_welcome_message(segment, name, network_context)
        # 4. Generar recomendaciones personalizadas
        recommendations = self._generate_recommendations(user_id, segment, context, network_context)
        # 5. Configuración avanzada de UI/dashboard
        ui_config = self._get_ui_config(segment, context, network_context)
        # 6. Insights ejecutivos si aplica
        executive_insights = None
        if segment == "executive":
            executive_insights = self.executive_analytics.generate_business_insights(network_context)
        # 7. Aprendizaje continuo
        self._learn_from_interaction(user_id, segment, context, network_context)
        # 8. Retornar resultado enriquecido
        return {
            "user_id": user_id,
            "segment": segment,
            "welcome_message": welcome_message,
            "recommendations": recommendations,
            "ui_config": ui_config,
            "network_context": network_context,
            "executive_insights": executive_insights,
            "timestamp": datetime.now().isoformat()
        }

    def _detect_segment(self, user_id: str, user_profile: Optional[Dict[str, Any]]) -> str:
        # Usa perfil, historial y GNN para segmentar
        if user_id in self.user_segments:
            return self.user_segments[user_id]
        if user_profile:
            if user_profile.get("is_executive"):
                segment = "executive"
            elif user_profile.get("is_student"):
                segment = "student"
            elif user_profile.get("role") in ["recruiter", "headhunter"]:
                segment = "recruiter"
            elif user_profile.get("industry") == "tech":
                segment = "tech"
            elif user_profile.get("department") == "HR":
                segment = "hr"
            elif user_profile.get("department") == "Sales":
                segment = "sales"
            else:
                segment = "junior"
        else:
            segment = self.gnn.infer_segment(user_id) or random.choice(SEGMENTS)
        self.user_segments[user_id] = segment
        return segment

    def _get_welcome_message(self, segment: str, name: str, network_context: Dict[str, Any]) -> str:
        # Mensaje adaptado según segmento y contexto de red
        base = {
            "executive": f"Bienvenido/a a tu panel ejecutivo, {name}. Acceso a insights estratégicos y benchmarking sectorial.",
            "junior": f"¡Hola {name}! Descubre cómo crecer profesionalmente y conecta con mentores clave de tu red.",
            "recruiter": f"Panel de reclutador activado. Analiza redes de candidatos y talento emergente.",
            "student": f"¡Bienvenido/a estudiante! Explora prácticas, skills y trayectorias de éxito en tu sector.",
            "entrepreneur": f"Panel emprendedor: conecta, aprende y accede a recursos para tu startup.",
            "tech": f"Panel tech: mantente actualizado/a y participa en retos tecnológicos.",
            "hr": f"Panel RRHH: gestiona talento, clima y compliance desde un solo lugar.",
            "sales": f"Panel ventas: identifica leads y oportunidades en tu red profesional."
        }
        # Personalización extra según contexto de red
        if network_context.get("influencer_score", 0) > 0.8:
            return base.get(segment, f"¡Bienvenido/a a AURA, {name}!") + " Eres un influencer clave en tu red."
        return base.get(segment, f"¡Bienvenido/a a AURA, {name}!")

    def _generate_recommendations(self, user_id: str, segment: str, context: Optional[str], network_context: Dict[str, Any]) -> List[str]:
        # Recomendaciones personalizadas usando historial, preferencias y contexto de red
        base = {
            "executive": ["Accede a KPIs exclusivos", "Solicita benchmarking sectorial", "Activa alertas de mercado"],
            "junior": ["Explora rutas de carrera", "Completa tu perfil", "Conecta con mentores"],
            "recruiter": ["Busca talento emergente", "Crea campañas de hunting", "Analiza redes de candidatos"],
            "student": ["Descubre prácticas profesionales", "Aprende skills en tendencia", "Simula trayectorias"],
            "entrepreneur": ["Conecta con inversores", "Accede a networking premium", "Solicita análisis de mercado"],
            "tech": ["Participa en hackathons", "Actualiza tus skills técnicos", "Recibe alertas de nuevas tecnologías"],
            "hr": ["Analiza clima organizacional", "Detecta influencers internos", "Activa panel de compliance"],
            "sales": ["Identifica leads estratégicos", "Solicita análisis de red", "Recibe alertas de oportunidades"]
        }
        recs = base.get(segment, [])
        # Personalización avanzada: sugerir conexiones clave si la GNN detecta oportunidades
        if network_context.get("suggested_connections"):
            recs.append("Conecta con personas clave sugeridas por tu red")
        # Añadir recomendaciones contextuales
        if context == "dashboard":
            recs.append("Personaliza tu dashboard desde Configuración")
        elif context == "chatbot":
            recs.append("Pregunta a AURA por oportunidades en tu sector")
        return recs[:4]

    def _get_ui_config(self, segment: str, context: Optional[str], network_context: Dict[str, Any]) -> dict:
        # Configuración avanzada de UI según segmento y contexto de red
        config = {
            "theme": "dark" if segment in ["executive", "tech"] else "light",
            "widgets": ["network", "skills", "alerts"]
        }
        if segment == "executive":
            config["widgets"].append("kpi")
        if network_context.get("influencer_score", 0) > 0.8:
            config["widgets"].append("influencer_panel")
        if context == "dashboard":
            config["widgets"].append("customize")
        return config

    def _learn_from_interaction(self, user_id: str, segment: str, context: Optional[str], network_context: Dict[str, Any]):
        # Aprendizaje continuo: guardar historial, preferencias y ajustar segmentación
        if user_id not in self.user_history:
            self.user_history[user_id] = []
        if context:
            self.user_history[user_id].append(context)
        # Ajustar preferencias según interacciones y contexto de red
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {}
        if network_context.get("suggested_connections"):
            self.user_preferences[user_id]["networking"] = True
        # Futuro: aprendizaje profundo, feedback loop, ajuste de segmentación vía GNN

    def _get_mock_personalization(self, user_id: str, user_profile: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        # Simulación básica para cuando está deshabilitado
        name = user_profile.get("name", "Usuario") if user_profile else "Usuario"
        return {
            "user_id": user_id,
            "segment": "junior",
            "welcome_message": f"¡Hola {name}! Descubre cómo crecer profesionalmente y conecta con mentores.",
            "recommendations": ["Explora rutas de carrera", "Completa tu perfil", "Conecta con mentores"],
            "ui_config": {"theme": "light", "widgets": ["network", "skills", "alerts"]},
            "network_context": {},
            "executive_insights": None,
            "timestamp": datetime.now().isoformat()
        }

personalization_engine = PersonalizationEngine() 