from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank

from .permissions import IsOwnerOrReadOnly, IsEmployer, IsFreelancer

from .models import (
    User, EmployerProfile, FreelancerProfile, Company, Category,
    Job, Application, Skill, UserSkill, JobSkill,
    Portfolio, WorkExperience, Education, Certification, FreelancerReview,
    JobRecommendation, SavedJob, JobView, Notification
)

from .serializers import (
    UserSerializer, UserRegistrationSerializer,
    EmployerProfileSerializer, EmployerProfileDetailSerializer,
    FreelancerProfileSerializer, FreelancerProfileDetailSerializer,
    CompanySerializer, CategorySerializer,
    JobListSerializer, JobDetailSerializer, JobCreateUpdateSerializer,
    ApplicationSerializer, SkillSerializer, UserSkillSerializer, JobSkillSerializer,
    PortfolioSerializer, WorkExperienceSerializer, EducationSerializer,
    CertificationSerializer, FreelancerReviewSerializer,
    JobRecommendationSerializer, SavedJobSerializer, JobViewSerializer,
    NotificationSerializer
)
from .tasks import notify_employer_new_application, notify_freelancer_application_status, generate_user_recommendations



# ============================================================================
# USER VIEWSETS
# ============================================================================

class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for User model."""
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsOwnerOrReadOnly]
    
    def get_permissions(self):
        """
        Allow unauthenticated users to register.
        """
        if self.action == 'create':
            return [permissions.AllowAny()]
        return super().get_permissions()

    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == 'create':
            return UserRegistrationSerializer
        return UserSerializer
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user profile."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class EmployerProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for Employer Profile."""
    
    queryset = EmployerProfile.objects.select_related('user', 'primary_company').all()
    serializer_class = EmployerProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    
    def get_serializer_class(self):
        """Return detailed serializer for retrieve action."""
        if self.action == 'retrieve':
            return EmployerProfileDetailSerializer
        return EmployerProfileSerializer
    
    def perform_create(self, serializer):
        """Automatically set the user field from the request."""
        serializer.save(user=self.request.user)


class FreelancerProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for Freelancer Profile."""
    
    queryset = FreelancerProfile.objects.select_related('user').prefetch_related(
        'skills', 'portfolio_items', 'work_experiences', 'education', 
        'certifications', 'reviews'
    ).all()
    serializer_class = FreelancerProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    
    def get_serializer_class(self):
        """Return detailed serializer for retrieve action."""
        if self.action == 'retrieve':
            return FreelancerProfileDetailSerializer
        return FreelancerProfileSerializer
    
    def perform_create(self, serializer):
        """Automatically set the user field from the request."""
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        """Update profile and regenerate recommendations."""
        serializer.save()
        generate_user_recommendations.delay(self.request.user.id)


# ============================================================================
# COMPANY & CATEGORY VIEWSETS
# ============================================================================

class CompanyViewSet(viewsets.ModelViewSet):
    """ViewSet for Company."""
    
    queryset = Company.objects.select_related('employer').all()
    serializer_class = CompanySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    
    def perform_create(self, serializer):
        """Automatically set the employer field from the user's profile."""
        try:
            employer_profile = self.request.user.employer_profile
            serializer.save(employer=employer_profile)
        except EmployerProfile.DoesNotExist:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("You must create an Employer Profile before creating a company.")

    @action(detail=True, methods=['get'])
    def jobs(self, request, pk=None):
        """Get all jobs for a company."""
        company = self.get_object()
        jobs = company.jobs.filter(status='published')
        serializer = JobListSerializer(jobs, many=True)
        return Response(serializer.data)


class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for Category."""
    
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    @action(detail=True, methods=['get'])
    def jobs(self, request, pk=None):
        """Get all jobs in a category."""
        category = self.get_object()
        jobs = category.jobs.filter(status='published')
        serializer = JobListSerializer(jobs, many=True)
        return Response(serializer.data)


# ============================================================================
# JOB & APPLICATION VIEWSETS
# ============================================================================

class JobViewSet(viewsets.ModelViewSet):
    """ViewSet for Job."""
    
    queryset = Job.objects.select_related('employer', 'company', 'category').all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    
    @method_decorator(cache_page(60 * 15)) # Cache for 15 minutes
    @method_decorator(vary_on_cookie)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return JobListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return JobCreateUpdateSerializer
        return JobDetailSerializer
    
    def get_permissions(self):
        """
        Custom permissions for specific actions.
        """
        if self.action in ['apply', 'save']:
            return [permissions.IsAuthenticated()]
        return super().get_permissions()
    
    def perform_create(self, serializer):
        """Automatically set the employer field."""
        try:
            employer_profile = self.request.user.employer_profile
            serializer.save(employer=employer_profile)
        except EmployerProfile.DoesNotExist:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("You must be an Employer to post jobs.")

    
    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()
        
        # Filter by status (default to published for list view)
        if self.action == 'list':
            queryset = queryset.filter(status='published')
        
        # PostgreSQL Full-Text Search
        search = self.request.query_params.get('search', None)
        if search:
            vector = SearchVector('title', weight='A') + \
                     SearchVector('description', weight='B') + \
                     SearchVector('requirements', weight='C')
            query = SearchQuery(search)
            queryset = queryset.annotate(
                rank=SearchRank(vector, query)
            ).filter(rank__gte=0.1).order_by('-rank')
        
        # Filter by location
        location = self.request.query_params.get('location', None)
        if location:
            queryset = queryset.filter(location__icontains=location)
        
        # Filter by job type
        job_type = self.request.query_params.get('job_type', None)
        if job_type:
            queryset = queryset.filter(job_type=job_type)
        
        # Filter by experience level
        experience_level = self.request.query_params.get('experience_level', None)
        if experience_level:
            queryset = queryset.filter(experience_level=experience_level)
        
        # Filter by remote
        is_remote = self.request.query_params.get('is_remote', None)
        if is_remote is not None:
            queryset = queryset.filter(is_remote=is_remote.lower() == 'true')
        
        # Filter by category
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category_id=category)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        """Apply for a job."""
        job = self.get_object()
        serializer = ApplicationSerializer(data={
            **request.data,
            'job': job.id,
            'applicant': request.user.id
        })
        if serializer.is_valid():
            application = serializer.save(applicant=request.user)
            # Trigger background notification
            notify_employer_new_application.delay(application.id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def save(self, request, pk=None):
        """Save/bookmark a job."""
        job = self.get_object()
        saved_job, created = SavedJob.objects.get_or_create(
            user=request.user,
            job=job,
            defaults={'notes': request.data.get('notes', '')}
        )
        serializer = SavedJobSerializer(saved_job)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class ApplicationViewSet(viewsets.ModelViewSet):
    """ViewSet for Application."""
    
    queryset = Application.objects.select_related('job', 'applicant').all()
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        """Send background notification on creation."""
        application = serializer.save()
        notify_employer_new_application.delay(application.id)

    def get_queryset(self):
        """Filter applications based on user role."""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update application status."""
        application = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(Application.STATUS_CHOICES):
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        application.status = new_status
        if 'rejection_reason' in request.data:
            application.rejection_reason = request.data['rejection_reason']
        application.save()
        
        # Trigger background notification for status change
        if new_status == 'accepted':
            notify_freelancer_application_status.delay(application.id, new_status)
        
        serializer = self.get_serializer(application)
        return Response(serializer.data)


