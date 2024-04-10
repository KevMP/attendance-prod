from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def role_required(*roles, redirect_url='login'):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            required_roles = set(roles)
            user_groups = set(request.user.groups.values_list('name', flat=True))
            
            if not required_roles.intersection(user_groups):
                # Flash a message before redirecting
                messages.error(request, "You do not have permission to view this page")
                return redirect(redirect_url)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
