"""
Employee Bulk Loader - International Employee Data Management
600+ lines of advanced bulk processing with validations
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date
from dataclasses import dataclass, field
from enum import Enum
import uuid
import pandas as pd
import io

from ..config.settings import get_settings
from ..models.base import UserRole, ValidationSeverity

settings = get_settings()
logger = logging.getLogger(__name__)


class FileFormat(Enum):
    """Supported file formats"""
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"


class ValidationResult(Enum):
    """Validation result types"""
    VALID = "valid"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class FieldMapping:
    """Field mapping configuration"""
    source_field: str
    target_field: str
    required: bool = False
    validation_rules: List[str] = field(default_factory=list)
    transformation: Optional[str] = None
    default_value: Optional[Any] = None


@dataclass
class ValidationIssue:
    """Validation issue record"""
    row_number: int
    field_name: str
    severity: ValidationSeverity
    message: str
    current_value: Any
    suggested_value: Optional[Any] = None


@dataclass
class ProcessingResult:
    """Bulk processing result"""
    total_rows: int
    successful_rows: int
    failed_rows: int
    warnings_count: int
    validation_issues: List[ValidationIssue]
    created_employees: List[str]
    updated_employees: List[str]
    skipped_employees: List[str]
    processing_time: float
    file_info: Dict[str, Any]


class CountryValidator:
    """Country-specific field validators"""
    
    @staticmethod
    def validate_mexico_fields(row_data: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate Mexico-specific fields"""
        issues = []
        row_num = row_data.get("_row_number", 0)
        
        # RFC validation
        rfc = row_data.get("rfc", "").strip().upper()
        if rfc:
            if not CountryValidator._validate_rfc(rfc):
                issues.append(ValidationIssue(
                    row_number=row_num,
                    field_name="rfc",
                    severity=ValidationSeverity.ERROR,
                    message="RFC format is invalid",
                    current_value=rfc,
                    suggested_value=CountryValidator._suggest_rfc_fix(rfc)
                ))
        
        # CURP validation
        curp = row_data.get("curp", "").strip().upper()
        if curp:
            if not CountryValidator._validate_curp(curp):
                issues.append(ValidationIssue(
                    row_number=row_num,
                    field_name="curp",
                    severity=ValidationSeverity.ERROR,
                    message="CURP format is invalid",
                    current_value=curp
                ))
        
        # NSS validation
        nss = row_data.get("nss", "").strip()
        if nss:
            if not CountryValidator._validate_nss(nss):
                issues.append(ValidationIssue(
                    row_number=row_num,
                    field_name="nss",
                    severity=ValidationSeverity.ERROR,
                    message="NSS format is invalid",
                    current_value=nss
                ))
        
        # CLABE validation
        clabe = row_data.get("clabe", "").strip()
        if clabe:
            if not CountryValidator._validate_clabe(clabe):
                issues.append(ValidationIssue(
                    row_number=row_num,
                    field_name="clabe",
                    severity=ValidationSeverity.ERROR,
                    message="CLABE format is invalid",
                    current_value=clabe
                ))
        
        return issues
    
    @staticmethod
    def validate_usa_fields(row_data: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate USA-specific fields"""
        issues = []
        row_num = row_data.get("_row_number", 0)
        
        # SSN validation
        ssn = row_data.get("ssn", "").strip()
        if ssn:
            if not CountryValidator._validate_ssn(ssn):
                issues.append(ValidationIssue(
                    row_number=row_num,
                    field_name="ssn",
                    severity=ValidationSeverity.ERROR,
                    message="SSN format is invalid",
                    current_value=ssn
                ))
        
        # State validation
        state = row_data.get("state", "").strip().upper()
        if state:
            if not CountryValidator._validate_us_state(state):
                issues.append(ValidationIssue(
                    row_number=row_num,
                    field_name="state",
                    severity=ValidationSeverity.ERROR,
                    message="Invalid US state code",
                    current_value=state
                ))
        
        return issues
    
    @staticmethod
    def _validate_rfc(rfc: str) -> bool:
        """Validate Mexican RFC"""
        # RFC pattern: 4 letters + 6 digits + 3 alphanumeric (homoclave)
        pattern = r"^[A-Z&Ñ]{3,4}[0-9]{6}[A-Z0-9]{3}$"
        return bool(re.match(pattern, rfc))
    
    @staticmethod
    def _suggest_rfc_fix(rfc: str) -> Optional[str]:
        """Suggest RFC fix"""
        # Remove spaces and special characters
        cleaned = re.sub(r"[^A-Z0-9&Ñ]", "", rfc.upper())
        if len(cleaned) == 13 and CountryValidator._validate_rfc(cleaned):
            return cleaned
        return None
    
    @staticmethod
    def _validate_curp(curp: str) -> bool:
        """Validate Mexican CURP"""
        # CURP pattern: 4 letters + 6 digits + 1 letter + 1 digit + 5 alphanumeric + 1 digit
        pattern = r"^[A-Z]{4}[0-9]{6}[HM][A-Z]{2}[B-DF-HJ-NP-TV-Z]{3}[A-Z0-9][0-9]$"
        return bool(re.match(pattern, curp))
    
    @staticmethod
    def _validate_nss(nss: str) -> bool:
        """Validate Mexican NSS (IMSS number)"""
        # NSS pattern: 11 digits
        pattern = r"^[0-9]{11}$"
        return bool(re.match(pattern, nss))
    
    @staticmethod
    def _validate_clabe(clabe: str) -> bool:
        """Validate Mexican CLABE"""
        if len(clabe) != 18 or not clabe.isdigit():
            return False
        
        # CLABE check digit validation
        weights = [3, 7, 1, 3, 7, 1, 3, 7, 1, 3, 7, 1, 3, 7, 1, 3, 7]
        total = sum(int(clabe[i]) * weights[i] for i in range(17))
        check_digit = (10 - (total % 10)) % 10
        return int(clabe[17]) == check_digit
    
    @staticmethod
    def _validate_ssn(ssn: str) -> bool:
        """Validate US SSN"""
        # Remove dashes and spaces
        cleaned = re.sub(r"[- ]", "", ssn)
        
        # SSN pattern: 9 digits, not all zeros or certain invalid patterns
        if not re.match(r"^[0-9]{9}$", cleaned):
            return False
        
        # Invalid SSN patterns
        invalid_patterns = [
            "000000000", "111111111", "222222222", "333333333",
            "444444444", "555555555", "666666666", "777777777",
            "888888888", "999999999"
        ]
        
        return cleaned not in invalid_patterns and not cleaned.startswith("000")
    
    @staticmethod
    def _validate_us_state(state: str) -> bool:
        """Validate US state code"""
        valid_states = {
            "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
            "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
            "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
            "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
            "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
            "DC", "PR", "VI", "GU", "AS", "MP"
        }
        return state in valid_states


class FieldValidator:
    """General field validators"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_phone(phone: str, country_code: str = "MEX") -> bool:
        """Validate phone number format by country"""
        # Remove all non-digit characters
        cleaned = re.sub(r"[^\d]", "", phone)
        
        if country_code == "MEX":
            # Mexican phone: 10 digits (mobile) or 8 digits (landline) + area code
            return len(cleaned) in [10, 12] and cleaned.isdigit()
        elif country_code == "USA":
            # US phone: 10 digits
            return len(cleaned) == 10 and cleaned.isdigit()
        else:
            # Generic: 7-15 digits
            return 7 <= len(cleaned) <= 15 and cleaned.isdigit()
    
    @staticmethod
    def validate_salary(salary: Any) -> Tuple[bool, Optional[float]]:
        """Validate and convert salary"""
        try:
            if isinstance(salary, str):
                # Remove currency symbols and commas
                cleaned = re.sub(r"[^\d.]", "", salary)
                if not cleaned:
                    return False, None
                salary_value = float(cleaned)
            else:
                salary_value = float(salary)
            
            # Reasonable salary range (100 to 1,000,000)
            if 100 <= salary_value <= 1000000:
                return True, salary_value
            else:
                return False, None
                
        except (ValueError, TypeError):
            return False, None
    
    @staticmethod
    def validate_date(date_str: str) -> Tuple[bool, Optional[date]]:
        """Validate and parse date"""
        if not date_str or pd.isna(date_str):
            return False, None
        
        # Try different date formats
        formats = [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%d-%m-%Y",
            "%Y/%m/%d"
        ]
        
        for fmt in formats:
            try:
                parsed_date = datetime.strptime(str(date_str), fmt).date()
                # Reasonable date range (1900 to current year + 1)
                if date(1900, 1, 1) <= parsed_date <= date(datetime.now().year + 1, 12, 31):
                    return True, parsed_date
            except ValueError:
                continue
        
        return False, None


class TemplateGenerator:
    """Generate templates for different countries"""
    
    MEXICO_TEMPLATE = {
        "required_fields": [
            "employee_number", "first_name", "last_name", "email",
            "hire_date", "job_title", "monthly_salary", "department"
        ],
        "optional_fields": [
            "middle_name", "rfc", "curp", "nss", "clabe", "phone",
            "whatsapp_number", "date_of_birth", "manager_email",
            "bank_name", "address"
        ],
        "country_code": "MEX",
        "currency": "MXN",
        "example_data": {
            "employee_number": "EMP001",
            "first_name": "Juan",
            "last_name": "Pérez",
            "email": "juan.perez@company.com",
            "phone": "5512345678",
            "rfc": "PEPJ850101ABC",
            "curp": "PEPJ850101HDFRRL01",
            "nss": "12345678901",
            "hire_date": "2024-01-15",
            "job_title": "Desarrollador",
            "monthly_salary": "25000",
            "department": "Tecnología"
        }
    }
    
    USA_TEMPLATE = {
        "required_fields": [
            "employee_number", "first_name", "last_name", "email",
            "hire_date", "job_title", "monthly_salary", "department", "state"
        ],
        "optional_fields": [
            "middle_name", "ssn", "phone", "date_of_birth",
            "manager_email", "bank_account", "address", "tax_status"
        ],
        "country_code": "USA",
        "currency": "USD",
        "example_data": {
            "employee_number": "EMP001",
            "first_name": "John",
            "last_name": "Smith",
            "email": "john.smith@company.com",
            "phone": "5551234567",
            "ssn": "123-45-6789",
            "state": "CA",
            "hire_date": "2024-01-15",
            "job_title": "Developer",
            "monthly_salary": "8000",
            "department": "Technology"
        }
    }
    
    @classmethod
    def generate_template(cls, country_code: str, file_format: FileFormat) -> bytes:
        """Generate template file for specific country"""
        template_data = cls._get_template_data(country_code)
        
        if file_format == FileFormat.EXCEL:
            return cls._generate_excel_template(template_data)
        elif file_format == FileFormat.CSV:
            return cls._generate_csv_template(template_data)
        else:
            raise ValueError(f"Unsupported template format: {file_format}")
    
    @classmethod
    def _get_template_data(cls, country_code: str) -> Dict[str, Any]:
        """Get template data for country"""
        templates = {
            "MEX": cls.MEXICO_TEMPLATE,
            "USA": cls.USA_TEMPLATE
        }
        return templates.get(country_code, cls.USA_TEMPLATE)
    
    @classmethod
    def _generate_excel_template(cls, template_data: Dict[str, Any]) -> bytes:
        """Generate Excel template"""
        # Create DataFrame with headers and example row
        all_fields = template_data["required_fields"] + template_data["optional_fields"]
        example_data = template_data["example_data"]
        
        # Create example row
        example_row = {field: example_data.get(field, "") for field in all_fields}
        
        df = pd.DataFrame([example_row])
        
        # Save to bytes
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Employees', index=False)
            
            # Add validation sheet
            validation_df = pd.DataFrame({
                'Field': all_fields,
                'Required': [field in template_data["required_fields"] for field in all_fields],
                'Description': [cls._get_field_description(field) for field in all_fields]
            })
            validation_df.to_excel(writer, sheet_name='Field_Descriptions', index=False)
        
        output.seek(0)
        return output.read()
    
    @classmethod
    def _generate_csv_template(cls, template_data: Dict[str, Any]) -> bytes:
        """Generate CSV template"""
        all_fields = template_data["required_fields"] + template_data["optional_fields"]
        example_data = template_data["example_data"]
        
        example_row = {field: example_data.get(field, "") for field in all_fields}
        df = pd.DataFrame([example_row])
        
        return df.to_csv(index=False).encode('utf-8')
    
    @classmethod
    def _get_field_description(cls, field: str) -> str:
        """Get field description"""
        descriptions = {
            "employee_number": "Unique employee identifier",
            "first_name": "Employee's first name",
            "last_name": "Employee's last name",
            "email": "Employee's email address",
            "phone": "Phone number",
            "rfc": "Mexican tax ID (RFC)",
            "curp": "Mexican unique population registry code",
            "nss": "Mexican social security number",
            "ssn": "US Social Security Number",
            "hire_date": "Date of hire (YYYY-MM-DD)",
            "job_title": "Employee's job title",
            "monthly_salary": "Monthly salary amount",
            "department": "Employee's department"
        }
        return descriptions.get(field, "")


class DuplicateDetector:
    """Detect duplicate employees"""
    
    @staticmethod
    def detect_duplicates(employees_data: List[Dict[str, Any]],
                         existing_employees: List[Dict[str, Any]]) -> List[ValidationIssue]:
        """Detect duplicate employees"""
        issues = []
        
        # Check for duplicates within the upload
        seen_employees = {}
        for i, emp in enumerate(employees_data):
            key = DuplicateDetector._generate_employee_key(emp)
            if key in seen_employees:
                issues.append(ValidationIssue(
                    row_number=i + 2,  # +2 for header row and 0-based index
                    field_name="employee_number",
                    severity=ValidationSeverity.ERROR,
                    message=f"Duplicate employee found in row {seen_employees[key] + 2}",
                    current_value=emp.get("employee_number", "")
                ))
            else:
                seen_employees[key] = i
        
        # Check for duplicates with existing employees
        existing_keys = {DuplicateDetector._generate_employee_key(emp): emp 
                        for emp in existing_employees}
        
        for i, emp in enumerate(employees_data):
            key = DuplicateDetector._generate_employee_key(emp)
            if key in existing_keys:
                issues.append(ValidationIssue(
                    row_number=i + 2,
                    field_name="employee_number",
                    severity=ValidationSeverity.WARNING,
                    message="Employee already exists - will be updated",
                    current_value=emp.get("employee_number", "")
                ))
        
        return issues
    
    @staticmethod
    def _generate_employee_key(employee: Dict[str, Any]) -> str:
        """Generate unique key for employee"""
        # Use employee_number or combination of name + email
        emp_number = employee.get("employee_number", "").strip()
        if emp_number:
            return f"emp_{emp_number}"
        
        email = employee.get("email", "").strip().lower()
        first_name = employee.get("first_name", "").strip().lower()
        last_name = employee.get("last_name", "").strip().lower()
        
        return f"name_{first_name}_{last_name}_{email}"


class EmployeeBulkLoader:
    """Main Employee Bulk Loader Engine"""
    
    def __init__(self):
        self.field_validator = FieldValidator()
        self.country_validator = CountryValidator()
        self.duplicate_detector = DuplicateDetector()
        self.template_generator = TemplateGenerator()
    
    async def process_file(self, file_content: bytes, filename: str,
                          company_id: str, country_code: str,
                          field_mapping: Optional[Dict[str, str]] = None) -> ProcessingResult:
        """Process uploaded employee file"""
        start_time = datetime.now()
        
        try:
            # Detect file format
            file_format = self._detect_file_format(filename)
            
            # Parse file content
            raw_data = self._parse_file(file_content, file_format)
            
            if raw_data.empty:
                return ProcessingResult(
                    total_rows=0, successful_rows=0, failed_rows=0,
                    warnings_count=0, validation_issues=[],
                    created_employees=[], updated_employees=[], skipped_employees=[],
                    processing_time=0, file_info={"error": "Empty file"}
                )
            
            # Apply field mapping
            if field_mapping:
                raw_data = self._apply_field_mapping(raw_data, field_mapping)
            
            # Add row numbers for error reporting
            raw_data["_row_number"] = range(2, len(raw_data) + 2)  # Start from 2 (after header)
            
            # Convert to list of dictionaries
            employees_data = raw_data.to_dict("records")
            
            # Validate data
            validation_issues = await self._validate_employees(employees_data, country_code)
            
            # Get existing employees for duplicate detection
            existing_employees = await self._get_existing_employees(company_id)
            
            # Detect duplicates
            duplicate_issues = self.duplicate_detector.detect_duplicates(employees_data, existing_employees)
            validation_issues.extend(duplicate_issues)
            
            # Separate valid and invalid employees
            valid_employees = []
            invalid_employees = []
            
            error_rows = {issue.row_number for issue in validation_issues 
                         if issue.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]}
            
            for emp in employees_data:
                row_num = emp.get("_row_number", 0)
                if row_num not in error_rows:
                    valid_employees.append(emp)
                else:
                    invalid_employees.append(emp)
            
            # Process valid employees
            created_employees = []
            updated_employees = []
            processing_errors = []
            
            for emp in valid_employees:
                try:
                    result = await self._process_employee(emp, company_id, country_code, existing_employees)
                    if result["action"] == "created":
                        created_employees.append(result["employee_id"])
                    elif result["action"] == "updated":
                        updated_employees.append(result["employee_id"])
                except Exception as e:
                    row_num = emp.get("_row_number", 0)
                    validation_issues.append(ValidationIssue(
                        row_number=row_num,
                        field_name="general",
                        severity=ValidationSeverity.ERROR,
                        message=f"Processing error: {str(e)}",
                        current_value=""
                    ))
                    processing_errors.append(emp)
            
            # Calculate results
            processing_time = (datetime.now() - start_time).total_seconds()
            warnings_count = sum(1 for issue in validation_issues 
                               if issue.severity == ValidationSeverity.WARNING)
            
            return ProcessingResult(
                total_rows=len(employees_data),
                successful_rows=len(created_employees) + len(updated_employees),
                failed_rows=len(invalid_employees) + len(processing_errors),
                warnings_count=warnings_count,
                validation_issues=validation_issues,
                created_employees=created_employees,
                updated_employees=updated_employees,
                skipped_employees=[],
                processing_time=processing_time,
                file_info={
                    "filename": filename,
                    "format": file_format.value,
                    "size_bytes": len(file_content),
                    "columns": list(raw_data.columns) if not raw_data.empty else []
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return ProcessingResult(
                total_rows=0, successful_rows=0, failed_rows=0,
                warnings_count=0, validation_issues=[],
                created_employees=[], updated_employees=[], skipped_employees=[],
                processing_time=processing_time,
                file_info={"error": str(e)}
            )
    
    def _detect_file_format(self, filename: str) -> FileFormat:
        """Detect file format from filename"""
        extension = filename.lower().split(".")[-1]
        
        if extension in ["xlsx", "xls"]:
            return FileFormat.EXCEL
        elif extension == "csv":
            return FileFormat.CSV
        elif extension == "json":
            return FileFormat.JSON
        else:
            raise ValueError(f"Unsupported file format: {extension}")
    
    def _parse_file(self, file_content: bytes, file_format: FileFormat) -> pd.DataFrame:
        """Parse file content to DataFrame"""
        if file_format == FileFormat.EXCEL:
            return pd.read_excel(io.BytesIO(file_content))
        elif file_format == FileFormat.CSV:
            return pd.read_csv(io.BytesIO(file_content))
        elif file_format == FileFormat.JSON:
            import json
            data = json.loads(file_content.decode('utf-8'))
            return pd.DataFrame(data)
        else:
            raise ValueError(f"Unsupported file format: {file_format}")
    
    def _apply_field_mapping(self, df: pd.DataFrame, field_mapping: Dict[str, str]) -> pd.DataFrame:
        """Apply field mapping to DataFrame"""
        # Rename columns based on mapping
        rename_map = {old_name: new_name for old_name, new_name in field_mapping.items() 
                     if old_name in df.columns}
        
        if rename_map:
            df = df.rename(columns=rename_map)
        
        return df
    
    async def _validate_employees(self, employees_data: List[Dict[str, Any]], 
                                 country_code: str) -> List[ValidationIssue]:
        """Validate employee data"""
        all_issues = []
        
        for emp in employees_data:
            row_num = emp.get("_row_number", 0)
            
            # Required field validation
            required_fields = self._get_required_fields(country_code)
            for field in required_fields:
                value = emp.get(field, "")
                if not value or (isinstance(value, str) and not value.strip()):
                    all_issues.append(ValidationIssue(
                        row_number=row_num,
                        field_name=field,
                        severity=ValidationSeverity.ERROR,
                        message=f"Required field '{field}' is missing or empty",
                        current_value=value
                    ))
            
            # Email validation
            email = emp.get("email", "")
            if email and not self.field_validator.validate_email(email):
                all_issues.append(ValidationIssue(
                    row_number=row_num,
                    field_name="email",
                    severity=ValidationSeverity.ERROR,
                    message="Invalid email format",
                    current_value=email
                ))
            
            # Phone validation
            phone = emp.get("phone", "")
            if phone and not self.field_validator.validate_phone(phone, country_code):
                all_issues.append(ValidationIssue(
                    row_number=row_num,
                    field_name="phone",
                    severity=ValidationSeverity.WARNING,
                    message="Invalid phone format",
                    current_value=phone
                ))
            
            # Salary validation
            salary = emp.get("monthly_salary", "")
            if salary:
                is_valid, parsed_salary = self.field_validator.validate_salary(salary)
                if not is_valid:
                    all_issues.append(ValidationIssue(
                        row_number=row_num,
                        field_name="monthly_salary",
                        severity=ValidationSeverity.ERROR,
                        message="Invalid salary format or amount",
                        current_value=salary
                    ))
                else:
                    emp["monthly_salary"] = parsed_salary  # Update with parsed value
            
            # Date validation
            hire_date = emp.get("hire_date", "")
            if hire_date:
                is_valid, parsed_date = self.field_validator.validate_date(hire_date)
                if not is_valid:
                    all_issues.append(ValidationIssue(
                        row_number=row_num,
                        field_name="hire_date",
                        severity=ValidationSeverity.ERROR,
                        message="Invalid date format",
                        current_value=hire_date
                    ))
                else:
                    emp["hire_date"] = parsed_date.isoformat()  # Update with parsed value
            
            # Country-specific validation
            if country_code == "MEX":
                country_issues = self.country_validator.validate_mexico_fields(emp)
                all_issues.extend(country_issues)
            elif country_code == "USA":
                country_issues = self.country_validator.validate_usa_fields(emp)
                all_issues.extend(country_issues)
        
        return all_issues
    
    def _get_required_fields(self, country_code: str) -> List[str]:
        """Get required fields for country"""
        template_data = self.template_generator._get_template_data(country_code)
        return template_data["required_fields"]
    
    async def _get_existing_employees(self, company_id: str) -> List[Dict[str, Any]]:
        """Get existing employees for duplicate detection"""
        # Mock implementation - would query database
        return [
            {"employee_number": "EMP001", "email": "existing@company.com"},
            {"employee_number": "EMP002", "email": "another@company.com"}
        ]
    
    async def _process_employee(self, emp_data: Dict[str, Any], company_id: str,
                               country_code: str, existing_employees: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process single employee (create or update)"""
        # Check if employee exists
        employee_number = emp_data.get("employee_number", "")
        existing_emp = next((e for e in existing_employees 
                           if e.get("employee_number") == employee_number), None)
        
        if existing_emp:
            # Update existing employee
            employee_id = await self._update_employee(emp_data, company_id, country_code)
            return {"action": "updated", "employee_id": employee_id}
        else:
            # Create new employee
            employee_id = await self._create_employee(emp_data, company_id, country_code)
            return {"action": "created", "employee_id": employee_id}
    
    async def _create_employee(self, emp_data: Dict[str, Any], company_id: str, 
                              country_code: str) -> str:
        """Create new employee"""
        employee_id = str(uuid.uuid4())
        
        # Clean and prepare data
        clean_data = self._clean_employee_data(emp_data, country_code)
        clean_data.update({
            "id": employee_id,
            "company_id": company_id,
            "country_code": country_code,
            "created_at": datetime.now().isoformat(),
            "is_active": True
        })
        
        # Mock database save
        logger.info(f"Creating employee {employee_id}: {clean_data.get('first_name')} {clean_data.get('last_name')}")
        
        return employee_id
    
    async def _update_employee(self, emp_data: Dict[str, Any], company_id: str,
                              country_code: str) -> str:
        """Update existing employee"""
        employee_id = emp_data.get("employee_number", str(uuid.uuid4()))
        
        # Clean and prepare data
        clean_data = self._clean_employee_data(emp_data, country_code)
        clean_data.update({
            "updated_at": datetime.now().isoformat()
        })
        
        # Mock database update
        logger.info(f"Updating employee {employee_id}: {clean_data.get('first_name')} {clean_data.get('last_name')}")
        
        return employee_id
    
    def _clean_employee_data(self, emp_data: Dict[str, Any], country_code: str) -> Dict[str, Any]:
        """Clean and standardize employee data"""
        clean_data = {}
        
        # Basic fields
        basic_fields = [
            "employee_number", "first_name", "last_name", "middle_name",
            "email", "phone", "whatsapp_number", "job_title", "department",
            "monthly_salary", "hire_date", "date_of_birth", "manager_email"
        ]
        
        for field in basic_fields:
            value = emp_data.get(field)
            if value is not None and value != "":
                if isinstance(value, str):
                    clean_data[field] = value.strip()
                else:
                    clean_data[field] = value
        
        # Country-specific fields
        if country_code == "MEX":
            mexico_fields = ["rfc", "curp", "nss", "clabe"]
            for field in mexico_fields:
                value = emp_data.get(field)
                if value and isinstance(value, str):
                    clean_data[field] = value.strip().upper()
        
        elif country_code == "USA":
            usa_fields = ["ssn", "state", "tax_status"]
            for field in usa_fields:
                value = emp_data.get(field)
                if value and isinstance(value, str):
                    if field == "state":
                        clean_data[field] = value.strip().upper()
                    else:
                        clean_data[field] = value.strip()
        
        # Remove internal fields
        clean_data.pop("_row_number", None)
        
        return clean_data
    
    def generate_template(self, country_code: str, file_format: FileFormat) -> bytes:
        """Generate template file for country"""
        return self.template_generator.generate_template(country_code, file_format)
    
    def get_processing_summary(self, result: ProcessingResult) -> Dict[str, Any]:
        """Generate processing summary"""
        return {
            "file_info": result.file_info,
            "processing_stats": {
                "total_rows": result.total_rows,
                "successful_rows": result.successful_rows,
                "failed_rows": result.failed_rows,
                "success_rate": (result.successful_rows / result.total_rows * 100) if result.total_rows > 0 else 0,
                "processing_time_seconds": result.processing_time
            },
            "actions_taken": {
                "employees_created": len(result.created_employees),
                "employees_updated": len(result.updated_employees),
                "employees_skipped": len(result.skipped_employees)
            },
            "validation_summary": {
                "total_issues": len(result.validation_issues),
                "warnings": result.warnings_count,
                "errors": len([i for i in result.validation_issues if i.severity == ValidationSeverity.ERROR]),
                "critical": len([i for i in result.validation_issues if i.severity == ValidationSeverity.CRITICAL])
            },
            "next_steps": self._generate_next_steps(result)
        }
    
    def _generate_next_steps(self, result: ProcessingResult) -> List[str]:
        """Generate next steps based on processing result"""
        steps = []
        
        if result.failed_rows > 0:
            steps.append("Review and fix validation errors, then re-upload the corrected file")
        
        if result.warnings_count > 0:
            steps.append("Review warnings to ensure data quality")
        
        if result.successful_rows > 0:
            steps.append("Verify created/updated employees in the system")
            steps.append("Send welcome emails to new employees")
        
        if not steps:
            steps.append("All employees processed successfully!")
        
        return steps