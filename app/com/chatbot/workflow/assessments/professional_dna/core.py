from typing import Dict, List, Optional
from ....core.workflow import Workflow
from ....core.states import State
from ....core.actions import Action
from ....core.conditions import Condition
from ....core.metrics import Metric
from ....core.events import Event
from .questions import ProfessionalDNAQuestions, QuestionCategory

class ProfessionalDNAWorkflow(Workflow):
    def __init__(self):
        super().__init__()
        self.name = "professional_dna"
        self.description = "Workflow para evaluación de Professional DNA"
        self.questions = ProfessionalDNAQuestions()
        
        # Definir estados del workflow
        self.states = {
            'start': State('start', 'Inicio de la evaluación Professional DNA'),
            'leadership': State('leadership', 'Evaluación de liderazgo'),
            'innovation': State('innovation', 'Evaluación de innovación'),
            'communication': State('communication', 'Evaluación de comunicación'),
            'resilience': State('resilience', 'Evaluación de resiliencia'),
            'results': State('results', 'Evaluación de resultados'),
            'analysis': State('analysis', 'Análisis de resultados'),
            'end': State('end', 'Finalización de la evaluación')
        }
        
        # Definir acciones
        self.actions = {
            'start_evaluation': Action(
                name='start_evaluation',
                description='Iniciar la evaluación',
                handler=self._handle_start_evaluation
            ),
            'process_leadership': Action(
                name='process_leadership',
                description='Procesar respuestas de liderazgo',
                handler=self._handle_process_leadership
            ),
            'process_innovation': Action(
                name='process_innovation',
                description='Procesar respuestas de innovación',
                handler=self._handle_process_innovation
            ),
            'process_communication': Action(
                name='process_communication',
                description='Procesar respuestas de comunicación',
                handler=self._handle_process_communication
            ),
            'process_resilience': Action(
                name='process_resilience',
                description='Procesar respuestas de resiliencia',
                handler=self._handle_process_resilience
            ),
            'process_results': Action(
                name='process_results',
                description='Procesar respuestas de resultados',
                handler=self._handle_process_results
            ),
            'analyze_results': Action(
                name='analyze_results',
                description='Analizar resultados completos',
                handler=self._handle_analyze_results
            )
        }
        
        # Definir condiciones
        self.conditions = {
            'has_leadership_answers': Condition(
                name='has_leadership_answers',
                description='Verifica si se tienen respuestas de liderazgo',
                handler=self._check_has_leadership_answers
            ),
            'has_innovation_answers': Condition(
                name='has_innovation_answers',
                description='Verifica si se tienen respuestas de innovación',
                handler=self._check_has_innovation_answers
            ),
            'has_communication_answers': Condition(
                name='has_communication_answers',
                description='Verifica si se tienen respuestas de comunicación',
                handler=self._check_has_communication_answers
            ),
            'has_resilience_answers': Condition(
                name='has_resilience_answers',
                description='Verifica si se tienen respuestas de resiliencia',
                handler=self._check_has_resilience_answers
            ),
            'has_results_answers': Condition(
                name='has_results_answers',
                description='Verifica si se tienen respuestas de resultados',
                handler=self._check_has_results_answers
            )
        }
        
        # Definir métricas
        self.metrics = {
            'completion_rate': Metric(
                name='completion_rate',
                description='Tasa de completitud de la evaluación',
                handler=self._calculate_completion_rate
            ),
            'category_scores': Metric(
                name='category_scores',
                description='Puntuaciones por categoría',
                handler=self._calculate_category_scores
            )
        }
        
        # Definir eventos
        self.events = {
            'evaluation_started': Event('evaluation_started', 'Evaluación iniciada'),
            'category_completed': Event('category_completed', 'Categoría completada'),
            'evaluation_completed': Event('evaluation_completed', 'Evaluación completada'),
            'analysis_completed': Event('analysis_completed', 'Análisis completado')
        }
        
        # Configurar transiciones
        self._setup_transitions()
    
    def _setup_transitions(self):
        """Configura las transiciones entre estados"""
        self.add_transition(
            from_state='start',
            to_state='leadership',
            action='start_evaluation',
            condition=None
        )
        
        self.add_transition(
            from_state='leadership',
            to_state='innovation',
            action='process_leadership',
            condition='has_leadership_answers'
        )
        
        self.add_transition(
            from_state='innovation',
            to_state='communication',
            action='process_innovation',
            condition='has_innovation_answers'
        )
        
        self.add_transition(
            from_state='communication',
            to_state='resilience',
            action='process_communication',
            condition='has_communication_answers'
        )
        
        self.add_transition(
            from_state='resilience',
            to_state='results',
            action='process_resilience',
            condition='has_resilience_answers'
        )
        
        self.add_transition(
            from_state='results',
            to_state='analysis',
            action='process_results',
            condition='has_results_answers'
        )
        
        self.add_transition(
            from_state='analysis',
            to_state='end',
            action='analyze_results',
            condition=None
        )
    
    async def _handle_start_evaluation(self, context: Dict) -> Dict:
        """Maneja el inicio de la evaluación"""
        self.events['evaluation_started'].trigger()
        questions = self.questions.get_questions_by_category(QuestionCategory.LEADERSHIP)
        return {
            'status': 'success',
            'message': 'Iniciando evaluación Professional DNA',
            'questions': questions,
            'next_state': 'leadership'
        }
    
    async def _handle_process_leadership(self, context: Dict) -> Dict:
        """Maneja el procesamiento de respuestas de liderazgo"""
        self.events['category_completed'].trigger()
        questions = self.questions.get_questions_by_category(QuestionCategory.INNOVATION)
        return {
            'status': 'success',
            'message': 'Procesando respuestas de liderazgo',
            'questions': questions,
            'next_state': 'innovation'
        }
    
    # ... (implementar el resto de handlers)
    
    def _check_has_leadership_answers(self, context: Dict) -> bool:
        """Verifica si se tienen respuestas de liderazgo"""
        return bool(context.get('leadership_answers'))
    
    # ... (implementar el resto de checkers)
    
    def _calculate_completion_rate(self, context: Dict) -> float:
        """Calcula la tasa de completitud"""
        total_questions = len(self.questions.get_all_questions())
        answered_questions = sum(1 for category in QuestionCategory 
                               if context.get(f'{category.value}_answers'))
        return answered_questions / total_questions if total_questions > 0 else 0.0
    
    def _calculate_category_scores(self, context: Dict) -> Dict[str, float]:
        """Calcula las puntuaciones por categoría"""
        scores = {}
        for category in QuestionCategory:
            answers = context.get(f'{category.value}_answers', {})
            if answers:
                category_questions = self.questions.get_questions_by_category(category)
                total_weight = sum(q.weights.get(answers.get(str(q.id), 'A'), 0) 
                                 for q in category_questions)
                scores[category.value] = total_weight / len(category_questions)
        return scores 