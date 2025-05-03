# formatech/utils.py
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def has_permission(permission_code):
    """Vérifie si l'utilisateur a la permission spécifiée via son rôle"""
    def check_permission(user):
        if user.is_superuser:
            return True
        if not user.is_authenticated:
            return False
        if not user.role:
            return False
        user_perms = [p.code for p in user.get_permissions()]
        return permission_code in user_perms
    
    return user_passes_test(check_permission, login_url='/users/login/')

def admin_required(view_func):
    """Décorateur qui vérifie si l'utilisateur est admin"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_superuser or (request.user.role and request.user.role.name == "Admin"):
            return view_func(request, *args, **kwargs)
        messages.error(request, "Vous n'avez pas les droits pour accéder à cette page.")
        return redirect('formation:training_list')
    return wrapper