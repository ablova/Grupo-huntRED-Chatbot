"""
🚀 GhuntRED-v2 ML Tasks
Background ML processing tasks
"""

import logging
from celery import shared_task
from django.contrib.auth import get_user_model
from apps.candidates.models import CandidateProfile, CandidateAssessment
from apps.jobs.models import JobApplication
from ml import ml_factory

logger = logging.getLogger('ml.tasks')
User = get_user_model()

@shared_task(bind=True, max_retries=3)
def analyze_candidate_profile(self, candidate_id):
    """Analyze candidate profile with GenIA and AURA"""
    try:
        candidate = CandidateProfile.objects.get(id=candidate_id)
        
        # Prepare candidate data
        candidate_data = {
            'professional_summary': candidate.professional_summary,
            'years_of_experience': candidate.years_of_experience,
            'current_role': candidate.current_role,
            'skills': [{'name': skill.skill.name} for skill in candidate.skills.all()],
            'work_experience': [
                {
                    'company': exp.company,
                    'position': exp.position,
                    'description': exp.description,
                    'start_date': exp.start_date.isoformat() if exp.start_date else '',
                    'end_date': exp.end_date.isoformat() if exp.end_date else '',
                }
                for exp in candidate.work_experience.all()
            ],
        }
        
        # Run ML analysis
        analysis_results = ml_factory.analyze_candidate(candidate_data, "full")
        
        # Save GenIA assessment
        if 'genia_score' in analysis_results:
            CandidateAssessment.objects.update_or_create(
                candidate=candidate,
                assessment_type='genia',
                defaults={
                    'score': analysis_results['genia_score'],
                    'results': analysis_results.get('skills_analysis', {}),
                    'model_version': '2.0.0',
                }
            )
        
        # Save AURA assessment
        if 'aura_score' in analysis_results:
            CandidateAssessment.objects.update_or_create(
                candidate=candidate,
                assessment_type='aura',
                defaults={
                    'score': analysis_results['aura_score'],
                    'results': analysis_results.get('personality_analysis', {}),
                    'model_version': '2.0.0',
                }
            )
        
        # Update candidate profile with ML results
        candidate.skills_assessment = analysis_results.get('skills_analysis', {})
        candidate.personality_score = analysis_results.get('personality_analysis', {})
        candidate.compatibility_score = (
            analysis_results.get('genia_score', 0) + 
            analysis_results.get('aura_score', 0)
        ) / 2
        candidate.save()
        
        logger.info(f"✅ Completed ML analysis for candidate {candidate_id}")
        return analysis_results
        
    except CandidateProfile.DoesNotExist:
        logger.error(f"❌ Candidate {candidate_id} not found")
        raise
        
    except Exception as e:
        logger.error(f"❌ ML analysis failed for candidate {candidate_id}: {e}")
        # Retry with exponential backoff
        raise self.retry(countdown=60 * (2 ** self.request.retries))

@shared_task(bind=True, max_retries=3)
def analyze_job_application(self, application_id):
    """Analyze job application match score"""
    try:
        application = JobApplication.objects.get(id=application_id)
        
        # Prepare candidate data
        candidate_data = {
            'skills': [{'name': skill.skill.name} for skill in application.candidate.skills.all()],
            'years_of_experience': application.candidate.years_of_experience,
            'expected_salary_min': application.candidate.expected_salary_min,
            'work_type_preference': application.candidate.work_type_preference,
        }
        
        # Prepare job data
        job_data = {
            'required_skills': [{'name': skill.skill.name} for skill in application.job.required_skills.all()],
            'salary_min': application.job.salary_min,
            'salary_max': application.job.salary_max,
            'remote_work': application.job.remote_work,
        }
        
        # Run matching analysis
        matching_engine = ml_factory.get_analyzer('matching_engine')
        match_results = matching_engine.analyze(candidate_data, job_data)
        
        # Update application with match scores
        application.overall_match_score = match_results['score']
        application.skills_match = match_results['match_details']
        application.save()
        
        logger.info(f"✅ Completed match analysis for application {application_id}")
        return match_results
        
    except JobApplication.DoesNotExist:
        logger.error(f"❌ Application {application_id} not found")
        raise
        
    except Exception as e:
        logger.error(f"❌ Match analysis failed for application {application_id}: {e}")
        raise self.retry(countdown=60 * (2 ** self.request.retries))

@shared_task
def process_pending_candidate_analysis():
    """Process pending candidate analysis"""
    try:
        # Find candidates without recent analysis
        candidates_to_analyze = CandidateProfile.objects.filter(
            assessments__isnull=True
        )[:10]  # Process 10 at a time
        
        for candidate in candidates_to_analyze:
            analyze_candidate_profile.delay(candidate.id)
        
        logger.info(f"✅ Queued {len(candidates_to_analyze)} candidates for analysis")
        
    except Exception as e:
        logger.error(f"❌ Failed to process pending candidate analysis: {e}")

@shared_task
def bulk_analyze_applications(job_id):
    """Bulk analyze all applications for a job"""
    try:
        applications = JobApplication.objects.filter(
            job_id=job_id,
            overall_match_score__isnull=True
        )
        
        for application in applications:
            analyze_job_application.delay(application.id)
        
        logger.info(f"✅ Queued {len(applications)} applications for analysis")
        
    except Exception as e:
        logger.error(f"❌ Failed to bulk analyze applications for job {job_id}: {e}")