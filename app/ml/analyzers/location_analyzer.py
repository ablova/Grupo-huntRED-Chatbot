"""
Location Analyzer module for Grupo huntRED® assessment system.

Este módulo analiza y procesa información de ubicación y tráfico
para optimizar el matching de candidatos con vacantes.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import googlemaps
from django.conf import settings
from app.ml.analyzers.base_analyzer import BaseAnalyzer
from app.models import BusinessUnit, Person, Vacante, ConfiguracionBU
from django.core.cache import cache

logger = logging.getLogger(__name__)

class LocationAnalyzer(BaseAnalyzer):
    """
    Analizador de ubicación y tráfico para optimizar matching.
    
    Integra información de ubicación y patrones de tráfico
    para mejorar la precisión del matching.
    """
    
    def __init__(self, business_unit: Optional[BusinessUnit] = None):
        """
        Inicializa el analizador de ubicación.
        
        Args:
            business_unit: Unidad de negocio para la que se realizará el análisis
        """
        super().__init__()
        self.business_unit = business_unit
        self.config = self._load_config()
        self.gmaps = self._initialize_gmaps()
        self.cache_timeout = self.config['cache_ttl']
        self.traffic_thresholds = {
            'low': self.config['traffic_threshold'],
            'medium': self.config['traffic_threshold'] * 2,
            'high': self.config['traffic_threshold'] * 3
        }
    
    def _load_config(self) -> Dict:
        """Carga la configuración de Google Maps desde ConfiguracionBU."""
        try:
            if self.business_unit:
                config = ConfiguracionBU.objects.get(business_unit=self.business_unit)
                return config.get_google_maps_config()
            else:
                # Configuración por defecto
                return {
                    'api_key': None,
                    'cache_ttl': 3600,
                    'traffic_threshold': 30,
                    'alternative_routes': 3,
                    'commute_hours': {
                        'morning': ['08:00', '09:00'],
                        'evening': ['17:00', '18:00']
                    }
                }
        except ConfiguracionBU.DoesNotExist:
            logger.warning(f"No se encontró configuración para {self.business_unit}")
            return self._load_config()
    
    def _initialize_gmaps(self) -> Optional[googlemaps.Client]:
        """Inicializa el cliente de Google Maps."""
        if not self.config['api_key']:
            logger.warning("No se encontró API key de Google Maps")
            return None
            
        try:
            return googlemaps.Client(key=self.config['api_key'])
        except Exception as e:
            logger.error(f"Error inicializando Google Maps: {str(e)}")
            return None
    
    def get_required_fields(self) -> List[str]:
        """Get required fields for location analysis."""
        return ['person_id', 'business_unit']
    
    async def analyze(self, data: Dict, business_unit: Optional[BusinessUnit] = None) -> Dict:
        """
        Analiza la ubicación y patrones de tráfico.
        
        Args:
            data: Diccionario con datos de ubicación
            business_unit: Unidad de negocio para contexto
            
        Returns:
            Dict con análisis de ubicación y tráfico
        """
        try:
            person_id = data.get('person_id')
            person = await self._get_person_async(person_id)
            
            if not person or not person.lat or not person.lon:
                return self.get_default_result("Ubicación no disponible")
            
            # Obtener vacantes relevantes
            vacancies = await self._get_relevant_vacancies(person, business_unit)
            
            # Analizar patrones de tráfico
            traffic_analysis = await self._analyze_traffic_patterns(
                person.lat,
                person.lon,
                vacancies
            )
            
            # Calcular scores de accesibilidad
            accessibility_scores = await self._calculate_accessibility_scores(
                person,
                vacancies,
                traffic_analysis
            )
            
            return {
                'traffic_analysis': traffic_analysis,
                'accessibility_scores': accessibility_scores,
                'recommendations': self._generate_recommendations(
                    traffic_analysis,
                    accessibility_scores
                ),
                'metadata': {
                    'cache_ttl': self.cache_timeout,
                    'traffic_threshold': self.traffic_thresholds['low']
                }
            }
            
        except Exception as e:
            logger.error(f"Error en análisis de ubicación: {str(e)}")
            return self.get_default_result(str(e))
    
    async def _analyze_traffic_patterns(
        self,
        origin_lat: float,
        origin_lon: float,
        vacancies: List[Vacante]
    ) -> Dict:
        """
        Analiza patrones de tráfico para múltiples destinos.
        
        Args:
            origin_lat: Latitud de origen
            origin_lon: Longitud de origen
            vacancies: Lista de vacantes a analizar
            
        Returns:
            Dict con análisis de tráfico
        """
        traffic_data = {}
        
        for vacancy in vacancies:
            if not vacancy.lat or not vacancy.lon:
                continue
                
            # Obtener tiempos de viaje para diferentes horarios
            commute_times = await self._get_commute_times(
                origin_lat,
                origin_lon,
                vacancy.lat,
                vacancy.lon
            )
            
            traffic_data[vacancy.id] = {
                'morning_commute': commute_times.get('morning'),
                'evening_commute': commute_times.get('evening'),
                'traffic_level': self._calculate_traffic_level(commute_times),
                'alternative_routes': await self._get_alternative_routes(
                    origin_lat,
                    origin_lon,
                    vacancy.lat,
                    vacancy.lon
                )
            }
        
        return traffic_data
    
    async def _get_commute_times(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float
    ) -> Dict:
        """
        Obtiene tiempos de viaje para diferentes horarios.
        
        Args:
            origin_lat: Latitud de origen
            origin_lon: Longitud de origen
            dest_lat: Latitud de destino
            dest_lon: Longitud de destino
            
        Returns:
            Dict con tiempos de viaje
        """
        try:
            results = {}
            
            for period, hours in self.config['commute_hours'].items():
                for hour in hours:
                    time = datetime.strptime(hour, '%H:%M').time()
                    results[f"{period}_{hour}"] = await self._get_commute_time(
                        (origin_lat, origin_lon),
                        (dest_lat, dest_lon),
                        time
                    )
            
            return results
            
        except Exception as e:
            logger.error(f"Error obteniendo tiempos de viaje: {str(e)}")
            return {}
    
    async def _get_commute_time(self, origin: Dict, destination: Dict, time: datetime.time) -> Dict:
        """Obtiene el tiempo de viaje para un horario específico."""
        try:
            result = self.gmaps.directions(
                origin,
                destination,
                mode="driving",
                departure_time=time
            )
            
            if not result:
                return {'error': 'No se encontró ruta'}
            
            route = result[0]['legs'][0]
            return {
                'duration': route['duration']['value'] // 60,  # Convertir a minutos
                'distance': route['distance']['value'] / 1000,  # Convertir a km
                'traffic_level': self._calculate_traffic_level(route)
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo tiempo de viaje: {str(e)}")
            return {'error': str(e)}
    
    def _calculate_traffic_level(self, commute_times: Dict) -> str:
        """
        Calcula el nivel de tráfico basado en tiempos de viaje.
        
        Args:
            commute_times: Diccionario con tiempos de viaje
            
        Returns:
            str: Nivel de tráfico ('low', 'medium', 'high')
        """
        avg_time = sum(commute_times.values()) / len(commute_times)
        
        if avg_time <= self.traffic_thresholds['low']:
            return 'low'
        elif avg_time <= self.traffic_thresholds['medium']:
            return 'medium'
        else:
            return 'high'
    
    async def _get_alternative_routes(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float
    ) -> List[Dict]:
        """
        Obtiene rutas alternativas.
        
        Args:
            origin_lat: Latitud de origen
            origin_lon: Longitud de origen
            dest_lat: Latitud de destino
            dest_lon: Longitud de destino
            
        Returns:
            List[Dict]: Lista de rutas alternativas
        """
        try:
            result = self.gmaps.directions(
                (origin_lat, origin_lon),
                (dest_lat, dest_lon),
                mode="driving",
                alternatives=True
            )
            
            routes = []
            for route in result[:self.config['alternative_routes']]:
                leg = route['legs'][0]
                routes.append({
                    'duration': leg['duration']['value'] // 60,
                    'distance': leg['distance']['value'] / 1000,
                    'traffic_level': self._calculate_traffic_level(leg),
                    'steps': self._extract_route_steps(route)
                })
            
            return routes
            
        except Exception as e:
            logger.error(f"Error obteniendo rutas alternativas: {str(e)}")
            return []
    
    def _extract_route_steps(self, route: Dict) -> List[Dict]:
        """Extrae los pasos de una ruta."""
        return [
            {
                'instruction': step['html_instructions'],
                'distance': step['distance']['value'] / 1000,
                'duration': step['duration']['value'] // 60
            }
            for step in route['legs'][0]['steps']
        ] 