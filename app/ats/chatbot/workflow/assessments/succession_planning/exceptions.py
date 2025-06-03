"""
Excepciones personalizadas para el módulo de Plan de Sucesión.
"""

class SuccessionPlanningError(Exception):
    """Excepción base para errores en el módulo de Plan de Sucesión."""
    pass

class EmployeeNotFound(SuccessionPlanningError):
    """Se lanza cuando no se encuentra un empleado."""
    def __init__(self, employee_id: str):
        self.employee_id = employee_id
        super().__init__(f"Empleado con ID {employee_id} no encontrado")

class PositionNotFound(SuccessionPlanningError):
    """Se lanza cuando no se encuentra un puesto."""
    def __init__(self, position_id: str):
        self.position_id = position_id
        super().__init__(f"Puesto con ID {position_id} no encontrado")

class InvalidAssessmentData(SuccessionPlanningError):
    """Se lanza cuando los datos de evaluación no son válidos."""
    def __init__(self, message: str = "Datos de evaluación no válidos"):
        self.message = message
        super().__init__(message)

class SuccessionPlanNotFound(SuccessionPlanningError):
    """Se lanza cuando no se encuentra un plan de sucesión."""
    def __init__(self, plan_id: str = None):
        self.plan_id = plan_id
        msg = "Plan de sucesión no encontrado"
        if plan_id:
            msg += f" con ID {plan_id}"
        super().__init__(msg)

class SuccessionCandidateNotFound(SuccessionPlanningError):
    """Se lanza cuando no se encuentra un candidato en un plan de sucesión."""
    def __init__(self, candidate_id: str = None):
        self.candidate_id = candidate_id
        msg = "Candidato no encontrado en el plan de sucesión"
        if candidate_id:
            msg += f" con ID {candidate_id}"
        super().__init__(msg)

class ReadinessAssessmentError(SuccessionPlanningError):
    """Se lanza cuando hay un error al evaluar la preparación de un candidato."""
    def __init__(self, message: str = "Error al evaluar la preparación del candidato"):
        self.message = message
        super().__init__(message)

class DevelopmentPlanError(SuccessionPlanningError):
    """Se lanza cuando hay un error al generar un plan de desarrollo."""
    def __init__(self, message: str = "Error al generar el plan de desarrollo"):
        self.message = message
        super().__init__(message)

class SuccessionReportError(SuccessionPlanningError):
    """Se lanza cuando hay un error al generar un informe de sucesión."""
    def __init__(self, report_type: str = None, message: str = None):
        self.report_type = report_type
        if not message:
            message = f"Error al generar el informe de sucesión"
            if report_type:
                message += f" de tipo {report_type}"
        super().__init__(message)

class SuccessionQuestionnaireError(SuccessionPlanningError):
    """Se lanza cuando hay un error en el cuestionario de sucesión."""
    def __init__(self, message: str = "Error en el cuestionario de sucesión"):
        self.message = message
        super().__init__(message)

class SuccessionDataValidationError(SuccessionPlanningError):
    """Se lanza cuando los datos de sucesión no superan la validación."""
    def __init__(self, field: str = None, message: str = None):
        self.field = field
        if not message:
            message = "Error de validación en los datos de sucesión"
            if field:
                message += f" en el campo {field}"
        super().__init__(message)

class SuccessionIntegrationError(SuccessionPlanningError):
    """Se lanza cuando hay un error de integración con otros sistemas."""
    def __init__(self, system: str = None, message: str = None):
        self.system = system
        if not message:
            message = "Error de integración"
            if system:
                message += f" con el sistema {system}"
        super().__init__(message)
