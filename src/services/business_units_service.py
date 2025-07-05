"""
HuntRED® v2 - Business Units Service
Complete business units and organizational structure management system
"""

import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import json
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class BusinessUnitType(Enum):
    DIVISION = "division"
    DEPARTMENT = "department"
    TEAM = "team"
    PROJECT = "project"
    COST_CENTER = "cost_center"
    PROFIT_CENTER = "profit_center"
    SUBSIDIARY = "subsidiary"
    BRANCH = "branch"

class BusinessUnitStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PLANNING = "planning"
    SUSPENDED = "suspended"
    CLOSED = "closed"

class BudgetStatus(Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    ACTIVE = "active"
    EXCEEDED = "exceeded"
    CLOSED = "closed"

class BusinessUnitsService:
    """Complete business units management system"""
    
    def __init__(self, db):
        self.db = db
        
        # Business unit configuration templates
        self.unit_templates = {
            "technology_division": {
                "name": "División de Tecnología",
                "type": BusinessUnitType.DIVISION.value,
                "description": "División responsable de desarrollo tecnológico",
                "default_departments": [
                    {
                        "name": "Desarrollo de Software",
                        "type": BusinessUnitType.DEPARTMENT.value,
                        "teams": ["Frontend", "Backend", "Mobile", "DevOps"]
                    },
                    {
                        "name": "Infraestructura IT",
                        "type": BusinessUnitType.DEPARTMENT.value,
                        "teams": ["Redes", "Seguridad", "Soporte"]
                    },
                    {
                        "name": "Innovación y R&D",
                        "type": BusinessUnitType.DEPARTMENT.value,
                        "teams": ["Research", "Prototipos", "AI/ML"]
                    }
                ],
                "default_roles": [
                    "CTO", "Director de Tecnología", "Gerente de Desarrollo",
                    "Tech Lead", "Arquitecto de Software", "DevOps Engineer"
                ],
                "budget_categories": [
                    "salarios", "software_licenses", "hardware", "cloud_services",
                    "training", "consultoria_externa"
                ]
            },
            "sales_division": {
                "name": "División de Ventas",
                "type": BusinessUnitType.DIVISION.value,
                "description": "División responsable de ventas y revenue",
                "default_departments": [
                    {
                        "name": "Ventas Directas",
                        "type": BusinessUnitType.DEPARTMENT.value,
                        "teams": ["Enterprise", "SMB", "Inside Sales"]
                    },
                    {
                        "name": "Business Development",
                        "type": BusinessUnitType.DEPARTMENT.value,
                        "teams": ["Partnerships", "Channel Sales"]
                    },
                    {
                        "name": "Customer Success",
                        "type": BusinessUnitType.DEPARTMENT.value,
                        "teams": ["Onboarding", "Account Management", "Support"]
                    }
                ],
                "default_roles": [
                    "VP Sales", "Sales Director", "Sales Manager",
                    "Account Executive", "Sales Development Rep", "Customer Success Manager"
                ],
                "budget_categories": [
                    "salarios", "comisiones", "marketing", "travel",
                    "sales_tools", "events"
                ]
            },
            "operations_division": {
                "name": "División de Operaciones",
                "type": BusinessUnitType.DIVISION.value,
                "description": "División responsable de operaciones y procesos",
                "default_departments": [
                    {
                        "name": "Recursos Humanos",
                        "type": BusinessUnitType.DEPARTMENT.value,
                        "teams": ["Reclutamiento", "Compensaciones", "Desarrollo Organizacional"]
                    },
                    {
                        "name": "Finanzas",
                        "type": BusinessUnitType.DEPARTMENT.value,
                        "teams": ["Contabilidad", "Tesorería", "Planeación Financiera"]
                    },
                    {
                        "name": "Legal y Compliance",
                        "type": BusinessUnitType.DEPARTMENT.value,
                        "teams": ["Legal", "Compliance", "Contratos"]
                    }
                ],
                "default_roles": [
                    "COO", "HR Director", "CFO", "Legal Counsel",
                    "HR Manager", "Finance Manager", "Compliance Officer"
                ],
                "budget_categories": [
                    "salarios", "benefits", "legal_fees", "insurance",
                    "office_rent", "utilities"
                ]
            }
        }
        
        # KPI templates by business unit type
        self.kpi_templates = {
            BusinessUnitType.DIVISION.value: [
                {
                    "name": "Revenue Growth",
                    "description": "Crecimiento de ingresos año sobre año",
                    "metric_type": "percentage",
                    "target": 20.0,
                    "frequency": "monthly"
                },
                {
                    "name": "Employee Satisfaction",
                    "description": "Índice de satisfacción de empleados",
                    "metric_type": "score",
                    "target": 4.2,
                    "frequency": "quarterly"
                },
                {
                    "name": "Budget Variance",
                    "description": "Variación presupuestal",
                    "metric_type": "percentage",
                    "target": 5.0,
                    "frequency": "monthly"
                }
            ],
            BusinessUnitType.DEPARTMENT.value: [
                {
                    "name": "Productivity Index",
                    "description": "Índice de productividad del departamento",
                    "metric_type": "ratio",
                    "target": 1.2,
                    "frequency": "monthly"
                },
                {
                    "name": "Cost per Employee",
                    "description": "Costo promedio por empleado",
                    "metric_type": "currency",
                    "target": 50000.0,
                    "frequency": "monthly"
                }
            ],
            BusinessUnitType.TEAM.value: [
                {
                    "name": "Team Velocity",
                    "description": "Velocidad del equipo",
                    "metric_type": "points",
                    "target": 40.0,
                    "frequency": "weekly"
                },
                {
                    "name": "Quality Score",
                    "description": "Puntuación de calidad",
                    "metric_type": "percentage",
                    "target": 95.0,
                    "frequency": "weekly"
                }
            ]
        }
    
    async def create_business_unit(self, unit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new business unit"""
        try:
            unit_id = str(uuid.uuid4())
            
            # Use template if specified
            template_name = unit_data.get("template")
            if template_name and template_name in self.unit_templates:
                template = self.unit_templates[template_name]
                # Merge template with provided data
                for key, value in template.items():
                    if key not in unit_data:
                        unit_data[key] = value
            
            # Create business unit
            business_unit = {
                "id": unit_id,
                "name": unit_data["name"],
                "code": unit_data.get("code", self._generate_unit_code(unit_data["name"])),
                "type": unit_data.get("type", BusinessUnitType.DEPARTMENT.value),
                "status": BusinessUnitStatus.ACTIVE.value,
                "description": unit_data.get("description", ""),
                "parent_unit_id": unit_data.get("parent_unit_id"),
                "manager_id": unit_data.get("manager_id"),
                "location": unit_data.get("location", {}),
                "contact_info": unit_data.get("contact_info", {}),
                "created_at": datetime.now(),
                "effective_date": unit_data.get("effective_date", datetime.now()),
                "metadata": {
                    "created_by": unit_data.get("created_by"),
                    "cost_center": unit_data.get("cost_center"),
                    "profit_center": unit_data.get("profit_center"),
                    "legal_entity": unit_data.get("legal_entity"),
                    "tags": unit_data.get("tags", [])
                },
                "structure": {
                    "level": await self._calculate_unit_level(unit_data.get("parent_unit_id")),
                    "path": await self._calculate_unit_path(unit_data.get("parent_unit_id"), unit_id),
                    "children": [],
                    "employee_count": 0
                },
                "budget": {
                    "annual_budget": unit_data.get("annual_budget", 0),
                    "currency": unit_data.get("currency", "MXN"),
                    "budget_categories": unit_data.get("budget_categories", []),
                    "approved_by": unit_data.get("budget_approved_by"),
                    "approval_date": unit_data.get("budget_approval_date")
                },
                "kpis": await self._initialize_unit_kpis(unit_data.get("type", BusinessUnitType.DEPARTMENT.value)),
                "permissions": unit_data.get("permissions", {}),
                "settings": unit_data.get("settings", {})
            }
            
            # Validate business unit
            validation_result = await self._validate_business_unit(business_unit)
            if not validation_result["valid"]:
                return {"success": False, "error": validation_result["error"]}
            
            # Update parent unit if exists
            if business_unit["parent_unit_id"]:
                await self._update_parent_unit(business_unit["parent_unit_id"], unit_id)
            
            # Create default sub-units if template specifies
            if template_name and "default_departments" in self.unit_templates[template_name]:
                sub_units = await self._create_default_sub_units(
                    unit_id, self.unit_templates[template_name]["default_departments"]
                )
                business_unit["structure"]["children"] = [su["id"] for su in sub_units]
            
            # Save business unit
            # await self._save_business_unit(business_unit)
            
            logger.info(f"Business unit {unit_id} created successfully")
            
            return {
                "success": True,
                "unit_id": unit_id,
                "business_unit": business_unit
            }
            
        except Exception as e:
            logger.error(f"Error creating business unit: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_unit_code(self, name: str) -> str:
        """Generate unit code from name"""
        # Remove special characters and spaces, take first 6 characters
        code = "".join(c.upper() for c in name if c.isalnum())[:6]
        # Add random suffix to ensure uniqueness
        suffix = str(uuid.uuid4())[:4].upper()
        return f"{code}{suffix}"
    
    async def _calculate_unit_level(self, parent_unit_id: Optional[str]) -> int:
        """Calculate organizational level of unit"""
        if not parent_unit_id:
            return 0  # Root level
        
        # Get parent unit and add 1 to its level
        parent_unit = await self._get_business_unit(parent_unit_id)
        if parent_unit:
            return parent_unit["structure"]["level"] + 1
        
        return 0
    
    async def _calculate_unit_path(self, parent_unit_id: Optional[str], unit_id: str) -> str:
        """Calculate organizational path of unit"""
        if not parent_unit_id:
            return unit_id
        
        # Get parent unit path and append current unit
        parent_unit = await self._get_business_unit(parent_unit_id)
        if parent_unit:
            return f"{parent_unit['structure']['path']}/{unit_id}"
        
        return unit_id
    
    async def _initialize_unit_kpis(self, unit_type: str) -> List[Dict[str, Any]]:
        """Initialize KPIs for business unit based on type"""
        
        kpi_templates = self.kpi_templates.get(unit_type, [])
        kpis = []
        
        for template in kpi_templates:
            kpi = {
                "id": str(uuid.uuid4()),
                "name": template["name"],
                "description": template["description"],
                "metric_type": template["metric_type"],
                "target": template["target"],
                "frequency": template["frequency"],
                "current_value": 0,
                "status": "active",
                "created_at": datetime.now(),
                "history": []
            }
            kpis.append(kpi)
        
        return kpis
    
    async def _validate_business_unit(self, business_unit: Dict[str, Any]) -> Dict[str, Any]:
        """Validate business unit data"""
        
        # Check required fields
        required_fields = ["name", "type"]
        for field in required_fields:
            if not business_unit.get(field):
                return {"valid": False, "error": f"Missing required field: {field}"}
        
        # Validate parent unit exists if specified
        if business_unit.get("parent_unit_id"):
            parent_unit = await self._get_business_unit(business_unit["parent_unit_id"])
            if not parent_unit:
                return {"valid": False, "error": "Parent unit not found"}
        
        # Validate manager exists if specified
        if business_unit.get("manager_id"):
            manager = await self._get_employee(business_unit["manager_id"])
            if not manager:
                return {"valid": False, "error": "Manager not found"}
        
        return {"valid": True}
    
    async def _get_business_unit(self, unit_id: str) -> Optional[Dict[str, Any]]:
        """Get business unit by ID"""
        # Mock implementation
        if unit_id in ["unit_123", "parent_unit"]:
            return {
                "id": unit_id,
                "name": "Test Unit",
                "structure": {"level": 0, "path": unit_id, "children": []},
                "status": BusinessUnitStatus.ACTIVE.value
            }
        return None
    
    async def _get_employee(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """Get employee by ID"""
        # Mock implementation
        return {"id": employee_id, "name": "Test Manager"}
    
    async def _update_parent_unit(self, parent_unit_id: str, child_unit_id: str) -> None:
        """Update parent unit to include child"""
        parent_unit = await self._get_business_unit(parent_unit_id)
        if parent_unit:
            parent_unit["structure"]["children"].append(child_unit_id)
            # await self._save_business_unit(parent_unit)
    
    async def _create_default_sub_units(self, parent_unit_id: str, 
                                      departments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create default sub-units from template"""
        
        sub_units = []
        for dept_template in departments:
            # Create department
            dept_data = {
                "name": dept_template["name"],
                "type": dept_template["type"],
                "parent_unit_id": parent_unit_id,
                "description": f"Departamento de {dept_template['name']}"
            }
            
            dept_result = await self.create_business_unit(dept_data)
            if dept_result["success"]:
                sub_units.append(dept_result["business_unit"])
                
                # Create teams for department
                for team_name in dept_template.get("teams", []):
                    team_data = {
                        "name": team_name,
                        "type": BusinessUnitType.TEAM.value,
                        "parent_unit_id": dept_result["unit_id"],
                        "description": f"Equipo de {team_name}"
                    }
                    
                    await self.create_business_unit(team_data)
        
        return sub_units
    
    async def assign_employees_to_unit(self, unit_id: str, 
                                     employee_assignments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assign employees to business unit"""
        try:
            business_unit = await self._get_business_unit(unit_id)
            if not business_unit:
                return {"success": False, "error": "Business unit not found"}
            
            assignments = []
            for assignment in employee_assignments:
                employee_id = assignment["employee_id"]
                role = assignment.get("role", "Team Member")
                start_date = assignment.get("start_date", datetime.now())
                
                # Validate employee exists
                employee = await self._get_employee(employee_id)
                if not employee:
                    continue
                
                assignment_record = {
                    "id": str(uuid.uuid4()),
                    "employee_id": employee_id,
                    "unit_id": unit_id,
                    "role": role,
                    "start_date": start_date,
                    "end_date": assignment.get("end_date"),
                    "status": "active",
                    "created_at": datetime.now(),
                    "responsibilities": assignment.get("responsibilities", []),
                    "reporting_to": assignment.get("reporting_to")
                }
                
                assignments.append(assignment_record)
                
                # Update employee record
                await self._update_employee_unit_assignment(employee_id, unit_id, role)
            
            # Update unit employee count
            business_unit["structure"]["employee_count"] += len(assignments)
            # await self._save_business_unit(business_unit)
            
            logger.info(f"{len(assignments)} employees assigned to unit {unit_id}")
            
            return {
                "success": True,
                "unit_id": unit_id,
                "assignments": assignments,
                "total_assigned": len(assignments)
            }
            
        except Exception as e:
            logger.error(f"Error assigning employees to unit: {e}")
            return {"success": False, "error": str(e)}
    
    async def _update_employee_unit_assignment(self, employee_id: str, unit_id: str, role: str) -> None:
        """Update employee's unit assignment"""
        # Mock implementation
        logger.info(f"Employee {employee_id} assigned to unit {unit_id} as {role}")
    
    async def create_unit_budget(self, unit_id: str, budget_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create budget for business unit"""
        try:
            budget_id = str(uuid.uuid4())
            
            business_unit = await self._get_business_unit(unit_id)
            if not business_unit:
                return {"success": False, "error": "Business unit not found"}
            
            # Create budget
            budget = {
                "id": budget_id,
                "unit_id": unit_id,
                "fiscal_year": budget_data.get("fiscal_year", datetime.now().year),
                "total_budget": Decimal(str(budget_data["total_budget"])),
                "currency": budget_data.get("currency", "MXN"),
                "status": BudgetStatus.DRAFT.value,
                "created_at": datetime.now(),
                "created_by": budget_data.get("created_by"),
                "categories": {},
                "allocations": {},
                "approvals": [],
                "tracking": {
                    "spent": Decimal("0.00"),
                    "committed": Decimal("0.00"),
                    "available": Decimal(str(budget_data["total_budget"])),
                    "variance": Decimal("0.00")
                }
            }
            
            # Process budget categories
            categories = budget_data.get("categories", {})
            total_allocated = Decimal("0.00")
            
            for category, amount in categories.items():
                category_amount = Decimal(str(amount))
                budget["categories"][category] = {
                    "allocated": category_amount,
                    "spent": Decimal("0.00"),
                    "committed": Decimal("0.00"),
                    "available": category_amount,
                    "percentage": float((category_amount / budget["total_budget"]) * 100)
                }
                total_allocated += category_amount
            
            # Validate total allocation
            if total_allocated > budget["total_budget"]:
                return {"success": False, "error": "Total category allocation exceeds budget"}
            
            # Process monthly/quarterly allocations
            if budget_data.get("monthly_allocation"):
                budget["allocations"] = await self._create_budget_allocations(
                    budget["total_budget"], budget_data["monthly_allocation"]
                )
            
            # Save budget
            # await self._save_unit_budget(budget)
            
            # Update business unit budget reference
            business_unit["budget"]["budget_id"] = budget_id
            business_unit["budget"]["annual_budget"] = budget["total_budget"]
            # await self._save_business_unit(business_unit)
            
            logger.info(f"Budget {budget_id} created for unit {unit_id}")
            
            return {
                "success": True,
                "budget_id": budget_id,
                "budget": budget
            }
            
        except Exception as e:
            logger.error(f"Error creating unit budget: {e}")
            return {"success": False, "error": str(e)}
    
    async def _create_budget_allocations(self, total_budget: Decimal, 
                                       allocation_type: str) -> Dict[str, Any]:
        """Create budget allocations by period"""
        
        allocations = {}
        
        if allocation_type == "monthly":
            monthly_amount = total_budget / 12
            for month in range(1, 13):
                allocations[f"month_{month}"] = {
                    "allocated": monthly_amount,
                    "spent": Decimal("0.00"),
                    "available": monthly_amount
                }
        
        elif allocation_type == "quarterly":
            quarterly_amount = total_budget / 4
            for quarter in range(1, 5):
                allocations[f"q{quarter}"] = {
                    "allocated": quarterly_amount,
                    "spent": Decimal("0.00"),
                    "available": quarterly_amount
                }
        
        return allocations
    
    async def update_kpi_value(self, unit_id: str, kpi_id: str, 
                             new_value: float, period: str) -> Dict[str, Any]:
        """Update KPI value for business unit"""
        try:
            business_unit = await self._get_business_unit(unit_id)
            if not business_unit:
                return {"success": False, "error": "Business unit not found"}
            
            # Find KPI
            kpi = None
            for unit_kpi in business_unit.get("kpis", []):
                if unit_kpi["id"] == kpi_id:
                    kpi = unit_kpi
                    break
            
            if not kpi:
                return {"success": False, "error": "KPI not found"}
            
            # Update KPI value
            previous_value = kpi["current_value"]
            kpi["current_value"] = new_value
            kpi["last_updated"] = datetime.now()
            
            # Add to history
            history_entry = {
                "period": period,
                "value": new_value,
                "previous_value": previous_value,
                "change": new_value - previous_value,
                "change_percentage": ((new_value - previous_value) / previous_value * 100) if previous_value != 0 else 0,
                "recorded_at": datetime.now()
            }
            
            kpi["history"].append(history_entry)
            
            # Calculate performance vs target
            target = kpi["target"]
            performance = {
                "vs_target": new_value - target,
                "vs_target_percentage": ((new_value - target) / target * 100) if target != 0 else 0,
                "status": "above_target" if new_value >= target else "below_target"
            }
            
            kpi["performance"] = performance
            
            # Save updated business unit
            # await self._save_business_unit(business_unit)
            
            logger.info(f"KPI {kpi_id} updated for unit {unit_id}: {new_value}")
            
            return {
                "success": True,
                "kpi_id": kpi_id,
                "new_value": new_value,
                "performance": performance,
                "history_entry": history_entry
            }
            
        except Exception as e:
            logger.error(f"Error updating KPI: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_organizational_chart(self, root_unit_id: Optional[str] = None) -> Dict[str, Any]:
        """Get organizational chart"""
        try:
            # Get root units if no specific root provided
            if not root_unit_id:
                root_units = await self._get_root_business_units()
            else:
                root_unit = await self._get_business_unit(root_unit_id)
                root_units = [root_unit] if root_unit else []
            
            # Build organizational chart
            org_chart = {
                "chart_id": str(uuid.uuid4()),
                "generated_at": datetime.now(),
                "root_units": [],
                "total_units": 0,
                "total_employees": 0,
                "max_depth": 0
            }
            
            for root_unit in root_units:
                unit_tree = await self._build_unit_tree(root_unit, 0)
                org_chart["root_units"].append(unit_tree)
                
                # Update totals
                unit_stats = await self._calculate_tree_stats(unit_tree)
                org_chart["total_units"] += unit_stats["unit_count"]
                org_chart["total_employees"] += unit_stats["employee_count"]
                org_chart["max_depth"] = max(org_chart["max_depth"], unit_stats["max_depth"])
            
            return {
                "success": True,
                "organizational_chart": org_chart
            }
            
        except Exception as e:
            logger.error(f"Error generating organizational chart: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_root_business_units(self) -> List[Dict[str, Any]]:
        """Get root level business units"""
        # Mock implementation
        return [
            {
                "id": "root_1",
                "name": "HuntRED® México",
                "type": BusinessUnitType.DIVISION.value,
                "structure": {"level": 0, "children": ["tech_div", "sales_div", "ops_div"], "employee_count": 150}
            }
        ]
    
    async def _build_unit_tree(self, unit: Dict[str, Any], depth: int) -> Dict[str, Any]:
        """Build unit tree recursively"""
        
        unit_tree = {
            "id": unit["id"],
            "name": unit["name"],
            "type": unit["type"],
            "level": depth,
            "employee_count": unit["structure"]["employee_count"],
            "manager": await self._get_unit_manager(unit.get("manager_id")),
            "children": []
        }
        
        # Get child units
        for child_id in unit["structure"].get("children", []):
            child_unit = await self._get_business_unit(child_id)
            if child_unit:
                child_tree = await self._build_unit_tree(child_unit, depth + 1)
                unit_tree["children"].append(child_tree)
        
        return unit_tree
    
    async def _get_unit_manager(self, manager_id: Optional[str]) -> Optional[Dict[str, Any]]:
        """Get unit manager information"""
        if not manager_id:
            return None
        
        # Mock implementation
        return {
            "id": manager_id,
            "name": "Test Manager",
            "title": "Manager",
            "email": "manager@huntred.com"
        }
    
    async def _calculate_tree_stats(self, unit_tree: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate statistics for unit tree"""
        
        stats = {
            "unit_count": 1,
            "employee_count": unit_tree["employee_count"],
            "max_depth": unit_tree["level"]
        }
        
        for child in unit_tree["children"]:
            child_stats = await self._calculate_tree_stats(child)
            stats["unit_count"] += child_stats["unit_count"]
            stats["employee_count"] += child_stats["employee_count"]
            stats["max_depth"] = max(stats["max_depth"], child_stats["max_depth"])
        
        return stats
    
    async def get_unit_analytics(self, unit_id: str, date_range: Dict[str, Any]) -> Dict[str, Any]:
        """Get analytics for business unit"""
        try:
            business_unit = await self._get_business_unit(unit_id)
            if not business_unit:
                return {"success": False, "error": "Business unit not found"}
            
            # Mock analytics data
            analytics = {
                "unit_id": unit_id,
                "unit_name": business_unit["name"],
                "period": date_range,
                "employee_metrics": {
                    "total_employees": business_unit["structure"]["employee_count"],
                    "new_hires": 5,
                    "departures": 2,
                    "retention_rate": 95.2,
                    "avg_tenure": "2.3 years",
                    "satisfaction_score": 4.1
                },
                "financial_metrics": {
                    "budget_utilization": 78.5,
                    "cost_per_employee": 65000.0,
                    "revenue_per_employee": 180000.0,
                    "profit_margin": 22.3
                },
                "performance_metrics": {
                    "productivity_index": 1.15,
                    "quality_score": 92.8,
                    "efficiency_rating": 88.5,
                    "goal_achievement": 85.0
                },
                "kpi_summary": [],
                "trends": {
                    "headcount": "increasing",
                    "budget": "on_track",
                    "performance": "improving",
                    "satisfaction": "stable"
                },
                "benchmarks": {
                    "industry_avg_retention": 87.0,
                    "industry_avg_satisfaction": 3.8,
                    "company_avg_productivity": 1.10
                }
            }
            
            # Add KPI summary
            for kpi in business_unit.get("kpis", []):
                kpi_summary = {
                    "name": kpi["name"],
                    "current_value": kpi["current_value"],
                    "target": kpi["target"],
                    "status": kpi.get("performance", {}).get("status", "unknown"),
                    "trend": "improving" if len(kpi["history"]) > 1 and kpi["history"][-1]["change"] > 0 else "declining"
                }
                analytics["kpi_summary"].append(kpi_summary)
            
            return {
                "success": True,
                "analytics": analytics
            }
            
        except Exception as e:
            logger.error(f"Error getting unit analytics: {e}")
            return {"success": False, "error": str(e)}
    
    async def restructure_organization(self, restructure_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Execute organizational restructuring"""
        try:
            restructure_id = str(uuid.uuid4())
            
            # Create restructuring record
            restructuring = {
                "id": restructure_id,
                "name": restructure_plan["name"],
                "description": restructure_plan.get("description", ""),
                "effective_date": restructure_plan.get("effective_date", datetime.now()),
                "created_at": datetime.now(),
                "created_by": restructure_plan.get("created_by"),
                "status": "planned",
                "changes": restructure_plan.get("changes", []),
                "impact_analysis": {},
                "rollback_plan": {}
            }
            
            # Analyze impact
            impact_analysis = await self._analyze_restructure_impact(restructure_plan["changes"])
            restructuring["impact_analysis"] = impact_analysis
            
            # Validate restructuring plan
            validation_result = await self._validate_restructure_plan(restructure_plan)
            if not validation_result["valid"]:
                return {"success": False, "error": validation_result["error"]}
            
            # Execute changes if approved
            if restructure_plan.get("execute_immediately", False):
                execution_result = await self._execute_restructure_changes(restructuring)
                restructuring["execution_result"] = execution_result
                restructuring["status"] = "executed" if execution_result["success"] else "failed"
            
            # Save restructuring record
            # await self._save_restructuring(restructuring)
            
            logger.info(f"Organizational restructuring {restructure_id} planned")
            
            return {
                "success": True,
                "restructure_id": restructure_id,
                "restructuring": restructuring
            }
            
        except Exception as e:
            logger.error(f"Error planning organizational restructuring: {e}")
            return {"success": False, "error": str(e)}
    
    async def _analyze_restructure_impact(self, changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze impact of organizational restructuring"""
        
        impact = {
            "affected_units": 0,
            "affected_employees": 0,
            "budget_impact": 0.0,
            "risks": [],
            "benefits": [],
            "timeline_estimate": "30 days"
        }
        
        for change in changes:
            change_type = change.get("type")
            
            if change_type == "create_unit":
                impact["affected_units"] += 1
                impact["benefits"].append("New organizational capability")
            
            elif change_type == "merge_units":
                impact["affected_units"] += len(change.get("units_to_merge", []))
                impact["affected_employees"] += change.get("employee_count", 0)
                impact["risks"].append("Employee displacement during merger")
                impact["benefits"].append("Operational efficiency improvement")
            
            elif change_type == "eliminate_unit":
                impact["affected_units"] += 1
                impact["affected_employees"] += change.get("employee_count", 0)
                impact["budget_impact"] += change.get("cost_savings", 0)
                impact["risks"].append("Employee morale impact")
            
            elif change_type == "reassign_employees":
                impact["affected_employees"] += len(change.get("employees", []))
                impact["risks"].append("Productivity impact during transition")
        
        return impact
    
    async def _validate_restructure_plan(self, restructure_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Validate restructuring plan"""
        
        changes = restructure_plan.get("changes", [])
        if not changes:
            return {"valid": False, "error": "No changes specified"}
        
        # Validate each change
        for change in changes:
            if not change.get("type"):
                return {"valid": False, "error": "Change type not specified"}
            
            # Validate specific change types
            change_type = change["type"]
            if change_type == "merge_units":
                units_to_merge = change.get("units_to_merge", [])
                if len(units_to_merge) < 2:
                    return {"valid": False, "error": "Merge requires at least 2 units"}
        
        return {"valid": True}
    
    async def _execute_restructure_changes(self, restructuring: Dict[str, Any]) -> Dict[str, Any]:
        """Execute restructuring changes"""
        
        execution_result = {
            "success": True,
            "executed_changes": 0,
            "failed_changes": 0,
            "errors": []
        }
        
        for change in restructuring["changes"]:
            try:
                change_type = change["type"]
                
                if change_type == "create_unit":
                    await self._execute_create_unit_change(change)
                elif change_type == "merge_units":
                    await self._execute_merge_units_change(change)
                elif change_type == "eliminate_unit":
                    await self._execute_eliminate_unit_change(change)
                elif change_type == "reassign_employees":
                    await self._execute_reassign_employees_change(change)
                
                execution_result["executed_changes"] += 1
                
            except Exception as e:
                execution_result["failed_changes"] += 1
                execution_result["errors"].append(f"Failed to execute {change_type}: {str(e)}")
        
        if execution_result["failed_changes"] > 0:
            execution_result["success"] = False
        
        return execution_result
    
    async def _execute_create_unit_change(self, change: Dict[str, Any]) -> None:
        """Execute create unit change"""
        unit_data = change["unit_data"]
        await self.create_business_unit(unit_data)
    
    async def _execute_merge_units_change(self, change: Dict[str, Any]) -> None:
        """Execute merge units change"""
        # Mock implementation
        logger.info(f"Merging units: {change.get('units_to_merge', [])}")
    
    async def _execute_eliminate_unit_change(self, change: Dict[str, Any]) -> None:
        """Execute eliminate unit change"""
        # Mock implementation
        logger.info(f"Eliminating unit: {change.get('unit_id')}")
    
    async def _execute_reassign_employees_change(self, change: Dict[str, Any]) -> None:
        """Execute reassign employees change"""
        # Mock implementation
        logger.info(f"Reassigning {len(change.get('employees', []))} employees")

# Global business units service
def get_business_units_service(db) -> BusinessUnitsService:
    """Get business units service instance"""
    return BusinessUnitsService(db)