# ============================================================================
# SKILL VIEWSETS
# ============================================================================

class SkillViewSet(viewsets.ModelViewSet):
    """ViewSet for Skill."""
    
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class UserSkillViewSet(viewsets.ModelViewSet):
    """ViewSet for User Skills."""
    
    queryset = UserSkill.objects.select_related('freelancer_profile', 'skill').all()
    serializer_class = UserSkillSerializer
    permission_classes = [permissions.IsAuthenticated]


class JobSkillViewSet(viewsets.ModelViewSet):
    """ViewSet for Job Skills."""
    
    queryset = JobSkill.objects.select_related('job', 'skill').all()
    serializer_class = JobSkillSerializer
    permission_classes = [permissions.IsAuthenticated]


# ============================================================================
# PORTFOLIO & EXPERIENCE VIEWSETS
# ============================================================================

class PortfolioViewSet(viewsets.ModelViewSet):
    """ViewSet for Portfolio."""
    
    queryset = Portfolio.objects.select_related('freelancer_profile').all()
    serializer_class = PortfolioSerializer
    permission_classes = [permissions.IsAuthenticated]


class WorkExperienceViewSet(viewsets.ModelViewSet):
    """ViewSet for Work Experience."""
    
    queryset = WorkExperience.objects.select_related('freelancer_profile').all()
    serializer_class = WorkExperienceSerializer
    permission_classes = [permissions.IsAuthenticated]


class EducationViewSet(viewsets.ModelViewSet):
    """ViewSet for Education."""
    
    queryset = Education.objects.select_related('freelancer_profile').all()
    serializer_class = EducationSerializer
    permission_classes = [permissions.IsAuthenticated]


class CertificationViewSet(viewsets.ModelViewSet):
    """ViewSet for Certification."""
    
    queryset = Certification.objects.select_related('freelancer_profile').all()
    serializer_class = CertificationSerializer
    permission_classes = [permissions.IsAuthenticated]


class FreelancerReviewViewSet(viewsets.ModelViewSet):
    """ViewSet for Freelancer Reviews."""
    
    queryset = FreelancerReview.objects.select_related(
        'freelancer_profile', 'reviewer', 'job'
    ).all()
    serializer_class = FreelancerReviewSerializer
    permission_classes = [permissions.IsAuthenticated]


# ============================================================================
# RECOMMENDATION & ANALYTICS VIEWSETS
# ============================================================================

class JobRecommendationViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Job Recommendations (Read-only)."""
    
    queryset = JobRecommendation.objects.select_related('user', 'job').all()
    serializer_class = JobRecommendationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get recommendations for current user."""
        queryset = super().get_queryset().filter(user=self.request.user)
        
        # If no recommendations exist, generate them on the fly
        if not queryset.exists():
            from .recommendations import RecommendationEngine
            engine = RecommendationEngine()
            engine.generate_recommendations(self.request.user)
            # Refetch
            queryset = super().get_queryset().filter(user=self.request.user)
            
        return queryset


class SavedJobViewSet(viewsets.ModelViewSet):
    """ViewSet for Saved Jobs."""
    
    queryset = SavedJob.objects.select_related('user', 'job').all()
    serializer_class = SavedJobSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get saved jobs for current user."""
        return super().get_queryset().filter(user=self.request.user)


class JobViewViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Job Views (Analytics - Read-only)."""
    
    queryset = JobView.objects.select_related('user', 'job').all()
    serializer_class = JobViewSerializer
    permission_classes = [permissions.IsAdminUser]


class NotificationViewSet(viewsets.ModelViewSet):
    """ViewSet for Notifications."""
    
    queryset = Notification.objects.select_related('user').all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get notifications for current user."""
        return super().get_queryset().filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark notification as read."""
        notification = self.get_object()
        notification.mark_as_read()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """Mark all notifications as read."""
        self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({'status': 'all notifications marked as read'})
