"""
Ghuntred-v2 - Real Application with Database Integration
Complete HR Technology Platform with Real Database Services
"""

from fastapi import FastAPI, HTTPException, Depends, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import uvicorn
import logging
from datetime import datetime
import asyncio

# Import database components
from database.database import get_db, create_tables
from database.models import Employee, Company, UserRole

# Import real services
from services.employee_service import EmployeeService
from services.real_payroll_service import RealPayrollService

# Import existing engines (for WhatsApp bot functionality)
from services.whatsapp_bot import WhatsAppBotEngine
from services.sociallink_engine import SocialLinkEngine
from services.overtime_management import OvertimeManagementEngine
from services.unified_messaging import UnifiedMessagingEngine

# Import real API endpoints
from api.real_endpoints import router as real_api_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Ghuntred-v2 - Real HR Technology Platform",
    description="Complete HR platform with real database integration, conversational AI, and Mexico 2024 payroll compliance",
    version="2.0.0-real",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engines (keeping existing functionality)
whatsapp_bot = WhatsAppBotEngine()
social_engine = SocialLinkEngine()
overtime_engine = OvertimeManagementEngine()
messaging_engine = UnifiedMessagingEngine()

# Include real API endpoints
app.include_router(real_api_router, prefix="/api/v1", tags=["Real API"])

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database and services on startup"""
    logger.info("🚀 Starting Ghuntred-v2 Real Application...")
    
    try:
        # Create database tables
        create_tables()
        logger.info("✅ Database tables created/verified")
        
        # Test database connection
        db = next(get_db())
        try:
            # Test query
            company_count = db.query(Company).count()
            employee_count = db.query(Employee).count()
            logger.info(f"✅ Database connected: {company_count} companies, {employee_count} employees")
        finally:
            db.close()
        
        logger.info("🎉 Ghuntred-v2 started successfully!")
        
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
        raise

# Enhanced health check
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Enhanced health check with database status"""
    try:
        # Test database connection
        company_count = db.query(Company).count()
        employee_count = db.query(Employee).count()
        
        # Test services
        employee_service = EmployeeService(db)
        payroll_service = RealPayrollService(db)
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0-real",
            "system": "Ghuntred-v2 Real Platform",
            "database": {
                "status": "connected",
                "companies": company_count,
                "employees": employee_count
            },
            "services": {
                "employee_service": "online",
                "payroll_service": "online",
                "whatsapp_bot": "online",
                "social_engine": "online",
                "overtime_engine": "online",
                "messaging_engine": "online"
            },
            "features": [
                "Real database integration",
                "Mexico 2024 payroll compliance",
                "Multi-tenant architecture",
                "Conversational AI",
                "Multi-channel messaging",
                "Real-time webhooks",
                "Advanced analytics",
                "Complete REST API"
            ]
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

# WhatsApp Webhook Integration (Real)
@app.post("/api/v1/webhooks/whatsapp/{company_id}")
async def whatsapp_webhook_real(
    company_id: str,
    request: Request,
    db: Session = Depends(get_db),
    x_hub_signature_256: Optional[str] = Header(None)
):
    """Real WhatsApp webhook handler with database integration"""
    try:
        # Get webhook data
        webhook_data = await request.json()
        
        # Extract message info
        from_number = webhook_data.get("From", "").replace("whatsapp:", "")
        message_body = webhook_data.get("Body", "").strip()
        
        logger.info(f"WhatsApp message from {from_number} to company {company_id}: {message_body}")
        
        # Authenticate user using database
        employee_service = EmployeeService(db)
        employee = await employee_service.get_employee_by_phone(from_number, company_id)
        
        if not employee:
            # Send authentication error
            response_message = "❌ No tienes acceso a este sistema. Contacta a Recursos Humanos."
            # Here you would send the message via WhatsApp API
            return {"status": "error", "message": "User not authenticated"}
        
        # Process message based on content
        response_message = await process_whatsapp_message(employee, message_body, db)
        
        # Here you would send the response via WhatsApp API
        logger.info(f"Response to {from_number}: {response_message}")
        
        return {
            "status": "success",
            "employee": f"{employee.first_name} {employee.last_name}",
            "response": response_message
        }
        
    except Exception as e:
        logger.error(f"WhatsApp webhook error: {e}")
        return {"status": "error", "message": str(e)}

