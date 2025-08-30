# quotes/forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import Customer, Quote, QuoteItem
from recipes.models import Recipe
from datetime import date, timedelta
from decimal import Decimal

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'company', 'email', 'phone', 'address', 'city', 'postal_code', 'country']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du contact'
            }),
            'company': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de l\'entreprise (optionnel)'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'contact@exemple.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '01 23 45 67 89'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Adresse complète'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ville'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '75000'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'value': 'France'
            })
        }

class QuoteForm(forms.ModelForm):
    class Meta:
        model = Quote
        fields = [
            'customer', 'title', 'description', 'quote_date', 'valid_until', 
            'event_date', 'discount_percentage', 'tax_rate', 'terms_conditions'
        ]
        widgets = {
            'customer': forms.Select(attrs={
                'class': 'form-select'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Traiteur pour mariage, Repas d\'entreprise...'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description du service proposé...'
            }),
            'quote_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'valid_until': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'event_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'discount_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'value': '0'
            }),
            'tax_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'value': '20'
            }),
            'terms_conditions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Conditions particulières pour ce devis...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Définir des valeurs par défaut
        if not self.instance.pk:  # Nouveau devis
            self.fields['quote_date'].initial = date.today()
            self.fields['valid_until'].initial = date.today() + timedelta(days=30)

class QuoteItemForm(forms.ModelForm):
    class Meta:
        model = QuoteItem
        fields = ['recipe', 'quantity', 'unit_price', 'description']
        widgets = {
            'recipe': forms.Select(attrs={
                'class': 'form-select recipe-select'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control quantity-input',
                'min': '1',
                'value': '1'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control price-input',
                'step': '0.01',
                'min': '0'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Description spécifique (optionnel)...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ajouter des informations sur les coûts dans les options
        recipe_choices = [('', '---------')]
        
        try:
            for recipe in Recipe.objects.all():
                cost = recipe.cost_per_serving
                # Utiliser Decimal pour éviter l'erreur de type
                suggested_price = cost * Decimal('2.5')  # Suggestion avec marge de 150%
                label = f"{recipe.name} (coût: {cost:.2f}€, suggéré: {suggested_price:.2f}€)"
                recipe_choices.append((recipe.pk, label))
        except Exception as e:
            # En cas d'erreur, utiliser les choix par défaut
            for recipe in Recipe.objects.all():
                recipe_choices.append((recipe.pk, recipe.name))
        
        self.fields['recipe'].choices = recipe_choices

# Formset pour gérer plusieurs items dans un devis
QuoteItemFormSet = inlineformset_factory(
    Quote,
    QuoteItem,
    form=QuoteItemForm,
    extra=3,  # 3 lignes vides par défaut
    can_delete=True,
    min_num=1,  # Au moins 1 item requis
    validate_min=True
)