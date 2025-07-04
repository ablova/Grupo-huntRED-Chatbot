"""
🚀 GhuntRED-v2 Core Models
Base models and user authentication system
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.core.validators import EmailValidator
import uuid

class BaseModel(models.Model):
    """Base model with common fields for all models"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        abstract = True
        
    def soft_delete(self):
        """Soft delete by setting is_active to False"""
        self.is_active = False
        self.save()

class BusinessUnit(BaseModel):
    """Business units for the platform"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    color = models.CharField(max_length=7, default='#ef4444')  # Hex color
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='business_units/', blank=True, null=True)
    enabled = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Business Unit'
        verbose_name_plural = 'Business Units'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class User(AbstractUser):
    """Custom user model with extended fields"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, validators=[EmailValidator()])
    phone = models.CharField(max_length=20, blank=True)
    
    # Profile fields
    birth_date = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    
    # Location
    country = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    
    # Professional fields
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    
    # Business unit association
    business_unit = models.ForeignKey(
        BusinessUnit, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    
    # Verification
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    
    # Privacy settings
    show_email = models.BooleanField(default=False)
    show_phone = models.BooleanField(default=False)
    
    # Timestamps
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.username
    
    @property
    def has_complete_profile(self):
        """Check if user has completed their profile"""
        required_fields = [
            self.first_name, 
            self.last_name, 
            self.email, 
            self.phone
        ]
        return all(field for field in required_fields)

class UserSession(BaseModel):
    """Track user sessions for security"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=200, blank=True)
    login_time = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'User Session'
        verbose_name_plural = 'User Sessions'
        ordering = ['-login_time']
    
    def __str__(self):
        return f"{self.user.email} - {self.ip_address}"

class SystemConfiguration(BaseModel):
    """System-wide configuration settings"""
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    is_sensitive = models.BooleanField(default=False)  # For passwords, API keys, etc.
    
    class Meta:
        verbose_name = 'System Configuration'
        verbose_name_plural = 'System Configurations'
        ordering = ['key']
    
    def __str__(self):
        return f"{self.key}: {self.value[:50]}..."

class APIKey(BaseModel):
    """API keys for external integrations"""
    name = models.CharField(max_length=100)
    key = models.CharField(max_length=255, unique=True)
    secret = models.CharField(max_length=255, blank=True)
    service = models.CharField(max_length=100)  # e.g., 'whatsapp', 'telegram', 'sendgrid'
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'API Key'
        verbose_name_plural = 'API Keys'
        ordering = ['service', 'name']
    
    def __str__(self):
        return f"{self.service} - {self.name}"
    
    @property
    def is_expired(self):
        """Check if API key is expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False