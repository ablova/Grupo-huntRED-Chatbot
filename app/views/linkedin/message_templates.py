from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from app.models import LinkedInMessageTemplate
from app.forms import LinkedInMessageTemplateForm

@login_required
def template_list(request):
    """Lista todos los templates de mensajes de LinkedIn."""
    templates = LinkedInMessageTemplate.objects.all().order_by('-created_at')
    return render(request, 'linkedin/template_list.html', {
        'templates': templates
    })

@login_required
def template_create(request):
    """Crea un nuevo template de mensaje."""
    if request.method == 'POST':
        form = LinkedInMessageTemplateForm(request.POST)
        if form.is_valid():
            template = form.save(commit=False)
            template.created_by = request.user
            template.save()
            messages.success(request, 'Template creado exitosamente')
            return redirect('linkedin:template_list')
    else:
        form = LinkedInMessageTemplateForm()
        
    return render(request, 'linkedin/template_form.html', {
        'form': form,
        'action': 'Crear'
    })

@login_required
def template_edit(request, pk):
    """Edita un template existente."""
    template = get_object_or_404(LinkedInMessageTemplate, pk=pk)
    
    if request.method == 'POST':
        form = LinkedInMessageTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, 'Template actualizado exitosamente')
            return redirect('linkedin:template_list')
    else:
        form = LinkedInMessageTemplateForm(instance=template)
        
    return render(request, 'linkedin/template_form.html', {
        'form': form,
        'action': 'Editar'
    })

@login_required
def template_toggle(request, pk):
    """Activa/desactiva un template."""
    template = get_object_or_404(LinkedInMessageTemplate, pk=pk)
    
    # Desactivar todos los templates
    LinkedInMessageTemplate.objects.all().update(is_active=False)
    
    # Activar/desactivar el template seleccionado
    template.is_active = not template.is_active
    template.save()
    
    status = "activado" if template.is_active else "desactivado"
    messages.success(request, f'Template {status} exitosamente')
    
    return redirect('linkedin:template_list')

@login_required
def template_delete(request, pk):
    """Elimina un template."""
    template = get_object_or_404(LinkedInMessageTemplate, pk=pk)
    
    if request.method == 'POST':
        template.delete()
        messages.success(request, 'Template eliminado exitosamente')
        return redirect('linkedin:template_list')
        
    return render(request, 'linkedin/template_confirm_delete.html', {
        'template': template
    }) 