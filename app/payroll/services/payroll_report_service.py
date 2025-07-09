"""
Servicio para generación y envío de reportes de nómina multi-país
"""
import logging
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from django.urls import reverse
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings

from ..models import (
    PayrollCompany, 
    PayrollSubsidiary, 
    GlobalPayrollPeriod, 
    PayrollPeriod,
    FiscalSyncConfiguration,
    FiscalSyncHistory
)
from app.ats.integrations.services import EmailService

logger = logging.getLogger(__name__)

class PayrollEmailReportService:
    """
    Servicio para generación y envío de reportes de nómina por correo electrónico.
    Utiliza el template HTML para crear reportes visuales completos.
    """
    
    def __init__(self, company: PayrollCompany):
        """
        Inicializa el servicio con la empresa global
        """
        self.company = company
        self.email_service = None
        self._initialize_email_service()
    
    def _initialize_email_service(self):
        """Inicializa el servicio de correo con la configuración de la empresa"""
        if not self.company.email_config:
            logger.warning(f"No email configuration found for company {self.company.name}")
            return
            
        config = self.company.email_config
        self.email_service = EmailService(
            smtp_host=config.get('smtp_host', 'smtp.gmail.com'),
            smtp_port=config.get('smtp_port', 587),
            username=config.get('username', ''),
            password=config.get('password', ''),
            from_email=config.get('from_email', '')
        )
    
    async def send_payroll_report(
        self, 
        to_email: Union[str, List[str]], 
        period_id: str = None,
        country_code: str = None,
        include_charts: bool = True,
        include_pdf: bool = False,
        cc: List[str] = None,
        bcc: List[str] = None
    ) -> Dict[str, Any]:
        """
        Genera y envía un reporte de nómina por correo electrónico
        
        Args:
            to_email: Dirección(es) de correo de destinatario(s)
            period_id: ID del periodo (usa el último si no se especifica)
            country_code: Código de país para filtrar datos (None = reporte global)
            include_charts: Si se deben incluir gráficos en el correo
            include_pdf: Si se debe adjuntar PDF con el reporte completo
            cc: Lista de destinatarios en copia
            bcc: Lista de destinatarios en copia oculta
            
        Returns:
            Dict con resultado del envío
        """
        # Validar que tengamos servicio de correo configurado
        if not self.email_service:
            return {
                "success": False, 
                "error": "Email service not configured for this company"
            }
            
        # Obtener el periodo solicitado o el último periodo global
        period = await self._get_period(period_id)
        if not period:
            return {
                "success": False, 
                "error": "No payroll period found"
            }
            
        # Generar datos del reporte
        report_data = await self._generate_report_data(period, country_code)
        
        # Generar gráficos si se solicitaron
        chart_url = None
        if include_charts:
            chart_url = await self._generate_charts(period, country_code)
        
        # Preparar contexto para la plantilla
        template_context = {
            'company': {
                'name': self.company.name,
                'logo_url': self.company.logo_url
            },
            'period': {
                'name': period.name,
                'start_date': period.start_date,
                'end_date': period.end_date
            },
            'global_data': report_data['global'],
            'countries_data': report_data['countries'],
            'chart_url': chart_url,
            'dashboard_url': self._get_dashboard_url(period.id),
            'current_datetime': timezone.now(),
            'current_year': timezone.now().year
        }
        
        # Renderizar plantilla HTML
        subject = f"Reporte de Nómina Multi-País - {period.name}"
        body_html = render_to_string('payroll/multicountry_report.html', template_context)
        
        # Preparar adjuntos si se solicitaron
        attachments = None
        if include_pdf:
            pdf_data = await self._generate_pdf_report(template_context)
            if pdf_data:
                attachments = [{
                    'filename': f'payroll_report_{period.name}.pdf',
                    'content': pdf_data,
                    'mimetype': 'application/pdf'
                }]
        
        # Convertir correo único a lista para procesamiento uniforme
        to_emails = [to_email] if isinstance(to_email, str) else to_email
        
        # Enviar correo
        try:
            if len(to_emails) == 1:
                # Envío a un solo destinatario
                success = await self.email_service.send_email(
                    to_email=to_emails[0],
                    subject=subject,
                    body=body_html,
                    attachment=attachments[0]['content'] if attachments else None
                )
                return {"success": success}
            else:
                # Envío masivo
                recipients = [{"email": email} for email in to_emails]
                results = await self.email_service.send_bulk_emails(
                    recipients=recipients,
                    subject=subject,
                    body=body_html,
                    attachments=attachments
                )
                return results
                
        except Exception as e:
            logger.error(f"Error sending payroll report: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _get_period(self, period_id: str = None) -> Optional[GlobalPayrollPeriod]:
        """
        Obtiene el periodo solicitado o el último periodo global
        """
        try:
            if period_id:
                return GlobalPayrollPeriod.objects.get(id=period_id)
            else:
                # Obtener el último periodo
                return GlobalPayrollPeriod.objects.filter(
                    company=self.company
                ).order_by('-end_date').first()
        except GlobalPayrollPeriod.DoesNotExist:
            logger.warning(f"Period {period_id} not found for company {self.company.name}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving period: {str(e)}")
            return None
    
    async def _generate_report_data(
        self, 
        period: GlobalPayrollPeriod,
        country_code: str = None
    ) -> Dict[str, Any]:
        """
        Genera los datos para el reporte de nómina
        """
        # Datos globales para todas las subsidiarias
        global_data = {
            'total_employees': 0,
            'total_gross': 0,
            'total_net': 0,
            'total_taxes': 0,
            'previous_gross': 0,
            'gross_diff': 0,
            'gross_trend': 0,
            'employee_trend': 0,
            'net_ratio': 0,
            'tax_rate': 0,
            'avg_tax_rate': 0,
            'currency_symbol': self.company.default_currency_symbol or '$'
        }
        
        countries_data = []
        
        # Si se especificó un país, filtrar subsidiarias
        subsidiaries = PayrollSubsidiary.objects.filter(company=self.company)
        if country_code:
            subsidiaries = subsidiaries.filter(country_code=country_code)
        
        # Recopilar datos de cada subsidiaria
        for subsidiary in subsidiaries:
            # Obtener datos de nómina para el período actual
            payroll_period = PayrollPeriod.objects.filter(
                global_period=period,
                subsidiary=subsidiary
            ).first()
            
            if not payroll_period:
                continue
                
            # Calcular datos para esta subsidiaria
            employees = payroll_period.employee_count or 0
            gross = payroll_period.total_gross or 0
            net = payroll_period.total_net or 0
            taxes = payroll_period.total_taxes or 0
            tax_rate = 0 if gross == 0 else (taxes / gross) * 100
            
            # Añadir a datos globales
            global_data['total_employees'] += employees
            global_data['total_gross'] += gross
            global_data['total_net'] += net
            global_data['total_taxes'] += taxes
            
            # Buscar período anterior para comparación
            previous_period = PayrollPeriod.objects.filter(
                subsidiary=subsidiary,
                end_date__lt=payroll_period.start_date
            ).order_by('-end_date').first()
            
            previous_gross = 0
            previous_employees = 0
            if previous_period:
                previous_gross = previous_period.total_gross or 0
                previous_employees = previous_period.employee_count or 0
                global_data['previous_gross'] += previous_gross
            
            # Calcular tendencias para esta subsidiaria
            gross_trend = 0
            employee_trend = 0
            if previous_gross > 0:
                gross_trend = ((gross - previous_gross) / previous_gross) * 100
            if previous_employees > 0:
                employee_trend = ((employees - previous_employees) / previous_employees) * 100
            
            # Estado de la subsidiaria basado en tendencias
            status = 'ok'
            status_text = 'Normal'
            if gross_trend < -5:
                status = 'warning'
                status_text = 'Revisar'
            if gross_trend < -15:
                status = 'danger'
                status_text = 'Atención'
            
            # Añadir datos de esta subsidiaria al listado de países
            countries_data.append({
                'name': subsidiary.name,
                'country_code': subsidiary.country_code,
                'employees': employees,
                'gross': gross,
                'net': net,
                'taxes': taxes,
                'gross_global': gross,  # Ya convertido a moneda global
                'net_global': net,      # Ya convertido a moneda global
                'taxes_global': taxes,  # Ya convertido a moneda global
                'tax_rate': tax_rate,
                'gross_trend': gross_trend,
                'employee_trend': employee_trend,
                'status': status,
                'status_text': status_text,
                'currency': subsidiary.currency,
                'currency_symbol': subsidiary.currency_symbol
            })
        
        # Finalizar cálculos globales
        if global_data['total_gross'] > 0:
            global_data['net_ratio'] = (global_data['total_net'] / global_data['total_gross']) * 100
            global_data['tax_rate'] = (global_data['total_taxes'] / global_data['total_gross']) * 100
        
        if global_data['previous_gross'] > 0:
            global_data['gross_diff'] = global_data['total_gross'] - global_data['previous_gross']
            global_data['gross_trend'] = (global_data['gross_diff'] / global_data['previous_gross']) * 100
        
        # Obtener tendencia de empleados a nivel global
        previous_global_period = GlobalPayrollPeriod.objects.filter(
            company=self.company,
            end_date__lt=period.start_date
        ).order_by('-end_date').first()
        
        if previous_global_period:
            previous_employee_count = previous_global_period.total_employees or 0
            if previous_employee_count > 0:
                global_data['employee_trend'] = (
                    (global_data['total_employees'] - previous_employee_count) / 
                    previous_employee_count
                ) * 100
        
        # Ordenar países por número de empleados
        countries_data.sort(key=lambda x: x['employees'], reverse=True)
        
        return {
            'global': global_data,
            'countries': countries_data
        }
    
    async def _generate_charts(
        self, 
        period: GlobalPayrollPeriod,
        country_code: str = None
    ) -> Optional[str]:
        """
        Genera gráficos para el reporte y devuelve URL a la imagen
        """
        # Implementación simplificada - en un sistema real, esto generaría 
        # gráficos dinámicamente y almacenaría la URL
        
        # Para esta demo, retornamos None indicando que no hay gráficos
        # En un sistema real, aquí se llamaría a un servicio de generación de gráficos
        return None
    
    async def _generate_pdf_report(self, template_context: Dict) -> Optional[bytes]:
        """
        Genera un PDF del reporte completo
        """
        # Implementación simplificada - en un sistema real, esto generaría 
        # un PDF con los mismos datos del reporte HTML
        
        # Para esta demo, retornamos None indicando que no hay PDF
        # En un sistema real, aquí se usaría una librería como WeasyPrint para generar PDF
        return None
    
    def _get_dashboard_url(self, period_id: str) -> str:
        """
        Obtiene la URL al dashboard para el periodo especificado
        """
        try:
            base_url = settings.BASE_URL
            dashboard_path = reverse('payroll:dashboard')
            return f"{base_url}{dashboard_path}?period={period_id}"
        except:
            # Fallback si no se puede generar la URL
            return "#"


class PayrollWhatsAppReportService:
    """
    Servicio para enviar reportes resumidos de nómina por WhatsApp
    """
    
    def __init__(self, company: PayrollCompany):
        """
        Inicializa el servicio con la empresa global
        """
        self.company = company
        # Usar el servicio unificado de WhatsApp
        self.whatsapp_service = None
        from .unified_whatsapp_service import UnifiedWhatsAppService
        self.whatsapp_service = UnifiedWhatsAppService(company)
    
    async def send_payroll_report(
        self, 
        to_phone: str,
        user_data: Dict,
        period_id: str = None,
        country_code: str = None
    ) -> Dict[str, Any]:
        """
        Genera y envía un reporte resumido de nómina por WhatsApp
        
        Args:
            to_phone: Número de teléfono del destinatario
            user_data: Datos del usuario para personalizar el mensaje
            period_id: ID del periodo (usa el último si no se especifica)
            country_code: Código de país para filtrar datos (None = reporte global)
            
        Returns:
            Dict con resultado del envío
        """
        # Si no tenemos servicio de WhatsApp, retornar error
        if not self.whatsapp_service:
            return {
                "success": False, 
                "error": "WhatsApp service not available"
            }
        
        # Obtener período
        try:
            period = None
            if period_id:
                period = GlobalPayrollPeriod.objects.get(id=period_id)
            else:
                period = GlobalPayrollPeriod.objects.filter(
                    company=self.company
                ).order_by('-end_date').first()
                
            if not period:
                return {
                    "success": False, 
                    "error": "No payroll period found"
                }
        except Exception as e:
            logger.error(f"Error retrieving period: {str(e)}")
            return {"success": False, "error": str(e)}
        
        # Generar datos resumidos del reporte
        report_data = await self._generate_summary_report(period, country_code)
        
        # Crear mensaje para WhatsApp (formato adaptado para mensajería)
        message = self._format_whatsapp_report(report_data, period, user_data)
        
        # Obtener idioma preferido del usuario
        lang = self._get_user_language(to_phone)
        
        # Enviar mensaje por WhatsApp
        try:
            response = await self.whatsapp_service.process_message(
                from_number=to_phone,
                message=f"reporte_nomina_{period_id or 'ultimo'}",
                message_type="text"
            )
            
            if response and response.get("success", False):
                # Enviar el reporte formateado en un mensaje separado
                # Esto es necesario porque el mensaje puede ser extenso
                await self.whatsapp_service._send_typing_indicator(to_phone, 2)
                
                return await self.whatsapp_service.send_text_message(
                    to_phone, 
                    message,
                    quick_replies=self._get_report_quick_replies(lang, period_id, country_code)
                )
            else:
                return {"success": False, "error": "Failed to process initial message"}
                
        except Exception as e:
            logger.error(f"Error sending WhatsApp report: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _generate_summary_report(
        self, 
        period: GlobalPayrollPeriod,
        country_code: str = None
    ) -> Dict[str, Any]:
        """
        Genera un resumen de datos para el reporte por WhatsApp
        """
        # Similar al método _generate_report_data pero simplificado
        # para adaptarse mejor a formato de WhatsApp
        global_data = {
            'total_employees': 0,
            'total_gross': 0,
            'total_net': 0,
            'total_taxes': 0,
            'gross_trend': 0,
            'currency_symbol': self.company.default_currency_symbol or '$'
        }
        
        top_countries = []
        
        # Si se especificó un país, filtrar subsidiarias
        subsidiaries = PayrollSubsidiary.objects.filter(company=self.company)
        if country_code:
            subsidiaries = subsidiaries.filter(country_code=country_code)
        
        # Recopilar datos resumidos
        for subsidiary in subsidiaries:
            payroll_period = PayrollPeriod.objects.filter(
                global_period=period,
                subsidiary=subsidiary
            ).first()
            
            if not payroll_period:
                continue
                
            employees = payroll_period.employee_count or 0
            gross = payroll_period.total_gross or 0
            net = payroll_period.total_net or 0
            taxes = payroll_period.total_taxes or 0
            
            global_data['total_employees'] += employees
            global_data['total_gross'] += gross
            global_data['total_net'] += net
            global_data['total_taxes'] += taxes
            
            # Guardar datos de los 3 países principales por número de empleados
            if len(top_countries) < 3:
                top_countries.append({
                    'name': subsidiary.name,
                    'employees': employees,
                    'gross': gross,
                })
        
        # Ordenar países por número de empleados
        top_countries.sort(key=lambda x: x['employees'], reverse=True)
        
        # Calcular tendencia global (comparación con período anterior)
        previous_global_period = GlobalPayrollPeriod.objects.filter(
            company=self.company,
            end_date__lt=period.start_date
        ).order_by('-end_date').first()
        
        if previous_global_period:
            previous_total = 0
            for subsidiary in subsidiaries:
                prev_period = PayrollPeriod.objects.filter(
                    global_period=previous_global_period,
                    subsidiary=subsidiary
                ).first()
                
                if prev_period:
                    previous_total += prev_period.total_gross or 0
            
            if previous_total > 0:
                global_data['gross_trend'] = (
                    (global_data['total_gross'] - previous_total) / previous_total
                ) * 100
        
        return {
            'global': global_data,
            'top_countries': top_countries,
        }
    
    def _format_whatsapp_report(
        self, 
        report_data: Dict[str, Any],
        period: GlobalPayrollPeriod,
        user_data: Dict
    ) -> str:
        """
        Formatea el reporte para envío por WhatsApp
        """
        # Datos globales
        global_data = report_data['global']
        
        # Formato adaptado a las limitaciones de WhatsApp (sin HTML, sin tablas complejas)
        message = f"📊 *REPORTE DE NÓMINA* 📊\n"
        message += f"*{self.company.name}*\n"
        message += f"Período: {period.name}\n"
        message += f"{period.start_date.strftime('%d/%m/%Y')} - {period.end_date.strftime('%d/%m/%Y')}\n\n"
        
        # Resumen global
        message += "*RESUMEN GLOBAL*\n"
        message += f"👥 Total Empleados: {global_data['total_employees']}\n"
        message += f"💰 Nómina Bruta: {global_data['currency_symbol']} {global_data['total_gross']:,.2f}\n"
        message += f"💸 Nómina Neta: {global_data['currency_symbol']} {global_data['total_net']:,.2f}\n"
        
        # Tendencia
        trend_icon = "↗️" if global_data['gross_trend'] >= 0 else "↘️"
        message += f"{trend_icon} Tendencia: {abs(global_data['gross_trend']):.1f}%"
        message += " de incremento\n\n" if global_data['gross_trend'] >= 0 else " de disminución\n\n"
        
        # Principales países (si es reporte global)
        if len(report_data['top_countries']) > 1:
            message += "*PRINCIPALES PAÍSES*\n"
            for idx, country in enumerate(report_data['top_countries']):
                message += f"{idx+1}. {country['name']}: {country['employees']} empleados, "
                message += f"{global_data['currency_symbol']} {country['gross']:,.2f}\n"
        
        # Nota de pie
        message += "\n📱 Consulte el dashboard completo en la plataforma web para más detalles.\n"
        message += "Para solicitar el reporte por email, responda con 'email'."
        
        return message
    
    def _get_user_language(self, phone_number: str) -> str:
        """
        Obtiene el idioma preferido del usuario
        """
        if hasattr(self.whatsapp_service, '_get_user_language'):
            return self.whatsapp_service._get_user_language(phone_number)
        return 'es'  # Español por defecto
    
    def _get_report_quick_replies(
        self,
        lang: str, 
        period_id: str,
        country_code: str
    ) -> List[Dict[str, str]]:
        """
        Genera respuestas rápidas para el reporte
        """
        # Mapa de traducciones básicas
        translations = {
            'es': {
                'email': '📧 Enviar por email',
                'detail': '📋 Ver detalles',
                'dashboard': '📊 Ir al dashboard'
            },
            'en': {
                'email': '📧 Send by email',
                'detail': '📋 View details',
                'dashboard': '📊 Go to dashboard'
            },
            'fr': {
                'email': '📧 Envoyer par email',
                'detail': '📋 Voir détails',
                'dashboard': '📊 Aller au dashboard'
            },
            'pt': {
                'email': '📧 Enviar por email',
                'detail': '📋 Ver detalhes',
                'dashboard': '📊 Ir ao dashboard'
            }
        }
        
        # Usar español por defecto si el idioma no está soportado
        t = translations.get(lang, translations['es'])
        
        quick_replies = [
            {"text": t['email'], "action": f"report_email_{period_id or 'latest'}"},
            {"text": t['detail'], "action": f"report_detail_{period_id or 'latest'}"}
        ]
        
        return quick_replies
