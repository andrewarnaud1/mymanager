# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import PermissionDenied
from .forms import CustomLoginForm, UserProfileForm
from .decorators import admin_required

def login_view(request):
    """
    Vue de connexion personnalisée
    """
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        form = CustomLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data.get('remember_me', False)
            
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    
                    # Gérer "Se souvenir de moi"
                    if not remember_me:
                        request.session.set_expiry(0)  # Session expire à la fermeture du navigateur
                    else:
                        request.session.set_expiry(1209600)  # 2 semaines
                    
                    # Redirection après connexion
                    next_url = request.GET.get('next')
                    if next_url:
                        return redirect(next_url)
                    else:
                        # Redirection basée sur le rôle
                        if user.is_superuser or user.groups.filter(name='Managers').exists():
                            messages.success(request, f'Bienvenue {user.get_full_name() or user.username} !')
                            return redirect('dashboard:dashboard')
                        else:
                            messages.success(request, f'Bienvenue {user.get_full_name() or user.username} !')
                            return redirect('finances:dashboard')  # Employés vers finances uniquement
                else:
                    messages.error(request, 'Votre compte est désactivé.')
            else:
                messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')
    else:
        form = CustomLoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def logout_view(request):
    """
    Vue de déconnexion
    """
    username = request.user.get_full_name() or request.user.username
    logout(request)
    messages.info(request, f'Vous avez été déconnecté. À bientôt {username} !')
    return redirect('accounts:login')

@login_required
def profile_view(request):
    """
    Vue du profil utilisateur
    """
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil mis à jour avec succès !')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    # Informations sur les permissions
    user_groups = request.user.groups.all()
    permissions = {
        'is_admin': request.user.is_superuser,
        'is_manager': request.user.groups.filter(name='Managers').exists(),
        'is_employee': request.user.groups.filter(name='Employees').exists(),
        'can_manage_finances': request.user.is_superuser or request.user.groups.filter(name__in=['Managers', 'Employees']).exists(),
        'can_manage_quotes': request.user.is_superuser or request.user.groups.filter(name='Managers').exists(),
        'can_manage_recipes': request.user.is_superuser or request.user.groups.filter(name='Managers').exists(),
        'can_import_excel': request.user.is_superuser or request.user.groups.filter(name='Managers').exists(),
    }
    
    context = {
        'form': form,
        'user_groups': user_groups,
        'permissions': permissions
    }
    
    return render(request, 'accounts/profile.html', context)

@admin_required
def users_management_view(request):
    """
    Gestion des utilisateurs (admin uniquement)
    """
    users = User.objects.all().order_by('-date_joined')
    groups = Group.objects.all()
    
    context = {
        'users': users,
        'groups': groups
    }
    
    return render(request, 'accounts/users_management.html', context)

@admin_required
def toggle_user_status(request, user_id):
    """
    Activer/désactiver un utilisateur (AJAX)
    """
    if request.method == 'POST':
        try:
            user = User.objects.get(id=user_id)
            if user == request.user:
                return JsonResponse({'success': False, 'message': 'Vous ne pouvez pas modifier votre propre statut.'})
            
            user.is_active = not user.is_active
            user.save()
            
            status = 'activé' if user.is_active else 'désactivé'
            return JsonResponse({
                'success': True, 
                'message': f'Utilisateur {user.username} {status}.',
                'is_active': user.is_active
            })
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Utilisateur non trouvé.'})
    
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée.'})

@admin_required
def change_user_group(request, user_id):
    """
    Changer le groupe d'un utilisateur (AJAX)
    """
    if request.method == 'POST':
        try:
            user = User.objects.get(id=user_id)
            group_name = request.POST.get('group')
            
            if user == request.user:
                return JsonResponse({'success': False, 'message': 'Vous ne pouvez pas modifier vos propres permissions.'})
            
            # Supprimer tous les groupes actuels
            user.groups.clear()
            
            # Ajouter le nouveau groupe si spécifié
            if group_name and group_name != 'none':
                try:
                    group = Group.objects.get(name=group_name)
                    user.groups.add(group)
                    message = f'Utilisateur {user.username} ajouté au groupe {group_name}.'
                except Group.DoesNotExist:
                    return JsonResponse({'success': False, 'message': f'Groupe {group_name} non trouvé.'})
            else:
                message = f'Tous les groupes supprimés pour {user.username}.'
            
            return JsonResponse({'success': True, 'message': message})
            
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Utilisateur non trouvé.'})
    
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée.'})

def register_view(request):
    """
    Vue d'inscription (peut être désactivée en production)
    """
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Ajouter automatiquement au groupe Employees
            employees_group, created = Group.objects.get_or_create(name='Employees')
            user.groups.add(employees_group)
            
            messages.success(request, 'Compte créé avec succès ! Vous pouvez maintenant vous connecter.')
            return redirect('accounts:login')
    else:
        form = UserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def access_denied_view(request):
    """
    Page d'accès refusé
    """
    return render(request, 'accounts/access_denied.html', status=403)