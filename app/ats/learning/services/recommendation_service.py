from typing import Dict, Any, List
from app.ats.learning.models.skill import Skill
from app.ats.learning.models.course import Course
from app.ats.learning.models.learning_path import LearningPath
from app.ats.models.business_unit import BusinessUnit
from app.ats.models.user import User
from app.ats.integrations.notifications.process.learning_notifications import LearningNotificationService
from app.ml.analyzers.learning.skill_analyzer import SkillAnalyzer
from app.ml.analyzers.learning.learning_path import LearningPathGenerator
from app.ml.analyzers.learning.course_recommender import CourseRecommender

class LearningRecommendationService:
    """Servicio de recomendaciones de aprendizaje"""
    
    def __init__(self):
        self.notification_service = LearningNotificationService()
        self.skill_analyzer = SkillAnalyzer()
        self.path_generator = LearningPathGenerator()
        self.course_recommender = CourseRecommender()
    
    async def generate_recommendations(
        self,
        user: User,
        business_unit: BusinessUnit
    ) -> Dict[str, Any]:
        """Genera recomendaciones de aprendizaje"""
        try:
            # Analizar gaps de habilidades
            skill_gaps = await self.skill_analyzer.analyze_skill_gaps(user.id)
            
            # Generar ruta de aprendizaje
            learning_path = await self.path_generator.generate_path(
                user_id=user.id,
                skill_gaps=skill_gaps
            )
            
            # Obtener recomendaciones de cursos
            course_recommendations = await self.course_recommender.get_recommendations(
                user_id=user.id,
                skills=skill_gaps['gaps']
            )
            
            # Notificar recomendaciones
            await self._notify_recommendations(
                user=user,
                business_unit=business_unit,
                recommendations={
                    'skill_gaps': skill_gaps,
                    'learning_path': learning_path,
                    'courses': course_recommendations
                }
            )
            
            return {
                'user_id': user.id,
                'business_unit': business_unit.id,
                'skill_gaps': skill_gaps,
                'learning_path': learning_path,
                'courses': course_recommendations
            }
        except Exception as e:
            self.logger.error(f"Error generando recomendaciones: {str(e)}")
            return None
    
    async def _notify_recommendations(
        self,
        user: User,
        business_unit: BusinessUnit,
        recommendations: Dict[str, Any]
    ) -> None:
        """Notifica recomendaciones generadas"""
        await self.notification_service.send_notification(
            title="Nuevas Recomendaciones de Aprendizaje",
            message=self._format_recommendations_message(recommendations),
            notification_type="LEARNING_RECOMMENDATIONS",
            severity="INFO",
            business_unit=business_unit,
            user=user,
            metadata={'recommendations': recommendations}
        )
    
    def _format_recommendations_message(self, recommendations: Dict[str, Any]) -> str:
        """Formatea mensaje de recomendaciones"""
        return (
            "Nuevas recomendaciones de aprendizaje:\n\n"
            f"Gaps de Habilidades:\n{self._format_skill_gaps(recommendations['skill_gaps'])}\n\n"
            f"Ruta de Aprendizaje:\n{self._format_learning_path(recommendations['learning_path'])}\n\n"
            f"Cursos Recomendados:\n{self._format_courses(recommendations['courses'])}"
        )
    
    def _format_skill_gaps(self, skill_gaps: Dict[str, Any]) -> str:
        """Formatea gaps de habilidades"""
        return "\n".join([
            f"• {gap['skill']}: Nivel actual {gap['current_level']}, "
            f"Nivel requerido {gap['required_level']}"
            for gap in skill_gaps['gaps']
        ])
    
    def _format_learning_path(self, learning_path: Dict[str, Any]) -> str:
        """Formatea ruta de aprendizaje"""
        return "\n".join([
            f"• {step['skill']}: {step['description']} "
            f"(Duración estimada: {step['estimated_duration']})"
            for step in learning_path['steps']
        ])
    
    def _format_courses(self, courses: List[Dict[str, Any]]) -> str:
        """Formatea cursos recomendados"""
        return "\n".join([
            f"• {course['title']} ({course['provider']}):\n"
            f"  - Nivel: {course['level']}\n"
            f"  - Duración: {course['duration']}\n"
            f"  - Precio: {course['price']}\n"
            f"  - URL: {course['url']}"
            for course in courses
        ]) 