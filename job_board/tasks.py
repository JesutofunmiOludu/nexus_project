from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Application, User
from .recommendations import RecommendationEngine

@shared_task
def notify_employer_new_application(application_id):
    """
    Sends an email to the employer when a new application is received.
    """
    try:
        application = Application.objects.select_related('job__employer__user', 'applicant__freelancer_profile').get(id=application_id)
        job = application.job
        employer_email = job.employer.user.email
        applicant_name = application.applicant.get_full_name()
        
        subject = f"New Application for {job.title}"
        message = f"""
        Hello {job.employer.first_name},

        You have received a new application for the position: {job.title}.

        Applicant: {applicant_name}
        
        Log in to your dashboard to review the application.
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [employer_email],
            fail_silently=False,
        )
        return f"Notification sent to employer: {employer_email}"
        
    except Application.DoesNotExist:
        return f"Application {application_id} not found."
    except Exception as e:
        return f"Error sending notification: {str(e)}"

@shared_task
def notify_freelancer_application_status(application_id, status_update):
    """
    Sends an email to the freelancer when their application status changes (e.g., Accepted).
    """
    try:
        application = Application.objects.select_related('job__company', 'applicant').get(id=application_id)
        freelancer_email = application.applicant.email
        job_title = application.job.title
        company_name = application.job.company.name
        
        if status_update == 'accepted':
            subject = f"Congratulations! Your application for {job_title} was accepted"
            message = f"""
            Hello {application.applicant.first_name},

            Great news! Your application for {job_title} at {company_name} has been accepted.

            The employer will be in touch with next steps.
            """
        else:
             # Can extend for other statuses if needed
            return f"No email configured for status: {status_update}"

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [freelancer_email],
            fail_silently=False,
        )
        return f"Notification sent to freelancer: {freelancer_email}"

    except Application.DoesNotExist:
        return f"Application {application_id} not found."
    except Exception as e:
        return f"Error sending notification: {str(e)}"

@shared_task
def generate_user_recommendations(user_id):
    """
    Background task to generate job recommendations for a user.
    """
    try:
        user = User.objects.get(id=user_id)
        engine = RecommendationEngine()
        recommendations = engine.generate_recommendations(user)
        return f"Generated {len(recommendations)} recommendations for user {user.email}"
    except User.DoesNotExist:
        return f"User {user_id} not found"
    except Exception as e:
        return f"Error generating recommendations: {str(e)}"
