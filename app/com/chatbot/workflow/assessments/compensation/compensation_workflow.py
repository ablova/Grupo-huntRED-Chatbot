# app/com/chatbot/workflow/assessments/compensation/compensation_workflow.py
import logging
import asyncio
from typing import Dict, Any, Optional, List
from django.core.cache import cache
from asgiref.sync import sync_to_async

# Importar el analizador centralizado
from app.ml.analyzers import SalaryAnalyzer
from app.models import Person, BusinessUnit

logger = logging.getLogger(__name__)

class CompensationAssessment:
    """Clase para manejar la evaluación de compensación y beneficios."""
    
    # Preguntas del assessment organizadas por categoría
    ASSESSMENT_QUESTIONS = {
        'salary_satisfaction': [
            {
                'text': '¿Qué tan satisfecho estás con tu salario actual?',
                'options': ['1 - Muy insatisfecho', '2 - Insatisfecho', '3 - Neutral', '4 - Satisfecho', '5 - Muy satisfecho']
            },
            {
                'text': '¿Consideras que tu salario es competitivo en el mercado laboral?',
                'options': ['1 - Nada competitivo', '2 - Poco competitivo', '3 - En el promedio', '4 - Competitivo', '5 - Muy competitivo']
            },
            {
                'text': '¿Tu salario refleja adecuadamente tu experiencia y habilidades?',
                'options': ['1 - Nada adecuado', '2 - Poco adecuado', '3 - Neutral', '4 - Adecuado', '5 - Muy adecuado']
            }
        ],
        'benefits_satisfaction': [
            {
                'text': '¿Cómo calificas el paquete de beneficios de tu empresa actual?',
                'options': ['1 - Muy pobre', '2 - Pobre', '3 - Adecuado', '4 - Bueno', '5 - Excelente']
            },
            {
                'text': '¿Qué tan importantes son los beneficios no monetarios en tu decisión de permanecer en una empresa?',
                'options': ['1 - Nada importantes', '2 - Poco importantes', '3 - Moderadamente importantes', '4 - Importantes', '5 - Muy importantes']
            }
        ],
        'compensation_equity': [
            {
                'text': '¿Consideras que existe equidad salarial en tu organización?',
                'options': ['1 - Nada equitativo', '2 - Poco equitativo', '3 - Neutral', '4 - Equitativo', '5 - Muy equitativo']
            },
            {
                'text': '¿Qué tan transparentes son las políticas de compensación en tu empresa?',
                'options': ['1 - Nada transparentes', '2 - Poco transparentes', '3 - Neutral', '4 - Transparentes', '5 - Muy transparentes']
            }
        ],
        'growth_opportunities': [
            {
                'text': '¿Cómo evalúas las oportunidades de crecimiento salarial en tu posición actual?',
                'options': ['1 - Muy limitadas', '2 - Limitadas', '3 - Moderadas', '4 - Buenas', '5 - Excelentes']
            },
            {
                'text': '¿Qué tan claras son las métricas o criterios para obtener aumentos salariales?',
                'options': ['1 - Nada claras', '2 - Poco claras', '3 - Neutral', '4 - Claras', '5 - Muy claras']
            }
        ],
        'additional_info': [
            {
                'text': '¿Cuál es tu salario bruto mensual actual en moneda local?',
                'type': 'numeric'
            },
            {
                'text': '¿Qué beneficios no monetarios valoras más? (selecciona hasta 3)',
                'type': 'multiple_choice',
                'options': [
                    'Seguro médico privado', 
                    'Plan de pensiones/jubilación', 
                    'Horario flexible', 
                    'Trabajo remoto', 
                    'Días adicionales de vacaciones',
                    'Bonos por desempeño',
                    'Desarrollo profesional/capacitación',
                    'Gimnasio/actividades recreativas',
                    'Servicio de comedor/alimentación',
                    'Transporte/estacionamiento'
                ],
                'max_selections': 3
            },
            {
                'text': '¿Cuál sería tu expectativa salarial para tu próxima posición?',
                'type': 'numeric'
            }
        ]
    }
    
    # Preguntas específicas por unidad de negocio
    BU_SPECIFIC_QUESTIONS = {
        'huntRED': [
            {
                'text': '¿Qué componente de compensación variable considerarías más atractivo?',
                'options': [
                    'Bonos por cumplimiento de objetivos',
                    'Comisiones por colocación de candidatos',
                    'Participación en utilidades',
                    'Stock options/acciones',
                    'Bonos por retención de clientes'
                ]
            }
        ],
        'huntU': [
            {
                'text': '¿Qué beneficio educativo valorarías más en tu paquete de compensación?',
                'options': [
                    'Becas para estudios de posgrado',
                    'Cursos especializados pagados',
                    'Certificaciones profesionales',
                    'Tiempo libre para estudios',
                    'Mentorías con ejecutivos'
                ]
            }
        ],
        'Amigro': [
            {
                'text': '¿Qué tipo de incentivo te motivaría más en un rol de colocación de migrantes?',
                'options': [
                    'Bonos por número de colocaciones',
                    'Comisión por satisfacción del empleador',
                    'Incentivos por seguimiento post-colocación',
                    'Bonos por diversidad de industrias',
                    'Comisión por permanencia del trabajador'
                ]
            }
        ]
    }
    
    def __init__(self):
        self.salary_analyzer = SalaryAnalyzer()
    
    def get_questions(self, category=None, business_unit=None):
        """
        Obtiene las preguntas del assessment, filtradas por categoría y/o unidad de negocio.
        
        Args:
            category: Categoría de preguntas a obtener
            business_unit: Unidad de negocio para obtener preguntas específicas
            
        Returns:
            Lista de preguntas del assessment
        """
        if category and category in self.ASSESSMENT_QUESTIONS:
            questions = self.ASSESSMENT_QUESTIONS[category]
        else:
            # Si no se especifica categoría, devolver todas las preguntas
            questions = []
            for cat_questions in self.ASSESSMENT_QUESTIONS.values():
                questions.extend(cat_questions)
        
        # Añadir preguntas específicas de la unidad de negocio si aplica
        if business_unit and business_unit in self.BU_SPECIFIC_QUESTIONS:
            questions.extend(self.BU_SPECIFIC_QUESTIONS[business_unit])
            
        return questions
    
    async def analyze_responses_async(self, responses: dict, person_id: int, business_unit: str = None) -> dict:
        """
        Analiza las respuestas del assessment de compensación de manera asíncrona.
        
        Args:
            responses: Diccionario con las respuestas del usuario
            person_id: ID de la persona evaluada
            business_unit: Unidad de negocio para contextualizar el análisis
            
        Returns:
            Dict con resultados del análisis de compensación
        """
        # Verificar caché primero (validez de 7 días para datos salariales)
        cache_key = f"compensation_assessment_{person_id}_{business_unit}"
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f"Usando resultados en caché para assessment de compensación: {person_id}")
            return cached_result
        
        try:
            # Obtener la persona de la base de datos
            person = await self._get_person_async(person_id)
            if not person:
                logger.error(f"Persona no encontrada: {person_id}")
                return {"status": "error", "message": "Persona no encontrada"}
            
            # Preparar datos para el analizador
            analysis_data = {
                'assessment_type': 'compensation',
                'responses': responses,
                'person_id': person_id
            }
            
            # Obtener análisis del SalaryAnalyzer
            salary_analysis = await self.salary_analyzer.analyze_async(person, business_unit)
            
            # Combinar con nuestro análisis de las respuestas del assessment
            satisfaction_scores = self._calculate_satisfaction_scores(responses)
            market_position = self._determine_market_position(responses, salary_analysis)
            retention_risk = self._calculate_retention_risk(satisfaction_scores, market_position)
            
            # Formar resultado final
            result = {
                'status': 'success',
                'satisfaction_scores': satisfaction_scores,
                'market_position': market_position,
                'retention_risk': retention_risk,
                'salary_analysis': salary_analysis,
                'recommendations': self._generate_recommendations(
                    satisfaction_scores, 
                    market_position, 
                    retention_risk, 
                    salary_analysis
                )
            }
            
            # Guardar en caché por 7 días
            cache.set(cache_key, result, 60 * 60 * 24 * 7)
            
            return result
            
        except Exception as e:
            logger.error(f"Error en análisis de compensación: {str(e)}")
            return {
                "status": "error", 
                "message": f"Error en análisis: {str(e)}"
            }
    
    def analyze_responses(self, responses: dict, person_id: int, business_unit: str = None) -> dict:
        """
        Versión síncrona del método analyze_responses_async para compatibilidad.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.analyze_responses_async(responses, person_id, business_unit)
            )
        finally:
            loop.close()
    
    @sync_to_async
    def _get_person_async(self, person_id: int) -> Optional[Person]:
        """Obtiene una persona de la base de datos de manera asíncrona."""
        try:
            return Person.objects.get(id=person_id)
        except Person.DoesNotExist:
            return None
    
    def _calculate_satisfaction_scores(self, responses: dict) -> dict:
        """
        Calcula puntuaciones de satisfacción basadas en las respuestas.
        """
        scores = {
            'salary': 0,
            'benefits': 0,
            'equity': 0,
            'growth': 0,
            'overall': 0
        }
        
        # Procesar respuestas de satisfacción salarial
        if 'salary_satisfaction' in responses:
            salary_responses = responses['salary_satisfaction']
            scores['salary'] = sum(salary_responses) / len(salary_responses)
        
        # Procesar respuestas de satisfacción con beneficios
        if 'benefits_satisfaction' in responses:
            benefit_responses = responses['benefits_satisfaction']
            scores['benefits'] = sum(benefit_responses) / len(benefit_responses)
        
        # Procesar respuestas de equidad
        if 'compensation_equity' in responses:
            equity_responses = responses['compensation_equity']
            scores['equity'] = sum(equity_responses) / len(equity_responses)
        
        # Procesar respuestas de crecimiento
        if 'growth_opportunities' in responses:
            growth_responses = responses['growth_opportunities']
            scores['growth'] = sum(growth_responses) / len(growth_responses)
        
        # Calcular puntuación general ponderada
        weights = {'salary': 0.4, 'benefits': 0.2, 'equity': 0.2, 'growth': 0.2}
        total_weight = sum(weights.values())
        
        weighted_sum = 0
        for category, weight in weights.items():
            if scores[category] > 0:  # Solo considerar categorías con respuestas
                weighted_sum += scores[category] * weight
        
        scores['overall'] = weighted_sum / total_weight if total_weight > 0 else 0
        
        return scores
    
    def _determine_market_position(self, responses: dict, salary_analysis: dict) -> dict:
        """
        Determina la posición en el mercado basado en respuestas y análisis salarial.
        """
        position = {
            'percentile': 0,
            'category': 'unknown',
            'gap_percentage': 0
        }
        
        # Obtener salario actual de las respuestas
        current_salary = 0
        if 'additional_info' in responses:
            for item in responses['additional_info']:
                if isinstance(item, dict) and 'salary' in item:
                    current_salary = item['salary']
                    break
        
        # Si no hay salario en las respuestas pero sí en el análisis, usarlo
        if current_salary == 0 and 'current_salary' in salary_analysis:
            current_salary = salary_analysis['current_salary']
        
        # Si tenemos datos de mercado y salario actual, calcular posición
        if current_salary > 0 and 'market_data' in salary_analysis:
            market_data = salary_analysis['market_data']
            
            # Determinar percentil aproximado
            percentiles = market_data.get('percentiles', {})
            position['percentile'] = self._estimate_percentile(current_salary, percentiles)
            
            # Categorizar posición en el mercado
            if position['percentile'] < 25:
                position['category'] = 'below_market'
            elif position['percentile'] < 75:
                position['category'] = 'at_market'
            else:
                position['category'] = 'above_market'
            
            # Calcular brecha porcentual con la media del mercado
            market_avg = market_data.get('average', 0)
            if market_avg > 0:
                position['gap_percentage'] = ((current_salary - market_avg) / market_avg) * 100
        
        return position
    
    def _estimate_percentile(self, salary: float, percentiles: dict) -> float:
        """
        Estima el percentil aproximado de un salario dado.
        """
        if not percentiles:
            return 50  # Valor por defecto si no hay datos
        
        # Convertir claves de percentiles a números
        num_percentiles = {float(k): v for k, v in percentiles.items()}
        
        # Ordenar percentiles
        sorted_percentiles = sorted(num_percentiles.items())
        
        # Si el salario es menor que el percentil más bajo
        if salary <= sorted_percentiles[0][1]:
            return sorted_percentiles[0][0] * (salary / sorted_percentiles[0][1])
        
        # Si el salario es mayor que el percentil más alto
        if salary >= sorted_percentiles[-1][1]:
            return sorted_percentiles[-1][0] + (100 - sorted_percentiles[-1][0]) * min(1, (salary - sorted_percentiles[-1][1]) / sorted_percentiles[-1][1])
        
        # Interpolar entre percentiles
        for i in range(len(sorted_percentiles) - 1):
            p1, s1 = sorted_percentiles[i]
            p2, s2 = sorted_percentiles[i + 1]
            
            if s1 <= salary <= s2:
                # Interpolación lineal
                return p1 + (p2 - p1) * ((salary - s1) / (s2 - s1))
        
        return 50  # Fallback
    
    def _calculate_retention_risk(self, satisfaction_scores: dict, market_position: dict) -> dict:
        """
        Calcula el riesgo de retención basado en satisfacción y posición de mercado.
        """
        risk = {
            'level': 'medium',  # bajo, medio, alto
            'score': 5,         # 1-10, donde 10 es el riesgo más alto
            'factors': []       # factores que contribuyen al riesgo
        }
        
        # Base score from overall satisfaction (inverted: lower satisfaction = higher risk)
        base_risk = 10 - (satisfaction_scores['overall'] * 2)  # Convertir escala 1-5 a escala de riesgo 0-10
        
        # Adjust for market position
        position_adjustment = 0
        if market_position['category'] == 'below_market':
            position_adjustment = 2  # Aumenta riesgo si está por debajo del mercado
            risk['factors'].append('Salario por debajo del mercado')
        elif market_position['category'] == 'above_market':
            position_adjustment = -1  # Reduce riesgo si está por encima del mercado
        
        # Check for specific risk factors
        if satisfaction_scores['salary'] < 3:
            risk['factors'].append('Baja satisfacción salarial')
        
        if satisfaction_scores['growth'] < 2.5:
            risk['factors'].append('Percepción limitada de crecimiento')
            position_adjustment += 1
        
        if satisfaction_scores['equity'] < 2:
            risk['factors'].append('Percepción de inequidad salarial')
            position_adjustment += 1.5
        
        # Calculate final risk score
        risk['score'] = min(10, max(1, base_risk + position_adjustment))
        
        # Determine risk level
        if risk['score'] < 4:
            risk['level'] = 'bajo'
        elif risk['score'] < 7:
            risk['level'] = 'medio'
        else:
            risk['level'] = 'alto'
        
        return risk
    
    def _generate_recommendations(self, satisfaction: dict, market_position: dict, 
                                retention_risk: dict, salary_analysis: dict) -> List[Dict]:
        """
        Genera recomendaciones accionables basadas en el análisis.
        """
        recommendations = []
        
        # Recomendaciones basadas en posición de mercado
        if market_position['category'] == 'below_market' and market_position['gap_percentage'] < -15:
            recommendations.append({
                'priority': 'alta',
                'category': 'compensación',
                'action': 'Revisar y ajustar salario actual para acercarse al menos al percentil 25 del mercado',
                'reason': f'Salario actual está {abs(market_position["gap_percentage"]):.1f}% por debajo de la media del mercado'
            })
        elif market_position['category'] == 'below_market':
            recommendations.append({
                'priority': 'media',
                'category': 'compensación',
                'action': 'Considerar un ajuste salarial en el próximo ciclo de revisión',
                'reason': 'Salario ligeramente por debajo del mercado'
            })
            
        # Recomendaciones basadas en satisfacción
        if satisfaction['benefits'] < 3 and satisfaction['salary'] > 3:
            recommendations.append({
                'priority': 'media',
                'category': 'beneficios',
                'action': 'Enriquecer el paquete de beneficios no monetarios',
                'reason': 'Satisfacción salarial adecuada pero baja satisfacción con beneficios'
            })
            
        if satisfaction['equity'] < 2.5:
            recommendations.append({
                'priority': 'alta',
                'category': 'equidad',
                'action': 'Revisar políticas de equidad salarial y transparencia',
                'reason': 'Baja percepción de equidad que puede afectar el compromiso'
            })
            
        if satisfaction['growth'] < 3:
            recommendations.append({
                'priority': 'media',
                'category': 'desarrollo',
                'action': 'Establecer plan claro de crecimiento salarial ligado a desempeño',
                'reason': 'Percepción limitada de oportunidades de crecimiento'
            })
            
        # Recomendaciones basadas en riesgo de retención
        if retention_risk['level'] == 'alto':
            recommendations.append({
                'priority': 'crítica',
                'category': 'retención',
                'action': 'Implementar plan de retención personalizado',
                'reason': f'Alto riesgo de rotación: {", ".join(retention_risk["factors"])}'
            })
        
        # Si no hay recomendaciones (todo está bien), añadir una genérica
        if not recommendations:
            recommendations.append({
                'priority': 'baja',
                'category': 'mantenimiento',
                'action': 'Mantener estructura de compensación actual',
                'reason': 'Buena posición en el mercado y satisfacción adecuada'
            })
            
        return recommendations
