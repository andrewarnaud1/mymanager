# finances/forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import DailySale
from datetime import date

class DailySaleForm(forms.ModelForm):
    """
    Formulaire pour saisir/modifier une vente journalière
    """
    class Meta:
        model = DailySale
        fields = [
            'date', 'cb_caisse', 'cb_tpe', 'especes_caisse', 'especes_reel',
            'tr_caisse', 'tr_reel', 'nombre_clients', 'commentaires'
        ]
        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'cb_caisse': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'cb_tpe': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'especes_caisse': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'especes_reel': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'tr_caisse': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'tr_reel': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'nombre_clients': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'commentaires': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Commentaires sur cette journée...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Date par défaut = aujourd'hui pour un nouveau formulaire
        if not self.instance.pk:
            self.fields['date'].initial = date.today()
        
        # Rendre certains champs optionnels avec des labels clairs
        self.fields['cb_caisse'].required = False
        self.fields['cb_tpe'].required = False
        self.fields['especes_caisse'].required = False
        self.fields['especes_reel'].required = False
        self.fields['tr_caisse'].required = False
        self.fields['tr_reel'].required = False
        self.fields['nombre_clients'].required = False
        
        # Labels personnalisés
        self.fields['cb_caisse'].label = "CB Caisse (€)"
        self.fields['cb_tpe'].label = "CB TPE (€)"
        self.fields['especes_caisse'].label = "Espèces Caisse (€)"
        self.fields['especes_reel'].label = "Espèces Réel (€)"
        self.fields['tr_caisse'].label = "TR Caisse (€)"
        self.fields['tr_reel'].label = "TR Réel (€)"
    
    def clean_date(self):
        """Valider que la date n'est pas trop future"""
        date_value = self.cleaned_data['date']
        if date_value > date.today():
            # Autoriser jusqu'à 1 jour dans le futur (pour saisie en soirée)
            from datetime import timedelta
            max_date = date.today() + timedelta(days=1)
            if date_value > max_date:
                raise ValidationError("La date ne peut pas être trop éloignée dans le futur.")
        return date_value
    
    def clean(self):
        """Validation croisée des champs"""
        cleaned_data = super().clean()
        
        # Vérifier qu'au moins un montant est renseigné
        montants = [
            cleaned_data.get('cb_caisse'),
            cleaned_data.get('cb_tpe'),
            cleaned_data.get('especes_caisse'),
            cleaned_data.get('especes_reel'),
            cleaned_data.get('tr_caisse'),
            cleaned_data.get('tr_reel')
        ]
        
        if not any(montant for montant in montants if montant):
            raise ValidationError("Veuillez renseigner au moins un montant.")
        
        return cleaned_data


class ExcelImportForm(forms.Form):
    """
    Formulaire pour importer un fichier Excel
    """
    file = forms.FileField(
        label="Fichier Excel",
        help_text="Sélectionnez votre fichier Excel (.xlsx)",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls'
        })
    )
    
    overwrite_existing = forms.BooleanField(
        label="Écraser les données existantes",
        help_text="Si coché, les données existantes pour les mêmes dates seront mises à jour",
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def clean_file(self):
        """Valider le fichier uploadé"""
        file = self.cleaned_data['file']
        
        # Vérifier l'extension
        if not file.name.lower().endswith(('.xlsx', '.xls')):
            raise ValidationError("Seuls les fichiers Excel (.xlsx, .xls) sont acceptés.")
        
        # Vérifier la taille (max 10MB)
        if file.size > 10 * 1024 * 1024:
            raise ValidationError("Le fichier est trop volumineux. Taille maximum : 10MB.")
        
        return file


class DateRangeFilterForm(forms.Form):
    """
    Formulaire pour filtrer par période
    """
    date_debut = forms.DateField(
        label="Date de début",
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    date_fin = forms.DateField(
        label="Date de fin",
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    def clean(self):
        """Valider que la date de fin est après la date de début"""
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')
        
        if date_debut and date_fin and date_debut > date_fin:
            raise ValidationError("La date de début ne peut pas être après la date de fin.")
        
        return cleaned_data


class MonthYearFilterForm(forms.Form):
    """
    Formulaire pour filtrer par mois/année
    """
    MOIS_CHOICES = [
        ('', 'Tous les mois'),
        (1, 'Janvier'), (2, 'Février'), (3, 'Mars'), (4, 'Avril'),
        (5, 'Mai'), (6, 'Juin'), (7, 'Juillet'), (8, 'Août'),
        (9, 'Septembre'), (10, 'Octobre'), (11, 'Novembre'), (12, 'Décembre')
    ]
    
    annee = forms.IntegerField(
        label="Année",
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '2020',
            'max': '2030',
            'placeholder': 'AAAA'
        })
    )
    
    mois = forms.ChoiceField(
        label="Mois",
        choices=MOIS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Année par défaut = année actuelle
        if not self.data and not self.initial:
            self.fields['annee'].initial = date.today().year