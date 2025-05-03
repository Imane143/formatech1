from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def permission_required(permission_code):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            # Check if user is authenticated
            if not request.user.is_authenticated:
                messages.error(request, "Vous devez être connecté pour accéder à cette page.")
                return redirect('users:login')
            
            # Admin users have all permissions
            if request.user.is_superuser or request.user.is_staff:
                return view_func(request, *args, **kwargs)
            
            # Check user's role permissions
            user_permissions = request.user.get_permissions()
            has_permission = any(p.code == permission_code for p in user_permissions)
            
            if not has_permission:
                messages.error(request, "Vous n'avez pas les permissions nécessaires pour accéder à cette page.")
                return redirect('formation:training_list')
                
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator