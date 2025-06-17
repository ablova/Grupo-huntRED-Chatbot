import aiohttp
from typing import Dict, Any
from django.conf import settings

class UniversityRankingsAnalyzer:
    """
    Analizador de rankings universitarios usando QS World University Rankings API.
    """
    def __init__(self):
        self.api_key = settings.QS_UNIVERSITY_RANKINGS_API_KEY
        self.base_url = "https://api.gugudata.io/v1/metadata/global-university-ranking"
        
    async def get_university_ranking(self, university_name: str) -> Dict[str, Any]:
        """
        Obtiene ranking de una universidad específica.
        """
        async with aiohttp.ClientSession() as session:
            params = {
                'appkey': self.api_key,
                'name': university_name
            }
            
            async with session.get(self.base_url, params=params) as response:
                response.raise_for_status()
                return await response.json()
        
    async def analyze_university_metrics(self, university_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analiza métricas de la universidad.
        """
        return {
            'academic_reputation': university_data.get('academicReputationScore'),
            'employer_reputation': university_data.get('employerReputationScore'),
            'faculty_student_ratio': university_data.get('facultyStudentRatioScore'),
            'international_student_ratio': university_data.get('internationalStudentRatioScore'),
            'overall_ranking': university_data.get('rank'),
            'sustainability': university_data.get('sustainabilityScore'),
            'research_network': university_data.get('internationalResearchNetworkScore')
        } 