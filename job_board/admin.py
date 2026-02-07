from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, EmployerProfile, FreelancerProfile, Company, Category,
    Job, Application, Skill, UserSkill, JobSkill,
    Portfolio, WorkExperience, Education, Certification, FreelancerReview,
    JobRecommendation, SavedJob, JobView, Notification
)


# ============================================================================
# USER ADMIN
# ============================================================================

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin."""
    
    list_display = ['email', 'role', 'is_active', 'is_verified', 'is_email_verified', 'created_at']
    list_filter = ['role', 'is_active', 'is_verified', 'is_email_verified', 'is_staff']
    search_fields = ['email']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Role & Type', {'fields': ('role', 'account_type')}),
        ('Status', {'fields': ('is_active', 'is_verified', 'is_email_verified', 'is_staff', 'is_superuser')}),
        ('Permissions', {'fields': ('groups', 'user_permissions')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at', 'last_login')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role', 'account_type'),
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'last_login']


# ============================================================================
# PROFILE ADMIN
# ============================================================================

@admin.register(EmployerProfile)
class EmployerProfileAdmin(admin.ModelAdmin):
    """Employer Profile admin."""
    
    list_display = ['user', 'first_name', 'last_name', 'verification_status', 'can_post_jobs', 'jobs_posted_count', 'active_jobs_count']
    list_filter = ['verification_status', 'can_post_jobs']
    search_fields = ['user__email', 'first_name', 'last_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone', 'position_title', 'bio')}),
        ('Links', {'fields': ('profile_picture_url', 'linkedin_url')}),
        ('Company', {'fields': ('primary_company',)}),
        ('Verification', {'fields': ('verification_status', 'verified_at', 'can_post_jobs')}),
        ('Statistics', {'fields': ('jobs_posted_count', 'active_jobs_count')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(FreelancerProfile)
class FreelancerProfileAdmin(admin.ModelAdmin):
    """Freelancer Profile admin."""
    
    list_display = ['user', 'first_name', 'last_name', 'is_available', 'average_rating', 'total_reviews', 'projects_completed']
    list_filter = ['is_available', 'is_open_to_remote']
    search_fields = ['user__email', 'first_name', 'last_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone', 'bio')}),
        ('Links', {'fields': ('profile_picture_url', 'resume_url', 'portfolio_url', 'linkedin_url', 'github_url')}),
        ('Preferences', {'fields': ('service_categories', 'preferred_project_types', 'preferred_locations')}),
        ('Rate', {'fields': ('hourly_rate_min', 'hourly_rate_max', 'rate_currency')}),
        ('Availability', {'fields': ('is_available', 'is_open_to_remote', 'availability_hours', 'time_zones')}),
        ('Statistics', {'fields': ('projects_completed', 'average_rating', 'total_reviews', 'total_experience_years')}),
        ('Payment', {'fields': ('payment_methods',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


# ============================================================================
# COMPANY & CATEGORY ADMIN
# ============================================================================

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """Company admin."""
    
    list_display = ['name', 'employer', 'industry', 'size', 'is_verified', 'created_at']
    list_filter = ['is_verified', 'industry', 'size']
    search_fields = ['name', 'employer__user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Info', {'fields': ('employer', 'name', 'description')}),
        ('Images', {'fields': ('logo_url', 'cover_image_url')}),
        ('Contact', {'fields': ('website', 'email', 'phone')}),
        ('Details', {'fields': ('industry', 'size', 'headquarters_location', 'office_locations', 'founded_date', 'employee_count')}),
        ('Culture', {'fields': ('culture_description', 'benefits', 'social_media_links')}),
        ('Verification', {'fields': ('is_verified', 'verified_at')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Category admin."""
    
    list_display = ['name', 'slug', 'parent', 'job_count', 'created_at']
    list_filter = ['parent']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']


