"""
Custom security middleware for staging environment.
Adds Content-Security-Policy and other security headers.
"""

from django.conf import settings


class SecurityHeadersMiddleware:
    """
    Middleware to add security headers to all responses.
    This supplements Django's SecurityMiddleware with CSP and other headers.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Add Content-Security-Policy header
        if hasattr(settings, 'CSP_HEADER') and settings.CSP_HEADER:
            response['Content-Security-Policy'] = settings.CSP_HEADER
        
        # Add Permissions-Policy (formerly Feature-Policy)
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
        
        # Add Referrer-Policy (more restrictive than Django default)
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Add Cross-Origin headers for additional security
        response['Cross-Origin-Embedder-Policy'] = 'credentialless'
        response['Cross-Origin-Resource-Policy'] = 'same-origin'
        
        return response
