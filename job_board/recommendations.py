from .models import Job, FreelancerProfile, UserSkill, JobSkill, JobRecommendation

class RecommendationEngine:
    def __init__(self):
        self.weights = {
            'skills': 0.6,
            'location': 0.2,
            'job_type': 0.2
        }

    def calculate_score(self, freelancer_profile, job):
        score = 0.0
        
        # 1. Skills Match (60%)
        score += self._calculate_skills_score(freelancer_profile, job) * self.weights['skills']
        
        # 2. Location Match (20%)
        score += self._calculate_location_score(freelancer_profile, job) * self.weights['location']
        
        # 3. Job Type Match (20%)
        score += self._calculate_type_score(freelancer_profile, job) * self.weights['job_type']
        
        return round(score, 2)

    def _calculate_skills_score(self, profile, job):
        job_skills = set(job.required_skills.values_list('skill__name', flat=True))
        if not job_skills:
            return 1.0  # If no skills required, anyone is a match
            
        user_skills = set(profile.skills.values_list('skill__name', flat=True))
        if not user_skills:
            return 0.0
            
        matching_skills = user_skills.intersection(job_skills)
        return len(matching_skills) / len(job_skills)

    def _calculate_location_score(self, profile, job):
        if not profile.preferred_locations:
            # If user has no preference but is open to remote, and job is remote -> mismatch? 
            # Let's assume neutral if no prefs, 0.5
            return 0.5
            
        # Check if job location is in preferred locations
        # Simple string matching for now (e.g. "San Francisco" in ["San Francisco, CA"])
        job_loc = job.location.lower()
        for loc in profile.preferred_locations:
            if loc.lower() in job_loc or job_loc in loc.lower():
                return 1.0
                
        # Check remote
        if job.is_remote and profile.is_open_to_remote:
            return 1.0
            
        return 0.0

    def _calculate_type_score(self, profile, job):
        # Match job type (full_time, etc)
        # preferred_project_types is a JSON list in profile
        if not profile.preferred_project_types:
            return 0.5
            
        if job.job_type in profile.preferred_project_types:
            return 1.0
            
        return 0.0

    def generate_recommendations(self, user, limit=10):
        try:
            profile = user.freelancer_profile
        except FreelancerProfile.DoesNotExist:
            return []

        # Get all published jobs excluding ones applied to
        applied_job_ids = user.applications.values_list('job_id', flat=True)
        candidate_jobs = Job.objects.filter(status='published').exclude(id__in=applied_job_ids)
        
        recommendations = []
        for job in candidate_jobs:
            score = self.calculate_score(profile, job)
            if score > 0.1:  # Threshold
                recommendations.append(
                    JobRecommendation(
                        user=user,
                        job=job,
                        score=score,
                        algorithm_type='content_based',
                        reason=f"Matched based on skills and preferences (Score: {int(score*100)}%)"
                    )
                )
        
        # sort by score desc
        recommendations.sort(key=lambda x: x.score, reverse=True)
        
        # Save top N
        top_recs = recommendations[:limit]
        
        # Clear old content-based recommendations
        JobRecommendation.objects.filter(user=user, algorithm_type='content_based').delete()
        
        # Bulk create new ones
        JobRecommendation.objects.bulk_create(top_recs)
        
        return top_recs
