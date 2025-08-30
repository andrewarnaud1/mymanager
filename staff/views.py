# staff/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from datetime import date, timedelta, datetime
import json

from accounts.decorators import manager_required, employee_required
from .models import Employee, WeeklySchedule, Shift
from .forms import (
    EmployeeForm, EmployeeInternalForm, ConvertEmployeeForm,
    WeeklyScheduleForm, ShiftForm, QuickShiftForm, WeekNavigationForm
)
from .utils import generate_schedule_pdf, generate_schedule_excel


# ============ VUES EMPLOYÉS ============

@method_decorator(manager_required, name='dispatch')
class EmployeeListView(ListView):
    """Liste des employés"""
    model = Employee
    template_name = 'staff/employees_list.html'
    context_object_name = 'employees'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Employee.objects.select_related('user').annotate(
            shifts_count=Count('shift')
        )
        
        # Filtres
        search = self.request.GET.get('search')
        status = self.request.GET.get('status')
        
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(phone__icontains=search) |
                Q(user__username__icontains=search)
            )
        
        if status == 'internal':
            queryset = queryset.filter(is_external=False)
        elif status == 'external':
            queryset = queryset.filter(is_external=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        return queryset.order_by('last_name', 'first_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['status'] = self.request.GET.get('status', '')
        context['total_employees'] = Employee.objects.count()
        context['internal_count'] = Employee.objects.filter(is_external=False).count()
        context['external_count'] = Employee.objects.filter(is_external=True).count()
        context['inactive_count'] = Employee.objects.filter(is_active=False).count()
        return context


@manager_required
def employee_create(request):
    """Créer un nouvel employé"""
    if request.method == 'POST':
        employee_type = request.POST.get('employee_type', 'external')
        
        if employee_type == 'internal':
            form = EmployeeInternalForm(request.POST)
            if form.is_valid():
                employee = form.save()
                messages.success(request, f'Employé interne {employee.full_name} créé avec succès.')
                return redirect('staff:employees_list')
        else:
            form = EmployeeForm(request.POST)
            if form.is_valid():
                employee = form.save(commit=False)
                employee.is_external = True
                employee.save()
                messages.success(request, f'Employé externe {employee.full_name} créé avec succès.')
                return redirect('staff:employees_list')
    else:
        employee_type = request.GET.get('type', 'external')
        if employee_type == 'internal':
            form = EmployeeInternalForm()
        else:
            form = EmployeeForm()
    
    return render(request, 'staff/employee_form.html', {
        'form': form,
        'title': 'Nouvel employé',
        'employee_type': employee_type
    })


@manager_required
def employee_update(request, pk):
    """Modifier un employé"""
    employee = get_object_or_404(Employee, pk=pk)
    
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, f'Employé {employee.full_name} modifié avec succès.')
            return redirect('staff:employees_list')
    else:
        form = EmployeeForm(instance=employee)
    
    return render(request, 'staff/employee_form.html', {
        'form': form,
        'employee': employee,
        'title': f'Modifier {employee.full_name}'
    })


@manager_required
def employee_convert(request, pk):
    """Convertir un employé externe en interne"""
    employee = get_object_or_404(Employee, pk=pk, is_external=True)
    
    if request.method == 'POST':
        form = ConvertEmployeeForm(employee, request.POST)
        if form.is_valid():
            try:
                user = form.convert()
                messages.success(
                    request, 
                    f'{employee.full_name} est maintenant un employé interne. '
                    f'Nom d\'utilisateur: {user.username}'
                )
                return redirect('staff:employees_list')
            except Exception as e:
                messages.error(request, f'Erreur lors de la conversion: {str(e)}')
    else:
        form = ConvertEmployeeForm(employee)
    
    return render(request, 'staff/employee_convert.html', {
        'form': form,
        'employee': employee,
        'title': f'Convertir {employee.full_name} en employé interne'
    })


@require_POST
@manager_required
def employee_toggle_status(request, pk):
    """Activer/désactiver un employé (AJAX)"""
    employee = get_object_or_404(Employee, pk=pk)
    employee.is_active = not employee.is_active
    employee.save()
    
    status = 'activé' if employee.is_active else 'désactivé'
    return JsonResponse({
        'success': True,
        'message': f'{employee.full_name} {status} avec succès.',
        'is_active': employee.is_active
    })


# ============ VUES PLANNINGS ============

@employee_required
def schedules_list(request):
    """Liste des plannings (accessible aux employés)"""
    # Calculer la semaine actuelle
    today = date.today()
    current_week_start = today - timedelta(days=today.weekday())
    current_week_end = current_week_start + timedelta(days=6)  # Ajout de cette ligne
    
    # Récupérer les plannings
    schedules = WeeklySchedule.objects.select_related('created_by').prefetch_related(
        'shifts__employee'
    ).order_by('-week_start')
    
    # Filtres
    search = request.GET.get('search')
    if search:
        schedules = schedules.filter(
            Q(notes__icontains=search) |
            Q(shifts__employee__first_name__icontains=search) |
            Q(shifts__employee__last_name__icontains=search)
        ).distinct()
    
    # Pagination
    paginator = Paginator(schedules, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'staff/schedules_list.html', {
        'page_obj': page_obj,
        'search': search,
        'current_week_start': current_week_start,
        'current_week_end': current_week_end  # Ajout de cette ligne
    })


@manager_required
def schedule_create(request):
    """Créer un nouveau planning"""
    # Par défaut, créer pour la semaine prochaine
    today = date.today()
    next_week_start = today - timedelta(days=today.weekday()) + timedelta(days=7)
    
    if request.method == 'POST':
        form = WeeklyScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.created_by = request.user
            schedule.save()
            messages.success(request, f'Planning {schedule} créé avec succès.')
            return redirect('staff:schedule_detail', pk=schedule.pk)
    else:
        form = WeeklyScheduleForm(initial={'week_start': next_week_start})
    
    return render(request, 'staff/schedule_form.html', {
        'form': form,
        'title': 'Nouveau planning'
    })


@employee_required
def schedule_detail(request, pk):
    """Détail d'un planning"""
    schedule = get_object_or_404(WeeklySchedule, pk=pk)
    
    # Organiser les créneaux par jour et employé
    shifts = schedule.shifts.select_related('employee').order_by('date', 'start_time')
    
    # Créer structure de données pour l'affichage calendrier
    days = []
    for i in range(7):
        current_date = schedule.week_start + timedelta(days=i)
        day_name = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'][i]
        day_shifts = shifts.filter(date=current_date)
        
        days.append({
            'date': current_date,
            'name': day_name,
            'shifts': day_shifts
        })
    
    # Statistiques
    total_hours = sum(shift.duration_hours for shift in shifts)
    employees_count = shifts.values('employee').distinct().count()
    
    # Navigation
    prev_week = schedule.week_start - timedelta(days=7)
    next_week = schedule.week_start + timedelta(days=7)
    
    try:
        prev_schedule = WeeklySchedule.objects.get(week_start=prev_week)
    except WeeklySchedule.DoesNotExist:
        prev_schedule = None
    
    try:
        next_schedule = WeeklySchedule.objects.get(week_start=next_week)
    except WeeklySchedule.DoesNotExist:
        next_schedule = None
    
    # Permissions
    can_edit = (request.user.is_superuser or 
                request.user.groups.filter(name='Managers').exists())
    
    return render(request, 'staff/schedule_detail.html', {
        'schedule': schedule,
        'days': days,
        'shifts': shifts,
        'total_hours': total_hours,
        'employees_count': employees_count,
        'prev_schedule': prev_schedule,
        'next_schedule': next_schedule,
        'can_edit': can_edit
    })


@manager_required
def schedule_copy(request, pk):
    """Copier un planning existant"""
    source_schedule = get_object_or_404(WeeklySchedule, pk=pk)
    
    if request.method == 'POST':
        form = WeeklyScheduleForm(request.POST)
        if form.is_valid():
            # Créer le nouveau planning
            new_schedule = form.save(commit=False)
            new_schedule.created_by = request.user
            new_schedule.save()
            
            # Copier tous les créneaux
            shifts_copied = 0
            for shift in source_schedule.shifts.all():
                # Calculer la nouvelle date
                days_diff = (shift.date - source_schedule.week_start).days
                new_date = new_schedule.week_start + timedelta(days=days_diff)
                
                Shift.objects.create(
                    schedule=new_schedule,
                    employee=shift.employee,
                    date=new_date,
                    start_time=shift.start_time,
                    end_time=shift.end_time,
                    notes=shift.notes
                )
                shifts_copied += 1
            
            messages.success(
                request, 
                f'Planning copié avec succès. {shifts_copied} créneaux créés.'
            )
            return redirect('staff:schedule_detail', pk=new_schedule.pk)
    else:
        # Suggérer la semaine suivante
        next_week = source_schedule.week_start + timedelta(days=7)
        form = WeeklyScheduleForm(initial={
            'week_start': next_week,
            'notes': f'Copie du planning {source_schedule}'
        })
    
    return render(request, 'staff/schedule_form.html', {
        'form': form,
        'title': f'Copier le planning {source_schedule}',
        'source_schedule': source_schedule
    })


# ============ VUES CRÉNEAUX ============

@manager_required
def shift_create(request, schedule_pk):
    """Créer un nouveau créneau"""
    schedule = get_object_or_404(WeeklySchedule, pk=schedule_pk)
    
    if request.method == 'POST':
        form = ShiftForm(schedule, request.POST)
        if form.is_valid():
            shift = form.save()
            messages.success(request, f'Créneau {shift} ajouté avec succès.')
            return redirect('staff:schedule_detail', pk=schedule.pk)
    else:
        # Valeurs par défaut
        initial_data = {}
        date_param = request.GET.get('date')
        if date_param:
            try:
                initial_data['date'] = datetime.strptime(date_param, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        form = ShiftForm(schedule, initial=initial_data)
    
    return render(request, 'staff/shift_form.html', {
        'form': form,
        'schedule': schedule,
        'title': 'Nouveau créneau'
    })


@manager_required
def shift_update(request, pk):
    """Modifier un créneau"""
    shift = get_object_or_404(Shift, pk=pk)
    
    if request.method == 'POST':
        form = ShiftForm(shift.schedule, request.POST, instance=shift)
        if form.is_valid():
            form.save()
            messages.success(request, f'Créneau {shift} modifié avec succès.')
            return redirect('staff:schedule_detail', pk=shift.schedule.pk)
    else:
        form = ShiftForm(shift.schedule, instance=shift)
    
    return render(request, 'staff/shift_form.html', {
        'form': form,
        'shift': shift,
        'schedule': shift.schedule,
        'title': f'Modifier le créneau de {shift.employee.full_name}'
    })


@manager_required
def shift_delete(request, pk):
    """Vue de confirmation et suppression d'un créneau (formulaire POST)"""
    shift = get_object_or_404(Shift, pk=pk)
    if request.method == 'POST':
        schedule_pk = shift.schedule.pk
        employee_name = shift.employee.full_name
        shift.delete()
        messages.success(request, f'Créneau de {employee_name} supprimé avec succès.')
        return redirect('staff:schedule_detail', pk=schedule_pk)
    return render(request, 'staff/shift_confirm_delete.html', {'shift': shift})


@manager_required
def quick_shifts_create(request, schedule_pk):
    """Créer plusieurs créneaux rapidement"""
    schedule = get_object_or_404(WeeklySchedule, pk=schedule_pk)
    
    if request.method == 'POST':
        form = QuickShiftForm(schedule, request.POST)
        if form.is_valid():
            shifts_created = form.save()
            count = len(shifts_created)
            messages.success(request, f'{count} créneaux créés avec succès.')
            return redirect('staff:schedule_detail', pk=schedule.pk)
    else:
        form = QuickShiftForm(schedule)
    
    return render(request, 'staff/quick_shifts_form.html', {
        'form': form,
        'schedule': schedule,
        'title': 'Ajout rapide de créneaux'
    })


# ============ NAVIGATION ET UTILITAIRES ============

@employee_required
def schedule_calendar(request):
    """Vue calendrier des plannings"""
    # Récupérer ou calculer la semaine à afficher
    week_param = request.GET.get('week')
    if week_param:
        try:
            week_start = datetime.strptime(week_param, '%Y-%m-%d').date()
            # Ajuster au lundi si nécessaire
            week_start = week_start - timedelta(days=week_start.weekday())
        except ValueError:
            week_start = date.today() - timedelta(days=date.today().weekday())
    else:
        week_start = date.today() - timedelta(days=date.today().weekday())
    
    # Récupérer ou créer le planning
    try:
        schedule = WeeklySchedule.objects.get(week_start=week_start)
    except WeeklySchedule.DoesNotExist:
        schedule = None
    
    # Navigation
    prev_week = week_start - timedelta(days=7)
    next_week = week_start + timedelta(days=7)
    
    # Organiser les données pour le calendrier
    calendar_data = []
    employees = Employee.objects.filter(is_active=True).order_by('last_name', 'first_name')
    
    for i in range(7):
        current_date = week_start + timedelta(days=i)
        day_name = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'][i]
        
        day_data = {
            'date': current_date,
            'name': day_name,
            'employees': []
        }
        
        for employee in employees:
            employee_shifts = []
            if schedule:
                employee_shifts = list(schedule.shifts.filter(
                    employee=employee,
                    date=current_date
                ).order_by('start_time'))
            
            day_data['employees'].append({
                'employee': employee,
                'shifts': employee_shifts
            })
        
        calendar_data.append(day_data)
    
    # Permissions
    can_edit = (request.user.is_superuser or 
                request.user.groups.filter(name='Managers').exists())
    
    return render(request, 'staff/schedule_calendar.html', {
        'calendar_data': calendar_data,
        'schedule': schedule,
        'week_start': week_start,
        'week_end': week_start + timedelta(days=6),
        'prev_week': prev_week,
        'next_week': next_week,
        'employees': employees,
        'can_edit': can_edit
    })


# ============ EXPORTS ============

@manager_required
def export_schedule_pdf(request, pk):
    """Exporter un planning en PDF"""
    schedule = get_object_or_404(WeeklySchedule, pk=pk)
    
    try:
        pdf_response = generate_schedule_pdf(schedule)
        return pdf_response
    except Exception as e:
        messages.error(request, f'Erreur lors de la génération du PDF: {str(e)}')
        return redirect('staff:schedule_detail', pk=pk)


@manager_required
def export_schedule_excel(request, pk):
    """Exporter un planning en Excel"""
    schedule = get_object_or_404(WeeklySchedule, pk=pk)
    
    try:
        excel_response = generate_schedule_excel(schedule)
        return excel_response
    except Exception as e:
        messages.error(request, f'Erreur lors de la génération de l\'Excel: {str(e)}')
        return redirect('staff:schedule_detail', pk=pk)


@manager_required
def export_employee_schedule_pdf(request, employee_pk, schedule_pk):
    """Exporter le planning d'un employé spécifique en PDF"""
    employee = get_object_or_404(Employee, pk=employee_pk)
    schedule = get_object_or_404(WeeklySchedule, pk=schedule_pk)
    
    try:
        pdf_response = generate_schedule_pdf(schedule, employee=employee)
        return pdf_response
    except Exception as e:
        messages.error(request, f'Erreur lors de la génération du PDF: {str(e)}')
        return redirect('staff:schedule_detail', pk=schedule_pk)


# ============ API AJAX ============

@employee_required
def api_employee_search(request):
    """API pour recherche d'employés (autocomplete)"""
    term = request.GET.get('term', '')
    
    employees = Employee.objects.filter(
        Q(first_name__icontains=term) | Q(last_name__icontains=term),
        is_active=True
    )[:10]
    
    results = [{
        'id': emp.id,
        'label': emp.full_name,
        'value': emp.full_name
    } for emp in employees]
    
    return JsonResponse(results, safe=False)


@manager_required
def api_shift_conflicts(request):
    """API pour vérifier les conflits de créneaux"""
    employee_id = request.GET.get('employee_id')
    date_str = request.GET.get('date')
    start_time_str = request.GET.get('start_time')
    end_time_str = request.GET.get('end_time')
    exclude_id = request.GET.get('exclude_id')
    
    try:
        employee = Employee.objects.get(id=employee_id)
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        start_time = datetime.strptime(start_time_str, '%H:%M').time()
        end_time = datetime.strptime(end_time_str, '%H:%M').time()
        
        conflicts = Shift.get_overlapping_shifts(
            employee=employee,
            date_obj=date_obj,
            start_time=start_time,
            end_time=end_time,
            exclude_pk=int(exclude_id) if exclude_id else None
        )
        
        conflicts_data = [{
            'id': shift.id,
            'start_time': shift.start_time.strftime('%H:%M'),
            'end_time': shift.end_time.strftime('%H:%M'),
            'notes': shift.notes
        } for shift in conflicts]
        
        return JsonResponse({
            'has_conflicts': len(conflicts) > 0,
            'conflicts': conflicts_data
        })
        
    except (Employee.DoesNotExist, ValueError) as e:
        return JsonResponse({'error': str(e)}, status=400)