"""
🗺️ HuntRED® v2 - Location Analytics Service
Advanced location analysis with Google Maps API integration
Supports distance, traffic, and commute analysis by business unit
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import googlemaps
import requests
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
import redis
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class TransportMode(Enum):
    DRIVING = "driving"
    WALKING = "walking"
    BICYCLING = "bicycling"
    TRANSIT = "transit"

class TrafficModel(Enum):
    BEST_GUESS = "best_guess"
    PESSIMISTIC = "pessimistic"
    OPTIMISTIC = "optimistic"

@dataclass
class LocationData:
    """Datos de ubicación completos"""
    address: str
    latitude: float
    longitude: float
    city: str
    state: str
    country: str
    postal_code: str
    formatted_address: str
    place_id: str
    accuracy: str  # ROOFTOP, RANGE_INTERPOLATED, GEOMETRIC_CENTER, APPROXIMATE

@dataclass
class DistanceAnalysis:
    """Análisis de distancia entre dos puntos"""
    origin: LocationData
    destination: LocationData
    distance_km: float
    duration_minutes: int
    duration_in_traffic_minutes: Optional[int]
    transport_mode: str
    traffic_model: str
    route_quality: str  # EXCELLENT, GOOD, FAIR, POOR
    toll_roads: bool
    highways: bool
    alternative_routes: List[Dict[str, Any]]

@dataclass
class CommuteAnalysis:
    """Análisis completo de commute"""
    employee_location: LocationData
    office_location: LocationData
    morning_commute: DistanceAnalysis
    evening_commute: DistanceAnalysis
    weekly_commute_cost: float
    monthly_commute_cost: float
    commute_stress_score: float  # 1-10 scale
    recommended_transport: str
    flexible_work_recommendation: str

@dataclass
class BusinessUnitLocationConfig:
    """Configuración de ubicación por unidad de negocio"""
    business_unit_id: str
    business_unit_name: str
    google_maps_api_key: str
    office_locations: List[LocationData]
    coverage_radius_km: float
    preferred_transport_modes: List[str]
    max_commute_time_minutes: int
    traffic_analysis_enabled: bool
    real_time_updates: bool
    cost_per_km: float  # Para cálculo de costos de transporte

class LocationAnalyticsService:
    """
    Servicio avanzado de análisis de ubicación con Google Maps API
    """
    
    def __init__(self, db: Session, redis_client: redis.Redis):
        self.db = db
        self.redis = redis_client
        
        # Configuraciones por unidad de negocio
        self.business_unit_configs = {}
        
        # Clientes Google Maps por unidad de negocio
        self.gmaps_clients = {}
        
        # Geocodificador alternativo
        self.geocoder = Nominatim(user_agent="huntred-v2-location-service")
        
        # Cache de ubicaciones (24 horas)
        self.location_cache_ttl = 86400
        
        # Configuraciones de tráfico
        self.traffic_config = {
            'peak_hours': {
                'morning': {'start': 7, 'end': 9},
                'evening': {'start': 17, 'end': 19}
            },
            'analysis_days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
            'weekend_factor': 0.7  # Tráfico 30% menor en fines de semana
        }
        
        self.initialized = False
    
    async def initialize_service(self):
        """Inicializar el servicio con configuraciones por unidad de negocio"""
        if self.initialized:
            return
            
        logger.info("🗺️ Inicializando Location Analytics Service...")
        
        # Cargar configuraciones por unidad de negocio
        await self._load_business_unit_configs()
        
        # Inicializar clientes Google Maps
        await self._initialize_gmaps_clients()
        
        # Verificar conectividad
        await self._verify_api_connectivity()
        
        self.initialized = True
        logger.info("✅ Location Analytics Service inicializado")
    
    async def _load_business_unit_configs(self):
        """Cargar configuraciones de ubicación por unidad de negocio"""
        
        # Configuraciones por defecto para cada unidad de negocio
        default_configs = {
            'huntred_executive': {
                'business_unit_id': 'huntred_executive',
                'business_unit_name': 'huntRED® Executive',
                'google_maps_api_key': 'AIzaSyBvOkBwgGlbUiuS2oSI0m-Y_2TLV_d4WzI',  # Configurar desde env
                'office_locations': [
                    {
                        'address': 'Av. Presidente Masaryk 111, Polanco, Ciudad de México',
                        'latitude': 19.4326,
                        'longitude': -99.1332,
                        'city': 'Ciudad de México',
                        'state': 'CDMX',
                        'country': 'México',
                        'postal_code': '11560',
                        'formatted_address': 'Av. Presidente Masaryk 111, Polanco V Secc, Miguel Hidalgo, 11560 Ciudad de México, CDMX',
                        'place_id': 'ChIJN1t_tDeuEmsRUsoyG83frY4',
                        'accuracy': 'ROOFTOP'
                    }
                ],
                'coverage_radius_km': 50.0,
                'preferred_transport_modes': ['driving', 'transit'],
                'max_commute_time_minutes': 90,
                'traffic_analysis_enabled': True,
                'real_time_updates': True,
                'cost_per_km': 8.5  # MXN por km
            },
            'huntred_general': {
                'business_unit_id': 'huntred_general',
                'business_unit_name': 'huntRED®',
                'google_maps_api_key': 'AIzaSyBvOkBwgGlbUiuS2oSI0m-Y_2TLV_d4WzI',
                'office_locations': [
                    {
                        'address': 'Av. Insurgentes Sur 1602, San José Insurgentes, Ciudad de México',
                        'latitude': 19.3629,
                        'longitude': -99.1677,
                        'city': 'Ciudad de México',
                        'state': 'CDMX',
                        'country': 'México',
                        'postal_code': '03900',
                        'formatted_address': 'Av. Insurgentes Sur 1602, San José Insurgentes, Benito Juárez, 03900 Ciudad de México, CDMX',
                        'place_id': 'ChIJdd4hrwug2YgRiHoeI0DAuGQ',
                        'accuracy': 'ROOFTOP'
                    }
                ],
                'coverage_radius_km': 40.0,
                'preferred_transport_modes': ['driving', 'transit', 'walking'],
                'max_commute_time_minutes': 75,
                'traffic_analysis_enabled': True,
                'real_time_updates': True,
                'cost_per_km': 7.0
            },
            'huntU': {
                'business_unit_id': 'huntU',
                'business_unit_name': 'huntU',
                'google_maps_api_key': 'AIzaSyBvOkBwgGlbUiuS2oSI0m-Y_2TLV_d4WzI',
                'office_locations': [
                    {
                        'address': 'Av. Universidad 1449, Oxtopulco Universidad, Ciudad de México',
                        'latitude': 19.3370,
                        'longitude': -99.1890,
                        'city': 'Ciudad de México',
                        'state': 'CDMX',
                        'country': 'México',
                        'postal_code': '04318',
                        'formatted_address': 'Av. Universidad 1449, Oxtopulco Universidad, Coyoacán, 04318 Ciudad de México, CDMX',
                        'place_id': 'ChIJPfQC8Dqg2YgRFTgWnJ-EU9Q',
                        'accuracy': 'ROOFTOP'
                    }
                ],
                'coverage_radius_km': 35.0,
                'preferred_transport_modes': ['transit', 'bicycling', 'walking'],
                'max_commute_time_minutes': 60,
                'traffic_analysis_enabled': True,
                'real_time_updates': False,  # Estudiantes menos crítico
                'cost_per_km': 5.0
            },
            'amigro': {
                'business_unit_id': 'amigro',
                'business_unit_name': 'Amigro',
                'google_maps_api_key': 'AIzaSyBvOkBwgGlbUiuS2oSI0m-Y_2TLV_d4WzI',
                'office_locations': [
                    {
                        'address': 'Av. Central 450, Industrial Vallejo, Ciudad de México',
                        'latitude': 19.4969,
                        'longitude': -99.1269,
                        'city': 'Ciudad de México',
                        'state': 'CDMX',
                        'country': 'México',
                        'postal_code': '02300',
                        'formatted_address': 'Av. Central 450, Industrial Vallejo, Azcapotzalco, 02300 Ciudad de México, CDMX',
                        'place_id': 'ChIJIQBpAG-ahYgRnuiGo2EJzpA',
                        'accuracy': 'ROOFTOP'
                    }
                ],
                'coverage_radius_km': 60.0,  # Mayor cobertura para migrantes
                'preferred_transport_modes': ['transit', 'walking'],
                'max_commute_time_minutes': 120,  # Más flexible
                'traffic_analysis_enabled': True,
                'real_time_updates': False,
                'cost_per_km': 4.0  # Más económico
            }
        }
        
        # Convertir a objetos BusinessUnitLocationConfig
        for unit_id, config in default_configs.items():
            office_locations = [
                LocationData(**loc) for loc in config['office_locations']
            ]
            
            self.business_unit_configs[unit_id] = BusinessUnitLocationConfig(
                business_unit_id=config['business_unit_id'],
                business_unit_name=config['business_unit_name'],
                google_maps_api_key=config['google_maps_api_key'],
                office_locations=office_locations,
                coverage_radius_km=config['coverage_radius_km'],
                preferred_transport_modes=config['preferred_transport_modes'],
                max_commute_time_minutes=config['max_commute_time_minutes'],
                traffic_analysis_enabled=config['traffic_analysis_enabled'],
                real_time_updates=config['real_time_updates'],
                cost_per_km=config['cost_per_km']
            )
        
        logger.info(f"✅ Configuraciones cargadas para {len(self.business_unit_configs)} unidades de negocio")
    
    async def _initialize_gmaps_clients(self):
        """Inicializar clientes Google Maps por unidad de negocio"""
        
        for unit_id, config in self.business_unit_configs.items():
            try:
                self.gmaps_clients[unit_id] = googlemaps.Client(
                    key=config.google_maps_api_key,
                    timeout=10
                )
                logger.info(f"✅ Cliente Google Maps inicializado para {config.business_unit_name}")
                
            except Exception as e:
                logger.error(f"❌ Error inicializando Google Maps para {unit_id}: {e}")
                # Fallback a cliente genérico si está disponible
                self.gmaps_clients[unit_id] = None
    
    async def _verify_api_connectivity(self):
        """Verificar conectividad con Google Maps API"""
        
        for unit_id, client in self.gmaps_clients.items():
            if client:
                try:
                    # Test básico de geocoding
                    result = client.geocode("Ciudad de México, México")
                    if result:
                        logger.info(f"✅ Conectividad Google Maps verificada para {unit_id}")
                    else:
                        logger.warning(f"⚠️ Respuesta vacía de Google Maps para {unit_id}")
                        
                except Exception as e:
                    logger.error(f"❌ Error de conectividad Google Maps para {unit_id}: {e}")
    
    async def geocode_address(self, address: str, business_unit_id: str) -> Optional[LocationData]:
        """
        Geocodificar una dirección usando Google Maps API
        
        Args:
            address: Dirección a geocodificar
            business_unit_id: ID de la unidad de negocio
            
        Returns:
            Datos de ubicación o None si no se puede geocodificar
        """
        
        # Verificar cache
        cache_key = f"geocode:{business_unit_id}:{address}"
        cached_result = await self._get_from_cache(cache_key)
        if cached_result:
            return LocationData(**cached_result)
        
        # Obtener cliente para la unidad de negocio
        client = self.gmaps_clients.get(business_unit_id)
        if not client:
            logger.warning(f"⚠️ No hay cliente Google Maps para {business_unit_id}")
            return await self._fallback_geocode(address)
        
        try:
            # Geocodificar con Google Maps
            results = client.geocode(address, region="mx")  # Bias hacia México
            
            if not results:
                logger.warning(f"⚠️ No se encontraron resultados para: {address}")
                return await self._fallback_geocode(address)
            
            # Tomar el primer resultado
            result = results[0]
            location = result['geometry']['location']
            
            location_data = LocationData(
                address=address,
                latitude=location['lat'],
                longitude=location['lng'],
                city=self._extract_address_component(result, 'locality'),
                state=self._extract_address_component(result, 'administrative_area_level_1'),
                country=self._extract_address_component(result, 'country'),
                postal_code=self._extract_address_component(result, 'postal_code'),
                formatted_address=result['formatted_address'],
                place_id=result['place_id'],
                accuracy=result['geometry']['location_type']
            )
            
            # Guardar en cache
            await self._save_to_cache(cache_key, asdict(location_data))
            
            return location_data
            
        except Exception as e:
            logger.error(f"❌ Error geocodificando {address}: {e}")
            return await self._fallback_geocode(address)
    
    async def _fallback_geocode(self, address: str) -> Optional[LocationData]:
        """Geocodificación de respaldo usando Nominatim"""
        
        try:
            location = self.geocoder.geocode(address, timeout=10)
            if location:
                return LocationData(
                    address=address,
                    latitude=location.latitude,
                    longitude=location.longitude,
                    city="",
                    state="",
                    country="",
                    postal_code="",
                    formatted_address=location.address,
                    place_id="",
                    accuracy="APPROXIMATE"
                )
            return None
            
        except Exception as e:
            logger.error(f"❌ Error en geocodificación de respaldo: {e}")
            return None
    
    def _extract_address_component(self, result: Dict, component_type: str) -> str:
        """Extraer componente de dirección de resultado de Google Maps"""
        
        for component in result.get('address_components', []):
            if component_type in component.get('types', []):
                return component.get('long_name', '')
        return ''
    
    async def calculate_distance_matrix(self, 
                                      origins: List[LocationData],
                                      destinations: List[LocationData],
                                      business_unit_id: str,
                                      transport_mode: TransportMode = TransportMode.DRIVING,
                                      traffic_model: TrafficModel = TrafficModel.BEST_GUESS,
                                      departure_time: Optional[datetime] = None) -> List[List[DistanceAnalysis]]:
        """
        Calcular matriz de distancias entre múltiples orígenes y destinos
        
        Args:
            origins: Lista de ubicaciones de origen
            destinations: Lista de ubicaciones de destino
            business_unit_id: ID de la unidad de negocio
            transport_mode: Modo de transporte
            traffic_model: Modelo de tráfico
            departure_time: Hora de salida para análisis de tráfico
            
        Returns:
            Matriz de análisis de distancias
        """
        
        client = self.gmaps_clients.get(business_unit_id)
        if not client:
            logger.error(f"❌ No hay cliente Google Maps para {business_unit_id}")
            return []
        
        try:
            # Preparar coordenadas
            origin_coords = [(loc.latitude, loc.longitude) for loc in origins]
            dest_coords = [(loc.latitude, loc.longitude) for loc in destinations]
            
            # Configurar parámetros
            params = {
                'origins': origin_coords,
                'destinations': dest_coords,
                'mode': transport_mode.value,
                'units': 'metric',
                'avoid': [],
                'language': 'es',
                'region': 'mx'
            }
            
            # Agregar análisis de tráfico si está disponible
            if transport_mode == TransportMode.DRIVING:
                params['traffic_model'] = traffic_model.value
                if departure_time:
                    params['departure_time'] = departure_time
                else:
                    params['departure_time'] = datetime.now()
            
            # Ejecutar consulta
            result = client.distance_matrix(**params)
            
            # Procesar resultados
            analysis_matrix = []
            
            for i, origin in enumerate(origins):
                origin_results = []
                
                for j, destination in enumerate(destinations):
                    element = result['rows'][i]['elements'][j]
                    
                    if element['status'] == 'OK':
                        distance_analysis = DistanceAnalysis(
                            origin=origin,
                            destination=destination,
                            distance_km=element['distance']['value'] / 1000,
                            duration_minutes=element['duration']['value'] / 60,
                            duration_in_traffic_minutes=element.get('duration_in_traffic', {}).get('value', 0) / 60 if element.get('duration_in_traffic') else None,
                            transport_mode=transport_mode.value,
                            traffic_model=traffic_model.value,
                            route_quality=self._assess_route_quality(element),
                            toll_roads=False,  # Requiere análisis adicional
                            highways=False,    # Requiere análisis adicional
                            alternative_routes=[]
                        )
                    else:
                        # Crear análisis de fallback
                        distance_analysis = self._create_fallback_analysis(
                            origin, destination, transport_mode.value
                        )
                    
                    origin_results.append(distance_analysis)
                
                analysis_matrix.append(origin_results)
            
            return analysis_matrix
            
        except Exception as e:
            logger.error(f"❌ Error calculando matriz de distancias: {e}")
            return []
    
    def _assess_route_quality(self, element: Dict) -> str:
        """Evaluar la calidad de la ruta basada en duración y tráfico"""
        
        duration = element['duration']['value'] / 60  # minutos
        traffic_duration = element.get('duration_in_traffic', {}).get('value', 0) / 60
        
        if traffic_duration == 0:
            return "GOOD"
        
        traffic_ratio = traffic_duration / duration
        
        if traffic_ratio <= 1.1:
            return "EXCELLENT"
        elif traffic_ratio <= 1.3:
            return "GOOD"
        elif traffic_ratio <= 1.6:
            return "FAIR"
        else:
            return "POOR"
    
    def _create_fallback_analysis(self, origin: LocationData, destination: LocationData, transport_mode: str) -> DistanceAnalysis:
        """Crear análisis de distancia de respaldo usando cálculo directo"""
        
        # Calcular distancia directa
        distance_km = geodesic(
            (origin.latitude, origin.longitude),
            (destination.latitude, destination.longitude)
        ).kilometers
        
        # Estimar duración basada en modo de transporte
        speed_km_h = {
            'driving': 30,      # Promedio en ciudad
            'walking': 5,       # Velocidad promedio caminando
            'bicycling': 15,    # Velocidad promedio en bicicleta
            'transit': 25       # Promedio transporte público
        }
        
        duration_minutes = (distance_km / speed_km_h.get(transport_mode, 30)) * 60
        
        return DistanceAnalysis(
            origin=origin,
            destination=destination,
            distance_km=distance_km,
            duration_minutes=int(duration_minutes),
            duration_in_traffic_minutes=None,
            transport_mode=transport_mode,
            traffic_model="fallback",
            route_quality="APPROXIMATE",
            toll_roads=False,
            highways=False,
            alternative_routes=[]
        )
    
    async def analyze_commute_comprehensive(self,
                                         employee_address: str,
                                         business_unit_id: str,
                                         work_schedule: Dict[str, Any] = None) -> Optional[CommuteAnalysis]:
        """
        Análisis comprehensivo de commute para un empleado
        
        Args:
            employee_address: Dirección del empleado
            business_unit_id: ID de la unidad de negocio
            work_schedule: Horario de trabajo (opcional)
            
        Returns:
            Análisis completo de commute
        """
        
        # Geocodificar dirección del empleado
        employee_location = await self.geocode_address(employee_address, business_unit_id)
        if not employee_location:
            logger.error(f"❌ No se pudo geocodificar dirección del empleado: {employee_address}")
            return None
        
        # Obtener configuración de la unidad de negocio
        config = self.business_unit_configs.get(business_unit_id)
        if not config:
            logger.error(f"❌ No hay configuración para unidad de negocio: {business_unit_id}")
            return None
        
        # Analizar commute a cada oficina (tomar la más cercana)
        best_commute = None
        min_commute_time = float('inf')
        
        for office_location in config.office_locations:
            
            # Horarios de análisis
            morning_time = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
            evening_time = datetime.now().replace(hour=18, minute=0, second=0, microsecond=0)
            
            # Análisis de ida (mañana)
            morning_matrix = await self.calculate_distance_matrix(
                origins=[employee_location],
                destinations=[office_location],
                business_unit_id=business_unit_id,
                transport_mode=TransportMode.DRIVING,
                traffic_model=TrafficModel.BEST_GUESS,
                departure_time=morning_time
            )
            
            # Análisis de vuelta (tarde)
            evening_matrix = await self.calculate_distance_matrix(
                origins=[office_location],
                destinations=[employee_location],
                business_unit_id=business_unit_id,
                transport_mode=TransportMode.DRIVING,
                traffic_model=TrafficModel.BEST_GUESS,
                departure_time=evening_time
            )
            
            if morning_matrix and evening_matrix:
                morning_commute = morning_matrix[0][0]
                evening_commute = evening_matrix[0][0]
                
                # Calcular tiempo total de commute
                total_commute_time = (morning_commute.duration_in_traffic_minutes or morning_commute.duration_minutes) + \
                                   (evening_commute.duration_in_traffic_minutes or evening_commute.duration_minutes)
                
                if total_commute_time < min_commute_time:
                    min_commute_time = total_commute_time
                    
                    # Calcular costos y métricas
                    daily_distance = morning_commute.distance_km + evening_commute.distance_km
                    weekly_cost = daily_distance * 5 * config.cost_per_km
                    monthly_cost = weekly_cost * 4.33
                    
                    # Calcular stress score
                    stress_score = self._calculate_commute_stress(
                        morning_commute, evening_commute, config
                    )
                    
                    # Recomendaciones
                    transport_recommendation = self._recommend_transport_mode(
                        morning_commute, config
                    )
                    
                    flexibility_recommendation = self._recommend_flexibility(
                        morning_commute, evening_commute, config
                    )
                    
                    best_commute = CommuteAnalysis(
                        employee_location=employee_location,
                        office_location=office_location,
                        morning_commute=morning_commute,
                        evening_commute=evening_commute,
                        weekly_commute_cost=weekly_cost,
                        monthly_commute_cost=monthly_cost,
                        commute_stress_score=stress_score,
                        recommended_transport=transport_recommendation,
                        flexible_work_recommendation=flexibility_recommendation
                    )
        
        return best_commute
    
    def _calculate_commute_stress(self, morning: DistanceAnalysis, evening: DistanceAnalysis, config: BusinessUnitLocationConfig) -> float:
        """Calcular score de estrés del commute (1-10)"""
        
        # Factores de estrés
        factors = []
        
        # Tiempo total de commute
        total_time = (morning.duration_in_traffic_minutes or morning.duration_minutes) + \
                    (evening.duration_in_traffic_minutes or evening.duration_minutes)
        
        if total_time > config.max_commute_time_minutes:
            factors.append(3.0)  # Excede tiempo máximo
        elif total_time > config.max_commute_time_minutes * 0.8:
            factors.append(2.0)  # Cerca del límite
        else:
            factors.append(1.0)  # Tiempo aceptable
        
        # Calidad de la ruta
        route_quality_scores = {
            'EXCELLENT': 1.0,
            'GOOD': 1.5,
            'FAIR': 2.5,
            'POOR': 4.0,
            'APPROXIMATE': 2.0
        }
        
        morning_quality = route_quality_scores.get(morning.route_quality, 2.0)
        evening_quality = route_quality_scores.get(evening.route_quality, 2.0)
        factors.append((morning_quality + evening_quality) / 2)
        
        # Distancia total
        total_distance = morning.distance_km + evening.distance_km
        if total_distance > 60:
            factors.append(3.0)
        elif total_distance > 40:
            factors.append(2.0)
        else:
            factors.append(1.0)
        
        # Variabilidad de tráfico
        if morning.duration_in_traffic_minutes and evening.duration_in_traffic_minutes:
            morning_ratio = morning.duration_in_traffic_minutes / morning.duration_minutes
            evening_ratio = evening.duration_in_traffic_minutes / evening.duration_minutes
            
            avg_ratio = (morning_ratio + evening_ratio) / 2
            if avg_ratio > 1.5:
                factors.append(3.0)
            elif avg_ratio > 1.2:
                factors.append(2.0)
            else:
                factors.append(1.0)
        else:
            factors.append(1.5)  # Sin datos de tráfico
        
        # Calcular score promedio
        stress_score = sum(factors) / len(factors)
        return min(10.0, max(1.0, stress_score))
    
    def _recommend_transport_mode(self, commute: DistanceAnalysis, config: BusinessUnitLocationConfig) -> str:
        """Recomendar modo de transporte óptimo"""
        
        distance = commute.distance_km
        duration = commute.duration_minutes
        
        # Reglas de recomendación
        if distance <= 2 and 'walking' in config.preferred_transport_modes:
            return "walking"
        elif distance <= 8 and 'bicycling' in config.preferred_transport_modes:
            return "bicycling"
        elif 'transit' in config.preferred_transport_modes and distance <= 25:
            return "transit"
        else:
            return "driving"
    
    def _recommend_flexibility(self, morning: DistanceAnalysis, evening: DistanceAnalysis, config: BusinessUnitLocationConfig) -> str:
        """Recomendar modalidad de trabajo flexible"""
        
        total_time = (morning.duration_in_traffic_minutes or morning.duration_minutes) + \
                    (evening.duration_in_traffic_minutes or evening.duration_minutes)
        
        total_distance = morning.distance_km + evening.distance_km
        
        if total_time > config.max_commute_time_minutes * 1.2:
            return "remote_work_recommended"
        elif total_time > config.max_commute_time_minutes * 0.9:
            return "hybrid_work_recommended"
        elif total_distance > 50:
            return "flexible_hours_recommended"
        else:
            return "office_work_optimal"
    
    async def get_location_insights_for_matching(self, 
                                               candidate_address: str,
                                               job_location: str,
                                               business_unit_id: str) -> Dict[str, Any]:
        """
        Obtener insights de ubicación para el sistema de matching
        
        Args:
            candidate_address: Dirección del candidato
            job_location: Ubicación del trabajo
            business_unit_id: ID de la unidad de negocio
            
        Returns:
            Insights para el matching
        """
        
        # Geocodificar ambas ubicaciones
        candidate_location = await self.geocode_address(candidate_address, business_unit_id)
        job_location_data = await self.geocode_address(job_location, business_unit_id)
        
        if not candidate_location or not job_location_data:
            return {
                'location_match_score': 0.0,
                'commute_feasible': False,
                'insights': ['No se pudo analizar la ubicación']
            }
        
        # Analizar commute
        commute_analysis = await self.analyze_commute_comprehensive(
            candidate_address, business_unit_id
        )
        
        if not commute_analysis:
            return {
                'location_match_score': 0.0,
                'commute_feasible': False,
                'insights': ['No se pudo analizar el commute']
            }
        
        # Calcular score de matching de ubicación
        location_match_score = self._calculate_location_match_score(commute_analysis)
        
        # Generar insights
        insights = self._generate_location_insights(commute_analysis)
        
        return {
            'location_match_score': location_match_score,
            'commute_feasible': commute_analysis.commute_stress_score <= 7.0,
            'commute_time_minutes': (commute_analysis.morning_commute.duration_in_traffic_minutes or 
                                   commute_analysis.morning_commute.duration_minutes) * 2,
            'commute_distance_km': commute_analysis.morning_commute.distance_km * 2,
            'monthly_commute_cost': commute_analysis.monthly_commute_cost,
            'stress_score': commute_analysis.commute_stress_score,
            'recommended_transport': commute_analysis.recommended_transport,
            'work_flexibility_recommendation': commute_analysis.flexible_work_recommendation,
            'insights': insights
        }
    
    def _calculate_location_match_score(self, commute: CommuteAnalysis) -> float:
        """Calcular score de matching basado en ubicación (0-1)"""
        
        # Factores para el score
        factors = []
        
        # Tiempo de commute (peso: 40%)
        total_time = (commute.morning_commute.duration_in_traffic_minutes or 
                     commute.morning_commute.duration_minutes) * 2
        
        if total_time <= 30:
            factors.append(1.0)
        elif total_time <= 60:
            factors.append(0.8)
        elif total_time <= 90:
            factors.append(0.6)
        elif total_time <= 120:
            factors.append(0.4)
        else:
            factors.append(0.2)
        
        # Stress score (peso: 30%)
        stress_factor = max(0.0, (10 - commute.commute_stress_score) / 10)
        factors.append(stress_factor)
        
        # Costo mensual (peso: 20%)
        if commute.monthly_commute_cost <= 2000:
            factors.append(1.0)
        elif commute.monthly_commute_cost <= 4000:
            factors.append(0.8)
        elif commute.monthly_commute_cost <= 6000:
            factors.append(0.6)
        else:
            factors.append(0.4)
        
        # Calidad de ruta (peso: 10%)
        route_quality_scores = {
            'EXCELLENT': 1.0,
            'GOOD': 0.8,
            'FAIR': 0.6,
            'POOR': 0.4,
            'APPROXIMATE': 0.5
        }
        
        quality_score = route_quality_scores.get(commute.morning_commute.route_quality, 0.5)
        factors.append(quality_score)
        
        # Calcular score ponderado
        weights = [0.4, 0.3, 0.2, 0.1]
        weighted_score = sum(factor * weight for factor, weight in zip(factors, weights))
        
        return round(weighted_score, 3)
    
    def _generate_location_insights(self, commute: CommuteAnalysis) -> List[str]:
        """Generar insights sobre la ubicación"""
        
        insights = []
        
        total_time = (commute.morning_commute.duration_in_traffic_minutes or 
                     commute.morning_commute.duration_minutes) * 2
        
        # Insights de tiempo
        if total_time <= 30:
            insights.append("Excelente ubicación - commute muy corto")
        elif total_time <= 60:
            insights.append("Buena ubicación - commute aceptable")
        elif total_time <= 90:
            insights.append("Ubicación regular - commute moderado")
        else:
            insights.append("Ubicación desafiante - commute largo")
        
        # Insights de costo
        if commute.monthly_commute_cost <= 2000:
            insights.append("Costo de transporte bajo")
        elif commute.monthly_commute_cost <= 4000:
            insights.append("Costo de transporte moderado")
        else:
            insights.append("Costo de transporte alto")
        
        # Insights de estrés
        if commute.commute_stress_score <= 3:
            insights.append("Commute de bajo estrés")
        elif commute.commute_stress_score <= 6:
            insights.append("Commute de estrés moderado")
        else:
            insights.append("Commute de alto estrés")
        
        # Recomendaciones específicas
        if commute.flexible_work_recommendation == "remote_work_recommended":
            insights.append("Se recomienda trabajo remoto")
        elif commute.flexible_work_recommendation == "hybrid_work_recommended":
            insights.append("Se recomienda trabajo híbrido")
        elif commute.flexible_work_recommendation == "flexible_hours_recommended":
            insights.append("Se recomienda horario flexible")
        
        return insights
    
    async def _get_from_cache(self, key: str) -> Optional[Dict]:
        """Obtener datos del cache Redis"""
        try:
            cached_data = self.redis.get(key)
            if cached_data:
                return json.loads(cached_data)
            return None
        except Exception as e:
            logger.error(f"❌ Error obteniendo del cache: {e}")
            return None
    
    async def _save_to_cache(self, key: str, data: Dict, ttl: int = None):
        """Guardar datos en cache Redis"""
        try:
            ttl = ttl or self.location_cache_ttl
            self.redis.setex(key, ttl, json.dumps(data))
        except Exception as e:
            logger.error(f"❌ Error guardando en cache: {e}")
    
    async def get_service_health(self) -> Dict[str, Any]:
        """Obtener estado de salud del servicio"""
        
        health_status = {
            'service_name': 'Location Analytics Service',
            'status': 'healthy',
            'business_units': {},
            'cache_status': 'unknown',
            'last_check': datetime.now().isoformat()
        }
        
        # Verificar estado por unidad de negocio
        for unit_id, config in self.business_unit_configs.items():
            client = self.gmaps_clients.get(unit_id)
            
            if client:
                try:
                    # Test rápido de geocoding
                    result = client.geocode("México")
                    unit_status = 'healthy' if result else 'degraded'
                except Exception:
                    unit_status = 'unhealthy'
            else:
                unit_status = 'no_client'
            
            health_status['business_units'][unit_id] = {
                'name': config.business_unit_name,
                'status': unit_status,
                'api_key_configured': bool(config.google_maps_api_key),
                'office_locations': len(config.office_locations),
                'traffic_analysis': config.traffic_analysis_enabled
            }
        
        # Verificar cache
        try:
            self.redis.ping()
            health_status['cache_status'] = 'healthy'
        except Exception:
            health_status['cache_status'] = 'unhealthy'
        
        # Determinar estado general
        unit_statuses = [unit['status'] for unit in health_status['business_units'].values()]
        if all(status == 'healthy' for status in unit_statuses):
            health_status['status'] = 'healthy'
        elif any(status == 'healthy' for status in unit_statuses):
            health_status['status'] = 'degraded'
        else:
            health_status['status'] = 'unhealthy'
        
        return health_status

# Instancia global del servicio
location_service = None

def get_location_service(db: Session, redis_client: redis.Redis) -> LocationAnalyticsService:
    """Obtener instancia del servicio de análisis de ubicación"""
    global location_service
    
    if location_service is None:
        location_service = LocationAnalyticsService(db, redis_client)
    
    return location_service