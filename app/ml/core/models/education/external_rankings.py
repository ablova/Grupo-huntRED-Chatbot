"""
Adaptador para rankings educativos externos.
"""
from typing import Dict, List, Optional, Any
import requests
import pandas as pd
from datetime import datetime
import json

class ExternalRankingsAdapter:
    """Adaptador para rankings educativos externos."""
    
    def __init__(self):
        """Inicializa el adaptador."""
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_timestamp: Dict[str, datetime] = {}
        
    def get_edurank_data(self, 
                        university: str,
                        program: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Obtiene datos de edurank.org.
        
        Args:
            university: Nombre de la universidad
            program: Nombre del programa (opcional)
            
        Returns:
            Datos de edurank o None si no se encuentra
        """
        # Verificar caché
        cache_key = f"{university}_{program}" if program else university
        if cache_key in self.cache:
            # Verificar si el caché está expirado (24 horas)
            if (datetime.now() - self.cache_timestamp[cache_key]).days < 1:
                return self.cache[cache_key]
                
        try:
            # Construir URL
            url = f"https://edurank.org/api/v1/universities/{university}"
            if program:
                url += f"/programs/{program}"
                
            # Hacer request
            response = requests.get(url)
            response.raise_for_status()
            
            # Procesar respuesta
            data = response.json()
            
            # Guardar en caché
            self.cache[cache_key] = data
            self.cache_timestamp[cache_key] = datetime.now()
            
            return data
            
        except Exception as e:
            print(f"Error obteniendo datos de edurank: {e}")
            return None
            
    def get_ranking_data(self, 
                        source: str,
                        university: str,
                        program: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Obtiene datos de rankings de diferentes fuentes.
        
        Args:
            source: Fuente del ranking ('edurank', 'qs', etc.)
            university: Nombre de la universidad
            program: Nombre del programa (opcional)
            
        Returns:
            Datos del ranking o None si no se encuentra
        """
        if source == 'edurank':
            return self.get_edurank_data(university, program)
        # Agregar más fuentes según sea necesario
        return None
        
    def get_metrics(self,
                   university: str,
                   program: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtiene métricas combinadas de diferentes fuentes.
        
        Args:
            university: Nombre de la universidad
            program: Nombre del programa (opcional)
            
        Returns:
            Métricas combinadas
        """
        metrics = {
            'rankings': {},
            'scores': {},
            'metrics': {}
        }
        
        # Obtener datos de edurank
        edurank_data = self.get_edurank_data(university, program)
        if edurank_data:
            metrics['rankings']['edurank'] = edurank_data.get('rank')
            metrics['scores']['edurank'] = edurank_data.get('score')
            metrics['metrics'].update(edurank_data.get('metrics', {}))
            
        # Agregar más fuentes según sea necesario
        
        return metrics
        
    def get_top_universities(self,
                           source: str,
                           n: int = 10,
                           program: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtiene las top N universidades de una fuente.
        
        Args:
            source: Fuente del ranking
            n: Número de universidades a retornar
            program: Filtrar por programa (opcional)
            
        Returns:
            Lista de diccionarios con información de las universidades
        """
        if source == 'edurank':
            try:
                # Construir URL
                url = "https://edurank.org/api/v1/rankings"
                if program:
                    url += f"/programs/{program}"
                    
                # Hacer request
                response = requests.get(url)
                response.raise_for_status()
                
                # Procesar respuesta
                data = response.json()
                
                # Ordenar y limitar
                universities = sorted(
                    data['universities'],
                    key=lambda x: x['rank']
                )[:n]
                
                return [
                    {
                        'university': u['name'],
                        'rank': u['rank'],
                        'score': u['score'],
                        'country': u['country']
                    }
                    for u in universities
                ]
                
            except Exception as e:
                print(f"Error obteniendo top universidades de edurank: {e}")
                return []
                
        return [] 