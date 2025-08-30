# staff/admin.py
from django.contrib import admin
from .models import Employee, WeeklySchedule, Shift


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'phone', 'is_external', 'is_active', 'created_at']
    list_filter = ['is_external', 'is_active', 'created_at']
    search_fields = ['first_name', 'last_name', 'phone', 'user__username']
    ordering = ['last_name', 'first_name']
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('first_name', 'last_name', 'phone', 'hire_date')
        }),
        ('Statut', {
            'fields': ('is_external', 'is_active')
        }),
        ('Compte utilisateur', {
            'fields': ('user',),
            'description': 'Laisser vide pour un employé externe'
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        # Les employés externes ne peuvent pas avoir de compte User
        if obj and obj.is_external:
            return ['user'] + list(self.readonly_fields or [])
        return self.readonly_fields or []


@admin.register(WeeklySchedule)
class WeeklyScheduleAdmin(admin.ModelAdmin):
    list_display = ['week_range_display', 'employees_count', 'total_hours', 'created_by', 'created_at']
    list_filter = ['created_at', 'created_by']
    search_fields = ['week_start', 'notes']
    ordering = ['-week_start']
    
    fieldsets = (
        ('Période', {
            'fields': ('week_start',)
        }),
        ('Informations', {
            'fields': ('notes',)
        }),
        ('Métadonnées', {
            'fields': ('created_by',),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing object
            return ['created_by'] + list(self.readonly_fields or [])
        return self.readonly_fields or []
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'day_name', 'start_time', 'end_time', 'duration_display', 'notes']
    list_filter = ['date', 'employee', 'schedule']
    search_fields = ['employee__first_name', 'employee__last_name', 'notes']
    ordering = ['-date', 'start_time']
    
    fieldsets = (
        ('Planning', {
            'fields': ('schedule', 'employee')
        }),
        ('Horaires', {
            'fields': ('date', 'start_time', 'end_time')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('employee', 'schedule')


# Configuration globale de l'admin
admin.site.site_header = "Administration Restaurant Manager"
admin.site.site_title = "Restaurant Manager Admin"
admin.site.index_title = "Gestion du Personnel"