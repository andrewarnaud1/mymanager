# dashboard/views.py
from django.shortcuts import render
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from datetime import date

@login_required
def dashboard_view(request):
    """
    Dashboard principal avec aperçu de tous les modules
    """
    today = date.today()
    debut_mois = date(today.year, today.month, 1)
    
    context = {
        'today': today,
        'debut_mois': debut_mois
    }
    
    # === FINANCES ===
    try:
        from finances.models import DailySale, MonthlySummary
        
        # KPIs finances du mois
        ventes_mois = DailySale.objects.filter(date__gte=debut_mois)
        ca_mois = ventes_mois.aggregate(total=Sum('total_journalier'))['total'] or 0
        nb_jours_mois = ventes_mois.filter(total_journalier__gt=0).count()
        
        # Dernières ventes
        dernieres_ventes = DailySale.objects.all().order_by('-date')[:5]
        
        # Résumé mensuel actuel
        try:
            resume_actuel = MonthlySummary.objects.get(
                annee=today.year, 
                mois=today.month
            )
        except MonthlySummary.DoesNotExist:
            resume_actuel = None
        
        context.update({
            'finances_enabled': True,
            'ca_mois': ca_mois,
            'nb_jours_mois': nb_jours_mois,
            'dernieres_ventes': dernieres_ventes,
            'resume_actuel': resume_actuel
        })
    except ImportError:
        context['finances_enabled'] = False
    
    # === RECETTES ===
    try:
        from recipes.models import Recipe, Ingredient
        
        nb_recettes = Recipe.objects.count()
        nb_ingredients = Ingredient.objects.count()
        dernieres_recettes = Recipe.objects.all().order_by('-created_at')[:5]
        
        context.update({
            'recipes_enabled': True,
            'nb_recettes': nb_recettes,
            'nb_ingredients': nb_ingredients,
            'dernieres_recettes': dernieres_recettes
        })
    except ImportError:
        context['recipes_enabled'] = False
    
    # === DEVIS ===
    try:
        from quotes.models import Quote, Customer
        
        nb_devis = Quote.objects.count()
        nb_clients = Customer.objects.count()
        devis_en_cours = Quote.objects.filter(status__in=['draft', 'sent']).count()
        derniers_devis = Quote.objects.all().order_by('-created_at')[:5]
        
        # CA potentiel (devis acceptés du mois)
        devis_acceptes = Quote.objects.filter(
            status='accepted',
            quote_date__gte=debut_mois
        )
        ca_potentiel = sum(devis.total_amount for devis in devis_acceptes)
        
        context.update({
            'quotes_enabled': True,
            'nb_devis': nb_devis,
            'nb_clients': nb_clients,
            'devis_en_cours': devis_en_cours,
            'derniers_devis': derniers_devis,
            'ca_potentiel': ca_potentiel
        })
    except ImportError:
        context['quotes_enabled'] = False
    
    return render(request, 'dashboard/dashboard.html', context)