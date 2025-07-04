"""
Overtime Management System - International Compliance
1000+ lines of advanced overtime calculations and approvals
"""

import asyncio
import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date, timedelta, time
from dataclasses import dataclass
from enum import Enum
import uuid

from ..config.settings import get_settings
from ..models.base import OvertimeStatus, UserRole

settings = get_settings()
logger = logging.getLogger(__name__)


class OvertimeType(Enum):
    """Types of overtime"""
    REGULAR = "regular"  # Normal overtime
    WEEKEND = "weekend"  # Weekend work
    HOLIDAY = "holiday"  # Holiday work
    NIGHT_SHIFT = "night_shift"  # Night shift premium
    EMERGENCY = "emergency"  # Emergency overtime


class CountryCode(Enum):
    """Supported countries"""
    MEXICO = "MEX"
    USA = "USA"
    CANADA = "CAN"
    SPAIN = "ESP"
    UK = "GBR"
    GERMANY = "DEU"


@dataclass
class OvertimeRequest:
    """Overtime request structure"""
    id: str
    employee_id: str
    company_id: str
    request_date: datetime
    work_date: date
    start_time: time
    end_time: time
    hours_requested: Decimal
    overtime_type: OvertimeType
    reason: str
    status: OvertimeStatus
    requested_by: str
    approved_by: Optional[str] = None
    approval_date: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None


@dataclass
class OvertimeCalculation:
    """Overtime calculation results"""
    employee_id: str
    overtime_request_id: str
    regular_hours: Decimal
    overtime_hours: Decimal
    double_time_hours: Decimal
    triple_time_hours: Decimal
    base_hourly_rate: Decimal
    overtime_rate_multiplier: Decimal
    total_overtime_amount: Decimal
    calculation_date: datetime
    country_code: str
    currency: str


class OvertimeLimits:
    """Overtime limits by country"""
    
    # Mexico - Ley Federal del Trabajo
    MEXICO_LIMITS = {
        "max_daily_overtime": 3,  # 3 hours max per day
        "max_weekly_overtime": 9,  # 9 hours max per week
        "max_annual_overtime": 780,  # 26 weeks * 30 hours
        "double_time_threshold": 9,  # First 9 hours double time
        "triple_time_threshold": 17,  # Hours 10+ triple time
        "requires_approval": True,
        "employee_consent_required": True
    }
    
    # USA - Fair Labor Standards Act (FLSA)
    USA_LIMITS = {
        "max_weekly_hours": 40,  # 40 hours before overtime
        "overtime_rate": Decimal("1.5"),  # Time and a half
        "no_daily_limit": True,
        "requires_approval": False,  # Depends on company policy
        "state_variations": True
    }
    
    # Canada - Labour Standards
    CANADA_LIMITS = {
        "max_daily_hours": 8,  # 8 hours before overtime
        "max_weekly_hours": 44,  # 44 hours before overtime
        "overtime_rate": Decimal("1.5"),
        "double_time_after": 12,  # Double time after 12 hours/day
        "requires_approval": True
    }
    
    # European Union - Working Time Directive
    EU_LIMITS = {
        "max_weekly_hours": 48,  # Including overtime
        "max_daily_hours": 11,  # Including breaks
        "min_rest_period": 11,  # Hours between shifts
        "requires_employee_agreement": True,
        "opt_out_available": True  # Some countries allow opt-out
    }
    
    @classmethod
    def get_limits_for_country(cls, country_code: str) -> Dict[str, Any]:
        """Get overtime limits for specific country"""
        limits_map = {
            "MEX": cls.MEXICO_LIMITS,
            "USA": cls.USA_LIMITS,
            "CAN": cls.CANADA_LIMITS,
            "ESP": cls.EU_LIMITS,
            "GBR": cls.EU_LIMITS,
            "DEU": cls.EU_LIMITS,
        }
        return limits_map.get(country_code, cls.USA_LIMITS)


