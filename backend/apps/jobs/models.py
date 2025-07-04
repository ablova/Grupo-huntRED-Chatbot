"""
🚀 GhuntRED-v2 Job Models
Job postings, applications, and ML-powered matching
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models import BaseModel
from apps.companies.models import Company
from apps.candidates.models import CandidateProfile, Skill

User = get_user_model()

class JobPosting(BaseModel):
    """Job postings with ML-enhanced matching"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='job_postings')
    posted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    # Basic job information
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(max_length=5000)
    requirements = models.TextField(max_length=3000, blank=True)
    responsibilities = models.TextField(max_length=3000, blank=True)
    
    # Job details
    employment_type = models.CharField(
        max_length=20,
        choices=[
            ('full_time', 'Full Time'),
            ('part_time', 'Part Time'),
            ('contract', 'Contract'),
            ('freelance', 'Freelance'),
            ('internship', 'Internship'),
        ],
        default='full_time'
    )
    
    experience_level = models.CharField(
        max_length=20,
        choices=[
            ('entry', 'Entry Level'),
            ('junior', 'Junior'),
            ('mid', 'Mid Level'),
            ('senior', 'Senior'),
            ('lead', 'Lead'),
            ('manager', 'Manager'),
            ('director', 'Director'),
            ('executive', 'Executive'),
        ]
    )
    
    department = models.CharField(max_length=100, blank=True)
    category = models.CharField(max_length=100, blank=True)
    
    # Compensation
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='MXN')
    salary_type = models.CharField(
        max_length=20,
        choices=[
            ('hourly', 'Hourly'),
            ('monthly', 'Monthly'),
            ('yearly', 'Yearly'),
        ],
        default='monthly'
    )
    
    # Location and remote work
    location = models.CharField(max_length=200, blank=True)
    country = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    
    remote_work = models.CharField(
        max_length=20,
        choices=[
            ('no', 'No Remote'),
            ('hybrid', 'Hybrid'),
            ('full_remote', 'Full Remote'),
        ],
        default='no'
    )
    
    # Application settings
    application_deadline = models.DateTimeField(null=True, blank=True)
    application_email = models.EmailField(blank=True)
    external_url = models.URLField(blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('published', 'Published'),
            ('paused', 'Paused'),
            ('closed', 'Closed'),
            ('filled', 'Filled'),
        ],
        default='draft'
    )
    
    # ML features
    auto_screen = models.BooleanField(default=True)  # Auto-screen with GenIA
    aura_analysis = models.BooleanField(default=True)  # AURA compatibility analysis
    required_skills = models.ManyToManyField(Skill, through='JobSkillRequirement')
    
    # Analytics
    view_count = models.PositiveIntegerField(default=0)
    application_count = models.PositiveIntegerField(default=0)
    
    # Publishing
    published_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Job Posting'
        verbose_name_plural = 'Job Postings'
        ordering = ['-published_at', '-created_at']
    
    def __str__(self):
        return f"{self.title} at {self.company.name}"

class JobSkillRequirement(BaseModel):
    """Required skills for job postings"""
    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    
    required_level = models.CharField(
        max_length=20,
        choices=[
            ('basic', 'Basic'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
            ('expert', 'Expert'),
        ],
        default='intermediate'
    )
    
    is_required = models.BooleanField(default=True)  # Required vs. Nice to have
    weight = models.FloatField(default=1.0)  # Importance weight for ML matching
    
    class Meta:
        verbose_name = 'Job Skill Requirement'
        verbose_name_plural = 'Job Skill Requirements'
        unique_together = ['job', 'skill']
    
    def __str__(self):
        return f"{self.job.title} - {self.skill.name} ({self.required_level})"

class JobApplication(BaseModel):
    """Job applications from candidates"""
    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='applications')
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name='applications')
    
    # Application content
    cover_letter = models.TextField(max_length=2000, blank=True)
    custom_resume = models.FileField(upload_to='applications/resumes/', blank=True, null=True)
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=[
            ('submitted', 'Submitted'),
            ('screening', 'Screening'),
            ('interview_scheduled', 'Interview Scheduled'),
            ('interviewing', 'Interviewing'),
            ('under_review', 'Under Review'),
            ('offer_extended', 'Offer Extended'),
            ('hired', 'Hired'),
            ('rejected', 'Rejected'),
            ('withdrawn', 'Withdrawn'),
        ],
        default='submitted'
    )
    
    # ML Analysis Results
    genia_score = models.FloatField(null=True, blank=True)  # GenIA screening score
    aura_compatibility = models.FloatField(null=True, blank=True)  # AURA compatibility
    overall_match_score = models.FloatField(null=True, blank=True)  # Combined score
    
    # ML Analysis Details
    skills_match = models.JSONField(default=dict, blank=True)
    personality_match = models.JSONField(default=dict, blank=True)
    experience_analysis = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    applied_at = models.DateTimeField(auto_now_add=True)
    last_status_change = models.DateTimeField(auto_now=True)
    
    # Screening notes
    screening_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Job Application'
        verbose_name_plural = 'Job Applications'
        unique_together = ['job', 'candidate']
        ordering = ['-applied_at']
    
    def __str__(self):
        return f"{self.candidate.user.get_full_name()} → {self.job.title}"

