# finances/urls.py
from django.urls import path
from . import views

app_name = 'finances'

urlpatterns = [
    # Dashboard principal
    path('', views.dashboard_view, name='dashboard'),
    
    # Gestion des ventes journalières
    path('ventes/', views.sales_list_view, name='sales_list'),
    path('ventes/nouvelle/', views.sale_create_view, name='sale_create'),
    path('ventes/<int:pk>/modifier/', views.sale_update_view, name='sale_update'),
    path('ventes/<int:pk>/supprimer/', views.sale_delete_view, name='sale_delete'),
    
    # Import Excel
    path('import-excel/', views.excel_import_view, name='excel_import'),
    
    # Rapports
    path('rapports-mensuels/', views.monthly_reports_view, name='monthly_reports'),
    
    # API pour graphiques
    path('api/sales-data/', views.api_sales_data, name='api_sales_data'),
]