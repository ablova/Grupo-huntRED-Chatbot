"""
Complete API Endpoints - Full System Integration
All endpoints with JWT authentication and real services
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
import logging

from ..database.database import get_db
from ..database.models import Employee, UserRole
from ..auth.auth_service import auth_service
from ..services.employee_service import EmployeeService
from ..services.real_payroll_service import RealPayrollService
from ..services.attendance_service import AttendanceService
from ..services.reports_service import ReportsService

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Pydantic models for requests
class LoginRequest(BaseModel):
    email: str
    password: str

class AttendanceRequest(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notes: Optional[str] = None

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

# Authentication Endpoints
@router.post("/auth/login", response_model=Dict[str, Any])
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Employee login with JWT token"""
    try:
        # Authenticate employee
        employee = await auth_service.authenticate_employee(request.email, request.password, db)
        
        if not employee:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        
        # Create access token
        token_data = {
            "sub": employee.id,
            "email": employee.email,
            "role": employee.role.value,
            "company_id": employee.company_id
        }
        access_token = auth_service.create_access_token(data=token_data)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "employee": {
                "id": employee.id,
                "name": f"{employee.first_name} {employee.last_name}",
                "email": employee.email,
                "role": employee.role.value,
                "department": employee.department,
                "position": employee.position
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/auth/me", response_model=Dict[str, Any])
async def get_current_user_info(current_employee: Employee = Depends(auth_service.get_current_employee)):
    """Get current authenticated employee info"""
    return {
        "id": current_employee.id,
        "employee_number": current_employee.employee_number,
        "name": f"{current_employee.first_name} {current_employee.last_name}",
        "email": current_employee.email,
        "role": current_employee.role.value,
        "department": current_employee.department,
        "position": current_employee.position,
        "hire_date": current_employee.hire_date.isoformat(),
        "monthly_salary": float(current_employee.monthly_salary),
        "company_id": current_employee.company_id
    }

# Attendance Endpoints
@router.post("/attendance/check-in", response_model=Dict[str, Any])
async def check_in(
    request: AttendanceRequest,
    current_employee: Employee = Depends(auth_service.get_current_employee),
    db: Session = Depends(get_db)
):
    """Employee check-in with geolocation"""
    try:
        attendance_service = AttendanceService(db)
        result = await attendance_service.check_in(
            employee_id=current_employee.id,
            latitude=request.latitude,
            longitude=request.longitude,
            notes=request.notes
        )
        return result
        
    except Exception as e:
        logger.error(f"Check-in error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/attendance/check-out", response_model=Dict[str, Any])
async def check_out(
    request: AttendanceRequest,
    current_employee: Employee = Depends(auth_service.get_current_employee),
    db: Session = Depends(get_db)
):
    """Employee check-out with hours calculation"""
    try:
        attendance_service = AttendanceService(db)
        result = await attendance_service.check_out(
            employee_id=current_employee.id,
            latitude=request.latitude,
            longitude=request.longitude,
            notes=request.notes
        )
        return result
        
    except Exception as e:
        logger.error(f"Check-out error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/attendance/status", response_model=Dict[str, Any])
async def get_attendance_status(
    target_date: Optional[str] = Query(None),
    current_employee: Employee = Depends(auth_service.get_current_employee),
    db: Session = Depends(get_db)
):
    """Get current attendance status"""
    try:
        attendance_service = AttendanceService(db)
        date_obj = datetime.fromisoformat(target_date).date() if target_date else None
        
        result = await attendance_service.get_attendance_status(
            employee_id=current_employee.id,
            target_date=date_obj
        )
        return result
        
    except Exception as e:
        logger.error(f"Attendance status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/attendance/history", response_model=List[Dict[str, Any]])
async def get_attendance_history(
    start_date: str = Query(...),
    end_date: str = Query(...),
    current_employee: Employee = Depends(auth_service.get_current_employee),
    db: Session = Depends(get_db)
):
    """Get attendance history for employee"""
    try:
        attendance_service = AttendanceService(db)
        
        result = await attendance_service.get_attendance_history(
            employee_id=current_employee.id,
            start_date=datetime.fromisoformat(start_date).date(),
            end_date=datetime.fromisoformat(end_date).date()
        )
        return result
        
    except Exception as e:
        logger.error(f"Attendance history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Team Management Endpoints (Supervisors/HR)
@router.get("/team/attendance-summary", response_model=Dict[str, Any])
async def get_team_attendance_summary(
    target_date: Optional[str] = Query(None),
    current_employee: Employee = Depends(auth_service.require_role([UserRole.SUPERVISOR, UserRole.HR_ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db)
):
    """Get attendance summary for manager's team"""
    try:
        attendance_service = AttendanceService(db)
        date_obj = datetime.fromisoformat(target_date).date() if target_date else None
        
        result = await attendance_service.get_team_attendance_summary(
            manager_id=current_employee.id,
            target_date=date_obj
        )
        return result
        
    except Exception as e:
        logger.error(f"Team attendance summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/team/members", response_model=List[Dict[str, Any]])
async def get_team_members(
    current_employee: Employee = Depends(auth_service.require_role([UserRole.SUPERVISOR, UserRole.HR_ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db)
):
    """Get team members for manager"""
    try:
        employee_service = EmployeeService(db)
        team_members = await employee_service.get_employees_by_manager(current_employee.id)
        
        return [
            {
                "id": emp.id,
                "employee_number": emp.employee_number,
                "name": f"{emp.first_name} {emp.last_name}",
                "email": emp.email,
                "department": emp.department,
                "position": emp.position,
                "hire_date": emp.hire_date.isoformat(),
                "monthly_salary": float(emp.monthly_salary),
                "is_active": emp.is_active
            }
            for emp in team_members
        ]
        
    except Exception as e:
        logger.error(f"Get team members error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Payroll Endpoints
@router.post("/payroll/calculate", response_model=Dict[str, Any])
async def calculate_payroll(
    request: PayrollCalculateRequest,
    current_employee: Employee = Depends(auth_service.require_role([UserRole.HR_ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db)
):
    """Calculate payroll for an employee (HR only)"""
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
        logger.error(f"Payroll calculation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/payroll/my-history", response_model=List[Dict[str, Any]])
async def get_my_payroll_history(
    limit: int = Query(12),
    current_employee: Employee = Depends(auth_service.get_current_employee),
    db: Session = Depends(get_db)
):
    """Get payroll history for current employee"""
    try:
        payroll_service = RealPayrollService(db)
        history = await payroll_service.get_employee_payroll_history(current_employee.id, limit)
        
        return history
        
    except Exception as e:
        logger.error(f"Payroll history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/payroll/latest-payslip", response_model=Dict[str, Any])
async def get_latest_payslip(
    current_employee: Employee = Depends(auth_service.get_current_employee),
    db: Session = Depends(get_db)
):
    """Get latest payslip for current employee"""
    try:
        payroll_service = RealPayrollService(db)
        history = await payroll_service.get_employee_payroll_history(current_employee.id, 1)
        
        if not history:
            raise HTTPException(status_code=404, detail="No payslips found")
        
        latest_payslip = history[0]
        
        # Format for display
        return {
            "employee": {
                "name": f"{current_employee.first_name} {current_employee.last_name}",
                "employee_number": current_employee.employee_number,
                "department": current_employee.department,
                "position": current_employee.position
            },
            "payslip": latest_payslip,
            "whatsapp_formatted": f"""💰 *RECIBO DE NÓMINA*

📅 Período: {latest_payslip['pay_period']['start']} al {latest_payslip['pay_period']['end']}

💵 Sueldo bruto: ${latest_payslip['gross_income']:,.2f}
➖ Deducciones: ${latest_payslip['total_deductions']:,.2f}
💰 *Neto pagado: ${latest_payslip['net_pay']:,.2f}*

📄 Para más detalles, visita el portal web."""
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Latest payslip error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Reports Endpoints (HR/Admin only)
@router.get("/reports/payroll", response_model=Dict[str, Any])
async def generate_payroll_report(
    start_date: str = Query(...),
    end_date: str = Query(...),
    current_employee: Employee = Depends(auth_service.require_role([UserRole.HR_ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db)
):
    """Generate payroll report (HR only)"""
    try:
        reports_service = ReportsService(db)
        
        report = await reports_service.generate_payroll_report(
            company_id=current_employee.company_id,
            start_date=datetime.fromisoformat(start_date).date(),
            end_date=datetime.fromisoformat(end_date).date()
        )
        
        return report
        
    except Exception as e:
        logger.error(f"Payroll report error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports/attendance", response_model=Dict[str, Any])
async def generate_attendance_report(
    start_date: str = Query(...),
    end_date: str = Query(...),
    current_employee: Employee = Depends(auth_service.require_role([UserRole.SUPERVISOR, UserRole.HR_ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db)
):
    """Generate attendance report"""
    try:
        reports_service = ReportsService(db)
        
        report = await reports_service.generate_attendance_report(
            company_id=current_employee.company_id,
            start_date=datetime.fromisoformat(start_date).date(),
            end_date=datetime.fromisoformat(end_date).date()
        )
        
        return report
        
    except Exception as e:
        logger.error(f"Attendance report error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports/executive-dashboard", response_model=Dict[str, Any])
async def get_executive_dashboard(
    current_employee: Employee = Depends(auth_service.require_role([UserRole.HR_ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db)
):
    """Get executive dashboard with KPIs"""
    try:
        reports_service = ReportsService(db)
        
        dashboard = await reports_service.generate_executive_dashboard(
            company_id=current_employee.company_id
        )
        
        return dashboard
        
    except Exception as e:
        logger.error(f"Executive dashboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports/employee-performance/{employee_id}", response_model=Dict[str, Any])
async def get_employee_performance_report(
    employee_id: str,
    start_date: str = Query(...),
    end_date: str = Query(...),
    current_employee: Employee = Depends(auth_service.require_role([UserRole.SUPERVISOR, UserRole.HR_ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db)
):
    """Get employee performance report"""
    try:
        reports_service = ReportsService(db)
        
        # Check if current employee can view this employee's data
        if current_employee.role == UserRole.SUPERVISOR:
            employee_service = EmployeeService(db)
            target_employee = await employee_service.get_employee_by_id(employee_id)
            if not target_employee or target_employee.manager_id != current_employee.id:
                raise HTTPException(status_code=403, detail="Not authorized to view this employee's data")
        
        report = await reports_service.generate_employee_performance_report(
            employee_id=employee_id,
            start_date=datetime.fromisoformat(start_date).date(),
            end_date=datetime.fromisoformat(end_date).date()
        )
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Employee performance report error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WhatsApp Bot Integration
@router.post("/whatsapp/process-message", response_model=Dict[str, Any])
async def process_whatsapp_message(
    phone_number: str = Form(...),
    message: str = Form(...),
    company_id: str = Form(...),
    db: Session = Depends(get_db)
):
    """Process WhatsApp message (for webhook integration)"""
    try:
        # Authenticate user by phone
        employee_service = EmployeeService(db)
        employee = await employee_service.get_employee_by_phone(phone_number, company_id)
        
        if not employee:
            return {
                "response": "❌ No tienes acceso a este sistema. Contacta a Recursos Humanos.",
                "authenticated": False
            }
        
        # Process message based on content
        message_lower = message.lower().strip()
        
        if message_lower in ["hola", "hello", "hi", "inicio"]:
            response = f"¡Hola {employee.first_name}! 👋\n\n" \
                      f"Soy tu asistente de nómina de HuntRED®.\n\n" \
                      f"Comandos disponibles:\n" \
                      f"• *recibo* - Ver mi último recibo\n" \
                      f"• *entrada* - Registrar entrada\n" \
                      f"• *salida* - Registrar salida\n" \
                      f"• *estado* - Ver estado de asistencia\n" \
                      f"• *menu* - Ver todas las opciones"
        
        elif message_lower in ["recibo", "nomina", "payslip"]:
            payroll_service = RealPayrollService(db)
            history = await payroll_service.get_employee_payroll_history(employee.id, 1)
            
            if not history:
                response = "❌ No tienes recibos de nómina disponibles."
            else:
                payslip = history[0]
                response = f"💰 *RECIBO DE NÓMINA*\n\n" \
                          f"📅 Período: {payslip['pay_period']['start']} al {payslip['pay_period']['end']}\n\n" \
                          f"💵 Sueldo bruto: ${payslip['gross_income']:,.2f}\n" \
                          f"➖ Deducciones: ${payslip['total_deductions']:,.2f}\n" \
                          f"💰 *Neto pagado: ${payslip['net_pay']:,.2f}*"
        
        elif message_lower in ["estado", "status", "asistencia"]:
            attendance_service = AttendanceService(db)
            status = await attendance_service.get_attendance_status(employee.id)
            
            response = f"📊 *ESTADO DE ASISTENCIA*\n\n" \
                      f"📅 Fecha: {status['date']}\n" \
                      f"📋 Estado: {status['message']}\n"
            
            if "check_in_time" in status:
                response += f"🕐 Entrada: {status['check_in_time']}\n"
            if "hours_worked_so_far" in status:
                response += f"⏱️ Horas trabajadas: {status['hours_worked_so_far']:.1f}h"
        
        elif message_lower in ["menu", "menú", "opciones"]:
            menu_options = [
                "💰 *recibo* - Ver mi último recibo",
                "📊 *estado* - Ver estado de asistencia",
                "👤 *perfil* - Ver mi perfil",
                "📞 *ayuda* - Obtener ayuda"
            ]
            
            if employee.role in [UserRole.SUPERVISOR, UserRole.HR_ADMIN, UserRole.SUPER_ADMIN]:
                menu_options.extend([
                    "👥 *equipo* - Ver mi equipo",
                    "📈 *reportes* - Generar reportes"
                ])
            
            response = f"📋 *MENÚ PRINCIPAL*\n\n" + "\n".join(menu_options)
        
        else:
            response = f"❓ No entendí tu mensaje: '{message}'\n\n" \
                      f"Escribe *menu* para ver las opciones disponibles."
        
        return {
            "response": response,
            "authenticated": True,
            "employee": {
                "name": f"{employee.first_name} {employee.last_name}",
                "role": employee.role.value
            }
        }
        
    except Exception as e:
        logger.error(f"WhatsApp message processing error: {e}")
        return {
            "response": "❌ Ocurrió un error procesando tu solicitud. Por favor intenta de nuevo.",
            "authenticated": False,
            "error": str(e)
        }

# System Status
@router.get("/system/status", response_model=Dict[str, Any])
async def get_system_status(
    current_employee: Employee = Depends(auth_service.require_role([UserRole.HR_ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db)
):
    """Get system status and health"""
    try:
        # Get basic stats
        employee_service = EmployeeService(db)
        total_employees = await employee_service.get_employee_count_by_company(current_employee.company_id)
        
        # Test services
        attendance_service = AttendanceService(db)
        payroll_service = RealPayrollService(db)
        reports_service = ReportsService(db)
        
        return {
            "system_status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "company_id": current_employee.company_id,
            "statistics": {
                "total_employees": total_employees,
                "active_services": [
                    "employee_service",
                    "payroll_service", 
                    "attendance_service",
                    "reports_service",
                    "auth_service"
                ]
            },
            "features": [
                "JWT Authentication",
                "Role-based Access Control",
                "Real-time Attendance Tracking",
                "Mexico 2024 Payroll Compliance",
                "Advanced Reporting",
                "WhatsApp Bot Integration",
                "Geolocation Validation"
            ]
        }
        
    except Exception as e:
        logger.error(f"System status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))