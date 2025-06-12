from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from app.models import LinkedInInvitationSchedule
from app.forms import LinkedInInvitationScheduleForm

@login_required
def schedule_list(request):
    """Lista todas las programaciones de invitaciones."""
    schedules = LinkedInInvitationSchedule.objects.all().order_by('time_window_start')
    return render(request, 'linkedin/schedule_list.html', {
        'schedules': schedules
    })

@login_required
def schedule_create(request):
    """Crea una nueva programación."""
    if request.method == 'POST':
        form = LinkedInInvitationScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save()
            messages.success(request, 'Programación creada exitosamente')
            return redirect('linkedin:schedule_list')
    else:
        form = LinkedInInvitationScheduleForm()
        
    return render(request, 'linkedin/schedule_form.html', {
        'form': form,
        'action': 'Crear'
    })

@login_required
def schedule_edit(request, pk):
    """Edita una programación existente."""
    schedule = get_object_or_404(LinkedInInvitationSchedule, pk=pk)
    
    if request.method == 'POST':
        form = LinkedInInvitationScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            messages.success(request, 'Programación actualizada exitosamente')
            return redirect('linkedin:schedule_list')
    else:
        form = LinkedInInvitationScheduleForm(instance=schedule)
        
    return render(request, 'linkedin/schedule_form.html', {
        'form': form,
        'action': 'Editar'
    })

@login_required
def schedule_toggle(request, pk):
    """Activa/desactiva una programación."""
    schedule = get_object_or_404(LinkedInInvitationSchedule, pk=pk)
    schedule.is_active = not schedule.is_active
    schedule.save()
    
    status = "activada" if schedule.is_active else "desactivada"
    messages.success(request, f'Programación {status} exitosamente')
    
    return redirect('linkedin:schedule_list')

@login_required
def schedule_delete(request, pk):
    """Elimina una programación."""
    schedule = get_object_or_404(LinkedInInvitationSchedule, pk=pk)
    
    if request.method == 'POST':
        schedule.delete()
        messages.success(request, 'Programación eliminada exitosamente')
        return redirect('linkedin:schedule_list')
        
    return render(request, 'linkedin/schedule_confirm_delete.html', {
        'schedule': schedule
    }) 