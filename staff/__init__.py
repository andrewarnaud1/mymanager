"""
Module de gestion du personnel et des plannings

Ce module permet de :
- Gérer les employés (internes avec comptes et externes)
- Créer des plannings hebdomadaires
- Gérer les créneaux de travail
- Exporter les plannings en PDF et Excel
- Convertir des employés externes en internes

Dépendances optionnelles :
- reportlab : pour l'export PDF
- openpyxl : pour l'export Excel

Configuration requise :
- Ajouter 'staff' dans INSTALLED_APPS
- Inclure les URLs dans le projet principal
"""

default_app_config = 'staff.apps.StaffConfig'
