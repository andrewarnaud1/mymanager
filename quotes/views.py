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
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    from io import BytesIO
    import os
    
    quote = get_object_or_404(Quote, pk=pk)
    items = quote.quote_items.all().select_related('recipe')
    
    # Paramètres par défaut de l'entreprise
    company_settings = {
        'name': 'Les Délices de Pauline',
        'address': '51 Rue des Girondins, 69007 Lyon, France',
        'phone': '+33 6 99 56 91 83',
        'email': 'paulinearnaudcs@gmail.com',
        'siret': 'À compléter',
        'tva_number': 'À compléter',
        'logo_path': os.path.join('static', 'images', 'logo.png')  # chemin relatif au projet
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
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#F0A103'),
        spaceAfter=30,
        alignment=TA_CENTER
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#F0A103'),
        spaceAfter=12
    )

    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#000000'),
        spaceAfter=6
    )
    
    # Contenu du PDF
    content = []

    # Logo (si présent)
    logo_path = company_settings['logo_path']
    if os.path.exists(logo_path):
        img = Image(logo_path, width=3*cm, height=3*cm)
        img.hAlign = 'LEFT'
        content.append(img)
        content.append(Spacer(1, 10))

    # En-tête entreprise modernisé
    company_data = [
        [
            Paragraph(f"<b>{company_settings['name']}</b>", heading_style),
            Paragraph(f"SIRET: {company_settings['siret']}<br/>TVA: {company_settings['tva_number']}", normal_style)
        ],
        [
            Paragraph(company_settings['address'].replace('\n', '<br/>'), normal_style),
            Paragraph(f"Tél: {company_settings['phone']}<br/>{company_settings['email']}", normal_style)
        ]
    ]
    company_table = Table(company_data, colWidths=[9*cm, 8*cm])
    company_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFFFFF')),
        ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#F0A103')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    content.append(company_table)
    content.append(Spacer(1, 18))

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
        [Paragraph(client_info, normal_style),
         Paragraph(quote_info, normal_style)]
    ]
    info_table = Table(info_data, colWidths=[8.5*cm, 8.5*cm])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOX', (0, 0), (0, 0), 1, colors.HexColor('#E2E2E2')),
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#E2E2E2')),
        ('PADDING', (0, 0), (-1, -1), 12),
    ]))
    content.append(info_table)
    content.append(Spacer(1, 18))
    
    # Objet du devis
    content.append(Paragraph(f"<b>Objet:</b> {quote.title}", heading_style))
    if quote.description:
        content.append(Paragraph(quote.description, normal_style))
    content.append(Spacer(1, 16))
    
    # Tableau des prestations
    content.append(Paragraph("Détail des prestations", heading_style))

    # En-têtes du tableau
    data = [[
        Paragraph('<b>Prestation</b>', normal_style),
        Paragraph('<b>Quantité</b>', normal_style),
        Paragraph('<b>Prix unitaire HT</b>', normal_style),
        Paragraph('<b>Total HT</b>', normal_style)
    ]]

    # Lignes des prestations
    for item in items:
        description = f"{item.recipe.name}"
        if item.description:
            description += f"\n{item.description}"
        data.append([
            Paragraph(description, normal_style),
            Paragraph(f"{item.quantity} portions", normal_style),
            Paragraph(f"{item.unit_price:.2f} €", normal_style),
            Paragraph(f"{item.total_price:.2f} €", normal_style)
        ])

    # Ligne sous-total
    data.append(['', '', Paragraph('<b>Sous-total HT:</b>', normal_style), Paragraph(f"{quote.subtotal:.2f} €", normal_style)])

    # Ligne remise si applicable
    if quote.discount_percentage > 0:
        data.append(['', '', Paragraph(f'<b>Remise ({quote.discount_percentage}%):</b>', normal_style), Paragraph(f"-{quote.discount_amount:.2f} €", normal_style)])
        data.append(['', '', Paragraph('<b>Net HT:</b>', normal_style), Paragraph(f"{quote.subtotal_after_discount:.2f} €", normal_style)])

    # Ligne TVA
    data.append(['', '', Paragraph(f'<b>TVA ({quote.tax_rate}%):</b>', normal_style), Paragraph(f"{quote.tax_amount:.2f} €", normal_style)])

    # Ligne total
    data.append(['', '', Paragraph('<b>TOTAL TTC:</b>', normal_style), Paragraph(f"{quote.total_amount:.2f} €", normal_style)])

    # Créer le tableau
    table = Table(data, colWidths=[7*cm, 3*cm, 4*cm, 3*cm])
    table.setStyle(TableStyle([
        # En-tête
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F0A103')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#FFFFFF')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),

        # Bordures
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E2E2E2')),

        # Total
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#F0A103')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#FFFFFF')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))

    content.append(table)
    content.append(Spacer(1, 24))
    
    # Conditions
    content.append(Paragraph("Conditions générales", heading_style))
    conditions_text = f"""
    <b>Modalités de paiement:</b> 30% d'acompte à la commande, solde à la livraison.<br/>
    <b>Validité du devis:</b> Ce devis est valable jusqu'au {quote.valid_until.strftime('%d/%m/%Y')}.<br/>
    <b>Livraison:</b> Les prestations seront livrées à l'adresse indiquée par le client.<br/><br/>
    {quote.terms_conditions if quote.terms_conditions else ''}
    """
    content.append(Paragraph(conditions_text, normal_style))
    content.append(Spacer(1, 18))
    
    # Signature
    signature_data = [
        [
            Paragraph('Bon pour accord<br/>Date et signature du client :', normal_style),
            Paragraph(f'{company_settings["name"]}<br/>Signature et cachet', normal_style)
        ]
    ]
    signature_table = Table(signature_data, colWidths=[8.5*cm, 8.5*cm], rowHeights=[2.2*cm])
    signature_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E2E2E2')),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFFFFF')),
    ]))
    content.append(signature_table)
    
    # Générer le PDF
    doc.build(content)
    
    # Réponse HTTP
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="devis_{quote.quote_number}.pdf"'
    
    return response