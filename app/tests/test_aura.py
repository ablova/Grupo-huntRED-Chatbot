"""
Tests unitarios para AURA (Advanced User Relationship Analytics)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

from app.aura.engine import AuraEngine
from app.aura.graph_builder import AuraGraphBuilder
from app.aura.connectors.linkedin_connector import LinkedInConnector
from app.aura.connectors.icloud_connector import iCloudConnector
from app.aura.models.gnn.community_detection import CommunityDetectionModel
from app.aura.models.gnn.influence_analysis import InfluenceAnalysisModel
from app.aura.models.gnn.compatibility_prediction import CompatibilityPredictionModel
from app.aura.analyzer import NetworkAnalyzer
from app.aura.cache import CacheManager
from app.aura.metrics import MetricsCollector

User = get_user_model()


class AuraEngineTestCase(TestCase):
    """Tests para el motor principal de AURA"""
    
    def setUp(self):
        """Configuración inicial"""
        self.aura_engine = AuraEngine()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_aura_engine_initialization(self):
        """Test de inicialización del motor AURA"""
        self.assertIsNotNone(self.aura_engine)
        self.assertIsNotNone(self.aura_engine.graph_builder)
        self.assertIsNotNone(self.aura_engine.connectors)
        self.assertIsNotNone(self.aura_engine.gnn_models)
        self.assertIsNotNone(self.aura_engine.analyzer)
        self.assertIsNotNone(self.aura_engine.cache)
    
    @patch('app.aura.engine.AuraEngine._load_models')
    def test_aura_engine_health_check(self, mock_load_models):
        """Test de verificación de salud del motor"""
        mock_load_models.return_value = True
        
        health_status = self.aura_engine.check_health()
        
        self.assertIn('overall_status', health_status)
        self.assertIn('aura_engine', health_status)
        self.assertIn('integration_layer', health_status)
        self.assertIn('gnn_models', health_status)
        self.assertIn('connectors', health_status)
        self.assertIn('database_connection', health_status)
    
    @patch('app.aura.engine.AuraEngine._analyze_person_internal')
    def test_analyze_person(self, mock_analyze):
        """Test de análisis de persona"""
        mock_analysis = Mock()
        mock_analysis.aura_score = 0.85
        mock_analysis.network_strength = 0.72
        mock_analysis.key_connections = ['conn1', 'conn2']
        mock_analyze.return_value = mock_analysis
        
        result = self.aura_engine.analyze_person(person_id=123)
        
        self.assertEqual(result.aura_score, 0.85)
        self.assertEqual(result.network_strength, 0.72)
        self.assertEqual(len(result.key_connections), 2)
        mock_analyze.assert_called_once_with(123)
    
    @patch('app.aura.engine.AuraEngine._build_network_internal')
    def test_build_network(self, mock_build):
        """Test de construcción de red"""
        mock_network = Mock()
        mock_network.node_count = 100
        mock_network.edge_count = 250
        mock_network.communities = ['comm1', 'comm2', 'comm3']
        mock_build.return_value = mock_network
        
        result = self.aura_engine.build_network(
            people_ids=[1, 2, 3, 4, 5],
            include_external=True,
            depth=2
        )
        
        self.assertEqual(result.node_count, 100)
        self.assertEqual(result.edge_count, 250)
        self.assertEqual(len(result.communities), 3)
        mock_build.assert_called_once_with([1, 2, 3, 4, 5], True, 2)


class AuraGraphBuilderTestCase(TestCase):
    """Tests para el constructor de grafos"""
    
    def setUp(self):
        """Configuración inicial"""
        self.graph_builder = AuraGraphBuilder()
    
    def test_graph_builder_initialization(self):
        """Test de inicialización del constructor de grafos"""
        self.assertIsNotNone(self.graph_builder)
    
    def test_build_network_graph(self):
        """Test de construcción de grafo de red"""
        people_data = [
            {'id': 1, 'name': 'John Doe', 'role': 'Developer'},
            {'id': 2, 'name': 'Jane Smith', 'role': 'Manager'},
            {'id': 3, 'name': 'Bob Johnson', 'role': 'Designer'}
        ]
        
        connections_data = [
            {'from': 1, 'to': 2, 'strength': 0.8},
            {'from': 2, 'to': 3, 'strength': 0.6},
            {'from': 1, 'to': 3, 'strength': 0.4}
        ]
        
        graph = self.graph_builder.build_network_graph(people_data, connections_data)
        
        self.assertIsNotNone(graph)
        self.assertEqual(len(graph.nodes), 3)
        self.assertEqual(len(graph.edges), 3)
    
    def test_add_external_data(self):
        """Test de adición de datos externos"""
        graph = Mock()
        external_data = {
            'linkedin_connections': [{'id': 4, 'name': 'External User'}],
            'icloud_contacts': [{'id': 5, 'name': 'iCloud Contact'}]
        }
        
        result = self.graph_builder.add_external_data(graph, external_data)
        
        self.assertIsNotNone(result)
    
    def test_optimize_graph(self):
        """Test de optimización de grafo"""
        graph = Mock()
        graph.number_of_nodes.return_value = 100
        graph.number_of_edges.return_value = 200
        
        optimized_graph = self.graph_builder.optimize_graph(graph)
        
        self.assertIsNotNone(optimized_graph)


class ConnectorTestCase(TestCase):
    """Tests para conectores externos"""
    
    def setUp(self):
        """Configuración inicial"""
        self.linkedin_connector = LinkedInConnector()
        self.icloud_connector = iCloudConnector()
    
    @patch('app.aura.connectors.linkedin_connector.requests.get')
    def test_linkedin_connector_get_profile(self, mock_get):
        """Test de obtención de perfil de LinkedIn"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'id': 'linkedin_123',
            'name': 'John Doe',
            'headline': 'Software Developer',
            'company': 'Tech Corp'
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        profile_data = self.linkedin_connector.get_profile_data('https://linkedin.com/in/johndoe')
        
        self.assertIsNotNone(profile_data)
        self.assertEqual(profile_data['name'], 'John Doe')
        self.assertEqual(profile_data['headline'], 'Software Developer')
    
    @patch('app.aura.connectors.linkedin_connector.requests.get')
    def test_linkedin_connector_get_connections(self, mock_get):
        """Test de obtención de conexiones de LinkedIn"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'connections': [
                {'id': 'conn1', 'name': 'Connection 1'},
                {'id': 'conn2', 'name': 'Connection 2'}
            ]
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        connections = self.linkedin_connector.get_connections('linkedin_123')
        
        self.assertIsNotNone(connections)
        self.assertEqual(len(connections), 2)
    
    @patch('app.aura.connectors.icloud_connector.icloud.ICloud')
    def test_icloud_connector_get_contacts(self, mock_icloud):
        """Test de obtención de contactos de iCloud"""
        mock_icloud_instance = Mock()
        mock_icloud_instance.contacts.all.return_value = [
            {'name': 'Contact 1', 'email': 'contact1@example.com'},
            {'name': 'Contact 2', 'email': 'contact2@example.com'}
        ]
        mock_icloud.return_value = mock_icloud_instance
        
        contacts = self.icloud_connector.get_contacts()
        
        self.assertIsNotNone(contacts)
        self.assertEqual(len(contacts), 2)


class GNNModelsTestCase(TestCase):
    """Tests para modelos GNN"""
    
    def setUp(self):
        """Configuración inicial"""
        self.community_model = CommunityDetectionModel()
        self.influence_model = InfluenceAnalysisModel()
        self.compatibility_model = CompatibilityPredictionModel()
    
    def test_community_detection_model_initialization(self):
        """Test de inicialización del modelo de detección de comunidades"""
        self.assertIsNotNone(self.community_model)
        self.assertIsNotNone(self.community_model.model)
    
    def test_influence_analysis_model_initialization(self):
        """Test de inicialización del modelo de análisis de influencia"""
        self.assertIsNotNone(self.influence_model)
    
    def test_compatibility_prediction_model_initialization(self):
        """Test de inicialización del modelo de predicción de compatibilidad"""
        self.assertIsNotNone(self.compatibility_model)
    
    @patch('app.aura.models.gnn.community_detection.CommunityDetectionModel.model')
    def test_detect_communities(self, mock_model):
        """Test de detección de comunidades"""
        mock_model.return_value = [0, 0, 1, 1, 2, 2]  # 3 comunidades
        
        graph = Mock()
        graph.number_of_nodes.return_value = 6
        
        communities = self.community_model.detect_communities(graph)
        
        self.assertIsNotNone(communities)
        self.assertEqual(len(set(communities)), 3)
    
    @patch('app.aura.models.gnn.influence_analysis.InfluenceAnalysisModel.model')
    def test_analyze_influence(self, mock_model):
        """Test de análisis de influencia"""
        mock_model.return_value = 0.85
        
        graph = Mock()
        node_id = 1
        
        influence_score = self.influence_model.analyze_influence(graph, node_id)
        
        self.assertIsNotNone(influence_score)
        self.assertGreaterEqual(influence_score, 0)
        self.assertLessEqual(influence_score, 1)
    
    @patch('app.aura.models.gnn.compatibility_prediction.CompatibilityPredictionModel.model')
    def test_predict_compatibility(self, mock_model):
        """Test de predicción de compatibilidad"""
        mock_model.return_value = 0.92
        
        candidate_features = [0.8, 0.7, 0.9, 0.6]
        job_features = [0.9, 0.8, 0.7, 0.8]
        
        compatibility_score = self.compatibility_model.predict_compatibility(
            candidate_features, job_features
        )
        
        self.assertIsNotNone(compatibility_score)
        self.assertGreaterEqual(compatibility_score, 0)
        self.assertLessEqual(compatibility_score, 1)


class NetworkAnalyzerTestCase(TestCase):
    """Tests para el analizador de redes"""
    
    def setUp(self):
        """Configuración inicial"""
        self.analyzer = NetworkAnalyzer()
    
    def test_analyzer_initialization(self):
        """Test de inicialización del analizador"""
        self.assertIsNotNone(self.analyzer)
    
    def test_analyze_network_strength(self):
        """Test de análisis de fuerza de red"""
        graph = Mock()
        graph.number_of_nodes.return_value = 100
        graph.number_of_edges.return_value = 250
        
        strength = self.analyzer.analyze_network_strength(graph)
        
        self.assertIsNotNone(strength)
        self.assertGreaterEqual(strength, 0)
        self.assertLessEqual(strength, 1)
    
    def test_analyze_reputation_score(self):
        """Test de análisis de score de reputación"""
        graph = Mock()
        node_id = 1
        
        reputation = self.analyzer.analyze_reputation_score(graph, node_id)
        
        self.assertIsNotNone(reputation)
        self.assertGreaterEqual(reputation, 0)
        self.assertLessEqual(reputation, 1)
    
    def test_identify_key_connections(self):
        """Test de identificación de conexiones clave"""
        graph = Mock()
        node_id = 1
        
        key_connections = self.analyzer.identify_key_connections(graph, node_id)
        
        self.assertIsNotNone(key_connections)
        self.assertIsInstance(key_connections, list)


class CacheManagerTestCase(TestCase):
    """Tests para el gestor de caché"""
    
    def setUp(self):
        """Configuración inicial"""
        self.cache_manager = CacheManager()
    
    def test_cache_manager_initialization(self):
        """Test de inicialización del gestor de caché"""
        self.assertIsNotNone(self.cache_manager)
    
    @patch('app.aura.cache.CacheManager.redis_client')
    def test_set_get_cache(self, mock_redis):
        """Test de set/get de caché"""
        mock_redis.set.return_value = True
        mock_redis.get.return_value = b'{"test": "data"}'
        
        # Test set
        result = self.cache_manager.set('test_key', {'test': 'data'}, ttl=3600)
        self.assertTrue(result)
        
        # Test get
        data = self.cache_manager.get('test_key')
        self.assertEqual(data, {'test': 'data'})
    
    @patch('app.aura.cache.CacheManager.redis_client')
    def test_clear_cache(self, mock_redis):
        """Test de limpieza de caché"""
        mock_redis.flushdb.return_value = True
        
        result = self.cache_manager.clear_all()
        
        self.assertTrue(result)
        mock_redis.flushdb.assert_called_once()


class MetricsCollectorTestCase(TestCase):
    """Tests para el recolector de métricas"""
    
    def setUp(self):
        """Configuración inicial"""
        self.metrics_collector = MetricsCollector()
    
    def test_metrics_collector_initialization(self):
        """Test de inicialización del recolector de métricas"""
        self.assertIsNotNone(self.metrics_collector)
    
    def test_collect_system_metrics(self):
        """Test de recolección de métricas del sistema"""
        metrics = self.metrics_collector.collect_system_metrics()
        
        self.assertIsNotNone(metrics)
        self.assertIn('total_people_analyzed', metrics)
        self.assertIn('total_connections_analyzed', metrics)
        self.assertIn('communities_detected', metrics)
        self.assertIn('influencers_identified', metrics)
        self.assertIn('validations_performed', metrics)
        self.assertIn('system_uptime', metrics)
        self.assertIn('last_updated', metrics)
    
    def test_collect_performance_metrics(self):
        """Test de recolección de métricas de rendimiento"""
        metrics = self.metrics_collector.collect_performance_metrics()
        
        self.assertIsNotNone(metrics)
        self.assertIn('avg_analysis_time', metrics)
        self.assertIn('avg_network_build_time', metrics)
        self.assertIn('cache_hit_rate', metrics)
        self.assertIn('api_response_time', metrics)


class AuraAPITestCase(APITestCase):
    """Tests para APIs REST de AURA"""
    
    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_health_check_endpoint(self):
        """Test del endpoint de verificación de salud"""
        url = reverse('aura:health')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('overall_status', response.data)
        self.assertIn('aura_engine', response.data)
        self.assertIn('connectors', response.data)
    
    def test_metrics_endpoint(self):
        """Test del endpoint de métricas"""
        url = reverse('aura:metrics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_people_analyzed', response.data)
        self.assertIn('total_connections_analyzed', response.data)
        self.assertIn('communities_detected', response.data)
    
    @patch('app.aura.engine.AuraEngine.analyze_person')
    def test_person_analysis_endpoint(self, mock_analyze):
        """Test del endpoint de análisis de persona"""
        mock_analysis = Mock()
        mock_analysis.aura_score = 0.85
        mock_analysis.network_strength = 0.72
        mock_analysis.key_connections = ['conn1', 'conn2']
        mock_analyze.return_value = mock_analysis
        
        url = reverse('aura:person_analysis', kwargs={'person_id': 123})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('aura_score', response.data)
        self.assertIn('network_insights', response.data)
    
    @patch('app.aura.engine.AuraEngine.build_network')
    def test_network_build_endpoint(self, mock_build):
        """Test del endpoint de construcción de red"""
        mock_network = Mock()
        mock_network.node_count = 100
        mock_network.edge_count = 250
        mock_network.communities = ['comm1', 'comm2']
        mock_build.return_value = mock_network
        
        url = reverse('aura:network_build')
        data = {
            'people_ids': [1, 2, 3, 4, 5],
            'include_external': True,
            'depth': 2
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('node_count', response.data)
        self.assertIn('edge_count', response.data)
        self.assertIn('communities', response.data)
    
    def test_unauthorized_access(self):
        """Test de acceso no autorizado"""
        self.client.force_authenticate(user=None)
        
        url = reverse('aura:health')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuraViewsTestCase(TestCase):
    """Tests para vistas web de AURA"""
    
    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_aura_dashboard_view(self):
        """Test de la vista del dashboard de AURA"""
        url = reverse('ats:aura_dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ats/aura/dashboard.html')
        self.assertIn('page_title', response.context)
        self.assertIn('total_people', response.context)
        self.assertIn('total_candidates', response.context)
        self.assertIn('total_jobs', response.context)
        self.assertIn('aura_metrics', response.context)
        self.assertIn('health_status', response.context)
    
    def test_aura_person_detail_view(self):
        """Test de la vista de detalle de persona"""
        url = reverse('ats:aura_person_detail', kwargs={'person_id': 123})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ats/aura/person_detail.html')
    
    def test_aura_network_visualization_view(self):
        """Test de la vista de visualización de red"""
        url = reverse('ats:aura_network_visualization')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ats/aura/network_visualization.html')
        self.assertIn('network_data', response.context)
        self.assertIn('network_stats', response.context)
        self.assertIn('communities', response.context)


class AuraTasksTestCase(TestCase):
    """Tests para tareas asíncronas de AURA"""
    
    @patch('app.aura.engine.AuraEngine.analyze_person')
    def test_analyze_person_aura_task(self, mock_analyze):
        """Test de tarea de análisis de aura de persona"""
        from app.tasks.aura_tasks import analyze_person_aura
        
        mock_analysis = Mock()
        mock_analysis.aura_score = 0.85
        mock_analyze.return_value = mock_analysis
        
        result = analyze_person_aura.delay(123)
        
        self.assertIsNotNone(result)
        mock_analyze.assert_called_once_with(123)
    
    @patch('app.aura.engine.AuraEngine.build_network')
    def test_build_network_graph_task(self, mock_build):
        """Test de tarea de construcción de grafo de red"""
        from app.tasks.aura_tasks import build_network_graph
        
        mock_network = Mock()
        mock_network.node_count = 100
        mock_build.return_value = mock_network
        
        result = build_network_graph.delay([1, 2, 3, 4, 5])
        
        self.assertIsNotNone(result)
        mock_build.assert_called_once_with([1, 2, 3, 4, 5], True, 2)
    
    @patch('app.aura.engine.AuraEngine.validate_person')
    def test_validate_person_data_task(self, mock_validate):
        """Test de tarea de validación de datos de persona"""
        from app.tasks.aura_tasks import validate_person_data
        
        mock_validation = Mock()
        mock_validation.is_valid = True
        mock_validation.score = 0.95
        mock_validate.return_value = mock_validation
        
        result = validate_person_data.delay(123)
        
        self.assertIsNotNone(result)
        mock_validate.assert_called_once_with(123)
    
    @patch('app.aura.connectors.ConnectorManager.sync_all')
    def test_sync_external_data_task(self, mock_sync):
        """Test de tarea de sincronización de datos externos"""
        from app.tasks.aura_tasks import sync_external_data
        
        mock_sync.return_value = {'linkedin': True, 'icloud': True}
        
        result = sync_external_data.delay()
        
        self.assertIsNotNone(result)
        mock_sync.assert_called_once()


# Fixtures para tests
@pytest.fixture
def sample_people_data():
    """Datos de ejemplo de personas"""
    return [
        {'id': 1, 'name': 'John Doe', 'role': 'Software Developer', 'company': 'Tech Corp'},
        {'id': 2, 'name': 'Jane Smith', 'role': 'Product Manager', 'company': 'Tech Corp'},
        {'id': 3, 'name': 'Bob Johnson', 'role': 'UX Designer', 'company': 'Design Studio'},
        {'id': 4, 'name': 'Alice Brown', 'role': 'Data Scientist', 'company': 'AI Labs'},
        {'id': 5, 'name': 'Charlie Wilson', 'role': 'DevOps Engineer', 'company': 'Cloud Inc'}
    ]


@pytest.fixture
def sample_connections_data():
    """Datos de ejemplo de conexiones"""
    return [
        {'from': 1, 'to': 2, 'strength': 0.8, 'type': 'colleague'},
        {'from': 2, 'to': 3, 'strength': 0.6, 'type': 'project'},
        {'from': 1, 'to': 3, 'strength': 0.4, 'type': 'network'},
        {'from': 3, 'to': 4, 'strength': 0.7, 'type': 'colleague'},
        {'from': 4, 'to': 5, 'strength': 0.9, 'type': 'mentor'},
        {'from': 1, 'to': 5, 'strength': 0.5, 'type': 'network'}
    ]


@pytest.fixture
def sample_network_graph(sample_people_data, sample_connections_data):
    """Grafo de red de ejemplo"""
    graph_builder = AuraGraphBuilder()
    return graph_builder.build_network_graph(sample_people_data, sample_connections_data)


# Tests de integración
class AuraIntegrationTestCase(TestCase):
    """Tests de integración para AURA"""
    
    def setUp(self):
        """Configuración inicial"""
        self.aura_engine = AuraEngine()
        self.user = User.objects.create_user(
            username='integrationuser',
            email='integration@example.com',
            password='testpass123'
        )
    
    def test_full_analysis_workflow(self):
        """Test del flujo completo de análisis"""
        # 1. Construir red
        network = self.aura_engine.build_network(
            people_ids=[1, 2, 3, 4, 5],
            include_external=False,
            depth=1
        )
        
        self.assertIsNotNone(network)
        
        # 2. Analizar persona
        analysis = self.aura_engine.analyze_person(person_id=1)
        
        self.assertIsNotNone(analysis)
        self.assertGreaterEqual(analysis.aura_score, 0)
        self.assertLessEqual(analysis.aura_score, 1)
        
        # 3. Verificar métricas
        metrics = self.aura_engine.get_metrics()
        
        self.assertIsNotNone(metrics)
        self.assertIn('total_people_analyzed', metrics)
    
    def test_cache_integration(self):
        """Test de integración con caché"""
        # Guardar en caché
        self.aura_engine.cache.set('test_key', {'data': 'test'}, ttl=3600)
        
        # Recuperar de caché
        cached_data = self.aura_engine.cache.get('test_key')
        
        self.assertEqual(cached_data, {'data': 'test'})
    
    def test_connector_integration(self):
        """Test de integración con conectores"""
        # Verificar estado de conectores
        connector_status = self.aura_engine.connectors.check_status()
        
        self.assertIsNotNone(connector_status)
        self.assertIn('linkedin', connector_status)
        self.assertIn('icloud', connector_status)


if __name__ == '__main__':
    pytest.main([__file__]) 