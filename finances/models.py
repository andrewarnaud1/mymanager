# finances/models.py
from django.db import models
from decimal import Decimal
from django.utils import timezone
from datetime import date
import calendar

class DailySale(models.Model):
    """
    Modèle pour les ventes journalières basé sur la structure Excel
    """
    # Date et identifiants
    date = models.DateField(verbose_name="Date", unique=True)
    
    # Carte bancaire
    cb_caisse = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        verbose_name="CB Caisse", help_text="Montant CB selon la caisse"
    )
    cb_tpe = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        verbose_name="CB TPE", help_text="Montant CB selon le TPE"
    )
    cb_ecart = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="Écart CB", help_text="Différence CB TPE - CB Caisse"
    )
    
    # Espèces
    especes_caisse = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        verbose_name="Espèces Caisse", help_text="Montant espèces selon la caisse"
    )
    especes_reel = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        verbose_name="Espèces Réel", help_text="Montant espèces compté"
    )
    especes_ecart = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="Écart Espèces", help_text="Différence Espèces Réel - Espèces Caisse"
    )
    
    # Tickets restaurant
    tr_caisse = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        verbose_name="TR Caisse", help_text="Tickets restaurant selon la caisse"
    )
    tr_reel = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        verbose_name="TR Réel", help_text="Tickets restaurant comptés"
    )
    tr_ecart = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="Écart TR", help_text="Différence TR Réel - TR Caisse"
    )
    
    # Totaux
    total_journalier = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="Total Journalier", help_text="Total des ventes de la journée"
    )
    ecart_total = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="Écart Total", help_text="Écart total de la journée"
    )
    
    # Statistiques clients (optionnel)
    nombre_clients = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name="Nombre de clients"
    )
    ticket_moyen = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        verbose_name="Ticket moyen"
    )
    
    # Informations complémentaires
    commentaires = models.TextField(
        blank=True,
        verbose_name="Commentaires",
        help_text="Notes et commentaires sur cette journée"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    imported_from_excel = models.BooleanField(
        default=False,
        verbose_name="Importé depuis Excel"
    )
    
    class Meta:
        verbose_name = "Vente journalière"
        verbose_name_plural = "Ventes journalières"
        ordering = ['-date']
    
    def __str__(self):
        return f"Ventes du {self.date.strftime('%d/%m/%Y')} - {self.total_journalier}€"
    
    def save(self, *args, **kwargs):
        """Calcul automatique des écarts et totaux"""
        # Calcul des écarts
        if self.cb_caisse is not None and self.cb_tpe is not None:
            self.cb_ecart = self.cb_tpe - self.cb_caisse
        
        if self.especes_caisse is not None and self.especes_reel is not None:
            self.especes_ecart = self.especes_reel - self.especes_caisse
        
        if self.tr_caisse is not None and self.tr_reel is not None:
            self.tr_ecart = self.tr_reel - self.tr_caisse
        
        # Calcul du total journalier (basé sur les montants réels ou caisse si réel non disponible)
        total = Decimal('0.00')
        if self.cb_tpe is not None:
            total += self.cb_tpe
        elif self.cb_caisse is not None:
            total += self.cb_caisse
            
        if self.especes_reel is not None:
            total += self.especes_reel
        elif self.especes_caisse is not None:
            total += self.especes_caisse
            
        if self.tr_reel is not None:
            total += self.tr_reel
        elif self.tr_caisse is not None:
            total += self.tr_caisse
        
        self.total_journalier = total
        
        # Calcul de l'écart total
        self.ecart_total = self.cb_ecart + self.especes_ecart + self.tr_ecart
        
        # Calcul du ticket moyen si nombre de clients disponible
        if self.nombre_clients and self.nombre_clients > 0:
            self.ticket_moyen = self.total_journalier / self.nombre_clients
        
        super().save(*args, **kwargs)
    
    @property
    def chiffre_affaires_cb(self):
        """Retourne le CA CB (TPE prioritaire)"""
        return self.cb_tpe or self.cb_caisse or Decimal('0.00')
    
    @property
    def chiffre_affaires_especes(self):
        """Retourne le CA espèces (réel prioritaire)"""
        return self.especes_reel or self.especes_caisse or Decimal('0.00')
    
    @property
    def chiffre_affaires_tr(self):
        """Retourne le CA tickets restaurant (réel prioritaire)"""
        return self.tr_reel or self.tr_caisse or Decimal('0.00')
    
    @property
    def has_ecarts(self):
        """Indique s'il y a des écarts sur cette journée"""
        return abs(self.ecart_total) > Decimal('0.01')
    
    @property
    def mois_annee(self):
        """Retourne mois/année pour regroupement"""
        return f"{self.date.year}-{self.date.month:02d}"


class MonthlySummary(models.Model):
    """
    Résumé mensuel calculé automatiquement
    """
    annee = models.PositiveIntegerField(verbose_name="Année")
    mois = models.PositiveIntegerField(verbose_name="Mois", choices=[
        (1, 'Janvier'), (2, 'Février'), (3, 'Mars'), (4, 'Avril'),
        (5, 'Mai'), (6, 'Juin'), (7, 'Juillet'), (8, 'Août'),
        (9, 'Septembre'), (10, 'Octobre'), (11, 'Novembre'), (12, 'Décembre')
    ])
    
    # Totaux mensuels
    total_ca = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="CA Total"
    )
    total_cb = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="CA Carte Bancaire"
    )
    total_especes = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="CA Espèces"
    )
    total_tr = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="CA Tickets Restaurant"
    )
    
    # Moyennes
    ca_moyen_jour = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="CA moyen par jour"
    )
    ticket_moyen_mensuel = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        verbose_name="Ticket moyen mensuel"
    )
    
    # Statistiques
    jours_ouverture = models.PositiveIntegerField(
        default=0, verbose_name="Jours d'ouverture"
    )
    total_clients = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Total clients"
    )
    
    # Écarts
    total_ecarts = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="Total des écarts"
    )
    
    # Métadonnées
    last_calculated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Résumé mensuel"
        verbose_name_plural = "Résumés mensuels"
        unique_together = ('annee', 'mois')
        ordering = ['-annee', '-mois']
    
    def __str__(self):
        return f"{calendar.month_name[self.mois]} {self.annee} - {self.total_ca}€"
    
    @classmethod
    def recalculate_for_month(cls, annee, mois):
        """Recalcule les statistiques pour un mois donné"""
        sales = DailySale.objects.filter(
            date__year=annee,
            date__month=mois
        )
        
        if not sales.exists():
            # Supprimer le résumé s'il n'y a pas de ventes
            cls.objects.filter(annee=annee, mois=mois).delete()
            return None
        
        # Calculs
        total_ca = sum(sale.total_journalier for sale in sales)
        total_cb = sum(sale.chiffre_affaires_cb for sale in sales)
        total_especes = sum(sale.chiffre_affaires_especes for sale in sales)
        total_tr = sum(sale.chiffre_affaires_tr for sale in sales)
        total_ecarts = sum(sale.ecart_total for sale in sales)
        
        jours_ouverture = sales.filter(total_journalier__gt=0).count()
        total_clients = sum(sale.nombre_clients for sale in sales if sale.nombre_clients)
        
        ca_moyen_jour = total_ca / jours_ouverture if jours_ouverture > 0 else 0
        ticket_moyen = total_ca / total_clients if total_clients > 0 else None
        
        # Créer ou mettre à jour
        summary, created = cls.objects.update_or_create(
            annee=annee,
            mois=mois,
            defaults={
                'total_ca': total_ca,
                'total_cb': total_cb,
                'total_especes': total_especes,
                'total_tr': total_tr,
                'ca_moyen_jour': ca_moyen_jour,
                'ticket_moyen_mensuel': ticket_moyen,
                'jours_ouverture': jours_ouverture,
                'total_clients': total_clients,
                'total_ecarts': total_ecarts,
            }
        )
        
        return summary


