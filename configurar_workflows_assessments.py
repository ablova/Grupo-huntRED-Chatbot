#!/usr/bin/env python3
"""
Script de Configuración de Workflows y Assessments por Unidad de Negocio

Este script configura:
1. Workflows específicos para cada BU (huntRED® Executive, huntRED®, huntU®, Amigro)
2. Assessments personalizados por BU
3. Configuración de preguntas y evaluaciones
4. Flujos de conversación del chatbot

Autor: huntRED® Group
Versión: 2.0.0
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('workflows_assessments_config.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WorkflowAssessmentConfigurator:
    """Configurador de workflows y assessments."""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.workflow_dir = self.base_dir / 'app' / 'ats' / 'chatbot' / 'workflow'
        self.assessment_dir = self.workflow_dir / 'assessments'
        
        # Configuraciones de workflows por BU
        self.workflow_configs = {
            'huntRED_executive': {
                'name': 'huntRED® Executive',
                'description': 'Flujo para posiciones C-level y miembros de consejo',
                'states': [
                    'INICIO',
                    'IDENTIFICACION_EJECUTIVA',
                    'PERFIL_EJECUTIVO',
                    'EXPERIENCIA_CONSEJOS',
                    'OPORTUNIDAD_EJECUTIVA',
                    'ENTREVISTA_EJECUTIVA',
                    'EVALUACION_EJECUTIVA',
                    'PROPUESTA_EJECUTIVA',
                    'CERRADO'
                ],
                'transitions': {
                    'INICIO': ['IDENTIFICACION_EJECUTIVA'],
                    'IDENTIFICACION_EJECUTIVA': ['PERFIL_EJECUTIVO'],
                    'PERFIL_EJECUTIVO': ['EXPERIENCIA_CONSEJOS'],
                    'EXPERIENCIA_CONSEJOS': ['OPORTUNIDAD_EJECUTIVA'],
                    'OPORTUNIDAD_EJECUTIVA': ['ENTREVISTA_EJECUTIVA'],
                    'ENTREVISTA_EJECUTIVA': ['EVALUACION_EJECUTIVA'],
                    'EVALUACION_EJECUTIVA': ['PROPUESTA_EJECUTIVA'],
                    'PROPUESTA_EJECUTIVA': ['CERRADO']
                },
                'timeouts': {
                    'IDENTIFICACION_EJECUTIVA': 48 * 3600,  # 48 horas
                    'PERFIL_EJECUTIVO': 72 * 3600,  # 72 horas
                    'EXPERIENCIA_CONSEJOS': 48 * 3600,  # 48 horas
                    'OPORTUNIDAD_EJECUTIVA': 96 * 3600,  # 96 horas
                    'ENTREVISTA_EJECUTIVA': 24 * 3600,  # 24 horas
                    'EVALUACION_EJECUTIVA': 72 * 3600,  # 72 horas
                    'PROPUESTA_EJECUTIVA': 48 * 3600,  # 48 horas
                },
                'required_fields': [
                    'nombre_completo',
                    'email',
                    'telefono',
                    'tipo_posicion_ejecutiva',
                    'experiencia_consejos',
                    'industria_preferida',
                    'expectativa_salarial',
                    'ubicacion_preferida'
                ],
                'assessments': [
                    'executive_personality',
                    'leadership_style',
                    'board_experience',
                    'strategic_thinking'
                ]
            },
            'huntRED': {
                'name': 'huntRED®',
                'description': 'Flujo para posiciones gerenciales especializadas',
                'states': [
                    'INICIO',
                    'IDENTIFICACION',
                    'PERFIL_GERENCIAL',
                    'EXPERIENCIA_TECNICA',
                    'OPORTUNIDAD',
                    'ENTREVISTA_TECNICA',
                    'REFERENCIAS',
                    'PROPUESTA',
                    'CERRADO'
                ],
                'transitions': {
                    'INICIO': ['IDENTIFICACION'],
                    'IDENTIFICACION': ['PERFIL_GERENCIAL'],
                    'PERFIL_GERENCIAL': ['EXPERIENCIA_TECNICA'],
                    'EXPERIENCIA_TECNICA': ['OPORTUNIDAD'],
                    'OPORTUNIDAD': ['ENTREVISTA_TECNICA'],
                    'ENTREVISTA_TECNICA': ['REFERENCIAS'],
                    'REFERENCIAS': ['PROPUESTA'],
                    'PROPUESTA': ['CERRADO']
                },
                'timeouts': {
                    'IDENTIFICACION': 24 * 3600,  # 24 horas
                    'PERFIL_GERENCIAL': 48 * 3600,  # 48 horas
                    'EXPERIENCIA_TECNICA': 48 * 3600,  # 48 horas
                    'OPORTUNIDAD': 72 * 3600,  # 72 horas
                    'ENTREVISTA_TECNICA': 24 * 3600,  # 24 horas
                    'REFERENCIAS': 168 * 3600,  # 1 semana
                    'PROPUESTA': 48 * 3600,  # 48 horas
                },
                'required_fields': [
                    'nombre_completo',
                    'email',
                    'telefono',
                    'nivel_gerencial',
                    'experiencia_anos',
                    'especialidad_tecnica',
                    'expectativa_salarial',
                    'ubicacion_preferida'
                ],
                'assessments': [
                    'personality',
                    'technical_skills',
                    'cultural_fit',
                    'leadership_potential'
                ]
            },
            'huntU': {
                'name': 'huntU®',
                'description': 'Flujo para talento universitario y puestos de entrada',
                'states': [
                    'INICIO',
                    'IDENTIFICACION_ESTUDIANTIL',
                    'PERFIL_ACADEMICO',
                    'HABILIDADES_BLANDAS',
                    'OPORTUNIDAD_JUNIOR',
                    'ENTREVISTA_JUNIOR',
                    'EVALUACION_POTENCIAL',
                    'PROPUESTA_JUNIOR',
                    'CERRADO'
                ],
                'transitions': {
                    'INICIO': ['IDENTIFICACION_ESTUDIANTIL'],
                    'IDENTIFICACION_ESTUDIANTIL': ['PERFIL_ACADEMICO'],
                    'PERFIL_ACADEMICO': ['HABILIDADES_BLANDAS'],
                    'HABILIDADES_BLANDAS': ['OPORTUNIDAD_JUNIOR'],
                    'OPORTUNIDAD_JUNIOR': ['ENTREVISTA_JUNIOR'],
                    'ENTREVISTA_JUNIOR': ['EVALUACION_POTENCIAL'],
                    'EVALUACION_POTENCIAL': ['PROPUESTA_JUNIOR'],
                    'PROPUESTA_JUNIOR': ['CERRADO']
                },
                'timeouts': {
                    'IDENTIFICACION_ESTUDIANTIL': 24 * 3600,  # 24 horas
                    'PERFIL_ACADEMICO': 48 * 3600,  # 48 horas
                    'HABILIDADES_BLANDAS': 24 * 3600,  # 24 horas
                    'OPORTUNIDAD_JUNIOR': 72 * 3600,  # 72 horas
                    'ENTREVISTA_JUNIOR': 24 * 3600,  # 24 horas
                    'EVALUACION_POTENCIAL': 48 * 3600,  # 48 horas
                    'PROPUESTA_JUNIOR': 48 * 3600,  # 48 horas
                },
                'required_fields': [
                    'nombre_completo',
                    'email',
                    'telefono',
                    'universidad',
                    'carrera',
                    'semestre_graduacion',
                    'experiencia_practicas',
                    'expectativa_salarial'
                ],
                'assessments': [
                    'personality',
                    'potential_assessment',
                    'cultural_fit',
                    'learning_agility'
                ]
            },
            'amigro': {
                'name': 'Amigro',
                'description': 'Flujo para oportunidades laborales para migrantes',
                'states': [
                    'INICIO',
                    'IDENTIFICACION_MIGRANTE',
                    'PERFIL_BASICO',
                    'HABILIDADES_IDIOMA',
                    'OPORTUNIDAD_OPERATIVA',
                    'ENTREVISTA_BASICA',
                    'EVALUACION_ADAPTACION',
                    'PROPUESTA_OPERATIVA',
                    'CERRADO'
                ],
                'transitions': {
                    'INICIO': ['IDENTIFICACION_MIGRANTE'],
                    'IDENTIFICACION_MIGRANTE': ['PERFIL_BASICO'],
                    'PERFIL_BASICO': ['HABILIDADES_IDIOMA'],
                    'HABILIDADES_IDIOMA': ['OPORTUNIDAD_OPERATIVA'],
                    'OPORTUNIDAD_OPERATIVA': ['ENTREVISTA_BASICA'],
                    'ENTREVISTA_BASICA': ['EVALUACION_ADAPTACION'],
                    'EVALUACION_ADAPTACION': ['PROPUESTA_OPERATIVA'],
                    'PROPUESTA_OPERATIVA': ['CERRADO']
                },
                'timeouts': {
                    'IDENTIFICACION_MIGRANTE': 24 * 3600,  # 24 horas
                    'PERFIL_BASICO': 48 * 3600,  # 48 horas
                    'HABILIDADES_IDIOMA': 24 * 3600,  # 24 horas
                    'OPORTUNIDAD_OPERATIVA': 72 * 3600,  # 72 horas
                    'ENTREVISTA_BASICA': 24 * 3600,  # 24 horas
                    'EVALUACION_ADAPTACION': 48 * 3600,  # 48 horas
                    'PROPUESTA_OPERATIVA': 48 * 3600,  # 48 horas
                },
                'required_fields': [
                    'nombre_completo',
                    'email',
                    'telefono',
                    'pais_origen',
                    'idiomas',
                    'experiencia_laboral',
                    'expectativa_salarial',
                    'ubicacion_preferida'
                ],
                'assessments': [
                    'basic_skills',
                    'language_assessment',
                    'cultural_adaptation',
                    'work_attitude'
                ]
            }
        }
        
        # Configuraciones de assessments
        self.assessment_configs = {
            'executive_personality': {
                'name': 'Evaluación de Personalidad Ejecutiva',
                'description': 'Evaluación específica para personalidades ejecutivas',
                'questions_count': 80,
                'time_limit_minutes': 45,
                'passing_score': 80,
                'categories': [
                    'liderazgo_ejecutivo',
                    'toma_decisiones',
                    'comunicacion_ejecutiva',
                    'vision_estrategica',
                    'manejo_presion'
                ],
                'questions': [
                    {
                        'id': 'leadership_style',
                        'text': '¿Cómo describirías tu estilo de liderazgo en situaciones de crisis?',
                        'type': 'multiple_choice',
                        'options': [
                            'Directivo y autoritario',
                            'Colaborativo y participativo',
                            'Delegativo y empoderador',
                            'Transformacional e inspirador'
                        ],
                        'weight': 1.0
                    },
                    {
                        'id': 'decision_making',
                        'text': 'En una decisión estratégica crítica, ¿qué factor consideras más importante?',
                        'type': 'multiple_choice',
                        'options': [
                            'Análisis de datos y métricas',
                            'Intuición y experiencia',
                            'Consenso del equipo',
                            'Impacto a largo plazo'
                        ],
                        'weight': 1.0
                    }
                ]
            },
            'leadership_style': {
                'name': 'Estilo de Liderazgo',
                'description': 'Evaluación del estilo de liderazgo',
                'questions_count': 60,
                'time_limit_minutes': 35,
                'passing_score': 75,
                'categories': [
                    'liderazgo_transformacional',
                    'liderazgo_situacional',
                    'liderazgo_servicial',
                    'liderazgo_estrategico'
                ]
            },
            'board_experience': {
                'name': 'Experiencia en Consejos',
                'description': 'Evaluación de experiencia en consejos directivos',
                'questions_count': 40,
                'time_limit_minutes': 25,
                'passing_score': 80,
                'categories': [
                    'gobernanza_corporativa',
                    'toma_decisiones_consejo',
                    'relacion_accionistas',
                    'cumplimiento_regulatorio'
                ]
            },
            'strategic_thinking': {
                'name': 'Pensamiento Estratégico',
                'description': 'Evaluación de capacidades de pensamiento estratégico',
                'questions_count': 35,
                'time_limit_minutes': 30,
                'passing_score': 80,
                'categories': [
                    'vision_estrategica',
                    'analisis_mercado',
                    'planeacion_largo_plazo',
                    'innovacion_estrategica'
                ]
            },
            'personality': {
                'name': 'Evaluación de Personalidad',
                'description': 'Evaluación general de personalidad',
                'questions_count': 50,
                'time_limit_minutes': 30,
                'passing_score': 70,
                'categories': [
                    'extraversion',
                    'responsabilidad',
                    'apertura_experiencia',
                    'amabilidad',
                    'estabilidad_emocional'
                ]
            },
            'technical_skills': {
                'name': 'Habilidades Técnicas',
                'description': 'Evaluación de habilidades técnicas específicas',
                'questions_count': 40,
                'time_limit_minutes': 60,
                'passing_score': 75,
                'categories': [
                    'programacion',
                    'gestion_proyectos',
                    'analisis_datos',
                    'herramientas_tecnologicas'
                ]
            },
            'cultural_fit': {
                'name': 'Ajuste Cultural',
                'description': 'Evaluación de ajuste cultural organizacional',
                'questions_count': 30,
                'time_limit_minutes': 20,
                'passing_score': 70,
                'categories': [
                    'valores_organizacionales',
                    'estilo_trabajo',
                    'comunicacion_equipo',
                    'adaptabilidad_cambio'
                ]
            },
            'leadership_potential': {
                'name': 'Potencial de Liderazgo',
                'description': 'Evaluación del potencial de liderazgo',
                'questions_count': 45,
                'time_limit_minutes': 25,
                'passing_score': 70,
                'categories': [
                    'influencia_otros',
                    'toma_decisiones',
                    'comunicacion_efectiva',
                    'desarrollo_equipo'
                ]
            },
            'potential_assessment': {
                'name': 'Evaluación de Potencial',
                'description': 'Evaluación del potencial de desarrollo',
                'questions_count': 45,
                'time_limit_minutes': 25,
                'passing_score': 70,
                'categories': [
                    'capacidad_aprendizaje',
                    'adaptabilidad',
                    'iniciativa',
                    'resolucion_problemas'
                ]
            },
            'learning_agility': {
                'name': 'Agilidad de Aprendizaje',
                'description': 'Evaluación de la capacidad de aprendizaje rápido',
                'questions_count': 35,
                'time_limit_minutes': 20,
                'passing_score': 70,
                'categories': [
                    'aprendizaje_rapido',
                    'aplicacion_conocimiento',
                    'experimentacion',
                    'reflexion_aprendizaje'
                ]
            },
            'basic_skills': {
                'name': 'Habilidades Básicas',
                'description': 'Evaluación de habilidades básicas laborales',
                'questions_count': 25,
                'time_limit_minutes': 15,
                'passing_score': 60,
                'categories': [
                    'comunicacion_basica',
                    'trabajo_equipo',
                    'puntualidad',
                    'responsabilidad'
                ]
            },
            'language_assessment': {
                'name': 'Evaluación de Idiomas',
                'description': 'Evaluación de competencias lingüísticas',
                'questions_count': 30,
                'time_limit_minutes': 20,
                'passing_score': 65,
                'categories': [
                    'comprension_lectora',
                    'expresion_escrita',
                    'comprension_auditiva',
                    'expresion_oral'
                ]
            },
            'cultural_adaptation': {
                'name': 'Adaptación Cultural',
                'description': 'Evaluación de adaptación cultural',
                'questions_count': 20,
                'time_limit_minutes': 15,
                'passing_score': 60,
                'categories': [
                    'respeto_diversidad',
                    'adaptacion_cambios',
                    'trabajo_multicultural',
                    'comunicacion_intercultural'
                ]
            },
            'work_attitude': {
                'name': 'Actitud Laboral',
                'description': 'Evaluación de actitud hacia el trabajo',
                'questions_count': 25,
                'time_limit_minutes': 15,
                'passing_score': 65,
                'categories': [
                    'motivacion_trabajo',
                    'compromiso_organizacion',
                    'iniciativa_propia',
                    'trabajo_equipo'
                ]
            }
        }
    
    def run_configuration(self):
        """Ejecuta la configuración de workflows y assessments."""
        logger.info("🚀 Iniciando configuración de Workflows y Assessments")
        
        try:
            # 1. Configurar Workflows
            self.configure_workflows()
            
            # 2. Configurar Assessments
            self.configure_assessments()
            
            # 3. Generar archivos de configuración
            self.generate_workflow_files()
            self.generate_assessment_files()
            
            # 4. Validar configuración
            self.validate_workflow_configuration()
            
            logger.info("✅ Configuración de Workflows y Assessments completada")
            
        except Exception as e:
            logger.error(f"❌ Error durante la configuración: {str(e)}")
            raise
    
    def configure_workflows(self):
        """Configura los workflows por unidad de negocio."""
        logger.info("🔄 Configurando Workflows por Unidad de Negocio...")
        
        for bu_code, config in self.workflow_configs.items():
            logger.info(f"  Configurando workflow para {config['name']}...")
            
            print(f"\n🔄 {config['name']} ({bu_code})")
            print(f"   Descripción: {config['description']}")
            print(f"   Estados: {len(config['states'])}")
            print(f"   Transiciones: {len(config['transitions'])}")
            print(f"   Timeouts configurados: {len(config['timeouts'])}")
            print(f"   Campos requeridos: {len(config['required_fields'])}")
            print(f"   Assessments: {len(config['assessments'])}")
            
            # Mostrar estados
            print(f"   Estados del flujo:")
            for i, state in enumerate(config['states'], 1):
                timeout = config['timeouts'].get(state, 'Sin timeout')
                if isinstance(timeout, int):
                    timeout = f"{timeout // 3600}h"
                print(f"     {i}. {state} (timeout: {timeout})")
    
    def configure_assessments(self):
        """Configura los assessments."""
        logger.info("📊 Configurando Assessments...")
        
        for assessment_code, config in self.assessment_configs.items():
            logger.info(f"  Configurando {config['name']}...")
            
            print(f"\n📝 {config['name']} ({assessment_code})")
            print(f"   Descripción: {config['description']}")
            print(f"   Preguntas: {config['questions_count']}")
            print(f"   Tiempo límite: {config['time_limit_minutes']} minutos")
            print(f"   Puntaje mínimo: {config['passing_score']}%")
            print(f"   Categorías: {len(config['categories'])}")
            
            # Mostrar categorías
            print(f"   Categorías de evaluación:")
            for i, category in enumerate(config['categories'], 1):
                print(f"     {i}. {category.replace('_', ' ').title()}")
    
    def generate_workflow_files(self):
        """Genera los archivos de configuración de workflows."""
        logger.info("📄 Generando archivos de configuración de workflows...")
        
        # Crear directorio si no existe
        workflow_config_dir = self.base_dir / 'config' / 'workflows'
        workflow_config_dir.mkdir(parents=True, exist_ok=True)
        
        # Generar archivo principal de workflows
        workflows_config = {
            'version': '2.0.0',
            'generated_at': datetime.now().isoformat(),
            'workflows': self.workflow_configs
        }
        
        workflows_file = workflow_config_dir / 'workflows_config.json'
        with open(workflows_file, 'w', encoding='utf-8') as f:
            json.dump(workflows_config, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Archivo de workflows generado: {workflows_file}")
        
        # Generar archivos individuales por BU
        for bu_code, config in self.workflow_configs.items():
            bu_file = workflow_config_dir / f'{bu_code}_workflow.json'
            with open(bu_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Workflow generado para {bu_code}: {bu_file}")
    
    def generate_assessment_files(self):
        """Genera los archivos de configuración de assessments."""
        logger.info("📄 Generando archivos de configuración de assessments...")
        
        # Crear directorio si no existe
        assessment_config_dir = self.base_dir / 'config' / 'assessments'
        assessment_config_dir.mkdir(parents=True, exist_ok=True)
        
        # Generar archivo principal de assessments
        assessments_config = {
            'version': '2.0.0',
            'generated_at': datetime.now().isoformat(),
            'assessments': self.assessment_configs
        }
        
        assessments_file = assessment_config_dir / 'assessments_config.json'
        with open(assessments_file, 'w', encoding='utf-8') as f:
            json.dump(assessments_config, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Archivo de assessments generado: {assessments_file}")
        
        # Generar archivos individuales por assessment
        for assessment_code, config in self.assessment_configs.items():
            assessment_file = assessment_config_dir / f'{assessment_code}_assessment.json'
            with open(assessment_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Assessment generado para {assessment_code}: {assessment_file}")
    
    def validate_workflow_configuration(self):
        """Valida la configuración de workflows."""
        logger.info("✅ Validando configuración de workflows...")
        
        # Validar workflows
        for bu_code, config in self.workflow_configs.items():
            # Verificar que todos los estados en transitions existen
            for from_state, to_states in config['transitions'].items():
                if from_state not in config['states']:
                    raise ValueError(f"Estado origen '{from_state}' no existe en {bu_code}")
                
                for to_state in to_states:
                    if to_state not in config['states']:
                        raise ValueError(f"Estado destino '{to_state}' no existe en {bu_code}")
            
            # Verificar que todos los timeouts corresponden a estados válidos
            for state in config['timeouts']:
                if state not in config['states']:
                    raise ValueError(f"Timeout para estado '{state}' no existe en {bu_code}")
            
            # Verificar que todos los assessments existen
            for assessment in config['assessments']:
                if assessment not in self.assessment_configs:
                    raise ValueError(f"Assessment '{assessment}' no existe para {bu_code}")
        
        # Validar assessments
        for assessment_code, config in self.assessment_configs.items():
            if config['passing_score'] < 0 or config['passing_score'] > 100:
                raise ValueError(f"Puntaje mínimo inválido para {assessment_code}: {config['passing_score']}%")
            
            if config['questions_count'] <= 0:
                raise ValueError(f"Número de preguntas inválido para {assessment_code}: {config['questions_count']}")
            
            if config['time_limit_minutes'] <= 0:
                raise ValueError(f"Tiempo límite inválido para {assessment_code}: {config['time_limit_minutes']} minutos")
        
        logger.info("✅ Validación de workflows completada")
    
    def show_summary(self):
        """Muestra un resumen de la configuración."""
        print("\n" + "="*80)
        print("📋 RESUMEN DE CONFIGURACIÓN DE WORKFLOWS Y ASSESSMENTS")
        print("="*80)
        
        # Workflows
        print(f"\n🔄 WORKFLOWS CONFIGURADOS: {len(self.workflow_configs)}")
        for bu_code, config in self.workflow_configs.items():
            print(f"   ✅ {config['name']} ({bu_code})")
            print(f"      Estados: {len(config['states'])}")
            print(f"      Assessments: {len(config['assessments'])}")
        
        # Assessments
        print(f"\n📊 ASSESSMENTS CONFIGURADOS: {len(self.assessment_configs)}")
        for assessment_code, config in self.assessment_configs.items():
            print(f"   ✅ {config['name']} ({assessment_code})")
            print(f"      Preguntas: {config['questions_count']}")
            print(f"      Tiempo: {config['time_limit_minutes']} min")
            print(f"      Puntaje mínimo: {config['passing_score']}%")
        
        print("\n" + "="*80)
        print("🎉 ¡Configuración de Workflows y Assessments completada!")
        print("="*80)

def main():
    """Función principal."""
    print("🚀 Configurador de Workflows y Assessments huntRED®")
    print("="*60)
    
    configurator = WorkflowAssessmentConfigurator()
    
    try:
        # Ejecutar configuración
        configurator.run_configuration()
        
        # Mostrar resumen
        configurator.show_summary()
        
        print("\n📝 PRÓXIMOS PASOS:")
        print("1. Revisar los archivos de configuración generados")
        print("2. Personalizar las preguntas de los assessments")
        print("3. Ajustar los timeouts de los workflows según necesidades")
        print("4. Configurar las transiciones específicas por BU")
        print("5. Integrar con el sistema de chatbot")
        print("6. Probar los flujos de conversación")
        
        print("\n📚 ARCHIVOS GENERADOS:")
        print("- Workflows: config/workflows/")
        print("- Assessments: config/assessments/")
        print("- Logs: workflows_assessments_config.log")
        
    except Exception as e:
        logger.error(f"❌ Error en la configuración: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 