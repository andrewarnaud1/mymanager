# quotes/admin.py
from django.contrib import admin
from .models import Customer, Quote, QuoteItem, CompanySettings

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'email']
    ordering = ['-created_at']

class QuoteItemInline(admin.TabularInline):
    model = QuoteItem
    extra = 1
    min_num = 1

@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ['quote_number', 'customer', 'status', 'total_amount', 'quote_date', 'created_at']
    list_filter = ['status', 'quote_date', 'created_at']
    search_fields = ['quote_number', 'customer__name', 'title']
    ordering = ['-created_at']
    inlines = [QuoteItemInline]
    
    def total_amount(self, obj):
        return f"{obj.total_amount}€"
    total_amount.short_description = "Montant total"

@admin.register(CompanySettings)
class CompanySettingsAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone']
    
    def has_add_permission(self, request):
        # Ne permettre qu'un seul paramétrage d'entreprise
        return not CompanySettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Ne pas permettre la suppression
        return False

