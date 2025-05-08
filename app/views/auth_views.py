from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseBadRequest
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone

from app.models import CustomUser, UserPermission, DocumentVerification
from app.forms import CustomUserCreationForm, CustomUserChangeForm

import logging

logger = logging.getLogger(__name__)

def login_view(request):
    """
    Vista para autenticar usuarios.
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            if user.status == 'ACTIVE':
                login(request, user)
                logger.info(f"Usuario {user.email} inició sesión exitosamente")
                return redirect('dashboard')
            else:
                messages.error(request, 'Tu cuenta está inactiva o pendiente de aprobación.')
        else:
            messages.error(request, 'Credenciales inválidas.')
            
            # Registrar intento fallido de login
            FailedLoginAttempt.objects.create(
                email=email,
                ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
                user_agent=request.META.get('HTTP_USER_AGENT', 'Unknown')
            )
    
    return render(request, 'authentication/signin.html')

def logout_view(request):
    """
    Vista para cerrar sesión.
    """
    logout(request)
    return redirect('login')

@method_decorator(login_required, name='dispatch')
@method_decorator(staff_member_required, name='dispatch')
def user_management(request):
    """
    Vista para gestionar usuarios (solo accesible por super admin).
    """
    if not request.user.is_superuser:
        raise PermissionDenied("No tienes permisos para acceder a esta página.")
    
    users = CustomUser.objects.all()
    form = CustomUserCreationForm()
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.status = 'PENDING_APPROVAL'
            user.save()
            messages.success(request, 'Usuario creado exitosamente.')
            return redirect('user_management')
    
    return render(request, 'authentication/user_management.html', {
        'users': users,
        'form': form
    })

@login_required
@staff_member_required
def approve_user(request, user_id):
    """
    Vista para aprobar un usuario.
    """
    if not request.user.is_superuser:
        raise PermissionDenied("No tienes permisos para aprobar usuarios.")
    
    user = get_object_or_404(CustomUser, id=user_id)
    user.status = 'ACTIVE'
    user.save()
    
    messages.success(request, f'Usuario {user.email} aprobado exitosamente.')
    return redirect('user_management')

@login_required
def profile(request):
    """
    Vista para ver y editar el perfil del usuario.
    """
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado exitosamente.')
            return redirect('profile')
    else:
        form = CustomUserChangeForm(instance=request.user)
    
    return render(request, 'authentication/profile.html', {
        'form': form
    })

@csrf_exempt
@login_required
def change_password(request):
    """
    Vista para cambiar la contraseña del usuario.
    """
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not request.user.check_password(current_password):
            return JsonResponse({'success': False, 'error': 'Contraseña actual incorrecta.'})
            
        if new_password != confirm_password:
            return JsonResponse({'success': False, 'error': 'Las contraseñas no coinciden.'})
            
        request.user.set_password(new_password)
        request.user.save()
        
        logger.info(f"Usuario {request.user.email} cambió su contraseña")
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido.'}, status=405)

def forgot_password(request):
    """
    Vista para recuperar contraseña.
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = CustomUser.objects.get(email=email)
            # Aquí implementar lógica de envío de email con enlace de recuperación
            messages.success(request, 'Se ha enviado un correo con instrucciones para recuperar tu contraseña.')
        except CustomUser.DoesNotExist:
            messages.error(request, 'No existe un usuario con ese email.')
        
        return redirect('signin')
    
    return render(request, 'authentication/forgotPassword.html')

def reset_password(request, token):
    """
    Vista para restablecer contraseña usando token.
    """
    # Aquí implementar la lógica de validación del token
    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password != confirm_password:
            messages.error(request, 'Las contraseñas no coinciden.')
            return redirect('reset_password', token=token)
            
        # Aquí implementar la lógica para encontrar el usuario y cambiar su contraseña
        messages.success(request, 'Contraseña cambiada exitosamente.')
        return redirect('signin')
    
    return render(request, 'authentication/reset_password.html')

@login_required
def document_verification(request):
    """
    Vista para verificar documentos del usuario.
    """
    if request.method == 'POST':
        document_type = request.POST.get('document_type')
        document_number = request.POST.get('document_number')
        document_front = request.FILES.get('document_front')
        document_back = request.FILES.get('document_back')
        selfie = request.FILES.get('selfie')
        
        if not all([document_type, document_number, document_front, selfie]):
            messages.error(request, 'Todos los campos son requeridos.')
            return redirect('document_verification')
            
        verification = DocumentVerification.objects.create(
            user=request.user,
            document_type=document_type,
            document_number=document_number,
            document_front=document_front,
            document_back=document_back,
            selfie=selfie
        )
        
        messages.success(request, 'Documento enviado para verificación.')
        return redirect('profile')
    
    return render(request, 'authentication/document_verification.html')
