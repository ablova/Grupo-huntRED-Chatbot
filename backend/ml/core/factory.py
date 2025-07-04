"""
🚀 GhuntRED-v2 ML Factory
Central factory for ML analyzers with performance optimizations
"""

import logging
import threading
import time
from typing import Dict, Any, Optional
from django.conf import settings
from django.core.cache import cache

from .exceptions import MLException, ModelNotFound, PredictionError
from .metrics import MLMetrics

logger = logging.getLogger('ml')

class MLFactory:
    """Central factory for ML analyzers with thread safety and caching"""
    
    _instance = None
    _lock = threading.Lock()
    _analyzers = {}
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(MLFactory, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def initialize(cls):
        """Initialize ML models and analyzers"""
        if cls._initialized:
            return
        
        with cls._lock:
            if cls._initialized:
                return
            
            try:
                logger.info("🚀 Initializing ML Factory...")
                start_time = time.time()
                
                # Initialize GenIA analyzers
                cls._load_genia_analyzers()
                
                # Initialize AURA analyzers
                cls._load_aura_analyzers()
                
                # Initialize core analyzers
                cls._load_core_analyzers()
                
                init_time = time.time() - start_time
                logger.info(f"✅ ML Factory initialized in {init_time:.2f}s")
                cls._initialized = True
                
            except Exception as e:
                logger.error(f"❌ Failed to initialize ML Factory: {e}")
                raise MLException(f"Factory initialization failed: {e}")
    
    @classmethod
    def _load_genia_analyzers(cls):
        """Load GenIA analyzers"""
        try:
            from ..genia.skill_analyzer import SkillAnalyzer
            from ..genia.experience_analyzer import ExperienceAnalyzer
            from ..genia.resume_analyzer import ResumeAnalyzer
            from ..genia.matching_engine import MatchingEngine
            
            cls._analyzers.update({
                'skill_analyzer': SkillAnalyzer(),
                'experience_analyzer': ExperienceAnalyzer(),
                'resume_analyzer': ResumeAnalyzer(),
                'matching_engine': MatchingEngine(),
            })
            
            logger.info("✅ GenIA analyzers loaded")
            
        except ImportError as e:
            logger.warning(f"⚠️ GenIA analyzers not available: {e}")
    
    @classmethod
    def _load_aura_analyzers(cls):
        """Load AURA analyzers"""
        try:
            from ..aura.personality_analyzer import PersonalityAnalyzer
            from ..aura.compatibility_analyzer import CompatibilityAnalyzer
            from ..aura.vibrational_matcher import VibrationalMatcher
            from ..aura.holistic_assessor import HolisticAssessor
            
            cls._analyzers.update({
                'personality_analyzer': PersonalityAnalyzer(),
                'compatibility_analyzer': CompatibilityAnalyzer(),
                'vibrational_matcher': VibrationalMatcher(),
                'holistic_assessor': HolisticAssessor(),
            })
            
            logger.info("✅ AURA analyzers loaded")
            
        except ImportError as e:
            logger.warning(f"⚠️ AURA analyzers not available: {e}")
    
    @classmethod
    def _load_core_analyzers(cls):
        """Load core analyzers"""
        try:
            from .text_processor import TextProcessor
            from .feature_extractor import FeatureExtractor
            
            cls._analyzers.update({
                'text_processor': TextProcessor(),
                'feature_extractor': FeatureExtractor(),
            })
            
            logger.info("✅ Core analyzers loaded")
            
        except ImportError as e:
            logger.warning(f"⚠️ Core analyzers not available: {e}")
    
    def get_analyzer(self, analyzer_type: str):
        """Get analyzer instance with caching"""
        if not self._initialized:
            self.initialize()
        
        if analyzer_type not in self._analyzers:
            raise ModelNotFound(analyzer_type)
        
        return self._analyzers[analyzer_type]
    
    def analyze_candidate(self, candidate_data: dict, analysis_type: str = "full") -> dict:
        """Comprehensive candidate analysis"""
        try:
            start_time = time.time()
            results = {}
            
            if analysis_type in ["full", "genia"]:
                # GenIA Analysis
                results.update(self._run_genia_analysis(candidate_data))
            
            if analysis_type in ["full", "aura"]:
                # AURA Analysis
                results.update(self._run_aura_analysis(candidate_data))
            
            # Add performance metrics
            results['analysis_metadata'] = {
                'processing_time': time.time() - start_time,
                'analysis_type': analysis_type,
                'timestamp': time.time(),
            }
            
            # Record metrics
            MLMetrics.record_analysis(analysis_type, time.time() - start_time)
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Candidate analysis failed: {e}")
            raise PredictionError("candidate_analysis", str(e))
    
    def _run_genia_analysis(self, candidate_data: dict) -> dict:
        """Run GenIA analysis pipeline"""
        results = {}
        
        try:
            # Skills analysis
            if skills_analyzer := self.get_analyzer('skill_analyzer'):
                results['skills_analysis'] = skills_analyzer.analyze(candidate_data)
            
            # Experience analysis
            if exp_analyzer := self.get_analyzer('experience_analyzer'):
                results['experience_analysis'] = exp_analyzer.analyze(candidate_data)
            
            # Resume analysis
            if resume_analyzer := self.get_analyzer('resume_analyzer'):
                results['resume_analysis'] = resume_analyzer.analyze(candidate_data)
            
            # Calculate overall GenIA score
            results['genia_score'] = self._calculate_genia_score(results)
            
        except Exception as e:
            logger.warning(f"⚠️ GenIA analysis partial failure: {e}")
            results['genia_error'] = str(e)
        
        return results
    
    def _run_aura_analysis(self, candidate_data: dict) -> dict:
        """Run AURA analysis pipeline"""
        results = {}
        
        try:
            # Personality analysis
            if personality_analyzer := self.get_analyzer('personality_analyzer'):
                results['personality_analysis'] = personality_analyzer.analyze(candidate_data)
            
            # Compatibility analysis
            if compat_analyzer := self.get_analyzer('compatibility_analyzer'):
                results['compatibility_analysis'] = compat_analyzer.analyze(candidate_data)
            
            # Vibrational matching
            if vib_matcher := self.get_analyzer('vibrational_matcher'):
                results['vibrational_match'] = vib_matcher.analyze(candidate_data)
            
            # Holistic assessment
            if holistic_assessor := self.get_analyzer('holistic_assessor'):
                results['holistic_assessment'] = holistic_assessor.analyze(candidate_data)
            
            # Calculate overall AURA score
            results['aura_score'] = self._calculate_aura_score(results)
            
        except Exception as e:
            logger.warning(f"⚠️ AURA analysis partial failure: {e}")
            results['aura_error'] = str(e)
        
        return results
    
    def _calculate_genia_score(self, genia_results: dict) -> float:
        """Calculate overall GenIA score"""
        scores = []
        
        if 'skills_analysis' in genia_results:
            scores.append(genia_results['skills_analysis'].get('score', 0))
        
        if 'experience_analysis' in genia_results:
            scores.append(genia_results['experience_analysis'].get('score', 0))
        
        if 'resume_analysis' in genia_results:
            scores.append(genia_results['resume_analysis'].get('score', 0))
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _calculate_aura_score(self, aura_results: dict) -> float:
        """Calculate overall AURA score"""
        scores = []
        
        if 'personality_analysis' in aura_results:
            scores.append(aura_results['personality_analysis'].get('score', 0))
        
        if 'compatibility_analysis' in aura_results:
            scores.append(aura_results['compatibility_analysis'].get('score', 0))
        
        if 'vibrational_match' in aura_results:
            scores.append(aura_results['vibrational_match'].get('score', 0))
        
        if 'holistic_assessment' in aura_results:
            scores.append(aura_results['holistic_assessment'].get('score', 0))
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def get_available_analyzers(self) -> list:
        """Get list of available analyzers"""
        if not self._initialized:
            self.initialize()
        return list(self._analyzers.keys())
    
    def health_check(self) -> dict:
        """Perform health check on all analyzers"""
        if not self._initialized:
            self.initialize()
        
        health_status = {
            'status': 'healthy',
            'analyzers': {},
            'total_analyzers': len(self._analyzers),
            'healthy_analyzers': 0,
        }
        
        for name, analyzer in self._analyzers.items():
            try:
                # Simple health check - call a basic method
                if hasattr(analyzer, 'health_check'):
                    analyzer.health_check()
                health_status['analyzers'][name] = 'healthy'
                health_status['healthy_analyzers'] += 1
            except Exception as e:
                health_status['analyzers'][name] = f'unhealthy: {e}'
                health_status['status'] = 'degraded'
        
        if health_status['healthy_analyzers'] == 0:
            health_status['status'] = 'unhealthy'
        
        return health_status