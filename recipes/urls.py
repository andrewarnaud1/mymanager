
from django.urls import path
from . import views

app_name = 'recipes'

urlpatterns = [
    # Recettes
    path('', views.recipes_list, name='list'),
    path('nouveau/', views.recipe_create, name='create'),
    path('<int:pk>/', views.recipe_detail, name='detail'),
    path('<int:pk>/modifier/', views.recipe_update, name='update'),
    path('<int:pk>/supprimer/', views.recipe_delete, name='delete'),
    
    # Ingrédients
    path('ingredients/', views.ingredients_list, name='ingredients'),
    path('ingredients/nouveau/', views.ingredient_create, name='ingredient_create'),
    path('ingredients/<int:pk>/modifier/', views.ingredient_update, name='ingredient_update'),
    path('ingredients/<int:pk>/supprimer/', views.ingredient_delete, name='ingredient_delete'),
]