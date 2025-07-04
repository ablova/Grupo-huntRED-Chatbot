"""
Database Initialization Script
Creates tables and populates with sample data for testing
"""

import asyncio
from datetime import datetime, date
from decimal import Decimal
import uuid

from database.database import create_tables, drop_tables, SessionLocal
from database.models import Company, Employee, UserRole, PayrollRecord
from services.employee_service import EmployeeService
from services.real_payroll_service import RealPayrollService

async def init_database():
    """Initialize database with sample data"""
    print("🚀 Initializing Ghuntred-v2 Database...")
    
    # Create tables
    print("📋 Creating database tables...")
    create_tables()
    print("✅ Tables created successfully")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Create sample company
        print("🏢 Creating sample company...")
        company = Company(
            id="huntred_mx",
            name="HuntRED® México",
            country="MX",
            timezone="America/Mexico_City",
            whatsapp_number="+525512345678",
            telegram_bot_token="sample_token"
        )
        db.add(company)
        db.commit()
        print("✅ Company created: HuntRED® México")
        
        # Create sample employees
        print("👥 Creating sample employees...")
        employee_service = EmployeeService(db)
        
        # CEO
        ceo_data = {
            "company_id": "huntred_mx",
            "employee_number": "CEO001",
            "first_name": "Carlos",
            "last_name": "Rodríguez",
            "email": "carlos.rodriguez@huntred.com",
            "phone_number": "+525512345678",
            "role": "super_admin",
            "department": "Dirección General",
            "position": "CEO",
            "hire_date": "2020-01-01",
            "monthly_salary": 80000.00,
            "hourly_rate": 500.00
        }
        ceo = await employee_service.create_employee(ceo_data)
        print(f"✅ Created CEO: {ceo.first_name} {ceo.last_name}")
        
        # HR Manager
        hr_data = {
            "company_id": "huntred_mx",
            "employee_number": "HR001",
            "first_name": "María",
            "last_name": "González",
            "email": "maria.gonzalez@huntred.com",
            "phone_number": "+525587654321",
            "role": "hr_admin",
            "department": "Recursos Humanos",
            "position": "HR Manager",
            "hire_date": "2020-03-15",
            "monthly_salary": 45000.00,
            "hourly_rate": 281.25,
            "manager_id": ceo.id
        }
        hr_manager = await employee_service.create_employee(hr_data)
        print(f"✅ Created HR Manager: {hr_manager.first_name} {hr_manager.last_name}")
        
        # IT Supervisor
        it_super_data = {
            "company_id": "huntred_mx",
            "employee_number": "IT001",
            "first_name": "Juan",
            "last_name": "Pérez",
            "email": "juan.perez@huntred.com",
            "phone_number": "+525555123456",
            "role": "supervisor",
            "department": "Tecnología",
            "position": "IT Supervisor",
            "hire_date": "2021-02-01",
            "monthly_salary": 35000.00,
            "hourly_rate": 218.75,
            "manager_id": ceo.id
        }
        it_supervisor = await employee_service.create_employee(it_super_data)
        print(f"✅ Created IT Supervisor: {it_supervisor.first_name} {it_supervisor.last_name}")
        
        # Software Developers
        developers = [
            {
                "company_id": "huntred_mx",
                "employee_number": "DEV001",
                "first_name": "Ana",
                "last_name": "López",
                "email": "ana.lopez@huntred.com",
                "phone_number": "+525555234567",
                "role": "employee",
                "department": "Tecnología",
                "position": "Senior Developer",
                "hire_date": "2021-06-15",
                "monthly_salary": 28000.00,
                "hourly_rate": 175.00,
                "manager_id": it_supervisor.id
            },
            {
                "company_id": "huntred_mx",
                "employee_number": "DEV002",
                "first_name": "Luis",
                "last_name": "Martínez",
                "email": "luis.martinez@huntred.com",
                "phone_number": "+525555345678",
                "role": "employee",
                "department": "Tecnología",
                "position": "Full Stack Developer",
                "hire_date": "2022-01-10",
                "monthly_salary": 25000.00,
                "hourly_rate": 156.25,
                "manager_id": it_supervisor.id
            },
            {
                "company_id": "huntred_mx",
                "employee_number": "DEV003",
                "first_name": "Sofia",
                "last_name": "Hernández",
                "email": "sofia.hernandez@huntred.com",
                "phone_number": "+525555456789",
                "role": "employee",
                "department": "Tecnología",
                "position": "Frontend Developer",
                "hire_date": "2022-08-01",
                "monthly_salary": 22000.00,
                "hourly_rate": 137.50,
                "manager_id": it_supervisor.id
            }
        ]
        
        dev_employees = []
        for dev_data in developers:
            dev = await employee_service.create_employee(dev_data)
            dev_employees.append(dev)
            print(f"✅ Created Developer: {dev.first_name} {dev.last_name}")
        
        # Sales Team
        sales_data = [
            {
                "company_id": "huntred_mx",
                "employee_number": "SALES001",
                "first_name": "Roberto",
                "last_name": "Jiménez",
                "email": "roberto.jimenez@huntred.com",
                "phone_number": "+525555567890",
                "role": "employee",
                "department": "Ventas",
                "position": "Sales Representative",
                "hire_date": "2021-09-01",
                "monthly_salary": 20000.00,
                "hourly_rate": 125.00,
                "manager_id": ceo.id
            },
            {
                "company_id": "huntred_mx",
                "employee_number": "SALES002",
                "first_name": "Carmen",
                "last_name": "Vázquez",
                "email": "carmen.vazquez@huntred.com",
                "phone_number": "+525555678901",
                "role": "employee",
                "department": "Ventas",
                "position": "Account Manager",
                "hire_date": "2022-03-15",
                "monthly_salary": 23000.00,
                "hourly_rate": 143.75,
                "manager_id": ceo.id
            }
        ]
        
        for sales_emp_data in sales_data:
            sales_emp = await employee_service.create_employee(sales_emp_data)
            print(f"✅ Created Sales Employee: {sales_emp.first_name} {sales_emp.last_name}")
        
        print(f"✅ Created {await employee_service.get_employee_count_by_company('huntred_mx')} employees total")
        
        # Create sample payroll records
        print("💰 Creating sample payroll records...")
        payroll_service = RealPayrollService(db)
        
        # Get all employees for payroll
        all_employees = await employee_service.get_employees_by_company("huntred_mx")
        
        # Create payroll for last month
        from datetime import datetime, timedelta
        last_month = datetime.now() - timedelta(days=30)
        pay_period_start = last_month.replace(day=1).date()
        pay_period_end = last_month.replace(day=28).date()
        
        payroll_count = 0
        for employee in all_employees:
            try:
                # Add some variety to payroll
                overtime_hours = 0
                bonuses = 0
                
                if employee.role == UserRole.SUPER_ADMIN:
                    bonuses = 5000.00  # CEO bonus
                elif employee.role == UserRole.HR_ADMIN:
                    bonuses = 2000.00  # HR bonus
                elif employee.department == "Tecnología":
                    overtime_hours = 8  # IT overtime
                elif employee.department == "Ventas":
                    bonuses = 1500.00  # Sales commission
                
                await payroll_service.calculate_employee_payroll(
                    employee_id=employee.id,
                    pay_period_start=pay_period_start,
                    pay_period_end=pay_period_end,
                    overtime_hours=overtime_hours,
                    bonuses=bonuses
                )
                payroll_count += 1
                
            except Exception as e:
                print(f"❌ Error creating payroll for {employee.first_name}: {e}")
        
        print(f"✅ Created {payroll_count} payroll records")
        
        # Print summary
        print("\n🎉 Database initialization completed successfully!")
        print("\n📊 SUMMARY:")
        print(f"   • Company: HuntRED® México")
        print(f"   • Employees: {await employee_service.get_employee_count_by_company('huntred_mx')}")
        print(f"   • Payroll Records: {payroll_count}")
        print(f"   • Departments: Dirección General, Recursos Humanos, Tecnología, Ventas")
        
        print("\n🔐 TEST CREDENTIALS:")
        print(f"   • CEO: carlos.rodriguez@huntred.com (+525512345678)")
        print(f"   • HR Manager: maria.gonzalez@huntred.com (+525587654321)")
        print(f"   • IT Supervisor: juan.perez@huntred.com (+525555123456)")
        print(f"   • Developer: ana.lopez@huntred.com (+525555234567)")
        
        print("\n🚀 API ENDPOINTS:")
        print(f"   • Health Check: GET /api/v1/health")
        print(f"   • Employees: GET /api/v1/companies/huntred_mx/employees")
        print(f"   • Create Employee: POST /api/v1/employees")
        print(f"   • Calculate Payroll: POST /api/v1/payroll/calculate")
        print(f"   • WhatsApp Auth: POST /api/v1/whatsapp/authenticate/+525512345678")
        
        print("\n💬 WHATSAPP BOT:")
        print(f"   • Test with: +525512345678 (CEO)")
        print(f"   • Test with: +525587654321 (HR Manager)")
        print(f"   • Commands: 'hola', 'menu', 'recibo', 'entrada', 'salida'")
        
    except Exception as e:
        print(f"❌ Error during initialization: {e}")
        db.rollback()
        raise
    finally:
        db.close()

async def reset_database():
    """Reset database (drop and recreate)"""
    print("🔄 Resetting database...")
    drop_tables()
    print("✅ Tables dropped")
    await init_database()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "reset":
        asyncio.run(reset_database())
    else:
        asyncio.run(init_database())