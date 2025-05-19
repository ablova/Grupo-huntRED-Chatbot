from typing import Dict, Any, Optional, List
import logging
from app.com.dynamics.corecore import DynamicModule
from app.models import Person

logger = logging.getLogger(__name__)

class GamificationSystem(DynamicModule):
    """Gamification system module."""
    
    def __init__(self, business_unit: BusinessUnit):
        super().__init__(business_unit)
        self.achievements = {}
        self.badges = {}
        self.progress = {}
        
    def _load_config(self) -> Dict:
        """Load gamification configuration."""
        return {
            'points_per_action': {
                'message': 1,
                'application': 10,
                'interview': 20,
                'offer': 50
            },
            'badge_thresholds': {
                'bronze': 100,
                'silver': 500,
                'gold': 1000,
                'platinum': 2000
            }
        }
        
    async def initialize(self) -> None:
        """Initialize gamification resources."""
        await super().initialize()
        self._load_achievements()
        self._load_badges()
        
    def _load_achievements(self) -> None:
        """Load achievements specific to business unit."""
        self.achievements = {
            'first_message': {
                'name': 'Bienvenido',
                'description': 'Enviar primer mensaje',
                'points': 5
            },
            'first_application': {
                'name': 'Aplicante',
                'description': 'Primera aplicación',
                'points': 25
            },
            'first_interview': {
                'name': 'Entrevistado',
                'description': 'Primera entrevista',
                'points': 50
            }
        }
        
    def _load_badges(self) -> None:
        """Load badges specific to business unit."""
        self.badges = {
            'bronze': {
                'name': 'Bronce',
                'points_required': 100,
                'description': 'Primeros pasos'
            },
            'silver': {
                'name': 'Plata',
                'points_required': 500,
                'description': 'Activo'
            },
            'gold': {
                'name': 'Oro',
                'points_required': 1000,
                'description': 'Comprometido'
            }
        }
        
    async def track_progress(self, person: Person, action: str) -> Dict:
        """Track user progress and unlock achievements."""
        if person.id not in self.progress:
            self.progress[person.id] = {
                'points': 0,
                'achievements': [],
                'badges': []
            }
            
        # Update points
        points = self.config['points_per_action'].get(action, 0)
        self.progress[person.id]['points'] += points
        
        # Check achievements
        for achievement_id, achievement in self.achievements.items():
            if achievement_id not in self.progress[person.id]['achievements']:
                # Add achievement if conditions met
                self.progress[person.id]['achievements'].append(achievement_id)
                
        # Check badges
        for badge_id, badge in self.badges.items():
            if (badge_id not in self.progress[person.id]['badges'] and
                self.progress[person.id]['points'] >= badge['points_required']):
                self.progress[person.id]['badges'].append(badge_id)
                
        return self.progress[person.id]
        
    async def generate_rewards(self, person: Person) -> List[Dict]:
        """Generate rewards based on achievements."""
        rewards = []
        if person.id in self.progress:
            points = self.progress[person.id]['points']
            badges = self.progress[person.id]['badges']
            
            # Generate rewards based on points and badges
            if points >= 1000:
                rewards.append({
                    'type': 'discount',
                    'value': 10,
                    'description': '10% de descuento'
                })
                
            if 'gold' in badges:
                rewards.append({
                    'type': 'priority',
                    'value': 'high',
                    'description': 'Prioridad alta'
                })
                
        return rewards
        
    async def process_event(self, event_type: str, data: Dict) -> Dict:
        """Process gamification events."""
        if event_type == 'user_action':
            person = await Person.objects.aget(id=data['person_id'])
            return await self.track_progress(person, data['action'])
            
        return {}