class Interview(BaseModel):
    """Interview scheduling and management"""
    application = models.ForeignKey(JobApplication, on_delete=models.CASCADE, related_name='interviews')
    interviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    # Interview details
    interview_type = models.CharField(
        max_length=20,
        choices=[
            ('phone', 'Phone Screen'),
            ('video', 'Video Interview'),
            ('onsite', 'On-site Interview'),
            ('technical', 'Technical Interview'),
            ('panel', 'Panel Interview'),
            ('final', 'Final Interview'),
        ]
    )
    
    scheduled_at = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    location = models.CharField(max_length=200, blank=True)  # For onsite or meeting link
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('scheduled', 'Scheduled'),
            ('confirmed', 'Confirmed'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
            ('no_show', 'No Show'),
            ('rescheduled', 'Rescheduled'),
        ],
        default='scheduled'
    )
    
    # Feedback
    interviewer_feedback = models.TextField(blank=True)
    candidate_feedback = models.TextField(blank=True)
    
    # Ratings
    technical_rating = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    communication_rating = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    cultural_fit_rating = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    overall_rating = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    # Recommendations
    recommendation = models.CharField(
        max_length=20,
        choices=[
            ('strong_hire', 'Strong Hire'),
            ('hire', 'Hire'),
            ('no_hire', 'No Hire'),
            ('strong_no_hire', 'Strong No Hire'),
        ],
        blank=True
    )
    
    class Meta:
        verbose_name = 'Interview'
        verbose_name_plural = 'Interviews'
        ordering = ['-scheduled_at']
    
    def __str__(self):
        return f"{self.application} - {self.interview_type} on {self.scheduled_at.date()}"

class JobOffer(BaseModel):
    """Job offers and negotiations"""
    application = models.OneToOneField(JobApplication, on_delete=models.CASCADE, related_name='offer')
    offered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    # Offer details
    position_title = models.CharField(max_length=200)
    salary_offered = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='MXN')
    
    # Benefits
    benefits_package = models.TextField(blank=True)
    start_date = models.DateField()
    
    # Offer status
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('accepted', 'Accepted'),
            ('rejected', 'Rejected'),
            ('negotiating', 'Negotiating'),
            ('withdrawn', 'Withdrawn'),
            ('expired', 'Expired'),
        ],
        default='pending'
    )
    
    # Negotiation
    candidate_counter_offer = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    negotiation_notes = models.TextField(blank=True)
    
    # Timeline
    offered_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    responded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Job Offer'
        verbose_name_plural = 'Job Offers'
        ordering = ['-offered_at']
    
    def __str__(self):
        return f"Offer to {self.application.candidate.user.get_full_name()} - {self.position_title}"

class SavedJob(BaseModel):
    """Candidates can save jobs for later"""
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name='saved_jobs')
    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='saved_by')
    
    class Meta:
        verbose_name = 'Saved Job'
        verbose_name_plural = 'Saved Jobs'
        unique_together = ['candidate', 'job']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.candidate.user.get_full_name()} saved {self.job.title}"

class JobAlert(BaseModel):
    """Job alerts for candidates"""
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name='job_alerts')
    
    # Alert criteria
    keywords = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=200, blank=True)
    employment_type = models.CharField(max_length=20, blank=True)
    experience_level = models.CharField(max_length=20, blank=True)
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    remote_work = models.CharField(max_length=20, blank=True)
    
    # Alert settings
    frequency = models.CharField(
        max_length=20,
        choices=[
            ('immediate', 'Immediate'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
        ],
        default='daily'
    )
    
    is_active = models.BooleanField(default=True)
    last_sent = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Job Alert'
        verbose_name_plural = 'Job Alerts'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Job Alert for {self.candidate.user.get_full_name()}"