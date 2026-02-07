import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


# ============================================================================
# USER MODELS & AUTHENTICATION
# ============================================================================

class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with the given email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'admin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model with role-based access control."""
    
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('employer', 'Employer'),
        ('freelancer', 'Freelancer'),
    ]
    
    ACCOUNT_TYPE_CHOICES = [
        ('employer', 'Employer'),
        ('freelancer', 'Freelancer'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, max_length=255)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='freelancer')
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES, null=True, blank=True)
    
    # Status fields
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role', 'is_active']),
        ]
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Return the user's full name from their profile."""
        if hasattr(self, 'employer_profile'):
            return f"{self.employer_profile.first_name} {self.employer_profile.last_name}"
        elif hasattr(self, 'freelancer_profile'):
            return f"{self.freelancer_profile.first_name} {self.freelancer_profile.last_name}"
        return self.email


class EmployerProfile(models.Model):
    """Profile for employers who post jobs."""
    
    VERIFICATION_STATUS_CHOICES = [
        ('unverified', 'Unverified'),
        ('pending', 'Pending'),
        ('verified', 'Verified'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employer_profile')
    
    # Personal information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True, null=True)
    position_title = models.CharField(max_length=150, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    profile_picture_url = models.URLField(max_length=500, blank=True, null=True)
    linkedin_url = models.URLField(max_length=500, blank=True, null=True)
    
    # Company relationship
    primary_company = models.ForeignKey('Company', on_delete=models.SET_NULL, null=True, blank=True, related_name='primary_employers')
    
    # Permissions and verification
    can_post_jobs = models.BooleanField(default=True)
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS_CHOICES, default='unverified')
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Statistics
    jobs_posted_count = models.IntegerField(default=0)
    active_jobs_count = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'employer_profiles'
        verbose_name = 'Employer Profile'
        verbose_name_plural = 'Employer Profiles'
        indexes = [
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.user.email}"


class FreelancerProfile(models.Model):
    """Comprehensive profile for freelancers/job seekers."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='freelancer_profile')
    
    # Personal information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    profile_picture_url = models.URLField(max_length=500, blank=True, null=True)
    
    # Professional links
    resume_url = models.URLField(max_length=500, blank=True, null=True)
    portfolio_url = models.URLField(max_length=500, blank=True, null=True)
    linkedin_url = models.URLField(max_length=500, blank=True, null=True)
    github_url = models.URLField(max_length=500, blank=True, null=True)
    
    # Preferences (stored as JSON)
    service_categories = models.JSONField(default=list, blank=True)
    preferred_project_types = models.JSONField(default=list, blank=True)
    preferred_locations = models.JSONField(default=list, blank=True)
    
    # Rate information
    hourly_rate_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    hourly_rate_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    rate_currency = models.CharField(max_length=3, default='USD')
    
    # Availability
    is_available = models.BooleanField(default=True)
    is_open_to_remote = models.BooleanField(default=True)
    availability_hours = models.JSONField(default=dict, blank=True)
    time_zones = models.JSONField(default=list, blank=True)
    
    # Statistics
    projects_completed = models.IntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00, validators=[MinValueValidator(0), MaxValueValidator(5)])
    total_reviews = models.IntegerField(default=0)
    total_experience_years = models.IntegerField(default=0)
    
    # Payment
    payment_methods = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'freelancer_profiles'
        verbose_name = 'Freelancer Profile'
        verbose_name_plural = 'Freelancer Profiles'
        indexes = [
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.user.email}"


# ============================================================================
# COMPANY & CATEGORY MODELS
# ============================================================================

class Company(models.Model):
    """Company profiles managed by employers."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employer = models.ForeignKey(EmployerProfile, on_delete=models.CASCADE, related_name='companies')
    
    # Basic information
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    logo_url = models.URLField(max_length=500, blank=True, null=True)
    cover_image_url = models.URLField(max_length=500, blank=True, null=True)
    
    # Contact information
    website = models.URLField(max_length=500, blank=True, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Company details
    industry = models.CharField(max_length=100, blank=True, null=True)
    size = models.CharField(max_length=50, blank=True, null=True)
    headquarters_location = models.CharField(max_length=255, blank=True, null=True)
    office_locations = models.JSONField(default=list, blank=True)
    founded_date = models.DateField(null=True, blank=True)
    employee_count = models.IntegerField(null=True, blank=True)
    
    # Culture and benefits
    culture_description = models.TextField(blank=True, null=True)
    benefits = models.JSONField(default=list, blank=True)
    social_media_links = models.JSONField(default=dict, blank=True)
    
    # Verification
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'companies'
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'
        indexes = [
            models.Index(fields=['employer']),
            models.Index(fields=['is_verified']),
        ]
    
    def __str__(self):
        return self.name


class Category(models.Model):
    """Hierarchical job categories."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    job_count = models.IntegerField(default=0)
    icon_url = models.URLField(max_length=500, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'categories'
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
    
    def __str__(self):
        return self.name


# ============================================================================
# JOB & APPLICATION MODELS
# ============================================================================

class Job(models.Model):
    """Core job posting model."""
    
    JOB_TYPE_CHOICES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('freelance', 'Freelance'),
        ('internship', 'Internship'),
    ]
    
    EXPERIENCE_LEVEL_CHOICES = [
        ('entry', 'Entry Level'),
        ('intermediate', 'Intermediate'),
        ('senior', 'Senior'),
        ('lead', 'Lead'),
        ('executive', 'Executive'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('closed', 'Closed'),
        ('archived', 'Archived'),
    ]
    
    SALARY_PERIOD_CHOICES = [
        ('hourly', 'Hourly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employer = models.ForeignKey(EmployerProfile, on_delete=models.CASCADE, related_name='jobs')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='jobs')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='jobs')
    
    # Job details
    title = models.CharField(max_length=255)
    description = models.TextField()
    requirements = models.TextField(blank=True, null=True)
    responsibilities = models.TextField(blank=True, null=True)
    benefits = models.TextField(blank=True, null=True)
    
    # Location
    location = models.CharField(max_length=255)
    is_remote = models.BooleanField(default=False)
    
    # Job type and level
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES, default='full_time')
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVEL_CHOICES, default='intermediate')
    
    # Salary information
    salary_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_currency = models.CharField(max_length=3, default='USD')
    salary_period = models.CharField(max_length=20, choices=SALARY_PERIOD_CHOICES, default='yearly')
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Statistics
    view_count = models.IntegerField(default=0)
    application_count = models.IntegerField(default=0)
    save_count = models.IntegerField(default=0)
    
    # Dates
    published_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'jobs'
        verbose_name = 'Job'
        verbose_name_plural = 'Jobs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['employer']),
            models.Index(fields=['company']),
            models.Index(fields=['category']),
            models.Index(fields=['status', 'published_at']),
            models.Index(fields=['job_type']),
            models.Index(fields=['location']),
            models.Index(fields=['-view_count']),
            models.Index(fields=['-application_count']),
        ]
    
    def __str__(self):
        return f"{self.title} at {self.company.name}"
    
    def save(self, *args, **kwargs):
        """Auto-set published_at when status changes to published."""
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)


class Application(models.Model):
    """Job application tracking."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewing', 'Reviewing'),
        ('shortlisted', 'Shortlisted'),
        ('interviewing', 'Interviewing'),
        ('offered', 'Offered'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    
    # Application details
    cover_letter = models.TextField(blank=True, null=True)
    resume_url = models.URLField(max_length=500, blank=True, null=True)
    answers = models.JSONField(default=dict, blank=True)  # For custom application questions
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    rejection_reason = models.TextField(blank=True, null=True)
    
    # Employer notes
    rating = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    internal_notes = models.TextField(blank=True, null=True)
    
    # Timestamps
    applied_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    status_changed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'applications'
        verbose_name = 'Application'
        verbose_name_plural = 'Applications'
        ordering = ['-applied_at']
        unique_together = ['job', 'applicant']  # Prevent duplicate applications
        indexes = [
            models.Index(fields=['job', 'status']),
            models.Index(fields=['applicant']),
            models.Index(fields=['status', 'applied_at']),
        ]
    
    def __str__(self):
        return f"{self.applicant.email} - {self.job.title}"
    
    def save(self, *args, **kwargs):
        """Track status changes."""
        if self.pk:
            old_status = Application.objects.get(pk=self.pk).status
            if old_status != self.status:
                self.status_changed_at = timezone.now()
        super().save(*args, **kwargs)


# ============================================================================
# SKILL MODELS
# ============================================================================

class Skill(models.Model):
    """Master skill table."""
    
    CATEGORY_CHOICES = [
        ('programming', 'Programming Language'),
        ('framework', 'Framework'),
        ('tool', 'Tool'),
        ('soft_skill', 'Soft Skill'),
        ('language', 'Language'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='programming')
    popularity_score = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'skills'
        verbose_name = 'Skill'
        verbose_name_plural = 'Skills'
    
    def __str__(self):
        return self.name


class UserSkill(models.Model):
    """Freelancer skills with proficiency levels."""
    
    PROFICIENCY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    freelancer_profile = models.ForeignKey(FreelancerProfile, on_delete=models.CASCADE, related_name='skills')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='user_skills')
    proficiency_level = models.CharField(max_length=20, choices=PROFICIENCY_CHOICES, default='intermediate')
    years_of_experience = models.IntegerField(default=0)
    last_used = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_skills'
        verbose_name = 'User Skill'
        verbose_name_plural = 'User Skills'
        unique_together = ['freelancer_profile', 'skill']
        indexes = [
            models.Index(fields=['freelancer_profile']),
            models.Index(fields=['skill']),
        ]
    
    def __str__(self):
        return f"{self.freelancer_profile.user.email} - {self.skill.name} ({self.proficiency_level})"


class JobSkill(models.Model):
    """Job skill requirements."""
    
    PROFICIENCY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='required_skills')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='job_skills')
    proficiency_level = models.CharField(max_length=20, choices=PROFICIENCY_CHOICES, default='intermediate')
    is_required = models.BooleanField(default=True)
    years_required = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'job_skills'
        verbose_name = 'Job Skill'
        verbose_name_plural = 'Job Skills'
        unique_together = ['job', 'skill']
        indexes = [
            models.Index(fields=['job']),
            models.Index(fields=['skill']),
        ]
    
    def __str__(self):
        return f"{self.job.title} - {self.skill.name}"


# ============================================================================
# FREELANCER PORTFOLIO & EXPERIENCE MODELS
# ============================================================================

class Portfolio(models.Model):
    """Freelancer portfolio projects."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    freelancer_profile = models.ForeignKey(FreelancerProfile, on_delete=models.CASCADE, related_name='portfolio_items')
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    project_url = models.URLField(max_length=500, blank=True, null=True)
    thumbnail_url = models.URLField(max_length=500, blank=True, null=True)
    images = models.JSONField(default=list, blank=True)
    technologies_used = models.JSONField(default=list, blank=True)
    project_date = models.DateField(null=True, blank=True)
    client_name = models.CharField(max_length=255, blank=True, null=True)
    project_type = models.CharField(max_length=100, blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'portfolios'
        verbose_name = 'Portfolio'
        verbose_name_plural = 'Portfolios'
        ordering = ['-is_featured', '-project_date']
        indexes = [
            models.Index(fields=['freelancer_profile']),
        ]
    
    def __str__(self):
        return f"{self.freelancer_profile.user.email} - {self.title}"


class WorkExperience(models.Model):
    """Freelancer work experience."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    freelancer_profile = models.ForeignKey(FreelancerProfile, on_delete=models.CASCADE, related_name='work_experiences')
    
    company_name = models.CharField(max_length=255)
    job_title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    responsibilities = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'work_experiences'
        verbose_name = 'Work Experience'
        verbose_name_plural = 'Work Experiences'
        ordering = ['-is_current', '-start_date']
        indexes = [
            models.Index(fields=['freelancer_profile']),
        ]
    
    def __str__(self):
        return f"{self.freelancer_profile.user.email} - {self.job_title} at {self.company_name}"


class Education(models.Model):
    """Freelancer education."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    freelancer_profile = models.ForeignKey(FreelancerProfile, on_delete=models.CASCADE, related_name='education')
    
    institution = models.CharField(max_length=255)
    degree = models.CharField(max_length=255)
    field_of_study = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    gpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'education'
        verbose_name = 'Education'
        verbose_name_plural = 'Education'
        ordering = ['-is_current', '-start_date']
        indexes = [
            models.Index(fields=['freelancer_profile']),
        ]
    
    def __str__(self):
        return f"{self.freelancer_profile.user.email} - {self.degree} at {self.institution}"


class Certification(models.Model):
    """Professional certifications."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    freelancer_profile = models.ForeignKey(FreelancerProfile, on_delete=models.CASCADE, related_name='certifications')
    
    name = models.CharField(max_length=255)
    issuing_organization = models.CharField(max_length=255)
    credential_id = models.CharField(max_length=255, blank=True, null=True)
    credential_url = models.URLField(max_length=500, blank=True, null=True)
    issue_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    does_not_expire = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'certifications'
        verbose_name = 'Certification'
        verbose_name_plural = 'Certifications'
        ordering = ['-issue_date']
        indexes = [
            models.Index(fields=['freelancer_profile']),
        ]
    
    def __str__(self):
        return f"{self.freelancer_profile.user.email} - {self.name}"


class FreelancerReview(models.Model):
    """Employer reviews of freelancers."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    freelancer_profile = models.ForeignKey(FreelancerProfile, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_reviews')
    job = models.ForeignKey(Job, on_delete=models.SET_NULL, null=True, blank=True, related_name='freelancer_reviews')
    
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review_text = models.TextField()
    rating_breakdown = models.JSONField(default=dict, blank=True)  # e.g., {"quality": 5, "communication": 4, "timeliness": 5}
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'freelancer_reviews'
        verbose_name = 'Freelancer Review'
        verbose_name_plural = 'Freelancer Reviews'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['freelancer_profile']),
        ]
    
    def __str__(self):
        return f"Review for {self.freelancer_profile.user.email} - {self.rating}/5"


# ============================================================================
# RECOMMENDATION & ANALYTICS MODELS
# ============================================================================

class JobRecommendation(models.Model):
    """ML-based job recommendations."""
    
    ALGORITHM_CHOICES = [
        ('content_based', 'Content Based'),
        ('collaborative', 'Collaborative'),
        ('hybrid', 'Hybrid'),
        ('trending', 'Trending'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_recommendations')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='recommendations')
    
    score = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    reason = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    algorithm_type = models.CharField(max_length=20, choices=ALGORITHM_CHOICES, default='hybrid')
    
    # Interaction tracking
    is_viewed = models.BooleanField(default=False)
    is_clicked = models.BooleanField(default=False)
    is_applied = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'job_recommendations'
        verbose_name = 'Job Recommendation'
        verbose_name_plural = 'Job Recommendations'
        ordering = ['-score', '-created_at']
        indexes = [
            models.Index(fields=['user', '-score']),
        ]
    
    def __str__(self):
        return f"Recommendation for {self.user.email} - {self.job.title} (Score: {self.score})"


class SavedJob(models.Model):
    """User's saved/bookmarked jobs."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_jobs')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='saved_by')
    
    notes = models.TextField(blank=True, null=True)
    tags = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'saved_jobs'
        verbose_name = 'Saved Job'
        verbose_name_plural = 'Saved Jobs'
        unique_together = ['user', 'job']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"{self.user.email} saved {self.job.title}"


class JobView(models.Model):
    """Analytics tracking for job views."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='job_views')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='views')
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    duration_seconds = models.IntegerField(default=0)
    referrer = models.URLField(max_length=500, blank=True, null=True)
    
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'job_views'
        verbose_name = 'Job View'
        verbose_name_plural = 'Job Views'
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['job', 'viewed_at']),
        ]
    
    def __str__(self):
        user_email = self.user.email if self.user else 'Anonymous'
        return f"{user_email} viewed {self.job.title}"


class Notification(models.Model):
    """User notifications."""
    
    TYPE_CHOICES = [
        ('application_status', 'Application Status'),
        ('job_match', 'Job Match'),
        ('message', 'Message'),
        ('system', 'System'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default='system')
    title = models.CharField(max_length=255)
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    action_url = models.URLField(max_length=500, blank=True, null=True)
    
    # Status flags
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    is_email_sent = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'notifications'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
        ]
    
    def __str__(self):
        return f"Notification for {self.user.email} - {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()