# Ubicación del archivo: /home/pablo/app/tests/test_admin/test_admin_registry.py
"""
Pruebas para el sistema centralizado de registro de administradores.
"""
import pytest
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.apps import apps
from app.config.admin_registry import initialize_admin, ADMIN_CLASS_MAPPING


class TestAdminRegistry(TestCase):
    """Pruebas para el sistema centralizado de registro de administradores."""

    def setUp(self):
        """Configurando ambiente de prueba."""
        self.site = AdminSite()
        self.original_registry = admin.site._registry.copy()

    def tearDown(self):
        """Limpiando cambios después de las pruebas."""
        admin.site._registry = self.original_registry

    @patch('app.config.admin_registry.admin')
    def test_initialize_admin_registers_all_models(self, mock_admin):
        """Verificando que initialize_admin registra todos los modelos correctamente."""
        # Preparando mock
        mock_admin.site = MagicMock()
        mock_admin.sites.NotRegistered = admin.sites.NotRegistered

        # Ejecutando función a probar
        initialize_admin(force_register=True)

        # Verificando que todos los modelos del mapeo fueron registrados
        for model, admin_class in ADMIN_CLASS_MAPPING.items():
            mock_admin.site.register.assert_any_call(model, admin_class)

    @patch('importlib.import_module')
    def test_initialize_admin_imports_all_modules(self, mock_import):
        """Verificando que initialize_admin importa todos los módulos de admin especificados."""
        from app.config.admin_registry import ADMIN_MODULES, _initialize_admin_modules

        # Ejecutando función a probar
        _initialize_admin_modules()

        # Verificando que todos los módulos fueron importados
        for module in ADMIN_MODULES:
            mock_import.assert_any_call(module)

    def test_admin_class_mapping_contains_all_required_models(self):
        """Verificando que ADMIN_CLASS_MAPPING contiene todos los modelos requeridos."""
        # Lista de modelos que deberían estar mapeados
        required_models = [
            'Person', 'Application', 'Vacante', 'BusinessUnit',
            'Configuracion', 'EnhancedNetworkGamificationProfile',
            'GamificationAchievement', 'GamificationBadge', 'GamificationEvent',
            'WorkflowStage', 'ChatState', 'DominioScraping',
            'RegistroScraping', 'ReporteScraping'
        ]

        # Obteniendo modelos del mapeo
        mapped_models = [model.__name__ for model in ADMIN_CLASS_MAPPING.keys()]

        # Verificando que todos los modelos requeridos están mapeados
        for model_name in required_models:
            assert model_name in mapped_models, f"Modelo {model_name} no está en ADMIN_CLASS_MAPPING"

    def test_admin_classes_are_properly_configured(self):
        """Verificando que las clases admin están configuradas correctamente."""
        for model, admin_class in ADMIN_CLASS_MAPPING.items():
            admin_instance = admin_class(model, self.site)
            
            # Verificando que tiene atributos básicos
            assert hasattr(admin_instance, 'list_display'), f"{admin_class.__name__} no tiene list_display"
            
            # Si aplica el modelo base, debe tener los métodos
            if 'BaseModelAdmin' in admin_class.__mro__[1].__name__:
                assert hasattr(admin_instance, 'get_readonly_fields'), f"{admin_class.__name__} no tiene get_readonly_fields"
