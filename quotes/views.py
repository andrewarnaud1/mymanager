# quotes/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from accounts.decorators import manager_required
from .models import Customer, Quote, QuoteItem
from .forms import CustomerForm, QuoteForm, QuoteItemFormSet

# ===== VUES CLIENTS =====
@manager_required
def customers_list(request):
    """Liste tous les clients"""
    customers = Customer.objects.all().order_by('name')
    return render(request, 'quotes/customers_list.html', {
        'customers': customers
    })

@manager_required
def customer_create(request):
    """Créer un nouveau client"""
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f'Client "{customer.name}" créé avec succès!')
            return redirect('quotes:customers')
    else:
        form = CustomerForm()
    
    return render(request, 'quotes/customer_form.html', {
        'form': form,
        'title': 'Ajouter un client'
    })

@manager_required
def customer_update(request, pk):
    """Modifier un client"""
    customer = get_object_or_404(Customer, pk=pk)
    
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f'Client "{customer.name}" modifié avec succès!')
            return redirect('quotes:customers')
    else:
        form = CustomerForm(instance=customer)
    
    return render(request, 'quotes/customer_form.html', {
        'form': form,
        'title': f'Modifier {customer.name}',
        'customer': customer
    })

@manager_required
def customer_detail(request, pk):
    """Détail d'un client avec ses devis"""
    customer = get_object_or_404(Customer, pk=pk)
    quotes = Quote.objects.filter(customer=customer).order_by('-created_at')
    
    return render(request, 'quotes/customer_detail.html', {
        'customer': customer,
        'quotes': quotes
    })

# ===== VUES DEVIS =====
@manager_required
def quotes_list(request):
    """Liste tous les devis"""
    from datetime import date
    quotes = Quote.objects.all().select_related('customer').order_by('-created_at')
    
    # Filtres optionnels
    status_filter = request.GET.get('status')
    if status_filter:
        quotes = quotes.filter(status=status_filter)
    
    return render(request, 'quotes/quotes_list.html', {
        'quotes': quotes,
        'current_filter': status_filter,
        'today': date.today()
    })

@manager_required
def quote_create(request):
    """Créer un nouveau devis"""
    if request.method == 'POST':
        form = QuoteForm(request.POST)
        formset = QuoteItemFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            quote = form.save(commit=False)
            if request.user.is_authenticated:
                quote.created_by = request.user
            quote.save()
            
            formset.instance = quote
            formset.save()
            
            messages.success(request, f'Devis {quote.quote_number} créé avec succès!')
            return redirect('quotes:detail', pk=quote.pk)
    else:
        form = QuoteForm()
        formset = QuoteItemFormSet(queryset=QuoteItem.objects.none())
        
        # Pré-sélectionner le client si passé en paramètre
        customer_id = request.GET.get('customer')
        if customer_id:
            try:
                customer = Customer.objects.get(pk=customer_id)
                form.fields['customer'].initial = customer
            except Customer.DoesNotExist:
                pass
    
    return render(request, 'quotes/quote_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Créer un devis'
    })

@manager_required
def quote_detail(request, pk):
    """Détail d'un devis avec calculs"""
    quote = get_object_or_404(Quote, pk=pk)
    items = quote.quote_items.all().select_related('recipe')
    
    return render(request, 'quotes/quote_detail.html', {
        'quote': quote,
        'items': items
    })

@manager_required
def quote_update(request, pk):
    """Modifier un devis"""
    quote = get_object_or_404(Quote, pk=pk)
    
    if request.method == 'POST':
        form = QuoteForm(request.POST, instance=quote)
        formset = QuoteItemFormSet(request.POST, instance=quote)
        
        if form.is_valid() and formset.is_valid():
            quote = form.save()
            formset.save()
            messages.success(request, f'Devis {quote.quote_number} modifié avec succès!')
            return redirect('quotes:detail', pk=quote.pk)
    else:
        form = QuoteForm(instance=quote)
        formset = QuoteItemFormSet(instance=quote)
    
    return render(request, 'quotes/quote_form.html', {
        'form': form,
        'formset': formset,
        'title': f'Modifier {quote.quote_number}',
        'quote': quote
    })

@manager_required
def quote_duplicate(request, pk):
    """Dupliquer un devis"""
    original_quote = get_object_or_404(Quote, pk=pk)
    
    # Créer une copie du devis
    new_quote = Quote.objects.get(pk=pk)
    new_quote.pk = None  # Créer un nouveau objet
    new_quote.quote_number = ""  # Le numéro sera généré automatiquement
    new_quote.status = 'draft'
    new_quote.save()
    
    # Copier les items
    for item in original_quote.quote_items.all():
        QuoteItem.objects.create(
            quote=new_quote,
            recipe=item.recipe,
            quantity=item.quantity,
            unit_price=item.unit_price,
            description=item.description
        )
    
    messages.success(request, f'Devis dupliqué avec le numéro {new_quote.quote_number}')
    return redirect('quotes:detail', pk=new_quote.pk)

@manager_required
def quote_change_status(request, pk):
    """Changer le statut d'un devis"""
    quote = get_object_or_404(Quote, pk=pk)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Quote.STATUS_CHOICES):
            quote.status = new_status
            quote.save()
            messages.success(request, f'Statut du devis {quote.quote_number} mis à jour!')
    
    return redirect('quotes:detail', pk=quote.pk)

@manager_required
def quote_pdf(request, pk):
    """Générer le PDF du devis avec ReportLab"""
    from django.http import HttpResponse
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    from io import BytesIO
    
    quote = get_object_or_404(Quote, pk=pk)
    items = quote.quote_items.all().select_related('recipe')
    
    # Paramètres par défaut de l'entreprise
    company_settings = {
        'name': 'Restaurant Manager',
        'address': '123 Rue de la Gastronomie\n75001 Paris, France',
        'phone': '01 23 45 67 89',
        'email': 'contact@restaurant-manager.fr',
        'siret': '123 456 789 00012',
        'tva_number': 'FR12345678901'
    }
    
    # Créer le buffer PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm, 
                          topMargin=2*cm, bottomMargin=2*cm)
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#007bff'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#007bff'),
        spaceAfter=12
    )
    
    # Contenu du PDF
    content = []
    
    # En-tête entreprise
    company_data = [
        [Paragraph(f"<b>{company_settings['name']}</b>", styles['Heading2']), 
         Paragraph(f"SIRET: {company_settings['siret']}<br/>TVA: {company_settings['tva_number']}", styles['Normal'])]
    ]
    company_table = Table(company_data, colWidths=[10*cm, 7*cm])
    company_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#007bff')),
    ]))
    content.append(company_table)
    content.append(Spacer(1, 20))
    
    # Titre du devis
    content.append(Paragraph(f"DEVIS N° {quote.quote_number}", title_style))
    
    # Informations client et devis
    client_info = f"""
    <b>Client:</b><br/>
    {quote.customer.name}<br/>
    {quote.customer.company or ''}<br/>
    {quote.customer.address or ''}<br/>
    {quote.customer.postal_code or ''} {quote.customer.city or ''}<br/>
    {quote.customer.email or ''}<br/>
    {quote.customer.phone or ''}
    """
    
    quote_info = f"""
    <b>Détails du devis:</b><br/>
    Date: {quote.quote_date.strftime('%d/%m/%Y')}<br/>
    Valable jusqu'au: {quote.valid_until.strftime('%d/%m/%Y')}<br/>
    {f"Événement: {quote.event_date.strftime('%d/%m/%Y')}" if quote.event_date else ""}
    """
    
    info_data = [
        [Paragraph(client_info, styles['Normal']), 
         Paragraph(quote_info, styles['Normal'])]
    ]
    info_table = Table(info_data, colWidths=[8.5*cm, 8.5*cm])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOX', (0, 0), (0, 0), 1, colors.grey),
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#f9f9f9')),
        ('PADDING', (0, 0), (-1, -1), 12),
    ]))
    content.append(info_table)
    content.append(Spacer(1, 20))
    
    # Objet du devis
    content.append(Paragraph(f"<b>Objet:</b> {quote.title}", heading_style))
    if quote.description:
        content.append(Paragraph(quote.description, styles['Normal']))
    content.append(Spacer(1, 20))
    
    # Tableau des prestations
    content.append(Paragraph("Détail des prestations", heading_style))
    
    # En-têtes du tableau
    data = [['Prestation', 'Quantité', 'Prix unitaire HT', 'Total HT']]
    
    # Lignes des prestations
    for item in items:
        description = f"{item.recipe.name}"
        if item.description:
            description += f"\n{item.description}"
        
        data.append([
            description,
            f"{item.quantity} portions",
            f"{item.unit_price:.2f} €",
            f"{item.total_price:.2f} €"
        ])
    
    # Ligne sous-total
    data.append(['', '', 'Sous-total HT:', f"{quote.subtotal:.2f} €"])
    
    # Ligne remise si applicable
    if quote.discount_percentage > 0:
        data.append(['', '', f'Remise ({quote.discount_percentage}%):', f"-{quote.discount_amount:.2f} €"])
        data.append(['', '', 'Net HT:', f"{quote.subtotal_after_discount:.2f} €"])
    
    # Ligne TVA
    data.append(['', '', f'TVA ({quote.tax_rate}%):', f"{quote.tax_amount:.2f} €"])
    
    # Ligne total
    data.append(['', '', 'TOTAL TTC:', f"{quote.total_amount:.2f} €"])
    
    # Créer le tableau
    table = Table(data, colWidths=[7*cm, 3*cm, 4*cm, 3*cm])
    table.setStyle(TableStyle([
        # En-tête
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#007bff')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        
        # Bordures
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        
        # Total
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#28a745')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    
    content.append(table)
    content.append(Spacer(1, 30))
    
    # Conditions
    content.append(Paragraph("Conditions générales", heading_style))
    conditions_text = f"""
    <b>Modalités de paiement:</b> 30% d'acompte à la commande, solde à la livraison.<br/>
    <b>Validité du devis:</b> Ce devis est valable jusqu'au {quote.valid_until.strftime('%d/%m/%Y')}.<br/>
    <b>Livraison:</b> Les prestations seront livrées à l'adresse indiquée par le client.<br/><br/>
    
    {quote.terms_conditions if quote.terms_conditions else ''}
    """
    content.append(Paragraph(conditions_text, styles['Normal']))
    content.append(Spacer(1, 30))
    
    # Signature
    signature_data = [
        ['Bon pour accord\nDate et signature du client:', f'{company_settings["name"]}\nSignature et cachet']
    ]
    signature_table = Table(signature_data, colWidths=[8.5*cm, 8.5*cm], rowHeights=[3*cm])
    signature_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
    ]))
    content.append(signature_table)
    
    # Générer le PDF
    doc.build(content)
    
    # Réponse HTTP
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="devis_{quote.quote_number}.pdf"'
    
    return response