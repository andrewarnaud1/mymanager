# finances/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from .models import DailySale, MonthlySummary, ExcelImportLog

@admin.register(DailySale)
class DailySaleAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'total_journalier', 'chiffre_affaires_cb', 
        'chiffre_affaires_especes', 'chiffre_affaires_tr',
        'ecart_total_colored', 'nombre_clients', 'imported_from_excel'
    ]
    list_filter = [
        'imported_from_excel', 'date', 'nombre_clients'
    ]
    search_fields = ['commentaires']
    ordering = ['-date']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Date et identification', {
            'fields': ('date', 'imported_from_excel')
        }),
        ('Carte Bancaire', {
            'fields': ('cb_caisse', 'cb_tpe', 'cb_ecart'),
            'classes': ['collapse']
        }),
        ('Espèces', {
            'fields': ('especes_caisse', 'especes_reel', 'especes_ecart'),
            'classes': ['collapse']
        }),
        ('Tickets Restaurant', {
            'fields': ('tr_caisse', 'tr_reel', 'tr_ecart'),
            'classes': ['collapse']
        }),
        ('Totaux', {
            'fields': ('total_journalier', 'ecart_total')
        }),
        ('Statistiques clients', {
            'fields': ('nombre_clients', 'ticket_moyen'),
            'classes': ['collapse']
        }),
        ('Commentaires', {
            'fields': ('commentaires',),
            'classes': ['collapse']
        })
    )
    
    readonly_fields = ['cb_ecart', 'especes_ecart', 'tr_ecart', 'total_journalier', 'ecart_total', 'ticket_moyen']
    
    def ecart_total_colored(self, obj):
        """Affiche l'écart total avec couleur selon le signe"""
        if abs(obj.ecart_total) < 0.01:
            return format_html('<span style="color: green;">0.00€</span>')
        elif obj.ecart_total > 0:
            return format_html('<span style="color: blue;">+{:.2f}€</span>', obj.ecart_total)
        else:
            return format_html('<span style="color: red;">{:.2f}€</span>', obj.ecart_total)
    ecart_total_colored.short_description = 'Écart Total'
    ecart_total_colored.admin_order_field = 'ecart_total'
    
    def get_changelist_footers(self, request, results):
        """Ajoute des totaux en bas de liste"""
        if results:
            total_ca = sum(r.total_journalier for r in results)
            total_ecarts = sum(r.ecart_total for r in results)
            return {
                'total_ca': f"{total_ca:.2f}€",
                'total_ecarts': f"{total_ecarts:.2f}€",
                'nb_jours': len(results)
            }
        return {}


@admin.register(MonthlySummary)
class MonthlySummaryAdmin(admin.ModelAdmin):
    list_display = [
        'mois_annee_display', 'total_ca', 'jours_ouverture', 
        'ca_moyen_jour', 'total_clients', 'ticket_moyen_mensuel',
        'total_ecarts', 'last_calculated'
    ]
    list_filter = ['annee', 'mois']
    ordering = ['-annee', '-mois']
    
    def mois_annee_display(self, obj):
        mois_names = [
            '', 'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
            'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
        ]
        return f"{mois_names[obj.mois]} {obj.annee}"
    mois_annee_display.short_description = 'Période'
    mois_annee_display.admin_order_field = 'annee'
    
    def has_add_permission(self, request):
        """Empêcher la création manuelle (calcul automatique)"""
        return False
    
    def get_readonly_fields(self, request, obj=None):
        """Tous les champs en lecture seule (calcul automatique)"""
        return [f.name for f in self.model._meta.fields]


@admin.register(ExcelImportLog)
class ExcelImportLogAdmin(admin.ModelAdmin):
    list_display = [
        'filename', 'imported_at', 'success_icon', 
        'nb_records_created', 'nb_records_updated', 'nb_records_skipped'
    ]
    list_filter = ['success', 'imported_at']
    search_fields = ['filename']
    ordering = ['-imported_at']
    readonly_fields = [
        'filename', 'imported_at', 'nb_records_created', 
        'nb_records_updated', 'nb_records_skipped', 'errors', 'success'
    ]
    
    def success_icon(self, obj):
        if obj.success:
            return format_html('<span style="color: green;">✓ Réussi</span>')
        else:
            return format_html('<span style="color: red;">✗ Échec</span>')
    success_icon.short_description = 'Statut'
    success_icon.admin_order_field = 'success'
    
    def has_add_permission(self, request):
        """Empêcher la création manuelle"""
        return False


# Actions personnalisées
def recalculate_monthly_summaries(modeladmin, request, queryset):
    """Action pour recalculer les résumés mensuels"""
    count = 0
    for sale in queryset:
        MonthlySummary.recalculate_for_month(sale.date.year, sale.date.month)
        count += 1
    
    modeladmin.message_user(
        request, 
        f"Résumés mensuels recalculés pour {count} période(s)."
    )

recalculate_monthly_summaries.short_description = "Recalculer les résumés mensuels"

# Ajouter l'action à DailySaleAdmin
DailySaleAdmin.actions = [recalculate_monthly_summaries]