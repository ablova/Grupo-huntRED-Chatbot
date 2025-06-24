# /home/pablo/app/views/dashboard.py
#
# Vista para el módulo. Implementa la lógica de presentación y manejo de peticiones HTTP.

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q, F
from django.utils import timezone
from datetime import timedelta, datetime
from calendar import monthrange
from app.models import (
    Person, Vacante, Application, Interview, CartaOferta,
    ChatState, IntentPattern, StateTransition, ConfiguracionBU,
    BusinessUnit
)
from app.ats.utils.Events import Event, EventType, EventStatus, EventParticipant
from app.ats.services.interview_service import InterviewService
from app.ats.utils.vacantes import requiere_slots_grupales

@login_required
def dashboard(request):
    # Obtener el período de filtrado (por defecto semana)
    period = request.GET.get('period', 'week')
    
    # Función para obtener fechas según el período
    def get_period_dates(period):
        today = timezone.now()
        if period == 'week':
            start_date = today - timedelta(days=7)
            end_date = today
        elif period == 'month':
            _, days_in_month = monthrange(today.year, today.month)
            start_date = today.replace(day=1)
            end_date = today.replace(day=days_in_month)
        elif period == 'year':
            start_date = today.replace(month=1, day=1)
            end_date = today.replace(month=12, day=31)
        return start_date, end_date

    # Obtener fechas para el período seleccionado
    start_date, end_date = get_period_dates(period)

    # Obtener datos de métricas
    metrics = {
        "total_users": Person.objects.count(),
        "active_chats": ChatState.objects.filter(
            last_transition__gte=timezone.now() - timedelta(hours=24)
        ).count(),
        "new_applications": Application.objects.filter(
            applied_at__gte=start_date,
            applied_at__lte=end_date
        ).count(),
        "pending_interviews": Interview.objects.filter(
            resultado='pendiente',
            fecha__gte=timezone.now()
        ).count()
    }

    # Obtener datos para gráficos
    # Preparar datos para el gráfico de aplicaciones
    applications_data = Application.objects.filter(
        applied_at__gte=start_date,
        applied_at__lte=end_date
    ).annotate(
        date=F('applied_at__date')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')

    # Preparar datos para el gráfico de entrevistas
    interviews_data = Interview.objects.filter(
        fecha__gte=start_date,
        fecha__lte=end_date
    ).values('resultado').annotate(
        count=Count('id')
    )

    # Obtener datos de chatbot
    chatbot_data = {
        "states": ChatState.objects.filter(
            last_transition__gte=start_date,
            last_transition__lte=end_date
        )[:5],
        "pending_transitions": StateTransition.objects.filter(
            Q(current_state='PROFILE') | Q(current_state='SEARCH'),
            created_at__gte=start_date,
            created_at__lte=end_date
        )[:5]
    }

    # Obtener datos de propuestas
    proposals_data = {
        "recent": CartaOferta.objects.filter(
            status__in=['pending', 'sent'],
            created_at__gte=start_date,
            created_at__lte=end_date
        ).order_by('-created_at')[:5]
    }

    # Preparar datos para el template
    context = {
        'metrics': metrics,
        'period': period,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'chatbot_data': chatbot_data,
        'proposals_data': proposals_data,
        'applications_data': applications_data,
        'interviews_data': interviews_data
    }

    return render(request, 'dashboard.html', context)

@login_required
def interview_slots_dashboard(request):
    """
    Dashboard para gestionar slots de entrevistas.
    Incluye slots grupales e individuales.
    """
    try:
        # Obtener parámetros de filtro
        business_unit_id = request.GET.get('business_unit')
        vacancy_id = request.GET.get('vacancy')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        session_type = request.GET.get('session_type')
        
        # Obtener unidades de negocio del usuario
        if request.user.is_superuser:
            business_units = BusinessUnit.objects.all()
        else:
            business_units = BusinessUnit.objects.filter(
                consultants__person__user=request.user
            ).distinct()
        
        # Filtrar por unidad de negocio
        if business_unit_id:
            business_unit = get_object_or_404(BusinessUnit, id=business_unit_id)
        else:
            business_unit = business_units.first()
        
        # Construir filtros para eventos
        filters = {
            'event_type': EventType.ENTREVISTA,
        }
        
        if business_unit:
            filters['description__icontains'] = f'business_unit_{business_unit.id}'
        
        if vacancy_id:
            filters['description__icontains'] = f'vacante_{vacancy_id}'
        
        if session_type:
            filters['session_type'] = session_type
        
        # Filtros de fecha
        if date_from:
            filters['start_time__gte'] = datetime.strptime(date_from, '%Y-%m-%d')
        else:
            filters['start_time__gte'] = timezone.now()
        
        if date_to:
            filters['start_time__lte'] = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
        else:
            filters['start_time__lte'] = timezone.now() + timedelta(days=30)
        
        # Obtener eventos
        events = Event.objects.filter(**filters).order_by('start_time')
        
        # Obtener vacantes para filtro
        if business_unit:
            vacancies = Vacante.objects.filter(business_unit=business_unit, activa=True)
        else:
            vacancies = Vacante.objects.filter(activa=True)
        
        # Estadísticas
        stats = {
            'total_slots': events.count(),
            'group_slots': events.filter(session_type='grupal').count(),
            'individual_slots': events.filter(session_type='individual').count(),
            'confirmed_slots': events.filter(status=EventStatus.CONFIRMADO).count(),
            'pending_slots': events.filter(status=EventStatus.PENDIENTE).count(),
            'total_participants': EventParticipant.objects.filter(
                event__in=events
            ).count(),
        }
        
        # Preparar datos para el template
        slots_data = []
        for event in events:
            participants = event.participants.all()
            available_spots = event.lugares_disponibles()
            
            slots_data.append({
                'id': event.id,
                'title': event.title,
                'start_time': event.start_time,
                'end_time': event.end_time,
                'session_type': event.get_session_type_display(),
                'status': event.get_status_display(),
                'mode': event.get_event_mode_display(),
                'location': event.location,
                'virtual_link': event.virtual_link,
                'total_spots': event.cupo_maximo or 1,
                'available_spots': available_spots,
                'participants_count': participants.count(),
                'participants': [
                    {
                        'name': p.person.full_name,
                        'email': p.person.email,
                        'phone': p.person.phone,
                        'status': p.get_status_display()
                    } for p in participants
                ],
                'is_group': event.session_type == 'grupal',
                'is_full': available_spots == 0,
                'is_upcoming': event.is_upcoming(),
                'is_overdue': event.is_overdue()
            })
        
        context = {
            'business_units': business_units,
            'selected_business_unit': business_unit,
            'vacancies': vacancies,
            'selected_vacancy_id': vacancy_id,
            'session_types': [
                ('', 'Todos'),
                ('individual', 'Individual'),
                ('grupal', 'Grupal')
            ],
            'selected_session_type': session_type,
            'date_from': date_from,
            'date_to': date_to,
            'slots': slots_data,
            'stats': stats,
            'page_title': 'Gestión de Slots de Entrevista',
            'active_tab': 'interview_slots'
        }
        
        return render(request, 'dashboard/interview_slots.html', context)
        
    except Exception as e:
        messages.error(request, f"Error cargando el dashboard: {str(e)}")
        return redirect('dashboard')

@login_required
def generate_slots(request):
    """
    Genera slots de entrevista automáticamente.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            vacancy_id = data.get('vacancy_id')
            start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d')
            end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%d')
            slot_duration = int(data.get('slot_duration', 45))
            max_slots_per_day = int(data.get('max_slots_per_day', 8))
            
            # Obtener vacante
            vacancy = get_object_or_404(Vacante, id=vacancy_id)
            
            # Verificar permisos
            if not request.user.is_superuser:
                if not vacancy.business_unit.consultants.filter(person__user=request.user).exists():
                    return JsonResponse({
                        'success': False,
                        'error': 'No tienes permisos para esta vacante'
                    }, status=403)
            
            # Crear servicio y generar slots
            interview_service = InterviewService(vacancy.business_unit)
            
            # Usar sync_to_async para llamar al método async
            from asgiref.sync import sync_to_async
            import asyncio
            
            # Crear un nuevo event loop para la operación async
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                created_slots = loop.run_until_complete(
                    interview_service.generate_interview_slots(
                        vacancy=vacancy,
                        start_date=start_date,
                        end_date=end_date,
                        slot_duration=slot_duration,
                        max_slots_per_day=max_slots_per_day
                    )
                )
                
                return JsonResponse({
                    'success': True,
                    'message': f'Se generaron {len(created_slots)} slots exitosamente',
                    'slots_count': len(created_slots)
                })
                
            finally:
                loop.close()
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

@login_required
def slot_details(request, slot_id):
    """
    Muestra detalles de un slot específico.
    """
    try:
        event = get_object_or_404(Event, id=slot_id)
        
        # Verificar permisos
        if not request.user.is_superuser:
            # Extraer business_unit_id del description
            import re
            match = re.search(r'business_unit_(\d+)', event.description or '')
            if match:
                business_unit_id = int(match.group(1))
                if not BusinessUnit.objects.filter(
                    id=business_unit_id,
                    consultants__person__user=request.user
                ).exists():
                    messages.error(request, 'No tienes permisos para ver este slot')
                    return redirect('interview_slots_dashboard')
        
        # Obtener participantes
        participants = event.participants.all().select_related('person')
        
        # Obtener información de la vacante
        vacancy_info = None
        if event.description:
            import re
            match = re.search(r'vacante_(\d+)', event.description)
            if match:
                try:
                    vacancy = Vacante.objects.get(id=int(match.group(1)))
                    vacancy_info = {
                        'id': vacancy.id,
                        'title': vacancy.titulo,
                        'company': vacancy.empresa.razon_social if vacancy.empresa else 'N/A',
                        'location': vacancy.ubicacion,
                        'mode': vacancy.modalidad
                    }
                except Vacante.DoesNotExist:
                    pass
        
        context = {
            'event': event,
            'participants': participants,
            'vacancy_info': vacancy_info,
            'available_spots': event.lugares_disponibles(),
            'is_group': event.session_type == 'grupal',
            'page_title': f'Detalles del Slot - {event.title}',
            'active_tab': 'interview_slots'
        }
        
        return render(request, 'dashboard/slot_details.html', context)
        
    except Exception as e:
        messages.error(request, f"Error cargando detalles del slot: {str(e)}")
        return redirect('interview_slots_dashboard')

@login_required
def edit_slot(request, slot_id):
    """
    Edita un slot de entrevista.
    """
    event = get_object_or_404(Event, id=slot_id)
    
    # Verificar permisos
    if not request.user.is_superuser:
        import re
        match = re.search(r'business_unit_(\d+)', event.description or '')
        if match:
            business_unit_id = int(match.group(1))
            if not BusinessUnit.objects.filter(
                id=business_unit_id,
                consultants__person__user=request.user
            ).exists():
                messages.error(request, 'No tienes permisos para editar este slot')
                return redirect('interview_slots_dashboard')
    
    if request.method == 'POST':
        try:
            # Actualizar datos del evento
            event.title = request.POST.get('title', event.title)
            event.start_time = datetime.strptime(
                request.POST.get('start_time'), 
                '%Y-%m-%dT%H:%M'
            )
            event.end_time = datetime.strptime(
                request.POST.get('end_time'), 
                '%Y-%m-%dT%H:%M'
            )
            event.location = request.POST.get('location', event.location)
            event.virtual_link = request.POST.get('virtual_link', event.virtual_link)
            event.event_mode = request.POST.get('event_mode', event.event_mode)
            
            if event.session_type == 'grupal':
                event.cupo_maximo = int(request.POST.get('cupo_maximo', event.cupo_maximo or 1))
            
            event.save()
            
            messages.success(request, 'Slot actualizado exitosamente')
            return redirect('slot_details', slot_id=slot_id)
            
        except Exception as e:
            messages.error(request, f"Error actualizando slot: {str(e)}")
    
    context = {
        'event': event,
        'page_title': f'Editar Slot - {event.title}',
        'active_tab': 'interview_slots'
    }
    
    return render(request, 'dashboard/edit_slot.html', context)

@login_required
def delete_slot(request, slot_id):
    """
    Elimina un slot de entrevista.
    """
    if request.method == 'POST':
        try:
            event = get_object_or_404(Event, id=slot_id)
            
            # Verificar permisos
            if not request.user.is_superuser:
                import re
                match = re.search(r'business_unit_(\d+)', event.description or '')
                if match:
                    business_unit_id = int(match.group(1))
                    if not BusinessUnit.objects.filter(
                        id=business_unit_id,
                        consultants__person__user=request.user
                    ).exists():
                        return JsonResponse({
                            'success': False,
                            'error': 'No tienes permisos para eliminar este slot'
                        }, status=403)
            
            # Verificar que no haya participantes confirmados
            confirmed_participants = event.participants.filter(status=EventStatus.CONFIRMADO)
            if confirmed_participants.exists():
                return JsonResponse({
                    'success': False,
                    'error': 'No se puede eliminar un slot con participantes confirmados'
                }, status=400)
            
            # Eliminar participantes pendientes
            event.participants.all().delete()
            
            # Eliminar el evento
            event.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Slot eliminado exitosamente'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

@login_required
def slot_analytics(request):
    """
    Muestra analytics de slots de entrevista.
    """
    try:
        # Obtener parámetros
        business_unit_id = request.GET.get('business_unit')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        
        # Filtrar por unidad de negocio
        if business_unit_id:
            business_unit = get_object_or_404(BusinessUnit, id=business_unit_id)
        else:
            business_unit = None
        
        # Construir filtros
        filters = {'event_type': EventType.ENTREVISTA}
        
        if business_unit:
            filters['description__icontains'] = f'business_unit_{business_unit.id}'
        
        if date_from:
            filters['start_time__gte'] = datetime.strptime(date_from, '%Y-%m-%d')
        else:
            filters['start_time__gte'] = timezone.now() - timedelta(days=30)
        
        if date_to:
            filters['start_time__lte'] = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
        else:
            filters['start_time__lte'] = timezone.now() + timedelta(days=30)
        
        # Obtener eventos
        events = Event.objects.filter(**filters)
        
        # Estadísticas
        total_slots = events.count()
        group_slots = events.filter(session_type='grupal').count()
        individual_slots = events.filter(session_type='individual').count()
        
        confirmed_slots = events.filter(status=EventStatus.CONFIRMADO).count()
        pending_slots = events.filter(status=EventStatus.PENDIENTE).count()
        
        total_participants = EventParticipant.objects.filter(event__in=events).count()
        confirmed_participants = EventParticipant.objects.filter(
            event__in=events,
            status=EventStatus.CONFIRMADO
        ).count()
        
        # Slots por día de la semana
        slots_by_day = events.extra(
            select={'day': 'EXTRACT(dow FROM start_time)'}
        ).values('day').annotate(count=Count('id')).order_by('day')
        
        # Slots por hora
        slots_by_hour = events.extra(
            select={'hour': 'EXTRACT(hour FROM start_time)'}
        ).values('hour').annotate(count=Count('id')).order_by('hour')
        
        # Ocupación de slots grupales
        group_occupation = []
        group_events = events.filter(session_type='grupal')
        for event in group_events:
            total_spots = event.cupo_maximo or 1
            occupied_spots = event.participants.count()
            occupation_rate = (occupied_spots / total_spots) * 100 if total_spots > 0 else 0
            
            group_occupation.append({
                'event_id': event.id,
                'title': event.title,
                'start_time': event.start_time,
                'total_spots': total_spots,
                'occupied_spots': occupied_spots,
                'occupation_rate': round(occupation_rate, 1)
            })
        
        context = {
            'business_unit': business_unit,
            'date_from': date_from,
            'date_to': date_to,
            'stats': {
                'total_slots': total_slots,
                'group_slots': group_slots,
                'individual_slots': individual_slots,
                'confirmed_slots': confirmed_slots,
                'pending_slots': pending_slots,
                'total_participants': total_participants,
                'confirmed_participants': confirmed_participants,
                'group_occupation_rate': round(
                    (confirmed_participants / total_slots) * 100 if total_slots > 0 else 0, 1
                )
            },
            'slots_by_day': list(slots_by_day),
            'slots_by_hour': list(slots_by_hour),
            'group_occupation': group_occupation,
            'page_title': 'Analytics de Slots de Entrevista',
            'active_tab': 'interview_slots'
        }
        
        return render(request, 'dashboard/slot_analytics.html', context)
        
    except Exception as e:
        messages.error(request, f"Error cargando analytics: {str(e)}")
        return redirect('interview_slots_dashboard')
