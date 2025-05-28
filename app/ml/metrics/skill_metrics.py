from typing import Dict, List, Optional
import numpy as np
from sklearn.metrics import precision_recall_fscore_support
import logging

logger = logging.getLogger(__name__)

class SkillMetrics:
    """Clase para calcular métricas específicas para skills"""
    
    def __init__(self):
        self.metrics = {
            'basic': ['accuracy', 'precision', 'recall', 'f1'],
            'advanced': [
                'skill_coverage',
                'skill_relevance',
                'skill_diversity',
                'skill_hierarchy_match'
            ]
        }

    def calculate_basic_metrics(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict:
        """Calcula métricas básicas de clasificación"""
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_true, 
            y_pred, 
            average='weighted'
        )
        
        accuracy = np.mean(y_true == y_pred)
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1
        }

    def calculate_skill_coverage(self, 
                               predicted_skills: List[str],
                               required_skills: List[str]) -> Dict:
        """Calcula la cobertura de skills requeridos"""
        predicted_set = set(predicted_skills)
        required_set = set(required_skills)
        
        covered = predicted_set.intersection(required_set)
        missing = required_set - predicted_set
        extra = predicted_set - required_set
        
        coverage_ratio = len(covered) / len(required_set) if required_set else 0
        
        return {
            'coverage_ratio': coverage_ratio,
            'covered_skills': list(covered),
            'missing_skills': list(missing),
            'extra_skills': list(extra)
        }

    def calculate_skill_relevance(self,
                                predicted_skills: List[str],
                                skill_weights: Dict[str, float]) -> Dict:
        """Calcula la relevancia de los skills predichos"""
        total_weight = sum(skill_weights.values())
        predicted_weight = sum(
            skill_weights.get(skill, 0)
            for skill in predicted_skills
        )
        
        relevance_score = predicted_weight / total_weight if total_weight > 0 else 0
        
        return {
            'relevance_score': relevance_score,
            'weighted_skills': {
                skill: skill_weights.get(skill, 0)
                for skill in predicted_skills
            }
        }

    def calculate_skill_diversity(self,
                                predicted_skills: List[str],
                                skill_categories: Dict[str, str]) -> Dict:
        """Calcula la diversidad de skills predichos"""
        category_counts = {}
        for skill in predicted_skills:
            category = skill_categories.get(skill, 'unknown')
            category_counts[category] = category_counts.get(category, 0) + 1
            
        total_skills = len(predicted_skills)
        diversity_scores = {
            category: count / total_skills
            for category, count in category_counts.items()
        }
        
        # Calcular índice de diversidad (1 - concentración)
        concentration = sum(score ** 2 for score in diversity_scores.values())
        diversity_index = 1 - concentration
        
        return {
            'diversity_index': diversity_index,
            'category_distribution': diversity_scores,
            'total_categories': len(category_counts)
        }

    def calculate_skill_hierarchy_match(self,
                                      predicted_skills: List[str],
                                      skill_hierarchy: Dict[str, List[str]]) -> Dict:
        """Calcula la coherencia jerárquica de los skills predichos"""
        hierarchy_scores = {}
        
        for skill in predicted_skills:
            if skill in skill_hierarchy:
                prerequisites = skill_hierarchy[skill]
                missing_prerequisites = [
                    prereq for prereq in prerequisites
                    if prereq not in predicted_skills
                ]
                
                hierarchy_scores[skill] = {
                    'has_prerequisites': len(missing_prerequisites) == 0,
                    'missing_prerequisites': missing_prerequisites,
                    'completeness': 1 - (len(missing_prerequisites) / len(prerequisites))
                    if prerequisites else 1
                }
        
        overall_score = np.mean([
            score['completeness']
            for score in hierarchy_scores.values()
        ]) if hierarchy_scores else 0
        
        return {
            'overall_hierarchy_score': overall_score,
            'skill_scores': hierarchy_scores
        }

    def calculate_all_metrics(self,
                            y_true: np.ndarray,
                            y_pred: np.ndarray,
                            predicted_skills: List[str],
                            required_skills: List[str],
                            skill_weights: Dict[str, float],
                            skill_categories: Dict[str, str],
                            skill_hierarchy: Dict[str, List[str]]) -> Dict:
        """Calcula todas las métricas disponibles"""
        try:
            basic_metrics = self.calculate_basic_metrics(y_true, y_pred)
            coverage_metrics = self.calculate_skill_coverage(
                predicted_skills, 
                required_skills
            )
            relevance_metrics = self.calculate_skill_relevance(
                predicted_skills,
                skill_weights
            )
            diversity_metrics = self.calculate_skill_diversity(
                predicted_skills,
                skill_categories
            )
            hierarchy_metrics = self.calculate_skill_hierarchy_match(
                predicted_skills,
                skill_hierarchy
            )
            
            return {
                'status': 'success',
                'basic_metrics': basic_metrics,
                'coverage_metrics': coverage_metrics,
                'relevance_metrics': relevance_metrics,
                'diversity_metrics': diversity_metrics,
                'hierarchy_metrics': hierarchy_metrics,
                'overall_score': np.mean([
                    basic_metrics['f1_score'],
                    coverage_metrics['coverage_ratio'],
                    relevance_metrics['relevance_score'],
                    diversity_metrics['diversity_index'],
                    hierarchy_metrics['overall_hierarchy_score']
                ])
            }
            
        except Exception as e:
            logger.error(f"Error calculando métricas: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            } 