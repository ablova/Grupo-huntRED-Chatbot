# Ubicación del archivo: /home/pablo/app/tests/test_admin/test_admin_scraping.py
"""
Pruebas para las clases de administración de modelos de scraping.
"""
import pytest
from unittest.mock import patch, MagicMock
from django.test import TestCase, RequestFactory
from django.contrib.admin.sites import AdminSite
from django.contrib.admin.models import LogEntry
from django.contrib import messages
from django.http import HttpRequest
from django.urls import reverse
from django.http import FileResponse
from io import BytesIO
import base64

from app.models import DominioScraping, RegistroScraping, ReporteScraping, BusinessUnit
from app.ats.config.admin_scraping import (
    DominioScrapingAdmin,
    RegistroScrapingAdmin,
    ReporteScrapingAdmin
)


class AdminScrapingTestCase(TestCase):
    """Base para pruebas de clases admin de modelos de scraping."""
    
    def setUp(self):
        """Configurando ambiente de prueba."""
        self.site = AdminSite()
        self.request_factory = RequestFactory()
        
        # Creando objetos de prueba
        self.business_unit = BusinessUnit.objects.create(
            name="TestBU",
            description="Test Business Unit",
            active=True
        )
        
        self.dominio = DominioScraping.objects.create(
            empresa="TestCompany",
            dominio="test-company.com",
            plataforma="linkedin",
            estado="active",
            verificado=True,
            email_scraping_enabled=True
        )
        
        self.registro = RegistroScraping.objects.create(
            dominio=self.dominio,
            estado="completed",
            fecha_inicio="2025-05-01T10:00:00Z",
            fecha_fin="2025-05-01T10:30:00Z",
            vacantes_encontradas=5
        )
        
        self.reporte = ReporteScraping.objects.create(
            business_unit=self.business_unit,
            fecha="2025-05-01",
            vacantes_creadas=10,
            exitosos=8,
            fallidos=1,
            parciales=1
        )
        
        # Configurando request mock
        self.request = HttpRequest()
        self.request.user = MagicMock()
        
        # Mock para mensajes
        self.messages = MagicMock()
        self.request._messages = self.messages


class TestDominioScrapingAdmin(AdminScrapingTestCase):
    """Pruebas específicas para DominioScrapingAdmin."""
    
    def test_list_display_fields(self):
        """Verificando campos de list_display en DominioScrapingAdmin."""
        admin_instance = DominioScrapingAdmin(DominioScraping, self.site)
        expected_fields = [
            'id', 'empresa', 'plataforma', 'verificado', 
            'email_scraping_enabled', 'valid_senders', 
            'ultima_verificacion', 'estado'
        ]
        for field in expected_fields:
            self.assertIn(field, admin_instance.list_display)
    
    @patch('django.contrib.messages.add_message')
    @patch('django.urls.reverse')
    def test_ejecutar_scraping_action(self, mock_reverse, mock_add_message):
        """Verificando acción para ejecutar scraping."""
        admin_instance = DominioScrapingAdmin(DominioScraping, self.site)
        queryset = DominioScraping.objects.filter(id=self.dominio.id)
        
        # Ejecutando acción
        admin_instance.ejecutar_scraping_action(self.request, queryset)
        
        # Verificando que el estado se actualizó
        self.dominio.refresh_from_db()
        self.assertEqual(self.dominio.estado, 'processing')
        
        # Verificando mensaje
        mock_add_message.assert_called_once()
    
    def test_custom_actions(self):
        """Verificando que las acciones personalizadas están registradas."""
        admin_instance = DominioScrapingAdmin(DominioScraping, self.site)
        self.assertIn('marcar_como_definido', admin_instance.actions)
        self.assertIn('ejecutar_scraping_action', admin_instance.actions)
        self.assertIn('desactivar_dominios_invalidos', admin_instance.actions)


class TestReporteScrapingAdmin(AdminScrapingTestCase):
    """Pruebas específicas para ReporteScrapingAdmin."""
    
    @patch('reportlab.pdfgen.canvas.Canvas')
    def test_generar_reporte_pdf(self, mock_canvas):
        """Verificando generación de reporte PDF."""
        admin_instance = ReporteScrapingAdmin(ReporteScraping, self.site)
        queryset = ReporteScraping.objects.filter(id=self.reporte.id)
        
        # Configurando mocks
        mock_canvas_instance = MagicMock()
        mock_canvas.return_value = mock_canvas_instance
        
        # Ejecutando acción
        with patch('io.BytesIO') as mock_bytesio:
            mock_buffer = MagicMock()
            mock_bytesio.return_value = mock_buffer
            
            response = admin_instance.generar_reporte_pdf(self.request, queryset)
            
            # Verificando que se dibujaron elementos en el PDF
            mock_canvas_instance.drawString.assert_called()
            mock_canvas_instance.line.assert_called()
            mock_canvas_instance.save.assert_called_once()
            
            # Verificando el tipo de respuesta
            self.assertIsInstance(response, FileResponse)
    
    def test_list_display_fields(self):
        """Verificando campos de list_display en ReporteScrapingAdmin."""
        admin_instance = ReporteScrapingAdmin(ReporteScraping, self.site)
        expected_fields = [
            'business_unit', 'fecha', 'vacantes_creadas', 
            'exitosos', 'fallidos', 'parciales'
        ]
        for field in expected_fields:
            self.assertIn(field, admin_instance.list_display)
