# finances/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import DailySale, MonthlySummary

@receiver([post_save, post_delete], sender=DailySale)
def update_monthly_summary(sender, instance, **kwargs):
    """Recalcule automatiquement le résumé mensuel quand une vente est modifiée"""
    try:
        MonthlySummary.recalculate_for_month(instance.date.year, instance.date.month)
    except Exception as e:
        # En cas d'erreur, continuer sans faire planter l'application
        print(f"Erreur lors du recalcul du résumé mensuel: {e}")