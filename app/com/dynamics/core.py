from typing import Dict, Any, Optional, List, Type
import logging
from django.db import models
from app.models import BusinessUnit

logger = logging.getLogger(__name__)

class DynamicModule:
    """Base class for all dynamic modules."""
    
    def __init__(self, business_unit: BusinessUnit):
        self.business_unit = business_unit
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        """Load module-specific configuration."""
        return {}
        
    async def initialize(self) -> None:
        """Initialize module resources."""
        pass
        
    async def cleanup(self) -> None:
        """Clean up module resources."""
        pass

class DynamicsManager:
    """Central manager for all dynamic modules."""
    
    def __init__(self, business_unit: BusinessUnit):
        self.business_unit = business_unit
        self.modules: Dict[str, DynamicModule] = {}
        self._module_classes = {
            'nlp': EnhancedNLPProcessor,
            'gamification': GamificationSystem,
            'analytics': EnhancedAnalytics,
            'feedback': FeedbackSystem,
            'ai_assistant': AIAssistant,
            'optimization': PerformanceOptimizer,
            'security': SecurityManager,
            'integrations': IntegrationSystem,
            'talent_analytics': TalentAnalytics
        }
        self._load_config()
        
    def _load_config(self) -> None:
        """Load configuration for all modules."""
        bu_config = BusinessUnit.objects.get(name=self.business_unit.name).config
        self.config = {
            'enabled_modules': bu_config.get('enabled_modules', []),
            'module_settings': bu_config.get('module_settings', {})
        }
        
    async def get_module(self, name: str) -> Optional[DynamicModule]:
        """Lazy initialization of modules."""
        if name not in self.modules:
            if name in self._module_classes:
                # Verificar si el módulo está habilitado para este BU
                if name not in self.config['enabled_modules']:
                    logger.warning(f"Module {name} not enabled for {self.business_unit.name}")
                    return None
                    
                module_class = self._module_classes[name]
                module = module_class(self.business_unit)
                await module.initialize()
                self.modules[name] = module
            else:
                return None
        return self.modules[name]
        
    async def initialize(self) -> None:
        """Initialize only enabled modules."""
        for name in self.config['enabled_modules']:
            if name in self._module_classes:
                module = await self.get_module(name)
                if module:
                    await module.initialize()
        
    async def cleanup(self) -> None:
        """Clean up all initialized modules."""
        for module in self.modules.values():
            await module.cleanup()
            
    async def process_event(self, event_type: str, data: Dict) -> Dict:
        """Process an event through all relevant modules."""
        results = {}
        for name in self.config['enabled_modules']:
            module = self.modules.get(name)
            if module and hasattr(module, f'process_{event_type}'):
                try:
                    result = await getattr(module, f'process_{event_type}')(data)
                    results[name] = result
                except Exception as e:
                    logger.error(f"Error processing {event_type} in {name}: {str(e)}")
        return results
        
    async def register_module(self, name: str, module_class: Type[DynamicModule]) -> None:
        """Register a new module."""
        if name in self._module_classes:
            logger.warning(f"Module {name} already registered")
            return
            
        self._module_classes[name] = module_class
        if name in self.config['enabled_modules']:
            try:
                module = module_class(self.business_unit)
                await module.initialize()
                self.modules[name] = module
            except Exception as e:
                logger.error(f"Failed to register module {name}: {str(e)}")
                
    async def unregister_module(self, name: str) -> None:
        """Unregister a module."""
        if name in self.modules:
            module = self.modules[name]
            await module.cleanup()
            del self.modules[name]
            
    async def analyze_talent(self, messages: List[Dict]) -> Dict:
        """Analyze talent profile from messages."""
        talent_analytics = await self.get_module('talent_analytics')
        if talent_analytics:
            return await talent_analytics.extract_talent_profile(messages)
        return {}
        
    async def calculate_match(self, talent_id: int, job_id: int) -> Dict:
        """Calculate match score between talent and job."""
        talent_analytics = await self.get_module('talent_analytics')
        if talent_analytics:
            return await talent_analytics.calculate_match_score(talent_id, job_id)
        return {'score': 0.0, 'details': {} }
        
    async def get_top_matches(self, job_id: int, limit: int = 5) -> List[Dict]:
        """Get top matches for a job."""
        talent_analytics = await self.get_module('talent_analytics')
        if talent_analytics:
            return await talent_analytics.get_top_matches(job_id, limit)
        return []
        
    async def initialize(self) -> None:
        """Initialize all modules."""
        for module in self.modules.values():
            await module.initialize()
        
    async def cleanup(self) -> None:
        """Clean up all modules."""
        for module in self.modules.values():
            await module.cleanup()
            
    def get_module(self, name: str) -> Optional[DynamicModule]:
        """Get a specific module by name."""
        return self.modules.get(name)
        
    async def process_event(self, event_type: str, data: Dict) -> Dict:
        """Process an event through all relevant modules."""
        results = {}
        for module_name, module in self.modules.items():
            if hasattr(module, f'process_{event_type}'):
                try:
                    result = await getattr(module, f'process_{event_type}')(data)
                    results[module_name] = result
                except Exception as e:
                    logger.error(f"Error processing {event_type} in {module_name}: {str(e)}")
        return results
        
    def register_module(self, name: str, module_class: Type[DynamicModule]) -> None:
        """Register a new module."""
        if name in self.modules:
            logger.warning(f"Module {name} already registered")
            return
            
        try:
            module = module_class(self.business_unit)
            self.modules[name] = module
            await module.initialize()
        except Exception as e:
            logger.error(f"Failed to register module {name}: {str(e)}")
            
    def unregister_module(self, name: str) -> None:
        """Unregister a module."""
        if name not in self.modules:
            return
            
        module = self.modules[name]
        await module.cleanup()
        del self.modules[name]
