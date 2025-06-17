"""
Modelo para manejar los rankings QS de universidades.
"""
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np

class QSRankingModel:
    """Modelo para procesar y normalizar rankings QS."""
    
    def __init__(self):
        """Inicializa el modelo de rankings QS."""
        self.rankings: Dict[str, Dict[str, Any]] = {}
        self.metrics = {
            'academic_reputation': 'Academic Reputation',
            'employer_reputation': 'Employer Reputation',
            'faculty_student': 'Faculty Student',
            'citations': 'Citations per Faculty',
            'international_faculty': 'International Faculty',
            'international_students': 'International Students',
            'international_research': 'International Research Network',
            'employment_outcomes': 'Employment Outcomes',
            'sustainability': 'Sustainability'
        }
        
    def load_rankings(self, file_path: str) -> None:
        """
        Carga los rankings desde un archivo Excel.
        
        Args:
            file_path: Ruta al archivo Excel con rankings QS
        """
        try:
            df = pd.read_excel(file_path)
            for _, row in df.iterrows():
                university = row['Institution Name']
                self.rankings[university] = {
                    'rank_2025': int(row['2025']),
                    'rank_2024': int(row['2024']),
                    'location': row['Location'],
                    'region': row['Classification'],
                    'size': row['SIZE'],
                    'focus': row['FOCUS'],
                    'research': row['RES.'],
                    'status': row['STATUS'],
                    'scores': {
                        'academic_reputation': float(row['Academic Reputation']),
                        'employer_reputation': float(row['Employer Reputation']),
                        'faculty_student': float(row['Faculty Student']),
                        'citations': float(row['Citations per Faculty']),
                        'international_faculty': float(row['International Faculty']),
                        'international_students': float(row['International Students']),
                        'international_research': float(row['International Research Network']),
                        'employment_outcomes': float(row['Employment Outcomes']),
                        'sustainability': float(row['Sustainability'])
                    },
                    'overall_score': float(row['Overall'])
                }
        except Exception as e:
            print(f"Error cargando rankings QS: {str(e)}")
            
    def get_university_rank(self, university: str) -> Optional[int]:
        """
        Obtiene el ranking de una universidad.
        
        Args:
            university: Nombre de la universidad
            
        Returns:
            Ranking de la universidad o None si no se encuentra
        """
        if university in self.rankings:
            return self.rankings[university]['rank_2025']
        return None
        
    def get_university_score(self, university: str) -> Optional[float]:
        """
        Obtiene el score general de una universidad.
        
        Args:
            university: Nombre de la universidad
            
        Returns:
            Score general (0-100) o None si no se encuentra
        """
        if university in self.rankings:
            return self.rankings[university]['overall_score']
        return None
        
    def get_metric_score(self, university: str, metric: str) -> Optional[float]:
        """
        Obtiene el score de una métrica específica.
        
        Args:
            university: Nombre de la universidad
            metric: Nombre de la métrica
            
        Returns:
            Score de la métrica (0-100) o None si no se encuentra
        """
        if university in self.rankings and metric in self.metrics:
            return self.rankings[university]['scores'].get(metric)
        return None
        
    def get_top_universities(self, n: int = 100) -> List[Dict[str, Any]]:
        """
        Obtiene las top N universidades.
        
        Args:
            n: Número de universidades a retornar
            
        Returns:
            Lista de diccionarios con información de las universidades
        """
        sorted_universities = sorted(
            self.rankings.items(),
            key=lambda x: x[1]['rank_2025']
        )[:n]
        
        return [
            {
                'name': name,
                'rank': data['rank_2025'],
                'location': data['location'],
                'score': data['overall_score']
            }
            for name, data in sorted_universities
        ]
        
    def get_universities_by_region(self, region: str) -> List[Dict[str, Any]]:
        """
        Obtiene universidades por región.
        
        Args:
            region: Región a filtrar
            
        Returns:
            Lista de diccionarios con información de las universidades
        """
        return [
            {
                'name': name,
                'rank': data['rank_2025'],
                'location': data['location'],
                'score': data['overall_score']
            }
            for name, data in self.rankings.items()
            if data['region'] == region
        ]
        
    def get_universities_by_country(self, country: str) -> List[Dict[str, Any]]:
        """
        Obtiene universidades por país.
        
        Args:
            country: País a filtrar
            
        Returns:
            Lista de diccionarios con información de las universidades
        """
        return [
            {
                'name': name,
                'rank': data['rank_2025'],
                'location': data['location'],
                'score': data['overall_score']
            }
            for name, data in self.rankings.items()
            if data['location'] == country
        ] 