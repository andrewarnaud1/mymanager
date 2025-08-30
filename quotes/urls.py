# quotes/urls.py
from django.urls import path
from . import views

app_name = 'quotes'

urlpatterns = [
    # Devis
    path('', views.quotes_list, name='list'),
    path('nouveau/', views.quote_create, name='create'),
    path('<int:pk>/', views.quote_detail, name='detail'),
    path('<int:pk>/modifier/', views.quote_update, name='update'),
    path('<int:pk>/dupliquer/', views.quote_duplicate, name='duplicate'),
    path('<int:pk>/statut/', views.quote_change_status, name='change_status'),
    path('<int:pk>/pdf/', views.quote_pdf, name='pdf'),
    
    # Clients
    path('clients/', views.customers_list, name='customers'),
    path('clients/nouveau/', views.customer_create, name='customer_create'),
    path('clients/<int:pk>/', views.customer_detail, name='customer_detail'),
    path('clients/<int:pk>/modifier/', views.customer_update, name='customer_update'),
]