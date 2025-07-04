"""
🚀 GhuntRED-v2 Company Models
Company profiles, teams, and hiring management
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import URLValidator
from apps.core.models import BaseModel

User = get_user_model()

class Company(BaseModel):
    """Company profiles and information"""
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    
    # Basic information
    description = models.TextField(max_length=2000, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    company_size = models.CharField(
        max_length=20,
        choices=[
            ('startup', '1-10 employees'),
            ('small', '11-50 employees'),
            ('medium', '51-200 employees'),
            ('large', '201-1000 employees'),
            ('enterprise', '1000+ employees'),
        ],
        blank=True
    )
    founded_year = models.PositiveIntegerField(null=True, blank=True)
    
    # Contact information
    website = models.URLField(blank=True, validators=[URLValidator()])
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    # Location
    headquarters = models.CharField(max_length=200, blank=True)
    country = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    
    # Media
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    banner_image = models.ImageField(upload_to='company_banners/', blank=True, null=True)
    
    # Social media
    linkedin_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    
    # Business information
    business_model = models.CharField(max_length=100, blank=True)
    funding_stage = models.CharField(
        max_length=20,
        choices=[
            ('bootstrapped', 'Bootstrapped'),
            ('seed', 'Seed'),
            ('series_a', 'Series A'),
            ('series_b', 'Series B'),
            ('series_c', 'Series C+'),
            ('ipo', 'Public'),
        ],
        blank=True
    )
    
    # Status
    is_verified = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    profile_completion = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class CompanyTeamMember(BaseModel):
    """Company team members and roles"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='team_members')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    role = models.CharField(
        max_length=20,
        choices=[
            ('owner', 'Owner'),
            ('admin', 'Administrator'),
            ('hr', 'HR Manager'),
            ('recruiter', 'Recruiter'),
            ('member', 'Team Member'),
        ],
        default='member'
    )
    
    title = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    
    # Permissions
    can_post_jobs = models.BooleanField(default=False)
    can_view_candidates = models.BooleanField(default=False)
    can_interview = models.BooleanField(default=False)
    can_hire = models.BooleanField(default=False)
    
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Company Team Member'
        verbose_name_plural = 'Company Team Members'
        unique_together = ['company', 'user']
        ordering = ['-joined_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.company.name} ({self.role})"

class CompanyReview(BaseModel):
    """Company reviews from employees/candidates"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Rating (1-5 stars)
    overall_rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])
    culture_rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])
    compensation_rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])
    management_rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])
    
    # Review content
    title = models.CharField(max_length=200)
    pros = models.TextField(max_length=1000)
    cons = models.TextField(max_length=1000)
    advice_to_management = models.TextField(max_length=1000, blank=True)
    
    # Metadata
    reviewer_role = models.CharField(max_length=100, blank=True)
    employment_status = models.CharField(
        max_length=20,
        choices=[
            ('current', 'Current Employee'),
            ('former', 'Former Employee'),
            ('candidate', 'Candidate'),
        ]
    )
    
    is_anonymous = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Company Review'
        verbose_name_plural = 'Company Reviews'
        ordering = ['-created_at']
        unique_together = ['company', 'reviewer']  # One review per user per company
    
    def __str__(self):
        return f"{self.company.name} - {self.overall_rating}⭐ by {self.reviewer.get_full_name()}"

class CompanyBenefit(BaseModel):
    """Company benefits and perks"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='benefits')
    
    name = models.CharField(max_length=100)
    category = models.CharField(
        max_length=30,
        choices=[
            ('health', 'Health & Wellness'),
            ('financial', 'Financial'),
            ('time_off', 'Time Off'),
            ('professional', 'Professional Development'),
            ('workplace', 'Workplace'),
            ('family', 'Family'),
            ('transportation', 'Transportation'),
            ('food', 'Food & Dining'),
            ('other', 'Other'),
        ]
    )
    description = models.TextField(max_length=500, blank=True)
    
    class Meta:
        verbose_name = 'Company Benefit'
        verbose_name_plural = 'Company Benefits'
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.company.name} - {self.name}"

class CompanyMetrics(BaseModel):
    """Company hiring metrics and analytics"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='metrics')
    
    # Time period
    month = models.PositiveIntegerField()
    year = models.PositiveIntegerField()
    
    # Hiring metrics
    jobs_posted = models.PositiveIntegerField(default=0)
    applications_received = models.PositiveIntegerField(default=0)
    candidates_interviewed = models.PositiveIntegerField(default=0)
    hires_made = models.PositiveIntegerField(default=0)
    
    # Performance metrics
    avg_time_to_hire = models.FloatField(null=True, blank=True)  # Days
    avg_cost_per_hire = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    offer_acceptance_rate = models.FloatField(null=True, blank=True)  # Percentage
    
    # Engagement metrics
    page_views = models.PositiveIntegerField(default=0)
    profile_views = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = 'Company Metrics'
        verbose_name_plural = 'Company Metrics'
        unique_together = ['company', 'month', 'year']
        ordering = ['-year', '-month']
    
    def __str__(self):
        return f"{self.company.name} - {self.month}/{self.year}"