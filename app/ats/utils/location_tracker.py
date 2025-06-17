"""
Servicio para el seguimiento de ubicación de candidatos en entrevistas.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
from django.utils import timezone

from app.models import Person, Interview
from app.ats.integrations.maps import GoogleMapsService
from app.ats.integrations.traffic import TrafficAnalyzer

logger = logging.getLogger(__name__)

class LocationTracker:
    """
    Servicio para rastrear la ubicación de candidatos y calcular tiempos de llegada.
    """
    
    def __init__(self):
        """Inicializa el servicio con las integraciones necesarias."""
        self.maps_service = GoogleMapsService()
        self.traffic_analyzer = TrafficAnalyzer()
        
    async def get_current_location(self, person: Person) -> Dict[str, Any]:
        """
        Obtiene la ubicación actual del candidato.
        
        Args:
            person: Candidato a rastrear
            
        Returns:
            Dict con información de ubicación
        """
        try:
            # Obtener ubicación del dispositivo
            location = await self.maps_service.get_device_location(person.device_id)
            
            # Obtener información adicional
            address = await self.maps_service.get_address_from_coordinates(
                location['latitude'],
                location['longitude']
            )
            
            return {
                'latitude': location['latitude'],
                'longitude': location['longitude'],
                'name': address['formatted_address'],
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo ubicación actual: {str(e)}")
            return None
            
    async def calculate_distance(
        self,
        current_location: Dict[str, Any],
        target_location: Dict[str, Any]
    ) -> float:
        """
        Calcula la distancia entre dos ubicaciones.
        
        Args:
            current_location: Ubicación actual
            target_location: Ubicación objetivo
            
        Returns:
            Distancia en kilómetros
        """
        try:
            distance = await self.maps_service.calculate_distance(
                origin={
                    'lat': current_location['latitude'],
                    'lng': current_location['longitude']
                },
                destination={
                    'lat': target_location['latitude'],
                    'lng': target_location['longitude']
                }
            )
            
            return distance['value'] / 1000  # Convertir a kilómetros
            
        except Exception as e:
            logger.error(f"Error calculando distancia: {str(e)}")
            return None
            
    async def estimate_arrival_time(
        self,
        current_location: Dict[str, Any],
        target_location: Dict[str, Any],
        target_time: datetime
    ) -> Optional[datetime]:
        """
        Estima el tiempo de llegada considerando el tráfico.
        
        Args:
            current_location: Ubicación actual
            target_location: Ubicación objetivo
            target_time: Hora objetivo de llegada
            
        Returns:
            Hora estimada de llegada
        """
        try:
            # Obtener condiciones de tráfico
            traffic_conditions = await self.traffic_analyzer.get_traffic_conditions(
                origin={
                    'lat': current_location['latitude'],
                    'lng': current_location['longitude']
                },
                destination={
                    'lat': target_location['latitude'],
                    'lng': target_location['longitude']
                },
                departure_time=timezone.now()
            )
            
            # Calcular tiempo de viaje
            travel_time = await self.maps_service.calculate_travel_time(
                origin={
                    'lat': current_location['latitude'],
                    'lng': current_location['longitude']
                },
                destination={
                    'lat': target_location['latitude'],
                    'lng': target_location['longitude']
                },
                traffic_conditions=traffic_conditions
            )
            
            # Calcular hora de llegada
            arrival_time = timezone.now() + timedelta(seconds=travel_time['value'])
            
            return arrival_time
            
        except Exception as e:
            logger.error(f"Error estimando tiempo de llegada: {str(e)}")
            return None
            
    async def start_location_tracking(self, interview_id: int, interval_minutes: int = 5):
        """
        Inicia el seguimiento de ubicación para una entrevista.
        
        Args:
            interview_id: ID de la entrevista
            interval_minutes: Intervalo de actualización en minutos
        """
        try:
            interview = await Interview.objects.aget(id=interview_id)
            
            while True:
                # Verificar si la entrevista ya pasó
                if timezone.now() > interview.interview_date:
                    break
                    
                # Obtener ubicación actual
                current_location = await self.get_current_location(interview.person)
                if not current_location:
                    continue
                    
                # Calcular distancia
                distance = await self.calculate_distance(
                    current_location,
                    interview.location
                )
                
                # Determinar estado
                if distance < 1:  # Menos de 1 km
                    status = 'cerca'
                elif distance < 5:  # Menos de 5 km
                    status = 'en_traslado'
                else:
                    status = 'llegando_tarde'
                    
                # Calcular tiempo estimado de llegada
                estimated_arrival = await self.estimate_arrival_time(
                    current_location,
                    interview.location,
                    interview.interview_date
                )
                
                # Actualizar estado
                await interview.update_location(current_location, status)
                if estimated_arrival:
                    interview.estimated_arrival = estimated_arrival
                    await interview.asave()
                
                # Esperar hasta la siguiente actualización
                await asyncio.sleep(interval_minutes * 60)
                
        except Exception as e:
            logger.error(f"Error en seguimiento de ubicación: {str(e)}")
            
    async def stop_location_tracking(self, interview_id: int):
        """
        Detiene el seguimiento de ubicación para una entrevista.
        
        Args:
            interview_id: ID de la entrevista
        """
        try:
            interview = await Interview.objects.aget(id=interview_id)
            interview.location_status = None
            interview.current_location = None
            interview.estimated_arrival = None
            await interview.asave()
            
        except Exception as e:
            logger.error(f"Error deteniendo seguimiento: {str(e)}") 