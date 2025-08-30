# staff/forms.py
from django import forms
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from .models import Employee, WeeklySchedule, Shift


class EmployeeForm(forms.ModelForm):
    """
    Formulaire pour créer/modifier un employé
    """
    class Meta:
        model = Employee
        fields = ['first_name', 'last_name', 'phone', 'hire_date', 'is_external', 'is_active']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Prénom de l\'employé'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de l\'employé'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 01 23 45 67 89'
            }),
            'hire_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'is_external': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        is_external = cleaned_data.get('is_external')
        
        # Validation métier spécifique si nécessaire
        return cleaned_data


class EmployeeInternalForm(forms.ModelForm):
    """
    Formulaire pour créer un employé interne (avec compte User)
    """
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom d\'utilisateur pour se connecter'
        }),
        help_text='Nom d\'utilisateur unique pour se connecter au système'
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'adresse@exemple.com'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mot de passe temporaire'
        }),
        help_text='Mot de passe temporaire (l\'employé pourra le changer)'
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmer le mot de passe'
        }),
        help_text='Saisir à nouveau le mot de passe'
    )
    user_group = forms.ModelChoiceField(
        queryset=Group.objects.filter(name__in=['Managers', 'Employees']),
        empty_label="Choisir un groupe...",
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Niveau d\'accès dans l\'application'
    )
    
    class Meta:
        model = Employee
        fields = ['first_name', 'last_name', 'phone', 'hire_date']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Prénom'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Téléphone'
            }),
            'hire_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
    
    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise ValidationError('Ce nom d\'utilisateur existe déjà.')
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError('Cette adresse email est déjà utilisée.')
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm:
            if password != password_confirm:
                raise ValidationError('Les mots de passe ne correspondent pas.')
        
        return cleaned_data
    
    def save(self, commit=True):
        # Créer d'abord l'employé
        employee = super().save(commit=False)
        employee.is_external = False
        employee.is_active = True
        
        if commit:
            # Créer le compte User
            user = User.objects.create_user(
                username=self.cleaned_data['username'],
                email=self.cleaned_data.get('email', ''),
                password=self.cleaned_data['password'],
                first_name=employee.first_name,
                last_name=employee.last_name
            )
            
            # Ajouter au groupe
            user_group = self.cleaned_data['user_group']
            user.groups.add(user_group)
            
            # Lier l'employé au User
            employee.user = user
            employee.save()
        
        return employee


class ConvertEmployeeForm(forms.Form):
    """
    Formulaire pour convertir un employé externe en interne
    """
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom d\'utilisateur'
        })
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email (optionnel)'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mot de passe'
        })
    )
    user_group = forms.ModelChoiceField(
        queryset=Group.objects.filter(name__in=['Managers', 'Employees']),
        empty_label="Choisir un groupe...",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, employee, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.employee = employee
        
        # Pré-remplir avec les données de l'employé
        if not kwargs.get('data'):
            self.fields['username'].initial = f"{employee.first_name.lower()}.{employee.last_name.lower()}"
    
    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise ValidationError('Ce nom d\'utilisateur existe déjà.')
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError('Cette adresse email est déjà utilisée.')
        return email
    
    def convert(self):
        """Effectue la conversion"""
        return self.employee.convert_to_internal(
            username=self.cleaned_data['username'],
            email=self.cleaned_data.get('email', ''),
            password=self.cleaned_data['password']
        )


class WeeklyScheduleForm(forms.ModelForm):
    """
    Formulaire pour créer/modifier un planning hebdomadaire
    """
    class Meta:
        model = WeeklySchedule
        fields = ['week_start', 'notes']
        widgets = {
            'week_start': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notes optionnelles pour cette semaine...'
            }),
        }
    
    def clean_week_start(self):
        week_start = self.cleaned_data['week_start']
        
        # Vérifier que c'est un lundi
        if week_start.weekday() != 0:
            raise ValidationError('La date de début doit être un lundi.')
        
        return week_start


