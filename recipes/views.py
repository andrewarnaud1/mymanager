# recipes/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from accounts.decorators import manager_required
from .models import Ingredient, Recipe, RecipeIngredient
from .forms import IngredientForm, RecipeForm, RecipeIngredientFormSet

# ===== VUES INGRÉDIENTS =====
@manager_required
def ingredients_list(request):
    """Liste tous les ingrédients"""
    ingredients = Ingredient.objects.all().order_by('name')
    return render(request, 'recipes/ingredients_list.html', {
        'ingredients': ingredients
    })

@manager_required
def ingredient_create(request):
    """Créer un nouvel ingrédient"""
    if request.method == 'POST':
        form = IngredientForm(request.POST)
        if form.is_valid():
            ingredient = form.save()
            messages.success(request, f'Ingrédient "{ingredient.name}" créé avec succès!')
            return redirect('recipes:ingredients')
    else:
        form = IngredientForm()
    
    return render(request, 'recipes/ingredient_form.html', {
        'form': form,
        'title': 'Ajouter un ingrédient'
    })

@manager_required
def ingredient_update(request, pk):
    """Modifier un ingrédient"""
    ingredient = get_object_or_404(Ingredient, pk=pk)
    
    if request.method == 'POST':
        form = IngredientForm(request.POST, instance=ingredient)
        if form.is_valid():
            ingredient = form.save()
            messages.success(request, f'Ingrédient "{ingredient.name}" modifié avec succès!')
            return redirect('recipes:ingredients')
    else:
        form = IngredientForm(instance=ingredient)
    
    return render(request, 'recipes/ingredient_form.html', {
        'form': form,
        'title': f'Modifier {ingredient.name}',
        'ingredient': ingredient
    })

@manager_required
def ingredient_delete(request, pk):
    """Supprimer un ingrédient"""
    ingredient = get_object_or_404(Ingredient, pk=pk)
    
    if request.method == 'POST':
        name = ingredient.name
        ingredient.delete()
        messages.success(request, f'Ingrédient "{name}" supprimé avec succès!')
        return redirect('recipes:ingredients')
    
    return render(request, 'recipes/ingredient_confirm_delete.html', {
        'ingredient': ingredient
    })

# ===== VUES RECETTES =====
@manager_required
def recipes_list(request):
    """Liste toutes les recettes"""
    recipes = Recipe.objects.all().order_by('-created_at')
    return render(request, 'recipes/recipes_list.html', {
        'recipes': recipes
    })

@manager_required
def recipe_create(request):
    """Créer une nouvelle recette"""
    if request.method == 'POST':
        form = RecipeForm(request.POST)
        formset = RecipeIngredientFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            recipe = form.save()
            formset.instance = recipe
            formset.save()
            messages.success(request, f'Recette "{recipe.name}" créée avec succès!')
            return redirect('recipes:detail', pk=recipe.pk)
    else:
        form = RecipeForm()
        # Créer un formset vide avec des formulaires qui incluent tous les champs
        formset = RecipeIngredientFormSet(queryset=RecipeIngredient.objects.none())
    
    return render(request, 'recipes/recipe_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Créer une recette'
    })

@manager_required
def recipe_update(request, pk):
    """Modifier une recette"""
    recipe = get_object_or_404(Recipe, pk=pk)
    
    if request.method == 'POST':
        form = RecipeForm(request.POST, instance=recipe)
        formset = RecipeIngredientFormSet(request.POST, instance=recipe)
        
        if form.is_valid() and formset.is_valid():
            recipe = form.save()
            formset.save()
            messages.success(request, f'Recette "{recipe.name}" modifiée avec succès!')
            return redirect('recipes:detail', pk=recipe.pk)
    else:
        form = RecipeForm(instance=recipe)
        formset = RecipeIngredientFormSet(instance=recipe)
    
    return render(request, 'recipes/recipe_form.html', {
        'form': form,
        'formset': formset,
        'title': f'Modifier {recipe.name}',
        'recipe': recipe
    })

@manager_required
def recipe_detail(request, pk):
    """Détail d'une recette avec calcul des coûts"""
    recipe = get_object_or_404(Recipe, pk=pk)
    ingredients = recipe.recipe_ingredients.all().select_related('ingredient')
    
    return render(request, 'recipes/recipe_detail.html', {
        'recipe': recipe,
        'ingredients': ingredients
    })

@manager_required
def recipe_delete(request, pk):
    """Supprimer une recette"""
    recipe = get_object_or_404(Recipe, pk=pk)
    
    if request.method == 'POST':
        name = recipe.name
        recipe.delete()
        messages.success(request, f'Recette "{name}" supprimée avec succès!')
        return redirect('recipes:list')
    
    return render(request, 'recipes/recipe_confirm_delete.html', {
        'recipe': recipe
    })