# ============================================================================
# JOB & APPLICATION ADMIN
# ============================================================================

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    """Job admin."""
    
    list_display = ['title', 'company', 'employer', 'status', 'job_type', 'experience_level', 'view_count', 'application_count', 'published_at']
    list_filter = ['status', 'job_type', 'experience_level', 'is_remote']
    search_fields = ['title', 'company__name', 'employer__user__email', 'location']
    readonly_fields = ['view_count', 'application_count', 'save_count', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Info', {'fields': ('employer', 'company', 'category', 'title', 'description')}),
        ('Details', {'fields': ('requirements', 'responsibilities', 'benefits')}),
        ('Location', {'fields': ('location', 'is_remote')}),
        ('Type & Level', {'fields': ('job_type', 'experience_level')}),
        ('Salary', {'fields': ('salary_min', 'salary_max', 'salary_currency', 'salary_period')}),
        ('Status', {'fields': ('status',)}),
        ('Statistics', {'fields': ('view_count', 'application_count', 'save_count')}),
        ('Dates', {'fields': ('published_at', 'expires_at')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    """Application admin."""
    
    list_display = ['applicant', 'job', 'status', 'rating', 'applied_at', 'status_changed_at']
    list_filter = ['status', 'rating']
    search_fields = ['applicant__email', 'job__title']
    readonly_fields = ['applied_at', 'reviewed_at', 'status_changed_at', 'updated_at']
    date_hierarchy = 'applied_at'
    
    fieldsets = (
        ('Application', {'fields': ('job', 'applicant')}),
        ('Details', {'fields': ('cover_letter', 'resume_url', 'answers')}),
        ('Status', {'fields': ('status', 'rejection_reason')}),
        ('Employer Notes', {'fields': ('rating', 'internal_notes')}),
        ('Timestamps', {'fields': ('applied_at', 'reviewed_at', 'status_changed_at', 'updated_at')}),
    )


# ============================================================================
# SKILL ADMIN
# ============================================================================

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    """Skill admin."""
    
    list_display = ['name', 'slug', 'category', 'popularity_score', 'created_at']
    list_filter = ['category']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at']


@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    """User Skill admin."""
    
    list_display = ['freelancer_profile', 'skill', 'proficiency_level', 'years_of_experience', 'last_used']
    list_filter = ['proficiency_level']
    search_fields = ['freelancer_profile__user__email', 'skill__name']
    readonly_fields = ['created_at']


@admin.register(JobSkill)
class JobSkillAdmin(admin.ModelAdmin):
    """Job Skill admin."""
    
    list_display = ['job', 'skill', 'proficiency_level', 'is_required', 'years_required']
    list_filter = ['proficiency_level', 'is_required']
    search_fields = ['job__title', 'skill__name']


# ============================================================================
# PORTFOLIO & EXPERIENCE ADMIN
# ============================================================================

@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    """Portfolio admin."""
    
    list_display = ['freelancer_profile', 'title', 'project_type', 'is_featured', 'project_date', 'created_at']
    list_filter = ['is_featured', 'project_type']
    search_fields = ['freelancer_profile__user__email', 'title', 'client_name']
    readonly_fields = ['created_at']


@admin.register(WorkExperience)
class WorkExperienceAdmin(admin.ModelAdmin):
    """Work Experience admin."""
    
    list_display = ['freelancer_profile', 'job_title', 'company_name', 'is_current', 'start_date', 'end_date']
    list_filter = ['is_current']
    search_fields = ['freelancer_profile__user__email', 'job_title', 'company_name']
    readonly_fields = ['created_at']


@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    """Education admin."""
    
    list_display = ['freelancer_profile', 'degree', 'institution', 'field_of_study', 'is_current', 'start_date', 'end_date']
    list_filter = ['is_current']
    search_fields = ['freelancer_profile__user__email', 'institution', 'degree']
    readonly_fields = ['created_at']


@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    """Certification admin."""
    
    list_display = ['freelancer_profile', 'name', 'issuing_organization', 'issue_date', 'expiry_date', 'does_not_expire']
    list_filter = ['does_not_expire']
    search_fields = ['freelancer_profile__user__email', 'name', 'issuing_organization']
    readonly_fields = ['created_at']


@admin.register(FreelancerReview)
class FreelancerReviewAdmin(admin.ModelAdmin):
    """Freelancer Review admin."""
    
    list_display = ['freelancer_profile', 'reviewer', 'rating', 'job', 'created_at']
    list_filter = ['rating']
    search_fields = ['freelancer_profile__user__email', 'reviewer__email']
    readonly_fields = ['created_at']


# ============================================================================
# RECOMMENDATION & ANALYTICS ADMIN
# ============================================================================

@admin.register(JobRecommendation)
class JobRecommendationAdmin(admin.ModelAdmin):
    """Job Recommendation admin."""
    
    list_display = ['user', 'job', 'score', 'algorithm_type', 'is_viewed', 'is_clicked', 'is_applied', 'created_at']
    list_filter = ['algorithm_type', 'is_viewed', 'is_clicked', 'is_applied']
    search_fields = ['user__email', 'job__title']
    readonly_fields = ['created_at']


@admin.register(SavedJob)
class SavedJobAdmin(admin.ModelAdmin):
    """Saved Job admin."""
    
    list_display = ['user', 'job', 'created_at']
    search_fields = ['user__email', 'job__title']
    readonly_fields = ['created_at']


@admin.register(JobView)
class JobViewAdmin(admin.ModelAdmin):
    """Job View admin."""
    
    list_display = ['user', 'job', 'ip_address', 'duration_seconds', 'viewed_at']
    search_fields = ['user__email', 'job__title', 'ip_address']
    readonly_fields = ['viewed_at']
    date_hierarchy = 'viewed_at'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Notification admin."""
    
    list_display = ['user', 'notification_type', 'title', 'is_read', 'is_sent', 'is_email_sent', 'created_at']
    list_filter = ['notification_type', 'is_read', 'is_sent', 'is_email_sent']
    search_fields = ['user__email', 'title', 'message']
    readonly_fields = ['created_at', 'read_at', 'sent_at']
    date_hierarchy = 'created_at'
