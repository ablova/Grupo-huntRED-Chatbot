"""
HuntRED® v2 - Onboarding Service
Complete employee onboarding and orientation system
"""

import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import json
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class OnboardingStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class TaskType(Enum):
    DOCUMENT_UPLOAD = "document_upload"
    FORM_COMPLETION = "form_completion"
    TRAINING_MODULE = "training_module"
    MEETING = "meeting"
    SYSTEM_ACCESS = "system_access"
    EQUIPMENT_ASSIGNMENT = "equipment_assignment"
    ORIENTATION = "orientation"
    POLICY_REVIEW = "policy_review"

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    SKIPPED = "skipped"

class OnboardingService:
    """Complete employee onboarding system"""
    
    def __init__(self, db):
        self.db = db
        
        # Onboarding templates by position/department
        self.onboarding_templates = {
            "general": {
                "name": "Onboarding General",
                "description": "Proceso estándar para todos los empleados",
                "duration_days": 30,
                "tasks": [
                    {
                        "id": "welcome_email",
                        "name": "Email de Bienvenida",
                        "type": TaskType.FORM_COMPLETION.value,
                        "description": "Envío automático de email de bienvenida",
                        "due_days": 0,
                        "mandatory": True,
                        "automated": True
                    },
                    {
                        "id": "personal_info",
                        "name": "Información Personal",
                        "type": TaskType.FORM_COMPLETION.value,
                        "description": "Completar formulario de información personal",
                        "due_days": 1,
                        "mandatory": True,
                        "form_id": "personal_info_form"
                    },
                    {
                        "id": "documents_upload",
                        "name": "Subir Documentos",
                        "type": TaskType.DOCUMENT_UPLOAD.value,
                        "description": "Subir documentos requeridos (INE, CURP, RFC, etc.)",
                        "due_days": 3,
                        "mandatory": True,
                        "required_documents": ["ine", "curp", "rfc", "acta_nacimiento", "comprobante_domicilio"]
                    },
                    {
                        "id": "company_policies",
                        "name": "Políticas de la Empresa",
                        "type": TaskType.POLICY_REVIEW.value,
                        "description": "Revisar y aceptar políticas de la empresa",
                        "due_days": 5,
                        "mandatory": True,
                        "policies": ["codigo_conducta", "politica_privacidad", "reglamento_interno"]
                    },
                    {
                        "id": "system_access",
                        "name": "Acceso a Sistemas",
                        "type": TaskType.SYSTEM_ACCESS.value,
                        "description": "Configurar acceso a sistemas y aplicaciones",
                        "due_days": 7,
                        "mandatory": True,
                        "systems": ["email", "huntred_app", "intranet"]
                    },
                    {
                        "id": "orientation_meeting",
                        "name": "Reunión de Orientación",
                        "type": TaskType.MEETING.value,
                        "description": "Reunión inicial con RRHH",
                        "due_days": 10,
                        "mandatory": True,
                        "duration_minutes": 60,
                        "attendees": ["hr_manager", "direct_supervisor"]
                    },
                    {
                        "id": "safety_training",
                        "name": "Capacitación en Seguridad",
                        "type": TaskType.TRAINING_MODULE.value,
                        "description": "Módulo de capacitación en seguridad laboral",
                        "due_days": 15,
                        "mandatory": True,
                        "training_id": "safety_101"
                    },
                    {
                        "id": "equipment_assignment",
                        "name": "Asignación de Equipo",
                        "type": TaskType.EQUIPMENT_ASSIGNMENT.value,
                        "description": "Asignar equipo de trabajo necesario",
                        "due_days": 7,
                        "mandatory": True,
                        "equipment_types": ["laptop", "phone", "access_card"]
                    },
                    {
                        "id": "30_day_checkin",
                        "name": "Check-in 30 días",
                        "type": TaskType.MEETING.value,
                        "description": "Reunión de seguimiento a los 30 días",
                        "due_days": 30,
                        "mandatory": True,
                        "duration_minutes": 30,
                        "attendees": ["hr_manager", "direct_supervisor"]
                    }
                ]
            },
            "developer": {
                "name": "Onboarding Desarrollador",
                "description": "Proceso específico para desarrolladores",
                "duration_days": 45,
                "extends": "general",
                "additional_tasks": [
                    {
                        "id": "dev_environment",
                        "name": "Configuración de Entorno",
                        "type": TaskType.SYSTEM_ACCESS.value,
                        "description": "Configurar entorno de desarrollo",
                        "due_days": 3,
                        "mandatory": True,
                        "systems": ["github", "jira", "slack", "docker"]
                    },
                    {
                        "id": "code_review_training",
                        "name": "Capacitación Code Review",
                        "type": TaskType.TRAINING_MODULE.value,
                        "description": "Proceso de revisión de código",
                        "due_days": 14,
                        "mandatory": True,
                        "training_id": "code_review_101"
                    },
                    {
                        "id": "architecture_overview",
                        "name": "Arquitectura del Sistema",
                        "type": TaskType.TRAINING_MODULE.value,
                        "description": "Visión general de la arquitectura",
                        "due_days": 21,
                        "mandatory": True,
                        "training_id": "architecture_overview"
                    }
                ]
            },
            "manager": {
                "name": "Onboarding Manager",
                "description": "Proceso específico para managers",
                "duration_days": 60,
                "extends": "general",
                "additional_tasks": [
                    {
                        "id": "leadership_training",
                        "name": "Capacitación en Liderazgo",
                        "type": TaskType.TRAINING_MODULE.value,
                        "description": "Módulo de liderazgo y gestión",
                        "due_days": 30,
                        "mandatory": True,
                        "training_id": "leadership_101"
                    },
                    {
                        "id": "budget_access",
                        "name": "Acceso a Presupuestos",
                        "type": TaskType.SYSTEM_ACCESS.value,
                        "description": "Configurar acceso a sistemas financieros",
                        "due_days": 14,
                        "mandatory": True,
                        "systems": ["budget_system", "expense_reports"]
                    },
                    {
                        "id": "team_introduction",
                        "name": "Presentación del Equipo",
                        "type": TaskType.MEETING.value,
                        "description": "Reunión con el equipo a cargo",
                        "due_days": 7,
                        "mandatory": True,
                        "duration_minutes": 90,
                        "attendees": ["team_members", "hr_manager"]
                    }
                ]
            }
        }
        
        # Document templates
        self.document_requirements = {
            "ine": {
                "name": "Identificación Oficial (INE)",
                "description": "Copia de credencial de elector vigente",
                "mandatory": True,
                "validation_rules": ["valid_format", "not_expired"]
            },
            "curp": {
                "name": "CURP",
                "description": "Clave Única de Registro de Población",
                "mandatory": True,
                "validation_rules": ["valid_format", "matches_name"]
            },
            "rfc": {
                "name": "RFC",
                "description": "Registro Federal de Contribuyentes",
                "mandatory": True,
                "validation_rules": ["valid_format", "active_status"]
            },
            "acta_nacimiento": {
                "name": "Acta de Nacimiento",
                "description": "Copia certificada del acta de nacimiento",
                "mandatory": True,
                "validation_rules": ["valid_format", "matches_curp"]
            },
            "comprobante_domicilio": {
                "name": "Comprobante de Domicilio",
                "description": "Recibo de servicios no mayor a 3 meses",
                "mandatory": True,
                "validation_rules": ["valid_format", "recent_date"]
            }
        }
    
    async def create_onboarding_process(self, employee_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create onboarding process for new employee"""
        try:
            onboarding_id = str(uuid.uuid4())
            
            # Determine onboarding template
            position = employee_data.get("position", "general")
            department = employee_data.get("department", "general")
            
            template_name = self._determine_template(position, department)
            template = self.onboarding_templates.get(template_name, self.onboarding_templates["general"])
            
            # Create onboarding process
            onboarding_process = {
                "id": onboarding_id,
                "employee_id": employee_data["employee_id"],
                "employee_info": employee_data,
                "template_name": template_name,
                "status": OnboardingStatus.NOT_STARTED.value,
                "created_at": datetime.now(),
                "start_date": employee_data.get("start_date", datetime.now()),
                "expected_completion": datetime.now() + timedelta(days=template["duration_days"]),
                "progress": {
                    "total_tasks": 0,
                    "completed_tasks": 0,
                    "percentage": 0
                },
                "tasks": [],
                "documents": {},
                "meetings": [],
                "notifications": []
            }
            
            # Generate tasks from template
            tasks = await self._generate_tasks_from_template(template, onboarding_process)
            onboarding_process["tasks"] = tasks
            onboarding_process["progress"]["total_tasks"] = len(tasks)
            
            # Save onboarding process
            # await self._save_onboarding_process(onboarding_process)
            
            # Send welcome notification
            await self._send_welcome_notification(onboarding_process)
            
            logger.info(f"Onboarding process {onboarding_id} created for employee {employee_data['employee_id']}")
            
            return {
                "success": True,
                "onboarding_id": onboarding_id,
                "onboarding_process": onboarding_process
            }
            
        except Exception as e:
            logger.error(f"Error creating onboarding process: {e}")
            return {"success": False, "error": str(e)}
    
    def _determine_template(self, position: str, department: str) -> str:
        """Determine which onboarding template to use"""
        
        # Check for position-specific templates
        position_lower = position.lower()
        if "developer" in position_lower or "programador" in position_lower:
            return "developer"
        elif "manager" in position_lower or "gerente" in position_lower or "supervisor" in position_lower:
            return "manager"
        
        # Check for department-specific templates
        department_lower = department.lower()
        if "desarrollo" in department_lower or "tecnologia" in department_lower:
            return "developer"
        
        return "general"
    
    async def _generate_tasks_from_template(self, template: Dict[str, Any], 
                                          onboarding_process: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate tasks from onboarding template"""
        
        tasks = []
        start_date = onboarding_process["start_date"]
        
        # Base tasks
        for task_template in template["tasks"]:
            task = await self._create_task_from_template(task_template, start_date)
            tasks.append(task)
        
        # Additional tasks if template extends another
        if template.get("extends") and template.get("additional_tasks"):
            for task_template in template["additional_tasks"]:
                task = await self._create_task_from_template(task_template, start_date)
                tasks.append(task)
        
        return tasks
    
    async def _create_task_from_template(self, task_template: Dict[str, Any], 
                                       start_date: datetime) -> Dict[str, Any]:
        """Create task from template"""
        
        task_id = str(uuid.uuid4())
        due_date = start_date + timedelta(days=task_template["due_days"])
        
        task = {
            "id": task_id,
            "template_id": task_template["id"],
            "name": task_template["name"],
            "type": task_template["type"],
            "description": task_template["description"],
            "status": TaskStatus.PENDING.value,
            "mandatory": task_template.get("mandatory", False),
            "automated": task_template.get("automated", False),
            "due_date": due_date,
            "created_at": datetime.now(),
            "progress": 0,
            "metadata": {}
        }
        
        # Add type-specific metadata
        if task_template["type"] == TaskType.DOCUMENT_UPLOAD.value:
            task["metadata"]["required_documents"] = task_template.get("required_documents", [])
        elif task_template["type"] == TaskType.MEETING.value:
            task["metadata"]["duration_minutes"] = task_template.get("duration_minutes", 60)
            task["metadata"]["attendees"] = task_template.get("attendees", [])
        elif task_template["type"] == TaskType.TRAINING_MODULE.value:
            task["metadata"]["training_id"] = task_template.get("training_id")
        elif task_template["type"] == TaskType.SYSTEM_ACCESS.value:
            task["metadata"]["systems"] = task_template.get("systems", [])
        elif task_template["type"] == TaskType.FORM_COMPLETION.value:
            task["metadata"]["form_id"] = task_template.get("form_id")
        elif task_template["type"] == TaskType.POLICY_REVIEW.value:
            task["metadata"]["policies"] = task_template.get("policies", [])
        elif task_template["type"] == TaskType.EQUIPMENT_ASSIGNMENT.value:
            task["metadata"]["equipment_types"] = task_template.get("equipment_types", [])
        
        return task
    
    async def _send_welcome_notification(self, onboarding_process: Dict[str, Any]) -> None:
        """Send welcome notification to new employee"""
        # Mock notification sending
        logger.info(f"Welcome notification sent to employee {onboarding_process['employee_id']}")
    
    async def complete_task(self, onboarding_id: str, task_id: str, 
                          completion_data: Dict[str, Any]) -> Dict[str, Any]:
        """Complete an onboarding task"""
        try:
            # Get onboarding process
            onboarding_process = await self._get_onboarding_process(onboarding_id)
            
            if not onboarding_process:
                return {"success": False, "error": "Onboarding process not found"}
            
            # Find task
            task = None
            for t in onboarding_process["tasks"]:
                if t["id"] == task_id:
                    task = t
                    break
            
            if not task:
                return {"success": False, "error": "Task not found"}
            
            if task["status"] == TaskStatus.COMPLETED.value:
                return {"success": False, "error": "Task already completed"}
            
            # Validate completion data based on task type
            validation_result = await self._validate_task_completion(task, completion_data)
            if not validation_result["valid"]:
                return {"success": False, "error": validation_result["error"]}
            
            # Update task status
            task["status"] = TaskStatus.COMPLETED.value
            task["completed_at"] = datetime.now()
            task["completion_data"] = completion_data
            task["progress"] = 100
            
            # Update onboarding progress
            await self._update_onboarding_progress(onboarding_process)
            
            # Save updated process
            # await self._save_onboarding_process(onboarding_process)
            
            # Send completion notification
            await self._send_task_completion_notification(onboarding_process, task)
            
            # Check if onboarding is complete
            if onboarding_process["progress"]["percentage"] == 100:
                await self._complete_onboarding_process(onboarding_process)
            
            logger.info(f"Task {task_id} completed for onboarding {onboarding_id}")
            
            return {
                "success": True,
                "task_id": task_id,
                "onboarding_progress": onboarding_process["progress"]
            }
            
        except Exception as e:
            logger.error(f"Error completing task: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_onboarding_process(self, onboarding_id: str) -> Optional[Dict[str, Any]]:
        """Get onboarding process by ID"""
        # Mock implementation
        return {
            "id": onboarding_id,
            "employee_id": "emp_123",
            "status": OnboardingStatus.IN_PROGRESS.value,
            "tasks": [
                {
                    "id": "task_1",
                    "name": "Test Task",
                    "type": TaskType.FORM_COMPLETION.value,
                    "status": TaskStatus.PENDING.value,
                    "metadata": {}
                }
            ],
            "progress": {"total_tasks": 1, "completed_tasks": 0, "percentage": 0}
        }
    
    async def _validate_task_completion(self, task: Dict[str, Any], 
                                      completion_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate task completion data"""
        
        task_type = task["type"]
        
        if task_type == TaskType.DOCUMENT_UPLOAD.value:
            return await self._validate_document_upload(task, completion_data)
        elif task_type == TaskType.FORM_COMPLETION.value:
            return await self._validate_form_completion(task, completion_data)
        elif task_type == TaskType.TRAINING_MODULE.value:
            return await self._validate_training_completion(task, completion_data)
        elif task_type == TaskType.MEETING.value:
            return await self._validate_meeting_completion(task, completion_data)
        elif task_type == TaskType.POLICY_REVIEW.value:
            return await self._validate_policy_review(task, completion_data)
        else:
            return {"valid": True}
    
    async def _validate_document_upload(self, task: Dict[str, Any], 
                                      completion_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate document upload"""
        
        required_documents = task["metadata"].get("required_documents", [])
        uploaded_documents = completion_data.get("documents", {})
        
        for doc_type in required_documents:
            if doc_type not in uploaded_documents:
                return {"valid": False, "error": f"Missing required document: {doc_type}"}
            
            # Validate document
            doc_validation = await self._validate_document(doc_type, uploaded_documents[doc_type])
            if not doc_validation["valid"]:
                return {"valid": False, "error": f"Invalid document {doc_type}: {doc_validation['error']}"}
        
        return {"valid": True}
    
    async def _validate_document(self, doc_type: str, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate individual document"""
        
        doc_requirements = self.document_requirements.get(doc_type, {})
        validation_rules = doc_requirements.get("validation_rules", [])
        
        for rule in validation_rules:
            if rule == "valid_format":
                if not document_data.get("file_url"):
                    return {"valid": False, "error": "Missing file"}
            elif rule == "not_expired":
                # Mock validation
                pass
            elif rule == "matches_name":
                # Mock validation
                pass
        
        return {"valid": True}
    
    async def _validate_form_completion(self, task: Dict[str, Any], 
                                      completion_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate form completion"""
        
        form_data = completion_data.get("form_data", {})
        if not form_data:
            return {"valid": False, "error": "Form data is required"}
        
        return {"valid": True}
    
    async def _validate_training_completion(self, task: Dict[str, Any], 
                                          completion_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate training completion"""
        
        score = completion_data.get("score", 0)
        if score < 80:  # Minimum passing score
            return {"valid": False, "error": "Minimum score of 80% required"}
        
        return {"valid": True}
    
    async def _validate_meeting_completion(self, task: Dict[str, Any], 
                                         completion_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate meeting completion"""
        
        attendees = completion_data.get("attendees", [])
        if not attendees:
            return {"valid": False, "error": "Meeting attendees are required"}
        
        return {"valid": True}
    
    async def _validate_policy_review(self, task: Dict[str, Any], 
                                    completion_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate policy review"""
        
        policies_accepted = completion_data.get("policies_accepted", [])
        required_policies = task["metadata"].get("policies", [])
        
        for policy in required_policies:
            if policy not in policies_accepted:
                return {"valid": False, "error": f"Policy not accepted: {policy}"}
        
        return {"valid": True}
    
    async def _update_onboarding_progress(self, onboarding_process: Dict[str, Any]) -> None:
        """Update onboarding progress"""
        
        total_tasks = len(onboarding_process["tasks"])
        completed_tasks = len([t for t in onboarding_process["tasks"] if t["status"] == TaskStatus.COMPLETED.value])
        
        onboarding_process["progress"] = {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "percentage": round((completed_tasks / total_tasks) * 100, 2) if total_tasks > 0 else 0
        }
        
        # Update overall status
        if completed_tasks == 0:
            onboarding_process["status"] = OnboardingStatus.NOT_STARTED.value
        elif completed_tasks == total_tasks:
            onboarding_process["status"] = OnboardingStatus.COMPLETED.value
        else:
            onboarding_process["status"] = OnboardingStatus.IN_PROGRESS.value
    
    async def _send_task_completion_notification(self, onboarding_process: Dict[str, Any], 
                                               task: Dict[str, Any]) -> None:
        """Send task completion notification"""
        # Mock notification
        logger.info(f"Task completion notification sent for task {task['id']}")
    
    async def _complete_onboarding_process(self, onboarding_process: Dict[str, Any]) -> None:
        """Complete onboarding process"""
        
        onboarding_process["status"] = OnboardingStatus.COMPLETED.value
        onboarding_process["completed_at"] = datetime.now()
        
        # Send completion notification
        await self._send_onboarding_completion_notification(onboarding_process)
        
        # Create follow-up tasks
        await self._create_followup_tasks(onboarding_process)
        
        logger.info(f"Onboarding process {onboarding_process['id']} completed")
    
    async def _send_onboarding_completion_notification(self, onboarding_process: Dict[str, Any]) -> None:
        """Send onboarding completion notification"""
        # Mock notification
        logger.info(f"Onboarding completion notification sent for {onboarding_process['employee_id']}")
    
    async def _create_followup_tasks(self, onboarding_process: Dict[str, Any]) -> None:
        """Create follow-up tasks after onboarding"""
        
        # 90-day check-in
        followup_task = {
            "id": str(uuid.uuid4()),
            "name": "Check-in 90 días",
            "type": TaskType.MEETING.value,
            "description": "Reunión de seguimiento a los 90 días",
            "due_date": datetime.now() + timedelta(days=90),
            "assignee": "hr_manager"
        }
        
        # Mock task creation
        logger.info(f"90-day follow-up task created for {onboarding_process['employee_id']}")
    
    async def get_onboarding_dashboard(self, employee_id: str) -> Dict[str, Any]:
        """Get onboarding dashboard for employee"""
        try:
            # Get onboarding process
            onboarding_process = await self._get_onboarding_process_by_employee(employee_id)
            
            if not onboarding_process:
                return {"success": False, "error": "Onboarding process not found"}
            
            # Get upcoming tasks
            upcoming_tasks = [
                task for task in onboarding_process["tasks"]
                if task["status"] == TaskStatus.PENDING.value
            ]
            
            # Get overdue tasks
            overdue_tasks = [
                task for task in upcoming_tasks
                if datetime.fromisoformat(task["due_date"]) < datetime.now()
            ]
            
            # Get completed tasks
            completed_tasks = [
                task for task in onboarding_process["tasks"]
                if task["status"] == TaskStatus.COMPLETED.value
            ]
            
            dashboard = {
                "onboarding_id": onboarding_process["id"],
                "employee_id": employee_id,
                "status": onboarding_process["status"],
                "progress": onboarding_process["progress"],
                "start_date": onboarding_process["start_date"],
                "expected_completion": onboarding_process["expected_completion"],
                "upcoming_tasks": upcoming_tasks[:5],  # Next 5 tasks
                "overdue_tasks": overdue_tasks,
                "completed_tasks": completed_tasks[-5:],  # Last 5 completed
                "documents_status": await self._get_documents_status(onboarding_process),
                "next_milestone": await self._get_next_milestone(onboarding_process)
            }
            
            return {
                "success": True,
                "dashboard": dashboard
            }
            
        except Exception as e:
            logger.error(f"Error getting onboarding dashboard: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_onboarding_process_by_employee(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """Get onboarding process by employee ID"""
        # Mock implementation
        return {
            "id": "onboarding_123",
            "employee_id": employee_id,
            "status": OnboardingStatus.IN_PROGRESS.value,
            "progress": {"total_tasks": 9, "completed_tasks": 3, "percentage": 33.33},
            "start_date": datetime.now() - timedelta(days=5),
            "expected_completion": datetime.now() + timedelta(days=25),
            "tasks": [
                {
                    "id": "task_1",
                    "name": "Información Personal",
                    "status": TaskStatus.COMPLETED.value,
                    "due_date": (datetime.now() - timedelta(days=4)).isoformat()
                },
                {
                    "id": "task_2",
                    "name": "Subir Documentos",
                    "status": TaskStatus.PENDING.value,
                    "due_date": (datetime.now() + timedelta(days=2)).isoformat()
                }
            ]
        }
    
    async def _get_documents_status(self, onboarding_process: Dict[str, Any]) -> Dict[str, Any]:
        """Get documents upload status"""
        
        # Mock implementation
        return {
            "total_required": 5,
            "uploaded": 2,
            "pending": 3,
            "documents": {
                "ine": {"status": "uploaded", "uploaded_at": "2024-01-15T10:00:00"},
                "curp": {"status": "uploaded", "uploaded_at": "2024-01-15T10:05:00"},
                "rfc": {"status": "pending"},
                "acta_nacimiento": {"status": "pending"},
                "comprobante_domicilio": {"status": "pending"}
            }
        }
    
    async def _get_next_milestone(self, onboarding_process: Dict[str, Any]) -> Dict[str, Any]:
        """Get next milestone in onboarding process"""
        
        # Mock implementation
        return {
            "name": "Reunión de Orientación",
            "due_date": (datetime.now() + timedelta(days=5)).isoformat(),
            "description": "Reunión inicial con RRHH y supervisor directo",
            "progress_required": 50  # 50% of tasks must be completed
        }
    
    async def get_onboarding_analytics(self, date_range: Dict[str, Any]) -> Dict[str, Any]:
        """Get onboarding analytics"""
        try:
            # Mock analytics data
            analytics = {
                "period": date_range,
                "total_onboardings": 45,
                "completed_onboardings": 38,
                "in_progress": 7,
                "completion_rate": 84.4,
                "average_completion_time": 28.5,  # days
                "by_department": {
                    "desarrollo": {"total": 15, "completed": 13, "avg_time": 32.1},
                    "ventas": {"total": 12, "completed": 10, "avg_time": 25.3},
                    "marketing": {"total": 8, "completed": 7, "avg_time": 27.8},
                    "rrhh": {"total": 5, "completed": 4, "avg_time": 30.2},
                    "finanzas": {"total": 5, "completed": 4, "avg_time": 26.5}
                },
                "common_bottlenecks": [
                    {"task": "Subir Documentos", "avg_delay": 3.2},
                    {"task": "Capacitación en Seguridad", "avg_delay": 2.8},
                    {"task": "Acceso a Sistemas", "avg_delay": 2.1}
                ],
                "satisfaction_score": 4.3,  # out of 5
                "feedback_highlights": [
                    "Proceso claro y bien estructurado",
                    "Buen soporte de RRHH",
                    "Falta más tiempo para capacitaciones"
                ]
            }
            
            return {
                "success": True,
                "analytics": analytics
            }
            
        except Exception as e:
            logger.error(f"Error getting onboarding analytics: {e}")
            return {"success": False, "error": str(e)}

# Global onboarding service
def get_onboarding_service(db) -> OnboardingService:
    """Get onboarding service instance"""
    return OnboardingService(db)