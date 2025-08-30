# quotes/models.py
from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from recipes.models import Recipe

class Customer(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nom")
    company = models.CharField(max_length=200, blank=True, verbose_name="Entreprise")
    email = models.EmailField(blank=True, verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    address = models.TextField(blank=True, verbose_name="Adresse")
    city = models.CharField(max_length=100, blank=True, verbose_name="Ville")
    postal_code = models.CharField(max_length=10, blank=True, verbose_name="Code postal")
    country = models.CharField(max_length=100, default="France", verbose_name="Pays")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.company})" if self.company else self.name
    
    @property
    def full_address(self):
        """Retourne l'adresse complète formatée"""
        parts = [self.address, self.postal_code, self.city, self.country]
        return ", ".join([part for part in parts if part])

class Quote(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('sent', 'Envoyé'),
        ('accepted', 'Accepté'),
        ('declined', 'Refusé'),
        ('expired', 'Expiré'),
    ]
    
    # Informations de base
    quote_number = models.CharField(max_length=50, unique=True, verbose_name="Numéro de devis")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="Client")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="Statut")
    
    # Dates
    quote_date = models.DateField(verbose_name="Date du devis")
    valid_until = models.DateField(verbose_name="Valable jusqu'au")
    event_date = models.DateField(blank=True, null=True, verbose_name="Date de l'événement")
    
    # Informations commerciales
    title = models.CharField(max_length=200, verbose_name="Objet du devis")
    description = models.TextField(blank=True, verbose_name="Description")
    
    # Paramètres financiers
    discount_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        verbose_name="Remise (%)"
    )
    tax_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=20,
        verbose_name="Taux TVA (%)"
    )
    
    # Notes
    terms_conditions = models.TextField(
        blank=True,
        verbose_name="Conditions générales",
        help_text="Conditions particulières pour ce devis"
    )
    internal_notes = models.TextField(
        blank=True,
        verbose_name="Notes internes",
        help_text="Notes privées, non visibles sur le devis"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Créé par")
    
    class Meta:
        verbose_name = "Devis"
        verbose_name_plural = "Devis"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Devis {self.quote_number} - {self.customer.name}"
    
    def save(self, *args, **kwargs):
        if not self.quote_number:
            # Génération automatique du numéro de devis
            from datetime import date
            today = date.today()
            year = today.year
            
            # Compter les devis de l'année
            count = Quote.objects.filter(
                quote_date__year=year
            ).count() + 1
            
            self.quote_number = f"DEV{year}-{count:04d}"
        
        super().save(*args, **kwargs)
    
    @property
    def subtotal(self):
        """Calcule le sous-total (avant remise et TVA)"""
        total = Decimal('0.00')
        for item in self.quote_items.all():
            total += item.total_price
        return total
    
    @property
    def discount_amount(self):
        """Calcule le montant de la remise"""
        return self.subtotal * (self.discount_percentage / 100)
    
    @property
    def subtotal_after_discount(self):
        """Sous-total après remise"""
        return self.subtotal - self.discount_amount
    
    @property
    def tax_amount(self):
        """Calcule le montant de la TVA"""
        return self.subtotal_after_discount * (self.tax_rate / 100)
    
    @property
    def total_amount(self):
        """Calcule le montant total TTC"""
        return self.subtotal_after_discount + self.tax_amount
    
    @property
    def total_cost(self):
        """Calcule le coût total de revient"""
        total = Decimal('0.00')
        for item in self.quote_items.all():
            total += item.total_cost
        return total
    
    @property
    def profit_margin(self):
        """Calcule la marge bénéficiaire en euros"""
        return self.subtotal_after_discount - self.total_cost
    
    @property
    def profit_margin_percentage(self):
        """Calcule la marge bénéficiaire en pourcentage"""
        if self.total_cost > 0:
            return (self.profit_margin / self.total_cost) * 100
        return Decimal('0.00')

class QuoteItem(models.Model):
    quote = models.ForeignKey(
        Quote, 
        on_delete=models.CASCADE, 
        related_name='quote_items',
        verbose_name="Devis"
    )
    recipe = models.ForeignKey(
        Recipe, 
        on_delete=models.CASCADE,
        verbose_name="Recette"
    )
    quantity = models.PositiveIntegerField(verbose_name="Quantité (portions)")
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name="Prix unitaire"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description personnalisée",
        help_text="Description spécifique pour ce devis (optionnel)"
    )
    
    class Meta:
        verbose_name = "Ligne de devis"
        verbose_name_plural = "Lignes de devis"
    
    def __str__(self):
        return f"{self.quantity}x {self.recipe.name}"
    
    @property
    def total_price(self):
        """Prix total de cette ligne (quantité × prix unitaire)"""
        return self.quantity * self.unit_price
    
    @property
    def total_cost(self):
        """Coût total de cette ligne (quantité × coût de revient)"""
        return self.quantity * self.recipe.cost_per_serving
    
    @property
    def margin_per_item(self):
        """Marge par portion"""
        return self.unit_price - self.recipe.cost_per_serving
    
    @property
    def total_margin(self):
        """Marge totale de cette ligne"""
        return self.quantity * self.margin_per_item
    

class CompanySettings(models.Model):
    """Paramètres de l'entreprise pour les devis"""
    name = models.CharField(max_length=200, verbose_name="Nom de l'entreprise")
    address = models.TextField(verbose_name="Adresse")
    phone = models.CharField(max_length=20, verbose_name="Téléphone")
    email = models.EmailField(verbose_name="Email")
    siret = models.CharField(max_length=14, blank=True, verbose_name="SIRET")
    tva_number = models.CharField(max_length=20, blank=True, verbose_name="Numéro TVA")
    logo = models.ImageField(upload_to='company/', blank=True, verbose_name="Logo")
    
    # Conditions par défaut
    default_terms = models.TextField(
        blank=True,
        verbose_name="Conditions générales par défaut",
        help_text="Conditions qui apparaîtront sur tous les devis"
    )
    
    # Paramètres de paiement
    payment_terms = models.TextField(
        default="30% d'acompte à la commande, solde à la livraison.",
        verbose_name="Modalités de paiement"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Paramètres entreprise"
        verbose_name_plural = "Paramètres entreprise"
    
    def __str__(self):
        return self.name
    
    @classmethod
    def get_settings(cls):
        """Récupère les paramètres actuels ou crée des paramètres par défaut"""
        settings, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                'name': 'Restaurant Manager',
                'address': '123 Rue de la Gastronomie\n75001 Paris, France',
                'phone': '01 23 45 67 89',
                'email': 'contact@restaurant-manager.fr',
                'siret': '123 456 789 00012',
                'tva_number': 'FR12345678901'
            }
        )
        return settings