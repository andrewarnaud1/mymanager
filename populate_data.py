#!/usr/bin/env python
"""
Script de génération de données fictives pour MyManager
Utilise Django ORM pour créer des données de test réalistes
"""

import os
import sys
import django
from datetime import date, datetime, timedelta
from decimal import Decimal
import random

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mymanager.settings')
django.setup()

from django.contrib.auth.models import User
from staff.models import Employee, WeeklySchedule, Shift
from finances.models import DailySale, MonthlySummary
from quotes.models import Customer, Quote, QuoteItem, CompanySettings
from recipes.models import Ingredient, Recipe, RecipeIngredient

class DataPopulator:
    def __init__(self):
        self.users = []
        self.employees = []
        self.customers = []
        self.ingredients = []
        self.recipes = []
        self.quotes = []
        
    def run(self):
        """Exécute toutes les étapes de création de données"""
        print("🚀 Démarrage de la génération de données fictives...")
        
        self.create_superuser()
        self.create_users()
        self.create_employees()
        self.create_staff_schedules()
        self.create_ingredients()
        self.create_recipes()
        self.create_customers()
        self.create_quotes()
        self.create_company_settings()
        self.create_sales_data()
        
        print("✅ Génération de données terminée avec succès!")
        print("\n📊 Résumé des données créées:")
        print(f"- {User.objects.count()} utilisateurs")
        print(f"- {Employee.objects.count()} employés")
        print(f"- {Ingredient.objects.count()} ingrédients")
        print(f"- {Recipe.objects.count()} recettes")
        print(f"- {Customer.objects.count()} clients")
        print(f"- {Quote.objects.count()} devis")
        print(f"- {DailySale.objects.count()} ventes journalières")
        print(f"- {WeeklySchedule.objects.count()} plannings hebdomadaires")
        print(f"- {Shift.objects.count()} créneaux de travail")
        
        print("\n🔑 Comptes de test:")
        print("- Superuser: admin / admin123")
        print("- Manager: manager / manager123")
        print("- Chef: chef / chef123")
        print("- Serveur1: serveur1 / serveur123")
        
    def create_superuser(self):
        """Crée un superutilisateur"""
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@restaurant.com',
                password='admin123',
                first_name='Admin',
                last_name='Restaurant'
            )
            print("✅ Superutilisateur créé: admin / admin123")
        
    def create_users(self):
        """Crée des utilisateurs de test"""
        users_data = [
            {'username': 'manager', 'email': 'manager@restaurant.com', 'password': 'manager123', 
             'first_name': 'Marie', 'last_name': 'Dupont', 'is_staff': True},
            {'username': 'chef', 'email': 'chef@restaurant.com', 'password': 'chef123',
             'first_name': 'Pierre', 'last_name': 'Martin', 'is_staff': True},
            {'username': 'serveur1', 'email': 'serveur1@restaurant.com', 'password': 'serveur123',
             'first_name': 'Julie', 'last_name': 'Bernard', 'is_staff': False},
            {'username': 'serveur2', 'email': 'serveur2@restaurant.com', 'password': 'serveur123',
             'first_name': 'Antoine', 'last_name': 'Rousseau', 'is_staff': False},
        ]
        
        for user_data in users_data:
            if not User.objects.filter(username=user_data['username']).exists():
                user = User.objects.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    password=user_data['password'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    is_staff=user_data['is_staff']
                )
                self.users.append(user)
                print(f"✅ Utilisateur créé: {user.username}")
    
    def create_employees(self):
        """Crée des employés (internes et externes)"""
        # Employés internes (liés aux utilisateurs)
        for user in User.objects.all():
            if user.username != 'admin':  # Skip admin
                employee = Employee.objects.create(
                    user=user,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    phone=f"0{random.randint(100000000, 999999999)}",
                    is_external=False,
                    hire_date=date.today() - timedelta(days=random.randint(30, 365))
                )
                self.employees.append(employee)
        
        # Employés externes (sans compte utilisateur)
        external_employees = [
            {'first_name': 'Sophie', 'last_name': 'Mercier', 'phone': '0612345678'},
            {'first_name': 'Thomas', 'last_name': 'Girard', 'phone': '0687654321'},
            {'first_name': 'Emma', 'last_name': 'Leroy', 'phone': '0698765432'},
        ]
        
        for emp_data in external_employees:
            employee = Employee.objects.create(
                first_name=emp_data['first_name'],
                last_name=emp_data['last_name'],
                phone=emp_data['phone'],
                is_external=True,
                hire_date=date.today() - timedelta(days=random.randint(10, 180))
            )
            self.employees.append(employee)
        
        print(f"✅ {len(self.employees)} employés créés")
    
    def create_staff_schedules(self):
        """Crée des plannings de travail"""
        # Créer des plannings pour les 4 dernières semaines et 2 semaines futures
        start_date = date.today() - timedelta(weeks=4)
        manager = User.objects.filter(username='manager').first() or User.objects.first()
        
        for week in range(6):  # 6 semaines
            week_start = start_date + timedelta(weeks=week)
            # S'assurer que c'est un lundi
            while week_start.weekday() != 0:
                week_start += timedelta(days=1)
            
            schedule = WeeklySchedule.objects.create(
                week_start=week_start,
                created_by=manager,
                notes=f"Planning de la semaine du {week_start.strftime('%d/%m/%Y')}"
            )
            
            # Créer des créneaux pour cette semaine
            self.create_shifts_for_week(schedule)
        
        print(f"✅ {WeeklySchedule.objects.count()} plannings hebdomadaires créés")
    
    def create_shifts_for_week(self, schedule):
        """Crée des créneaux de travail pour une semaine"""
        employees = list(Employee.objects.filter(is_active=True))
        if not employees:
            return
            
        # Horaires typiques d'un restaurant
        service_times = [
            ('11:30', '14:30'),  # Service déjeuner
            ('18:30', '22:30'),  # Service dîner
            ('09:00', '15:00'),  # Journée continue
            ('16:00', '23:00'),  # Soirée
        ]
        
        for day_offset in range(7):  # Lundi à dimanche
            shift_date = schedule.week_start + timedelta(days=day_offset)
            
            # Programmer 2-4 employés par jour avec différents créneaux
            daily_employees = random.sample(employees, min(random.randint(2, 4), len(employees)))
            
            for employee in daily_employees:
                if random.choice([True, False]):  # 50% de chance d'être programmé
                    start_time, end_time = random.choice(service_times)
                    
                    # Ajouter une variation aléatoire de ±30 minutes
                    start_hour, start_min = map(int, start_time.split(':'))
                    end_hour, end_min = map(int, end_time.split(':'))
                    
                    start_variation = random.randint(-30, 30)
                    end_variation = random.randint(-30, 30)
                    
                    start_datetime = datetime.combine(date.today(), datetime.min.time().replace(hour=start_hour, minute=start_min)) + timedelta(minutes=start_variation)
                    end_datetime = datetime.combine(date.today(), datetime.min.time().replace(hour=end_hour, minute=end_min)) + timedelta(minutes=end_variation)
                    
                    try:
                        Shift.objects.create(
                            schedule=schedule,
                            employee=employee,
                            date=shift_date,
                            start_time=start_datetime.time(),
                            end_time=end_datetime.time(),
                            notes=random.choice(['', 'Formation', 'Fermeture', 'Ouverture', ''])
                        )
                    except:
                        pass  # Ignorer les erreurs de validation
    
    def create_ingredients(self):
        """Crée des ingrédients de base"""
        ingredients_data = [
            # Légumes
            {'name': 'Tomates', 'unit': 'kg', 'price': '3.50'},
            {'name': 'Oignons', 'unit': 'kg', 'price': '2.20'},
            {'name': 'Carottes', 'unit': 'kg', 'price': '1.80'},
            {'name': 'Courgettes', 'unit': 'kg', 'price': '2.90'},
            {'name': 'Aubergines', 'unit': 'kg', 'price': '4.20'},
            {'name': 'Poivrons', 'unit': 'kg', 'price': '5.50'},
            {'name': 'Champignons de Paris', 'unit': 'kg', 'price': '6.80'},
            {'name': 'Salade verte', 'unit': 'piece', 'price': '1.50'},
            
            # Viandes
            {'name': 'Bœuf (entrecôte)', 'unit': 'kg', 'price': '25.00'},
            {'name': 'Porc (côtelettes)', 'unit': 'kg', 'price': '12.50'},
            {'name': 'Poulet (blanc)', 'unit': 'kg', 'price': '8.90'},
            {'name': 'Saumon', 'unit': 'kg', 'price': '18.50'},
            
            # Produits laitiers
            {'name': 'Beurre', 'unit': 'kg', 'price': '7.20'},
            {'name': 'Crème fraîche', 'unit': 'l', 'price': '4.50'},
            {'name': 'Lait', 'unit': 'l', 'price': '1.20'},
            {'name': 'Fromage râpé', 'unit': 'kg', 'price': '12.80'},
            {'name': 'Mozzarella', 'unit': 'kg', 'price': '8.90'},
            
            # Féculents
            {'name': 'Riz basmati', 'unit': 'kg', 'price': '3.80'},
            {'name': 'Pâtes fraîches', 'unit': 'kg', 'price': '4.50'},
            {'name': 'Pommes de terre', 'unit': 'kg', 'price': '1.50'},
            {'name': 'Farine', 'unit': 'kg', 'price': '1.20'},
            
            # Épices et condiments
            {'name': 'Huile d\'olive', 'unit': 'l', 'price': '8.50'},
            {'name': 'Sel', 'unit': 'kg', 'price': '0.80'},
            {'name': 'Poivre noir', 'unit': 'g', 'price': '0.05'},
            {'name': 'Ail', 'unit': 'kg', 'price': '6.50'},
            {'name': 'Persil', 'unit': 'g', 'price': '0.08'},
            {'name': 'Basilic', 'unit': 'g', 'price': '0.12'},
            {'name': 'Thym', 'unit': 'g', 'price': '0.10'},
            
            # Cuillères pour petites quantités
            {'name': 'Paprika', 'unit': 'c_cafe', 'price': '0.15'},
            {'name': 'Cumin', 'unit': 'c_cafe', 'price': '0.20'},
            {'name': 'Moutarde', 'unit': 'c_soupe', 'price': '0.25'},
        ]
        
        for ing_data in ingredients_data:
            ingredient = Ingredient.objects.create(
                name=ing_data['name'],
                unit=ing_data['unit'],
                unit_price=Decimal(ing_data['price'])
            )
            self.ingredients.append(ingredient)
        
        print(f"✅ {len(self.ingredients)} ingrédients créés")
    
    def create_recipes(self):
        """Crée des recettes avec leurs ingrédients"""
        recipes_data = [
            {
                'name': 'Ratatouille Provençale',
                'description': 'Délicieux mélange de légumes du soleil mijoté aux herbes de Provence',
                'servings': 6,
                'prep_time': 30,
                'cook_time': 45,
                'instructions': '''1. Laver et couper tous les légumes en dés
2. Faire revenir l'oignon et l'ail dans l'huile d'olive
3. Ajouter les aubergines et courgettes, cuire 10 min
4. Incorporer les tomates et poivrons
5. Assaisonner et laisser mijoter 30 minutes
6. Parsemer d'herbes fraîches avant de servir''',
                'ingredients': [
                    ('Aubergines', 800, 'g'),
                    ('Courgettes', 600, 'g'),
                    ('Tomates', 1000, 'g'),
                    ('Poivrons', 400, 'g'),
                    ('Oignons', 200, 'g'),
                    ('Ail', 30, 'g'),
                    ('Huile d\'olive', 50, 'ml'),
                    ('Basilic', 20, 'g'),
                    ('Thym', 5, 'g'),
                ]
            },
            {
                'name': 'Risotto aux Champignons',
                'description': 'Risotto crémeux aux champignons de Paris et parmesan',
                'servings': 4,
                'prep_time': 15,
                'cook_time': 25,
                'instructions': '''1. Faire revenir les champignons dans le beurre
2. Ajouter le riz et nacrer 2 minutes
3. Incorporer le bouillon chaud louche par louche
4. Remuer constamment pendant 18 minutes
5. Incorporer le fromage râpé et rectifier l'assaisonnement''',
                'ingredients': [
                    ('Riz basmati', 320, 'g'),
                    ('Champignons de Paris', 400, 'g'),
                    ('Oignons', 100, 'g'),
                    ('Fromage râpé', 100, 'g'),
                    ('Beurre', 50, 'g'),
                    ('Huile d\'olive', 30, 'ml'),
                ]
            },
            {
                'name': 'Saumon Grillé aux Herbes',
                'description': 'Pavé de saumon grillé avec un mélange d\'herbes fraîches',
                'servings': 4,
                'prep_time': 10,
                'cook_time': 15,
                'instructions': '''1. Mélanger les herbes hachées avec l'huile d'olive
2. Badigeonner les pavés de saumon
3. Griller 6-8 minutes de chaque côté
4. Servir immédiatement avec le mélange d'herbes''',
                'ingredients': [
                    ('Saumon', 800, 'g'),
                    ('Persil', 15, 'g'),
                    ('Basilic', 10, 'g'),
                    ('Thym', 5, 'g'),
                    ('Huile d\'olive', 40, 'ml'),
                    ('Sel', 5, 'g'),
                ]
            },
            {
                'name': 'Gratin de Pommes de Terre',
                'description': 'Gratin dauphinois traditionnel à la crème fraîche',
                'servings': 8,
                'prep_time': 20,
                'cook_time': 60,
                'instructions': '''1. Éplucher et trancher finement les pommes de terre
2. Disposer en couches dans un plat beurré
3. Mélanger crème, lait, ail écrasé et assaisonnement
4. Verser sur les pommes de terre
5. Cuire au four 1h à 180°C''',
                'ingredients': [
                    ('Pommes de terre', 1500, 'g'),
                    ('Crème fraîche', 300, 'ml'),
                    ('Lait', 200, 'ml'),
                    ('Ail', 20, 'g'),
                    ('Beurre', 30, 'g'),
                    ('Fromage râpé', 100, 'g'),
                ]
            },
            {
                'name': 'Pâtes à la Carbonara',
                'description': 'Pâtes crémeuses aux lardons et parmesan',
                'servings': 4,
                'prep_time': 5,
                'cook_time': 15,
                'instructions': '''1. Cuire les pâtes al dente
2. Faire revenir les lardons
3. Mélanger jaunes d'œufs et fromage
4. Incorporer aux pâtes chaudes hors du feu
5. Ajouter les lardons et servir immédiatement''',
                'ingredients': [
                    ('Pâtes fraîches', 400, 'g'),
                    ('Fromage râpé', 100, 'g'),
                    ('Crème fraîche', 150, 'ml'),
                    ('Huile d\'olive', 20, 'ml'),
                ]
            },
        ]
        
        for recipe_data in recipes_data:
            recipe = Recipe.objects.create(
                name=recipe_data['name'],
                description=recipe_data['description'],
                servings=recipe_data['servings'],
                preparation_time=recipe_data['prep_time'],
                cooking_time=recipe_data['cook_time'],
                instructions=recipe_data['instructions']
            )
            
            # Ajouter les ingrédients à la recette
            for ing_name, quantity, unit in recipe_data['ingredients']:
                try:
                    ingredient = Ingredient.objects.get(name=ing_name)
                    RecipeIngredient.objects.create(
                        recipe=recipe,
                        ingredient=ingredient,
                        quantity=Decimal(str(quantity)),
                        unit=unit
                    )
                except Ingredient.DoesNotExist:
                    print(f"⚠️  Ingrédient '{ing_name}' non trouvé pour la recette '{recipe.name}'")
            
            self.recipes.append(recipe)
        
        print(f"✅ {len(self.recipes)} recettes créées")
    
    def create_customers(self):
        """Crée des clients"""
        customers_data = [
            {
                'name': 'Jean-Pierre Dubois',
                'company': 'Mairie de Bordeaux',
                'email': 'jp.dubois@bordeaux.fr',
                'phone': '0556123456',
                'address': '12 Place Pey-Berland',
                'city': 'Bordeaux',
                'postal_code': '33000'
            },
            {
                'name': 'Marie Lefevre',
                'company': 'Société Générale',
                'email': 'marie.lefevre@sg.com',
                'phone': '0157894562',
                'address': '29 Boulevard Haussmann',
                'city': 'Paris',
                'postal_code': '75009'
            },
            {
                'name': 'Paul Martin',
                'company': '',
                'email': 'paul.martin@gmail.com',
                'phone': '0698765432',
                'address': '45 Rue de la République',
                'city': 'Lyon',
                'postal_code': '69002'
            },
            {
                'name': 'Sophie Rousseau',
                'company': 'Wedding Planner Pro',
                'email': 'sophie@weddingplannerpro.fr',
                'phone': '0612345678',
                'address': '78 Avenue des Champs-Élysées',
                'city': 'Paris',
                'postal_code': '75008'
            },
            {
                'name': 'Thomas Girard',
                'company': 'Entreprise Girard & Fils',
                'email': 'contact@girard-fils.com',
                'phone': '0467891234',
                'address': '156 Rue du Faubourg Saint-Antoine',
                'city': 'Montpellier',
                'postal_code': '34000'
            },
            {
                'name': 'Isabelle Moreau',
                'company': 'Centre Culturel Municipal',
                'email': 'i.moreau@centreculturel.fr',
                'phone': '0298765431',
                'address': '23 Place du Marché',
                'city': 'Brest',
                'postal_code': '29200'
            },
            {
                'name': 'David Leclerc',
                'company': 'Hotel Le Grand Palais',
                'email': 'direction@grandpalais-hotel.fr',
                'phone': '0493876543',
                'address': '67 Promenade des Anglais',
                'city': 'Nice',
                'postal_code': '06000'
            }
        ]
        
        for cust_data in customers_data:
            customer = Customer.objects.create(**cust_data)
            self.customers.append(customer)
        
        print(f"✅ {len(self.customers)} clients créés")
    
    def create_quotes(self):
        """Crée des devis"""
        if not self.customers or not self.recipes:
            print("⚠️  Impossible de créer des devis sans clients et recettes")
            return
        
        creator = User.objects.filter(username='manager').first() or User.objects.first()
        
        quotes_data = [
            {
                'customer': self.customers[0],
                'title': 'Cocktail de fin d\'année - Mairie',
                'description': 'Prestation traiteur pour 150 personnes lors du cocktail de fin d\'année de la mairie',
                'status': 'accepted',
                'event_date': date.today() + timedelta(days=45),
                'items': [
                    (self.recipes[0], 25, Decimal('12.50')),  # Ratatouille pour 150 personnes
                    (self.recipes[2], 20, Decimal('18.00')),  # Saumon
                ]
            },
            {
                'customer': self.customers[3],
                'title': 'Mariage Sophie & Antoine',
                'description': 'Repas de mariage pour 80 convives avec menu 3 services',
                'status': 'sent',
                'event_date': date.today() + timedelta(days=120),
                'items': [
                    (self.recipes[1], 20, Decimal('15.00')),  # Risotto
                    (self.recipes[2], 20, Decimal('22.00')),  # Saumon
                    (self.recipes[3], 10, Decimal('8.50')),   # Gratin
                ]
            },
            {
                'customer': self.customers[1],
                'title': 'Séminaire d\'entreprise',
                'description': 'Déjeuner d\'affaires pour 40 personnes',
                'status': 'draft',
                'event_date': date.today() + timedelta(days=30),
                'items': [
                    (self.recipes[4], 10, Decimal('14.00')),  # Carbonara
                    (self.recipes[0], 7, Decimal('10.00')),   # Ratatouille
                ]
            },
            {
                'customer': self.customers[6],
                'title': 'Événement hôtel - Buffet gastronomique',
                'description': 'Buffet haut de gamme pour 200 personnes',
                'status': 'accepted',
                'event_date': date.today() + timedelta(days=60),
                'items': [
                    (self.recipes[0], 35, Decimal('11.00')),
                    (self.recipes[1], 30, Decimal('16.50')),
                    (self.recipes[2], 50, Decimal('20.00')),
                ]
            },
            {
                'customer': self.customers[4],
                'title': 'Inauguration entreprise',
                'description': 'Cocktail dînatoire pour l\'inauguration des nouveaux locaux',
                'status': 'declined',
                'event_date': date.today() + timedelta(days=15),
                'items': [
                    (self.recipes[0], 15, Decimal('13.00')),
                    (self.recipes[4], 12, Decimal('15.50')),
                ]
            }
        ]
        
        for i, quote_data in enumerate(quotes_data, 1):
            quote_date = date.today() - timedelta(days=random.randint(1, 30))
            valid_until = quote_date + timedelta(days=30)
            
            quote = Quote.objects.create(
                customer=quote_data['customer'],
                title=quote_data['title'],
                description=quote_data['description'],
                status=quote_data['status'],
                quote_date=quote_date,
                valid_until=valid_until,
                event_date=quote_data['event_date'],
                discount_percentage=random.choice([0, 5, 10]) if random.choice([True, False]) else 0,
                tax_rate=Decimal('20.00'),
                created_by=creator
            )
            
            # Ajouter les lignes de devis
            for recipe, quantity, unit_price in quote_data['items']:
                QuoteItem.objects.create(
                    quote=quote,
                    recipe=recipe,
                    quantity=quantity,
                    unit_price=unit_price
                )
            
            self.quotes.append(quote)
        
        print(f"✅ {len(self.quotes)} devis créés")
    
    def create_company_settings(self):
        """Crée les paramètres de l'entreprise"""
        if not CompanySettings.objects.exists():
            CompanySettings.objects.create(
                name="Restaurant Le Gourmet",
                address="123 Avenue de la Gastronomie\n75001 Paris, France",
                phone="01 42 36 85 47",
                email="contact@restaurant-legourmet.fr",
                siret="123 456 789 00012",
                tva_number="FR12345678901",
                default_terms="""Conditions générales de vente :
- Les prix sont exprimés en euros TTC
- Acompte de 30% à la commande
- Solde à la livraison
- Prestations réalisées avec des produits frais de saison
- Annulation possible jusqu'à 48h avant l'événement""",
                payment_terms="30% d'acompte à la commande, solde à la livraison par chèque ou virement bancaire."
            )
            print("✅ Paramètres entreprise créés")
    
    def create_sales_data(self):
        """Crée des données de ventes sur les 3 derniers mois"""
        end_date = date.today()
        start_date = end_date - timedelta(days=90)
        
        current_date = start_date
        while current_date <= end_date:
            # Simuler des jours d'ouverture (pas tous les jours)
            if random.choice([True, True, True, True, True, False]):  # 83% chance d'ouverture
                # Générer des ventes réalistes
                base_ca = random.uniform(800, 2500)  # CA de base
                
                # Variation selon le jour de la semaine
                day_multipliers = {
                    0: 0.8,   # Lundi
                    1: 0.9,   # Mardi
                    2: 1.0,   # Mercredi
                    3: 1.1,   # Jeudi
                    4: 1.3,   # Vendredi
                    5: 1.4,   # Samedi
                    6: 0.7,   # Dimanche
                }
                
                multiplier = day_multipliers.get(current_date.weekday(), 1.0)
                daily_ca = base_ca * multiplier
                
                # Répartition par mode de paiement
                cb_ratio = random.uniform(0.6, 0.8)
                especes_ratio = random.uniform(0.15, 0.3)
                tr_ratio = 1 - cb_ratio - especes_ratio
                
                cb_amount = daily_ca * cb_ratio
                especes_amount = daily_ca * especes_ratio
                tr_amount = daily_ca * tr_ratio
                
                # Ajouter des écarts réalistes
                cb_ecart = random.uniform(-5, 5)
                especes_ecart = random.uniform(-10, 15)
                tr_ecart = random.uniform(-2, 3)
                
                # Nombre de clients
                nb_clients = random.randint(40, 120)
                
                DailySale.objects.create(
                    date=current_date,
                    cb_caisse=Decimal(str(round(cb_amount, 2))),
                    cb_tpe=Decimal(str(round(cb_amount + cb_ecart, 2))),
                    especes_caisse=Decimal(str(round(especes_amount, 2))),
                    especes_reel=Decimal(str(round(especes_amount + especes_ecart, 2))),
                    tr_caisse=Decimal(str(round(tr_amount, 2))),
                    tr_reel=Decimal(str(round(tr_amount + tr_ecart, 2))),
                    nombre_clients=nb_clients,
                    commentaires=random.choice(['', 'Soirée événement privé', 'Forte affluence', 'Jour férié', ''])
                )
            
            current_date += timedelta(days=1)
        
        print(f"✅ {DailySale.objects.count()} ventes journalières créées")
        
        # Recalculer les résumés mensuels
        for year in range(end_date.year - 1, end_date.year + 1):
            for month in range(1, 13):
                MonthlySummary.recalculate_for_month(year, month)
        
        print(f"✅ {MonthlySummary.objects.count()} résumés mensuels calculés")

if __name__ == '__main__':
    populator = DataPopulator()
    populator.run()