async def process_whatsapp_message(employee: Employee, message: str, db: Session) -> str:
    """Process WhatsApp message and return response"""
    message_lower = message.lower().strip()
    
    try:
        if message_lower in ["hola", "hello", "hi", "inicio"]:
            return f"¡Hola {employee.first_name}! 👋\n\n" \
                   f"Soy tu asistente de nómina de HuntRED®.\n\n" \
                   f"Comandos disponibles:\n" \
                   f"• *recibo* - Ver mi último recibo\n" \
                   f"• *saldo* - Consultar saldo pendiente\n" \
                   f"• *menu* - Ver todas las opciones\n" \
                   f"• *ayuda* - Obtener ayuda"
        
        elif message_lower in ["recibo", "nomina", "payslip", "sueldo"]:
            # Get latest payslip
            payroll_service = RealPayrollService(db)
            history = await payroll_service.get_employee_payroll_history(employee.id, 1)
            
            if not history:
                return "❌ No tienes recibos de nómina disponibles."
            
            payslip = history[0]
            return f"💰 *RECIBO DE NÓMINA*\n\n" \
                   f"📅 Período: {payslip['pay_period']['start']} al {payslip['pay_period']['end']}\n\n" \
                   f"💵 Sueldo bruto: ${payslip['gross_income']:,.2f}\n" \
                   f"➖ Deducciones: ${payslip['total_deductions']:,.2f}\n" \
                   f"💰 *Neto pagado: ${payslip['net_pay']:,.2f}*\n\n" \
                   f"📄 Para el recibo completo, visita el portal web."
        
        elif message_lower in ["saldo", "balance", "dinero"]:
            return f"💳 *CONSULTA DE SALDO*\n\n" \
                   f"👤 Empleado: {employee.first_name} {employee.last_name}\n" \
                   f"💰 Sueldo mensual: ${float(employee.monthly_salary):,.2f}\n" \
                   f"🏢 Departamento: {employee.department}\n" \
                   f"📋 Puesto: {employee.position}\n\n" \
                   f"Para información detallada, escribe *recibo*"
        
        elif message_lower in ["menu", "menú", "opciones"]:
            menu_options = [
                "💰 *recibo* - Ver mi último recibo",
                "💳 *saldo* - Consultar información salarial",
                "👤 *perfil* - Ver mi perfil",
                "📞 *ayuda* - Obtener ayuda"
            ]
            
            # Add manager options
            if employee.role in [UserRole.SUPERVISOR, UserRole.HR_ADMIN, UserRole.SUPER_ADMIN]:
                menu_options.extend([
                    "👥 *equipo* - Ver mi equipo",
                    "📊 *reportes* - Generar reportes"
                ])
            
            return f"📋 *MENÚ PRINCIPAL*\n\n" + "\n".join(menu_options)
        
        elif message_lower in ["perfil", "profile", "info"]:
            return f"👤 *MI PERFIL*\n\n" \
                   f"📛 Nombre: {employee.first_name} {employee.last_name}\n" \
                   f"🆔 Número: {employee.employee_number}\n" \
                   f"📧 Email: {employee.email}\n" \
                   f"🏢 Departamento: {employee.department}\n" \
                   f"📋 Puesto: {employee.position}\n" \
                   f"👑 Rol: {employee.role.value}\n" \
                   f"📅 Fecha de ingreso: {employee.hire_date.strftime('%d/%m/%Y')}"
        
        elif message_lower in ["equipo", "team"] and employee.role.value in ["supervisor", "hr_admin", "super_admin"]:
            # Get team members
            employee_service = EmployeeService(db)
            team_members = await employee_service.get_employees_by_manager(employee.id)
            
            if not team_members:
                return "👥 No tienes empleados a tu cargo."
            
            team_list = []
            for member in team_members:
                team_list.append(f"• {member.first_name} {member.last_name} ({member.position})")
            
            return f"👥 *MI EQUIPO* ({len(team_members)} personas)\n\n" + "\n".join(team_list)
        
        elif message_lower in ["reportes", "reports"] and employee.role.value in ["hr_admin", "super_admin"]:
            # Get company summary
            payroll_service = RealPayrollService(db)
            from datetime import datetime, timedelta
            
            # Get current month summary
            now = datetime.now()
            start_date = now.replace(day=1).date()
            end_date = now.date()
            
            summary = await payroll_service.get_company_payroll_summary(
                employee.company_id, start_date, end_date
            )
            
            return f"📊 *REPORTE EJECUTIVO*\n\n" \
                   f"📅 Período: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}\n\n" \
                   f"👥 Empleados: {summary['summary']['total_employees']}\n" \
                   f"💰 Nómina total: ${summary['summary']['total_gross_pay']:,.2f}\n" \
                   f"➖ Deducciones: ${summary['summary']['total_deductions']:,.2f}\n" \
                   f"💵 Neto pagado: ${summary['summary']['total_net_pay']:,.2f}\n" \
                   f"📊 Promedio: ${summary['summary']['average_net_pay']:,.2f}"
        
        elif message_lower in ["ayuda", "help", "?"]:
            return f"❓ *AYUDA - HUNTRED® BOT*\n\n" \
                   f"Este bot te ayuda con consultas de nómina y RH.\n\n" \
                   f"*Comandos disponibles:*\n" \
                   f"• hola - Saludo inicial\n" \
                   f"• recibo - Ver último recibo\n" \
                   f"• saldo - Consultar saldo\n" \
                   f"• perfil - Ver mi información\n" \
                   f"• menu - Ver todas las opciones\n\n" \
                   f"📞 Soporte: soporte@huntred.com\n" \
                   f"🌐 Portal web: https://huntred.com"
        
        else:
            return f"❓ No entendí tu mensaje: '{message}'\n\n" \
                   f"Escribe *menu* para ver las opciones disponibles o *ayuda* para obtener ayuda."
    
    except Exception as e:
        logger.error(f"Error processing WhatsApp message: {e}")
        return f"❌ Ocurrió un error procesando tu solicitud. Por favor intenta de nuevo."

