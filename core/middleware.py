import uuid
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages


class SingleDeviceMiddleware:
    """Middleware to enforce single device login for students"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check only if user is authenticated
        if request.user.is_authenticated:
            # Skip check for admin users
            if request.user.is_admin_staff or request.user.is_staff:
                return self.get_response(request)
            
            # Skip for login and logout paths
            if request.path in [reverse('login'), reverse('logout')]:
                return self.get_response(request)
            
            # Check if the user has a student profile
            if hasattr(request.user, 'student_profile'):
                profile = request.user.student_profile
                
                # Get the session token from the request session
                session_token = request.session.get('session_token')
                
                # Check if the session token matches the stored token
                if not session_token or str(profile.session_token) != session_token:
                    # Log out the user and redirect to login
                    messages.error(request, "Your session has been invalidated. You have been logged in from another device.")
                    return redirect('logout')
        
        response = self.get_response(request)
        return response
