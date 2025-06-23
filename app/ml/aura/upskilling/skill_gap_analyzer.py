"""
AURA - Skill Gap Analyzer Avanzado
Análisis de brecha de habilidades y recomendaciones de upskilling predictivo usando GNN y motores avanzados.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.ml.aura.graph_builder import GNNManager

logger = logging.getLogger(__name__)

class SkillGapAnalyzer:
    """
    Analizador avanzado de brecha de habilidades:
    - Usa la GNN para comparar el perfil del usuario con trayectorias objetivo y el mercado.
    - Identifica gaps técnicos, soft skills y gaps de red (networking).
    - Genera recomendaciones explicables y accionables.
    - Hooks para notificación, gamificación y logging.
    """
    def __init__(self):
        self.gnn = GNNManager()
        self.last_results = {}

    def analyze(self, user_id: str, target_profile: Dict[str, Any], notify: bool = True, gamify: bool = True) -> Dict[str, Any]:
        """
        Analiza la brecha de skills del usuario contra un perfil objetivo.
        Args:
            user_id: ID del usuario
            target_profile: dict con skills y niveles requeridos
            notify: si True, dispara notificación
            gamify: si True, dispara logros si cierra brechas
        Returns:
            dict con brechas, recomendaciones, explicabilidad y contexto de red
        """
        # 1. Obtener perfil enriquecido del usuario desde la GNN
        user_profile = self.gnn.get_user_profile(user_id)
        # 2. Comparar skills técnicas y soft skills
        gaps = {}
        recommendations = []
        explain = {}
        for skill, required_level in target_profile.get('skills', {}).items():
            user_level = user_profile.get('skills', {}).get(skill, 0)
            if user_level < required_level:
                gap = required_level - user_level
                gaps[skill] = {
                    'user_level': user_level,
                    'required_level': required_level,
                    'gap': gap
                }
                recommendations.append(f"Mejora tu nivel en '{skill}' de {user_level} a {required_level}.")
                explain[skill] = f"Requerido para el objetivo: {target_profile.get('role', 'desconocido')}"
        # 3. Analizar gaps de soft skills
        for soft, required_level in target_profile.get('soft_skills', {}).items():
            user_level = user_profile.get('soft_skills', {}).get(soft, 0)
            if user_level < required_level:
                gap = required_level - user_level
                gaps[soft] = {
                    'user_level': user_level,
                    'required_level': required_level,
                    'gap': gap
                }
                recommendations.append(f"Desarrolla tu soft skill '{soft}' de {user_level} a {required_level}.")
                explain[soft] = f"Clave para el éxito en {target_profile.get('role', 'desconocido')}"
        # 4. Analizar gaps de red (networking)
        network_gap = self.gnn.analyze_network_gap(user_id, target_profile)
        if network_gap:
            gaps['networking'] = network_gap
            recommendations.append("Expande tu red con conexiones estratégicas sugeridas.")
            explain['networking'] = "Tu red actual limita el acceso a oportunidades clave."
        # 5. Guardar resultados
        result = {
            'user_id': user_id,
            'target_profile': target_profile,
            'gaps': gaps,
            'recommendations': recommendations,
            'explainability': explain,
            'network_context': user_profile.get('network_context', {}),
            'timestamp': datetime.now().isoformat()
        }
        self.last_results[user_id] = result
        # 6. Hooks: notificación y gamificación
        if notify:
            self._notify_user(user_id, result)
        if gamify and not gaps:
            self._award_achievement(user_id, 'Skill Gap Closed')
        logger.info(f"SkillGapAnalyzer: análisis para {user_id} completado.")
        return result

    def _notify_user(self, user_id: str, result: Dict[str, Any]):
        """Envía notificación al usuario (hook para orquestador/chatbot)."""
        # Aquí se integraría con el orquestador o el chatbot
        logger.info(f"Notificación enviada a {user_id}: {result['recommendations']}")

    def _award_achievement(self, user_id: str, achievement: str):
        """Otorga logro al usuario (hook para gamificación)."""
        # Aquí se integraría con el sistema de logros/gamificación
        logger.info(f"Logro otorgado a {user_id}: {achievement}")

# Ejemplo de uso avanzado:
# analyzer = SkillGapAnalyzer()
# result = analyzer.analyze('user_123', {'role': 'Data Scientist', 'skills': {'Python': 4, 'ML': 3}, 'soft_skills': {'Comunicación': 3}}) 