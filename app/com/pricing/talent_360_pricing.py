# /home/pablo/app/com/pricing/talent_360_pricing.py
"""
Módulo para el pricing del servicio de Análisis de Talento 360°.

Este módulo proporciona funcionalidades para calcular precios del servicio de
Análisis de Talento 360° con estructura de descuentos por volumen,
registrar el servicio como addon en el sistema, y generar propuestas personalizadas.
"""

from decimal import Decimal, ROUND_HALF_UP
from django.db import models
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class Talent360Pricing:
    """
    Clase para calcular precios del Análisis de Talento 360° con estructura escalonada.
    
    La estructura de precios por usuario se basa en volumen con descuentos progresivos:
    - 1-11 usuarios: Precio base ($900 MXN por usuario)
    - 12-99 usuarios: 11% de descuento
    - 100-199 usuarios: 22% de descuento
    - 200+ usuarios: 33% de descuento
    """
    
    # Precio base y configuración de descuentos
    BASE_PRICE = Decimal('900.00')  # Precio base por usuario
    
    # Definir los niveles de descuento (con precio calculado para referencia)
    DISCOUNT_TIERS = [
        {'min_users': 1, 'max_users': 11, 'discount_pct': Decimal('0.00')},   # $900 por usuario
        {'min_users': 12, 'max_users': 99, 'discount_pct': Decimal('0.11')},   # $801 por usuario
        {'min_users': 100, 'max_users': 199, 'discount_pct': Decimal('0.22')}, # $702 por usuario
        {'min_users': 200, 'max_users': float('inf'), 'discount_pct': Decimal('0.33')} # $603 por usuario
    ]
    
    # IVA estándar en México
    IVA_RATE = Decimal('0.16')
    
    @classmethod
    def get_price_per_user(cls, user_count: int) -> Decimal:
        """
        Determina el precio por usuario basado en el número total de usuarios.
        
        Args:
            user_count: Número total de usuarios
            
        Returns:
            Decimal: Precio por usuario con descuento aplicado
        """
        discount = Decimal('0.00')
        
        # Encontrar el nivel de descuento aplicable
        for tier in cls.DISCOUNT_TIERS:
            if tier['min_users'] <= user_count <= tier['max_users']:
                discount = tier['discount_pct']
                break
                
        # Calcular precio con descuento
        price_per_user = cls.BASE_PRICE * (1 - discount)
        
        # Redondear a 2 decimales
        return price_per_user.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    @classmethod
    def calculate_total(cls, user_count: int, include_iva: bool = True) -> dict:
        """
        Calcula el precio total del servicio de Análisis de Talento 360°.
        
        Args:
            user_count: Número total de usuarios
            include_iva: Si se debe incluir el IVA en el cálculo
            
        Returns:
            dict: Detalle del cálculo incluyendo precio por usuario, subtotal, IVA y total
        """
        price_per_user = cls.get_price_per_user(user_count)
        subtotal = price_per_user * user_count
        
        # Calcular IVA si aplica
        iva = Decimal('0.00')
        if include_iva:
            iva = subtotal * cls.IVA_RATE
            
        # Calcular total
        total = subtotal + iva
        
        # Encontrar el nivel de descuento aplicado
        discount_pct = Decimal('0.00')
        for tier in cls.DISCOUNT_TIERS:
            if tier['min_users'] <= user_count <= tier['max_users']:
                discount_pct = tier['discount_pct']
                break
        
        # Generar objeto de respuesta
        return {
            'user_count': user_count,
            'base_price': cls.BASE_PRICE,
            'discount_percentage': discount_pct * 100,  # Convertir a porcentaje para mostrar
            'price_per_user': price_per_user,
            'subtotal': subtotal,
            'iva': iva,
            'total': total,
            'tiers': cls.DISCOUNT_TIERS,
            'currency': 'MXN'
        }
        
    @classmethod
    def generate_proposal_data(cls, company_name: str, user_count: int, 
                              contact_name: str = None, contact_email: str = None, 
                              contact_phone: str = None) -> dict:
        """
        Genera los datos necesarios para una propuesta de Análisis de Talento 360°.
        
        Args:
            company_name: Nombre de la empresa cliente
            user_count: Número de usuarios para el servicio
            contact_name: Nombre del contacto (opcional)
            contact_email: Email del contacto (opcional)
            contact_phone: Teléfono del contacto (opcional)
            
        Returns:
            dict: Datos completos para generar la propuesta
        """
        # Calcular pricing
        pricing_data = cls.calculate_total(user_count=user_count, include_iva=True)
        
        # Construir contexto para la plantilla
        proposal_data = {
            'company': {
                'name': company_name,
                'contact': {
                    'name': contact_name,
                    'email': contact_email,
                    'phone': contact_phone
                }
            },
            'service': {
                'name': 'Análisis de Talento 360°',
                'description': 'Evaluación integral de competencias y habilidades para optimizar el talento organizacional',
                'provider': 'huntRED® Solutions',
                'features': [
                    'Evaluación de competencias técnicas y blandas',
                    'Análisis de alineación con valores organizacionales',
                    'Identificación de áreas de oportunidad y desarrollo',
                    'Recomendaciones personalizadas de desarrollo',
                    'Dashboard interactivo para seguimiento de KPIs',
                    'Reportes comparativos por equipos y departamentos'
                ],
                'benefits': [
                    'Optimización de procesos de selección y retención',
                    'Reducción de costos de rotación',
                    'Mejora en la productividad y clima organizacional',
                    'Alineación del talento con la estrategia de negocio',
                    'Desarrollo de planes de carrera personalizados'
                ],
                'process': [
                    {'step': 1, 'name': 'Diagnóstico', 'description': 'Análisis de necesidades y objetivos organizacionales'},
                    {'step': 2, 'name': 'Implementación', 'description': 'Lanzamiento y seguimiento del proceso de evaluación'},
                    {'step': 3, 'name': 'Análisis', 'description': 'Procesamiento y análisis de resultados'},
                    {'step': 4, 'name': 'Reporte', 'description': 'Generación de informes y recomendaciones'},
                    {'step': 5, 'name': 'Seguimiento', 'description': 'Plan de acción y monitoreo de resultados'}
                ]
            },
            'pricing': pricing_data,
            'date': timezone.now().strftime('%d/%m/%Y'),
            'valid_until': (timezone.now() + timezone.timedelta(days=30)).strftime('%d/%m/%Y'),
            'logo': {
                'path': '/static/img/huntRED-logo.png',
                'alt': 'Grupo huntRED®'
            },
            'values': [
                {'name': 'Apoyo', 'description': 'Acompañamiento continuo para potenciar el talento de tu equipo'},
                {'name': 'Solidaridad', 'description': 'Compromiso con el desarrollo sostenible del capital humano'},
                {'name': 'Sinergia', 'description': 'Colaboración estratégica para multiplicar resultados'}
            ]
        }
        
        return proposal_data


