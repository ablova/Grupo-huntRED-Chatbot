"""
HuntRED® v2 - Workflows Service
Complete workflow automation and business process management system
"""

import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import json
import logging
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)

class WorkflowStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"

class WorkflowType(Enum):
    APPROVAL = "approval"
    NOTIFICATION = "notification"
    DATA_PROCESSING = "data_processing"
    INTEGRATION = "integration"
    SCHEDULED = "scheduled"
    EVENT_DRIVEN = "event_driven"

class StepType(Enum):
    START = "start"
    END = "end"
    TASK = "task"
    DECISION = "decision"
    APPROVAL = "approval"
    NOTIFICATION = "notification"
    API_CALL = "api_call"
    DATA_TRANSFORM = "data_transform"
    DELAY = "delay"
    PARALLEL = "parallel"
    MERGE = "merge"

class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WAITING = "waiting"

class WorkflowsService:
    """Complete workflow automation system"""
    
    def __init__(self, db):
        self.db = db
        
        # Predefined workflow templates
        self.workflow_templates = {
            "employee_onboarding": {
                "name": "Employee Onboarding Workflow",
                "description": "Automated employee onboarding process",
                "type": WorkflowType.EVENT_DRIVEN.value,
                "trigger": {
                    "event": "employee_created",
                    "conditions": []
                },
                "steps": [
                    {
                        "id": "start",
                        "type": StepType.START.value,
                        "name": "Start Onboarding",
                        "next": ["send_welcome"]
                    },
                    {
                        "id": "send_welcome",
                        "type": StepType.NOTIFICATION.value,
                        "name": "Send Welcome Email",
                        "config": {
                            "template": "welcome_email",
                            "recipient": "{{employee.email}}"
                        },
                        "next": ["create_accounts"]
                    },
                    {
                        "id": "create_accounts",
                        "type": StepType.TASK.value,
                        "name": "Create System Accounts",
                        "config": {
                            "assignee": "it_admin",
                            "systems": ["email", "intranet", "huntred"]
                        },
                        "next": ["hr_approval"]
                    },
                    {
                        "id": "hr_approval",
                        "type": StepType.APPROVAL.value,
                        "name": "HR Manager Approval",
                        "config": {
                            "approver": "hr_manager",
                            "timeout_hours": 24
                        },
                        "next": ["equipment_assignment", "document_request"]
                    },
                    {
                        "id": "equipment_assignment",
                        "type": StepType.TASK.value,
                        "name": "Assign Equipment",
                        "config": {
                            "assignee": "it_admin",
                            "equipment": ["laptop", "phone", "access_card"]
                        },
                        "next": ["merge_tasks"]
                    },
                    {
                        "id": "document_request",
                        "type": StepType.NOTIFICATION.value,
                        "name": "Request Documents",
                        "config": {
                            "template": "document_request",
                            "recipient": "{{employee.email}}"
                        },
                        "next": ["merge_tasks"]
                    },
                    {
                        "id": "merge_tasks",
                        "type": StepType.MERGE.value,
                        "name": "Wait for Tasks",
                        "next": ["orientation_meeting"]
                    },
                    {
                        "id": "orientation_meeting",
                        "type": StepType.TASK.value,
                        "name": "Schedule Orientation",
                        "config": {
                            "assignee": "hr_manager",
                            "duration": 60
                        },
                        "next": ["end"]
                    },
                    {
                        "id": "end",
                        "type": StepType.END.value,
                        "name": "Onboarding Complete"
                    }
                ]
            },
            "expense_approval": {
                "name": "Expense Approval Workflow",
                "description": "Multi-level expense approval process",
                "type": WorkflowType.APPROVAL.value,
                "trigger": {
                    "event": "expense_submitted",
                    "conditions": []
                },
                "steps": [
                    {
                        "id": "start",
                        "type": StepType.START.value,
                        "name": "Expense Submitted",
                        "next": ["amount_check"]
                    },
                    {
                        "id": "amount_check",
                        "type": StepType.DECISION.value,
                        "name": "Check Amount",
                        "config": {
                            "conditions": [
                                {
                                    "if": "{{expense.amount}} < 1000",
                                    "then": "supervisor_approval"
                                },
                                {
                                    "if": "{{expense.amount}} >= 1000 AND {{expense.amount}} < 5000",
                                    "then": "manager_approval"
                                },
                                {
                                    "else": "director_approval"
                                }
                            ]
                        }
                    },
                    {
                        "id": "supervisor_approval",
                        "type": StepType.APPROVAL.value,
                        "name": "Supervisor Approval",
                        "config": {
                            "approver": "{{employee.supervisor}}",
                            "timeout_hours": 48
                        },
                        "next": ["finance_processing"]
                    },
                    {
                        "id": "manager_approval",
                        "type": StepType.APPROVAL.value,
                        "name": "Manager Approval",
                        "config": {
                            "approver": "{{employee.manager}}",
                            "timeout_hours": 72
                        },
                        "next": ["finance_processing"]
                    },
                    {
                        "id": "director_approval",
                        "type": StepType.APPROVAL.value,
                        "name": "Director Approval",
                        "config": {
                            "approver": "finance_director",
                            "timeout_hours": 120
                        },
                        "next": ["finance_processing"]
                    },
                    {
                        "id": "finance_processing",
                        "type": StepType.TASK.value,
                        "name": "Process Payment",
                        "config": {
                            "assignee": "finance_team",
                            "action": "process_payment"
                        },
                        "next": ["notify_completion"]
                    },
                    {
                        "id": "notify_completion",
                        "type": StepType.NOTIFICATION.value,
                        "name": "Notify Employee",
                        "config": {
                            "template": "expense_approved",
                            "recipient": "{{employee.email}}"
                        },
                        "next": ["end"]
                    },
                    {
                        "id": "end",
                        "type": StepType.END.value,
                        "name": "Process Complete"
                    }
                ]
            },
            "payroll_processing": {
                "name": "Monthly Payroll Processing",
                "description": "Automated monthly payroll workflow",
                "type": WorkflowType.SCHEDULED.value,
                "trigger": {
                    "schedule": "0 0 25 * *",  # 25th of every month
                    "timezone": "America/Mexico_City"
                },
                "steps": [
                    {
                        "id": "start",
                        "type": StepType.START.value,
                        "name": "Start Payroll",
                        "next": ["gather_data"]
                    },
                    {
                        "id": "gather_data",
                        "type": StepType.DATA_TRANSFORM.value,
                        "name": "Gather Payroll Data",
                        "config": {
                            "sources": ["attendance", "overtime", "bonuses", "deductions"],
                            "period": "current_month"
                        },
                        "next": ["calculate_payroll"]
                    },
                    {
                        "id": "calculate_payroll",
                        "type": StepType.API_CALL.value,
                        "name": "Calculate Payroll",
                        "config": {
                            "service": "payroll_engine",
                            "method": "calculate_monthly_payroll",
                            "params": "{{gathered_data}}"
                        },
                        "next": ["hr_review"]
                    },
                    {
                        "id": "hr_review",
                        "type": StepType.APPROVAL.value,
                        "name": "HR Review",
                        "config": {
                            "approver": "hr_manager",
                            "timeout_hours": 24,
                            "data": "{{payroll_calculations}}"
                        },
                        "next": ["finance_approval"]
                    },
                    {
                        "id": "finance_approval",
                        "type": StepType.APPROVAL.value,
                        "name": "Finance Approval",
                        "config": {
                            "approver": "finance_manager",
                            "timeout_hours": 24
                        },
                        "next": ["generate_payslips"]
                    },
                    {
                        "id": "generate_payslips",
                        "type": StepType.API_CALL.value,
                        "name": "Generate Payslips",
                        "config": {
                            "service": "payroll_engine",
                            "method": "generate_payslips",
                            "params": "{{approved_payroll}}"
                        },
                        "next": ["process_payments"]
                    },
                    {
                        "id": "process_payments",
                        "type": StepType.API_CALL.value,
                        "name": "Process Bank Transfers",
                        "config": {
                            "service": "banking_api",
                            "method": "process_bulk_transfer",
                            "params": "{{payroll_data}}"
                        },
                        "next": ["notify_employees"]
                    },
                    {
                        "id": "notify_employees",
                        "type": StepType.NOTIFICATION.value,
                        "name": "Notify Employees",
                        "config": {
                            "template": "payroll_processed",
                            "recipients": "{{all_employees}}"
                        },
                        "next": ["end"]
                    },
                    {
                        "id": "end",
                        "type": StepType.END.value,
                        "name": "Payroll Complete"
                    }
                ]
            }
        }
        
        # Step execution handlers
        self.step_handlers = {
            StepType.TASK.value: self._execute_task_step,
            StepType.APPROVAL.value: self._execute_approval_step,
            StepType.NOTIFICATION.value: self._execute_notification_step,
            StepType.API_CALL.value: self._execute_api_call_step,
            StepType.DATA_TRANSFORM.value: self._execute_data_transform_step,
            StepType.DECISION.value: self._execute_decision_step,
            StepType.DELAY.value: self._execute_delay_step,
            StepType.PARALLEL.value: self._execute_parallel_step,
            StepType.MERGE.value: self._execute_merge_step
        }
    
    async def create_workflow(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new workflow"""
        try:
            workflow_id = str(uuid.uuid4())
            
            # Use template if specified
            if workflow_data.get("template"):
                template_name = workflow_data["template"]
                if template_name in self.workflow_templates:
                    template = self.workflow_templates[template_name]
                    workflow_data.update(template)
            
            # Create workflow
            workflow = {
                "id": workflow_id,
                "name": workflow_data["name"],
                "description": workflow_data.get("description", ""),
                "type": workflow_data.get("type", WorkflowType.EVENT_DRIVEN.value),
                "status": WorkflowStatus.DRAFT.value,
                "trigger": workflow_data.get("trigger", {}),
                "steps": workflow_data.get("steps", []),
                "variables": workflow_data.get("variables", {}),
                "created_at": datetime.now(),
                "created_by": workflow_data.get("created_by"),
                "version": 1,
                "metadata": {
                    "tags": workflow_data.get("tags", []),
                    "category": workflow_data.get("category"),
                    "priority": workflow_data.get("priority", "medium")
                }
            }
            
            # Validate workflow structure
            validation_result = await self._validate_workflow(workflow)
            if not validation_result["valid"]:
                return {"success": False, "error": validation_result["error"]}
            
            # Save workflow
            # await self._save_workflow(workflow)
            
            logger.info(f"Workflow {workflow_id} created successfully")
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "workflow": workflow
            }
            
        except Exception as e:
            logger.error(f"Error creating workflow: {e}")
            return {"success": False, "error": str(e)}
    
    async def _validate_workflow(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Validate workflow structure"""
        
        steps = workflow.get("steps", [])
        if not steps:
            return {"valid": False, "error": "Workflow must have at least one step"}
        
        # Check for start and end steps
        start_steps = [s for s in steps if s.get("type") == StepType.START.value]
        end_steps = [s for s in steps if s.get("type") == StepType.END.value]
        
        if not start_steps:
            return {"valid": False, "error": "Workflow must have a start step"}
        
        if not end_steps:
            return {"valid": False, "error": "Workflow must have an end step"}
        
        if len(start_steps) > 1:
            return {"valid": False, "error": "Workflow can have only one start step"}
        
        # Validate step connections
        step_ids = {s["id"] for s in steps}
        for step in steps:
            next_steps = step.get("next", [])
            for next_step in next_steps:
                if next_step not in step_ids:
                    return {"valid": False, "error": f"Step {step['id']} references unknown step {next_step}"}
        
        return {"valid": True}
    
    async def start_workflow_instance(self, workflow_id: str, 
                                    context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Start a new workflow instance"""
        try:
            instance_id = str(uuid.uuid4())
            
            # Get workflow definition
            workflow = await self._get_workflow(workflow_id)
            if not workflow:
                return {"success": False, "error": "Workflow not found"}
            
            if workflow["status"] != WorkflowStatus.ACTIVE.value:
                return {"success": False, "error": "Workflow is not active"}
            
            # Create workflow instance
            instance = {
                "id": instance_id,
                "workflow_id": workflow_id,
                "workflow_name": workflow["name"],
                "status": WorkflowStatus.ACTIVE.value,
                "context": context_data,
                "variables": workflow.get("variables", {}).copy(),
                "current_steps": [],
                "completed_steps": [],
                "failed_steps": [],
                "started_at": datetime.now(),
                "metadata": {
                    "started_by": context_data.get("started_by"),
                    "priority": workflow["metadata"].get("priority", "medium")
                }
            }
            
            # Find start step
            start_step = None
            for step in workflow["steps"]:
                if step["type"] == StepType.START.value:
                    start_step = step
                    break
            
            if not start_step:
                return {"success": False, "error": "No start step found"}
            
            # Execute start step
            await self._execute_step(instance, start_step, workflow)
            
            # Save instance
            # await self._save_workflow_instance(instance)
            
            logger.info(f"Workflow instance {instance_id} started")
            
            return {
                "success": True,
                "instance_id": instance_id,
                "instance": instance
            }
            
        except Exception as e:
            logger.error(f"Error starting workflow instance: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow by ID"""
        # Mock implementation
        if workflow_id in ["onboarding_wf", "expense_wf", "payroll_wf"]:
            return {
                "id": workflow_id,
                "name": "Test Workflow",
                "status": WorkflowStatus.ACTIVE.value,
                "steps": [
                    {
                        "id": "start",
                        "type": StepType.START.value,
                        "next": ["task1"]
                    },
                    {
                        "id": "task1",
                        "type": StepType.TASK.value,
                        "next": ["end"]
                    },
                    {
                        "id": "end",
                        "type": StepType.END.value
                    }
                ],
                "variables": {},
                "metadata": {"priority": "medium"}
            }
        return None
    
    async def _execute_step(self, instance: Dict[str, Any], step: Dict[str, Any], 
                          workflow: Dict[str, Any]) -> None:
        """Execute a workflow step"""
        
        step_execution = {
            "step_id": step["id"],
            "step_name": step.get("name", step["id"]),
            "step_type": step["type"],
            "status": StepStatus.RUNNING.value,
            "started_at": datetime.now(),
            "attempts": 1
        }
        
        instance["current_steps"].append(step_execution)
        
        try:
            # Get step handler
            handler = self.step_handlers.get(step["type"])
            if not handler:
                raise Exception(f"No handler for step type: {step['type']}")
            
            # Execute step
            result = await handler(instance, step, workflow)
            
            # Update step execution
            step_execution["status"] = StepStatus.COMPLETED.value
            step_execution["completed_at"] = datetime.now()
            step_execution["result"] = result
            
            # Move to completed steps
            instance["current_steps"].remove(step_execution)
            instance["completed_steps"].append(step_execution)
            
            # Execute next steps
            await self._execute_next_steps(instance, step, workflow)
            
        except Exception as e:
            logger.error(f"Error executing step {step['id']}: {e}")
            
            step_execution["status"] = StepStatus.FAILED.value
            step_execution["error"] = str(e)
            step_execution["failed_at"] = datetime.now()
            
            # Move to failed steps
            instance["current_steps"].remove(step_execution)
            instance["failed_steps"].append(step_execution)
            
            # Handle failure
            await self._handle_step_failure(instance, step, workflow, str(e))
    
    async def _execute_next_steps(self, instance: Dict[str, Any], current_step: Dict[str, Any], 
                                workflow: Dict[str, Any]) -> None:
        """Execute next steps in workflow"""
        
        next_step_ids = current_step.get("next", [])
        
        for next_step_id in next_step_ids:
            # Find next step definition
            next_step = None
            for step in workflow["steps"]:
                if step["id"] == next_step_id:
                    next_step = step
                    break
            
            if next_step:
                await self._execute_step(instance, next_step, workflow)
    
    async def _execute_task_step(self, instance: Dict[str, Any], step: Dict[str, Any], 
                               workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task step"""
        
        config = step.get("config", {})
        assignee = config.get("assignee")
        
        # Create task
        task = {
            "id": str(uuid.uuid4()),
            "workflow_instance_id": instance["id"],
            "step_id": step["id"],
            "title": step.get("name", "Workflow Task"),
            "description": step.get("description", ""),
            "assignee": assignee,
            "status": "pending",
            "created_at": datetime.now(),
            "config": config
        }
        
        # Mock task creation
        logger.info(f"Task created: {task['title']} assigned to {assignee}")
        
        return {"task_id": task["id"], "status": "created"}
    
    async def _execute_approval_step(self, instance: Dict[str, Any], step: Dict[str, Any], 
                                   workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Execute approval step"""
        
        config = step.get("config", {})
        approver = config.get("approver")
        timeout_hours = config.get("timeout_hours", 24)
        
        # Create approval request
        approval = {
            "id": str(uuid.uuid4()),
            "workflow_instance_id": instance["id"],
            "step_id": step["id"],
            "title": step.get("name", "Approval Required"),
            "approver": approver,
            "status": "pending",
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(hours=timeout_hours),
            "data": config.get("data", {})
        }
        
        # Mock approval creation
        logger.info(f"Approval request created for {approver}")
        
        return {"approval_id": approval["id"], "status": "pending"}
    
    async def _execute_notification_step(self, instance: Dict[str, Any], step: Dict[str, Any], 
                                       workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Execute notification step"""
        
        config = step.get("config", {})
        template = config.get("template")
        recipient = config.get("recipient")
        
        # Resolve template variables
        resolved_recipient = self._resolve_variables(recipient, instance["context"])
        
        # Send notification
        notification = {
            "template": template,
            "recipient": resolved_recipient,
            "variables": instance["context"],
            "sent_at": datetime.now()
        }
        
        # Mock notification sending
        logger.info(f"Notification sent: {template} to {resolved_recipient}")
        
        return {"notification_id": str(uuid.uuid4()), "status": "sent"}
    
    async def _execute_api_call_step(self, instance: Dict[str, Any], step: Dict[str, Any], 
                                   workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Execute API call step"""
        
        config = step.get("config", {})
        service = config.get("service")
        method = config.get("method")
        params = config.get("params", {})
        
        # Resolve parameters
        resolved_params = self._resolve_variables(params, instance["context"])
        
        # Mock API call
        result = {
            "service": service,
            "method": method,
            "params": resolved_params,
            "response": {"status": "success", "data": {}},
            "executed_at": datetime.now()
        }
        
        logger.info(f"API call executed: {service}.{method}")
        
        return result
    
    async def _execute_data_transform_step(self, instance: Dict[str, Any], step: Dict[str, Any], 
                                         workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data transformation step"""
        
        config = step.get("config", {})
        sources = config.get("sources", [])
        transformations = config.get("transformations", [])
        
        # Mock data gathering and transformation
        transformed_data = {
            "sources": sources,
            "transformations": transformations,
            "result": {"processed_records": 100},
            "processed_at": datetime.now()
        }
        
        # Store result in instance context
        instance["variables"]["transformed_data"] = transformed_data["result"]
        
        logger.info(f"Data transformation completed: {len(sources)} sources processed")
        
        return transformed_data
    
    async def _execute_decision_step(self, instance: Dict[str, Any], step: Dict[str, Any], 
                                   workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Execute decision step"""
        
        config = step.get("config", {})
        conditions = config.get("conditions", [])
        
        # Evaluate conditions
        for condition in conditions:
            if "if" in condition:
                # Evaluate condition
                condition_expr = condition["if"]
                resolved_expr = self._resolve_variables(condition_expr, instance["context"])
                
                # Mock condition evaluation
                if self._evaluate_condition(resolved_expr):
                    next_step = condition["then"]
                    logger.info(f"Condition matched: {condition_expr} -> {next_step}")
                    return {"decision": next_step, "condition": condition_expr}
            
            elif "else" in condition:
                next_step = condition["else"]
                logger.info(f"Default condition -> {next_step}")
                return {"decision": next_step, "condition": "default"}
        
        return {"decision": None, "condition": "no_match"}
    
    async def _execute_delay_step(self, instance: Dict[str, Any], step: Dict[str, Any], 
                                workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Execute delay step"""
        
        config = step.get("config", {})
        delay_seconds = config.get("delay_seconds", 60)
        
        # Mock delay (in real implementation, schedule for later execution)
        logger.info(f"Delay step: waiting {delay_seconds} seconds")
        
        return {"delayed_until": datetime.now() + timedelta(seconds=delay_seconds)}
    
    async def _execute_parallel_step(self, instance: Dict[str, Any], step: Dict[str, Any], 
                                   workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Execute parallel step"""
        
        config = step.get("config", {})
        parallel_steps = config.get("steps", [])
        
        # Execute steps in parallel
        tasks = []
        for parallel_step_id in parallel_steps:
            # Find step definition
            parallel_step = None
            for s in workflow["steps"]:
                if s["id"] == parallel_step_id:
                    parallel_step = s
                    break
            
            if parallel_step:
                task = self._execute_step(instance, parallel_step, workflow)
                tasks.append(task)
        
        # Wait for all parallel tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info(f"Parallel execution completed: {len(results)} steps")
        
        return {"parallel_results": results}
    
    async def _execute_merge_step(self, instance: Dict[str, Any], step: Dict[str, Any], 
                                workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Execute merge step (wait for multiple paths to converge)"""
        
        # Mock merge logic
        logger.info("Merge step: waiting for parallel paths to converge")
        
        return {"merged_at": datetime.now()}
    
    def _resolve_variables(self, template: Any, context: Dict[str, Any]) -> Any:
        """Resolve template variables with context data"""
        
        if isinstance(template, str):
            # Simple variable resolution (in real implementation, use proper templating)
            for key, value in context.items():
                template = template.replace(f"{{{{{key}}}}}", str(value))
            return template
        elif isinstance(template, dict):
            return {k: self._resolve_variables(v, context) for k, v in template.items()}
        elif isinstance(template, list):
            return [self._resolve_variables(item, context) for item in template]
        else:
            return template
    
    def _evaluate_condition(self, condition: str) -> bool:
        """Evaluate condition expression"""
        # Mock condition evaluation (in real implementation, use expression parser)
        return True
    
    async def _handle_step_failure(self, instance: Dict[str, Any], step: Dict[str, Any], 
                                 workflow: Dict[str, Any], error: str) -> None:
        """Handle step failure"""
        
        # Update instance status
        instance["status"] = WorkflowStatus.ERROR.value
        instance["error"] = error
        instance["failed_at"] = datetime.now()
        
        # Send failure notification
        logger.error(f"Workflow instance {instance['id']} failed at step {step['id']}: {error}")
    
    async def complete_task(self, task_id: str, completion_data: Dict[str, Any]) -> Dict[str, Any]:
        """Complete a workflow task"""
        try:
            # Get task
            task = await self._get_task(task_id)
            if not task:
                return {"success": False, "error": "Task not found"}
            
            # Update task status
            task["status"] = "completed"
            task["completed_at"] = datetime.now()
            task["completion_data"] = completion_data
            
            # Get workflow instance
            instance = await self._get_workflow_instance(task["workflow_instance_id"])
            if not instance:
                return {"success": False, "error": "Workflow instance not found"}
            
            # Continue workflow execution
            await self._continue_workflow_execution(instance, task)
            
            logger.info(f"Task {task_id} completed")
            
            return {
                "success": True,
                "task_id": task_id,
                "workflow_instance_id": instance["id"]
            }
            
        except Exception as e:
            logger.error(f"Error completing task: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task by ID"""
        # Mock implementation
        return {
            "id": task_id,
            "workflow_instance_id": "instance_123",
            "step_id": "task_step",
            "status": "pending"
        }
    
    async def _get_workflow_instance(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow instance by ID"""
        # Mock implementation
        return {
            "id": instance_id,
            "workflow_id": "workflow_123",
            "status": WorkflowStatus.ACTIVE.value,
            "context": {},
            "variables": {}
        }
    
    async def _continue_workflow_execution(self, instance: Dict[str, Any], 
                                         completed_task: Dict[str, Any]) -> None:
        """Continue workflow execution after task completion"""
        
        # Find the step that was completed
        step_id = completed_task["step_id"]
        
        # Get workflow definition
        workflow = await self._get_workflow(instance["workflow_id"])
        if not workflow:
            return
        
        # Find the completed step
        completed_step = None
        for step in workflow["steps"]:
            if step["id"] == step_id:
                completed_step = step
                break
        
        if completed_step:
            # Execute next steps
            await self._execute_next_steps(instance, completed_step, workflow)
    
    async def approve_step(self, approval_id: str, decision: str, 
                         comments: str = "") -> Dict[str, Any]:
        """Approve or reject an approval step"""
        try:
            # Get approval
            approval = await self._get_approval(approval_id)
            if not approval:
                return {"success": False, "error": "Approval not found"}
            
            # Update approval
            approval["status"] = decision  # "approved" or "rejected"
            approval["decided_at"] = datetime.now()
            approval["comments"] = comments
            
            # Get workflow instance
            instance = await self._get_workflow_instance(approval["workflow_instance_id"])
            if not instance:
                return {"success": False, "error": "Workflow instance not found"}
            
            # Handle approval decision
            if decision == "approved":
                await self._continue_workflow_execution(instance, {"step_id": approval["step_id"]})
            else:
                # Handle rejection
                await self._handle_approval_rejection(instance, approval)
            
            logger.info(f"Approval {approval_id} {decision}")
            
            return {
                "success": True,
                "approval_id": approval_id,
                "decision": decision
            }
            
        except Exception as e:
            logger.error(f"Error processing approval: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_approval(self, approval_id: str) -> Optional[Dict[str, Any]]:
        """Get approval by ID"""
        # Mock implementation
        return {
            "id": approval_id,
            "workflow_instance_id": "instance_123",
            "step_id": "approval_step",
            "status": "pending"
        }
    
    async def _handle_approval_rejection(self, instance: Dict[str, Any], 
                                       approval: Dict[str, Any]) -> None:
        """Handle approval rejection"""
        
        # Update instance status
        instance["status"] = WorkflowStatus.CANCELLED.value
        instance["cancelled_at"] = datetime.now()
        instance["cancellation_reason"] = f"Approval rejected: {approval['comments']}"
        
        logger.info(f"Workflow instance {instance['id']} cancelled due to approval rejection")
    
    async def get_workflow_analytics(self, date_range: Dict[str, Any]) -> Dict[str, Any]:
        """Get workflow analytics"""
        try:
            # Mock analytics data
            analytics = {
                "period": date_range,
                "total_workflows": 25,
                "active_workflows": 18,
                "total_instances": 450,
                "completed_instances": 380,
                "failed_instances": 35,
                "success_rate": 84.4,
                "average_completion_time": "2.5 hours",
                "by_workflow": {
                    "employee_onboarding": {
                        "instances": 150,
                        "completed": 135,
                        "avg_time": "3.2 hours",
                        "success_rate": 90.0
                    },
                    "expense_approval": {
                        "instances": 200,
                        "completed": 180,
                        "avg_time": "1.8 hours",
                        "success_rate": 90.0
                    },
                    "payroll_processing": {
                        "instances": 12,
                        "completed": 12,
                        "avg_time": "4.5 hours",
                        "success_rate": 100.0
                    }
                },
                "bottlenecks": [
                    {"step": "HR Approval", "avg_delay": "6.2 hours"},
                    {"step": "Document Upload", "avg_delay": "4.1 hours"},
                    {"step": "System Access", "avg_delay": "3.8 hours"}
                ],
                "performance_trends": {
                    "completion_time": "improving",
                    "success_rate": "stable",
                    "volume": "increasing"
                }
            }
            
            return {
                "success": True,
                "analytics": analytics
            }
            
        except Exception as e:
            logger.error(f"Error getting workflow analytics: {e}")
            return {"success": False, "error": str(e)}

# Global workflows service
def get_workflows_service(db) -> WorkflowsService:
    """Get workflows service instance"""
    return WorkflowsService(db)