"""
Views for handling assessment-related requests in the chatbot.
"""

import json
import logging
from typing import Dict, Any
from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from asgiref.sync import sync_to_async

from app.models import BusinessUnit
from app.ats.chatbot.handlers.assessment_handlers import AssessmentFactory

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
async def start_assessment(request: HttpRequest) -> JsonResponse:
    """
    Start a new assessment for a user.
    
    Expected POST data:
    {
        "user_id": "user123",
        "business_unit": "huntred",
        "assessment_type": "cultural_fit",
        "context": {
            "name": "John Doe",
            "email": "john@example.com",
            "target_entity_type": "COMPANY",
            "target_entity_id": "company123"
        }
    }
    """
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        business_unit_name = data.get('business_unit')
        assessment_type = data.get('assessment_type')
        context = data.get('context', {})
        
        if not all([user_id, business_unit_name, assessment_type]):
            return JsonResponse(
                {'error': 'Missing required parameters'}, 
                status=400
            )
        
        # Get business unit
        try:
            business_unit = await BusinessUnit.objects.aget(name__iexact=business_unit_name)
        except BusinessUnit.DoesNotExist:
            return JsonResponse(
                {'error': f'Business unit {business_unit_name} not found'}, 
                status=404
            )
        
        # Create and start assessment
        handler = await AssessmentFactory.create_handler(
            assessment_type=assessment_type,
            user_id=user_id,
            business_unit=business_unit,
            context=context
        )
        
        # Start the assessment and get first question
        first_question = await handler.start()
        
        return JsonResponse({
            'status': 'started',
            'assessment_type': assessment_type,
            'question': first_question,
            'session_id': str(getattr(handler, 'session_id', ''))
        })
        
    except json.JSONDecodeError:
        return JsonResponse(
            {'error': 'Invalid JSON data'}, 
            status=400
        )
    except Exception as e:
        logger.error(f"Error starting assessment: {str(e)}", exc_info=True)
        return JsonResponse(
            {'error': 'Internal server error'}, 
            status=500
        )

@csrf_exempt
@require_http_methods(["POST"])
async def process_assessment_response(request: HttpRequest) -> JsonResponse:
    """
    Process a user's response to an assessment question.
    
    Expected POST data:
    {
        "user_id": "user123",
        "assessment_type": "cultural_fit",
        "response": "user's answer",
        "session_id": "session123"  # Optional, for resuming sessions
    }
    """
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        assessment_type = data.get('assessment_type')
        user_response = data.get('response')
        session_id = data.get('session_id')
        
        if not all([user_id, assessment_type, user_response]):
            return JsonResponse(
                {'error': 'Missing required parameters'}, 
                status=400
            )
        
        # In a real implementation, you would look up the session and business unit
        # For this example, we'll use a default business unit
        business_unit = await BusinessUnit.objects.aget(name__iexact='huntred')
        
        # Create handler
        handler = await AssessmentFactory.create_handler(
            assessment_type=assessment_type,
            user_id=user_id,
            business_unit=business_unit,
            context={"session_id": session_id}
        )
        
        # Process the response
        result = await handler.process_response(user_response)
        
        return JsonResponse(result)
        
    except json.JSONDecodeError:
        return JsonResponse(
            {'error': 'Invalid JSON data'}, 
            status=400
        )
    except Exception as e:
        logger.error(f"Error processing assessment response: {str(e)}", exc_info=True)
        return JsonResponse(
            {'error': 'Internal server error'}, 
            status=500
        )

@csrf_exempt
@require_http_methods(["GET"])
async def get_assessment_results(request: HttpRequest, assessment_type: str, user_id: str) -> JsonResponse:
    """
    Get the results of a completed assessment.
    
    URL parameters:
    - assessment_type: Type of assessment (e.g., 'cultural_fit')
    - user_id: ID of the user who took the assessment
    
    Query parameters:
    - session_id: Optional session ID
    """
    try:
        session_id = request.GET.get('session_id')
        
        # In a real implementation, you would look up the session and business unit
        business_unit = await BusinessUnit.objects.aget(name__iexact='huntred')
        
        # Create handler
        handler = await AssessmentFactory.create_handler(
            assessment_type=assessment_type,
            user_id=user_id,
            business_unit=business_unit,
            context={"session_id": session_id} if session_id else {}
        )
        
        # Get results
        results = await handler.get_results()
        
        return JsonResponse({
            'status': 'success',
            'assessment_type': assessment_type,
            'user_id': user_id,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error getting assessment results: {str(e)}", exc_info=True)
        return JsonResponse(
            {'error': 'Internal server error'}, 
            status=500
        )
