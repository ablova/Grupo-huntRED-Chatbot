"""
Cargador de datos para rankings de universidades y programas.
"""
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np
from pathlib import Path

class EducationDataLoader:
    """Cargador de datos para rankings educativos."""
    
    def __init__(self):
        """Inicializa el cargador de datos."""
        self.university_data: Dict[str, Dict[str, Any]] = {}
        self.program_data: Dict[str, Dict[str, Any]] = {}
        
    def load_university_data(self, file_path: str) -> None:
        """
        Carga datos de universidades desde Excel.
        
        Args:
            file_path: Ruta al archivo Excel
        """
        # Leer Excel
        df = pd.read_excel(file_path, sheet_name='Universidades')
        
        # Procesar cada universidad
        for _, row in df.iterrows():
            university = row['Universidad']
            self.university_data[university] = {
                'score': float(row['Score Base']),
                'ranking': int(row['Ranking Nacional']),
                'cost': row['Nivel Costo'],
                'is_international': bool(row['Internacional']),
                'specialties': row['Especialidades'].split(',') if pd.notna(row['Especialidades']) else [],
                'qs_rank': int(row['Ranking QS']) if pd.notna(row['Ranking QS']) else None,
                'qs_score': float(row['Score QS']) if pd.notna(row['Score QS']) else None
            }
            
    def load_program_data(self, file_path: str) -> None:
        """
        Carga datos de programas desde Excel.
        
        Args:
            file_path: Ruta al archivo Excel
        """
        # Leer Excel
        df = pd.read_excel(file_path, sheet_name='Programas')
        
        # Procesar cada programa
        for _, row in df.iterrows():
            program = row['Programa']
            university = row['Universidad']
            
            if program not in self.program_data:
                self.program_data[program] = {}
                
            self.program_data[program][university] = {
                'ranking': int(row['Ranking']),
                'category': row['Categoría'],
                'metrics': {
                    'quality': float(row['Calidad']),
                    'demand': float(row['Demanda']),
                    'salary': float(row['Salario'])
                }
            }
            
    def get_university_data(self) -> Dict[str, Dict[str, Any]]:
        """
        Obtiene los datos de universidades.
        
        Returns:
            Diccionario con datos de universidades
        """
        return self.university_data
        
    def get_program_data(self) -> Dict[str, Dict[str, Any]]:
        """
        Obtiene los datos de programas.
        
        Returns:
            Diccionario con datos de programas
        """
        return self.program_data
        
    def get_university_metrics(self, university: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene métricas de una universidad.
        
        Args:
            university: Nombre de la universidad
            
        Returns:
            Métricas de la universidad o None si no se encuentra
        """
        return self.university_data.get(university)
        
    def get_program_metrics(self, 
                          program: str,
                          university: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene métricas de un programa en una universidad.
        
        Args:
            program: Nombre del programa
            university: Nombre de la universidad
            
        Returns:
            Métricas del programa o None si no se encuentra
        """
        return self.program_data.get(program, {}).get(university)
        
    def get_top_universities(self, n: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene las top N universidades.
        
        Args:
            n: Número de universidades a retornar
            
        Returns:
            Lista de diccionarios con información de las universidades
        """
        # Ordenar universidades por score
        sorted_universities = sorted(
            self.university_data.items(),
            key=lambda x: x[1]['score'],
            reverse=True
        )[:n]
        
        return [
            {
                'university': name,
                'score': data['score'],
                'ranking': data['ranking'],
                'qs_rank': data['qs_rank']
            }
            for name, data in sorted_universities
        ]
        
    def get_top_programs(self, 
                        program: str,
                        n: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene las top N universidades para un programa.
        
        Args:
            program: Nombre del programa
            n: Número de universidades a retornar
            
        Returns:
            Lista de diccionarios con información de las universidades
        """
        if program not in self.program_data:
            return []
            
        # Ordenar universidades por ranking del programa
        sorted_universities = sorted(
            self.program_data[program].items(),
            key=lambda x: x[1]['ranking']
        )[:n]
        
        return [
            {
                'university': name,
                'ranking': data['ranking'],
                'category': data['category'],
                'metrics': data['metrics']
            }
            for name, data in sorted_universities
        ] 