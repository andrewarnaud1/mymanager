# accounts/decorators.py
from functools import wraps
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.core.exceptions import PermissionDenied

def admin_required(function=None, redirect_url=None):
    """
    Décorateur pour restreindre l'accès aux administrateurs uniquement
    """
    def check_admin(user):
        return user.is_superuser
    
    actual_decorator = user_passes_test(
        check_admin,
        login_url=redirect_url or 'accounts:access_denied',
        redirect_field_name=None
    )
    
    if function:
        return login_required(actual_decorator(function))
    return lambda f: login_required(actual_decorator(f))

def manager_required(function=None, redirect_url=None):
    """
    Décorateur pour restreindre l'accès aux managers et administrateurs
    """
    def check_manager(user):
        return user.is_superuser or user.groups.filter(name='Managers').exists()
    
    actual_decorator = user_passes_test(
        check_manager,
        login_url=redirect_url or 'accounts:access_denied',
        redirect_field_name=None
    )
    
    if function:
        return login_required(actual_decorator(function))
    return lambda f: login_required(actual_decorator(f))

def employee_required(function=None, redirect_url=None):
    """
    Décorateur pour restreindre l'accès aux employés, managers et administrateurs
    """
    def check_employee(user):
        return (user.is_superuser or 
                user.groups.filter(name__in=['Managers', 'Employees']).exists())
    
    actual_decorator = user_passes_test(
        check_employee,
        login_url=redirect_url or 'accounts:access_denied',
        redirect_field_name=None
    )
    
    if function:
        return login_required(actual_decorator(function))
    return lambda f: login_required(actual_decorator(f))

def permission_required_custom(permission_check):
    """
    Décorateur générique pour vérifications de permissions personnalisées
    """
    def decorator(function):
        @wraps(function)
        @login_required
        def wrapper(request, *args, **kwargs):
            if permission_check(request.user):
                return function(request, *args, **kwargs)
            else:
                messages.error(request, 'Vous n\'avez pas les permissions nécessaires pour accéder à cette page.')
                return redirect('accounts:access_denied')
        return wrapper
    return decorator

# Fonctions utilitaires pour vérifier les permissions
def can_manage_finances(user):
    """Vérifie si l'utilisateur peut gérer les finances"""
    return user.is_superuser or user.groups.filter(name__in=['Managers', 'Employees']).exists()

def can_manage_quotes(user):
    """Vérifie si l'utilisateur peut gérer les devis"""
    return user.is_superuser or user.groups.filter(name='Managers').exists()

def can_manage_recipes(user):
    """Vérifie si l'utilisateur peut gérer les recettes"""
    return user.is_superuser or user.groups.filter(name='Managers').exists()

def can_import_excel(user):
    """Vérifie si l'utilisateur peut importer des fichiers Excel"""
    return user.is_superuser or user.groups.filter(name='Managers').exists()

def can_access_admin(user):
    """Vérifie si l'utilisateur peut accéder à l'administration"""
    return user.is_superuser