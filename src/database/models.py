"""
Database models for Ghuntred-v2
Real SQLAlchemy models for the HR system
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Enum, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from .database import Base

class UserRole(enum.Enum):
    EMPLOYEE = "employee"
    SUPERVISOR = "supervisor"
    HR_ADMIN = "hr_admin"
    SUPER_ADMIN = "super_admin"

class MessageChannel(enum.Enum):
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    EMAIL = "email"
    SMS = "sms"

class Company(Base):
    __tablename__ = "companies"
    
    id = Column(String, primary_key=True)
    name = Column(String(255), nullable=False)
    country = Column(String(2), nullable=False)
    timezone = Column(String(50), default="America/Mexico_City")
    whatsapp_number = Column(String(20))
    telegram_bot_token = Column(String(255))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    employees = relationship("Employee", back_populates="company")
    payroll_records = relationship("PayrollRecord", back_populates="company")

class Employee(Base):
    __tablename__ = "employees"
    
    id = Column(String, primary_key=True)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    employee_number = Column(String(50), unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone_number = Column(String(20), unique=True, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.EMPLOYEE)
    department = Column(String(100))
    position = Column(String(100))
    hire_date = Column(DateTime, nullable=False)
    monthly_salary = Column(Numeric(10, 2), nullable=False)
    hourly_rate = Column(Numeric(8, 2))
    manager_id = Column(String, ForeignKey("employees.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    company = relationship("Company", back_populates="employees")
    manager = relationship("Employee", remote_side=[id])
    payroll_records = relationship("PayrollRecord", back_populates="employee")
    attendance_records = relationship("AttendanceRecord", back_populates="employee")
    overtime_requests = relationship("OvertimeRequest", back_populates="employee")

class PayrollRecord(Base):
    __tablename__ = "payroll_records"
    
    id = Column(String, primary_key=True)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    employee_id = Column(String, ForeignKey("employees.id"), nullable=False)
    pay_period_start = Column(DateTime, nullable=False)
    pay_period_end = Column(DateTime, nullable=False)
    
    # Income
    base_salary = Column(Numeric(10, 2), nullable=False)
    overtime_hours = Column(Numeric(5, 2), default=0)
    overtime_amount = Column(Numeric(10, 2), default=0)
    bonuses = Column(Numeric(10, 2), default=0)
    commissions = Column(Numeric(10, 2), default=0)
    other_income = Column(Numeric(10, 2), default=0)
    gross_income = Column(Numeric(10, 2), nullable=False)
    
    # Deductions
    imss_employee = Column(Numeric(10, 2), default=0)
    isr_withheld = Column(Numeric(10, 2), default=0)
    loan_deductions = Column(Numeric(10, 2), default=0)
    advance_deductions = Column(Numeric(10, 2), default=0)
    other_deductions = Column(Numeric(10, 2), default=0)
    total_deductions = Column(Numeric(10, 2), nullable=False)
    
    # Net pay
    net_pay = Column(Numeric(10, 2), nullable=False)
    
    # Metadata
    calculation_date = Column(DateTime, default=func.now())
    processed_by = Column(String, nullable=False)
    is_processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    company = relationship("Company", back_populates="payroll_records")
    employee = relationship("Employee", back_populates="payroll_records")

class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    
    id = Column(String, primary_key=True)
    employee_id = Column(String, ForeignKey("employees.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    check_in_time = Column(DateTime)
    check_out_time = Column(DateTime)
    hours_worked = Column(Numeric(5, 2))
    location_lat = Column(Numeric(10, 8))
    location_lon = Column(Numeric(11, 8))
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    employee = relationship("Employee", back_populates="attendance_records")

class OvertimeRequest(Base):
    __tablename__ = "overtime_requests"
    
    id = Column(String, primary_key=True)
    employee_id = Column(String, ForeignKey("employees.id"), nullable=False)
    work_date = Column(DateTime, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    hours_requested = Column(Numeric(5, 2), nullable=False)
    overtime_type = Column(String(20), default="regular")
    reason = Column(Text)
    status = Column(String(20), default="pending")  # pending, approved, rejected
    approver_id = Column(String, ForeignKey("employees.id"))
    approved_at = Column(DateTime)
    comments = Column(Text)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    employee = relationship("Employee", back_populates="overtime_requests")
    approver = relationship("Employee", foreign_keys=[approver_id])

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    phone_number = Column(String(20), nullable=False)
    channel = Column(Enum(MessageChannel), nullable=False)
    state = Column(String(50), default="idle")
    context = Column(Text)  # JSON string
    is_authenticated = Column(Boolean, default=False)
    last_activity = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    user_id = Column(String, nullable=False)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    channel = Column(Enum(MessageChannel), nullable=False)
    message_type = Column(String(20), default="text")  # text, image, location, etc.
    content = Column(Text, nullable=False)
    response = Column(Text)
    intent = Column(String(50))
    confidence = Column(Numeric(3, 2))
    created_at = Column(DateTime, default=func.now())

class SystemSettings(Base):
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True)
    company_id = Column(String, ForeignKey("companies.id"))
    setting_key = Column(String(100), nullable=False)
    setting_value = Column(Text)
    setting_type = Column(String(20), default="string")
    description = Column(Text)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    updated_by = Column(String, nullable=False)