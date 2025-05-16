API_CONFIG = {
    'AOMNI_AI': {
        'ENABLED': False,
        'CATEGORIES': {
            'AI': {
                'ENDPOINT': None,
                'FIELDS': [
                    'company_info',
                    'strategies',
                    'value_propositions',
                    'success_factors'
                ]
            }
        }
    },
    'LINKEDIN': {
        'ENABLED': True,
        'PROFILE_LIMIT': 30000,
        'FIELDS': [
            'profile_info',
            'connections',
            'skills',
            'experience'
        ]
    },
    'CHATBOT': {
        'ENABLED': True,
        'FIELDS': [
            'company_interests',
            'contact_preferences',
            'business_needs'
        ]
    }
}
