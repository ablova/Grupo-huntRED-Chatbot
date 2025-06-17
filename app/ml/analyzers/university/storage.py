from typing import Dict, Any
from datetime import datetime
from app.models.university import University, UniversityCampus

class UniversityPreferenceStorage:
    """
    Almacenamiento de preferencias universitarias.
    """
    async def store_for_analysis(self, data: Dict[str, Any]) -> None:
        """
        Almacena datos para análisis futuro.
        """
        # TODO: Implementar almacenamiento en base de datos
        # Por ahora solo imprimimos los datos
        print(f"Storing university analysis data: {data}")
        
    async def get_university_data(self, university_name: str) -> Dict[str, Any]:
        """
        Obtiene datos de una universidad.
        """
        try:
            university = await University.objects.filter(normalized_name=university_name).first()
            if university:
                return {
                    'name': university.name,
                    'normalized_name': university.normalized_name,
                    'abbreviations': university.abbreviations,
                    'country': university.country,
                    'city': university.city,
                    'ranking_data': university.ranking_data
                }
        except Exception as e:
            print(f"Error getting university data: {e}")
        return {} 