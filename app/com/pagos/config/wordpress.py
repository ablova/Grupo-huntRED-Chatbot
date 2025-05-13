WORDPRESS_CONFIG = {
    'huntRED': {
        'base_url': 'https://huntred.com/wp-json/wp/v2',
        'auth_token': None,  # Se obtendrá de settings
        'endpoints': {
            'baselines': 'pricing/baselines',
            'addons': 'pricing/addons',
            'coupons': 'pricing/coupons',
            'milestones': 'pricing/milestones'
        }
    },
    'huntU': {
        'base_url': 'https://huntu.mx/wp-json/wp/v2',
        'auth_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjEsIm5hbWUiOiJodW50VSIsImlhdCI6MTczNzQwNzM2NywiZXhwIjoxODk1MDg3MzY3fQ.PovX_OvPT-YVezWBoFCqVqXCeLPjmR6iYgC6n0iDUlE',
        'endpoints': {
            'baselines': 'pricing/baselines',
            'addons': 'pricing/addons',
            'coupons': 'pricing/coupons',
            'milestones': 'pricing/milestones'
        }
    },
    'Amigro': {
        'base_url': 'https://amigro.org/wp-json/wp/v2',
        'auth_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjEsIm5hbWUiOiJQYWJsbyIsImlhdCI6MTczNzQwNzE4NSwiZXhwIjoxODk1MDg3MTg1fQ.GIS1QphBCe8_JnS60TDZW4jfvxGb6OJkhwKb71PZ9CY',
        'endpoints': {
            'baselines': 'pricing/baselines',
            'addons': 'pricing/addons',
            'coupons': 'pricing/coupons',
            'milestones': 'pricing/milestones'
        }
    }
}

# Configuración de timeouts y reintentos
WORDPRESS_SETTINGS = {
    'retry_attempts': 3,
    'retry_delay': 2.0,
    'cache_timeout': 600,
    'request_timeout': 30
}
