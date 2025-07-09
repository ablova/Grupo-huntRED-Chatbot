"""
Proveedor de tablas fiscales para México
Implementa acceso a API, caché y fallback para tablas ISR, UMA, etc.
"""
import logging
import requests
from typing import Dict, Any, Optional
from datetime import date
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings

from .base import TaxTableProvider

logger = logging.getLogger(__name__)

class MXTaxProvider(TaxTableProvider):
    """
    Implementación de proveedor fiscal para México
    Soporta tablas ISR, IMSS, UMA y otras constantes fiscales mexicanas
    """
    
    API_BASE_URL = "https://fiscal-api.internal.huntred.com/mx/"
    CACHE_TTL = 86400  # 24 horas en segundos
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Inicializa el proveedor con configuración opcional
        
        Args:
            config: Configuración opcional del proveedor
        """
        self.config = config or {}
        self.api_key = self.config.get('api_key') or getattr(settings, 'FISCAL_API_KEY', None)
        
        # Tablas de fallback por si la API no está disponible
        self._init_fallback_tables()
        
    def _init_fallback_tables(self):
        """Inicializa tablas de fallback"""
        self.fallback_tables = {
            # ISR mensual 2024
            "isr_monthly_2024": {
                "ranges": [
                    {"lower": 0.01, "upper": 746.04, "fixed": 0.00, "percentage": 1.92, "subsidy": 203.70},
                    {"lower": 746.05, "upper": 6332.05, "fixed": 14.32, "percentage": 6.40, "subsidy": 203.70},
                    {"lower": 6332.06, "upper": 11128.01, "fixed": 371.83, "percentage": 10.88, "subsidy": 203.70},
                    {"lower": 11128.02, "upper": 12935.82, "fixed": 893.63, "percentage": 16.00, "subsidy": 203.70},
                    {"lower": 12935.83, "upper": 15487.71, "fixed": 1182.88, "percentage": 17.92, "subsidy": 179.96},
                    {"lower": 15487.72, "upper": 31236.49, "fixed": 1640.18, "percentage": 21.36, "subsidy": 0.00},
                    {"lower": 31236.50, "upper": 49233.00, "fixed": 5004.12, "percentage": 23.52, "subsidy": 0.00},
                    {"lower": 49233.01, "upper": 93993.90, "fixed": 9236.89, "percentage": 30.00, "subsidy": 0.00},
                    {"lower": 93993.91, "upper": 125325.20, "fixed": 22665.17, "percentage": 32.00, "subsidy": 0.00},
                    {"lower": 125325.21, "upper": 375975.61, "fixed": 32691.18, "percentage": 34.00, "subsidy": 0.00},
                    {"lower": 375975.62, "upper": float('inf'), "fixed": 117912.32, "percentage": 35.00, "subsidy": 0.00}
                ],
                "updated_at": "2024-01-01"
            },
            
            # UMA valores
            "uma_values": {
                "2024": 108.57,
                "2023": 103.74,
                "2022": 96.22,
                "2021": 89.62,
                "2020": 86.88
            },
            
            # SMG (Salario Mínimo General)
            "smg_values": {
                "2024": {
                    "general": 248.93,
                    "frontera_norte": 374.89
                },
                "2023": {
                    "general": 207.44,
                    "frontera_norte": 312.41
                },
                "2022": {
                    "general": 172.87,
                    "frontera_norte": 260.34
                }
            }
        }
    
    def get_tax_table(self, table_name: str, year: int, period: str = None) -> Dict[str, Any]:
        """
        Obtiene tabla fiscal de México, primero de caché, luego de API y finalmente fallback
        
        Args:
            table_name: Nombre de la tabla (ej: "isr", "imss", "subsidio")
            year: Año de la tabla
            period: Periodo específico (opcional, ej: "monthly", "biweekly")
            
        Returns:
            Diccionario con la estructura de la tabla
        """
        # Construir key para caché
        cache_key = f"mxtax_{table_name}_{year}"
        if period:
            cache_key += f"_{period}"
            
        # Verificar caché primero
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.debug(f"Cache hit para tabla fiscal: {table_name}")
            return cached_data
            
        # Intentar obtener de API
        if self.api_key:
            try:
                url = f"{self.API_BASE_URL}tables/{table_name}"
                params = {"year": year}
                if period:
                    params["period"] = period
                    
                response = requests.get(
                    url,
                    params=params,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=5
                )
                
                if response.status_code == 200:
                    result = response.json()
                    # Guardar en caché
                    cache.set(cache_key, result, self.CACHE_TTL)
                    logger.info(f"Tabla fiscal {table_name} obtenida de API para {year}")
                    return result
                else:
                    logger.warning(f"Error obteniendo tabla fiscal {table_name}: {response.status_code}")
            except Exception as e:
                logger.error(f"Error en API fiscal: {e}")
        else:
            logger.warning("No hay API key configurada para fiscal API")
            
        # Usar fallback como último recurso
        fallback_key = f"{table_name}_{period}_{year}" if period else f"{table_name}_{year}"
        if fallback_key in self.fallback_tables:
            logger.info(f"Usando tabla fiscal de fallback para {fallback_key}")
            return self.fallback_tables[fallback_key]
        
        # Intentar con tabla genérica sin periodo
        if period and f"{table_name}_{year}" in self.fallback_tables:
            return self.fallback_tables[f"{table_name}_{year}"]
            
        logger.error(f"No se encontró tabla fiscal: {table_name} para {year} {period}")
        return {}
    
    def get_constant(self, constant_name: str, year: int, period: str = None) -> float:
        """
        Obtiene constante fiscal específica
        
        Args:
            constant_name: Nombre de la constante (ej: "uma", "smg")
            year: Año de la constante
            period: Periodo específico (opcional)
            
        Returns:
            Valor de la constante
        """
        # Construir key para caché
        cache_key = f"mxconst_{constant_name}_{year}"
        if period:
            cache_key += f"_{period}"
        
        # Verificar caché primero
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data
            
        # Intentar obtener de API
        if self.api_key:
            try:
                url = f"{self.API_BASE_URL}constants/{constant_name}"
                params = {"year": year}
                if period:
                    params["period"] = period
                    
                response = requests.get(
                    url, 
                    params=params,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=5
                )
                
                if response.status_code == 200:
                    result = response.json()
                    constant_value = float(result.get("value", 0))
                    # Guardar en caché
                    cache.set(cache_key, constant_value, self.CACHE_TTL)
                    return constant_value
            except Exception as e:
                logger.error(f"Error en API fiscal para constante {constant_name}: {e}")
        
        # Usar fallback para constantes específicas
        if constant_name == "uma":
            return self._get_uma_fallback(year)
        elif constant_name == "smg":
            return self._get_smg_fallback(year, period)
            
        logger.error(f"No se encontró constante fiscal: {constant_name} para {year}")
        return 0.0
        
    def is_available(self) -> bool:
        """
        Verifica si el proveedor está disponible
        
        Returns:
            True si el proveedor está activo y disponible
        """
        if not self.api_key:
            # Sin API key, pero tenemos fallbacks
            return True
            
        try:
            response = requests.get(
                f"{self.API_BASE_URL}health",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=2
            )
            return response.status_code == 200
        except:
            # API no disponible, pero tenemos fallbacks
            return True
    
    def _get_uma_fallback(self, year: int) -> float:
        """Obtiene valor UMA de fallback"""
        year_str = str(year)
        if year_str in self.fallback_tables.get("uma_values", {}):
            return self.fallback_tables["uma_values"][year_str]
            
        # Si no existe el año exacto, buscar el más reciente
        years = [int(y) for y in self.fallback_tables.get("uma_values", {}).keys()]
        years.sort(reverse=True)
        for y in years:
            if y <= year:
                logger.warning(f"UMA para {year} no encontrado, usando {y}")
                return self.fallback_tables["uma_values"][str(y)]
                
        return 0.0
        
    def _get_smg_fallback(self, year: int, region: str = None) -> float:
        """Obtiene Salario Mínimo General de fallback"""
        region = region or "general"
        year_str = str(year)
        
        if year_str in self.fallback_tables.get("smg_values", {}):
            smg_data = self.fallback_tables["smg_values"][year_str]
            return smg_data.get(region, smg_data.get("general", 0.0))
            
        # Si no existe el año exacto, buscar el más reciente
        years = [int(y) for y in self.fallback_tables.get("smg_values", {}).keys()]
        years.sort(reverse=True)
        for y in years:
            if y <= year:
                logger.warning(f"SMG para {year} no encontrado, usando {y}")
                smg_data = self.fallback_tables["smg_values"][str(y)]
                return smg_data.get(region, smg_data.get("general", 0.0))
                
        return 0.0
