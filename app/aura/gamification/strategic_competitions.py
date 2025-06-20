"""
AURA - Strategic Gamification (FASE 3)
Sistema de competencias profesionales y gamificación estratégica
"""

import logging
import random
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib

logger = logging.getLogger(__name__)

# CONFIGURACIÓN: DESHABILITADO POR DEFECTO
ENABLED = False  # Cambiar a True para habilitar


class CompetitionType(Enum):
    """Tipos de competencias"""
    NETWORKING_CHALLENGE = "networking_challenge"
    SKILL_HACKATHON = "skill_hackathon"
    INFLUENCE_CONTEST = "influence_contest"
    COLLABORATION_PROJECT = "collaboration_project"
    INNOVATION_CHALLENGE = "innovation_challenge"
    KNOWLEDGE_SHARING = "knowledge_sharing"


class ChallengeDifficulty(Enum):
    """Dificultad de desafíos"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass
class Competition:
    """Competencia profesional"""
    id: str
    name: str
    description: str
    type: CompetitionType
    difficulty: ChallengeDifficulty
    start_date: datetime
    end_date: datetime
    max_participants: int
    current_participants: int = 0
    rewards: Dict[str, Any] = field(default_factory=dict)
    rules: List[str] = field(default_factory=list)
    status: str = "upcoming"  # 'upcoming', 'active', 'completed', 'cancelled'
    participants: List[str] = field(default_factory=list)
    leaderboard: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Participant:
    """Participante en competencia"""
    user_id: str
    competition_id: str
    joined_at: datetime
    score: float = 0.0
    progress: Dict[str, Any] = field(default_factory=dict)
    achievements: List[str] = field(default_factory=list)
    rank: int = 0
    status: str = "active"  # 'active', 'disqualified', 'completed'


@dataclass
class Challenge:
    """Desafío específico"""
    id: str
    competition_id: str
    name: str
    description: str
    type: str
    points: int
    requirements: Dict[str, Any]
    completion_criteria: Dict[str, Any]
    time_limit: Optional[timedelta] = None
    bonus_multiplier: float = 1.0


class StrategicGamification:
    """
    Sistema de gamificación estratégica con competencias profesionales
    """
    
    def __init__(self):
        self.enabled = ENABLED
        if not self.enabled:
            logger.info("StrategicGamification: DESHABILITADO")
            return
        
        self.competitions = {}
        self.participants = {}
        self.challenges = {}
        self.user_progress = {}
        self.rewards_history = {}
        
        # Configuración de competencias
        self.competition_config = {
            "max_concurrent_competitions": 5,
            "min_participants": 3,
            "max_participants": 100,
            "scoring_algorithm": "weighted",
            "bonus_multipliers": {
                "early_bird": 1.2,
                "streak": 1.1,
                "team_collaboration": 1.3,
                "innovation": 1.5
            }
        }
        
        self._initialize_sample_competitions()
        logger.info("StrategicGamification: Inicializado")
    
    def _initialize_sample_competitions(self):
        """Inicializa competencias de ejemplo"""
        if not self.enabled:
            return
        
        # Competencia de Networking
        networking_comp = Competition(
            id="networking_master_2024",
            name="Networking Master 2024",
            description="Desafío para expandir tu red profesional de manera estratégica",
            type=CompetitionType.NETWORKING_CHALLENGE,
            difficulty=ChallengeDifficulty.INTERMEDIATE,
            start_date=datetime.now() + timedelta(days=7),
            end_date=datetime.now() + timedelta(days=30),
            max_participants=50,
            rewards={
                "points": 1000,
                "badge": "networking_master",
                "certificate": "Networking Excellence",
                "premium_features": ["advanced_analytics", "priority_support"]
            },
            rules=[
                "Conectar con al menos 20 nuevos profesionales",
                "Participar en 3 eventos de networking",
                "Crear contenido valioso para la comunidad",
                "Mantener engagement activo durante 30 días"
            ]
        )
        
        # Competencia de Habilidades
        skill_comp = Competition(
            id="skill_hackathon_2024",
            name="Skill Hackathon 2024",
            description="Desarrolla y demuestra tus habilidades técnicas en un hackathon virtual",
            type=CompetitionType.SKILL_HACKATHON,
            difficulty=ChallengeDifficulty.ADVANCED,
            start_date=datetime.now() + timedelta(days=14),
            end_date=datetime.now() + timedelta(days=21),
            max_participants=30,
            rewards={
                "points": 2000,
                "badge": "skill_master",
                "certificate": "Technical Excellence",
                "job_opportunities": True,
                "mentorship": "expert_mentor"
            },
            rules=[
                "Completar al menos 5 proyectos técnicos",
                "Colaborar con otros participantes",
                "Documentar el proceso de desarrollo",
                "Presentar soluciones innovadoras"
            ]
        )
        
        # Competencia de Influencia
        influence_comp = Competition(
            id="influence_leader_2024",
            name="Influence Leader 2024",
            description="Construye tu influencia profesional y lidera la comunidad",
            type=CompetitionType.INFLUENCE_CONTEST,
            difficulty=ChallengeDifficulty.EXPERT,
            start_date=datetime.now() + timedelta(days=21),
            end_date=datetime.now() + timedelta(days=45),
            max_participants=25,
            rewards={
                "points": 3000,
                "badge": "influence_leader",
                "certificate": "Leadership Excellence",
                "speaking_opportunities": True,
                "thought_leadership": True
            },
            rules=[
                "Alcanzar score de influencia de 0.8+",
                "Crear contenido que genere 1000+ interacciones",
                "Mentorear a al menos 5 profesionales",
                "Organizar 2 eventos de la comunidad"
            ]
        )
        
        self.competitions[networking_comp.id] = networking_comp
        self.competitions[skill_comp.id] = skill_comp
        self.competitions[influence_comp.id] = influence_comp
    
    def create_competition(self, competition_data: Dict[str, Any]) -> str:
        """
        Crea una nueva competencia
        """
        if not self.enabled:
            return "mock_competition_id"
        
        try:
            competition_id = f"comp_{len(self.competitions)}_{int(datetime.now().timestamp())}"
            
            competition = Competition(
                id=competition_id,
                name=competition_data["name"],
                description=competition_data["description"],
                type=CompetitionType(competition_data["type"]),
                difficulty=ChallengeDifficulty(competition_data["difficulty"]),
                start_date=datetime.fromisoformat(competition_data["start_date"]),
                end_date=datetime.fromisoformat(competition_data["end_date"]),
                max_participants=competition_data["max_participants"],
                rewards=competition_data.get("rewards", {}),
                rules=competition_data.get("rules", [])
            )
            
            self.competitions[competition_id] = competition
            
            # Crear desafíos asociados
            self._create_competition_challenges(competition_id, competition_data.get("challenges", []))
            
            logger.info(f"Competition created: {competition_id}")
            return competition_id
            
        except Exception as e:
            logger.error(f"Error creating competition: {e}")
            return None
    
    def _create_competition_challenges(self, competition_id: str, challenges_data: List[Dict[str, Any]]):
        """Crea desafíos para una competencia"""
        for i, challenge_data in enumerate(challenges_data):
            challenge_id = f"{competition_id}_challenge_{i}"
            
            challenge = Challenge(
                id=challenge_id,
                competition_id=competition_id,
                name=challenge_data["name"],
                description=challenge_data["description"],
                type=challenge_data["type"],
                points=challenge_data["points"],
                requirements=challenge_data.get("requirements", {}),
                completion_criteria=challenge_data.get("completion_criteria", {}),
                time_limit=timedelta(hours=challenge_data.get("time_limit_hours", 24)),
                bonus_multiplier=challenge_data.get("bonus_multiplier", 1.0)
            )
            
            self.challenges[challenge_id] = challenge
    
    def join_competition(self, user_id: str, competition_id: str) -> bool:
        """
        Une un usuario a una competencia
        """
        if not self.enabled:
            return True
        
        try:
            competition = self.competitions.get(competition_id)
            if not competition:
                logger.error(f"Competition not found: {competition_id}")
                return False
            
            # Verificar si la competencia está abierta
            if competition.status != "upcoming" and competition.status != "active":
                logger.error(f"Competition {competition_id} is not open for registration")
                return False
            
            # Verificar si hay espacio
            if competition.current_participants >= competition.max_participants:
                logger.error(f"Competition {competition_id} is full")
                return False
            
            # Verificar si el usuario ya está participando
            participant_key = f"{user_id}_{competition_id}"
            if participant_key in self.participants:
                logger.error(f"User {user_id} already participating in {competition_id}")
                return False
            
            # Crear participante
            participant = Participant(
                user_id=user_id,
                competition_id=competition_id,
                joined_at=datetime.now()
            )
            
            self.participants[participant_key] = participant
            competition.participants.append(user_id)
            competition.current_participants += 1
            
            # Inicializar progreso del usuario
            self.user_progress[participant_key] = {
                "score": 0.0,
                "challenges_completed": 0,
                "achievements": [],
                "last_activity": datetime.now(),
                "streak_days": 0
            }
            
            logger.info(f"User {user_id} joined competition {competition_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error joining competition: {e}")
            return False
    
    def submit_challenge_completion(self, user_id: str, competition_id: str, 
                                  challenge_id: str, submission_data: Dict[str, Any]) -> bool:
        """
        Envía completación de un desafío
        """
        if not self.enabled:
            return True
        
        try:
            participant_key = f"{user_id}_{competition_id}"
            participant = self.participants.get(participant_key)
            challenge = self.challenges.get(challenge_id)
            
            if not participant or not challenge:
                logger.error(f"Participant or challenge not found")
                return False
            
            # Verificar si el desafío ya fue completado
            if challenge_id in participant.achievements:
                logger.error(f"Challenge {challenge_id} already completed by user {user_id}")
                return False
            
            # Validar completación
            if self._validate_challenge_completion(challenge, submission_data):
                # Otorgar puntos
                points = challenge.points * challenge.bonus_multiplier
                participant.score += points
                participant.achievements.append(challenge_id)
                
                # Actualizar progreso
                user_progress = self.user_progress.get(participant_key, {})
                user_progress["score"] = participant.score
                user_progress["challenges_completed"] += 1
                user_progress["last_activity"] = datetime.now()
                
                # Verificar bonus de racha
                if self._check_streak_bonus(user_id, competition_id):
                    points *= self.competition_config["bonus_multipliers"]["streak"]
                    participant.score += points * 0.1  # Bonus adicional
                
                # Actualizar leaderboard
                self._update_leaderboard(competition_id)
                
                logger.info(f"Challenge {challenge_id} completed by user {user_id} for {points} points")
                return True
            else:
                logger.error(f"Challenge completion validation failed for user {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error submitting challenge completion: {e}")
            return False
    
    def _validate_challenge_completion(self, challenge: Challenge, submission_data: Dict[str, Any]) -> bool:
        """Valida la completación de un desafío"""
        try:
            criteria = challenge.completion_criteria
            
            for criterion, required_value in criteria.items():
                if criterion in submission_data:
                    submitted_value = submission_data[criterion]
                    
                    if isinstance(required_value, (int, float)):
                        if submitted_value < required_value:
                            return False
                    elif isinstance(required_value, str):
                        if submitted_value != required_value:
                            return False
                    elif isinstance(required_value, list):
                        if not all(item in submitted_value for item in required_value):
                            return False
                else:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating challenge completion: {e}")
            return False
    
    def _check_streak_bonus(self, user_id: str, competition_id: str) -> bool:
        """Verifica si el usuario merece bonus por racha"""
        participant_key = f"{user_id}_{competition_id}"
        user_progress = self.user_progress.get(participant_key, {})
        
        last_activity = user_progress.get("last_activity")
        if not last_activity:
            return False
        
        # Verificar si ha sido activo en los últimos 3 días
        days_since_activity = (datetime.now() - last_activity).days
        return days_since_activity <= 3
    
    def _update_leaderboard(self, competition_id: str):
        """Actualiza el leaderboard de una competencia"""
        competition = self.competitions.get(competition_id)
        if not competition:
            return
        
        # Obtener todos los participantes
        participants = [
            (key, participant) for key, participant in self.participants.items()
            if participant.competition_id == competition_id
        ]
        
        # Ordenar por score
        participants.sort(key=lambda x: x[1].score, reverse=True)
        
        # Actualizar rankings
        leaderboard = []
        for rank, (key, participant) in enumerate(participants, 1):
            participant.rank = rank
            leaderboard.append({
                "rank": rank,
                "user_id": participant.user_id,
                "score": participant.score,
                "challenges_completed": len(participant.achievements),
                "joined_at": participant.joined_at.isoformat()
            })
        
        competition.leaderboard = leaderboard
    
    def get_competition_leaderboard(self, competition_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene el leaderboard de una competencia
        """
        if not self.enabled:
            return self._get_mock_leaderboard(competition_id)
        
        competition = self.competitions.get(competition_id)
        if not competition:
            return []
        
        return competition.leaderboard
    
    def get_user_competitions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene competencias de un usuario
        """
        if not self.enabled:
            return self._get_mock_user_competitions(user_id)
        
        user_competitions = []
        
        for participant_key, participant in self.participants.items():
            if participant.user_id == user_id:
                competition = self.competitions.get(participant.competition_id)
                if competition:
                    user_competitions.append({
                        "competition_id": competition.id,
                        "name": competition.name,
                        "type": competition.type.value,
                        "difficulty": competition.difficulty.value,
                        "status": competition.status,
                        "score": participant.score,
                        "rank": participant.rank,
                        "joined_at": participant.joined_at.isoformat(),
                        "progress": self._calculate_user_progress(user_id, competition.id)
                    })
        
        return user_competitions
    
    def _calculate_user_progress(self, user_id: str, competition_id: str) -> Dict[str, Any]:
        """Calcula progreso del usuario en una competencia"""
        participant_key = f"{user_id}_{competition_id}"
        user_progress = self.user_progress.get(participant_key, {})
        competition = self.competitions.get(competition_id)
        
        if not competition:
            return {}
        
        # Contar desafíos de la competencia
        competition_challenges = [
            challenge for challenge in self.challenges.values()
            if challenge.competition_id == competition_id
        ]
        
        total_challenges = len(competition_challenges)
        completed_challenges = user_progress.get("challenges_completed", 0)
        
        return {
            "total_challenges": total_challenges,
            "completed_challenges": completed_challenges,
            "completion_percentage": (completed_challenges / total_challenges * 100) if total_challenges > 0 else 0,
            "current_score": user_progress.get("score", 0),
            "streak_days": user_progress.get("streak_days", 0),
            "last_activity": user_progress.get("last_activity", datetime.now()).isoformat()
        }
    
    def award_competition_rewards(self, competition_id: str) -> Dict[str, List[str]]:
        """
        Otorga recompensas al finalizar una competencia
        """
        if not self.enabled:
            return self._get_mock_rewards(competition_id)
        
        try:
            competition = self.competitions.get(competition_id)
            if not competition or competition.status != "completed":
                return {"error": "Competition not completed"}
            
            # Obtener top 3 participantes
            top_participants = competition.leaderboard[:3]
            awarded_users = []
            
            for i, participant_data in enumerate(top_participants):
                user_id = participant_data["user_id"]
                participant_key = f"{user_id}_{competition_id}"
                participant = self.participants.get(participant_key)
                
                if participant:
                    # Otorgar recompensas según posición
                    if i == 0:  # Primer lugar
                        rewards = competition.rewards.copy()
                        rewards["points"] = int(rewards.get("points", 0) * 1.5)
                        rewards["title"] = "Champion"
                    elif i == 1:  # Segundo lugar
                        rewards = competition.rewards.copy()
                        rewards["points"] = int(rewards.get("points", 0) * 1.2)
                        rewards["title"] = "Runner-up"
                    else:  # Tercer lugar
                        rewards = competition.rewards.copy()
                        rewards["title"] = "Finalist"
                    
                    # Guardar historial de recompensas
                    self.rewards_history[participant_key] = {
                        "competition_id": competition_id,
                        "position": i + 1,
                        "rewards": rewards,
                        "awarded_at": datetime.now().isoformat()
                    }
                    
                    awarded_users.append(user_id)
            
            logger.info(f"Rewards awarded for competition {competition_id} to {len(awarded_users)} users")
            return {"awarded_users": awarded_users}
            
        except Exception as e:
            logger.error(f"Error awarding competition rewards: {e}")
            return {"error": str(e)}
    
    def get_available_competitions(self) -> List[Dict[str, Any]]:
        """
        Obtiene competencias disponibles
        """
        if not self.enabled:
            return self._get_mock_available_competitions()
        
        available = []
        current_time = datetime.now()
        
        for competition in self.competitions.values():
            if competition.status in ["upcoming", "active"] and current_time <= competition.end_date:
                available.append({
                    "id": competition.id,
                    "name": competition.name,
                    "description": competition.description,
                    "type": competition.type.value,
                    "difficulty": competition.difficulty.value,
                    "start_date": competition.start_date.isoformat(),
                    "end_date": competition.end_date.isoformat(),
                    "current_participants": competition.current_participants,
                    "max_participants": competition.max_participants,
                    "rewards": competition.rewards,
                    "status": competition.status
                })
        
        return available
    
    def _get_mock_leaderboard(self, competition_id: str) -> List[Dict[str, Any]]:
        """Leaderboard simulado"""
        return [
            {
                "rank": 1,
                "user_id": "user_1",
                "score": 2500,
                "challenges_completed": 8,
                "joined_at": datetime.now().isoformat()
            },
            {
                "rank": 2,
                "user_id": "user_2",
                "score": 2200,
                "challenges_completed": 7,
                "joined_at": datetime.now().isoformat()
            }
        ]
    
    def _get_mock_user_competitions(self, user_id: str) -> List[Dict[str, Any]]:
        """Competencias de usuario simuladas"""
        return [
            {
                "competition_id": "networking_master_2024",
                "name": "Networking Master 2024",
                "type": "networking_challenge",
                "difficulty": "intermediate",
                "status": "active",
                "score": 750,
                "rank": 5,
                "joined_at": datetime.now().isoformat(),
                "progress": {
                    "total_challenges": 4,
                    "completed_challenges": 3,
                    "completion_percentage": 75.0,
                    "current_score": 750,
                    "streak_days": 5,
                    "last_activity": datetime.now().isoformat()
                }
            }
        ]
    
    def _get_mock_rewards(self, competition_id: str) -> Dict[str, List[str]]:
        """Recompensas simuladas"""
        return {
            "awarded_users": ["user_1", "user_2", "user_3"]
        }
    
    def _get_mock_available_competitions(self) -> List[Dict[str, Any]]:
        """Competencias disponibles simuladas"""
        return [
            {
                "id": "networking_master_2024",
                "name": "Networking Master 2024",
                "description": "Desafío para expandir tu red profesional",
                "type": "networking_challenge",
                "difficulty": "intermediate",
                "start_date": datetime.now().isoformat(),
                "end_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "current_participants": 25,
                "max_participants": 50,
                "rewards": {"points": 1000, "badge": "networking_master"},
                "status": "active"
            }
        ]


# Instancia global del sistema de gamificación estratégica
strategic_gamification = StrategicGamification() 