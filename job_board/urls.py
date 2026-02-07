from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from . import views

# Create a router and register our viewsets
router = DefaultRouter()

# User & Profile ViewSets
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'employer-profiles', views.EmployerProfileViewSet, basename='employer-profile')
router.register(r'freelancer-profiles', views.FreelancerProfileViewSet, basename='freelancer-profile')

# Company & Category ViewSets
router.register(r'companies', views.CompanyViewSet, basename='company')
router.register(r'categories', views.CategoryViewSet, basename='category')

# Job & Application ViewSets
router.register(r'jobs', views.JobViewSet, basename='job')
router.register(r'applications', views.ApplicationViewSet, basename='application')

# Skill ViewSets
router.register(r'skills', views.SkillViewSet, basename='skill')
router.register(r'user-skills', views.UserSkillViewSet, basename='user-skill')
router.register(r'job-skills', views.JobSkillViewSet, basename='job-skill')

# Portfolio & Experience ViewSets
router.register(r'portfolios', views.PortfolioViewSet, basename='portfolio')
router.register(r'work-experiences', views.WorkExperienceViewSet, basename='work-experience')
router.register(r'education', views.EducationViewSet, basename='education')
router.register(r'certifications', views.CertificationViewSet, basename='certification')
router.register(r'freelancer-reviews', views.FreelancerReviewViewSet, basename='freelancer-review')

# Recommendation & Analytics ViewSets
router.register(r'job-recommendations', views.JobRecommendationViewSet, basename='job-recommendation')
router.register(r'saved-jobs', views.SavedJobViewSet, basename='saved-job')
router.register(r'job-views', views.JobViewViewSet, basename='job-view')
router.register(r'notifications', views.NotificationViewSet, basename='notification')

# URL patterns
urlpatterns = [
    # JWT Authentication endpoints
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # API routes
    path('api/', include(router.urls)),
]
