from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from ..models import Client, Company, Person
import json
import re

@login_required
@require_http_methods(["POST"])
def update_client_info(request, client_id):
    """Actualizar información del cliente vía AJAX"""
    try:
        client = get_object_or_404(Client, id=client_id)
        
        # Verificar permisos
        if not (request.user.is_staff or request.user == client.company.account_manager):
            return JsonResponse({'success': False, 'message': 'No tiene permisos para editar esta información'})
        
        field = request.POST.get('field')
        value = request.POST.get('value', '').strip()
        
        # Validación básica
        if not field or field not in ['name', 'industry', 'address', 'city', 'phone', 
                                    'primary_contact_name', 'primary_contact_position', 'email',
                                    'tax_name', 'tax_id', 'tax_address', 'tax_regime', 'tax_cfdi', 'tax_email']:
            return JsonResponse({'success': False, 'message': 'Campo inválido'})
        
        # Validación específica por campo
        if field in ['email', 'tax_email'] and value:
            if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', value):
                return JsonResponse({'success': False, 'message': 'Email inválido'})
        
        if field == 'phone' and value:
            if not re.match(r'^[\d\s\-\+\(\)]+$', value):
                return JsonResponse({'success': False, 'message': 'Teléfono inválido'})
        
        if field == 'tax_id' and value:
            if not re.match(r'^[A-Z&Ñ]{3,4}[0-9]{6}[A-Z0-9]{3}$', value):
                return JsonResponse({'success': False, 'message': 'RFC inválido'})
        
        # Actualizar campo
        setattr(client, field, value)
        client.save()
        
        return JsonResponse({
            'success': True, 
            'message': 'Campo actualizado correctamente',
            'value': value
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})

@login_required
@require_http_methods(["POST"])
def update_company_contacts(request, company_id):
    """Actualizar contactos clave de la empresa vía AJAX"""
    try:
        company = get_object_or_404(Company, id=company_id)
        
        # Verificar permisos
        if not (request.user.is_staff or request.user == company.account_manager):
            return JsonResponse({'success': False, 'message': 'No tiene permisos para editar esta información'})
        
        field = request.POST.get('field')
        value = request.POST.get('value', '').strip()
        
        # Validación de campos
        contact_fields = ['signer', 'payment_responsible', 'fiscal_responsible', 'process_responsible']
        
        if field in contact_fields:
            if value:
                person = get_object_or_404(Person, id=value)
                setattr(company, field, person)
            else:
                setattr(company, field, None)
        elif field == 'notification_preferences':
            setattr(company, field, value)
        else:
            return JsonResponse({'success': False, 'message': 'Campo inválido'})
        
        company.save()
        
        return JsonResponse({
            'success': True, 
            'message': 'Contacto actualizado correctamente',
            'value': value
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})

@login_required
@require_http_methods(["POST"])
def add_invitee(request, company_id):
    """Añadir invitado a reportes vía AJAX"""
    try:
        company = get_object_or_404(Company, id=company_id)
        
        # Verificar permisos
        if not (request.user.is_staff or request.user == company.account_manager):
            return JsonResponse({'success': False, 'message': 'No tiene permisos para editar esta información'})
        
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        
        # Validación
        if not name or not email:
            return JsonResponse({'success': False, 'message': 'Nombre y email son requeridos'})
        
        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            return JsonResponse({'success': False, 'message': 'Email inválido'})
        
        # Crear o obtener persona
        person, created = Person.objects.get_or_create(
            company_email=email,
            defaults={'nombre': name, 'company': company}
        )
        
        if not created:
            person.nombre = name
            person.save()
        
        # Añadir a invitados
        company.report_invitees.add(person)
        
        return JsonResponse({
            'success': True, 
            'message': 'Invitado añadido correctamente',
            'person': {
                'id': person.id,
                'nombre': person.nombre,
                'company_email': person.company_email
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})

@login_required
@require_http_methods(["POST"])
def remove_invitee(request, company_id):
    """Eliminar invitado de reportes vía AJAX"""
    try:
        company = get_object_or_404(Company, id=company_id)
        
        # Verificar permisos
        if not (request.user.is_staff or request.user == company.account_manager):
            return JsonResponse({'success': False, 'message': 'No tiene permisos para editar esta información'})
        
        person_id = request.POST.get('person_id')
        if not person_id:
            return JsonResponse({'success': False, 'message': 'ID de persona requerido'})
        
        person = get_object_or_404(Person, id=person_id)
        company.report_invitees.remove(person)
        
        return JsonResponse({
            'success': True, 
            'message': 'Invitado eliminado correctamente'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'}) 