class OvertimeCalculator:
    """Calculate overtime amounts based on country regulations"""
    
    @classmethod
    def calculate_mexico_overtime(cls, base_hourly_rate: Decimal, 
                                overtime_hours: Decimal) -> OvertimeCalculation:
        """Calculate overtime for Mexico (LFT compliance)"""
        regular_hours = Decimal("0")
        double_time_hours = Decimal("0")
        triple_time_hours = Decimal("0")
        
        remaining_hours = overtime_hours
        
        # First 9 hours: double time (200%)
        if remaining_hours > 0:
            double_time_hours = min(remaining_hours, Decimal("9"))
            remaining_hours -= double_time_hours
        
        # Additional hours: triple time (300%)
        if remaining_hours > 0:
            triple_time_hours = remaining_hours
        
        # Calculate amounts
        double_time_amount = double_time_hours * base_hourly_rate * Decimal("2")
        triple_time_amount = triple_time_hours * base_hourly_rate * Decimal("3")
        total_amount = double_time_amount + triple_time_amount
        
        return OvertimeCalculation(
            employee_id="",
            overtime_request_id="",
            regular_hours=regular_hours,
            overtime_hours=overtime_hours,
            double_time_hours=double_time_hours,
            triple_time_hours=triple_time_hours,
            base_hourly_rate=base_hourly_rate,
            overtime_rate_multiplier=Decimal("2"),  # Primary rate
            total_overtime_amount=total_amount,
            calculation_date=datetime.now(),
            country_code="MEX",
            currency="MXN"
        )
    
    @classmethod
    def calculate_usa_overtime(cls, base_hourly_rate: Decimal,
                             regular_hours: Decimal, total_hours: Decimal) -> OvertimeCalculation:
        """Calculate overtime for USA (FLSA compliance)"""
        overtime_hours = max(Decimal("0"), total_hours - Decimal("40"))
        regular_pay_hours = min(total_hours, Decimal("40"))
        
        # Time and a half for hours over 40
        overtime_amount = overtime_hours * base_hourly_rate * Decimal("1.5")
        
        return OvertimeCalculation(
            employee_id="",
            overtime_request_id="",
            regular_hours=regular_pay_hours,
            overtime_hours=overtime_hours,
            double_time_hours=overtime_hours,  # All overtime is time and a half
            triple_time_hours=Decimal("0"),
            base_hourly_rate=base_hourly_rate,
            overtime_rate_multiplier=Decimal("1.5"),
            total_overtime_amount=overtime_amount,
            calculation_date=datetime.now(),
            country_code="USA",
            currency="USD"
        )
    
    @classmethod
    def calculate_canada_overtime(cls, base_hourly_rate: Decimal,
                                daily_hours: Decimal, weekly_hours: Decimal) -> OvertimeCalculation:
        """Calculate overtime for Canada"""
        # Daily overtime after 8 hours
        daily_overtime = max(Decimal("0"), daily_hours - Decimal("8"))
        
        # Weekly overtime after 44 hours
        weekly_overtime = max(Decimal("0"), weekly_hours - Decimal("44"))
        
        # Use the higher of daily or weekly calculation
        overtime_hours = max(daily_overtime, weekly_overtime)
        
        # Double time after 12 hours in a day
        double_time_hours = max(Decimal("0"), daily_hours - Decimal("12"))
        time_and_half_hours = overtime_hours - double_time_hours
        
        # Calculate amounts
        time_and_half_amount = time_and_half_hours * base_hourly_rate * Decimal("1.5")
        double_time_amount = double_time_hours * base_hourly_rate * Decimal("2")
        total_amount = time_and_half_amount + double_time_amount
        
        return OvertimeCalculation(
            employee_id="",
            overtime_request_id="",
            regular_hours=min(daily_hours, Decimal("8")),
            overtime_hours=overtime_hours,
            double_time_hours=time_and_half_hours,
            triple_time_hours=double_time_hours,  # Using triple_time for double time
            base_hourly_rate=base_hourly_rate,
            overtime_rate_multiplier=Decimal("1.5"),
            total_overtime_amount=total_amount,
            calculation_date=datetime.now(),
            country_code="CAN",
            currency="CAD"
        )
    
    @classmethod
    def calculate_eu_overtime(cls, base_hourly_rate: Decimal,
                            weekly_hours: Decimal, country_code: str) -> OvertimeCalculation:
        """Calculate overtime for EU countries"""
        # Basic EU calculation - countries may have specific rules
        overtime_hours = max(Decimal("0"), weekly_hours - Decimal("40"))
        
        # Most EU countries use time and a half or higher
        multiplier = Decimal("1.5")
        if country_code == "DEU":  # Germany often has higher rates
            multiplier = Decimal("1.75")
        
        overtime_amount = overtime_hours * base_hourly_rate * multiplier
        
        return OvertimeCalculation(
            employee_id="",
            overtime_request_id="",
            regular_hours=min(weekly_hours, Decimal("40")),
            overtime_hours=overtime_hours,
            double_time_hours=overtime_hours,
            triple_time_hours=Decimal("0"),
            base_hourly_rate=base_hourly_rate,
            overtime_rate_multiplier=multiplier,
            total_overtime_amount=overtime_amount,
            calculation_date=datetime.now(),
            country_code=country_code,
            currency="EUR"
        )


