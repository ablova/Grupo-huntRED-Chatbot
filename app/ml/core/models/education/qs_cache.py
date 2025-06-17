"""
Modelo de caché para rankings QS.
"""
from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime, timedelta
import redis
import json

class QSCache:
    """Caché para rankings QS."""
    
    def __init__(self, 
                 redis_url: str = 'redis://localhost:6379/0',
                 cache_ttl: int = 86400):  # 24 horas
        """
        Inicializa el caché QS.
        
        Args:
            redis_url: URL de Redis
            cache_ttl: Tiempo de vida del caché en segundos
        """
        self.redis = redis.from_url(redis_url)
        self.cache_ttl = cache_ttl
        self.cache_key = 'qs_rankings'
        
    def update_rankings(self, rankings: Dict[str, Dict[str, Any]]) -> None:
        """
        Actualiza los rankings en caché.
        
        Args:
            rankings: Diccionario con rankings
        """
        data = {
            'timestamp': datetime.now().isoformat(),
            'rankings': rankings
        }
        self.redis.setex(
            self.cache_key,
            self.cache_ttl,
            json.dumps(data)
        )
        
    def get_rankings(self) -> Optional[Dict[str, Dict[str, Any]]]:
        """
        Obtiene los rankings desde caché.
        
        Returns:
            Diccionario con rankings o None si no hay datos
        """
        data = self.redis.get(self.cache_key)
        if not data:
            return None
            
        data = json.loads(data)
        timestamp = datetime.fromisoformat(data['timestamp'])
        
        # Verificar si los datos están expirados
        if datetime.now() - timestamp > timedelta(seconds=self.cache_ttl):
            return None
            
        return data['rankings']
        
    def get_university_rank(self, university: str) -> Optional[int]:
        """
        Obtiene el ranking de una universidad.
        
        Args:
            university: Nombre de la universidad
            
        Returns:
            Ranking o None si no se encuentra
        """
        rankings = self.get_rankings()
        if not rankings:
            return None
            
        return rankings.get(university, {}).get('rank')
        
    def get_university_score(self, university: str) -> Optional[float]:
        """
        Obtiene el score de una universidad.
        
        Args:
            university: Nombre de la universidad
            
        Returns:
            Score o None si no se encuentra
        """
        rankings = self.get_rankings()
        if not rankings:
            return None
            
        return rankings.get(university, {}).get('score')
        
    def load_from_excel(self, file_path: str) -> None:
        """
        Carga rankings desde Excel.
        
        Args:
            file_path: Ruta al archivo Excel
        """
        # Leer Excel en chunks para optimizar memoria
        chunks = pd.read_excel(file_path, chunksize=1000)
        
        rankings = {}
        for chunk in chunks:
            for _, row in chunk.iterrows():
                university = row['University']
                rankings[university] = {
                    'rank': int(row['Rank']),
                    'score': float(row['Score']),
                    'country': row['Country'],
                    'faculty_student': float(row['Faculty/Student']),
                    'international_faculty': float(row['International Faculty']),
                    'international_students': float(row['International Students']),
                    'citations': float(row['Citations']),
                    'employer_reputation': float(row['Employer Reputation']),
                    'academic_reputation': float(row['Academic Reputation'])
                }
                
        self.update_rankings(rankings)
        
    def get_metrics(self, university: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene métricas detalladas de una universidad.
        
        Args:
            university: Nombre de la universidad
            
        Returns:
            Métricas o None si no se encuentra
        """
        rankings = self.get_rankings()
        if not rankings:
            return None
            
        return rankings.get(university)
        
    def get_top_universities(self, 
                           n: int = 10,
                           country: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtiene las top N universidades.
        
        Args:
            n: Número de universidades a retornar
            country: Filtrar por país (opcional)
            
        Returns:
            Lista de diccionarios con información de las universidades
        """
        rankings = self.get_rankings()
        if not rankings:
            return []
            
        # Filtrar por país si se especifica
        if country:
            rankings = {
                name: data
                for name, data in rankings.items()
                if data['country'] == country
            }
            
        # Ordenar por ranking
        sorted_universities = sorted(
            rankings.items(),
            key=lambda x: x[1]['rank']
        )[:n]
        
        return [
            {
                'university': name,
                'rank': data['rank'],
                'score': data['score'],
                'country': data['country']
            }
            for name, data in sorted_universities
        ] 