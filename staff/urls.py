# staff/urls.py
from django.urls import path
from . import views

app_name = 'staff'

urlpatterns = [
    # ============ EMPLOYÉS ============
    path('employes/', views.EmployeeListView.as_view(), name='employees_list'),
    path('employes/nouveau/', views.employee_create, name='employee_create'),
    path('employes/<int:pk>/modifier/', views.employee_update, name='employee_update'),
    path('employes/<int:pk>/convertir/', views.employee_convert, name='employee_convert'),
    path('employes/<int:pk>/toggle-status/', views.employee_toggle_status, name='employee_toggle_status'),
    
    # ============ PLANNINGS ============
    path('', views.schedules_list, name='schedules_list'),
    path('plannings/', views.schedules_list, name='schedules_list_alt'),
    path('plannings/nouveau/', views.schedule_create, name='schedule_create'),
    path('plannings/<int:pk>/', views.schedule_detail, name='schedule_detail'),
    path('plannings/<int:pk>/copier/', views.schedule_copy, name='schedule_copy'),
    
    # ============ CRÉNEAUX ============
    path('plannings/<int:schedule_pk>/creneaux/nouveau/', views.shift_create, name='shift_create'),
    path('creneaux/<int:pk>/modifier/', views.shift_update, name='shift_update'),
    path('creneaux/<int:pk>/supprimer/', views.shift_delete, name='shift_delete'),
    path('plannings/<int:schedule_pk>/creneaux/rapide/', views.quick_shifts_create, name='quick_shifts_create'),
    
    # ============ VUES CALENDRIER ============
    path('calendrier/', views.schedule_calendar, name='schedule_calendar'),
    
    # ============ EXPORTS ============
    path('plannings/<int:pk>/export/pdf/', views.export_schedule_pdf, name='export_schedule_pdf'),
    path('plannings/<int:pk>/export/excel/', views.export_schedule_excel, name='export_schedule_excel'),
    path('employes/<int:employee_pk>/plannings/<int:schedule_pk>/export/pdf/', 
         views.export_employee_schedule_pdf, name='export_employee_schedule_pdf'),
    
    # ============ API AJAX ============
    path('api/employes/recherche/', views.api_employee_search, name='api_employee_search'),
    path('api/creneaux/conflits/', views.api_shift_conflicts, name='api_shift_conflicts'),
]