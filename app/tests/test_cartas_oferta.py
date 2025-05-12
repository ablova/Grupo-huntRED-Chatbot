from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from app.models import CartaOferta, Candidato, Vacante, Empleador
from datetime import datetime, timedelta
import json

class CartaOfertaTestCase(TestCase):
    def setUp(self):
        # Crear un usuario de prueba
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword',
            email='test@example.com'
        )
        
        # Crear un empleador de prueba
        self.empleador = Empleador.objects.create(
            razon_social='Empresa Test',
            rfc='TEST123456789',
            direccion_fiscal='Calle Test 123'
        )
        
        # Crear una vacante de prueba
        self.vacante = Vacante.objects.create(
            titulo='Vacante de Prueba',
            descripcion='Descripción de prueba',
            empleador=self.empleador,
            ubicacion='Ciudad de México',
            modalidad='Presencial'
        )
        
        # Crear un candidato de prueba
        self.candidato = Candidato.objects.create(
            nombre='Juan',
            apellido_paterno='Pérez',
            email='juan@example.com',
            telefono='5555555555'
        )
        
        # Crear una carta de oferta de prueba
        self.carta = CartaOferta.objects.create(
            candidato=self.candidato,
            vacante=self.vacante,
            salario=100000,
            periodo_prueba=3,
            beneficios='Beneficios de prueba',
            fecha_inicio=datetime.now() + timedelta(days=7),
            fecha_expiracion=datetime.now() + timedelta(days=30),
            canal_envio='Email'
        )
        
        # Cliente para hacer requests
        self.client = Client()
        self.client.login(username='testuser', password='testpassword')

    def test_crear_carta(self):
        """Test para crear una nueva carta de oferta"""
        url = reverse('crear_carta')
        data = {
            'candidato': self.candidato.id,
            'vacante': self.vacante.id,
            'salario': 120000,
            'periodo_prueba': 6,
            'beneficios': 'Beneficios actualizados',
            'fecha_inicio': (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d'),
            'fecha_expiracion': (datetime.now() + timedelta(days=45)).strftime('%Y-%m-%d'),
            'canal_envio': 'Email'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(CartaOferta.objects.filter(candidato=self.candidato).count() > 1)

    def test_ver_carta(self):
        """Test para ver una carta de oferta"""
        url = reverse('ver_carta', args=[self.carta.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'carta_oferta.html')

    def test_marcar_como_firmada(self):
        """Test para marcar una carta como firmada"""
        url = reverse('marcar_como_firmada', args=[self.carta.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.carta.refresh_from_db()
        self.assertEqual(self.carta.estado, CartaOferta.FIRMADA)

    def test_reenviar_carta(self):
        """Test para reenviar una carta"""
        url = reverse('reenviar_carta', args=[self.carta.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.carta.refresh_from_db()
        self.assertTrue(self.carta.fecha_envio)

    def test_preview_carta(self):
        """Test para ver el preview de una carta"""
        url = reverse('preview_carta')
        data = {
            'beneficios': 'Beneficios de prueba'
        }
        response = self.client.get(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'preview_carta.html')

    def test_listar_cartas_pendientes(self):
        """Test para listar cartas pendientes"""
        url = reverse('cartas_pendientes')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'gestion_cartas_oferta.html')
        self.assertContains(response, 'Cartas de Oferta Pendientes')

    def test_filtrar_cartas(self):
        """Test para filtrar cartas por estado"""
        url = reverse('cartas_pendientes')
        data = {
            'estado': CartaOferta.PENDIENTE
        }
        response = self.client.get(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Estado: Pendiente')
