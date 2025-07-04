"""
🚀 GhuntRED-v2 Candidate Models
Complete candidate profile and assessment system
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models import BaseModel

User = get_user_model()

class Skill(BaseModel):
    """Skills catalog"""
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=50)  # e.g., 'Programming', 'Soft Skills'
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Skill'
        verbose_name_plural = 'Skills'
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.category})"

class CandidateProfile(BaseModel):
    """Extended candidate profile"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='candidate_profile')
    
    # Professional summary
    professional_summary = models.TextField(max_length=2000, blank=True)
    years_of_experience = models.PositiveIntegerField(default=0)
    current_role = models.CharField(max_length=200, blank=True)
    current_company = models.CharField(max_length=200, blank=True)
    
    # Salary expectations
    expected_salary_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    expected_salary_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='MXN')  # ISO currency code
    
    # Availability
    availability_status = models.CharField(
        max_length=20,
        choices=[
            ('available', 'Available'),
            ('passive', 'Passive'),
            ('not_available', 'Not Available'),
        ],
        default='available'
    )
    notice_period = models.CharField(max_length=50, blank=True)  # e.g., "2 weeks", "1 month"
    
    # Work preferences
    work_type_preference = models.CharField(
        max_length=20,
        choices=[
            ('remote', 'Remote'),
            ('hybrid', 'Hybrid'),
            ('onsite', 'On-site'),
            ('flexible', 'Flexible'),
        ],
        default='flexible'
    )
    
    # Documents
    resume_file = models.FileField(upload_to='resumes/', blank=True, null=True)
    cover_letter = models.TextField(max_length=1000, blank=True)
    
    # ML Analysis Results
    personality_score = models.JSONField(default=dict, blank=True)  # From AURA analysis
    skills_assessment = models.JSONField(default=dict, blank=True)  # From GenIA analysis
    compatibility_score = models.FloatField(null=True, blank=True)
    
    # Status tracking
    profile_completion = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(100)])
    last_activity = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Candidate Profile'
        verbose_name_plural = 'Candidate Profiles'
        ordering = ['-last_activity']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.current_role}"
    
    def calculate_profile_completion(self):
        """Calculate profile completion percentage"""
        fields_to_check = [
            self.professional_summary,
            self.current_role,
            self.years_of_experience > 0,
            self.expected_salary_min,
            self.resume_file,
            self.user.phone,
            self.user.city,
        ]
        completed_fields = sum(1 for field in fields_to_check if field)
        completion = (completed_fields / len(fields_to_check)) * 100
        self.profile_completion = round(completion)
        return self.profile_completion

class CandidateSkill(BaseModel):
    """Candidate skills with proficiency levels"""
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name='skills')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    proficiency_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
            ('expert', 'Expert'),
        ],
        default='intermediate'
    )
    years_of_experience = models.PositiveIntegerField(default=0)
    is_primary = models.BooleanField(default=False)  # Primary skills
    
    class Meta:
        verbose_name = 'Candidate Skill'
        verbose_name_plural = 'Candidate Skills'
        unique_together = ['candidate', 'skill']
        ordering = ['-is_primary', '-years_of_experience']
    
    def __str__(self):
        return f"{self.candidate.user.get_full_name()} - {self.skill.name} ({self.proficiency_level})"

class Education(BaseModel):
    """Educational background"""
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name='education')
    
    institution = models.CharField(max_length=200)
    degree = models.CharField(max_length=100)
    field_of_study = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)  # Null if currently studying
    gpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Education'
        verbose_name_plural = 'Education'
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.candidate.user.get_full_name()} - {self.degree} from {self.institution}"

class WorkExperience(BaseModel):
    """Work experience history"""
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name='work_experience')
    
    company = models.CharField(max_length=200)
    position = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)  # Null if current job
    description = models.TextField(blank=True)
    technologies_used = models.TextField(blank=True)  # Comma-separated or JSON
    achievements = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Work Experience'
        verbose_name_plural = 'Work Experience'
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.candidate.user.get_full_name()} - {self.position} at {self.company}"
    
    @property
    def is_current_job(self):
        """Check if this is the current job"""
        return self.end_date is None

class CandidateAssessment(BaseModel):
    """ML-powered candidate assessments"""
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name='assessments')
    
    assessment_type = models.CharField(
        max_length=20,
        choices=[
            ('genia', 'GenIA Analysis'),
            ('aura', 'AURA Analysis'),
            ('technical', 'Technical Assessment'),
            ('personality', 'Personality Test'),
        ]
    )
    
    # Assessment results
    score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    results = models.JSONField(default=dict)  # Detailed results
    recommendations = models.TextField(blank=True)
    
    # Metadata
    assessment_date = models.DateTimeField(auto_now_add=True)
    processing_time = models.FloatField(null=True, blank=True)  # In seconds
    model_version = models.CharField(max_length=50, blank=True)
    
    class Meta:
        verbose_name = 'Candidate Assessment'
        verbose_name_plural = 'Candidate Assessments'
        ordering = ['-assessment_date']
    
    def __str__(self):
        return f"{self.candidate.user.get_full_name()} - {self.assessment_type} ({self.score:.1f}%)"

class CandidateInteraction(BaseModel):
    """Track all interactions with candidates"""
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name='interactions')
    interaction_type = models.CharField(
        max_length=20,
        choices=[
            ('email', 'Email'),
            ('phone', 'Phone Call'),
            ('whatsapp', 'WhatsApp'),
            ('telegram', 'Telegram'),
            ('interview', 'Interview'),
            ('assessment', 'Assessment'),
        ]
    )
    
    subject = models.CharField(max_length=200, blank=True)
    content = models.TextField(blank=True)
    initiated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Interaction metadata
    scheduled_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('scheduled', 'Scheduled'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
            ('no_show', 'No Show'),
        ],
        default='completed'
    )
    
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Candidate Interaction'
        verbose_name_plural = 'Candidate Interactions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.candidate.user.get_full_name()} - {self.interaction_type}"