class Talent360AddonService(models.Model):
    """
    Modelo para el servicio de Análisis de Talento 360° como addon.
    """
    name = models.CharField(max_length=100, default='Análisis de Talento 360°')
    description = models.TextField(default='Evaluación integral de competencias y habilidades para optimizar el talento organizacional')
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('900.00'))
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Servicio de Análisis de Talento 360°'
        verbose_name_plural = 'Servicios de Análisis de Talento 360°'

    def __str__(self):
        return self.name


def register_talent_360_addon():
    """
    Registra el servicio de Análisis de Talento 360° en el sistema de addons.
    """
    try:
        from app.com.pricing.utils import register_addon_service
        
        register_addon_service(
            addon_id='talent_360_analysis',
            name='Análisis de Talento 360°',
            description='Evaluación integral de competencias y habilidades para optimizar el talento organizacional',
            model_class=Talent360AddonService,
            pricing_class=Talent360Pricing,
            template_name='proposals/talent_360_proposal.html'
        )
        
        logger.info("Servicio de Análisis de Talento 360° registrado exitosamente en el sistema de addons.")
        return True
        
    except ImportError as e:
        logger.error(f"Error de importación al registrar el servicio de Análisis de Talento 360°: {e}")
        return False
    except Exception as e:
        logger.error(f"Error al registrar el servicio de Análisis de Talento 360°: {e}")
        return False
