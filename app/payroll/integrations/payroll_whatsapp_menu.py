from app.ats.integrations.menu.base import BaseMenu
from app.ats.integrations.menu.whatsapp import WhatsAppMenu  # re-uso helpers
from app.payroll.services.whatsapp_reports_service import WhatsAppReportsService
from app.payroll.services.rh_email_reports_service import RHEmailReportsService
from app.payroll.services.hr_dashboard_service import HRDashboardService
from app.payroll.services.unified_whatsapp_service import UnifiedWhatsAppService
from app.payroll.services.assessment_integration_service import AssessmentIntegrationService
from datetime import datetime, date, timedelta
from django.utils import timezone
from app.payroll import PAYROLL_ROLES

# Importamos soporte de internacionalización
from app.payroll.i18n import get_message, get_button_text, detect_language, SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE

class PayrollWhatsAppMenu(BaseMenu):
    def __init__(self, company):
        super().__init__(business_unit="payroll")
        self.company = company
        self.reports = WhatsAppReportsService()
        self.hr_dashboard = HRDashboardService(company)
        self.whatsapp_service = UnifiedWhatsAppService(company)
        self.assessment_service = AssessmentIntegrationService(company)
        
        # Diccionario para almacenar preferencias de idioma de usuarios
        self.user_languages = {}
        
        # registrar handlers básicos
        self.register_handler("mis_reportes", self.handle_my)
        self.register_handler("reportes_equipo", self.handle_team)
        self.register_handler("enviar_reporte_rh", self.handle_rh)
        
        # registrar handlers de dashboard para RH
        self.register_handler("hr_dashboard", self.handle_hr_dashboard)
        self.register_handler("hr_report_attendance", self.handle_hr_attendance_report)
        self.register_handler("hr_report_roster", self.handle_hr_roster_report)
        self.register_handler("hr_report_payroll", self.handle_hr_payroll_report)
        self.register_handler("hr_report_terminations", self.handle_hr_terminations_report)
        self.register_handler("hr_report_new_hires", self.handle_hr_new_hires_report)
        self.register_handler("hr_report_vacation", self.handle_hr_vacation_report)
        self.register_handler("email_report", self.handle_email_report)
        
        # registrar handlers de assessments
        self.register_handler("nom35_dashboard", self.handle_nom35_dashboard)
        self.register_handler("nom35_status", self.handle_nom35_status)
        self.register_handler("nom35_send_invites", self.handle_nom35_send_invites)
        self.register_handler("nom35_invite_employee", self.handle_nom35_invite_employee)
        self.register_handler("nom35_compliance_report", self.handle_nom35_compliance_report)

    # ─ handlers ─
    def handle_my(self, item, **kw):
        return self.reports.get_employee_report(kw["employee"])

    def _create_text_message(self, text, quick_replies=None, language=DEFAULT_LANGUAGE):
        """Crea un mensaje de texto con soporte multilingüe"""
        response = {"text": text}
        if quick_replies:
            response["quick_replies"] = quick_replies
        return response
        
    def _get_user_language(self, phone_number):
        """Obtiene el idioma preferido del usuario o lo sincroniza con el WhatsAppService"""
        # Primero intentar obtener del menú
        if phone_number in self.user_languages:
            return self.user_languages[phone_number]
        
        # Si no está en el menú, intentar obtenerlo del servicio de WhatsApp
        if hasattr(self.whatsapp_service, 'user_languages') and phone_number in self.whatsapp_service.user_languages:
            self.user_languages[phone_number] = self.whatsapp_service.user_languages[phone_number]
            return self.user_languages[phone_number]
        
        # Si no está en ningún lado, usar el idioma por defecto
        return DEFAULT_LANGUAGE
    
    def _set_user_language(self, phone_number, language):
        """Establece el idioma preferido para un usuario y lo sincroniza con WhatsAppService"""
        if language in SUPPORTED_LANGUAGES:
            self.user_languages[phone_number] = language
            
            # Sincronizar con el servicio de WhatsApp
            if hasattr(self.whatsapp_service, 'user_languages'):
                self.whatsapp_service.user_languages[phone_number] = language

    def handle_team(self, item, **kw):
        return self.reports.get_team_report(kw["employee"])

    def handle_rh(self, item, **kw):
        emp = kw["employee"]
        RHEmailReportsService(emp.company).send_weekly_summary([emp.email])
        return self._create_text_message("📧 Reporte RH enviado.")
    
    # ─ Handlers para Dashboard RH ─
    
    def handle_hr_dashboard(self, item, **kw):
        """Muestra opciones de dashboard para RH"""
        emp = kw.get("employee")
        
        # Comprobar que sea un empleado con rol RH
        if not self._has_hr_permissions(emp):
            return self._create_text_message(
                "🔒 No tienes permisos para acceder al dashboard de RH.",
                [{"text": "⬅️ Volver", "action": "back"}]
            )
            
        message = """📊 *Dashboard de RH*

Selecciona una opción:"""
        
        options = [
            {"text": "📋 Reportes", "action": "hr_report_menu"},
            {"text": "📊 Dashboards", "action": "hr_dashboard_menu"},
            {"text": "📋 NOM 35", "action": "nom35_dashboard"}
        ]
        
        # Verificar que el empleado tenga rol de RH
        if not emp.has_role(PAYROLL_ROLES.HR):
            return self._create_text_message(
                "⚠️ No tienes permisos para acceder al dashboard de RH. "
                "Contacta al administrador si crees que esto es un error."
            )
        
        # Crear mensaje con opciones de reportes
        message = f"📊 *DASHBOARD RH* - {emp.company.name}\n\n"
        message += "Selecciona el tipo de reporte que deseas generar:\n\n"
        message += "1️⃣ Reporte de Asistencia\n"
        message += "2️⃣ Planilla de Empleados\n"
        message += "3️⃣ Resumen de Nómina\n"
        message += "4️⃣ Bajas de Personal\n"
        message += "5️⃣ Altas de Personal\n"
        message += "6️⃣ Balance de Vacaciones\n"
        message += "\n¿Qué reporte deseas generar?"
        
        # Crear opciones de respuesta rápida
        quick_replies = [
            {"text": "📋 Asistencia", "action": "hr_report_attendance"},
            {"text": "👥 Planilla", "action": "hr_report_roster"},
            {"text": "💰 Nómina", "action": "hr_report_payroll"},
            {"text": "🚪 Bajas", "action": "hr_report_terminations"},
            {"text": "🆕 Altas", "action": "hr_report_new_hires"},
            {"text": "🏖️ Vacaciones", "action": "hr_report_vacation"}
        ]
        
        return {
            "text": message,
            "quick_replies": quick_replies
        }
    
    def handle_hr_attendance_report(self, item, **kw):
        """Genera reporte de asistencia"""
        emp = kw["employee"]
        
        # Verificar permisos
        if not emp.has_role(PAYROLL_ROLES.HR):
            return self._create_text_message("⚠️ No tienes permisos para esta acción.")
        
        # Generar reporte de última semana
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=7)
        
        report_data = self.hr_dashboard.generate_report(
            report_type='attendance',
            start_date=start_date,
            end_date=end_date,
            report_format='text'
        )
        
        # Preparar respuesta para WhatsApp
        whatsapp_response = self.hr_dashboard.prepare_whatsapp_report(report_data)
        
        return whatsapp_response
    
    def handle_hr_roster_report(self, item, **kw):
        """Genera reporte de planilla de empleados"""
        emp = kw["employee"]
        
        # Verificar permisos
        if not emp.has_role(PAYROLL_ROLES.HR):
            return self._create_text_message("⚠️ No tienes permisos para esta acción.")
        
        report_data = self.hr_dashboard.generate_report(
            report_type='employee_roster',
            report_format='text'
        )
        
        # Preparar respuesta para WhatsApp
        whatsapp_response = self.hr_dashboard.prepare_whatsapp_report(report_data)
        
        return whatsapp_response
    
    def handle_hr_payroll_report(self, item, **kw):
        """Genera resumen de nómina"""
        emp = kw["employee"]
        
        # Verificar permisos
        if not emp.has_role(PAYROLL_ROLES.HR):
            return self._create_text_message("⚠️ No tienes permisos para esta acción.")
        
        # Generar reporte del mes actual
        today = timezone.now().date()
        start_date = date(today.year, today.month, 1)
        
        report_data = self.hr_dashboard.generate_report(
            report_type='payroll_summary',
            start_date=start_date,
            end_date=today,
            report_format='text'
        )
        
        # Preparar respuesta para WhatsApp
        whatsapp_response = self.hr_dashboard.prepare_whatsapp_report(report_data)
        
        return whatsapp_response
    
    def handle_hr_terminations_report(self, item, **kw):
        """Genera reporte de bajas de personal"""
        emp = kw["employee"]
        
        # Verificar permisos
        if not emp.has_role(PAYROLL_ROLES.HR):
            return self._create_text_message("⚠️ No tienes permisos para esta acción.")
        
        # Reporte de los últimos 30 días
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
        report_data = self.hr_dashboard.generate_report(
            report_type='terminations',
            start_date=start_date,
            end_date=end_date,
            report_format='text'
        )
        
        # Preparar respuesta para WhatsApp
        whatsapp_response = self.hr_dashboard.prepare_whatsapp_report(report_data)
        
        return whatsapp_response
        
    def handle_hr_new_hires_report(self, item, **kw):
        """Genera reporte de altas de personal"""
        emp = kw["employee"]
        
        # Verificar permisos
        if not emp.has_role(PAYROLL_ROLES.HR):
            return self._create_text_message("⚠️ No tienes permisos para esta acción.")
        
        # Reporte de los últimos 30 días
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
        report_data = self.hr_dashboard.generate_report(
            report_type='new_hires',
            start_date=start_date,
            end_date=end_date,
            report_format='text'
        )
        
        # Preparar respuesta para WhatsApp
        whatsapp_response = self.hr_dashboard.prepare_whatsapp_report(report_data)
        
        return whatsapp_response
    
    def handle_hr_vacation_report(self, item, **kw):
        """Genera reporte de balance de vacaciones"""
        emp = kw["employee"]
        
        # Verificar permisos
        if not emp.has_role(PAYROLL_ROLES.HR):
            return self._create_text_message("⚠️ No tienes permisos para esta acción.")
        
        report_data = self.hr_dashboard.generate_report(
            report_type='vacation_balance',
            report_format='text'
        )
        
        # Preparar respuesta para WhatsApp
        whatsapp_response = self.hr_dashboard.prepare_whatsapp_report(report_data)
        
        return whatsapp_response
    
    def handle_email_report(self, item, **kw):
        """Envía un reporte por correo electrónico"""
        emp = kw["employee"]
        action = item.get('action', '')
        
        # Verificar permisos
        if not emp.has_role(PAYROLL_ROLES.HR):
            return self._create_text_message("⚠️ No tienes permisos para esta acción.")
        
        # Extraer tipo de reporte de la acción (ejemplo: email_report_attendance)
        try:
            report_type = action.split('_')[-1]
        except IndexError:
            report_type = 'attendance'  # Por defecto
        
        # Determinar período según el tipo de reporte
        today = timezone.now().date()
        if report_type in ['terminations', 'new_hires']:
            start_date = today - timedelta(days=30)
        elif report_type == 'payroll_summary':
            start_date = date(today.year, today.month, 1)
        else:
            start_date = today - timedelta(days=7)
        
        # Generar reporte en formato Excel
        report_data = self.hr_dashboard.generate_report(
            report_type=report_type,
            start_date=start_date,
            end_date=today,
            report_format='excel'
        )
        
        # Enviar por correo
        if report_data.get('success', False):
            result = self.hr_dashboard.send_report_email(
                email=emp.email,
                report_data=report_data
            )
            
            if result.get('sent', False):
                return self._create_text_message(
                    "📧 Reporte enviado con éxito a tu correo.\n"
                    "Revisa tu bandeja de entrada."
                )
            else:
                return self._create_text_message(
                    f"❌ Error enviando el reporte: {result.get('error', 'Error desconocido')}"
                )
        else:
            return self._create_text_message(
                f"❌ Error generando el reporte: {report_data.get('error', 'Error desconocido')}"
            )