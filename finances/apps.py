# finances/apps.py
from django.apps import AppConfig

class FinancesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'finances'
    verbose_name = 'Finances'
    
    def ready(self):
        """Importer les signaux quand l'application est prête"""
        import finances.signals