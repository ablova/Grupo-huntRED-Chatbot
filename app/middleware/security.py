"""
Security middleware for AI HuntRED
Adds security headers to all HTTP responses
"""

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware to add security headers to all responses.
    """
    
    def process_response(self, request, response):
        # Content Security Policy
        if not settings.DEBUG:
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://code.jquery.com https://stackpath.bootstrapcdn.com; "
                "style-src 'self' 'unsafe-inline' https://stackpath.bootstrapcdn.com https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https://api.huntred.com wss://huntred.com; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self';"
            )
        
        # X-Content-Type-Options
        response['X-Content-Type-Options'] = 'nosniff'
        
        # X-Frame-Options (clickjacking protection)
        response['X-Frame-Options'] = 'DENY'
        
        # X-XSS-Protection (for older browsers)
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Feature Policy / Permissions Policy
        response['Permissions-Policy'] = (
            "accelerometer=(), "
            "camera=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "payment=(), "
            "usb=()"
        )
        
        # Remove server header if present
        if 'Server' in response:
            del response['Server']
        
        # Remove X-Powered-By header if present
        if 'X-Powered-By' in response:
            del response['X-Powered-By']
        
        return response


class RateLimitMiddleware(MiddlewareMixin):
    """
    Simple rate limiting middleware to prevent brute force attacks.
    For production, use django-ratelimit or similar.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.cache = {}
        super().__init__(get_response)
    
    def process_request(self, request):
        if request.path.startswith('/api/') or request.path.startswith('/auth/'):
            ip = self.get_client_ip(request)
            key = f"ratelimit:{ip}:{request.path}"
            
            # Simple in-memory rate limiting (use Redis in production)
            # This is just an example - use proper rate limiting library
            pass
    
    def get_client_ip(self, request):
        """Get the client's IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip