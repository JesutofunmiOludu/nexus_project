from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from django.urls import reverse
from .models import User, EmployerProfile, FreelancerProfile, Company, Category, Job, Application, Skill, JobRecommendation, JobSkill, UserSkill

class JobBoardTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create Users
        self.employer_user = User.objects.create_user(email='employer@example.com', password='password123', role='employer')
        self.freelancer_user = User.objects.create_user(email='freelancer@example.com', password='password123', role='freelancer')
        self.admin_user = User.objects.create_superuser(email='admin@example.com', password='password123')
        
        # Create Profiles
        self.employer_profile = EmployerProfile.objects.create(
            user=self.employer_user, 
            first_name='John', 
            last_name='Doe'
        )
        self.freelancer_profile = FreelancerProfile.objects.create(
            user=self.freelancer_user, 
            first_name='Jane', 
            last_name='Smith'
        )
        
        # Create Company
        self.company = Company.objects.create(
            employer=self.employer_profile,
            name='Tech Corp',
            description='A great tech company'
        )
        self.employer_profile.primary_company = self.company
        self.employer_profile.save()
        
        # Create Category
        self.category = Category.objects.create(name='Engineering', slug='engineering')
        
        # Create Skill
        self.skill_python = Skill.objects.create(name='Python', slug='python')

    def test_user_authentication(self):
        # Test Login
        url = reverse('token_obtain_pair')
        data = {
            'email': 'employer@example.com',
            'password': 'password123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.token = response.data['access']

    def test_create_job(self):
        # Authenticate as Employer
        self.client.force_authenticate(user=self.employer_user)
        
        url = reverse('job-list')
        data = {
            'title': 'Senior Python Developer',
            'description': 'We need a python expert',
            'company': self.company.id,
            'category': self.category.id,
            'location': 'Remote',
            'job_type': 'full_time',
            'salary_min': 100000,
            'salary_max': 150000,
            'status': 'published'
        }
        response = self.client.post(url, data, format='json')
        if response.status_code != 201:
             print(f"Create Job Error: {response.status_code} - {response.data}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Job.objects.count(), 1)
        self.job_id = response.data['id']

    from unittest.mock import patch
    @patch('job_board.views.notify_employer_new_application.delay')
    def test_apply_for_job(self, mock_notify):
        # Setup Job first
        job = Job.objects.create(
            employer=self.employer_profile,
            company=self.company,
            category=self.category,
            title='Python Dev',
            description='Code python',
            location='Remote',
            status='published'
        )
        
        # Authenticate as Freelancer
        self.client.force_authenticate(user=self.freelancer_user)
        
        url = reverse('job-apply', args=[job.id])
        data = {
            'cover_letter': 'I am great at Python'
        }
        response = self.client.post(url, data, format='json')
        if response.status_code != 201:
            print(f"Apply Job Error: {response.status_code} - {response.data}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Application.objects.count(), 1)
        mock_notify.assert_called_once()

    def test_recommendation_integration(self):
        # 1. Setup Job with Python skill
        job = Job.objects.create(
            employer=self.employer_profile,
            company=self.company,
            category=self.category,
            title='Python Dev',
            description='Code python',
            location='Remote',
            status='published',
            job_type='full_time'
        )
        JobSkill.objects.create(job=job, skill=self.skill_python, is_required=True)
        
        # 2. Setup Freelancer with Python skill
        UserSkill.objects.create(freelancer_profile=self.freelancer_profile, skill=self.skill_python)
        
        # 3. Authenticate and request recommendations
        self.client.force_authenticate(user=self.freelancer_user)
        url = reverse('job-recommendation-list')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should have generated 1 recommendation
        # Handle pagination
        if isinstance(response.data, dict) and 'results' in response.data:
            results = response.data['results']
        else:
            results = response.data
            
        self.assertEqual(len(results), 1)
        # Compatibility check: Serializer returns nested job object
        actual_job_id = results[0]['job']['id'] if isinstance(results[0]['job'], dict) else results[0]['job']
        self.assertEqual(str(actual_job_id), str(job.id))