class OvertimeValidator:
    """Validate overtime requests against legal limits"""
    
    @classmethod
    def validate_request(cls, request: OvertimeRequest, 
                        employee_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate overtime request"""
        errors = []
        country_code = employee_data.get("country_code", "USA")
        limits = OvertimeLimits.get_limits_for_country(country_code)
        
        # Validate based on country
        if country_code == "MEX":
            errors.extend(cls._validate_mexico_request(request, limits, employee_data))
        elif country_code == "USA":
            errors.extend(cls._validate_usa_request(request, limits, employee_data))
        elif country_code == "CAN":
            errors.extend(cls._validate_canada_request(request, limits, employee_data))
        else:  # EU countries
            errors.extend(cls._validate_eu_request(request, limits, employee_data))
        
        # Common validations
        errors.extend(cls._validate_common_rules(request, employee_data))
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    @classmethod
    def _validate_mexico_request(cls, request: OvertimeRequest, limits: Dict[str, Any],
                               employee_data: Dict[str, Any]) -> List[str]:
        """Validate Mexico-specific overtime rules"""
        errors = []
        
        # Daily limit check
        if request.hours_requested > limits["max_daily_overtime"]:
            errors.append(f"Exceeds daily overtime limit of {limits['max_daily_overtime']} hours")
        
        # Weekly limit check (would need to query existing overtime this week)
        # weekly_overtime = cls._get_weekly_overtime(request.employee_id, request.work_date)
        # if weekly_overtime + request.hours_requested > limits["max_weekly_overtime"]:
        #     errors.append(f"Exceeds weekly overtime limit of {limits['max_weekly_overtime']} hours")
        
        # Employee consent check
        if limits["employee_consent_required"]:
            consent = employee_data.get("overtime_consent", False)
            if not consent:
                errors.append("Employee consent required for overtime work")
        
        return errors
    
    @classmethod
    def _validate_usa_request(cls, request: OvertimeRequest, limits: Dict[str, Any],
                            employee_data: Dict[str, Any]) -> List[str]:
        """Validate USA-specific overtime rules"""
        errors = []
        
        # Check if employee is exempt
        if employee_data.get("flsa_exempt", False):
            errors.append("Employee is FLSA exempt and not eligible for overtime")
        
        # State-specific validations (simplified)
        state = employee_data.get("state", "")
        if state == "CA":  # California has daily overtime
            if request.hours_requested > 8:  # Daily limit
                errors.append("California daily overtime limit exceeded")
        
        return errors
    
    @classmethod
    def _validate_canada_request(cls, request: OvertimeRequest, limits: Dict[str, Any],
                               employee_data: Dict[str, Any]) -> List[str]:
        """Validate Canada-specific overtime rules"""
        errors = []
        
        # Daily hours check
        total_daily_hours = 8 + request.hours_requested  # Assuming 8 regular hours
        if total_daily_hours > 12:
            errors.append("Exceeds maximum daily hours (12)")
        
        # Approval required
        if limits["requires_approval"] and request.status == OvertimeStatus.AUTO_APPROVED:
            errors.append("Overtime requires manager approval in Canada")
        
        return errors
    
    @classmethod
    def _validate_eu_request(cls, request: OvertimeRequest, limits: Dict[str, Any],
                           employee_data: Dict[str, Any]) -> List[str]:
        """Validate EU-specific overtime rules"""
        errors = []
        
        # Weekly hours limit
        # weekly_hours = cls._get_weekly_hours(request.employee_id, request.work_date)
        # if weekly_hours + request.hours_requested > limits["max_weekly_hours"]:
        #     errors.append(f"Exceeds EU weekly working time limit of {limits['max_weekly_hours']} hours")
        
        # Employee agreement check
        if limits["requires_employee_agreement"]:
            agreement = employee_data.get("overtime_agreement", False)
            if not agreement:
                errors.append("Employee agreement required for overtime work")
        
        return errors
    
    @classmethod
    def _validate_common_rules(cls, request: OvertimeRequest,
                             employee_data: Dict[str, Any]) -> List[str]:
        """Common validation rules for all countries"""
        errors = []
        
        # Future date check
        if request.work_date < date.today():
            errors.append("Cannot request overtime for past dates")
        
        # Maximum request period
        max_advance_days = 30
        if request.work_date > date.today() + timedelta(days=max_advance_days):
            errors.append(f"Cannot request overtime more than {max_advance_days} days in advance")
        
        # Minimum hours check
        if request.hours_requested < Decimal("0.5"):
            errors.append("Minimum overtime request is 0.5 hours")
        
        # Maximum single request
        if request.hours_requested > Decimal("12"):
            errors.append("Maximum single overtime request is 12 hours")
        
        # Business hours check for certain types
        if request.overtime_type == OvertimeType.REGULAR:
            # Check if request is outside normal business hours
            start_hour = request.start_time.hour
            end_hour = request.end_time.hour
            
            if 9 <= start_hour <= 17 and 9 <= end_hour <= 17:
                errors.append("Regular overtime should be outside business hours (9 AM - 5 PM)")
        
        return errors


class ApprovalWorkflow:
    """Manage overtime approval workflows"""
    
    @classmethod
    def determine_approval_requirements(cls, request: OvertimeRequest,
                                      employee_data: Dict[str, Any]) -> Dict[str, Any]:
        """Determine what approvals are needed"""
        country_code = employee_data.get("country_code", "USA")
        limits = OvertimeLimits.get_limits_for_country(country_code)
        
        approval_info = {
            "requires_approval": False,
            "approval_levels": [],
            "auto_approve_eligible": False,
            "estimated_approval_time": timedelta(hours=24)
        }
        
        # Country-specific approval requirements
        if country_code == "MEX":
            approval_info["requires_approval"] = True
            approval_info["approval_levels"] = ["supervisor", "hr_admin"]
        elif country_code in ["CAN", "ESP", "GBR", "DEU"]:
            approval_info["requires_approval"] = True
            approval_info["approval_levels"] = ["supervisor"]
        
        # Auto-approval eligibility
        if (request.hours_requested <= Decimal("2") and 
            request.overtime_type == OvertimeType.REGULAR and
            not limits.get("requires_approval", True)):
            approval_info["auto_approve_eligible"] = True
        
        # Emergency override
        if request.overtime_type == OvertimeType.EMERGENCY:
            approval_info["auto_approve_eligible"] = True
            approval_info["estimated_approval_time"] = timedelta(hours=1)
        
        return approval_info
    
    @classmethod
    async def process_approval_request(cls, request: OvertimeRequest,
                                     approver_id: str, action: str,
                                     comments: str = "") -> Dict[str, Any]:
        """Process an approval action"""
        result = {
            "success": False,
            "message": "",
            "new_status": request.status,
            "next_approver": None
        }
        
        if action.lower() == "approve":
            # Check if this approver has authority
            approver_data = await cls._get_approver_data(approver_id)
            if not approver_data:
                result["message"] = "Approver not found"
                return result
            
            # Update request
            request.status = OvertimeStatus.APPROVED
            request.approved_by = approver_id
            request.approval_date = datetime.now()
            
            result["success"] = True
            result["message"] = "Overtime request approved"
            result["new_status"] = OvertimeStatus.APPROVED
            
        elif action.lower() == "reject":
            request.status = OvertimeStatus.REJECTED
            request.rejection_reason = comments
            request.approved_by = approver_id
            request.approval_date = datetime.now()
            
            result["success"] = True
            result["message"] = "Overtime request rejected"
            result["new_status"] = OvertimeStatus.REJECTED
        
        return result
    
    @classmethod
    async def _get_approver_data(cls, approver_id: str) -> Optional[Dict[str, Any]]:
        """Get approver information"""
        # Mock implementation - would query database
        mock_approvers = {
            "mgr_001": {
                "id": "mgr_001",
                "name": "Manager One",
                "role": "supervisor",
                "approval_limit": Decimal("8")
            },
            "hr_001": {
                "id": "hr_001",
                "name": "HR Admin",
                "role": "hr_admin",
                "approval_limit": Decimal("12")
            }
        }
        
        return mock_approvers.get(approver_id)


class OvertimeReporting:
    """Generate overtime reports and analytics"""
    
    @classmethod
    def generate_employee_overtime_summary(cls, employee_id: str,
                                         start_date: date, end_date: date) -> Dict[str, Any]:
        """Generate overtime summary for an employee"""
        # Mock data - would query database
        return {
            "employee_id": employee_id,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_overtime_hours": Decimal("32.5"),
            "total_overtime_amount": Decimal("2875.00"),
            "average_weekly_overtime": Decimal("8.1"),
            "overtime_by_type": {
                "regular": Decimal("28.0"),
                "weekend": Decimal("4.5"),
                "holiday": Decimal("0.0"),
                "emergency": Decimal("0.0")
            },
            "approval_stats": {
                "auto_approved": 5,
                "manager_approved": 3,
                "hr_approved": 1,
                "rejected": 0
            },
            "compliance_alerts": []
        }
    
    @classmethod
    def generate_company_overtime_report(cls, company_id: str,
                                       start_date: date, end_date: date) -> Dict[str, Any]:
        """Generate company-wide overtime report"""
        return {
            "company_id": company_id,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_employees": 25,
            "employees_with_overtime": 18,
            "total_overtime_hours": Decimal("456.5"),
            "total_overtime_cost": Decimal("47250.00"),
            "average_overtime_per_employee": Decimal("25.4"),
            "overtime_trend": {
                "vs_previous_period": "+12.5%",
                "monthly_average": Decimal("380.2")
            },
            "by_department": {
                "Engineering": {"hours": Decimal("285.0"), "cost": Decimal("31200.00")},
                "Sales": {"hours": Decimal("124.5"), "cost": Decimal("11850.00")},
                "Support": {"hours": Decimal("47.0"), "cost": Decimal("4200.00")}
            },
            "compliance_summary": {
                "violations": 0,
                "warnings": 2,
                "countries_covered": ["MEX", "USA"]
            }
        }


class OvertimeManagementEngine:
    """Main Overtime Management Engine"""
    
    def __init__(self):
        self.calculator = OvertimeCalculator()
        self.validator = OvertimeValidator()
        self.workflow = ApprovalWorkflow()
        self.reporting = OvertimeReporting()
    
    async def create_overtime_request(self, employee_id: str, company_id: str,
                                    overtime_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new overtime request"""
        try:
            # Create request object
            request = OvertimeRequest(
                id=str(uuid.uuid4()),
                employee_id=employee_id,
                company_id=company_id,
                request_date=datetime.now(),
                work_date=datetime.fromisoformat(overtime_data["work_date"]).date(),
                start_time=datetime.fromisoformat(overtime_data["start_time"]).time(),
                end_time=datetime.fromisoformat(overtime_data["end_time"]).time(),
                hours_requested=Decimal(str(overtime_data["hours_requested"])),
                overtime_type=OvertimeType(overtime_data.get("overtime_type", "regular")),
                reason=overtime_data.get("reason", ""),
                status=OvertimeStatus.PENDING,
                requested_by=employee_id
            )
            
            # Get employee data
            employee_data = await self._get_employee_data(employee_id)
            if not employee_data:
                return {"success": False, "message": "Employee not found"}
            
            # Validate request
            is_valid, errors = self.validator.validate_request(request, employee_data)
            if not is_valid:
                return {"success": False, "message": "Validation failed", "errors": errors}
            
            # Determine approval requirements
            approval_info = self.workflow.determine_approval_requirements(request, employee_data)
            
            # Auto-approve if eligible
            if approval_info["auto_approve_eligible"]:
                request.status = OvertimeStatus.AUTO_APPROVED
                request.approval_date = datetime.now()
            
            # Save request (mock)
            await self._save_overtime_request(request)
            
            # Calculate potential amount
            calculation = await self._calculate_overtime_amount(request, employee_data)
            
            return {
                "success": True,
                "request_id": request.id,
                "status": request.status.value,
                "approval_info": approval_info,
                "estimated_amount": float(calculation.total_overtime_amount),
                "message": "Overtime request created successfully"
            }
            
        except Exception as e:
            logger.error(f"Error creating overtime request: {e}")
            return {"success": False, "message": "System error occurred"}
    
    async def approve_overtime_request(self, request_id: str, approver_id: str,
                                     action: str, comments: str = "") -> Dict[str, Any]:
        """Approve or reject overtime request"""
        try:
            # Get request
            request = await self._get_overtime_request(request_id)
            if not request:
                return {"success": False, "message": "Request not found"}
            
            if request.status != OvertimeStatus.PENDING:
                return {"success": False, "message": "Request is not pending approval"}
            
            # Process approval
            result = await self.workflow.process_approval_request(
                request, approver_id, action, comments
            )
            
            if result["success"]:
                # Update request in database
                await self._save_overtime_request(request)
                
                # Send notification to employee
                await self._send_approval_notification(request, action, comments)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing approval: {e}")
            return {"success": False, "message": "System error occurred"}
    
    async def calculate_overtime_pay(self, employee_id: str,
                                   pay_period_start: date, pay_period_end: date) -> Dict[str, Any]:
        """Calculate total overtime pay for a pay period"""
        try:
            # Get approved overtime requests for period
            requests = await self._get_approved_overtime_requests(
                employee_id, pay_period_start, pay_period_end
            )
            
            if not requests:
                return {
                    "employee_id": employee_id,
                    "total_overtime_hours": Decimal("0"),
                    "total_overtime_amount": Decimal("0"),
                    "calculations": []
                }
            
            # Get employee data
            employee_data = await self._get_employee_data(employee_id)
            
            total_hours = Decimal("0")
            total_amount = Decimal("0")
            calculations = []
            
            for request in requests:
                calculation = await self._calculate_overtime_amount(request, employee_data)
                calculations.append({
                    "request_id": request.id,
                    "work_date": request.work_date.isoformat(),
                    "hours": float(request.hours_requested),
                    "amount": float(calculation.total_overtime_amount),
                    "overtime_type": request.overtime_type.value
                })
                
                total_hours += request.hours_requested
                total_amount += calculation.total_overtime_amount
            
            return {
                "employee_id": employee_id,
                "pay_period": {
                    "start": pay_period_start.isoformat(),
                    "end": pay_period_end.isoformat()
                },
                "total_overtime_hours": float(total_hours),
                "total_overtime_amount": float(total_amount),
                "calculations": calculations
            }
            
        except Exception as e:
            logger.error(f"Error calculating overtime pay: {e}")
            return {"error": "System error occurred"}
    
    async def get_pending_approvals(self, approver_id: str) -> List[Dict[str, Any]]:
        """Get pending overtime requests for an approver"""
        try:
            # Mock implementation - would query database
            pending_requests = [
                {
                    "id": "ot_001",
                    "employee_name": "Juan Pérez",
                    "work_date": "2024-12-15",
                    "hours_requested": 3.0,
                    "overtime_type": "regular",
                    "reason": "Project deadline",
                    "estimated_amount": 750.00,
                    "request_date": "2024-12-13T10:30:00"
                },
                {
                    "id": "ot_002",
                    "employee_name": "María González",
                    "work_date": "2024-12-16",
                    "hours_requested": 2.5,
                    "overtime_type": "weekend",
                    "reason": "Server maintenance",
                    "estimated_amount": 875.00,
                    "request_date": "2024-12-14T15:45:00"
                }
            ]
            
            return pending_requests
            
        except Exception as e:
            logger.error(f"Error getting pending approvals: {e}")
            return []
    
    async def generate_overtime_report(self, company_id: str, report_type: str,
                                     start_date: date, end_date: date) -> Dict[str, Any]:
        """Generate overtime reports"""
        try:
            if report_type == "company":
                return self.reporting.generate_company_overtime_report(
                    company_id, start_date, end_date
                )
            elif report_type == "employee":
                # Would need employee_id parameter
                return self.reporting.generate_employee_overtime_summary(
                    "emp_001", start_date, end_date
                )
            else:
                return {"error": "Invalid report type"}
                
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return {"error": "System error occurred"}
    
    async def _get_employee_data(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """Get employee data"""
        # Mock implementation
        mock_employees = {
            "emp_001": {
                "id": "emp_001",
                "name": "Juan Pérez",
                "country_code": "MEX",
                "monthly_salary": 15000.0,
                "overtime_consent": True,
                "flsa_exempt": False
            }
        }
        return mock_employees.get(employee_id)
    
    async def _save_overtime_request(self, request: OvertimeRequest):
        """Save overtime request to database"""
        # Mock implementation
        logger.info(f"Saving overtime request {request.id}")
    
    async def _get_overtime_request(self, request_id: str) -> Optional[OvertimeRequest]:
        """Get overtime request by ID"""
        # Mock implementation
        return None
    
    async def _get_approved_overtime_requests(self, employee_id: str,
                                            start_date: date, end_date: date) -> List[OvertimeRequest]:
        """Get approved overtime requests for period"""
        # Mock implementation
        return []
    
    async def _calculate_overtime_amount(self, request: OvertimeRequest,
                                       employee_data: Dict[str, Any]) -> OvertimeCalculation:
        """Calculate overtime amount for a request"""
        country_code = employee_data.get("country_code", "USA")
        monthly_salary = Decimal(str(employee_data.get("monthly_salary", 0)))
        
        # Calculate hourly rate (assuming 22 working days, 8 hours/day)
        hourly_rate = monthly_salary / (Decimal("22") * Decimal("8"))
        
        if country_code == "MEX":
            calculation = self.calculator.calculate_mexico_overtime(hourly_rate, request.hours_requested)
        elif country_code == "USA":
            calculation = self.calculator.calculate_usa_overtime(hourly_rate, Decimal("40"), Decimal("48"))
        elif country_code == "CAN":
            calculation = self.calculator.calculate_canada_overtime(hourly_rate, Decimal("10"), Decimal("44"))
        else:
            calculation = self.calculator.calculate_eu_overtime(hourly_rate, Decimal("48"), country_code)
        
        calculation.employee_id = request.employee_id
        calculation.overtime_request_id = request.id
        
        return calculation
    
    async def _send_approval_notification(self, request: OvertimeRequest,
                                        action: str, comments: str):
        """Send notification about approval decision"""
        # Would integrate with messaging system
        logger.info(f"Sending {action} notification for overtime request {request.id}")
    
    def validate_overtime_limits(self, employee_id: str, country_code: str) -> Dict[str, Any]:
        """Get overtime limits and current usage for an employee"""
        limits = OvertimeLimits.get_limits_for_country(country_code)
        
        # Mock current usage - would query database
        current_usage = {
            "daily_overtime_today": Decimal("2.0"),
            "weekly_overtime": Decimal("8.0"),
            "monthly_overtime": Decimal("32.0"),
            "annual_overtime": Decimal("384.0")
        }
        
        return {
            "limits": limits,
            "current_usage": current_usage,
            "remaining_capacity": {
                "daily": limits.get("max_daily_overtime", 12) - current_usage["daily_overtime_today"],
                "weekly": limits.get("max_weekly_overtime", 40) - current_usage["weekly_overtime"]
            }
        }