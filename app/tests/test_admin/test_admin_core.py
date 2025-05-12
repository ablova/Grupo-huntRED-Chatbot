# Ubicación del archivo: /home/pablo/app/tests/test_admin/test_admin_core.py
"""
Pruebas para las clases de administración de modelos core.
"""
import pytest
from unittest.mock import patch, MagicMock
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from app.models import Person, Application, Vacante, BusinessUnit
from app.config.admin_core import (
    PersonAdmin, ApplicationAdmin, VacanteAdmin, BusinessUnitAdmin,
    GamificationProfileAdmin, WorkflowStageAdmin
)


class MockSuperUser:
    """Usuario mock con permisos de superusuario para pruebas admin."""
    def has_perm(self, perm, obj=None):
        return True
        
    def has_module_perms(self, app_label):
        return True
        
    @property
    def is_active(self):
        return True
        
    @property
    def is_staff(self):
        return True
        
    @property
    def is_superuser(self):
        return True
        
    def get_all_permissions(self):
        return set()
        
    def get_group_permissions(self):
        return set()
        
    def get_username(self):
        return "admin"


class AdminCoreTestCase(TestCase):
    """Base para pruebas de clases admin de modelos core."""
    
    def setUp(self):
        """Configurando ambiente de prueba."""
        self.site = AdminSite()
        self.request_factory = RequestFactory()
        self.superuser = MockSuperUser()
        
        # Creando objetos de prueba
        self.business_unit = BusinessUnit.objects.create(
            name="TestBU",
            description="Test Business Unit",
            active=True
        )
        
        self.person = Person.objects.create(
            full_name="Test Person",
            email="test@example.com",
            phone="1234567890",
            status="active"
        )
        
        self.vacante = Vacante.objects.create(
            title="Test Position",
            description="Test job description",
            business_unit=self.business_unit,
            status="active"
        )
        
        self.application = Application.objects.create(
            candidate=self.person,
            vacancy=self.vacante,
            status="applied"
        )


class TestPersonAdmin(AdminCoreTestCase):
    """Pruebas específicas para PersonAdmin."""
    
    def test_list_display_fields(self):
        """Verificando campos de list_display en PersonAdmin."""
        admin_instance = PersonAdmin(Person, self.site)
        expected_fields = [
            'full_name', 'email', 'phone', 'status', 'gamification_score',
            'created_at', 'last_updated'
        ]
        for field in expected_fields:
            self.assertIn(field, admin_instance.list_display)
    
    def test_fieldsets_configuration(self):
        """Verificando configuración de fieldsets en PersonAdmin."""
        admin_instance = PersonAdmin(Person, self.site)
        # Verificando cantidad de secciones
        self.assertEqual(len(admin_instance.fieldsets), 3)
        
        # Verificando nombres de secciones
        section_names = [section[0] for section in admin_instance.fieldsets]
        self.assertIn('Información Personal', section_names)
        self.assertIn('Información Profesional', section_names)
        self.assertIn('Estado y Gamificación', section_names)
    
    def test_readonly_fields(self):
        """Verificando campos de solo lectura en PersonAdmin."""
        admin_instance = PersonAdmin(Person, self.site)
        self.assertIn('created_at', admin_instance.readonly_fields)
        self.assertIn('last_updated', admin_instance.readonly_fields)


class TestApplicationAdmin(AdminCoreTestCase):
    """Pruebas específicas para ApplicationAdmin."""
    
    def test_cv_link_generation(self):
        """Verificando generación de enlace para CV."""
        admin_instance = ApplicationAdmin(Application, self.site)
        
        # Caso sin CV
        result = admin_instance.get_cv_link(self.application)
        self.assertEqual(result, '-')
        
        # Caso con CV (mock)
        with patch.object(self.application, 'cv_file') as mock_file:
            mock_file.url = "/media/test_cv.pdf"
            result = admin_instance.get_cv_link(self.application)
            self.assertIn('href="/media/test_cv.pdf"', result)
            self.assertIn('Ver CV', result)


class TestVacanteAdmin(AdminCoreTestCase):
    """Pruebas específicas para VacanteAdmin."""
    
    def test_applications_count(self):
        """Verificando conteo de aplicaciones para una vacante."""
        admin_instance = VacanteAdmin(Vacante, self.site)
        
        # Verificando conteo correcto
        count = admin_instance.applications_count(self.vacante)
        self.assertEqual(count, 1)
        
        # Creando otra aplicación y verificando actualización
        Application.objects.create(
            candidate=self.person,
            vacancy=self.vacante,
            status="screening"
        )
        
        count = admin_instance.applications_count(self.vacante)
        self.assertEqual(count, 2)
