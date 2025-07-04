"""
Employee Service - Real Database Operations
Handles all employee-related database operations
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, date
import uuid
import logging

from ..database.models import Employee, Company, UserRole
from ..database.database import get_db

logger = logging.getLogger(__name__)

class EmployeeService:
    """Real employee service with database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_employee(self, employee_data: Dict[str, Any]) -> Employee:
        """Create a new employee"""
        try:
            employee = Employee(
                id=str(uuid.uuid4()),
                company_id=employee_data["company_id"],
                employee_number=employee_data["employee_number"],
                first_name=employee_data["first_name"],
                last_name=employee_data["last_name"],
                email=employee_data["email"],
                phone_number=employee_data["phone_number"],
                role=UserRole(employee_data.get("role", "employee")),
                department=employee_data.get("department"),
                position=employee_data.get("position"),
                hire_date=datetime.fromisoformat(employee_data["hire_date"]),
                monthly_salary=employee_data["monthly_salary"],
                hourly_rate=employee_data.get("hourly_rate"),
                manager_id=employee_data.get("manager_id"),
                is_active=employee_data.get("is_active", True)
            )
            
            self.db.add(employee)
            self.db.commit()
            self.db.refresh(employee)
            
            logger.info(f"Created employee: {employee.id}")
            return employee
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating employee: {e}")
            raise
    
    async def get_employee_by_id(self, employee_id: str) -> Optional[Employee]:
        """Get employee by ID"""
        return self.db.query(Employee).filter(Employee.id == employee_id).first()
    
    async def get_employee_by_phone(self, phone_number: str, company_id: str) -> Optional[Employee]:
        """Get employee by phone number and company"""
        return self.db.query(Employee).filter(
            and_(
                Employee.phone_number == phone_number,
                Employee.company_id == company_id,
                Employee.is_active == True
            )
        ).first()
    
    async def get_employee_by_email(self, email: str) -> Optional[Employee]:
        """Get employee by email"""
        return self.db.query(Employee).filter(
            and_(
                Employee.email == email,
                Employee.is_active == True
            )
        ).first()
    
    async def get_employees_by_company(self, company_id: str, skip: int = 0, limit: int = 100) -> List[Employee]:
        """Get all employees for a company"""
        return self.db.query(Employee).filter(
            and_(
                Employee.company_id == company_id,
                Employee.is_active == True
            )
        ).offset(skip).limit(limit).all()
    
    async def get_employees_by_manager(self, manager_id: str) -> List[Employee]:
        """Get all employees managed by a specific manager"""
        return self.db.query(Employee).filter(
            and_(
                Employee.manager_id == manager_id,
                Employee.is_active == True
            )
        ).all()
    
    async def update_employee(self, employee_id: str, update_data: Dict[str, Any]) -> Optional[Employee]:
        """Update employee information"""
        try:
            employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
            if not employee:
                return None
            
            for key, value in update_data.items():
                if hasattr(employee, key):
                    if key == "role" and isinstance(value, str):
                        value = UserRole(value)
                    elif key == "hire_date" and isinstance(value, str):
                        value = datetime.fromisoformat(value)
                    setattr(employee, key, value)
            
            employee.updated_at = datetime.now()
            self.db.commit()
            self.db.refresh(employee)
            
            logger.info(f"Updated employee: {employee_id}")
            return employee
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating employee {employee_id}: {e}")
            raise
    
    async def deactivate_employee(self, employee_id: str) -> bool:
        """Deactivate an employee (soft delete)"""
        try:
            employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
            if not employee:
                return False
            
            employee.is_active = False
            employee.updated_at = datetime.now()
            self.db.commit()
            
            logger.info(f"Deactivated employee: {employee_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deactivating employee {employee_id}: {e}")
            raise
    
    async def search_employees(self, company_id: str, query: str, skip: int = 0, limit: int = 50) -> List[Employee]:
        """Search employees by name, email, or employee number"""
        search_filter = or_(
            Employee.first_name.ilike(f"%{query}%"),
            Employee.last_name.ilike(f"%{query}%"),
            Employee.email.ilike(f"%{query}%"),
            Employee.employee_number.ilike(f"%{query}%")
        )
        
        return self.db.query(Employee).filter(
            and_(
                Employee.company_id == company_id,
                Employee.is_active == True,
                search_filter
            )
        ).offset(skip).limit(limit).all()
    
    async def get_employee_count_by_company(self, company_id: str) -> int:
        """Get total employee count for a company"""
        return self.db.query(Employee).filter(
            and_(
                Employee.company_id == company_id,
                Employee.is_active == True
            )
        ).count()
    
    async def get_employees_by_department(self, company_id: str, department: str) -> List[Employee]:
        """Get employees by department"""
        return self.db.query(Employee).filter(
            and_(
                Employee.company_id == company_id,
                Employee.department == department,
                Employee.is_active == True
            )
        ).all()
    
    async def get_employees_by_role(self, company_id: str, role: UserRole) -> List[Employee]:
        """Get employees by role"""
        return self.db.query(Employee).filter(
            and_(
                Employee.company_id == company_id,
                Employee.role == role,
                Employee.is_active == True
            )
        ).all()
    
    async def bulk_create_employees(self, employees_data: List[Dict[str, Any]]) -> List[Employee]:
        """Bulk create employees"""
        try:
            employees = []
            for emp_data in employees_data:
                employee = Employee(
                    id=str(uuid.uuid4()),
                    company_id=emp_data["company_id"],
                    employee_number=emp_data["employee_number"],
                    first_name=emp_data["first_name"],
                    last_name=emp_data["last_name"],
                    email=emp_data["email"],
                    phone_number=emp_data["phone_number"],
                    role=UserRole(emp_data.get("role", "employee")),
                    department=emp_data.get("department"),
                    position=emp_data.get("position"),
                    hire_date=datetime.fromisoformat(emp_data["hire_date"]),
                    monthly_salary=emp_data["monthly_salary"],
                    hourly_rate=emp_data.get("hourly_rate"),
                    manager_id=emp_data.get("manager_id"),
                    is_active=emp_data.get("is_active", True)
                )
                employees.append(employee)
            
            self.db.add_all(employees)
            self.db.commit()
            
            logger.info(f"Bulk created {len(employees)} employees")
            return employees
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error bulk creating employees: {e}")
            raise
    
    async def validate_employee_data(self, employee_data: Dict[str, Any]) -> List[str]:
        """Validate employee data before creation/update"""
        errors = []
        
        # Check required fields
        required_fields = ["first_name", "last_name", "email", "phone_number", "monthly_salary"]
        for field in required_fields:
            if field not in employee_data or not employee_data[field]:
                errors.append(f"Missing required field: {field}")
        
        # Check email format
        if "email" in employee_data:
            email = employee_data["email"]
            if "@" not in email or "." not in email:
                errors.append("Invalid email format")
            
            # Check if email already exists
            existing_employee = await self.get_employee_by_email(email)
            if existing_employee:
                errors.append(f"Email {email} already exists")
        
        # Check phone number format
        if "phone_number" in employee_data:
            phone = employee_data["phone_number"]
            if not phone.startswith("+"):
                errors.append("Phone number must start with country code (+)")
        
        # Check salary is positive
        if "monthly_salary" in employee_data:
            salary = employee_data["monthly_salary"]
            if salary <= 0:
                errors.append("Monthly salary must be positive")
        
        # Check role is valid
        if "role" in employee_data:
            role = employee_data["role"]
            valid_roles = [r.value for r in UserRole]
            if role not in valid_roles:
                errors.append(f"Invalid role. Must be one of: {valid_roles}")
        
        return errors
    
    async def get_employee_hierarchy(self, company_id: str) -> Dict[str, Any]:
        """Get employee hierarchy for a company"""
        employees = await self.get_employees_by_company(company_id)
        
        # Build hierarchy
        hierarchy = {}
        managers = {}
        
        for emp in employees:
            emp_data = {
                "id": emp.id,
                "name": f"{emp.first_name} {emp.last_name}",
                "position": emp.position,
                "department": emp.department,
                "role": emp.role.value,
                "subordinates": []
            }
            
            if emp.manager_id:
                if emp.manager_id not in managers:
                    managers[emp.manager_id] = []
                managers[emp.manager_id].append(emp_data)
            else:
                hierarchy[emp.id] = emp_data
        
        # Add subordinates to managers
        for manager_id, subordinates in managers.items():
            if manager_id in hierarchy:
                hierarchy[manager_id]["subordinates"] = subordinates
        
        return hierarchy