from rest_framework import serializers
from .models import (
    User, EmployerProfile, FreelancerProfile, Company, Category,
    Job, Application, Skill, UserSkill, JobSkill,
    Portfolio, WorkExperience, Education, Certification, FreelancerReview,
    JobRecommendation, SavedJob, JobView, Notification
)


# ============================================================================
# USER SERIALIZERS
# ============================================================================

class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'account_type', 'is_active', 
            'is_verified', 'is_email_verified', 'full_name',
            'created_at', 'updated_at', 'last_login'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_login']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def get_full_name(self, obj):
        """Get user's full name from profile."""
        return obj.get_full_name()
    
    def create(self, validated_data):
        """Create user with hashed password."""
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['email', 'password', 'password_confirm', 'role', 'account_type']
    
    def validate(self, data):
        """Validate password confirmation."""
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords do not match.")
        return data
    
    def create(self, validated_data):
        """Create user with hashed password."""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user


class EmployerProfileSerializer(serializers.ModelSerializer):
    """Serializer for Employer Profile."""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    company_name = serializers.CharField(source='primary_company.name', read_only=True, allow_null=True)
    
    class Meta:
        model = EmployerProfile
        fields = [
            'id', 'user', 'user_email', 'first_name', 'last_name', 'phone',
            'position_title', 'bio', 'profile_picture_url', 'linkedin_url',
            'primary_company', 'company_name', 'can_post_jobs', 
            'verification_status', 'verified_at', 'jobs_posted_count',
            'active_jobs_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'verified_at', 'jobs_posted_count', 
                           'active_jobs_count', 'created_at', 'updated_at']


class FreelancerProfileSerializer(serializers.ModelSerializer):
    """Serializer for Freelancer Profile."""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = FreelancerProfile
        fields = [
            'id', 'user', 'user_email', 'first_name', 'last_name', 'phone', 'bio',
            'profile_picture_url', 'resume_url', 'portfolio_url', 
            'linkedin_url', 'github_url', 'service_categories',
            'preferred_project_types', 'preferred_locations',
            'hourly_rate_min', 'hourly_rate_max', 'rate_currency',
            'is_available', 'is_open_to_remote', 'availability_hours',
            'time_zones', 'projects_completed', 'average_rating',
            'total_reviews', 'total_experience_years', 'payment_methods',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'projects_completed', 'average_rating',
                           'total_reviews', 'created_at', 'updated_at']


# ============================================================================
# COMPANY & CATEGORY SERIALIZERS
# ============================================================================

class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category."""
    
    parent_name = serializers.CharField(source='parent.name', read_only=True, allow_null=True)
    subcategories_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'parent', 'parent_name',
            'job_count', 'icon_url', 'subcategories_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'job_count', 'created_at', 'updated_at']
    
    def get_subcategories_count(self, obj):
        """Get count of subcategories."""
        return obj.subcategories.count()


class CompanySerializer(serializers.ModelSerializer):
    """Serializer for Company."""
    
    employer_name = serializers.SerializerMethodField()
    jobs_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Company
        fields = [
            'id', 'employer', 'employer_name', 'name', 'description',
            'logo_url', 'cover_image_url', 'website', 'email', 'phone',
            'industry', 'size', 'headquarters_location', 'office_locations',
            'founded_date', 'employee_count', 'culture_description',
            'benefits', 'social_media_links', 'is_verified', 'verified_at',
            'jobs_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'employer', 'verified_at', 'created_at', 'updated_at']
    
    def get_employer_name(self, obj):
        """Get employer's full name."""
        return f"{obj.employer.first_name} {obj.employer.last_name}"
    
    def get_jobs_count(self, obj):
        """Get count of jobs posted by this company."""
        return obj.jobs.filter(status='published').count()


# ============================================================================
# JOB & APPLICATION SERIALIZERS
# ============================================================================

class JobListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for job listings."""
    
    company_name = serializers.CharField(source='company.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Job
        fields = [
            'id', 'title', 'company_name', 'category_name', 'location',
            'is_remote', 'job_type', 'experience_level', 'salary_min',
            'salary_max', 'salary_currency', 'status', 'view_count',
            'application_count', 'published_at', 'created_at'
        ]
        read_only_fields = ['id', 'view_count', 'application_count', 
                           'published_at', 'created_at']


class JobDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for job details."""
    
    company = CompanySerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    employer_name = serializers.SerializerMethodField()
    required_skills = serializers.SerializerMethodField()
    
    class Meta:
        model = Job
        fields = [
            'id', 'employer', 'employer_name', 'company', 'category',
            'title', 'description', 'requirements', 'responsibilities',
            'benefits', 'location', 'is_remote', 'job_type',
            'experience_level', 'salary_min', 'salary_max',
            'salary_currency', 'salary_period', 'status',
            'view_count', 'application_count', 'save_count',
            'required_skills', 'published_at', 'expires_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'view_count', 'application_count',
                           'save_count', 'published_at', 'created_at', 'updated_at']
    
    def get_employer_name(self, obj):
        """Get employer's full name."""
        return f"{obj.employer.first_name} {obj.employer.last_name}"
    
    def get_required_skills(self, obj):
        """Get list of required skills."""
        skills = obj.required_skills.select_related('skill').all()
        return [{
            'name': js.skill.name,
            'proficiency_level': js.proficiency_level,
            'is_required': js.is_required,
            'years_required': js.years_required
        } for js in skills]


class JobCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating jobs."""
    
    class Meta:
        model = Job
        fields = [
            'id', 'company', 'category', 'title', 'description', 'requirements',
            'responsibilities', 'benefits', 'location', 'is_remote',
            'job_type', 'experience_level', 'salary_min', 'salary_max',
            'salary_currency', 'salary_period', 'status', 'expires_at'
        ]
        read_only_fields = ['id']
    
    def validate(self, data):
        """Validate job data."""
        if data.get('salary_min') and data.get('salary_max'):
            if data['salary_min'] > data['salary_max']:
                raise serializers.ValidationError(
                    "Minimum salary cannot be greater than maximum salary."
                )
        return data


class ApplicationSerializer(serializers.ModelSerializer):
    """Serializer for job applications."""
    
    job_title = serializers.CharField(source='job.title', read_only=True)
    applicant_name = serializers.SerializerMethodField()
    applicant_email = serializers.EmailField(source='applicant.email', read_only=True)
    
    class Meta:
        model = Application
        fields = [
            'id', 'job', 'job_title', 'applicant', 'applicant_name',
            'applicant_email', 'cover_letter', 'resume_url', 'answers',
            'status', 'rejection_reason', 'rating', 'internal_notes',
            'applied_at', 'reviewed_at', 'status_changed_at', 'updated_at'
        ]
        read_only_fields = ['id', 'applicant', 'applied_at', 'reviewed_at',
                           'status_changed_at', 'updated_at']
    
    def get_applicant_name(self, obj):
        """Get applicant's full name."""
        return obj.applicant.get_full_name()


# ============================================================================
# SKILL SERIALIZERS
# ============================================================================

