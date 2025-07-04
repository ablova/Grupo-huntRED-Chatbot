"""
Real Payroll Service - Database Integration
Integrates PayrollEngine with database operations
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
import uuid
import logging

from .payroll_engine import PayrollEngine, PayrollCalculation
from .employee_service import EmployeeService

logger = logging.getLogger(__name__)

class RealPayrollService:
    """Real payroll service with database integration"""
    
    def __init__(self, db_session):
        self.db = db_session
        self.payroll_engine = PayrollEngine()
        self.employee_service = EmployeeService(db_session)
    
    async def calculate_employee_payroll(self, employee_id: str, pay_period_start: date, 
                                       pay_period_end: date, **kwargs) -> Dict[str, Any]:
        """Calculate payroll for a specific employee"""
        try:
            # Get employee from database
            employee = await self.employee_service.get_employee_by_id(employee_id)
            if not employee:
                raise ValueError(f"Employee {employee_id} not found")
            
            # Prepare employee data for payroll engine
            employee_data = {
                "id": employee.id,
                "monthly_salary": float(employee.monthly_salary),
                "payroll_frequency": "monthly",  # Default, could be stored in employee record
                "employee_number": employee.employee_number,
                "name": f"{employee.first_name} {employee.last_name}",
                "department": employee.department,
                "position": employee.position
            }
            
            # Calculate payroll using the existing engine
            calculation = self.payroll_engine.calculate_payroll(
                employee_data=employee_data,
                pay_period_start=pay_period_start,
                pay_period_end=pay_period_end,
                overtime_hours=Decimal(str(kwargs.get("overtime_hours", 0))),
                bonuses=Decimal(str(kwargs.get("bonuses", 0))),
                commissions=Decimal(str(kwargs.get("commissions", 0))),
                other_income=Decimal(str(kwargs.get("other_income", 0))),
                loan_deductions=Decimal(str(kwargs.get("loan_deductions", 0))),
                advance_deductions=Decimal(str(kwargs.get("advance_deductions", 0))),
                other_deductions=Decimal(str(kwargs.get("other_deductions", 0)))
            )
            
            # Save to database
            payroll_record = await self._save_payroll_record(calculation)
            
            # Generate response
            return {
                "payroll_id": payroll_record.id,
                "employee": {
                    "id": employee.id,
                    "name": f"{employee.first_name} {employee.last_name}",
                    "employee_number": employee.employee_number,
                    "department": employee.department
                },
                "pay_period": {
                    "start": pay_period_start.isoformat(),
                    "end": pay_period_end.isoformat()
                },
                "income": {
                    "base_salary": float(calculation.base_salary),
                    "overtime_hours": float(calculation.overtime_hours),
                    "overtime_amount": float(calculation.overtime_amount),
                    "bonuses": float(calculation.bonuses),
                    "commissions": float(calculation.commissions),
                    "other_income": float(calculation.other_income),
                    "gross_total": float(calculation.gross_income)
                },
                "deductions": {
                    "imss": float(calculation.imss_employee),
                    "isr": float(calculation.isr_withheld),
                    "loans": float(calculation.loan_deductions),
                    "advances": float(calculation.advance_deductions),
                    "other": float(calculation.other_deductions),
                    "total": float(calculation.total_deductions)
                },
                "net_pay": float(calculation.net_pay),
                "employer_cost": float(calculation.total_employer_cost),
                "calculation_date": calculation.calculation_date.isoformat(),
                "currency": "MXN"
            }
            
        except Exception as e:
            logger.error(f"Error calculating payroll for employee {employee_id}: {e}")
            raise
    
    async def _save_payroll_record(self, calculation: PayrollCalculation):
        """Save payroll calculation to database"""
        try:
            # Import here to avoid circular imports
            from ..database.models import PayrollRecord
            
            payroll_record = PayrollRecord(
                id=str(uuid.uuid4()),
                company_id="default",  # Would get from employee
                employee_id=calculation.employee_id,
                pay_period_start=calculation.pay_period_start,
                pay_period_end=calculation.pay_period_end,
                base_salary=calculation.base_salary,
                overtime_hours=calculation.overtime_hours,
                overtime_amount=calculation.overtime_amount,
                bonuses=calculation.bonuses,
                commissions=calculation.commissions,
                other_income=calculation.other_income,
                gross_income=calculation.gross_income,
                imss_employee=calculation.imss_employee,
                isr_withheld=calculation.isr_withheld,
                loan_deductions=calculation.loan_deductions,
                advance_deductions=calculation.advance_deductions,
                other_deductions=calculation.other_deductions,
                total_deductions=calculation.total_deductions,
                net_pay=calculation.net_pay,
                calculation_date=calculation.calculation_date,
                processed_by="system",
                is_processed=True
            )
            
            self.db.add(payroll_record)
            self.db.commit()
            self.db.refresh(payroll_record)
            
            logger.info(f"Saved payroll record: {payroll_record.id}")
            return payroll_record
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving payroll record: {e}")
            raise
    
    async def get_employee_payroll_history(self, employee_id: str, limit: int = 12) -> List[Dict[str, Any]]:
        """Get payroll history for an employee"""
        try:
            from ..database.models import PayrollRecord
            
            records = self.db.query(PayrollRecord).filter(
                PayrollRecord.employee_id == employee_id
            ).order_by(PayrollRecord.pay_period_start.desc()).limit(limit).all()
            
            history = []
            for record in records:
                history.append({
                    "id": record.id,
                    "pay_period": {
                        "start": record.pay_period_start.isoformat(),
                        "end": record.pay_period_end.isoformat()
                    },
                    "gross_income": float(record.gross_income),
                    "total_deductions": float(record.total_deductions),
                    "net_pay": float(record.net_pay),
                    "calculation_date": record.calculation_date.isoformat()
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting payroll history for employee {employee_id}: {e}")
            raise
    
    async def bulk_process_payroll(self, company_id: str, pay_period_start: date, 
                                 pay_period_end: date) -> Dict[str, Any]:
        """Process payroll for all employees in a company"""
        try:
            # Get all active employees
            employees = await self.employee_service.get_employees_by_company(company_id)
            
            results = {
                "company_id": company_id,
                "pay_period": {
                    "start": pay_period_start.isoformat(),
                    "end": pay_period_end.isoformat()
                },
                "employees_processed": 0,
                "total_gross_pay": 0.0,
                "total_deductions": 0.0,
                "total_net_pay": 0.0,
                "errors": []
            }
            
            for employee in employees:
                try:
                    payroll_result = await self.calculate_employee_payroll(
                        employee.id, pay_period_start, pay_period_end
                    )
                    
                    results["employees_processed"] += 1
                    results["total_gross_pay"] += payroll_result["income"]["gross_total"]
                    results["total_deductions"] += payroll_result["deductions"]["total"]
                    results["total_net_pay"] += payroll_result["net_pay"]
                    
                except Exception as e:
                    results["errors"].append({
                        "employee_id": employee.id,
                        "employee_name": f"{employee.first_name} {employee.last_name}",
                        "error": str(e)
                    })
            
            logger.info(f"Bulk processed payroll for {results['employees_processed']} employees")
            return results
            
        except Exception as e:
            logger.error(f"Error in bulk payroll processing: {e}")
            raise
    
    async def get_company_payroll_summary(self, company_id: str, start_date: date, 
                                        end_date: date) -> Dict[str, Any]:
        """Get payroll summary for a company in a date range"""
        try:
            from ..database.models import PayrollRecord
            from sqlalchemy import func, and_
            
            # Get summary data
            summary = self.db.query(
                func.count(PayrollRecord.id).label("total_records"),
                func.sum(PayrollRecord.gross_income).label("total_gross"),
                func.sum(PayrollRecord.total_deductions).label("total_deductions"),
                func.sum(PayrollRecord.net_pay).label("total_net_pay"),
                func.avg(PayrollRecord.net_pay).label("avg_net_pay")
            ).filter(
                and_(
                    PayrollRecord.company_id == company_id,
                    PayrollRecord.pay_period_start >= start_date,
                    PayrollRecord.pay_period_end <= end_date
                )
            ).first()
            
            return {
                "company_id": company_id,
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "summary": {
                    "total_employees": summary.total_records or 0,
                    "total_gross_pay": float(summary.total_gross or 0),
                    "total_deductions": float(summary.total_deductions or 0),
                    "total_net_pay": float(summary.total_net_pay or 0),
                    "average_net_pay": float(summary.avg_net_pay or 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting payroll summary: {e}")
            raise
    
    async def get_payroll_by_id(self, payroll_id: str) -> Optional[Dict[str, Any]]:
        """Get specific payroll record by ID"""
        try:
            from ..database.models import PayrollRecord
            
            record = self.db.query(PayrollRecord).filter(
                PayrollRecord.id == payroll_id
            ).first()
            
            if not record:
                return None
            
            # Get employee info
            employee = await self.employee_service.get_employee_by_id(record.employee_id)
            
            return {
                "id": record.id,
                "employee": {
                    "id": employee.id,
                    "name": f"{employee.first_name} {employee.last_name}",
                    "employee_number": employee.employee_number
                } if employee else None,
                "pay_period": {
                    "start": record.pay_period_start.isoformat(),
                    "end": record.pay_period_end.isoformat()
                },
                "income": {
                    "base_salary": float(record.base_salary),
                    "overtime_amount": float(record.overtime_amount),
                    "bonuses": float(record.bonuses),
                    "commissions": float(record.commissions),
                    "other_income": float(record.other_income),
                    "gross_total": float(record.gross_income)
                },
                "deductions": {
                    "imss": float(record.imss_employee),
                    "isr": float(record.isr_withheld),
                    "loans": float(record.loan_deductions),
                    "advances": float(record.advance_deductions),
                    "other": float(record.other_deductions),
                    "total": float(record.total_deductions)
                },
                "net_pay": float(record.net_pay),
                "calculation_date": record.calculation_date.isoformat(),
                "is_processed": record.is_processed
            }
            
        except Exception as e:
            logger.error(f"Error getting payroll record {payroll_id}: {e}")
            raise