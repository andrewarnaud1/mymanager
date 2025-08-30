# recipes/forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import Ingredient, Recipe, RecipeIngredient

class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = ['name', 'unit', 'unit_price']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Farine, Tomates, Huile d\'olive...'
            }),
            'unit': forms.Select(attrs={
                'class': 'form-select'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            })
        }
        help_texts = {
            'unit_price': 'Prix pour 1 unité (ex: 0.99€ pour 1kg de farine)'
        }
    
    def clean_unit_price(self):
        """Valider que le prix est positif"""
        unit_price = self.cleaned_data.get('unit_price')
        if unit_price and unit_price < 0:
            raise forms.ValidationError("Le prix ne peut pas être négatif.")
        return unit_price

class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = ['name', 'description', 'servings', 'preparation_time', 'cooking_time', 'instructions']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Tarte aux pommes, Ratatouille...'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description courte de la recette...'
            }),
            'servings': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'value': '4'
            }),
            'preparation_time': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'En minutes'
            }),
            'cooking_time': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'En minutes'
            }),
            'instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': '1. Préchauffer le four...\n2. Mélanger les ingrédients...'
            })
        }

class RecipeIngredientForm(forms.ModelForm):
    class Meta:
        model = RecipeIngredient
        fields = ['ingredient', 'quantity', 'unit']
        widgets = {
            'ingredient': forms.Select(attrs={
                'class': 'form-select'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'unit': forms.Select(attrs={
                'class': 'form-select'
            })
        }

# Formset pour gérer plusieurs ingrédients dans une recette
RecipeIngredientFormSet = inlineformset_factory(
    Recipe, 
    RecipeIngredient,
    form=RecipeIngredientForm,
    extra=3,  # 3 lignes vides par défaut
    can_delete=True,
    min_num=1,  # Au moins 1 ingrédient requis
    validate_min=True
)