class ShiftForm(forms.ModelForm):
    """
    Formulaire pour créer/modifier un créneau
    """
    class Meta:
        model = Shift
        fields = ['employee', 'date', 'start_time', 'end_time', 'notes']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'start_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'end_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'notes': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Notes optionnelles...'
            }),
        }
    
    def __init__(self, schedule=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.schedule = schedule
        
        # Filtrer les employés actifs
        self.fields['employee'].queryset = Employee.objects.filter(is_active=True)
        
        # Si un planning est fourni, limiter les dates possibles
        if schedule:
            self.fields['date'].widget.attrs['min'] = schedule.week_start.isoformat()
            self.fields['date'].widget.attrs['max'] = schedule.week_end.isoformat()
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        employee = cleaned_data.get('employee')
        date_shift = cleaned_data.get('date')
        
        # Vérifier les horaires
        if start_time and end_time and start_time >= end_time:
            raise ValidationError('L\'heure de fin doit être après l\'heure de début.')
        
        # Vérifier la date dans la semaine du planning
        if self.schedule and date_shift:
            week_start = self.schedule.week_start
            week_end = week_start + timedelta(days=6)
            
            if not (week_start <= date_shift <= week_end):
                raise ValidationError(f'La date doit être dans la semaine du {week_start.strftime("%d/%m/%Y")} au {week_end.strftime("%d/%m/%Y")}.')
        
        # Vérifier les chevauchements si on a toutes les infos
        if employee and date_shift and start_time and end_time:
            overlapping = Shift.get_overlapping_shifts(
                employee=employee,
                date_obj=date_shift,
                start_time=start_time,
                end_time=end_time,
                exclude_pk=self.instance.pk if self.instance.pk else None
            )
            
            if overlapping:
                shift_list = ', '.join([f"{s.start_time}-{s.end_time}" for s in overlapping])
                raise ValidationError(f'Créneau en conflit avec: {shift_list}')
        
        return cleaned_data
    
    def save(self, commit=True):
        shift = super().save(commit=False)
        
        if self.schedule:
            shift.schedule = self.schedule
        
        if commit:
            shift.save()
        
        return shift


class QuickShiftForm(forms.Form):
    """
    Formulaire rapide pour ajouter plusieurs créneaux d'un coup
    """
    employees = forms.ModelMultipleChoiceField(
        queryset=Employee.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        help_text='Sélectionner les employés à planifier'
    )
    dates = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        help_text='Sélectionner les jours'
    )
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time'
        })
    )
    end_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time'
        })
    )
    notes = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Notes optionnelles...'
        })
    )
    
    def __init__(self, schedule, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.schedule = schedule
        
        # Générer les choix de dates pour la semaine
        dates_choices = []
        for i in range(7):
            current_date = schedule.week_start + timedelta(days=i)
            day_name = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'][i]
            dates_choices.append((current_date.isoformat(), f"{day_name} {current_date.strftime('%d/%m')}"))
        
        self.fields['dates'].choices = dates_choices
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time and start_time >= end_time:
            raise ValidationError('L\'heure de fin doit être après l\'heure de début.')
        
        return cleaned_data
    
    def save(self):
        """Créer tous les créneaux"""
        employees = self.cleaned_data['employees']
        dates = self.cleaned_data['dates']
        start_time = self.cleaned_data['start_time']
        end_time = self.cleaned_data['end_time']
        notes = self.cleaned_data.get('notes', '')
        
        shifts_created = []
        
        for employee in employees:
            for date_str in dates:
                date_obj = date.fromisoformat(date_str)
                
                # Vérifier s'il n'y a pas déjà un créneau similaire
                existing = Shift.objects.filter(
                    schedule=self.schedule,
                    employee=employee,
                    date=date_obj,
                    start_time=start_time,
                    end_time=end_time
                ).exists()
                
                if not existing:
                    shift = Shift.objects.create(
                        schedule=self.schedule,
                        employee=employee,
                        date=date_obj,
                        start_time=start_time,
                        end_time=end_time,
                        notes=notes
                    )
                    shifts_created.append(shift)
        
        return shifts_created


class WeekNavigationForm(forms.Form):
    """
    Formulaire pour naviguer entre les semaines
    """
    week_start = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    def clean_week_start(self):
        week_start = self.cleaned_data['week_start']
        
        # Ajuster automatiquement au lundi de la semaine
        if week_start.weekday() != 0:
            # Trouver le lundi de cette semaine
            week_start = week_start - timedelta(days=week_start.weekday())
        
        return week_start