import pytest
from unittest.mock import Mock, patch
from .analyzer import UniversityAnalyzer
from .rankings import UniversityRankingsAnalyzer
from .storage import UniversityPreferenceStorage

@pytest.fixture
def university_analyzer():
    return UniversityAnalyzer()

@pytest.fixture
def sample_job_description():
    return """
    Se busca Abogado Fiscalista con experiencia en derecho corporativo.
    Preferencia por egresados de la Universidad Panamericana o ITAM.
    Conocimientos en derecho fiscal y corporativo.
    """

@pytest.mark.asyncio
async def test_extract_universities(university_analyzer, sample_job_description):
    result = await university_analyzer.analyze(sample_job_description)
    
    assert 'universities' in result
    assert len(result['universities']) > 0
    assert any(u['normalized'] == 'Universidad Panamericana' for u in result['universities'])
    assert any(u['normalized'] == 'Instituto Tecnológico Autónomo de México' for u in result['universities'])

@pytest.mark.asyncio
async def test_analyze_rankings(university_analyzer):
    universities = [
        {'normalized': 'Universidad Panamericana'},
        {'normalized': 'Instituto Tecnológico Autónomo de México'}
    ]
    
    with patch.object(UniversityRankingsAnalyzer, 'get_university_ranking') as mock_get_ranking:
        mock_get_ranking.return_value = {
            'academicReputationScore': 85,
            'employerReputationScore': 90,
            'facultyStudentRatioScore': 80,
            'internationalStudentRatioScore': 75,
            'rank': 100,
            'sustainabilityScore': 85,
            'internationalResearchNetworkScore': 80
        }
        
        result = await university_analyzer._analyze_rankings(universities)
        
        assert len(result) == 2
        assert 'Universidad Panamericana' in result
        assert 'Instituto Tecnológico Autónomo de México' in result

@pytest.mark.asyncio
async def test_analyze_preferences(university_analyzer, sample_job_description):
    result = await university_analyzer._analyze_preferences(sample_job_description)
    
    assert 'explicit_preferences' in result
    assert 'implicit_preferences' in result
    assert 'confidence' in result
    assert isinstance(result['confidence'], float)

@pytest.mark.asyncio
async def test_store_for_analysis(university_analyzer):
    data = {
        'universities': [
            {'normalized': 'Universidad Panamericana'},
            {'normalized': 'Instituto Tecnológico Autónomo de México'}
        ],
        'rankings': {},
        'preferences': {
            'explicit_preferences': [],
            'implicit_preferences': [],
            'confidence': 0.0
        },
        'metadata': {
            'timestamp': '2024-03-20T12:00:00',
            'status': 'analyzed'
        }
    }
    
    with patch.object(UniversityPreferenceStorage, 'store_for_analysis') as mock_store:
        await university_analyzer.storage.store_for_analysis(data)
        mock_store.assert_called_once_with(data) 