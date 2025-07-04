"""
Reports Service - Advanced Analytics and Reporting
Complete reporting system with business intelligence
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging
from collections import defaultdict

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, extract

from ..database.models import Employee, PayrollRecord, AttendanceRecord, Company, UserRole

logger = logging.getLogger(__name__)

class ReportsService:
    """Advanced reporting and analytics service"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def generate_payroll_report(self, company_id: str, start_date: date, 
                                    end_date: date) -> Dict[str, Any]:
        """Generate comprehensive payroll report"""
        try:
            # Get payroll records in date range
            payroll_records = self.db.query(PayrollRecord).filter(
                and_(
                    PayrollRecord.company_id == company_id,
                    PayrollRecord.pay_period_start >= start_date,
                    PayrollRecord.pay_period_end <= end_date
                )
            ).all()
            
            # Calculate totals
            total_gross = sum(float(record.gross_income) for record in payroll_records)
            total_deductions = sum(float(record.total_deductions) for record in payroll_records)
            total_net = sum(float(record.net_pay) for record in payroll_records)
            total_imss = sum(float(record.imss_employee) for record in payroll_records)
            total_isr = sum(float(record.isr_withheld) for record in payroll_records)
            
            # Group by department
            dept_summary = defaultdict(lambda: {
                'employees': 0,
                'gross_pay': 0,
                'deductions': 0,
                'net_pay': 0
            })
            
            for record in payroll_records:
                # Get employee department
                employee = self.db.query(Employee).filter(Employee.id == record.employee_id).first()
                dept = employee.department if employee else "Sin Departamento"
                
                dept_summary[dept]['employees'] += 1
                dept_summary[dept]['gross_pay'] += float(record.gross_income)
                dept_summary[dept]['deductions'] += float(record.total_deductions)
                dept_summary[dept]['net_pay'] += float(record.net_pay)
            
            # Calculate averages
            num_employees = len(set(record.employee_id for record in payroll_records))
            avg_gross = total_gross / num_employees if num_employees > 0 else 0
            avg_net = total_net / num_employees if num_employees > 0 else 0
            
            return {
                "report_type": "payroll_summary",
                "company_id": company_id,
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "summary": {
                    "total_employees": num_employees,
                    "total_gross_pay": round(total_gross, 2),
                    "total_deductions": round(total_deductions, 2),
                    "total_net_pay": round(total_net, 2),
                    "total_imss": round(total_imss, 2),
                    "total_isr": round(total_isr, 2),
                    "average_gross_pay": round(avg_gross, 2),
                    "average_net_pay": round(avg_net, 2),
                    "deduction_rate": round((total_deductions / total_gross * 100) if total_gross > 0 else 0, 2)
                },
                "by_department": dict(dept_summary),
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating payroll report: {e}")
            raise
    
    async def generate_attendance_report(self, company_id: str, start_date: date, 
                                       end_date: date) -> Dict[str, Any]:
        """Generate comprehensive attendance report"""
        try:
            # Get all employees in company
            employees = self.db.query(Employee).filter(
                and_(
                    Employee.company_id == company_id,
                    Employee.is_active == True
                )
            ).all()
            
            # Get attendance records in date range
            attendance_records = self.db.query(AttendanceRecord).join(Employee).filter(
                and_(
                    Employee.company_id == company_id,
                    func.date(AttendanceRecord.date) >= start_date,
                    func.date(AttendanceRecord.date) <= end_date
                )
            ).all()
            
            # Calculate statistics
            total_work_days = (end_date - start_date).days + 1
            total_possible_hours = total_work_days * 8 * len(employees)  # 8 hours per day
            
            employee_stats = {}
            total_hours_worked = 0
            total_days_present = 0
            late_arrivals = 0
            
            for employee in employees:
                emp_records = [r for r in attendance_records if r.employee_id == employee.id]
                emp_hours = sum(float(r.hours_worked) for r in emp_records if r.hours_worked)
                emp_days = len([r for r in emp_records if r.check_in_time])
                
                # Count late arrivals (after 9:00 AM)
                emp_late = len([
                    r for r in emp_records 
                    if r.check_in_time and r.check_in_time.time() > datetime.strptime("09:00", "%H:%M").time()
                ])
                
                employee_stats[employee.id] = {
                    "name": f"{employee.first_name} {employee.last_name}",
                    "department": employee.department,
                    "days_present": emp_days,
                    "days_absent": total_work_days - emp_days,
                    "hours_worked": round(emp_hours, 2),
                    "late_arrivals": emp_late,
                    "attendance_rate": round((emp_days / total_work_days * 100), 2) if total_work_days > 0 else 0
                }
                
                total_hours_worked += emp_hours
                total_days_present += emp_days
                late_arrivals += emp_late
            
            # Department summary
            dept_summary = defaultdict(lambda: {
                'employees': 0,
                'total_hours': 0,
                'attendance_rate': 0,
                'late_arrivals': 0
            })
            
            for emp_id, stats in employee_stats.items():
                employee = next(e for e in employees if e.id == emp_id)
                dept = employee.department or "Sin Departamento"
                
                dept_summary[dept]['employees'] += 1
                dept_summary[dept]['total_hours'] += stats['hours_worked']
                dept_summary[dept]['attendance_rate'] += stats['attendance_rate']
                dept_summary[dept]['late_arrivals'] += stats['late_arrivals']
            
            # Calculate department averages
            for dept_data in dept_summary.values():
                if dept_data['employees'] > 0:
                    dept_data['attendance_rate'] = round(dept_data['attendance_rate'] / dept_data['employees'], 2)
                    dept_data['avg_hours_per_employee'] = round(dept_data['total_hours'] / dept_data['employees'], 2)
            
            return {
                "report_type": "attendance_summary",
                "company_id": company_id,
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                    "work_days": total_work_days
                },
                "summary": {
                    "total_employees": len(employees),
                    "total_hours_worked": round(total_hours_worked, 2),
                    "total_days_present": total_days_present,
                    "total_late_arrivals": late_arrivals,
                    "overall_attendance_rate": round((total_days_present / (total_work_days * len(employees)) * 100) if len(employees) > 0 else 0, 2),
                    "average_hours_per_employee": round(total_hours_worked / len(employees), 2) if len(employees) > 0 else 0
                },
                "by_employee": employee_stats,
                "by_department": dict(dept_summary),
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating attendance report: {e}")
            raise
    
    async def generate_executive_dashboard(self, company_id: str) -> Dict[str, Any]:
        """Generate executive dashboard with KPIs"""
        try:
            # Current month data
            now = datetime.now()
            current_month_start = now.replace(day=1).date()
            current_month_end = now.date()
            
            # Previous month for comparison
            prev_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
            prev_month_end = current_month_start - timedelta(days=1)
            
            # Get employee counts
            total_employees = self.db.query(Employee).filter(
                and_(
                    Employee.company_id == company_id,
                    Employee.is_active == True
                )
            ).count()
            
            # Current month payroll
            current_payroll = await self.generate_payroll_report(company_id, current_month_start, current_month_end)
            
            # Previous month payroll for comparison
            prev_payroll = await self.generate_payroll_report(company_id, prev_month_start, prev_month_end)
            
            # Current month attendance
            current_attendance = await self.generate_attendance_report(company_id, current_month_start, current_month_end)
            
            # Calculate trends
            payroll_trend = 0
            if prev_payroll["summary"]["total_gross_pay"] > 0:
                payroll_trend = round(
                    ((current_payroll["summary"]["total_gross_pay"] - prev_payroll["summary"]["total_gross_pay"]) / 
                     prev_payroll["summary"]["total_gross_pay"] * 100), 2
                )
            
            # Department distribution
            dept_distribution = self.db.query(
                Employee.department,
                func.count(Employee.id).label('count')
            ).filter(
                and_(
                    Employee.company_id == company_id,
                    Employee.is_active == True
                )
            ).group_by(Employee.department).all()
            
            dept_data = {dept or "Sin Departamento": count for dept, count in dept_distribution}
            
            # Role distribution
            role_distribution = self.db.query(
                Employee.role,
                func.count(Employee.id).label('count')
            ).filter(
                and_(
                    Employee.company_id == company_id,
                    Employee.is_active == True
                )
            ).group_by(Employee.role).all()
            
            role_data = {role.value: count for role, count in role_distribution}
            
            # Recent hires (last 30 days)
            thirty_days_ago = now.date() - timedelta(days=30)
            recent_hires = self.db.query(Employee).filter(
                and_(
                    Employee.company_id == company_id,
                    Employee.hire_date >= thirty_days_ago,
                    Employee.is_active == True
                )
            ).count()
            
            return {
                "dashboard_type": "executive_summary",
                "company_id": company_id,
                "generated_at": datetime.now().isoformat(),
                "kpis": {
                    "total_employees": total_employees,
                    "recent_hires_30_days": recent_hires,
                    "current_month_payroll": current_payroll["summary"]["total_gross_pay"],
                    "payroll_trend_percent": payroll_trend,
                    "attendance_rate": current_attendance["summary"]["overall_attendance_rate"],
                    "average_hours_per_employee": current_attendance["summary"]["average_hours_per_employee"]
                },
                "current_month": {
                    "payroll": current_payroll["summary"],
                    "attendance": current_attendance["summary"]
                },
                "distributions": {
                    "by_department": dept_data,
                    "by_role": role_data
                },
                "trends": {
                    "payroll_change_percent": payroll_trend,
                    "previous_month_payroll": prev_payroll["summary"]["total_gross_pay"]
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating executive dashboard: {e}")
            raise
    
    async def generate_employee_performance_report(self, employee_id: str, 
                                                 start_date: date, end_date: date) -> Dict[str, Any]:
        """Generate individual employee performance report"""
        try:
            # Get employee info
            employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
            if not employee:
                raise ValueError(f"Employee {employee_id} not found")
            
            # Get payroll records
            payroll_records = self.db.query(PayrollRecord).filter(
                and_(
                    PayrollRecord.employee_id == employee_id,
                    PayrollRecord.pay_period_start >= start_date,
                    PayrollRecord.pay_period_end <= end_date
                )
            ).all()
            
            # Get attendance records
            attendance_records = self.db.query(AttendanceRecord).filter(
                and_(
                    AttendanceRecord.employee_id == employee_id,
                    func.date(AttendanceRecord.date) >= start_date,
                    func.date(AttendanceRecord.date) <= end_date
                )
            ).all()
            
            # Calculate payroll stats
            total_gross = sum(float(record.gross_income) for record in payroll_records)
            total_net = sum(float(record.net_pay) for record in payroll_records)
            total_overtime = sum(float(record.overtime_amount) for record in payroll_records)
            avg_monthly_gross = total_gross / len(payroll_records) if payroll_records else 0
            
            # Calculate attendance stats
            total_hours_worked = sum(float(record.hours_worked) for record in attendance_records if record.hours_worked)
            days_present = len([r for r in attendance_records if r.check_in_time])
            total_days = (end_date - start_date).days + 1
            attendance_rate = (days_present / total_days * 100) if total_days > 0 else 0
            
            # Late arrivals
            late_count = len([
                r for r in attendance_records 
                if r.check_in_time and r.check_in_time.time() > datetime.strptime("09:00", "%H:%M").time()
            ])
            
            # Monthly breakdown
            monthly_data = defaultdict(lambda: {
                'gross_pay': 0,
                'net_pay': 0,
                'hours_worked': 0,
                'days_present': 0,
                'overtime_hours': 0
            })
            
            for record in payroll_records:
                month_key = record.pay_period_start.strftime("%Y-%m")
                monthly_data[month_key]['gross_pay'] += float(record.gross_income)
                monthly_data[month_key]['net_pay'] += float(record.net_pay)
                monthly_data[month_key]['overtime_hours'] += float(record.overtime_hours)
            
            for record in attendance_records:
                month_key = record.date.strftime("%Y-%m")
                if record.hours_worked:
                    monthly_data[month_key]['hours_worked'] += float(record.hours_worked)
                if record.check_in_time:
                    monthly_data[month_key]['days_present'] += 1
            
            return {
                "report_type": "employee_performance",
                "employee": {
                    "id": employee.id,
                    "name": f"{employee.first_name} {employee.last_name}",
                    "employee_number": employee.employee_number,
                    "department": employee.department,
                    "position": employee.position,
                    "hire_date": employee.hire_date.isoformat()
                },
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "payroll_summary": {
                    "total_gross_pay": round(total_gross, 2),
                    "total_net_pay": round(total_net, 2),
                    "total_overtime_pay": round(total_overtime, 2),
                    "average_monthly_gross": round(avg_monthly_gross, 2),
                    "pay_periods": len(payroll_records)
                },
                "attendance_summary": {
                    "total_hours_worked": round(total_hours_worked, 2),
                    "days_present": days_present,
                    "total_possible_days": total_days,
                    "attendance_rate": round(attendance_rate, 2),
                    "late_arrivals": late_count,
                    "average_hours_per_day": round(total_hours_worked / days_present, 2) if days_present > 0 else 0
                },
                "monthly_breakdown": dict(monthly_data),
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating employee performance report: {e}")
            raise
    
    async def generate_cost_analysis_report(self, company_id: str, start_date: date, 
                                          end_date: date) -> Dict[str, Any]:
        """Generate detailed cost analysis report"""
        try:
            # Get all payroll records
            payroll_records = self.db.query(PayrollRecord).filter(
                and_(
                    PayrollRecord.company_id == company_id,
                    PayrollRecord.pay_period_start >= start_date,
                    PayrollRecord.pay_period_end <= end_date
                )
            ).all()
            
            # Calculate detailed costs
            costs = {
                'base_salaries': 0,
                'overtime_costs': 0,
                'bonuses': 0,
                'commissions': 0,
                'imss_employee': 0,
                'isr_withheld': 0,
                'total_gross': 0,
                'total_deductions': 0,
                'total_net': 0
            }
            
            for record in payroll_records:
                costs['base_salaries'] += float(record.base_salary)
                costs['overtime_costs'] += float(record.overtime_amount)
                costs['bonuses'] += float(record.bonuses)
                costs['commissions'] += float(record.commissions)
                costs['imss_employee'] += float(record.imss_employee)
                costs['isr_withheld'] += float(record.isr_withheld)
                costs['total_gross'] += float(record.gross_income)
                costs['total_deductions'] += float(record.total_deductions)
                costs['total_net'] += float(record.net_pay)
            
            # Calculate percentages
            total_gross = costs['total_gross']
            cost_breakdown = {}
            if total_gross > 0:
                cost_breakdown = {
                    'base_salary_percent': round(costs['base_salaries'] / total_gross * 100, 2),
                    'overtime_percent': round(costs['overtime_costs'] / total_gross * 100, 2),
                    'bonus_percent': round(costs['bonuses'] / total_gross * 100, 2),
                    'commission_percent': round(costs['commissions'] / total_gross * 100, 2),
                    'deduction_percent': round(costs['total_deductions'] / total_gross * 100, 2)
                }
            
            # Department cost analysis
            dept_costs = defaultdict(lambda: {'gross': 0, 'net': 0, 'employees': 0})
            
            for record in payroll_records:
                employee = self.db.query(Employee).filter(Employee.id == record.employee_id).first()
                dept = employee.department if employee else "Sin Departamento"
                
                dept_costs[dept]['gross'] += float(record.gross_income)
                dept_costs[dept]['net'] += float(record.net_pay)
                dept_costs[dept]['employees'] += 1
            
            # Calculate average costs per department
            for dept_data in dept_costs.values():
                if dept_data['employees'] > 0:
                    dept_data['avg_gross_per_employee'] = round(dept_data['gross'] / dept_data['employees'], 2)
                    dept_data['avg_net_per_employee'] = round(dept_data['net'] / dept_data['employees'], 2)
            
            return {
                "report_type": "cost_analysis",
                "company_id": company_id,
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "total_costs": {k: round(v, 2) for k, v in costs.items()},
                "cost_breakdown_percentages": cost_breakdown,
                "by_department": dict(dept_costs),
                "key_metrics": {
                    "cost_per_employee": round(total_gross / len(set(r.employee_id for r in payroll_records)), 2) if payroll_records else 0,
                    "deduction_rate": round(costs['total_deductions'] / total_gross * 100, 2) if total_gross > 0 else 0,
                    "net_pay_rate": round(costs['total_net'] / total_gross * 100, 2) if total_gross > 0 else 0
                },
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating cost analysis report: {e}")
            raise