# Company Dashboard (Real)
@app.get("/api/v1/company/{company_id}/dashboard")
async def get_company_dashboard_real(company_id: str, db: Session = Depends(get_db)):
    """Real company dashboard with database data"""
    try:
        employee_service = EmployeeService(db)
        payroll_service = RealPayrollService(db)
        
        # Get employee counts
        total_employees = await employee_service.get_employee_count_by_company(company_id)
        
        # Get employees by department
        employees = await employee_service.get_employees_by_company(company_id)
        departments = {}
        for emp in employees:
            dept = emp.department or "Sin Departamento"
            departments[dept] = departments.get(dept, 0) + 1
        
        # Get payroll summary for current month
        from datetime import datetime
        now = datetime.now()
        start_date = now.replace(day=1).date()
        end_date = now.date()
        
        payroll_summary = await payroll_service.get_company_payroll_summary(
            company_id, start_date, end_date
        )
        
        return {
            "company_id": company_id,
            "timestamp": datetime.now().isoformat(),
            "employees": {
                "total": total_employees,
                "by_department": departments,
                "active": total_employees  # All employees are active in this query
            },
            "payroll": {
                "current_month": payroll_summary["summary"],
                "period": payroll_summary["period"]
            },
            "system": {
                "version": "2.0.0-real",
                "database": "connected",
                "features": ["Real data", "Mexico 2024 compliance", "WhatsApp integration"]
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting company dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"message": "Endpoint not found", "path": str(request.url)}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error", "error": str(exc)}
    )

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🔄 Shutting down Ghuntred-v2...")

if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "main_real:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )