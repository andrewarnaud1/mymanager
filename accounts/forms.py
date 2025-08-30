# accounts/forms.py
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm

class CustomLoginForm(forms.Form):
    """
    Formulaire de connexion personnalisé
    """
    username = forms.CharField(
        label='Nom d\'utilisateur',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre nom d\'utilisateur',
            'autocomplete': 'username',
            'autofocus': True
        })
    )
    
    password = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre mot de passe',
            'autocomplete': 'current-password'
        })
    )
    
    remember_me = forms.BooleanField(
        label='Se souvenir de moi',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            # Permettre la connexion avec email ou username
            if '@' in username:
                try:
                    user = User.objects.get(email=username)
                    return user.username
                except User.DoesNotExist:
                    pass
        return username

class UserProfileForm(forms.ModelForm):
    """
    Formulaire de modification du profil utilisateur
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Votre prénom'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Votre nom'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'votre.email@exemple.com'
            })
        }
        labels = {
            'first_name': 'Prénom',
            'last_name': 'Nom',
            'email': 'Adresse email'
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Vérifier que l'email n'est pas déjà utilisé par un autre utilisateur
            existing_user = User.objects.filter(email=email).exclude(id=self.instance.id)
            if existing_user.exists():
                raise forms.ValidationError('Cette adresse email est déjà utilisée.')
        return email