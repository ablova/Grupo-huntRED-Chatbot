# Sistema Integrado de Assessments - Grupo huntRED®

## Descripción General

El Sistema Integrado de Assessments de Grupo huntRED® es una plataforma avanzada de evaluación que combina múltiples dimensiones de análisis para proporcionar una visión holística de los candidatos. Este sistema permite realizar assessments individuales o integrados, generando insights profundos y accionables.

## Componentes Principales

### Analizadores

El sistema incluye los siguientes analizadores especializados:

1. **PersonalityAnalyzer**: Evalúa rasgos de personalidad, comportamiento, y compatibilidad con diferentes roles y entornos.
2. **CulturalAnalyzer**: Analiza la alineación de valores y la compatibilidad cultural con diferentes unidades de negocio.
3. **ProfessionalAnalyzer**: Evalúa competencias profesionales, experiencia, y potencial de desarrollo.
4. **TalentAnalyzer**: Analiza habilidades técnicas, aptitudes, y potencial para diversos roles.
5. **IntegratedAnalyzer**: Combina los resultados de los analizadores anteriores para generar insights holísticos.

### Gestores de Flujo

- **IntegratedAssessmentManager**: Proporciona una interfaz unificada para gestionar todos los tipos de assessments, permitiendo ejecutarlos individualmente o como conjunto integrado.

### Flujos de Trabajo

- **PersonalityAssessment**: Gestiona el flujo de evaluación de personalidad.
- **CulturalFitWorkflow**: Gestiona el flujo de evaluación de compatibilidad cultural.
- **ProfessionalDNAWorkflow**: Gestiona el flujo de evaluación de DNA profesional.
- **TalentAnalysisWorkflow**: Gestiona el flujo de evaluación de talento técnico.

## Características Principales

- **Análisis Holístico**: Integra diferentes dimensiones de evaluación para una comprensión completa del candidato.
- **Personalización por BU**: Adapta los análisis según la unidad de negocio (huntRED, huntU, Amigro, SEXSI).
- **Reportes Integrados**: Genera informes completos en diferentes formatos (HTML, PDF, texto).
- **Generación de CV**: Integración con el sistema de generación de CVs para crear perfiles profesionales enriquecidos.
- **Planes de Desarrollo**: Proporciona recomendaciones personalizadas para el crecimiento profesional.

## Uso del Sistema

### Realizar un Assessment Individual

```python
# Ejemplo: Realizar un assessment de personalidad
from app.ats.chatbot.workflow.assessments.integrated_assessment_manager import IntegratedAssessmentManager, AssessmentType

# Inicializar el gestor
assessment_manager = IntegratedAssessmentManager(business_unit="huntRED")

# Iniciar el assessment
welcome_message = await assessment_manager.initialize_assessment(
    AssessmentType.PERSONALITY,
    context={"persona_id": 12345}
)

# Procesar mensajes de usuario
response = await assessment_manager.process_assessment_message(
    AssessmentType.PERSONALITY,
    message="Me considero una persona analítica y metódica"
)

# Obtener resultados
results = await assessment_manager.get_assessment_results(
    AssessmentType.PERSONALITY,
    format_type="html"
)
```

### Realizar un Assessment Integrado

```python
# Inicializar assessments individuales
await assessment_manager.initialize_assessment(AssessmentType.PERSONALITY)
await assessment_manager.initialize_assessment(AssessmentType.CULTURAL)
await assessment_manager.initialize_assessment(AssessmentType.PROFESSIONAL)
await assessment_manager.initialize_assessment(AssessmentType.TALENT)

# Obtener resultados integrados
integrated_results = await assessment_manager.get_assessment_results(
    AssessmentType.INTEGRATED,
    format_type="html"
)

# Generar reporte integrado
report = await assessment_manager.generate_integrated_report(
    person_id=12345,
    include_assessments=["personality", "cultural", "professional", "talent"],
    report_format="pdf"
)
```

## Integración de Analizadores

El IntegratedAnalyzer combina los resultados de todos los analizadores individuales para proporcionar:

1. **Puntaje General**: Calcula un puntaje ponderado basado en todos los assessments.
2. **Análisis de Compatibilidad**: Evalúa la compatibilidad con diferentes roles y entornos.
3. **Análisis de Liderazgo**: Evalúa el potencial de liderazgo y el estilo de gestión.
4. **Plan de Desarrollo**: Genera un plan personalizado basado en las fortalezas y áreas de mejora.
5. **Métricas de Éxito**: Proporciona indicadores de éxito potencial en diferentes contextos.

## Configuración por Unidad de Negocio

Cada unidad de negocio tiene configuraciones específicas:

- **huntRED**: Enfoque en liderazgo ejecutivo, gestión estratégica y desarrollo de negocio.
- **huntU**: Enfoque en habilidades técnicas, análisis de datos y metodologías ágiles.
- **Amigro**: Enfoque en servicio comunitario, desarrollo social y comunicación intercultural.
- **SEXSI**: Enfoque en gestión de relaciones, confidencialidad y análisis de contratos.

## Extensión del Sistema

Para añadir nuevos tipos de assessments:

1. Crear un nuevo analizador que herede de BaseAnalyzer.
2. Implementar un flujo de trabajo específico.
3. Registrar el nuevo assessment en IntegratedAssessmentManager.
4. Actualizar IntegratedAnalyzer para incorporar los nuevos datos.

## Consideraciones Técnicas

- Los analizadores utilizan caché para optimizar el rendimiento.
- El sistema es compatible con operaciones asíncronas para mejorar la experiencia del usuario.
- La integración con generación de CV permite crear perfiles profesionales enriquecidos.
- Los resultados se pueden formatear en diferentes formatos (JSON, HTML, texto, PDF).

## Licencia

Este sistema es propiedad de Grupo huntRED® y su uso está restringido a personal autorizado.
