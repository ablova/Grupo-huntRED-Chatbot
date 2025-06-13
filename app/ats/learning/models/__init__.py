# /home/pablo/app/ats/learning/models/__init__.py
from app.ats.learning.models.course import Course
from app.ats.learning.models.learning_path import LearningPath, LearningPathStep
from app.models import Skill

__all__ = [
    'Course',
    'LearningPath',
    'LearningPathStep',
    'Skill'
] 