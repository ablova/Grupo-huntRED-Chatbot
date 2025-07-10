# app/payroll/services/overhead_calculator.py
"""
Servicio de Cálculo de Overhead
Sistema completo de cálculo de overhead individual y grupal con ML y AURA
"""
import logging
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from django.db import transaction
from django.utils import timezone

from ..models import (
    PayrollEmployee, PayrollPeriod, PayrollCompany, 
    EmployeeOverheadCalculation, TeamOverheadAnalysis,
    OverheadCategory, OverheadBenchmark
)

logger = logging.getLogger(__name__)


class OverheadCalculatorService:
    """
    Servicio principal para cálculo de overhead individual y grupal
    """
    
    def __init__(self, company: PayrollCompany):
        self.company = company
        self.categories = self._load_overhead_categories()
        self.benchmarks = self._load_benchmarks()
    
    def _load_overhead_categories(self) -> Dict:
        """Carga categorías de overhead de la empresa"""
        categories = {}
        for cat in self.company.overhead_categories.filter(is_active=True):
            categories[cat.aura_category] = {
                'rate': float(cat.default_rate),
                'method': cat.calculation_method,
                'min_amount': float(cat.min_amount),
                'max_amount': float(cat.max_amount) if cat.max_amount else None,
                'formula': cat.formula,
                'ml_enabled': cat.ml_enabled,
                'ml_weight': float(cat.ml_weight)
            }
        
        # Valores por defecto si no hay configuración personalizada
        if not categories:
            categories = {
                'infrastructure': {'rate': 0.15, 'method': 'percentage', 'min_amount': 0, 'ml_enabled': True, 'ml_weight': 1.0},
                'administrative': {'rate': 0.08, 'method': 'percentage', 'min_amount': 0, 'ml_enabled': True, 'ml_weight': 1.0},
                'benefits': {'rate': 0.12, 'method': 'percentage', 'min_amount': 0, 'ml_enabled': True, 'ml_weight': 1.0},
                'training': {'rate': 0.03, 'method': 'percentage', 'min_amount': 0, 'ml_enabled': True, 'ml_weight': 1.0},
                'technology': {'rate': 0.05, 'method': 'percentage', 'min_amount': 0, 'ml_enabled': True, 'ml_weight': 1.0},
                'social_impact': {'rate': 0.02, 'method': 'percentage', 'min_amount': 0, 'ml_enabled': True, 'ml_weight': 1.0},
                'sustainability': {'rate': 0.015, 'method': 'percentage', 'min_amount': 0, 'ml_enabled': True, 'ml_weight': 1.0},
                'wellbeing': {'rate': 0.025, 'method': 'percentage', 'min_amount': 0, 'ml_enabled': True, 'ml_weight': 1.0},
                'innovation': {'rate': 0.02, 'method': 'percentage', 'min_amount': 0, 'ml_enabled': True, 'ml_weight': 1.0}
            }
        
        return categories
    
    def _load_benchmarks(self) -> Dict:
        """Carga benchmarks relevantes para la empresa"""
        try:
            # Determinar tamaño de empresa
            employee_count = self.company.get_employee_count()
            if employee_count <= 10:
                size_range = '1-10'
            elif employee_count <= 50:
                size_range = '11-50'
            elif employee_count <= 200:
                size_range = '51-200'
            elif employee_count <= 500:
                size_range = '201-500'
            elif employee_count <= 1000:
                size_range = '501-1000'
            else:
                size_range = '1000+'
            
            # Buscar benchmark más específico
            benchmark = OverheadBenchmark.objects.filter(
                industry__icontains=self.company.business_unit.name,
                company_size_range=size_range,
                is_active=True
            ).first()
            
            if not benchmark:
                # Benchmark genérico por tamaño
                benchmark = OverheadBenchmark.objects.filter(
                    company_size_range=size_range,
                    is_active=True
                ).first()
            
            if benchmark:
                return {
                    'infrastructure': float(benchmark.infrastructure_benchmark),
                    'administrative': float(benchmark.administrative_benchmark),
                    'benefits': float(benchmark.benefits_benchmark),
                    'training': float(benchmark.training_benchmark),
                    'technology': float(benchmark.technology_benchmark),
                    'social_impact': float(benchmark.social_impact_benchmark),
                    'sustainability': float(benchmark.sustainability_benchmark),
                    'wellbeing': float(benchmark.wellbeing_benchmark),
                    'innovation': float(benchmark.innovation_benchmark),
                    'total': float(benchmark.total_overhead_benchmark),
                    'percentiles': benchmark.get_benchmark_range()
                }
            
        except Exception as e:
            logger.warning(f"Error cargando benchmarks: {e}")
        
        # Benchmarks por defecto
        return {
            'infrastructure': 15.0,
            'administrative': 8.0,
            'benefits': 12.0,
            'training': 3.0,
            'technology': 5.0,
            'social_impact': 2.0,
            'sustainability': 1.5,
            'wellbeing': 2.5,
            'innovation': 2.0,
            'total': 51.0,
            'percentiles': {'min': 45.0, 'max': 65.0, 'median': 55.0, 'top_decile': 75.0}
        }
    
    def calculate_individual_overhead(
        self, 
        employee: PayrollEmployee, 
        period: PayrollPeriod,
        use_aura: bool = None,
        save_calculation: bool = True
    ) -> Dict:
        """
        Calcula overhead individual para un empleado
        
        Args:
            employee: Empleado para calcular
            period: Período de cálculo
            use_aura: Si usar capacidades AURA (auto-detecta si no se especifica)
            save_calculation: Si guardar el cálculo en BD
        
        Returns:
            Dict con todos los datos del cálculo
        """
        try:
            # Auto-detectar si tiene AURA
            if use_aura is None:
                use_aura = self._has_aura_subscription()
            
            base_salary = float(employee.monthly_salary)
            
            # Cálculo tradicional
            traditional_overhead = self._calculate_traditional_overhead(base_salary)
            
            # Cálculo AURA enhanced (si aplica)
            aura_overhead = {}
            if use_aura:
                aura_overhead = self._calculate_aura_enhanced_overhead(employee, base_salary)
            
            # Combinar overheads
            combined_overhead = self._combine_overheads(traditional_overhead, aura_overhead)
            
            # Calcular totales
            total_traditional = sum(traditional_overhead.values())
            total_aura_enhanced = sum(aura_overhead.values()) if use_aura else 0
            total_overhead = total_traditional + total_aura_enhanced
            overhead_percentage = (total_overhead / base_salary) * 100
            
            # Benchmarking
            benchmark_data = self._compare_with_benchmarks(overhead_percentage)
            
            # Preparar resultado
            result = {
                'employee_id': str(employee.id),
                'period_id': str(period.id),
                'base_salary': base_salary,
                'traditional_overhead': traditional_overhead,
                'aura_enhanced_overhead': aura_overhead,
                'combined_overhead': combined_overhead,
                'total_traditional': total_traditional,
                'total_aura_enhanced': total_aura_enhanced,
                'total_overhead': total_overhead,
                'overhead_percentage': overhead_percentage,
                'total_cost': base_salary + total_overhead,
                'benchmark_data': benchmark_data,
                'use_aura': use_aura,
                'calculation_metadata': {
                    'version': '2.0',
                    'calculated_at': timezone.now().isoformat(),
                    'categories_used': list(self.categories.keys()),
                    'company_size': self.company.get_employee_count()
                }
            }
            
            # Guardar en BD si se solicita
            if save_calculation:
                self._save_individual_calculation(employee, period, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculando overhead individual para {employee.get_full_name()}: {e}")
            raise
    
    def _calculate_traditional_overhead(self, base_salary: float) -> Dict:
        """Calcula overhead tradicional"""
        overhead = {}
        
        for category in ['infrastructure', 'administrative', 'benefits', 'training', 'technology']:
            if category in self.categories:
                config = self.categories[category]
                if config['method'] == 'percentage':
                    amount = base_salary * config['rate']
                elif config['method'] == 'fixed':
                    amount = config['rate']
                else:
                    amount = base_salary * config['rate']  # Default a percentage
                
                # Aplicar límites
                amount = max(amount, config['min_amount'])
                if config.get('max_amount'):
                    amount = min(amount, config['max_amount'])
                
                overhead[category] = amount
            else:
                # Valor por defecto
                default_rates = {
                    'infrastructure': 0.15,
                    'administrative': 0.08,
                    'benefits': 0.12,
                    'training': 0.03,
                    'technology': 0.05
                }
                overhead[category] = base_salary * default_rates.get(category, 0.05)
        
        return overhead
    
    def _calculate_aura_enhanced_overhead(self, employee: PayrollEmployee, base_salary: float) -> Dict:
        """Calcula overhead mejorado con AURA"""
        overhead = {}
        
        # Factores AURA basados en el perfil del empleado
        aura_factors = self._get_aura_factors(employee)
        
        for category in ['social_impact', 'sustainability', 'wellbeing', 'innovation']:
            if category in self.categories:
                config = self.categories[category]
                base_amount = base_salary * config['rate']
                
                # Aplicar factor AURA
                aura_factor = aura_factors.get(category, 1.0)
                amount = base_amount * aura_factor
                
                # Aplicar límites
                amount = max(amount, config['min_amount'])
                if config.get('max_amount'):
                    amount = min(amount, config['max_amount'])
                
                overhead[category] = amount
            else:
                # Valores por defecto AURA
                default_rates = {
                    'social_impact': 0.02,
                    'sustainability': 0.015,
                    'wellbeing': 0.025,
                    'innovation': 0.02
                }
                overhead[category] = base_salary * default_rates.get(category, 0.02)
        
        return overhead
    
    def _get_aura_factors(self, employee: PayrollEmployee) -> Dict:
        """Obtiene factores AURA para el empleado"""
        factors = {}
        
        # Analizar datos del empleado para factores AURA
        performance_score = employee.career_profile.get('avg_score', 75) if employee.career_profile else 75
        attendance_rate = employee.attendance_pattern.get('rate', 95) if employee.attendance_pattern else 95
        
        # Factor para impacto social (basado en rol y departamento)
        if employee.department.lower() in ['rse', 'responsabilidad social', 'sustentabilidad']:
            factors['social_impact'] = 1.5
        elif employee.job_title.lower() in ['manager', 'director', 'gerente']:
            factors['social_impact'] = 1.2
        else:
            factors['social_impact'] = 1.0
        
        # Factor sustentabilidad (basado en performance)
        if performance_score >= 90:
            factors['sustainability'] = 1.3
        elif performance_score >= 80:
            factors['sustainability'] = 1.1
        else:
            factors['sustainability'] = 0.9
        
        # Factor bienestar (basado en asistencia)
        if attendance_rate >= 98:
            factors['wellbeing'] = 1.2
        elif attendance_rate >= 95:
            factors['wellbeing'] = 1.0
        else:
            factors['wellbeing'] = 0.8
        
        # Factor innovación (basado en departamento y experiencia)
        if employee.department.lower() in ['it', 'tecnologia', 'innovacion', 'r&d']:
            factors['innovation'] = 1.4
        elif hasattr(employee, 'experience_years') and employee.experience_years and employee.experience_years >= 5:
            factors['innovation'] = 1.1
        else:
            factors['innovation'] = 1.0
        
        return factors
    
    def _combine_overheads(self, traditional: Dict, aura: Dict) -> Dict:
        """Combina overhead tradicional y AURA"""
        combined = traditional.copy()
        combined.update(aura)
        return combined
    
    def _compare_with_benchmarks(self, overhead_percentage: float) -> Dict:
        """Compara con benchmarks de industria"""
        benchmark = self.benchmarks
        
        return {
            'industry_percentile': self._calculate_percentile(overhead_percentage, benchmark['percentiles']),
            'vs_median': overhead_percentage - benchmark['total'],
            'vs_top_quartile': overhead_percentage - benchmark['percentiles']['max'],
            'rating': self._get_efficiency_rating(overhead_percentage, benchmark),
            'benchmark_data': benchmark
        }
    
    def _calculate_percentile(self, value: float, percentiles: Dict) -> float:
        """Calcula en qué percentil está el valor"""
        if value <= percentiles['min']:
            return 25.0
        elif value <= percentiles['median']:
            return 50.0
        elif value <= percentiles['max']:
            return 75.0
        elif value <= percentiles['top_decile']:
            return 90.0
        else:
            return 95.0
    
    def _get_efficiency_rating(self, overhead_percentage: float, benchmark: Dict) -> str:
        """Obtiene rating de eficiencia"""
        median = benchmark['total']
        
        if overhead_percentage <= median * 0.8:
            return 'Excelente'
        elif overhead_percentage <= median * 0.9:
            return 'Muy Bueno'
        elif overhead_percentage <= median:
            return 'Bueno'
        elif overhead_percentage <= median * 1.1:
            return 'Promedio'
        elif overhead_percentage <= median * 1.2:
            return 'Por Debajo del Promedio'
        else:
            return 'Necesita Mejora'
    
    def _has_aura_subscription(self) -> bool:
        """Determina si la empresa tiene suscripción AURA"""
        # Verificar si tienen servicios premium AURA habilitados
        premium_services = self.company.premium_services
        return premium_services.get('aura_enabled', False) or premium_services.get('aura_subscription', False)
    
    def _save_individual_calculation(self, employee: PayrollEmployee, period: PayrollPeriod, result: Dict):
        """Guarda el cálculo individual en la base de datos"""
        try:
            traditional = result['traditional_overhead']
            aura = result['aura_enhanced_overhead']
            
            calculation, created = EmployeeOverheadCalculation.objects.update_or_create(
                employee=employee,
                period=period,
                defaults={
                    'infrastructure_cost': Decimal(str(traditional.get('infrastructure', 0))),
                    'administrative_cost': Decimal(str(traditional.get('administrative', 0))),
                    'benefits_cost': Decimal(str(traditional.get('benefits', 0))),
                    'training_cost': Decimal(str(traditional.get('training', 0))),
                    'technology_cost': Decimal(str(traditional.get('technology', 0))),
                    'social_impact_cost': Decimal(str(aura.get('social_impact', 0))),
                    'sustainability_cost': Decimal(str(aura.get('sustainability', 0))),
                    'wellbeing_cost': Decimal(str(aura.get('wellbeing', 0))),
                    'innovation_cost': Decimal(str(aura.get('innovation', 0))),
                    'traditional_overhead': Decimal(str(result['total_traditional'])),
                    'aura_enhanced_overhead': Decimal(str(result['total_aura_enhanced'])),
                    'total_overhead': Decimal(str(result['total_overhead'])),
                    'overhead_percentage': Decimal(str(result['overhead_percentage'])),
                    'industry_benchmark': Decimal(str(result['benchmark_data']['benchmark_data']['total'])),
                    'calculation_version': '2.0'
                }
            )
            
            logger.info(f"{'Creado' if created else 'Actualizado'} cálculo overhead para {employee.get_full_name()}")
            
        except Exception as e:
            logger.error(f"Error guardando cálculo individual: {e}")
    
    def calculate_team_overhead(
        self, 
        team_employees: List[PayrollEmployee], 
        period: PayrollPeriod,
        team_name: str,
        department: str = None,
        use_aura: bool = None,
        save_analysis: bool = True
    ) -> Dict:
        """
        Calcula overhead grupal para un equipo
        
        Args:
            team_employees: Lista de empleados del equipo
            period: Período de cálculo
            team_name: Nombre del equipo
            department: Departamento (opcional)
            use_aura: Si usar capacidades AURA
            save_analysis: Si guardar análisis en BD
        
        Returns:
            Dict con análisis completo del equipo
        """
        try:
            if use_aura is None:
                use_aura = self._has_aura_subscription()
            
            team_data = {
                'team_name': team_name,
                'department': department or (team_employees[0].department if team_employees else 'General'),
                'team_size': len(team_employees),
                'individual_calculations': [],
                'team_metrics': {}
            }
            
            # Calcular overhead individual para cada empleado
            total_salaries = 0
            total_overhead = 0
            total_traditional = 0
            total_aura = 0
            
            for employee in team_employees:
                individual = self.calculate_individual_overhead(employee, period, use_aura, save_calculation=False)
                team_data['individual_calculations'].append(individual)
                
                total_salaries += individual['base_salary']
                total_overhead += individual['total_overhead']
                total_traditional += individual['total_traditional']
                total_aura += individual['total_aura_enhanced']
            
            # Métricas del equipo
            team_data['team_metrics'] = {
                'total_salaries': total_salaries,
                'total_overhead': total_overhead,
                'total_traditional_overhead': total_traditional,
                'total_aura_overhead': total_aura,
                'overhead_per_employee': total_overhead / len(team_employees) if team_employees else 0,
                'average_overhead_percentage': (total_overhead / total_salaries * 100) if total_salaries > 0 else 0,
                'total_cost': total_salaries + total_overhead,
                'cost_per_employee': (total_salaries + total_overhead) / len(team_employees) if team_employees else 0
            }
            
            # Análisis de eficiencia del equipo
            efficiency_analysis = self._analyze_team_efficiency(team_data)
            team_data['efficiency_analysis'] = efficiency_analysis
            
            # Análisis AURA del equipo (si aplica)
            if use_aura:
                aura_analysis = self._analyze_team_aura(team_employees, team_data)
                team_data['aura_analysis'] = aura_analysis
            
            # Benchmarking del equipo
            team_benchmark = self._benchmark_team(team_data['team_metrics']['average_overhead_percentage'])
            team_data['benchmark_analysis'] = team_benchmark
            
            # Metadatos
            team_data['metadata'] = {
                'calculated_at': timezone.now().isoformat(),
                'use_aura': use_aura,
                'calculation_version': '2.0',
                'company_id': str(self.company.id),
                'period_id': str(period.id)
            }
            
            # Guardar análisis si se solicita
            if save_analysis:
                self._save_team_analysis(team_employees, period, team_data)
            
            return team_data
            
        except Exception as e:
            logger.error(f"Error calculando overhead de equipo {team_name}: {e}")
            raise
    
    def _analyze_team_efficiency(self, team_data: Dict) -> Dict:
        """Analiza eficiencia del equipo"""
        calculations = team_data['individual_calculations']
        
        if not calculations:
            return {}
        
        # Estadísticas de overhead
        overhead_percentages = [calc['overhead_percentage'] for calc in calculations]
        
        return {
            'min_overhead': min(overhead_percentages),
            'max_overhead': max(overhead_percentages),
            'avg_overhead': sum(overhead_percentages) / len(overhead_percentages),
            'std_overhead': self._calculate_std(overhead_percentages),
            'efficiency_score': self._calculate_team_efficiency_score(team_data),
            'improvement_opportunities': self._identify_improvement_opportunities(calculations)
        }
    
    def _analyze_team_aura(self, team_employees: List[PayrollEmployee], team_data: Dict) -> Dict:
        """Análisis AURA del equipo"""
        if not team_employees:
            return {}
        
        # Análisis de diversidad del equipo
        departments = set(emp.department for emp in team_employees)
        job_titles = set(emp.job_title for emp in team_employees)
        
        # Scores promedio del equipo
        performance_scores = []
        attendance_rates = []
        
        for emp in team_employees:
            if emp.career_profile:
                performance_scores.append(emp.career_profile.get('avg_score', 75))
            if emp.attendance_pattern:
                attendance_rates.append(emp.attendance_pattern.get('rate', 95))
        
        avg_performance = sum(performance_scores) / len(performance_scores) if performance_scores else 75
        avg_attendance = sum(attendance_rates) / len(attendance_rates) if attendance_rates else 95
        
        return {
            'diversity_score': min(100, (len(departments) + len(job_titles)) * 10),  # Simple diversity metric
            'avg_performance': avg_performance,
            'avg_attendance': avg_attendance,
            'team_cohesion_score': self._calculate_cohesion_score(team_employees),
            'sustainability_impact': self._calculate_team_sustainability_impact(team_data),
            'innovation_potential': self._calculate_innovation_potential(team_employees),
            'wellbeing_index': self._calculate_wellbeing_index(team_employees)
        }
    
    def _calculate_std(self, values: List[float]) -> float:
        """Calcula desviación estándar"""
        if len(values) <= 1:
            return 0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def _calculate_team_efficiency_score(self, team_data: Dict) -> float:
        """Calcula score de eficiencia del equipo"""
        metrics = team_data['team_metrics']
        
        # Factores de eficiencia
        overhead_efficiency = max(0, 100 - metrics['average_overhead_percentage'])
        
        # Consistency (menor variación = mayor eficiencia)
        if len(team_data['individual_calculations']) > 1:
            overhead_percentages = [calc['overhead_percentage'] for calc in team_data['individual_calculations']]
            consistency = max(0, 100 - self._calculate_std(overhead_percentages))
        else:
            consistency = 100
        
        # Score final (promedio ponderado)
        efficiency_score = (overhead_efficiency * 0.7) + (consistency * 0.3)
        
        return min(100, max(0, efficiency_score))
    
    def _identify_improvement_opportunities(self, calculations: List[Dict]) -> List[Dict]:
        """Identifica oportunidades de mejora"""
        opportunities = []
        
        # Analizar cada categoría
        categories = ['infrastructure', 'administrative', 'benefits', 'training', 'technology']
        
        for category in categories:
            values = []
            for calc in calculations:
                if category in calc['traditional_overhead']:
                    percentage = (calc['traditional_overhead'][category] / calc['base_salary']) * 100
                    values.append(percentage)
            
            if values:
                avg_percentage = sum(values) / len(values)
                benchmark = self.benchmarks.get(category, 0)
                
                if avg_percentage > benchmark * 1.2:  # 20% por encima del benchmark
                    opportunities.append({
                        'category': category,
                        'current_percentage': avg_percentage,
                        'benchmark_percentage': benchmark,
                        'excess_percentage': avg_percentage - benchmark,
                        'potential_savings_per_employee': (avg_percentage - benchmark) / 100,
                        'priority': 'Alta' if avg_percentage > benchmark * 1.5 else 'Media'
                    })
        
        return sorted(opportunities, key=lambda x: x['excess_percentage'], reverse=True)
    
    def _calculate_cohesion_score(self, team_employees: List[PayrollEmployee]) -> float:
        """Calcula score de cohesión del equipo"""
        # Factores simples de cohesión
        if len(team_employees) <= 1:
            return 100
        
        # Diversidad de experiencia
        experience_years = []
        for emp in team_employees:
            if hasattr(emp, 'experience_years') and emp.experience_years:
                experience_years.append(emp.experience_years)
        
        if experience_years:
            exp_diversity = min(30, self._calculate_std(experience_years) * 5)  # Max 30 points
        else:
            exp_diversity = 15
        
        # Diversidad salarial (indica niveles jerárquicos)
        salaries = [float(emp.monthly_salary) for emp in team_employees]
        salary_diversity = min(30, self._calculate_std(salaries) / 1000)  # Max 30 points
        
        # Base cohesion score
        base_score = 40
        
        return min(100, base_score + exp_diversity + salary_diversity)
    
    def _calculate_team_sustainability_impact(self, team_data: Dict) -> float:
        """Calcula impacto de sustentabilidad del equipo"""
        # Basado en overhead de sustentabilidad
        total_sustainability = 0
        total_salary = 0
        
        for calc in team_data['individual_calculations']:
            if 'sustainability' in calc['aura_enhanced_overhead']:
                total_sustainability += calc['aura_enhanced_overhead']['sustainability']
                total_salary += calc['base_salary']
        
        if total_salary > 0:
            sustainability_percentage = (total_sustainability / total_salary) * 100
            return min(100, sustainability_percentage * 50)  # Scale to 0-100
        
        return 0
    
    def _calculate_innovation_potential(self, team_employees: List[PayrollEmployee]) -> float:
        """Calcula potencial de innovación del equipo"""
        innovation_score = 0
        
        for emp in team_employees:
            # Factores de innovación
            if emp.department.lower() in ['it', 'tecnologia', 'innovacion', 'r&d']:
                innovation_score += 20
            elif 'senior' in emp.job_title.lower() or 'lead' in emp.job_title.lower():
                innovation_score += 15
            elif hasattr(emp, 'experience_years') and emp.experience_years and emp.experience_years >= 5:
                innovation_score += 10
            else:
                innovation_score += 5
        
        # Promedio y normalización
        if team_employees:
            avg_innovation = innovation_score / len(team_employees)
            return min(100, avg_innovation * 5)  # Scale to 0-100
        
        return 0
    
    def _calculate_wellbeing_index(self, team_employees: List[PayrollEmployee]) -> float:
        """Calcula índice de bienestar del equipo"""
        wellbeing_scores = []
        
        for emp in team_employees:
            score = 50  # Base score
            
            # Factor asistencia
            if emp.attendance_pattern and 'rate' in emp.attendance_pattern:
                attendance_rate = emp.attendance_pattern['rate']
                if attendance_rate >= 98:
                    score += 25
                elif attendance_rate >= 95:
                    score += 15
                elif attendance_rate >= 90:
                    score += 5
            
            # Factor performance
            if emp.career_profile and 'avg_score' in emp.career_profile:
                performance = emp.career_profile['avg_score']
                if performance >= 90:
                    score += 25
                elif performance >= 80:
                    score += 15
                elif performance >= 70:
                    score += 5
            
            wellbeing_scores.append(min(100, score))
        
        return sum(wellbeing_scores) / len(wellbeing_scores) if wellbeing_scores else 50
    
    def _benchmark_team(self, avg_overhead_percentage: float) -> Dict:
        """Benchmarking del equipo contra industria"""
        benchmark = self.benchmarks
        
        return {
            'team_percentile': self._calculate_percentile(avg_overhead_percentage, benchmark['percentiles']),
            'vs_industry_median': avg_overhead_percentage - benchmark['total'],
            'efficiency_rating': self._get_efficiency_rating(avg_overhead_percentage, benchmark),
            'recommendations': self._generate_team_recommendations(avg_overhead_percentage, benchmark)
        }
    
    def _generate_team_recommendations(self, overhead_percentage: float, benchmark: Dict) -> List[str]:
        """Genera recomendaciones para el equipo"""
        recommendations = []
        median = benchmark['total']
        
        if overhead_percentage > median * 1.2:
            recommendations.extend([
                "Revisar procesos administrativos para identificar ineficiencias",
                "Considerar automatización de tareas repetitivas",
                "Evaluar consolidación de infraestructura compartida"
            ])
        elif overhead_percentage > median * 1.1:
            recommendations.extend([
                "Optimizar uso de recursos tecnológicos",
                "Implementar mejores prácticas de gestión de costos"
            ])
        elif overhead_percentage < median * 0.8:
            recommendations.extend([
                "Excelente eficiencia - considerar compartir mejores prácticas",
                "Evaluar oportunidades de inversión en innovación"
            ])
        
        return recommendations
    
    def _save_team_analysis(self, team_employees: List[PayrollEmployee], period: PayrollPeriod, team_data: Dict):
        """Guarda análisis del equipo en la base de datos"""
        try:
            metrics = team_data['team_metrics']
            efficiency = team_data.get('efficiency_analysis', {})
            aura = team_data.get('aura_analysis', {})
            benchmark = team_data.get('benchmark_analysis', {})
            
            # Determinar team lead (empleado con mayor salario)
            team_lead = max(team_employees, key=lambda emp: emp.monthly_salary) if team_employees else None
            
            analysis, created = TeamOverheadAnalysis.objects.update_or_create(
                company=self.company,
                team_name=team_data['team_name'],
                period=period,
                defaults={
                    'department': team_data['department'],
                    'team_lead': team_lead,
                    'team_size': team_data['team_size'],
                    'total_salaries': Decimal(str(metrics['total_salaries'])),
                    'total_overhead': Decimal(str(metrics['total_overhead'])),
                    'overhead_per_employee': Decimal(str(metrics['overhead_per_employee'])),
                    'efficiency_score': Decimal(str(efficiency.get('efficiency_score', 0))),
                    'team_ethics_score': Decimal(str(aura.get('avg_performance', 0))),
                    'team_diversity_score': Decimal(str(aura.get('diversity_score', 0))),
                    'team_sustainability_score': Decimal(str(aura.get('sustainability_impact', 0))),
                    'team_innovation_score': Decimal(str(aura.get('innovation_potential', 0))),
                    'ml_efficiency_prediction': Decimal(str(efficiency.get('efficiency_score', 0))),
                    'industry_percentile': Decimal(str(benchmark.get('team_percentile', 50))),
                    'ml_cost_optimization': team_data.get('ml_optimization', {}),
                    'aura_holistic_assessment': aura,
                    'is_active': True
                }
            )
            
            logger.info(f"{'Creado' if created else 'Actualizado'} análisis de equipo {team_data['team_name']}")
            
        except Exception as e:
            logger.error(f"Error guardando análisis de equipo: {e}")