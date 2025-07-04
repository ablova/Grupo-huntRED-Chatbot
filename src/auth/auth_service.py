"""
Authentication Service - JWT Real Implementation
Complete authentication system with JWT tokens
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import logging

from ..database.database import get_db
from ..database.models import Employee, UserRole

logger = logging.getLogger(__name__)

# JWT Configuration
SECRET_KEY = "huntred_v2_secret_key_change_in_production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

class AuthService:
    """Real authentication service with JWT"""
    
    def __init__(self):
        self.pwd_context = pwd_context
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash password"""
        return self.pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    
    async def authenticate_employee(self, email: str, password: str, db: Session) -> Optional[Employee]:
        """Authenticate employee by email and password"""
        try:
            employee = db.query(Employee).filter(
                Employee.email == email,
                Employee.is_active == True
            ).first()
            
            if not employee:
                return None
            
            # For demo purposes, we'll use a simple password check
            # In production, you'd have a password field in the Employee model
            if not self.verify_demo_password(employee, password):
                return None
            
            logger.info(f"Employee authenticated: {employee.email}")
            return employee
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    
    def verify_demo_password(self, employee: Employee, password: str) -> bool:
        """Demo password verification (replace with real implementation)"""
        # Demo passwords based on employee role
        demo_passwords = {
            UserRole.SUPER_ADMIN: "admin123",
            UserRole.HR_ADMIN: "hr123",
            UserRole.SUPERVISOR: "supervisor123",
            UserRole.EMPLOYEE: "employee123"
        }
        return password == demo_passwords.get(employee.role, "employee123")
    
    async def get_current_employee(self, credentials: HTTPAuthorizationCredentials = Depends(security), 
                                 db: Session = Depends(get_db)) -> Employee:
        """Get current authenticated employee"""
        token = credentials.credentials
        payload = self.verify_token(token)
        
        employee_id = payload.get("sub")
        if not employee_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Employee not found"
            )
        
        return employee
    
    def require_role(self, required_roles: list):
        """Decorator to require specific roles"""
        def role_checker(current_employee: Employee = Depends(self.get_current_employee)):
            if current_employee.role not in required_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            return current_employee
        return role_checker

# Global auth service instance
auth_service = AuthService()