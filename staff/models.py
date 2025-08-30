# staff/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import datetime, date, timedelta


class Employee(models.Model):
    """
    Modèle représentant un employé (interne avec compte User ou externe)
    """
    # Employé interne (avec compte User Django)
    user = models.OneToOneField(
        User, 
        null=True, 
        blank=True, 
        on_delete=models.CASCADE,
        verbose_name="Compte utilisateur",
        help_text="Laisser vide pour un employé externe"
    )
    
    # Informations communes (obligatoires pour tous)
    first_name = models.CharField(max_length=100, verbose_name="Prénom")
    last_name = models.CharField(max_length=100, verbose_name="Nom")
    phone = models.CharField(
        max_length=20, 
        blank=True,
        verbose_name="Téléphone",
        help_text="Numéro de téléphone de contact"
    )
    
    # Statut et métadonnées
    is_external = models.BooleanField(
        default=False, 
        verbose_name="Employé externe",
        help_text="Employé sans compte utilisateur (planning uniquement)"
    )
    is_active = models.BooleanField(
        default=True, 
        verbose_name="Actif",
        help_text="Décocher pour désactiver l'employé"
    )
    
    # Dates de suivi
    hire_date = models.DateField(
        null=True, 
        blank=True,
        verbose_name="Date d'embauche"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    
    class Meta:
        verbose_name = "Employé"
        verbose_name_plural = "Employés"
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        status = " (Externe)" if self.is_external else ""
        return f"{self.first_name} {self.last_name}{status}"
    
    def clean(self):
        """Validation personnalisée"""
        # Un employé interne doit avoir un compte User
        if not self.is_external and not self.user:
            raise ValidationError({
                'user': 'Un employé interne doit être lié à un compte utilisateur.'
            })
        
        # Un employé externe ne peut pas avoir de compte User
        if self.is_external and self.user:
            raise ValidationError({
                'user': 'Un employé externe ne peut pas avoir de compte utilisateur.'
            })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def full_name(self):
        """Nom complet de l'employé"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def can_login(self):
        """Peut se connecter au système"""
        return not self.is_external and self.user and self.user.is_active
    
    @property
    def display_name(self):
        """Nom d'affichage avec indicateur de statut"""
        name = self.full_name
        if self.is_external:
            name += " (Externe)"
        if not self.is_active:
            name += " (Inactif)"
        return name
    
    def convert_to_internal(self, username, email, password=None):
        """
        Convertit un employé externe en employé interne
        en créant un compte User Django
        """
        if not self.is_external:
            raise ValidationError("Cet employé est déjà interne.")
        
        if User.objects.filter(username=username).exists():
            raise ValidationError(f"Le nom d'utilisateur '{username}' existe déjà.")
        
        if email and User.objects.filter(email=email).exists():
            raise ValidationError(f"L'email '{email}' est déjà utilisé.")
        
        # Créer le compte User
        user = User.objects.create_user(
            username=username,
            email=email or '',
            first_name=self.first_name,
            last_name=self.last_name,
            password=password or User.objects.make_random_password()
        )
        
        # Lier l'employé au compte et changer le statut
        self.user = user
        self.is_external = False
        self.save()
        
        return user


class WeeklySchedule(models.Model):
    """
    Planning hebdomadaire (semaine du lundi au dimanche)
    """
    week_start = models.DateField(
        verbose_name="Début de semaine",
        help_text="Date du lundi de la semaine planifiée"
    )
    
    # Métadonnées de création
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        verbose_name="Créé par"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    
    # Notes optionnelles
    notes = models.TextField(
        blank=True,
        verbose_name="Notes",
        help_text="Notes générales pour cette semaine"
    )
    
    class Meta:
        verbose_name = "Planning hebdomadaire"
        verbose_name_plural = "Plannings hebdomadaires"
        ordering = ['-week_start']
        unique_together = ['week_start']  # Un seul planning par semaine
    
    def __str__(self):
        week_end = self.week_start + timedelta(days=6)
        return f"Semaine du {self.week_start.strftime('%d/%m/%Y')} au {week_end.strftime('%d/%m/%Y')}"
    
    def clean(self):
        """Validation : week_start doit être un lundi"""
        if self.week_start and self.week_start.weekday() != 0:
            raise ValidationError({
                'week_start': 'La date de début doit être un lundi.'
            })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def week_end(self):
        """Date de fin de semaine (dimanche)"""
        return self.week_start + timedelta(days=6)
    
    @property
    def week_range_display(self):
        """Affichage de la période de la semaine"""
        return f"{self.week_start.strftime('%d/%m')} - {self.week_end.strftime('%d/%m/%Y')}"
    
    @property
    def is_current_week(self):
        """Vérifie si c'est la semaine actuelle"""
        today = date.today()
        monday_this_week = today - timedelta(days=today.weekday())
        return self.week_start == monday_this_week
    
    @property
    def total_hours(self):
        """Calcule le total d'heures planifiées pour la semaine"""
        total_minutes = 0
        for shift in self.shifts.all():
            total_minutes += shift.duration_minutes
        return total_minutes / 60
    
    @property
    def employees_count(self):
        """Nombre d'employés distincts planifiés cette semaine"""
        return self.shifts.values('employee').distinct().count()
    
    @classmethod
    def get_or_create_for_date(cls, date_obj, created_by):
        """
        Récupère ou crée un planning pour la semaine contenant la date donnée
        """
        # Calculer le lundi de la semaine
        monday = date_obj - timedelta(days=date_obj.weekday())
        
        schedule, created = cls.objects.get_or_create(
            week_start=monday,
            defaults={'created_by': created_by}
        )
        return schedule, created


class Shift(models.Model):
    """
    Créneau de travail pour un employé à une date/heure donnée
    """
    schedule = models.ForeignKey(
        WeeklySchedule, 
        on_delete=models.CASCADE,
        related_name='shifts',
        verbose_name="Planning"
    )
    employee = models.ForeignKey(
        Employee, 
        on_delete=models.CASCADE,
        verbose_name="Employé"
    )
    
    # Date et horaires
    date = models.DateField(verbose_name="Date")
    start_time = models.TimeField(verbose_name="Heure de début")
    end_time = models.TimeField(verbose_name="Heure de fin")
    
    # Notes optionnelles
    notes = models.CharField(
        max_length=200, 
        blank=True,
        verbose_name="Notes",
        help_text="Notes spécifiques pour ce créneau"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Créneau"
        verbose_name_plural = "Créneaux"
        ordering = ['date', 'start_time', 'employee__last_name']
        # Un employé peut avoir plusieurs créneaux le même jour
        # mais on évite les doublons exacts
        unique_together = ['schedule', 'employee', 'date', 'start_time', 'end_time']
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.date.strftime('%d/%m')} {self.start_time}-{self.end_time}"
    
    def clean(self):
        """Validation des horaires"""
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError({
                    'end_time': 'L\'heure de fin doit être après l\'heure de début.'
                })
        
    # Validation des horaires (hors validation de la semaine du planning, gérée dans le formulaire)
        
        # Vérifier que l'employé est actif
        if self.employee and not self.employee.is_active:
            raise ValidationError({
                'employee': 'Impossible de planifier un employé inactif.'
            })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def duration_minutes(self):
        """Durée du créneau en minutes"""
        if self.start_time and self.end_time:
            start_datetime = datetime.combine(date.today(), self.start_time)
            end_datetime = datetime.combine(date.today(), self.end_time)
            
            # Gérer le cas où le créneau passe minuit
            if end_datetime < start_datetime:
                end_datetime += timedelta(days=1)
            
            return int((end_datetime - start_datetime).total_seconds() / 60)
        return 0
    
    @property
    def duration_hours(self):
        """Durée du créneau en heures (format décimal)"""
        return self.duration_minutes / 60
    
    @property
    def duration_display(self):
        """Affichage formaté de la durée (ex: 7h30)"""
        minutes = self.duration_minutes
        hours = minutes // 60
        remaining_minutes = minutes % 60
        
        if remaining_minutes == 0:
            return f"{hours}h"
        else:
            return f"{hours}h{remaining_minutes:02d}"
    
    @property
    def time_range_display(self):
        """Affichage de la plage horaire"""
        return f"{self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"
    
    @property
    def day_name(self):
        """Nom du jour en français"""
        days = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        return days[self.date.weekday()]
    
    def overlaps_with(self, other_shift):
        """
        Vérifie si ce créneau chevauche avec un autre créneau
        du même employé le même jour
        """
        if (self.employee != other_shift.employee or 
            self.date != other_shift.date or
            self.pk == other_shift.pk):
            return False
        
        # Vérifier le chevauchement des horaires
        return not (self.end_time <= other_shift.start_time or 
                   self.start_time >= other_shift.end_time)
    
    @classmethod
    def get_overlapping_shifts(cls, employee, date_obj, start_time, end_time, exclude_pk=None):
        """
        Trouve les créneaux qui chevauchent avec les horaires donnés
        """
        queryset = cls.objects.filter(
            employee=employee,
            date=date_obj
        )
        
        if exclude_pk:
            queryset = queryset.exclude(pk=exclude_pk)
        
        overlapping = []
        for shift in queryset:
            # Créer un shift temporaire pour tester le chevauchement
            temp_shift = cls(
                employee=employee,
                date=date_obj,
                start_time=start_time,
                end_time=end_time
            )
            if temp_shift.overlaps_with(shift):
                overlapping.append(shift)
        
        return overlapping