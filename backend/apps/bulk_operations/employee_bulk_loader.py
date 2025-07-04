"""
Employee Bulk Loader huntRED® v2
=================================

Funcionalidades:
- Carga masiva de plantilla laboral
- Templates dinámicos por país/región
- Validaciones automáticas (RFC, CURP, NSS)
- Detección de duplicados inteligente
- Importación desde Excel/CSV
- Mapeo automático de campos
- Procesamiento asíncrono
- Reportes de errores detallados
- Integración automática con nómina
"""

import asyncio
import uuid
import pandas as pd
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
import re
import io
import base64

logger = logging.getLogger(__name__)

class LoadStatus(Enum):
    """Estados de carga masiva."""
    PENDING = "pending"
    PROCESSING = "processing"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"

class ValidationSeverity(Enum):
    """Severidad de validación."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class FieldType(Enum):
    """Tipos de campo para validación."""
    TEXT = "text"
    EMAIL = "email"
    PHONE = "phone"
    DATE = "date"
    NUMBER = "number"
    CURRENCY = "currency"
    RFC = "rfc"
    CURP = "curp"
    NSS = "nss"
    CLABE = "clabe"

@dataclass
class FieldMapping:
    """Mapeo de campo en template."""
    field_name: str
    display_name: str
    field_type: FieldType
    required: bool = True
    validation_pattern: Optional[str] = None
    default_value: Optional[str] = None
    description: str = ""
    country_specific: bool = False

@dataclass
class CountryTemplate:
    """Template de empleado por país."""
    country_code: str
    country_name: str
    
    # Campos obligatorios
    required_fields: List[FieldMapping] = field(default_factory=list)
    
    # Campos opcionales
    optional_fields: List[FieldMapping] = field(default_factory=list)
    
    # Validaciones específicas del país
    validations: Dict[str, Any] = field(default_factory=dict)
    
    # Configuración regional
    currency: str = "USD"
    date_format: str = "%Y-%m-%d"
    number_format: str = "en_US"
    
    # Metadatos
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class ValidationResult:
    """Resultado de validación de campo."""
    field_name: str
    severity: ValidationSeverity
    message: str
    value: Optional[str] = None
    suggested_value: Optional[str] = None
    row_number: Optional[int] = None

@dataclass
class EmployeeRecord:
    """Registro de empleado procesado."""
    row_number: int
    raw_data: Dict[str, Any]
    processed_data: Dict[str, Any] = field(default_factory=dict)
    validations: List[ValidationResult] = field(default_factory=list)
    is_valid: bool = False
    is_duplicate: bool = False
    duplicate_of: Optional[str] = None
    employee_id: Optional[str] = None

@dataclass
class BulkLoadJob:
    """Trabajo de carga masiva."""
    job_id: str
    client_id: str
    country_code: str
    
    # Archivo
    filename: str
    file_content: str  # Base64 encoded
    file_type: str = "excel"  # excel, csv
    
    # Configuración
    template_used: str = ""
    field_mappings: Dict[str, str] = field(default_factory=dict)
    skip_duplicates: bool = True
    update_existing: bool = False
    
    # Estado
    status: LoadStatus = LoadStatus.PENDING
    
    # Progreso
    total_rows: int = 0
    processed_rows: int = 0
    valid_rows: int = 0
    invalid_rows: int = 0
    duplicate_rows: int = 0
    
    # Resultados
    employee_records: List[EmployeeRecord] = field(default_factory=list)
    created_employees: List[str] = field(default_factory=list)
    error_summary: Dict[str, int] = field(default_factory=dict)
    
    # Metadatos
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: str = ""

class EmployeeBulkLoader:
    """Sistema principal de carga masiva de empleados."""
    
    def __init__(self):
        self.country_templates: Dict[str, CountryTemplate] = {}
        self.bulk_jobs: Dict[str, BulkLoadJob] = {}
        self.duplicate_detection_cache: Dict[str, List[str]] = {}
        
        # Importar sistemas relacionados
        from ..payroll.payroll_engine import PayrollEngine
        from ..multichannel.unified_messaging_engine import UnifiedMessagingEngine
        
        self.payroll_engine = PayrollEngine()
        self.messaging_engine = UnifiedMessagingEngine()
        
        # Setup inicial
        self._setup_country_templates()
        self._setup_validation_patterns()
    
    def _setup_country_templates(self):
        """Configura templates por país."""
        
        # Template México
        mexico_fields = [
            # Campos obligatorios
            FieldMapping("first_name", "Nombre(s)", FieldType.TEXT, True),
            FieldMapping("last_name", "Apellidos", FieldType.TEXT, True),
            FieldMapping("rfc", "RFC", FieldType.RFC, True, r"^[A-Z&Ñ]{3,4}[0-9]{6}[A-Z0-9]{3}$"),
            FieldMapping("curp", "CURP", FieldType.CURP, True, r"^[A-Z]{1}[AEIOUX]{1}[A-Z]{2}[0-9]{2}(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])[HM]{1}[A-Z]{2}[BCDFGHJKLMNPQRSTVWXYZ]{3}[0-9A-Z]{1}$"),
            FieldMapping("nss", "NSS", FieldType.NSS, True, r"^[0-9]{11}$"),
            FieldMapping("employee_number", "No. Empleado", FieldType.TEXT, True),
            FieldMapping("hire_date", "Fecha de Ingreso", FieldType.DATE, True),
            FieldMapping("job_title", "Puesto", FieldType.TEXT, True),
            FieldMapping("department", "Departamento", FieldType.TEXT, True),
            FieldMapping("base_salary", "Salario Base", FieldType.CURRENCY, True),
            FieldMapping("payment_frequency", "Frecuencia de Pago", FieldType.TEXT, True, default_value="monthly"),
        ]
        
        mexico_optional = [
            FieldMapping("middle_name", "Segundo Nombre", FieldType.TEXT, False),
            FieldMapping("email", "Email", FieldType.EMAIL, False),
            FieldMapping("phone", "Teléfono", FieldType.PHONE, False),
            FieldMapping("address", "Dirección", FieldType.TEXT, False),
            FieldMapping("zip_code", "Código Postal", FieldType.TEXT, False),
            FieldMapping("bank_name", "Banco", FieldType.TEXT, False),
            FieldMapping("bank_account", "Cuenta Bancaria", FieldType.TEXT, False),
            FieldMapping("bank_clabe", "CLABE", FieldType.CLABE, False, r"^[0-9]{18}$"),
            FieldMapping("imss_salary", "Salario IMSS", FieldType.CURRENCY, False),
            FieldMapping("infonavit_discount", "Descuento INFONAVIT", FieldType.NUMBER, False),
        ]
        
        mexico_template = CountryTemplate(
            country_code="MX",
            country_name="México",
            required_fields=mexico_fields,
            optional_fields=mexico_optional,
            currency="MXN",
            date_format="%d/%m/%Y",
            validations={
                "min_salary": 5000,  # Salario mínimo mensual
                "max_salary": 500000,  # Salario máximo mensual
                "valid_frequencies": ["weekly", "biweekly", "monthly"]
            }
        )
        
        # Template Estados Unidos
        usa_fields = [
            FieldMapping("first_name", "First Name", FieldType.TEXT, True),
            FieldMapping("last_name", "Last Name", FieldType.TEXT, True),
            FieldMapping("ssn", "SSN", FieldType.TEXT, True, r"^[0-9]{3}-[0-9]{2}-[0-9]{4}$"),
            FieldMapping("employee_number", "Employee ID", FieldType.TEXT, True),
            FieldMapping("hire_date", "Hire Date", FieldType.DATE, True),
            FieldMapping("job_title", "Job Title", FieldType.TEXT, True),
            FieldMapping("department", "Department", FieldType.TEXT, True),
            FieldMapping("base_salary", "Annual Salary", FieldType.CURRENCY, True),
            FieldMapping("payment_frequency", "Pay Frequency", FieldType.TEXT, True, default_value="biweekly"),
            FieldMapping("tax_status", "Tax Filing Status", FieldType.TEXT, True),
        ]
        
        usa_template = CountryTemplate(
            country_code="US",
            country_name="United States",
            required_fields=usa_fields,
            optional_fields=[
                FieldMapping("middle_name", "Middle Name", FieldType.TEXT, False),
                FieldMapping("email", "Email", FieldType.EMAIL, False),
                FieldMapping("phone", "Phone", FieldType.PHONE, False),
            ],
            currency="USD",
            date_format="%m/%d/%Y",
            validations={
                "min_salary": 15000,  # Salario mínimo anual
                "max_salary": 1000000,
                "valid_frequencies": ["weekly", "biweekly", "monthly"]
            }
        )
        
        self.country_templates["MX"] = mexico_template
        self.country_templates["US"] = usa_template
    
    def _setup_validation_patterns(self):
        """Configura patrones de validación."""
        
        self.validation_patterns = {
            FieldType.EMAIL: r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
            FieldType.PHONE: r"^(\+?[0-9]{1,3})?[0-9]{10,14}$",
            FieldType.RFC: r"^[A-Z&Ñ]{3,4}[0-9]{6}[A-Z0-9]{3}$",
            FieldType.CURP: r"^[A-Z]{1}[AEIOUX]{1}[A-Z]{2}[0-9]{2}(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])[HM]{1}[A-Z]{2}[BCDFGHJKLMNPQRSTVWXYZ]{3}[0-9A-Z]{1}$",
            FieldType.NSS: r"^[0-9]{11}$",
            FieldType.CLABE: r"^[0-9]{18}$"
        }
    
    async def create_bulk_load_job(self, job_data: Dict[str, Any]) -> str:
        """Crea un trabajo de carga masiva."""
        
        job_id = str(uuid.uuid4())
        
        job = BulkLoadJob(
            job_id=job_id,
            client_id=job_data["client_id"],
            country_code=job_data["country_code"],
            filename=job_data["filename"],
            file_content=job_data["file_content"],
            file_type=job_data.get("file_type", "excel"),
            skip_duplicates=job_data.get("skip_duplicates", True),
            update_existing=job_data.get("update_existing", False),
            created_by=job_data.get("created_by", "system")
        )
        
        self.bulk_jobs[job_id] = job
        
        # Iniciar procesamiento asíncrono
        asyncio.create_task(self._process_bulk_load_job(job_id))
        
        logger.info(f"Bulk load job created: {job_id}")
        return job_id
    
    async def _process_bulk_load_job(self, job_id: str):
        """Procesa trabajo de carga masiva."""
        
        job = self.bulk_jobs.get(job_id)
        if not job:
            return
        
        try:
            job.status = LoadStatus.PROCESSING
            job.started_at = datetime.now()
            
            # Paso 1: Leer archivo
            df = await self._read_file(job)
            job.total_rows = len(df)
            
            # Paso 2: Mapear campos automáticamente si no están especificados
            if not job.field_mappings:
                job.field_mappings = await self._auto_map_fields(df.columns.tolist(), job.country_code)
            
            job.status = LoadStatus.VALIDATING
            
            # Paso 3: Procesar cada fila
            for index, row in df.iterrows():
                await self._process_employee_row(job, index + 1, row.to_dict())
                job.processed_rows += 1
            
            # Paso 4: Detectar duplicados
            await self._detect_duplicates(job)
            
            # Paso 5: Crear empleados válidos
            await self._create_employees(job)
            
            # Paso 6: Generar reportes
            await self._generate_reports(job)
            
            job.status = LoadStatus.COMPLETED if job.invalid_rows == 0 else LoadStatus.PARTIAL
            job.completed_at = datetime.now()
            
            logger.info(f"Bulk load job completed: {job_id} - {job.valid_rows}/{job.total_rows} successful")
            
        except Exception as e:
            job.status = LoadStatus.FAILED
            job.completed_at = datetime.now()
            logger.error(f"Bulk load job failed: {job_id} - {e}")
    
    async def _read_file(self, job: BulkLoadJob) -> pd.DataFrame:
        """Lee archivo y retorna DataFrame."""
        
        # Decodificar contenido base64
        file_bytes = base64.b64decode(job.file_content)
        
        if job.file_type.lower() in ["excel", "xlsx", "xls"]:
            return pd.read_excel(io.BytesIO(file_bytes))
        elif job.file_type.lower() == "csv":
            return pd.read_csv(io.BytesIO(file_bytes))
        else:
            raise ValueError(f"Unsupported file type: {job.file_type}")
    
    async def _auto_map_fields(self, columns: List[str], country_code: str) -> Dict[str, str]:
        """Mapea automáticamente campos del archivo con el template."""
        
        template = self.country_templates.get(country_code)
        if not template:
            return {}
        
        # Combinar campos obligatorios y opcionales
        all_fields = template.required_fields + template.optional_fields
        
        mappings = {}
        
        for field in all_fields:
            # Buscar coincidencias exactas o similares
            for col in columns:
                col_lower = col.lower().strip()
                field_lower = field.display_name.lower()
                field_name_lower = field.field_name.lower()
                
                # Coincidencia exacta
                if col_lower == field_lower or col_lower == field_name_lower:
                    mappings[col] = field.field_name
                    break
                
                # Coincidencia parcial
                elif (field_lower in col_lower or col_lower in field_lower or
                      field_name_lower in col_lower or col_lower in field_name_lower):
                    mappings[col] = field.field_name
                    break
        
        return mappings
    
    async def _process_employee_row(self, job: BulkLoadJob, row_number: int, row_data: Dict[str, Any]):
        """Procesa una fila individual de empleado."""
        
        record = EmployeeRecord(
            row_number=row_number,
            raw_data=row_data
        )
        
        template = self.country_templates.get(job.country_code)
        if not template:
            record.validations.append(ValidationResult(
                "country", ValidationSeverity.ERROR, f"Template not found for country: {job.country_code}"
            ))
            job.invalid_rows += 1
            job.employee_records.append(record)
            return
        
        # Mapear campos
        for file_column, template_field in job.field_mappings.items():
            if file_column in row_data and pd.notna(row_data[file_column]):
                record.processed_data[template_field] = str(row_data[file_column]).strip()
        
        # Validar campos obligatorios
        for field in template.required_fields:
            await self._validate_field(record, field, template)
        
        # Validar campos opcionales presentes
        for field in template.optional_fields:
            if field.field_name in record.processed_data:
                await self._validate_field(record, field, template)
        
        # Validaciones específicas del país
        await self._validate_country_specific(record, template)
        
        # Determinar si el registro es válido
        has_critical_errors = any(
            v.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]
            for v in record.validations
        )
        
        record.is_valid = not has_critical_errors
        
        if record.is_valid:
            job.valid_rows += 1
        else:
            job.invalid_rows += 1
        
        job.employee_records.append(record)
    
    async def _validate_field(self, record: EmployeeRecord, field: FieldMapping, template: CountryTemplate):
        """Valida un campo específico."""
        
        value = record.processed_data.get(field.field_name)
        
        # Campo obligatorio faltante
        if field.required and not value:
            record.validations.append(ValidationResult(
                field.field_name, ValidationSeverity.ERROR,
                f"{field.display_name} es obligatorio", row_number=record.row_number
            ))
            return
        
        # Si no hay valor, no validar más
        if not value:
            return
        
        # Validación por tipo de campo
        if field.field_type == FieldType.EMAIL:
            await self._validate_email(record, field, value)
        elif field.field_type == FieldType.PHONE:
            await self._validate_phone(record, field, value)
        elif field.field_type == FieldType.DATE:
            await self._validate_date(record, field, value, template.date_format)
        elif field.field_type == FieldType.CURRENCY:
            await self._validate_currency(record, field, value)
        elif field.field_type == FieldType.RFC:
            await self._validate_rfc(record, field, value)
        elif field.field_type == FieldType.CURP:
            await self._validate_curp(record, field, value)
        elif field.field_type == FieldType.NSS:
            await self._validate_nss(record, field, value)
        elif field.field_type == FieldType.CLABE:
            await self._validate_clabe(record, field, value)
        
        # Validación con patrón personalizado
        if field.validation_pattern and value:
            if not re.match(field.validation_pattern, str(value)):
                record.validations.append(ValidationResult(
                    field.field_name, ValidationSeverity.ERROR,
                    f"{field.display_name} no cumple el formato requerido",
                    value, row_number=record.row_number
                ))
    
    async def _validate_email(self, record: EmployeeRecord, field: FieldMapping, value: str):
        """Valida formato de email."""
        
        pattern = self.validation_patterns[FieldType.EMAIL]
        if not re.match(pattern, value):
            record.validations.append(ValidationResult(
                field.field_name, ValidationSeverity.ERROR,
                f"Email inválido: {value}", value, row_number=record.row_number
            ))
    
    async def _validate_phone(self, record: EmployeeRecord, field: FieldMapping, value: str):
        """Valida formato de teléfono."""
        
        # Limpiar teléfono
        clean_phone = re.sub(r'[^\d+]', '', str(value))
        
        if len(clean_phone) < 10:
            record.validations.append(ValidationResult(
                field.field_name, ValidationSeverity.ERROR,
                f"Teléfono muy corto: {value}", value, clean_phone, record.row_number
            ))
    
    async def _validate_date(self, record: EmployeeRecord, field: FieldMapping, value: str, date_format: str):
        """Valida formato de fecha."""
        
        try:
            parsed_date = datetime.strptime(str(value), date_format).date()
            
            # Validaciones adicionales para fecha de ingreso
            if field.field_name == "hire_date":
                if parsed_date > date.today():
                    record.validations.append(ValidationResult(
                        field.field_name, ValidationSeverity.WARNING,
                        f"Fecha de ingreso en el futuro: {value}", value, row_number=record.row_number
                    ))
                elif parsed_date.year < 1950:
                    record.validations.append(ValidationResult(
                        field.field_name, ValidationSeverity.ERROR,
                        f"Fecha de ingreso muy antigua: {value}", value, row_number=record.row_number
                    ))
            
            # Actualizar valor procesado con formato estándar
            record.processed_data[field.field_name] = parsed_date.isoformat()
            
        except ValueError:
            record.validations.append(ValidationResult(
                field.field_name, ValidationSeverity.ERROR,
                f"Fecha inválida: {value} (formato esperado: {date_format})",
                value, row_number=record.row_number
            ))
    
    async def _validate_currency(self, record: EmployeeRecord, field: FieldMapping, value: str):
        """Valida formato de moneda."""
        
        try:
            # Limpiar valor (quitar comas, símbolos de moneda)
            clean_value = re.sub(r'[^\d.]', '', str(value))
            numeric_value = float(clean_value)
            
            if numeric_value <= 0:
                record.validations.append(ValidationResult(
                    field.field_name, ValidationSeverity.ERROR,
                    f"Salario debe ser mayor a 0: {value}", value, row_number=record.row_number
                ))
            
            # Actualizar valor procesado
            record.processed_data[field.field_name] = str(numeric_value)
            
        except (ValueError, TypeError):
            record.validations.append(ValidationResult(
                field.field_name, ValidationSeverity.ERROR,
                f"Valor monetario inválido: {value}", value, row_number=record.row_number
            ))
    
    async def _validate_rfc(self, record: EmployeeRecord, field: FieldMapping, value: str):
        """Valida RFC mexicano."""
        
        rfc_upper = str(value).upper().strip()
        pattern = self.validation_patterns[FieldType.RFC]
        
        if not re.match(pattern, rfc_upper):
            record.validations.append(ValidationResult(
                field.field_name, ValidationSeverity.ERROR,
                f"RFC inválido: {value}", value, rfc_upper, record.row_number
            ))
        else:
            record.processed_data[field.field_name] = rfc_upper
    
    async def _validate_curp(self, record: EmployeeRecord, field: FieldMapping, value: str):
        """Valida CURP mexicana."""
        
        curp_upper = str(value).upper().strip()
        pattern = self.validation_patterns[FieldType.CURP]
        
        if not re.match(pattern, curp_upper):
            record.validations.append(ValidationResult(
                field.field_name, ValidationSeverity.ERROR,
                f"CURP inválida: {value}", value, curp_upper, record.row_number
            ))
        else:
            record.processed_data[field.field_name] = curp_upper
    
    async def _validate_nss(self, record: EmployeeRecord, field: FieldMapping, value: str):
        """Valida NSS (Número de Seguridad Social)."""
        
        nss_clean = re.sub(r'[^\d]', '', str(value))
        pattern = self.validation_patterns[FieldType.NSS]
        
        if not re.match(pattern, nss_clean):
            record.validations.append(ValidationResult(
                field.field_name, ValidationSeverity.ERROR,
                f"NSS inválido: {value}", value, nss_clean, record.row_number
            ))
        else:
            record.processed_data[field.field_name] = nss_clean
    
    async def _validate_clabe(self, record: EmployeeRecord, field: FieldMapping, value: str):
        """Valida CLABE bancaria."""
        
        clabe_clean = re.sub(r'[^\d]', '', str(value))
        pattern = self.validation_patterns[FieldType.CLABE]
        
        if not re.match(pattern, clabe_clean):
            record.validations.append(ValidationResult(
                field.field_name, ValidationSeverity.ERROR,
                f"CLABE inválida: {value}", value, clabe_clean, record.row_number
            ))
        else:
            record.processed_data[field.field_name] = clabe_clean
    
    async def _validate_country_specific(self, record: EmployeeRecord, template: CountryTemplate):
        """Validaciones específicas del país."""
        
        # Validar rango de salario
        if "base_salary" in record.processed_data:
            try:
                salary = float(record.processed_data["base_salary"])
                min_salary = template.validations.get("min_salary", 0)
                max_salary = template.validations.get("max_salary", float('inf'))
                
                if salary < min_salary:
                    record.validations.append(ValidationResult(
                        "base_salary", ValidationSeverity.WARNING,
                        f"Salario por debajo del mínimo sugerido ({min_salary}): {salary}",
                        str(salary), row_number=record.row_number
                    ))
                elif salary > max_salary:
                    record.validations.append(ValidationResult(
                        "base_salary", ValidationSeverity.WARNING,
                        f"Salario por encima del máximo sugerido ({max_salary}): {salary}",
                        str(salary), row_number=record.row_number
                    ))
            except (ValueError, TypeError):
                pass
        
        # Validar frecuencia de pago
        if "payment_frequency" in record.processed_data:
            frequency = record.processed_data["payment_frequency"].lower()
            valid_frequencies = template.validations.get("valid_frequencies", [])
            
            if valid_frequencies and frequency not in valid_frequencies:
                record.validations.append(ValidationResult(
                    "payment_frequency", ValidationSeverity.ERROR,
                    f"Frecuencia de pago inválida: {frequency}. Válidas: {valid_frequencies}",
                    frequency, row_number=record.row_number
                ))
    
    async def _detect_duplicates(self, job: BulkLoadJob):
        """Detecta empleados duplicados."""
        
        # Crear índices para detección de duplicados
        rfc_index = {}
        email_index = {}
        employee_number_index = {}
        
        for record in job.employee_records:
            if not record.is_valid:
                continue
            
            # Indexar por RFC
            rfc = record.processed_data.get("rfc")
            if rfc:
                if rfc in rfc_index:
                    # Marcar como duplicado
                    record.is_duplicate = True
                    record.duplicate_of = rfc_index[rfc]
                    job.duplicate_rows += 1
                else:
                    rfc_index[rfc] = record.row_number
            
            # Indexar por email
            email = record.processed_data.get("email")
            if email:
                if email in email_index:
                    record.is_duplicate = True
                    record.duplicate_of = f"email_{email_index[email]}"
                    job.duplicate_rows += 1
                else:
                    email_index[email] = record.row_number
            
            # Indexar por número de empleado
            emp_num = record.processed_data.get("employee_number")
            if emp_num:
                if emp_num in employee_number_index:
                    record.is_duplicate = True
                    record.duplicate_of = f"emp_num_{employee_number_index[emp_num]}"
                    job.duplicate_rows += 1
                else:
                    employee_number_index[emp_num] = record.row_number
    
    async def _create_employees(self, job: BulkLoadJob):
        """Crea empleados válidos en el sistema."""
        
        for record in job.employee_records:
            if not record.is_valid:
                continue
            
            if record.is_duplicate and job.skip_duplicates:
                continue
            
            try:
                # Preparar datos para el PayrollEngine
                employee_data = {
                    "client_id": job.client_id,
                    **record.processed_data
                }
                
                # Crear empleado
                employee_id = await self.payroll_engine.create_employee(employee_data)
                record.employee_id = employee_id
                job.created_employees.append(employee_id)
                
                # Registrar en sistema de mensajería si hay datos de contacto
                if record.processed_data.get("email") or record.processed_data.get("phone"):
                    await self._register_employee_contacts(record, job.client_id)
                
            except Exception as e:
                record.validations.append(ValidationResult(
                    "creation", ValidationSeverity.ERROR,
                    f"Error creando empleado: {e}", row_number=record.row_number
                ))
                record.is_valid = False
                job.invalid_rows += 1
                job.valid_rows -= 1
    
    async def _register_employee_contacts(self, record: EmployeeRecord, client_id: str):
        """Registra contactos del empleado en sistema de mensajería."""
        
        if not record.employee_id:
            return
        
        contact_data = {
            "employee_id": record.employee_id,
            "client_id": client_id,
            "first_name": record.processed_data.get("first_name", ""),
            "last_name": record.processed_data.get("last_name", ""),
            "email": record.processed_data.get("email", ""),
            "whatsapp_number": record.processed_data.get("phone"),
            "preferred_channel": "whatsapp"
        }
        
        try:
            unified_id = await self.messaging_engine.register_unified_contact(contact_data)
            logger.info(f"Employee contact registered: {record.employee_id} -> {unified_id}")
        except Exception as e:
            logger.warning(f"Failed to register employee contact: {e}")
    
    async def _generate_reports(self, job: BulkLoadJob):
        """Genera reportes de la carga masiva."""
        
        # Resumen de errores
        error_summary = {}
        for record in job.employee_records:
            for validation in record.validations:
                error_key = f"{validation.field_name}_{validation.severity.value}"
                error_summary[error_key] = error_summary.get(error_key, 0) + 1
        
        job.error_summary = error_summary
        
        logger.info(f"Bulk load report generated for job {job.job_id}")
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Obtiene estado del trabajo de carga masiva."""
        
        job = self.bulk_jobs.get(job_id)
        if not job:
            return {"error": "Job not found"}
        
        progress_percentage = (job.processed_rows / job.total_rows * 100) if job.total_rows > 0 else 0
        
        return {
            "job_id": job_id,
            "status": job.status.value,
            "progress": {
                "total_rows": job.total_rows,
                "processed_rows": job.processed_rows,
                "valid_rows": job.valid_rows,
                "invalid_rows": job.invalid_rows,
                "duplicate_rows": job.duplicate_rows,
                "percentage": round(progress_percentage, 2)
            },
            "results": {
                "created_employees": len(job.created_employees),
                "error_summary": job.error_summary
            },
            "timing": {
                "created_at": job.created_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None
            }
        }
    
    def get_job_details(self, job_id: str) -> Dict[str, Any]:
        """Obtiene detalles completos del trabajo."""
        
        job = self.bulk_jobs.get(job_id)
        if not job:
            return {"error": "Job not found"}
        
        # Agrupar validaciones por tipo
        validations_by_type = {}
        for record in job.employee_records:
            for validation in record.validations:
                severity = validation.severity.value
                if severity not in validations_by_type:
                    validations_by_type[severity] = []
                validations_by_type[severity].append({
                    "row": validation.row_number,
                    "field": validation.field_name,
                    "message": validation.message,
                    "value": validation.value
                })
        
        return {
            **self.get_job_status(job_id),
            "validations": validations_by_type,
            "created_employees": job.created_employees,
            "sample_errors": validations_by_type.get("error", [])[:10]  # Primeros 10 errores
        }
    
    def get_country_template(self, country_code: str) -> Dict[str, Any]:
        """Obtiene template de país para descarga."""
        
        template = self.country_templates.get(country_code)
        if not template:
            return {"error": "Template not found"}
        
        # Generar headers para Excel
        headers = []
        field_descriptions = []
        
        # Campos obligatorios
        for field in template.required_fields:
            headers.append(field.display_name + " *")
            field_descriptions.append(f"{field.display_name}: {field.description or 'Campo obligatorio'}")
        
        # Campos opcionales
        for field in template.optional_fields:
            headers.append(field.display_name)
            field_descriptions.append(f"{field.display_name}: {field.description or 'Campo opcional'}")
        
        return {
            "country_code": country_code,
            "country_name": template.country_name,
            "headers": headers,
            "field_descriptions": field_descriptions,
            "currency": template.currency,
            "date_format": template.date_format,
            "validations": template.validations
        }

# Funciones de utilidad
async def create_employee_bulk_load(client_id: str, country_code: str, 
                                  file_content: str, filename: str) -> str:
    """Función de conveniencia para carga masiva."""
    
    loader = EmployeeBulkLoader()
    
    job_data = {
        "client_id": client_id,
        "country_code": country_code,
        "file_content": file_content,
        "filename": filename,
        "file_type": "excel" if filename.endswith(('.xlsx', '.xls')) else "csv"
    }
    
    return await loader.create_bulk_load_job(job_data)

# Exportaciones
__all__ = [
    'LoadStatus', 'ValidationSeverity', 'FieldType',
    'FieldMapping', 'CountryTemplate', 'ValidationResult', 'EmployeeRecord', 'BulkLoadJob',
    'EmployeeBulkLoader', 'create_employee_bulk_load'
]