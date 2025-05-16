from .core import DynamicsManager
from app.models import BusinessUnit

async def process_chat_message(message: Dict, business_unit: BusinessUnit) -> Dict:
    """Process a chat message using the dynamics system."""
    # Initialize dynamics manager
    dynamics_manager = DynamicsManager(business_unit)
    await dynamics_manager.initialize()
    
    try:
        # Process message through NLP module
        nlp_module = dynamics_manager.get_module('nlp')
        if nlp_module:
            nlp_result = await nlp_module.process_message(message)
            
        # Process through analytics
        analytics_module = dynamics_manager.get_module('analytics')
        if analytics_module:
            analytics_result = await analytics_module.process_event('message_received', message)
            
        # Generate feedback
        feedback_module = dynamics_manager.get_module('feedback')
        if feedback_module:
            feedback_result = await feedback_module.process_event('user_interaction', message)
            
        # Generate final response
        response = {
            'nlp': nlp_result,
            'analytics': analytics_result,
            'feedback': feedback_result
        }
        
        return response
        
    finally:
        # Cleanup resources
        await dynamics_manager.cleanup()

# Example usage
async def main():
    # Get business unit
    business_unit = await BusinessUnit.objects.aget(name='huntred')
    
    # Process a sample message
    message = {
        'text': 'Hola, ¿cómo estás?',
        'context': {
            'previous_message': 'Bienvenido a huntRED®',
            'history': ['Hola', 'Bienvenido'],
            'timestamp': '2025-05-15T18:14:31-06:00'
        }
    }
    
    result = await process_chat_message(message, business_unit)
    print(result)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
