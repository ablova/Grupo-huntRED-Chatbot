"""
Real API Endpoints - Database Integration
FastAPI endpoints that use real database services
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import logging

from ..database.database import get_db
from ..services.employee_service import EmployeeService
from ..services.real_payroll_service import RealPayrollService

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Pydantic models
class EmployeeCreate(BaseModel):
    company_id: str
    employee_number: str
    first_name: str
    last_name: str
    email: str
    phone_number: str
    role: str = "employee"
    department: Optional[str] = None
    position: Optional[str] = None
    hire_date: str
    monthly_salary: float
    hourly_rate: Optional[float] = None
    manager_id: Optional[str] = None

class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    role: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    monthly_salary: Optional[float] = None
    hourly_rate: Optional[float] = None
    manager_id: Optional[str] = None

class PayrollCalculateRequest(BaseModel):
    employee_id: str
    pay_period_start: str
    pay_period_end: str
    overtime_hours: float = 0
    bonuses: float = 0
    commissions: float = 0
    other_income: float = 0
    loan_deductions: float = 0
    advance_deductions: float = 0
    other_deductions: float = 0

# Employee Endpoints
@router.post("/employees", response_model=Dict[str, Any])
async def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):
    """Create a new employee"""
    try:
        employee_service = EmployeeService(db)
        
        # Validate employee data
        validation_errors = await employee_service.validate_employee_data(employee.dict())
        if validation_errors:
            raise HTTPException(status_code=400, detail={"errors": validation_errors})
        
        # Create employee
        new_employee = await employee_service.create_employee(employee.dict())
        
        return {
            "id": new_employee.id,
            "employee_number": new_employee.employee_number,
            "name": f"{new_employee.first_name} {new_employee.last_name}",
            "email": new_employee.email,
            "phone_number": new_employee.phone_number,
            "role": new_employee.role.value,
            "department": new_employee.department,
            "position": new_employee.position,
            "hire_date": new_employee.hire_date.isoformat(),
            "monthly_salary": float(new_employee.monthly_salary),
            "is_active": new_employee.is_active,
            "created_at": new_employee.created_at.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error creating employee: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/employees/{employee_id}", response_model=Dict[str, Any])
async def get_employee(employee_id: str, db: Session = Depends(get_db)):
    """Get employee by ID"""
    try:
        employee_service = EmployeeService(db)
        employee = await employee_service.get_employee_by_id(employee_id)
        
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        return {
            "id": employee.id,
            "employee_number": employee.employee_number,
            "name": f"{employee.first_name} {employee.last_name}",
            "email": employee.email,
            "phone_number": employee.phone_number,
            "role": employee.role.value,
            "department": employee.department,
            "position": employee.position,
            "hire_date": employee.hire_date.isoformat(),
            "monthly_salary": float(employee.monthly_salary),
            "is_active": employee.is_active,
            "manager_id": employee.manager_id,
            "created_at": employee.created_at.isoformat(),
            "updated_at": employee.updated_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting employee: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/employees/{employee_id}", response_model=Dict[str, Any])
async def update_employee(employee_id: str, employee_update: EmployeeUpdate, 
                         db: Session = Depends(get_db)):
    """Update employee information"""
    try:
        employee_service = EmployeeService(db)
        
        # Filter out None values
        update_data = {k: v for k, v in employee_update.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No data provided for update")
        
        updated_employee = await employee_service.update_employee(employee_id, update_data)
        
        if not updated_employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        return {
            "id": updated_employee.id,
            "employee_number": updated_employee.employee_number,
            "name": f"{updated_employee.first_name} {updated_employee.last_name}",
            "email": updated_employee.email,
            "phone_number": updated_employee.phone_number,
            "role": updated_employee.role.value,
            "department": updated_employee.department,
            "position": updated_employee.position,
            "monthly_salary": float(updated_employee.monthly_salary),
            "updated_at": updated_employee.updated_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating employee: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/employees/{employee_id}")
async def deactivate_employee(employee_id: str, db: Session = Depends(get_db)):
    """Deactivate an employee"""
    try:
        employee_service = EmployeeService(db)
        success = await employee_service.deactivate_employee(employee_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        return {"message": "Employee deactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating employee: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/companies/{company_id}/employees", response_model=List[Dict[str, Any]])
async def get_company_employees(company_id: str, skip: int = 0, limit: int = 100, 
                               db: Session = Depends(get_db)):
    """Get all employees for a company"""
    try:
        employee_service = EmployeeService(db)
        employees = await employee_service.get_employees_by_company(company_id, skip, limit)
        
        return [
            {
                "id": emp.id,
                "employee_number": emp.employee_number,
                "name": f"{emp.first_name} {emp.last_name}",
                "email": emp.email,
                "phone_number": emp.phone_number,
                "role": emp.role.value,
                "department": emp.department,
                "position": emp.position,
                "monthly_salary": float(emp.monthly_salary),
                "is_active": emp.is_active
            }
            for emp in employees
        ]
        
    except Exception as e:
        logger.error(f"Error getting company employees: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/employees/search/{company_id}", response_model=List[Dict[str, Any]])
async def search_employees(company_id: str, query: str, skip: int = 0, limit: int = 50,
                          db: Session = Depends(get_db)):
    """Search employees by name, email, or employee number"""
    try:
        employee_service = EmployeeService(db)
        employees = await employee_service.search_employees(company_id, query, skip, limit)
        
        return [
            {
                "id": emp.id,
                "employee_number": emp.employee_number,
                "name": f"{emp.first_name} {emp.last_name}",
                "email": emp.email,
                "department": emp.department,
                "position": emp.position,
                "role": emp.role.value
            }
            for emp in employees
        ]
        
    except Exception as e:
        logger.error(f"Error searching employees: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Payroll Endpoints
@router.post("/payroll/calculate", response_model=Dict[str, Any])
async def calculate_payroll(request: PayrollCalculateRequest, db: Session = Depends(get_db)):
    """Calculate payroll for an employee"""
    try:
        payroll_service = RealPayrollService(db)
        
        result = await payroll_service.calculate_employee_payroll(
            employee_id=request.employee_id,
            pay_period_start=datetime.fromisoformat(request.pay_period_start).date(),
            pay_period_end=datetime.fromisoformat(request.pay_period_end).date(),
            overtime_hours=request.overtime_hours,
            bonuses=request.bonuses,
            commissions=request.commissions,
            other_income=request.other_income,
            loan_deductions=request.loan_deductions,
            advance_deductions=request.advance_deductions,
            other_deductions=request.other_deductions
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error calculating payroll: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/payroll/history/{employee_id}", response_model=List[Dict[str, Any]])
async def get_payroll_history(employee_id: str, limit: int = 12, db: Session = Depends(get_db)):
    """Get payroll history for an employee"""
    try:
        payroll_service = RealPayrollService(db)
        history = await payroll_service.get_employee_payroll_history(employee_id, limit)
        
        return history
        
    except Exception as e:
        logger.error(f"Error getting payroll history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/payroll/bulk-process/{company_id}", response_model=Dict[str, Any])
async def bulk_process_payroll(company_id: str, pay_period_start: str, pay_period_end: str,
                              db: Session = Depends(get_db)):
    """Process payroll for all employees in a company"""
    try:
        payroll_service = RealPayrollService(db)
        
        result = await payroll_service.bulk_process_payroll(
            company_id=company_id,
            pay_period_start=datetime.fromisoformat(pay_period_start).date(),
            pay_period_end=datetime.fromisoformat(pay_period_end).date()
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error bulk processing payroll: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/payroll/summary/{company_id}", response_model=Dict[str, Any])
async def get_payroll_summary(company_id: str, start_date: str, end_date: str,
                             db: Session = Depends(get_db)):
    """Get payroll summary for a company"""
    try:
        payroll_service = RealPayrollService(db)
        
        summary = await payroll_service.get_company_payroll_summary(
            company_id=company_id,
            start_date=datetime.fromisoformat(start_date).date(),
            end_date=datetime.fromisoformat(end_date).date()
        )
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting payroll summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/payroll/{payroll_id}", response_model=Dict[str, Any])
async def get_payroll_record(payroll_id: str, db: Session = Depends(get_db)):
    """Get specific payroll record"""
    try:
        payroll_service = RealPayrollService(db)
        record = await payroll_service.get_payroll_by_id(payroll_id)
        
        if not record:
            raise HTTPException(status_code=404, detail="Payroll record not found")
        
        return record
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting payroll record: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WhatsApp Bot Integration
@router.post("/whatsapp/authenticate/{phone_number}")
async def authenticate_whatsapp_user(phone_number: str, company_id: str, 
                                   db: Session = Depends(get_db)):
    """Authenticate WhatsApp user by phone number"""
    try:
        employee_service = EmployeeService(db)
        employee = await employee_service.get_employee_by_phone(phone_number, company_id)
        
        if not employee:
            return {"authenticated": False, "message": "Employee not found"}
        
        return {
            "authenticated": True,
            "employee": {
                "id": employee.id,
                "name": f"{employee.first_name} {employee.last_name}",
                "role": employee.role.value,
                "department": employee.department,
                "position": employee.position
            }
        }
        
    except Exception as e:
        logger.error(f"Error authenticating WhatsApp user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/whatsapp/payslip/{employee_id}")
async def get_whatsapp_payslip(employee_id: str, db: Session = Depends(get_db)):
    """Get latest payslip for WhatsApp bot"""
    try:
        payroll_service = RealPayrollService(db)
        history = await payroll_service.get_employee_payroll_history(employee_id, 1)
        
        if not history:
            return {"message": "No payslips found"}
        
        latest_payslip = history[0]
        
        # Format for WhatsApp display
        return {
            "period": latest_payslip["pay_period"],
            "gross_income": latest_payslip["gross_income"],
            "total_deductions": latest_payslip["total_deductions"],
            "net_pay": latest_payslip["net_pay"],
            "formatted_message": f"""💰 *RECIBO DE NÓMINA*

📅 Período: {latest_payslip['pay_period']['start']} al {latest_payslip['pay_period']['end']}

💵 Sueldo bruto: ${latest_payslip['gross_income']:,.2f}
➖ Deducciones: ${latest_payslip['total_deductions']:,.2f}
💰 *Neto a pagar: ${latest_payslip['net_pay']:,.2f}*"""
        }
        
    except Exception as e:
        logger.error(f"Error getting WhatsApp payslip: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check
@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Test database connection
        from ..database.models import Employee
        db.query(Employee).first()
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }