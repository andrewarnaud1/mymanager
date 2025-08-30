# recipes/models.py
from django.db import models
from decimal import Decimal

class Ingredient(models.Model):
    UNIT_CHOICES = [
        # Poids
        ('g', 'grammes'),
        ('kg', 'kilogrammes'),
        # Volume
        ('ml', 'millilitres'),
        ('cl', 'centilitres'),
        ('l', 'litres'),
        # Quantité
        ('piece', 'pièce(s)'),
        ('c_soupe', 'cuillère(s) à soupe'),
        ('c_cafe', 'cuillère(s) à café'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="Nom")
    unit = models.CharField(
        max_length=20, 
        choices=UNIT_CHOICES,
        verbose_name="Unité d'achat"
    )
    unit_price = models.DecimalField(
        max_digits=10, 
        decimal_places=4,  # Plus de précision pour les petites unités
        verbose_name="Prix unitaire"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Ingrédient"
        verbose_name_plural = "Ingrédients"
    
    def __str__(self):
        return f"{self.name} ({self.get_unit_display()})"
    
    def get_price_per_base_unit(self):
        """Retourne le prix pour l'unité de base (grammes, ml, pièce)"""
        conversion_factors = {
            'kg': 1000,  # 1 kg = 1000g
            'g': 1,      # 1g = 1g
            'l': 1000,   # 1L = 1000ml
            'cl': 10,    # 1cl = 10ml
            'ml': 1,     # 1ml = 1ml
            'piece': 1,  # 1 pièce = 1 pièce
            'c_soupe': 1,
            'c_cafe': 1,
        }
        
        factor = conversion_factors.get(self.unit, 1)
        return self.unit_price / factor

class Recipe(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nom de la recette")
    description = models.TextField(blank=True, verbose_name="Description")
    servings = models.PositiveIntegerField(default=1, verbose_name="Nombre de portions")
    preparation_time = models.PositiveIntegerField(
        blank=True, null=True, 
        verbose_name="Temps de préparation (minutes)"
    )
    cooking_time = models.PositiveIntegerField(
        blank=True, null=True,
        verbose_name="Temps de cuisson (minutes)"
    )
    instructions = models.TextField(blank=True, verbose_name="Instructions")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Recette"
        verbose_name_plural = "Recettes"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    @property
    def total_cost(self):
        """Calcule le coût total de la recette"""
        total = Decimal('0.00')
        for recipe_ingredient in self.recipe_ingredients.all():
            total += recipe_ingredient.cost
        return total
    
    @property
    def cost_per_serving(self):
        """Calcule le coût par portion"""
        if self.servings > 0:
            return self.total_cost / self.servings
        return Decimal('0.00')
    
    @property
    def total_time(self):
        """Calcule le temps total (préparation + cuisson)"""
        prep = self.preparation_time or 0
        cook = self.cooking_time or 0
        return prep + cook

class RecipeIngredient(models.Model):
    UNIT_CHOICES = [
        # Poids
        ('g', 'grammes'),
        ('kg', 'kilogrammes'),
        # Volume
        ('ml', 'millilitres'),
        ('cl', 'centilitres'),
        ('l', 'litres'),
        # Quantité
        ('piece', 'pièce(s)'),
        ('c_soupe', 'cuillère(s) à soupe'),
        ('c_cafe', 'cuillère(s) à café'),
    ]
    
    recipe = models.ForeignKey(
        Recipe, 
        on_delete=models.CASCADE, 
        related_name='recipe_ingredients',
        verbose_name="Recette"
    )
    ingredient = models.ForeignKey(
        Ingredient, 
        on_delete=models.CASCADE,
        verbose_name="Ingrédient"
    )
    quantity = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Quantité"
    )
    unit = models.CharField(
        max_length=20, 
        choices=UNIT_CHOICES,
        verbose_name="Unité utilisée"
    )
    
    class Meta:
        verbose_name = "Ingrédient de recette"
        verbose_name_plural = "Ingrédients de recette"
        unique_together = ('recipe', 'ingredient')
    
    def __str__(self):
        return f"{self.quantity} {self.get_unit_display()} de {self.ingredient.name}"
    
    def get_quantity_in_base_unit(self):
        """Convertit la quantité vers l'unité de base"""
        conversion_factors = {
            'kg': 1000,  # vers grammes
            'g': 1,
            'l': 1000,   # vers ml
            'cl': 10,
            'ml': 1,
            'piece': 1,
            'c_soupe': 15,  # 1 c. à soupe ≈ 15ml
            'c_cafe': 5,    # 1 c. à café ≈ 5ml
        }
        
        factor = conversion_factors.get(self.unit, 1)
        return self.quantity * factor
    
    @property
    def cost(self):
        """Calcule le coût de cet ingrédient dans la recette avec conversion d'unités"""
        base_quantity = self.get_quantity_in_base_unit()
        price_per_base_unit = self.ingredient.get_price_per_base_unit()
        return base_quantity * price_per_base_unit