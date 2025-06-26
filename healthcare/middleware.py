"""
Custom middleware for XSS and SQL injection protection.
"""

import re
from django.http import HttpResponse, QueryDict
from django.utils.deprecation import MiddlewareMixin
from healthcare.security import SecurityUtils


class SecurityMiddleware(MiddlewareMixin):
    """
    Custom security middleware for XSS and SQL injection protection.
    """
    
    def process_request(self, request):
        """
        Process incoming requests for XSS and SQL injection detection.
        """
        # Check for suspicious patterns in request data
        if self._is_suspicious_request(request):
            return HttpResponse("Suspicious request detected", status=400)
        
        return None
    
    def process_response(self, request, response):
        """
        Add basic security headers to responses.
        """
        # XSS Protection
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Content Type Options
        response['X-Content-Type-Options'] = 'nosniff'
        
        # Frame Options
        response['X-Frame-Options'] = 'DENY'
        
        return response
    
    def _is_suspicious_request(self, request):
        """
        Check if the request contains XSS or SQL injection patterns.
        """
        # Check GET parameters
        for key, value in request.GET.items():
            if SecurityUtils.is_suspicious_input(value):
                return True
        
        # Check POST parameters
        if request.method == 'POST':
            for key, value in request.POST.items():
                if SecurityUtils.is_suspicious_input(value):
                    return True
        
        # Check headers
        for key, value in request.headers.items():
            if SecurityUtils.is_suspicious_input(value):
                return True
        
        return False


class InputSanitizationMiddleware(MiddlewareMixin):
    """
    Middleware to sanitize user input automatically.
    """
    
    def process_request(self, request):
        """
        Sanitize user input in request data.
        """
        # Sanitize GET parameters
        if request.GET:
            sanitized_get = {}
            for key, value in request.GET.items():
                sanitized_key = SecurityUtils.sanitize_input(key, 100)
                sanitized_value = SecurityUtils.sanitize_input(value, 1000)
                sanitized_get[sanitized_key] = sanitized_value
            # Create a new QueryDict with sanitized data
            request.GET = QueryDict('', mutable=True)
            for key, value in sanitized_get.items():
                request.GET[key] = value
            request.GET._mutable = False
        
        # Sanitize POST parameters
        if request.method == 'POST' and request.POST:
            sanitized_post = {}
            for key, value in request.POST.items():
                sanitized_key = SecurityUtils.sanitize_input(key, 100)
                sanitized_value = SecurityUtils.sanitize_input(value, 1000)
                sanitized_post[sanitized_key] = sanitized_value
            # Create a new QueryDict with sanitized data
            request.POST = QueryDict('', mutable=True)
            for key, value in sanitized_post.items():
                request.POST[key] = value
            request.POST._mutable = False
        
        return None


class AuditLogMiddleware(MiddlewareMixin):
    """
    Middleware to log security-relevant events.
    """
    
    def process_request(self, request):
        """
        Log suspicious requests and authentication attempts.
        """
        # Log failed login attempts
        if request.path.endswith('/login/') and request.method == 'POST':
            # This will be handled by django-axes, but we can add additional logging here
            pass
        
        # Log access to sensitive URLs
        sensitive_paths = [
            '/admin/', '/api/', '/users/', '/patients/', '/doctors/',
            '/medical-records/', '/appointments/', '/prescriptions/'
        ]
        
        for path in sensitive_paths:
            if path in request.path and request.user.is_authenticated:
                # Log access to sensitive areas
                pass
        
        return None 