class SkillSerializer(serializers.ModelSerializer):
    """Serializer for Skill."""
    
    class Meta:
        model = Skill
        fields = ['id', 'name', 'slug', 'description', 'category', 
                 'popularity_score', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserSkillSerializer(serializers.ModelSerializer):
    """Serializer for User Skills."""
    
    skill_name = serializers.CharField(source='skill.name', read_only=True)
    skill_category = serializers.CharField(source='skill.category', read_only=True)
    
    class Meta:
        model = UserSkill
        fields = [
            'id', 'freelancer_profile', 'skill', 'skill_name', 'skill_category',
            'proficiency_level', 'years_of_experience', 'last_used', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class JobSkillSerializer(serializers.ModelSerializer):
    """Serializer for Job Skills."""
    
    skill_name = serializers.CharField(source='skill.name', read_only=True)
    
    class Meta:
        model = JobSkill
        fields = [
            'id', 'job', 'skill', 'skill_name', 'proficiency_level',
            'is_required', 'years_required'
        ]
        read_only_fields = ['id']


# ============================================================================
# PORTFOLIO & EXPERIENCE SERIALIZERS
# ============================================================================

class PortfolioSerializer(serializers.ModelSerializer):
    """Serializer for Portfolio items."""
    
    class Meta:
        model = Portfolio
        fields = [
            'id', 'freelancer_profile', 'title', 'description', 'project_url',
            'thumbnail_url', 'images', 'technologies_used', 'project_date',
            'client_name', 'project_type', 'is_featured', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class WorkExperienceSerializer(serializers.ModelSerializer):
    """Serializer for Work Experience."""
    
    class Meta:
        model = WorkExperience
        fields = [
            'id', 'freelancer_profile', 'company_name', 'job_title',
            'description', 'responsibilities', 'location', 'start_date',
            'end_date', 'is_current', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def validate(self, data):
        """Validate work experience dates."""
        if not data.get('is_current') and not data.get('end_date'):
            raise serializers.ValidationError(
                "End date is required if position is not current."
            )
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError(
                    "Start date cannot be after end date."
                )
        return data


class EducationSerializer(serializers.ModelSerializer):
    """Serializer for Education."""
    
    class Meta:
        model = Education
        fields = [
            'id', 'freelancer_profile', 'institution', 'degree',
            'field_of_study', 'description', 'start_date', 'end_date',
            'is_current', 'gpa', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class CertificationSerializer(serializers.ModelSerializer):
    """Serializer for Certifications."""
    
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = Certification
        fields = [
            'id', 'freelancer_profile', 'name', 'issuing_organization',
            'credential_id', 'credential_url', 'issue_date', 'expiry_date',
            'does_not_expire', 'is_expired', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_is_expired(self, obj):
        """Check if certification is expired."""
        if obj.does_not_expire:
            return False
        if obj.expiry_date:
            from django.utils import timezone
            return obj.expiry_date < timezone.now().date()
        return False


class FreelancerReviewSerializer(serializers.ModelSerializer):
    """Serializer for Freelancer Reviews."""
    
    reviewer_name = serializers.SerializerMethodField()
    job_title = serializers.CharField(source='job.title', read_only=True, allow_null=True)
    
    class Meta:
        model = FreelancerReview
        fields = [
            'id', 'freelancer_profile', 'reviewer', 'reviewer_name',
            'job', 'job_title', 'rating', 'review_text',
            'rating_breakdown', 'created_at'
        ]
        read_only_fields = ['id', 'reviewer', 'created_at']
    
    def get_reviewer_name(self, obj):
        """Get reviewer's full name."""
        return obj.reviewer.get_full_name()


# ============================================================================
# RECOMMENDATION & ANALYTICS SERIALIZERS
# ============================================================================

class JobRecommendationSerializer(serializers.ModelSerializer):
    """Serializer for Job Recommendations."""
    
    job = JobListSerializer(read_only=True)
    
    class Meta:
        model = JobRecommendation
        fields = [
            'id', 'user', 'job', 'score', 'reason', 'metadata',
            'algorithm_type', 'is_viewed', 'is_clicked', 'is_applied',
            'created_at', 'expires_at'
        ]
        read_only_fields = ['id', 'created_at']


class SavedJobSerializer(serializers.ModelSerializer):
    """Serializer for Saved Jobs."""
    
    job = JobListSerializer(read_only=True)
    
    class Meta:
        model = SavedJob
        fields = ['id', 'user', 'job', 'notes', 'tags', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class JobViewSerializer(serializers.ModelSerializer):
    """Serializer for Job Views (Analytics)."""
    
    class Meta:
        model = JobView
        fields = [
            'id', 'user', 'job', 'ip_address', 'user_agent',
            'duration_seconds', 'referrer', 'viewed_at'
        ]
        read_only_fields = ['id', 'viewed_at']


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notifications."""
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'notification_type', 'title', 'message',
            'data', 'action_url', 'is_read', 'is_sent', 'is_email_sent',
            'created_at', 'read_at', 'sent_at'
        ]
        read_only_fields = ['id', 'user', 'is_sent', 'is_email_sent',
                           'created_at', 'read_at', 'sent_at']


# ============================================================================
# NESTED/COMPOSITE SERIALIZERS
# ============================================================================

class FreelancerProfileDetailSerializer(FreelancerProfileSerializer):
    """Detailed freelancer profile with nested data."""
    
    skills = UserSkillSerializer(many=True, read_only=True)
    portfolio_items = PortfolioSerializer(many=True, read_only=True)
    work_experiences = WorkExperienceSerializer(many=True, read_only=True)
    education = EducationSerializer(many=True, read_only=True)
    certifications = CertificationSerializer(many=True, read_only=True)
    reviews = FreelancerReviewSerializer(many=True, read_only=True)
    
    class Meta(FreelancerProfileSerializer.Meta):
        fields = FreelancerProfileSerializer.Meta.fields + [
            'skills', 'portfolio_items', 'work_experiences',
            'education', 'certifications', 'reviews'
        ]


class EmployerProfileDetailSerializer(EmployerProfileSerializer):
    """Detailed employer profile with nested data."""
    
    companies = CompanySerializer(many=True, read_only=True)
    jobs = JobListSerializer(many=True, read_only=True)
    
    class Meta(EmployerProfileSerializer.Meta):
        fields = EmployerProfileSerializer.Meta.fields + ['companies', 'jobs']