from app.ats.integrations.menu.base import BaseMenu
from app.ats.integrations.menu.whatsapp import WhatsAppMenu  # re-uso helpers
from app.payroll.services.whatsapp_reports_service import WhatsAppReportsService
from app.payroll.services.rh_email_reports_service import RHEmailReportsService
from app.payroll.services.hr_dashboard_service import HRDashboardService
from app.payroll.services.unified_whatsapp_service import UnifiedWhatsAppService
from app.payroll.services.assessment_integration_service import AssessmentIntegrationService
from app.payroll.services.payroll_report_service import PayrollEmailReportService, PayrollWhatsAppReportService
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
        
        # Servicios de reportes multi-país
        self.payroll_email_service = PayrollEmailReportService(company)
        self.payroll_whatsapp_service = PayrollWhatsAppReportService(company)
        
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
        
        # registrar handlers para reportes multi-país
        self.register_handler("multicountry_report", self.handle_multicountry_report)
        self.register_handler("country_report", self.handle_country_report)
        self.register_handler("report_email", self.handle_report_email_request)
        self.register_handler("report_detail", self.handle_report_detail_request)
        
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
            
        # Obtener idioma preferido
        lang = self._get_user_language(kw.get('phone_number', ''))
        
        # Textos adaptados al idioma
        header = get_message('hr_dashboard', 'header', lang)
        msg_intro = get_message('hr_dashboard', 'intro', lang)
        msg_choose = get_message('hr_dashboard', 'choose', lang)
        
        # Opciones de reportes
        attendance_text = get_message('hr_dashboard', 'attendance', lang)
        roster_text = get_message('hr_dashboard', 'roster', lang)
        payroll_text = get_message('hr_dashboard', 'payroll', lang)
        terminations_text = get_message('hr_dashboard', 'terminations', lang)
        new_hires_text = get_message('hr_dashboard', 'new_hires', lang)
        vacation_text = get_message('hr_dashboard', 'vacation', lang)
        multicountry_text = get_message('hr_dashboard', 'multicountry', lang, default="Nómina Multi-País")
        
        # Construir mensaje
        message = f"""*{header}*

{msg_intro}

{msg_choose}"""
        
        # Opciones del menú
        quick_replies = [
            {"text": f"🌎 {multicountry_text}", "action": "multicountry_report"},
            {"text": f"📊 {attendance_text}", "action": "hr_report_attendance"},
            {"text": f"👥 {roster_text}", "action": "hr_report_roster"},
            {"text": f"💰 {payroll_text}", "action": "hr_report_payroll"},
            {"text": f"🔴 {terminations_text}", "action": "hr_report_terminations"},
            {"text": f"🟢 {new_hires_text}", "action": "hr_report_new_hires"},
            {"text": f"🏖 {vacation_text}", "action": "hr_report_vacation"}
        ]
        
        # Formatear respuesta
        return self._create_text_message(message, quick_replies, lang)
    
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
    
    def handle_multicountry_report(self, item, **kw):
        """Muestra el reporte de nómina multi-país en WhatsApp"""
        emp = kw["employee"]
        phone_number = kw.get('phone_number', '')
        
        # Verificar permisos
        if not emp.has_role(PAYROLL_ROLES.HR):
            return self._create_text_message("⚠️ No tienes permisos para esta acción.")
        
        # Obtener el idioma preferido del usuario
        lang = self._get_user_language(phone_number)
        
        # Obtener periodo actual de nómina
        current_period = timezone.now().date().replace(day=1)
        previous_period = (current_period - timedelta(days=1)).replace(day=1)
        
        # Generar reporte en formato WhatsApp
        whatsapp_report = self.payroll_whatsapp_service.generate_global_payroll_summary(
            current_period=current_period,
            previous_period=previous_period,
            language=lang
        )
        
        # Opciones para solicitar reportes detallados por país
        countries = self.payroll_whatsapp_service.get_available_countries()
        country_options = [{"text": f"🏁 {country}", "action": f"country_report:{country}"} 
                          for country in countries[:6]]  # Limitar a 6 países para evitar sobrecarga
        
        # Añadir opción para solicitar el reporte por correo
        email_option = {"text": "📧 Recibir por Email", "action": "report_email"}
        country_options.append(email_option)
        
        # Crear respuesta para WhatsApp con opciones de países
        response = {
            "text": whatsapp_report,
            "quick_replies": country_options
        }
        
        return response
    
    def handle_country_report(self, item, **kw):
        """Muestra el reporte de nómina de un país específico"""
        emp = kw["employee"]
        phone_number = kw.get('phone_number', '')
        action = item.get('action', '')
        
        # Verificar permisos
        if not emp.has_role(PAYROLL_ROLES.HR):
            return self._create_text_message("⚠️ No tienes permisos para esta acción.")
        
        # Extraer código de país de la acción
        try:
            country_code = action.split(':')[1]
        except (IndexError, ValueError):
            return self._create_text_message("❌ Error: País no especificado o inválido.")
        
        # Obtener el idioma preferido del usuario
        lang = self._get_user_language(phone_number)
        
        # Obtener periodo actual de nómina
        current_period = timezone.now().date().replace(day=1)
        
        # Generar reporte por país en formato WhatsApp
        country_report = self.payroll_whatsapp_service.generate_country_payroll_summary(
            country_code=country_code,
            period=current_period,
            language=lang
        )
        
        # Opciones para solicitar más detalles o regresar
        quick_replies = [
            {"text": "📈 Más Detalles", "action": f"report_detail:{country_code}"},
            {"text": "📧 Enviar por Email", "action": f"report_email:{country_code}"},
            {"text": "⬅️ Volver", "action": "multicountry_report"}
        ]
        
        # Crear respuesta para WhatsApp
        response = {
            "text": country_report,
            "quick_replies": quick_replies
        }
        
        return response
    
    def handle_report_detail_request(self, item, **kw):
        """Proporciona detalles adicionales sobre un reporte específico"""
        emp = kw["employee"]
        action = item.get('action', '')
        phone_number = kw.get('phone_number', '')
        
        # Verificar permisos
        if not emp.has_role(PAYROLL_ROLES.HR):
            return self._create_text_message("⚠️ No tienes permisos para esta acción.")
        
        # Extraer código de país o tipo de detalle de la acción
        try:
            detail_type = action.split(':')[1]
        except (IndexError, ValueError):
            detail_type = 'global'  # Por defecto, detalles globales
        
        # Obtener el idioma preferido del usuario
        lang = self._get_user_language(phone_number)
        
        # Generar detalles adicionales (métricas, gráficos en texto, etc.)
        detail_report = self.payroll_whatsapp_service.generate_detailed_metrics(
            detail_type=detail_type,
            language=lang
        )
        
        # Opciones para regresar al menú anterior
        back_action = "multicountry_report" if detail_type == 'global' else f"country_report:{detail_type}"
        quick_replies = [
            {"text": "📧 Enviar por Email", "action": f"report_email:{detail_type}"},
            {"text": "⬅️ Volver", "action": back_action}
        ]
        
        # Crear respuesta para WhatsApp
        response = {
            "text": detail_report,
            "quick_replies": quick_replies
        }
        
        return response
    
    def handle_report_email_request(self, item, **kw):
        """Envía el reporte completo al correo del usuario"""
        emp = kw["employee"]
        action = item.get('action', '')
        phone_number = kw.get('phone_number', '')
        
        # Verificar permisos
        if not emp.has_role(PAYROLL_ROLES.HR):
            return self._create_text_message("⚠️ No tienes permisos para esta acción.")
        
        # Extraer código de país o tipo de reporte de la acción
        try:
            report_type = action.split(':')[1]
        except (IndexError, ValueError):
            report_type = 'global'  # Por defecto, reporte global
        
        # Obtener el idioma preferido del usuario
        lang = self._get_user_language(phone_number)
        
        # Determinar periodo actual de nómina
        current_period = timezone.now().date().replace(day=1)
        
        # Determinar destinatarios
        recipients = [emp.email]
        
        # Enviar el reporte por correo usando el servicio apropiado
        if report_type == 'global':
            # Reporte global multi-país
            success = self.payroll_email_service.send_global_payroll_report(
                recipients=recipients,
                period=current_period,
                include_charts=True,
                language=lang
            )
        else:
            # Reporte específico de un país
            success = self.payroll_email_service.send_country_payroll_report(
                recipients=recipients,
                country_code=report_type,
                period=current_period,
                include_charts=True,
                language=lang
            )
        
        # Crear mensaje de confirmación
        if success:
            message = f"""📧 *Reporte enviado con éxito*
            
Hemos enviado el reporte completo a tu correo electrónico ({emp.email}).
Revisa tu bandeja de entrada en unos momentos."""
        else:
            message = """❌ *Error al enviar el reporte*
            
Hubo un problema al enviar el reporte a tu correo electrónico.
Por favor, inténtalo más tarde o contacta con soporte."""
        
        # Opciones para regresar al menú anterior
        back_action = "multicountry_report" if report_type == 'global' else f"country_report:{report_type}"
        quick_replies = [
            {"text": "⬅️ Volver al Menú", "action": back_action}
        ]
        
        # Crear respuesta para WhatsApp
        response = {
            "text": message,
            "quick_replies": quick_replies
        }
        
        return response
    
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