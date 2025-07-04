"""
Configuration settings for huntRED® v2
Using Pydantic Settings for type-safe configuration management
"""

from typing import List, Optional, Any, Dict
from pydantic import BaseSettings, validator, Field
import os
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings using Pydantic BaseSettings"""
    
    # Application Settings
    project_name: str = Field(default="huntRED v2", env="PROJECT_NAME")
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    api_v1_str: str = Field(default="/api/v1", env="API_V1_STR")
    
    # Security Settings
    secret_key: str = Field(..., env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Database Settings
    database_url: str = Field(..., env="DATABASE_URL")
    redis_url: str = Field(..., env="REDIS_URL")
    
    # WhatsApp Business API
    whatsapp_access_token: str = Field(..., env="WHATSAPP_ACCESS_TOKEN")
    whatsapp_verify_token: str = Field(..., env="WHATSAPP_VERIFY_TOKEN")
    whatsapp_api_version: str = Field(default="v18.0", env="WHATSAPP_API_VERSION")
    whatsapp_phone_number_id: str = Field(..., env="WHATSAPP_PHONE_NUMBER_ID")
    webhook_endpoint_base_url: str = Field(..., env="WEBHOOK_ENDPOINT_BASE_URL")
    
    # Messaging Services
    telegram_bot_token: Optional[str] = Field(default=None, env="TELEGRAM_BOT_TOKEN")
    twilio_account_sid: Optional[str] = Field(default=None, env="TWILIO_ACCOUNT_SID")
    twilio_auth_token: Optional[str] = Field(default=None, env="TWILIO_AUTH_TOKEN")
    
    # AI & ML Services
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    
    # Social Media APIs
    linkedin_client_id: Optional[str] = Field(default=None, env="LINKEDIN_CLIENT_ID")
    linkedin_client_secret: Optional[str] = Field(default=None, env="LINKEDIN_CLIENT_SECRET")
    twitter_bearer_token: Optional[str] = Field(default=None, env="TWITTER_BEARER_TOKEN")
    github_token: Optional[str] = Field(default=None, env="GITHUB_TOKEN")
    
    # Email Configuration
    smtp_tls: bool = Field(default=True, env="SMTP_TLS")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_host: Optional[str] = Field(default=None, env="SMTP_HOST")
    smtp_user: Optional[str] = Field(default=None, env="SMTP_USER")
    smtp_password: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    
    # AWS Configuration
    aws_access_key_id: Optional[str] = Field(default=None, env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(default=None, env="AWS_SECRET_ACCESS_KEY")
    aws_default_region: str = Field(default="us-east-1", env="AWS_DEFAULT_REGION")
    s3_bucket_name: Optional[str] = Field(default=None, env="S3_BUCKET_NAME")
    
    # Monitoring
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")
    grafana_url: Optional[str] = Field(default=None, env="GRAFANA_URL")
    prometheus_url: Optional[str] = Field(default=None, env="PROMETHEUS_URL")
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    burst_limit: int = Field(default=10, env="BURST_LIMIT")
    
    # Geolocation Settings
    office_location_radius_meters: int = Field(default=100, env="OFFICE_LOCATION_RADIUS_METERS")
    default_timezone: str = Field(default="America/Mexico_City", env="DEFAULT_TIMEZONE")
    
    # Payroll Settings
    default_currency: str = Field(default="MXN", env="DEFAULT_CURRENCY")
    uma_daily_2024: float = Field(default=108.57, env="UMA_DAILY_2024")
    uma_monthly_2024: float = Field(default=3257.10, env="UMA_MONTHLY_2024")
    
    # File Upload Settings
    max_file_size_mb: int = Field(default=10, env="MAX_FILE_SIZE_MB")
    allowed_file_extensions: str = Field(default="pdf,xlsx,csv,jpg,png", env="ALLOWED_FILE_EXTENSIONS")
    
    # Celery Configuration
    celery_broker_url: str = Field(..., env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(..., env="CELERY_RESULT_BACKEND")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    # CORS Settings
    backend_cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        env="BACKEND_CORS_ORIGINS"
    )
    
    # Security - Allowed hosts for production
    allowed_hosts: List[str] = Field(
        default=["localhost", "127.0.0.1"],
        env="ALLOWED_HOSTS"
    )
    
    @validator("backend_cors_origins", pre=True)
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        """Parse CORS origins from string or list"""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    @validator("allowed_hosts", pre=True)
    def assemble_allowed_hosts(cls, v: str | List[str]) -> List[str]:
        """Parse allowed hosts from string or list"""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    @validator("allowed_file_extensions")
    def parse_file_extensions(cls, v: str) -> List[str]:
        """Parse file extensions from comma-separated string"""
        return [ext.strip().lower() for ext in v.split(",")]
    
    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL for SQLAlchemy"""
        return self.database_url.replace("postgresql://", "postgresql://")
    
    @property
    def database_url_async(self) -> str:
        """Get asynchronous database URL for SQLAlchemy"""
        return self.database_url.replace("postgresql://", "postgresql+asyncpg://")
    
    @property
    def whatsapp_api_base_url(self) -> str:
        """Get WhatsApp API base URL"""
        return f"https://graph.facebook.com/{self.whatsapp_api_version}"
    
    @property
    def max_file_size_bytes(self) -> int:
        """Get max file size in bytes"""
        return self.max_file_size_mb * 1024 * 1024
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment.lower() == "development"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()