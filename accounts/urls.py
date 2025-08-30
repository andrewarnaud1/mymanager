# accounts/urls.py
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentification
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    
    # Profil utilisateur
    path('profile/', views.profile_view, name='profile'),
    
    # Gestion des utilisateurs (admin uniquement)
    path('users/', views.users_management_view, name='users_management'),
    path('users/<int:user_id>/toggle-status/', views.toggle_user_status, name='toggle_user_status'),
    path('users/<int:user_id>/change-group/', views.change_user_group, name='change_user_group'),
    
    # Pages d'erreur
    path('access-denied/', views.access_denied_view, name='access_denied'),
]