class ExcelImportLog(models.Model):
    """
    Journal des imports Excel
    """
    filename = models.CharField(max_length=255, verbose_name="Nom du fichier")
    imported_at = models.DateTimeField(auto_now_add=True, verbose_name="Importé le")
    nb_records_created = models.PositiveIntegerField(
        default=0, verbose_name="Enregistrements créés"
    )
    nb_records_updated = models.PositiveIntegerField(
        default=0, verbose_name="Enregistrements mis à jour"
    )
    nb_records_skipped = models.PositiveIntegerField(
        default=0, verbose_name="Enregistrements ignorés"
    )
    errors = models.TextField(
        blank=True, verbose_name="Erreurs rencontrées"
    )
    success = models.BooleanField(default=True, verbose_name="Import réussi")
    
    class Meta:
        verbose_name = "Journal d'import Excel"
        verbose_name_plural = "Journaux d'import Excel"
        ordering = ['-imported_at']
    
    def __str__(self):
        status = "✓" if self.success else "✗"
        return f"{status} {self.filename} - {self.imported_at.strftime('%d/%m/%Y %H:%M')}"


# Signaux pour recalcul automatique des résumés mensuels
def update_monthly_summary_handler(sender, instance, **kwargs):
    """Recalcule automatiquement le résumé mensuel quand une vente est modifiée"""
    MonthlySummary.recalculate_for_month(instance.date.year, instance.date.month)

# Connecter les signaux après la définition des modèles
from django.db.models.signals import post_save, post_delete

post_save.connect(update_monthly_summary_handler, sender=DailySale)
post_delete.connect(update_monthly_summary_handler, sender=DailySale)