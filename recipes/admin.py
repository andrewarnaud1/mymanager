# recipes/admin.py
from django.contrib import admin
from .models import Ingredient, Recipe, RecipeIngredient

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ['name', 'unit', 'unit_price', 'price_per_base_unit', 'created_at']
    list_filter = ['unit', 'created_at']
    search_fields = ['name']
    ordering = ['name']
    
    def price_per_base_unit(self, obj):
        """Affiche le prix par unité de base"""
        base_unit = 'g' if obj.unit in ['g', 'kg'] else 'ml' if obj.unit in ['ml', 'cl', 'l'] else 'pièce'
        return f"{obj.get_price_per_base_unit():.4f}€/{base_unit}"
    price_per_base_unit.short_description = "Prix unité de base"

class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    min_num = 1
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        # Aide contextuelle
        formset.form.base_fields['unit'].help_text = "Unité utilisée dans la recette"
        return formset

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ['name', 'servings', 'total_cost', 'cost_per_serving', 'total_time', 'created_at']
    list_filter = ['servings', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['-created_at']
    inlines = [RecipeIngredientInline]
    
    def total_cost(self, obj):
        return f"{obj.total_cost:.2f}€"
    total_cost.short_description = "Coût total"
    
    def cost_per_serving(self, obj):
        return f"{obj.cost_per_serving:.2f}€"
    cost_per_serving.short_description = "Coût/portion"
    
    def total_time(self, obj):
        if obj.total_time:
            return f"{obj.total_time} min"
        return "-"
    total_time.short_description = "Temps total"
