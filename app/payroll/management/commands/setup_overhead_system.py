import json
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
from app.payroll.models import (
    PayrollCompany, PayrollEmployee, PayrollPeriod,
    OverheadCategory, EmployeeOverheadCalculation, TeamOverheadAnalysis,
    OverheadMLModel, OverheadBenchmark
)


class Command(BaseCommand):
    help = 'Configura el sistema completo de overhead con datos de ejemplo'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id',
            type=int,
            help='ID de la empresa para configurar',
        )
        parser.add_argument(
            '--with-aura',
            action='store_true',
            help='Incluir categorías AURA Enhanced',
        )
        parser.add_argument(
            '--with-ml',
            action='store_true',
            help='Crear modelos ML de ejemplo',
        )
        parser.add_argument(
            '--load-benchmarks',
            action='store_true',
            help='Cargar benchmarks de industria',
        )
        parser.add_argument(
            '--generate-history',
            type=int,
            default=12,
            help='Meses de historial a generar (default: 12)',
        )

    def handle(self, *args, **options):
        company_id = options.get('company_id')
        with_aura = options.get('with_aura', False)
        with_ml = options.get('with_ml', False)
        load_benchmarks = options.get('load_benchmarks', False)
        history_months = options.get('generate_history', 12)

        with transaction.atomic():
            # Obtener o crear empresa
            if company_id:
                try:
                    company = PayrollCompany.objects.get(id=company_id)
                    self.stdout.write(f"✓ Usando empresa: {company.name}")
                except PayrollCompany.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"Empresa con ID {company_id} no encontrada"))
                    return
            else:
                company, created = PayrollCompany.objects.get_or_create(
                    name="huntRED® Demo Corp",
                    defaults={
                        'rfc': 'HDC123456789',
                        'address': 'Av. Tecnología 123, Ciudad de México',
                        'phone': '+52 55 1234 5678',
                        'email': 'demo@huntred.com',
                        'is_active': True
                    }
                )
                if created:
                    self.stdout.write(f"✓ Empresa creada: {company.name}")
                else:
                    self.stdout.write(f"✓ Usando empresa existente: {company.name}")

            # 1. Crear categorías de overhead
            self.stdout.write("\n📂 Configurando categorías de overhead...")
            self.create_overhead_categories(company, with_aura)

            # 2. Cargar benchmarks si se solicita
            if load_benchmarks:
                self.stdout.write("\n📊 Cargando benchmarks de industria...")
                self.create_benchmarks()

            # 3. Crear modelos ML si se solicita
            if with_ml:
                self.stdout.write("\n🧠 Configurando modelos ML...")
                self.create_ml_models(company)

            # 4. Crear empleados de ejemplo
            self.stdout.write("\n👥 Creando empleados de ejemplo...")
            employees = self.create_sample_employees(company)

            # 5. Generar historial de cálculos
            self.stdout.write(f"\n📈 Generando {history_months} meses de historial...")
            self.generate_historical_data(company, employees, history_months, with_aura, with_ml)

            # 6. Crear análisis de equipos
            self.stdout.write("\n🏢 Creando análisis de equipos...")
            self.create_team_analyses(company, employees, with_aura, with_ml)

        self.stdout.write(self.style.SUCCESS("\n🎉 ¡Sistema de overhead configurado exitosamente!"))
        self.print_summary(company, with_aura, with_ml)

    def create_overhead_categories(self, company, with_aura):
        """Crear categorías tradicionales y AURA Enhanced"""
        
        # Categorías tradicionales
        traditional_categories = [
            {
                'name': 'Infraestructura',
                'description': 'Costos de oficinas, utilities, mantenimiento',
                'aura_category': 'INFRASTRUCTURE',
                'default_rate': Decimal('15.0'),
                'calculation_method': 'PERCENTAGE',
                'formula': 'base_salary * 0.15'
            },
            {
                'name': 'Administrativo',
                'description': 'Gastos administrativos, legal, contabilidad',
                'aura_category': 'ADMINISTRATIVE',
                'default_rate': Decimal('8.0'),
                'calculation_method': 'PERCENTAGE',
                'formula': 'base_salary * 0.08'
            },
            {
                'name': 'Beneficios',
                'description': 'Seguros, prestaciones, vacaciones',
                'aura_category': 'BENEFITS',
                'default_rate': Decimal('12.0'),
                'calculation_method': 'PERCENTAGE',
                'formula': 'base_salary * 0.12'
            },
            {
                'name': 'Capacitación',
                'description': 'Programas de entrenamiento y desarrollo',
                'aura_category': 'TRAINING',
                'default_rate': Decimal('3.0'),
                'calculation_method': 'PERCENTAGE',
                'formula': 'base_salary * 0.03'
            },
            {
                'name': 'Tecnología',
                'description': 'Hardware, software, licencias',
                'aura_category': 'TECHNOLOGY',
                'default_rate': Decimal('5.0'),
                'calculation_method': 'PERCENTAGE',
                'formula': 'base_salary * 0.05'
            }
        ]

        for cat_data in traditional_categories:
            category, created = OverheadCategory.objects.get_or_create(
                company=company,
                name=cat_data['name'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f"  ✓ Categoría creada: {category.name} ({category.default_rate}%)")

        # Categorías AURA Enhanced
        if with_aura:
            aura_categories = [
                {
                    'name': 'Impacto Social',
                    'description': 'Programas de responsabilidad social corporativa',
                    'aura_category': 'SOCIAL_IMPACT',
                    'default_rate': Decimal('2.0'),
                    'calculation_method': 'PERCENTAGE',
                    'formula': 'base_salary * 0.02',
                    'ml_enabled': True,
                    'ml_weight': Decimal('0.8')
                },
                {
                    'name': 'Sustentabilidad',
                    'description': 'Iniciativas ambientales y sustentables',
                    'aura_category': 'SUSTAINABILITY',
                    'default_rate': Decimal('1.5'),
                    'calculation_method': 'PERCENTAGE',
                    'formula': 'base_salary * 0.015',
                    'ml_enabled': True,
                    'ml_weight': Decimal('0.9')
                },
                {
                    'name': 'Bienestar',
                    'description': 'Programas de bienestar mental y físico',
                    'aura_category': 'WELLBEING',
                    'default_rate': Decimal('2.5'),
                    'calculation_method': 'PERCENTAGE',
                    'formula': 'base_salary * 0.025',
                    'ml_enabled': True,
                    'ml_weight': Decimal('0.85')
                },
                {
                    'name': 'Innovación',
                    'description': 'I+D, hackathons, proyectos innovadores',
                    'aura_category': 'INNOVATION',
                    'default_rate': Decimal('2.0'),
                    'calculation_method': 'PERCENTAGE',
                    'formula': 'base_salary * 0.02',
                    'ml_enabled': True,
                    'ml_weight': Decimal('0.75')
                }
            ]

            for cat_data in aura_categories:
                category, created = OverheadCategory.objects.get_or_create(
                    company=company,
                    name=cat_data['name'],
                    defaults=cat_data
                )
                if created:
                    self.stdout.write(f"  ✓ Categoría AURA creada: {category.name} ({category.default_rate}%)")

    def create_benchmarks(self):
        """Crear benchmarks de industria"""
        
        benchmarks_data = [
            {
                'industry': 'Tecnología',
                'region': 'México',
                'company_size_range': '50-250',
                'infrastructure_benchmark': Decimal('12.0'),
                'administrative_benchmark': Decimal('7.5'),
                'benefits_benchmark': Decimal('11.0'),
                'training_benchmark': Decimal('4.0'),
                'technology_benchmark': Decimal('6.5'),
                'social_impact_benchmark': Decimal('1.8'),
                'sustainability_benchmark': Decimal('1.3'),
                'wellbeing_benchmark': Decimal('2.2'),
                'innovation_benchmark': Decimal('2.8'),
                'total_overhead_benchmark': Decimal('41.1'),
                'sample_size': 150,
                'confidence_level': Decimal('95.0'),
                'data_source': 'Estudio huntRED® 2024'
            },
            {
                'industry': 'Finanzas',
                'region': 'México',
                'company_size_range': '50-250',
                'infrastructure_benchmark': Decimal('18.0'),
                'administrative_benchmark': Decimal('12.0'),
                'benefits_benchmark': Decimal('14.0'),
                'training_benchmark': Decimal('2.5'),
                'technology_benchmark': Decimal('4.0'),
                'social_impact_benchmark': Decimal('1.2'),
                'sustainability_benchmark': Decimal('0.8'),
                'wellbeing_benchmark': Decimal('1.8'),
                'innovation_benchmark': Decimal('1.0'),
                'total_overhead_benchmark': Decimal('55.3'),
                'sample_size': 95,
                'confidence_level': Decimal('93.0'),
                'data_source': 'Asociación Mexicana de Instituciones Financieras'
            },
            {
                'industry': 'Manufactura',
                'region': 'México',
                'company_size_range': '100-500',
                'infrastructure_benchmark': Decimal('22.0'),
                'administrative_benchmark': Decimal('9.0'),
                'benefits_benchmark': Decimal('13.5'),
                'training_benchmark': Decimal('2.0'),
                'technology_benchmark': Decimal('3.5'),
                'social_impact_benchmark': Decimal('0.8'),
                'sustainability_benchmark': Decimal('2.2'),
                'wellbeing_benchmark': Decimal('1.5'),
                'innovation_benchmark': Decimal('1.2'),
                'total_overhead_benchmark': Decimal('55.7'),
                'sample_size': 200,
                'confidence_level': Decimal('96.0'),
                'data_source': 'CANACINTRA 2024'
            }
        ]

        for benchmark_data in benchmarks_data:
            benchmark, created = OverheadBenchmark.objects.get_or_create(
                industry=benchmark_data['industry'],
                region=benchmark_data['region'],
                company_size_range=benchmark_data['company_size_range'],
                defaults=benchmark_data
            )
            if created:
                self.stdout.write(f"  ✓ Benchmark creado: {benchmark.industry} - {benchmark.region}")

    def create_ml_models(self, company):
        """Crear modelos ML de ejemplo"""
        
        models_data = [
            {
                'model_name': 'Random Forest Overhead Predictor',
                'model_type': 'RANDOM_FOREST',
                'version': '1.0.0',
                'accuracy': Decimal('87.3'),
                'precision': Decimal('89.1'),
                'recall': Decimal('85.7'),
                'f1_score': Decimal('87.4'),
                'mse': Decimal('0.045'),
                'training_data_size': 5000,
                'validation_data_size': 1000,
                'test_data_size': 500,
                'model_parameters': {
                    'n_estimators': 100,
                    'max_depth': 10,
                    'min_samples_split': 5,
                    'min_samples_leaf': 2
                },
                'feature_importance': {
                    'salary_level': 0.35,
                    'department': 0.22,
                    'experience': 0.18,
                    'team_size': 0.15,
                    'location': 0.10
                },
                'training_frequency_days': 30,
                'is_production': True
            },
            {
                'model_name': 'AURA Enhanced Neural Network',
                'model_type': 'AURA_ENHANCED',
                'version': '2.1.0',
                'accuracy': Decimal('91.7'),
                'precision': Decimal('93.2'),
                'recall': Decimal('90.8'),
                'f1_score': Decimal('92.0'),
                'mse': Decimal('0.032'),
                'aura_ethics_compliance': Decimal('96.5'),
                'aura_fairness_score': Decimal('94.2'),
                'aura_bias_detection': Decimal('98.1'),
                'training_data_size': 7500,
                'validation_data_size': 1500,
                'test_data_size': 750,
                'model_parameters': {
                    'hidden_layers': [128, 64, 32],
                    'activation': 'relu',
                    'optimizer': 'adam',
                    'learning_rate': 0.001,
                    'dropout_rate': 0.2
                },
                'aura_weights': {
                    'ethics_weight': 0.25,
                    'fairness_weight': 0.20,
                    'sustainability_weight': 0.25,
                    'innovation_weight': 0.15,
                    'transparency_weight': 0.15
                },
                'training_frequency_days': 15,
                'is_production': True
            },
            {
                'model_name': 'Hybrid ML+AURA Optimizer',
                'model_type': 'HYBRID_ML_AURA',
                'version': '3.0.0',
                'accuracy': Decimal('94.1'),
                'precision': Decimal('95.8'),
                'recall': Decimal('92.7'),
                'f1_score': Decimal('94.2'),
                'mse': Decimal('0.024'),
                'aura_ethics_compliance': Decimal('98.3'),
                'aura_fairness_score': Decimal('97.1'),
                'aura_bias_detection': Decimal('99.2'),
                'training_data_size': 10000,
                'validation_data_size': 2000,
                'test_data_size': 1000,
                'model_parameters': {
                    'ensemble_methods': ['random_forest', 'gradient_boosting', 'neural_network'],
                    'voting_strategy': 'soft',
                    'meta_learner': 'xgboost'
                },
                'training_frequency_days': 7,
                'is_production': True
            }
        ]

        for model_data in models_data:
            model_data['company'] = company
            model_data['last_training_date'] = timezone.now() - timedelta(days=model_data.get('training_frequency_days', 30))
            model_data['next_training_date'] = timezone.now() + timedelta(days=model_data.get('training_frequency_days', 30))
            
            model, created = OverheadMLModel.objects.get_or_create(
                company=company,
                model_name=model_data['model_name'],
                defaults=model_data
            )
            if created:
                self.stdout.write(f"  ✓ Modelo ML creado: {model.model_name} (Accuracy: {model.accuracy}%)")

    def create_sample_employees(self, company):
        """Crear empleados de ejemplo"""
        
        # Crear período actual
        current_period, _ = PayrollPeriod.objects.get_or_create(
            company=company,
            start_date=timezone.now().replace(day=1).date(),
            end_date=(timezone.now().replace(day=1) + timedelta(days=32)).replace(day=1).date() - timedelta(days=1),
            defaults={'is_closed': False}
        )

        employees_data = [
            # Equipo IT
            {'first_name': 'Ana', 'last_name': 'García López', 'email': 'ana.garcia@huntred.com', 'department': 'IT', 'salary': 85000, 'position': 'Senior Developer'},
            {'first_name': 'Carlos', 'last_name': 'Rodríguez Martín', 'email': 'carlos.rodriguez@huntred.com', 'department': 'IT', 'salary': 95000, 'position': 'Tech Lead'},
            {'first_name': 'María', 'last_name': 'Fernández Silva', 'email': 'maria.fernandez@huntred.com', 'department': 'IT', 'salary': 75000, 'position': 'Developer'},
            {'first_name': 'Luis', 'last_name': 'Mendoza Torres', 'email': 'luis.mendoza@huntred.com', 'department': 'IT', 'salary': 65000, 'position': 'Junior Developer'},
            
            # Marketing
            {'first_name': 'Sofia', 'last_name': 'Herrera Cruz', 'email': 'sofia.herrera@huntred.com', 'department': 'Marketing', 'salary': 70000, 'position': 'Marketing Manager'},
            {'first_name': 'Diego', 'last_name': 'Morales Vega', 'email': 'diego.morales@huntred.com', 'department': 'Marketing', 'salary': 55000, 'position': 'Digital Specialist'},
            {'first_name': 'Valentina', 'last_name': 'Castro Ruiz', 'email': 'valentina.castro@huntred.com', 'department': 'Marketing', 'salary': 60000, 'position': 'Content Creator'},
            
            # Finanzas
            {'first_name': 'Roberto', 'last_name': 'Jiménez Flores', 'email': 'roberto.jimenez@huntred.com', 'department': 'Finanzas', 'salary': 80000, 'position': 'Financial Analyst'},
            {'first_name': 'Carmen', 'last_name': 'Vargas Soto', 'email': 'carmen.vargas@huntred.com', 'department': 'Finanzas', 'salary': 90000, 'position': 'Finance Manager'},
            
            # RRHH
            {'first_name': 'Andrés', 'last_name': 'Ramírez Luna', 'email': 'andres.ramirez@huntred.com', 'department': 'RRHH', 'salary': 75000, 'position': 'HR Business Partner'},
            {'first_name': 'Natalia', 'last_name': 'Guerrero Paz', 'email': 'natalia.guerrero@huntred.com', 'department': 'RRHH', 'salary': 85000, 'position': 'HR Director'},
            
            # Operaciones
            {'first_name': 'Miguel', 'last_name': 'Ortega Ramos', 'email': 'miguel.ortega@huntred.com', 'department': 'Operaciones', 'salary': 70000, 'position': 'Operations Manager'},
            {'first_name': 'Isabel', 'last_name': 'Delgado Mora', 'email': 'isabel.delgado@huntred.com', 'department': 'Operaciones', 'salary': 60000, 'position': 'Operations Analyst'},
            
            # Ventas
            {'first_name': 'Fernando', 'last_name': 'Aguilar Peña', 'email': 'fernando.aguilar@huntred.com', 'department': 'Ventas', 'salary': 80000, 'position': 'Sales Manager'},
            {'first_name': 'Paola', 'last_name': 'Núñez Reyes', 'email': 'paola.nunez@huntred.com', 'department': 'Ventas', 'salary': 65000, 'position': 'Sales Representative'}
        ]

        employees = []
        for emp_data in employees_data:
            employee, created = PayrollEmployee.objects.get_or_create(
                company=company,
                email=emp_data['email'],
                defaults={
                    'first_name': emp_data['first_name'],
                    'last_name': emp_data['last_name'],
                    'department': emp_data['department'],
                    'position': emp_data['position'],
                    'hire_date': timezone.now().date() - timedelta(days=365),
                    'is_active': True
                }
            )
            if created:
                employees.append(employee)
                self.stdout.write(f"  ✓ Empleado creado: {employee.get_full_name()} - {emp_data['department']}")

        return employees

    def generate_historical_data(self, company, employees, months, with_aura, with_ml):
        """Generar historial de cálculos de overhead"""
        
        import random
        from decimal import Decimal as D
        
        categories = OverheadCategory.objects.filter(company=company)
        ml_models = OverheadMLModel.objects.filter(company=company) if with_ml else []
        
        for month_offset in range(months):
            period_date = timezone.now().date().replace(day=1) - timedelta(days=30 * month_offset)
            period, _ = PayrollPeriod.objects.get_or_create(
                company=company,
                start_date=period_date,
                end_date=period_date.replace(day=28),  # Simplified
                defaults={'is_closed': True}
            )

            for employee in employees:
                # Base salary with some variation
                base_salary = D(str(50000 + random.randint(15000, 45000)))
                
                # Calculate traditional overhead
                traditional_overhead = D('0')
                infrastructure_cost = base_salary * D('0.15') * (D('0.9') + D(str(random.random())) * D('0.2'))
                administrative_cost = base_salary * D('0.08') * (D('0.9') + D(str(random.random())) * D('0.2'))
                benefits_cost = base_salary * D('0.12') * (D('0.9') + D(str(random.random())) * D('0.2'))
                training_cost = base_salary * D('0.03') * (D('0.9') + D(str(random.random())) * D('0.2'))
                technology_cost = base_salary * D('0.05') * (D('0.9') + D(str(random.random())) * D('0.2'))
                
                traditional_overhead = (infrastructure_cost + administrative_cost + 
                                      benefits_cost + training_cost + technology_cost)

                # Calculate AURA overhead if enabled
                aura_enhanced_overhead = D('0')
                social_impact_cost = D('0')
                sustainability_cost = D('0')
                wellbeing_cost = D('0')
                innovation_cost = D('0')
                
                if with_aura:
                    social_impact_cost = base_salary * D('0.02') * (D('0.8') + D(str(random.random())) * D('0.4'))
                    sustainability_cost = base_salary * D('0.015') * (D('0.8') + D(str(random.random())) * D('0.4'))
                    wellbeing_cost = base_salary * D('0.025') * (D('0.8') + D(str(random.random())) * D('0.4'))
                    innovation_cost = base_salary * D('0.02') * (D('0.8') + D(str(random.random())) * D('0.4'))
                    aura_enhanced_overhead = (social_impact_cost + sustainability_cost + 
                                            wellbeing_cost + innovation_cost)

                total_overhead = traditional_overhead + aura_enhanced_overhead
                overhead_percentage = (total_overhead / base_salary) * 100

                # ML predictions if enabled
                ml_predicted_overhead = D('0')
                ml_confidence_score = D('0')
                ml_optimization_potential = D('0')
                ml_recommendations = {}
                
                if with_ml and ml_models:
                    model = random.choice(ml_models)
                    # Simulate ML prediction (slightly optimized)
                    ml_predicted_overhead = total_overhead * (D('0.88') + D(str(random.random())) * D('0.15'))
                    ml_confidence_score = model.accuracy + D(str(random.uniform(-5, 5)))
                    ml_optimization_potential = (total_overhead - ml_predicted_overhead) / total_overhead * 100
                    ml_recommendations = {
                        'suggested_optimizations': [
                            f'Optimize {employee.department} processes',
                            'Consider remote work benefits',
                            'Review technology stack efficiency'
                        ],
                        'priority_level': random.choice(['high', 'medium', 'low']),
                        'estimated_savings': float(total_overhead - ml_predicted_overhead)
                    }

                # AURA scores if enabled
                aura_ethics_score = D('0')
                aura_fairness_score = D('0')
                aura_sustainability_score = D('0')
                aura_insights = {}
                
                if with_aura:
                    aura_ethics_score = D(str(75 + random.randint(0, 20)))
                    aura_fairness_score = D(str(70 + random.randint(0, 25)))
                    aura_sustainability_score = D(str(65 + random.randint(0, 30)))
                    aura_insights = {
                        'ethical_compliance': random.choice(['excellent', 'good', 'fair']),
                        'diversity_score': random.randint(70, 95),
                        'environmental_impact': random.choice(['positive', 'neutral', 'needs_improvement']),
                        'social_responsibility': random.randint(65, 90)
                    }

                # Create calculation record
                calculation, created = EmployeeOverheadCalculation.objects.get_or_create(
                    employee=employee,
                    period=period,
                    defaults={
                        'infrastructure_cost': infrastructure_cost,
                        'administrative_cost': administrative_cost,
                        'benefits_cost': benefits_cost,
                        'training_cost': training_cost,
                        'technology_cost': technology_cost,
                        'traditional_overhead': traditional_overhead,
                        'social_impact_cost': social_impact_cost,
                        'sustainability_cost': sustainability_cost,
                        'wellbeing_cost': wellbeing_cost,
                        'innovation_cost': innovation_cost,
                        'aura_enhanced_overhead': aura_enhanced_overhead,
                        'total_overhead': total_overhead,
                        'overhead_percentage': overhead_percentage,
                        'ml_predicted_overhead': ml_predicted_overhead,
                        'ml_confidence_score': ml_confidence_score,
                        'ml_optimization_potential': ml_optimization_potential,
                        'ml_recommendations': ml_recommendations,
                        'aura_ethics_score': aura_ethics_score,
                        'aura_fairness_score': aura_fairness_score,
                        'aura_sustainability_score': aura_sustainability_score,
                        'aura_insights': aura_insights,
                        'industry_benchmark': D('45.0') + D(str(random.uniform(-5, 10))),
                        'company_size_benchmark': D('42.0') + D(str(random.uniform(-3, 8))),
                        'regional_benchmark': D('48.0') + D(str(random.uniform(-6, 12))),
                        'calculation_version': '1.0'
                    }
                )

            if month_offset % 3 == 0:  # Progress every 3 months
                self.stdout.write(f"  ✓ Historial generado para {months - month_offset} meses restantes...")

    def create_team_analyses(self, company, employees, with_aura, with_ml):
        """Crear análisis de equipos"""
        
        import random
        from decimal import Decimal as D
        from collections import defaultdict
        
        # Group employees by department
        departments = defaultdict(list)
        for employee in employees:
            departments[employee.department].append(employee)

        current_period = PayrollPeriod.objects.filter(company=company, is_closed=False).first()
        if not current_period:
            return

        for dept_name, dept_employees in departments.items():
            if len(dept_employees) < 2:  # Skip departments with less than 2 employees
                continue

            team_lead = random.choice(dept_employees)
            
            # Calculate team metrics
            total_salaries = D(str(len(dept_employees) * 70000))  # Approximate
            overhead_calculations = EmployeeOverheadCalculation.objects.filter(
                employee__in=dept_employees,
                period=current_period
            )
            
            if overhead_calculations.exists():
                total_overhead = sum(calc.total_overhead for calc in overhead_calculations)
                overhead_per_employee = total_overhead / len(dept_employees)
            else:
                total_overhead = total_salaries * D('0.45')  # Default 45%
                overhead_per_employee = total_overhead / len(dept_employees)

            # Team scores
            team_ethics_score = D(str(75 + random.randint(0, 20))) if with_aura else D('0')
            team_diversity_score = D(str(70 + random.randint(0, 25))) if with_aura else D('0')
            team_sustainability_score = D(str(65 + random.randint(0, 30))) if with_aura else D('0')
            team_innovation_score = D(str(60 + random.randint(0, 35))) if with_aura else D('0')

            # ML predictions
            ml_efficiency_prediction = D(str(80 + random.randint(0, 15))) if with_ml else D('0')
            ml_turnover_risk = D(str(random.randint(5, 25))) if with_ml else D('0')
            ml_performance_forecast = D(str(85 + random.randint(-10, 15))) if with_ml else D('0')
            ml_cost_optimization = D(str(random.randint(5, 20))) if with_ml else D('0')

            # AURA analysis
            aura_holistic_assessment = {}
            aura_energy_analysis = {}
            aura_compatibility_matrix = {}
            aura_growth_recommendations = []
            
            if with_aura:
                aura_holistic_assessment = {
                    'overall_harmony': random.randint(70, 95),
                    'energy_alignment': random.choice(['high', 'medium', 'low']),
                    'spiritual_balance': random.randint(65, 90),
                    'collective_consciousness': random.choice(['strong', 'moderate', 'developing'])
                }
                
                aura_energy_analysis = {
                    'dominant_energy': random.choice(['creative', 'analytical', 'collaborative', 'leadership']),
                    'energy_flow': random.choice(['optimal', 'good', 'blocked']),
                    'chakra_alignment': random.randint(60, 95),
                    'vibrational_frequency': f"{random.randint(432, 528)}Hz"
                }
                
                aura_compatibility_matrix = {
                    'team_synergy': random.randint(75, 95),
                    'conflict_potential': random.randint(5, 25),
                    'collaboration_index': random.randint(80, 98),
                    'leadership_compatibility': random.randint(70, 90)
                }
                
                aura_growth_recommendations = [
                    f"Focus on {random.choice(['meditation', 'team building', 'energy healing'])} sessions",
                    f"Enhance {random.choice(['communication', 'empathy', 'mindfulness'])} practices",
                    f"Consider {random.choice(['crystal therapy', 'sound healing', 'yoga'])} for team alignment"
                ]

            team_analysis, created = TeamOverheadAnalysis.objects.get_or_create(
                company=company,
                period=current_period,
                team_name=f"Equipo {dept_name}",
                department=dept_name,
                defaults={
                    'team_lead': team_lead,
                    'team_size': len(dept_employees),
                    'total_salaries': total_salaries,
                    'total_overhead': total_overhead,
                    'overhead_per_employee': overhead_per_employee,
                    'team_ethics_score': team_ethics_score,
                    'team_diversity_score': team_diversity_score,
                    'team_sustainability_score': team_sustainability_score,
                    'team_innovation_score': team_innovation_score,
                    'ml_efficiency_prediction': ml_efficiency_prediction,
                    'ml_turnover_risk': ml_turnover_risk,
                    'ml_performance_forecast': ml_performance_forecast,
                    'ml_cost_optimization': ml_cost_optimization,
                    'efficiency_score': D(str(75 + random.randint(0, 20))),
                    'industry_percentile': D(str(random.randint(60, 95))),
                    'company_ranking': random.randint(1, len(departments)),
                    'aura_holistic_assessment': aura_holistic_assessment,
                    'aura_energy_analysis': aura_energy_analysis,
                    'aura_compatibility_matrix': aura_compatibility_matrix,
                    'aura_growth_recommendations': aura_growth_recommendations,
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(f"  ✓ Análisis de equipo creado: {team_analysis.team_name} ({len(dept_employees)} miembros)")

    def print_summary(self, company, with_aura, with_ml):
        """Imprimir resumen de la configuración"""
        
        categories_count = OverheadCategory.objects.filter(company=company).count()
        employees_count = PayrollEmployee.objects.filter(company=company).count()
        calculations_count = EmployeeOverheadCalculation.objects.filter(employee__company=company).count()
        teams_count = TeamOverheadAnalysis.objects.filter(company=company).count()
        ml_models_count = OverheadMLModel.objects.filter(company=company).count() if with_ml else 0
        benchmarks_count = OverheadBenchmark.objects.count()

        self.stdout.write(f"""
╔════════════════════════════════════════════════════════════════╗
║                     RESUMEN DE CONFIGURACIÓN                   ║
╠════════════════════════════════════════════════════════════════╣
║ 🏢 Empresa: {company.name:<45} ║
║ 📂 Categorías de Overhead: {categories_count:<35} ║
║ 👥 Empleados Creados: {employees_count:<40} ║
║ 📊 Cálculos Generados: {calculations_count:<39} ║
║ 🏢 Análisis de Equipos: {teams_count:<37} ║
║ 🧠 Modelos ML: {ml_models_count:<47} ║
║ 📈 Benchmarks de Industria: {benchmarks_count:<33} ║
║                                                                ║
║ 🔮 AURA Enhanced: {'✓ Activado' if with_aura else '✗ Desactivado':<41} ║
║ 🤖 Machine Learning: {'✓ Activado' if with_ml else '✗ Desactivado':<41} ║
╚════════════════════════════════════════════════════════════════╝

📌 URLs de Acceso:
   • Dashboard: /payroll/overhead/dashboard/
   • API Calculadora: /api/payroll/overhead/calculate/
   • Admin: /admin/payroll/

🚀 ¡Sistema listo para usar en producción!
        """)