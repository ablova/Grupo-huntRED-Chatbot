"""
Servicio de Dashboard y Reportes para RH
Provee reportes a demanda vía WhatsApp y Email
"""
import logging
import json
import pandas as pd
import numpy as np
from io import BytesIO
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union

from django.utils import timezone
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from ..models import PayrollCompany, PayrollEmployee, AttendanceRecord, EmployeeRequest
from .. import PAYROLL_ROLES, ATTENDANCE_STATUSES, REQUEST_STATUSES

logger = logging.getLogger(__name__)

class HRDashboardService:
    """
    Servicio para generación y envío de reportes de RH a demanda
    """
    
    def __init__(self, company: PayrollCompany):
        """
        Inicializa servicio con la empresa especificada
        
        Args:
            company: Instancia de PayrollCompany
        """
        self.company = company
        self.report_formats = ['text', 'excel', 'pdf', 'chart']
        self.report_types = {
            'attendance': 'Reporte de Asistencia',
            'employee_roster': 'Planilla de Empleados',
            'payroll_summary': 'Resumen de Nómina',
            'terminations': 'Bajas de Personal',
            'new_hires': 'Altas de Personal',
            'vacation_balance': 'Balance de Vacaciones',
            'permissions': 'Permisos Solicitados'
        }
    
    def generate_report(self, report_type: str, 
                       start_date: Optional[date] = None,
                       end_date: Optional[date] = None,
                       report_format: str = 'text',
                       filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Genera reporte según el tipo solicitado
        
        Args:
            report_type: Tipo de reporte (attendance, employee_roster, etc.)
            start_date: Fecha de inicio para el reporte
            end_date: Fecha de fin para el reporte
            report_format: Formato del reporte (text, excel, pdf, chart)
            filters: Filtros adicionales para el reporte
            
        Returns:
            Diccionario con los resultados del reporte y metadatos
        """
        try:
            # Validar tipo de reporte
            if report_type not in self.report_types:
                return {
                    'success': False,
                    'error': f'Tipo de reporte inválido. Opciones: {", ".join(self.report_types.keys())}'
                }
            
            # Validar formato de reporte
            if report_format not in self.report_formats:
                return {
                    'success': False,
                    'error': f'Formato inválido. Opciones: {", ".join(self.report_formats)}'
                }
                
            # Establecer fechas por defecto si no se proporcionaron
            if not start_date:
                # Por defecto, una semana atrás
                start_date = (timezone.now() - timedelta(days=7)).date()
            
            if not end_date:
                # Por defecto, hoy
                end_date = timezone.now().date()
                
            # Inicializar filtros si es None
            filters = filters or {}
            
            # Añadir metadatos del reporte
            metadata = {
                'report_type': report_type,
                'report_name': self.report_types[report_type],
                'company': self.company.name,
                'generated_at': timezone.now(),
                'period': f'{start_date.strftime("%d/%m/%Y")} - {end_date.strftime("%d/%m/%Y")}',
                'format': report_format
            }
            
            # Generar el reporte específico según su tipo
            if report_type == 'attendance':
                result = self._generate_attendance_report(start_date, end_date, filters)
            elif report_type == 'employee_roster':
                result = self._generate_employee_roster(filters)
            elif report_type == 'payroll_summary':
                result = self._generate_payroll_summary(start_date, end_date, filters)
            elif report_type == 'terminations':
                result = self._generate_terminations_report(start_date, end_date, filters)
            elif report_type == 'new_hires':
                result = self._generate_new_hires_report(start_date, end_date, filters)
            elif report_type == 'vacation_balance':
                result = self._generate_vacation_balance_report(filters)
            elif report_type == 'permissions':
                result = self._generate_permissions_report(start_date, end_date, filters)
            else:
                return {
                    'success': False,
                    'error': 'Tipo de reporte no implementado'
                }
                
            # Formatear resultado según formato solicitado
            formatted_result = self._format_report(result, report_format, metadata)
            
            return {
                'success': True,
                'data': formatted_result,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Error generando reporte {report_type}: {str(e)}")
            return {
                'success': False,
                'error': f'Error generando reporte: {str(e)}'
            }
    
    def send_report_email(self, email: str, report_data: Dict[str, Any],
                         subject: Optional[str] = None) -> Dict[str, bool]:
        """
        Envía reporte por correo electrónico
        
        Args:
            email: Correo electrónico del destinatario
            report_data: Datos del reporte generado
            subject: Asunto del correo (opcional)
            
        Returns:
            Diccionario con resultado del envío
        """
        try:
            if not report_data.get('success', False):
                return {'sent': False, 'error': 'Datos de reporte inválidos'}
                
            metadata = report_data.get('metadata', {})
            report_type = metadata.get('report_type', 'unknown')
            report_name = metadata.get('report_name', 'Reporte')
            
            # Crear asunto si no se proporcionó
            if not subject:
                subject = f"{report_name} - {self.company.name} - {metadata.get('period', '')}"
                
            # Preparar el correo
            email_body = render_to_string('payroll/email/report_email.html', {
                'company_name': self.company.name,
                'report_name': report_name,
                'period': metadata.get('period', ''),
                'generated_at': metadata.get('generated_at', timezone.now()).strftime('%d/%m/%Y %H:%M')
            })
            
            # Crear el email
            email_message = EmailMessage(
                subject=subject,
                body=email_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email]
            )
            email_message.content_subtype = "html"
            
            # Adjuntar el reporte según su formato
            format_type = metadata.get('format', 'text')
            
            if format_type == 'excel':
                # El reporte debe contener un DataFrame o datos para Excel
                excel_data = report_data.get('data', {}).get('excel_data')
                if excel_data:
                    excel_buffer = BytesIO()
                    excel_data.to_excel(excel_buffer, index=False)
                    excel_buffer.seek(0)
                    email_message.attach(
                        f"{report_type}_{metadata.get('period', 'report')}.xlsx", 
                        excel_buffer.read(), 
                        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    )
            elif format_type == 'pdf':
                # El reporte debe contener datos de PDF
                pdf_data = report_data.get('data', {}).get('pdf_data')
                if pdf_data:
                    email_message.attach(
                        f"{report_type}_{metadata.get('period', 'report')}.pdf", 
                        pdf_data, 
                        'application/pdf'
                    )
            elif format_type == 'chart':
                # El reporte debe contener una imagen de gráfico
                chart_data = report_data.get('data', {}).get('chart_data')
                if chart_data:
                    email_message.attach(
                        f"{report_type}_{metadata.get('period', 'report')}.png", 
                        chart_data, 
                        'image/png'
                    )
            else:
                # Para formato texto, incluir directamente en el email
                text_data = report_data.get('data', {}).get('text')
                if text_data:
                    email_message.body += f"\n\n{text_data}"
            
            # Enviar el correo
            email_message.send()
            
            return {'sent': True}
            
        except Exception as e:
            logger.error(f"Error enviando reporte por email: {str(e)}")
            return {'sent': False, 'error': str(e)}
    
    def prepare_whatsapp_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepara reporte para envío por WhatsApp
        
        Args:
            report_data: Datos del reporte generado
            
        Returns:
            Diccionario con formato WhatsApp-friendly
        """
        try:
            if not report_data.get('success', False):
                return {
                    'success': False,
                    'message': f"❌ Error: {report_data.get('error', 'Reporte inválido')}",
                    'quick_replies': [
                        {"text": "🔄 Reintentar", "action": "retry_report"},
                        {"text": "📊 Otros reportes", "action": "hr_reports"},
                        {"text": "🏠 Menú principal", "action": "main_menu"}
                    ]
                }
            
            metadata = report_data.get('metadata', {})
            report_name = metadata.get('report_name', 'Reporte')
            period = metadata.get('period', '')
            
            # Preparar cabecera del mensaje
            header = f"📊 *{report_name.upper()}*\n"
            header += f"🏢 {self.company.name}\n"
            header += f"📅 Periodo: {period}\n"
            header += f"⏱️ Generado: {metadata.get('generated_at', timezone.now()).strftime('%d/%m/%Y %H:%M')}\n\n"
            
            # Para formatos no texto, ofrecer alternativa por email
            format_type = metadata.get('format', 'text')
            message = ""
            
            if format_type != 'text':
                message = header
                message += f"El reporte '{report_name}' está listo en formato {format_type.upper()}.\n\n"
                message += "Este tipo de reporte no puede visualizarse directamente en WhatsApp.\n"
                message += "¿Deseas recibirlo por correo electrónico?"
                
                return {
                    'success': True,
                    'message': message,
                    'quick_replies': [
                        {"text": "📧 Enviar por email", "action": f"email_report_{metadata.get('report_type')}"},
                        {"text": "📊 Otros reportes", "action": "hr_reports"},
                        {"text": "🏠 Menú principal", "action": "main_menu"}
                    ]
                }
            
            # Para formato texto, mostrar directamente
            text_data = report_data.get('data', {}).get('text', '')
            message = header + text_data
            
            # Si el mensaje es muy largo (límite de WhatsApp ~4096 caracteres)
            if len(message) > 3500:
                # Truncar y ofrecer completo por email
                message = message[:3500] + "...\n\n⚠️ *Reporte truncado*. El reporte completo está disponible por email."
            
            return {
                'success': True,
                'message': message,
                'quick_replies': [
                    {"text": "📧 Reporte completo por email", "action": f"email_report_{metadata.get('report_type')}"},
                    {"text": "📊 Otros reportes", "action": "hr_reports"},
                    {"text": "🏠 Menú principal", "action": "main_menu"}
                ]
            }
            
        except Exception as e:
            logger.error(f"Error preparando reporte para WhatsApp: {str(e)}")
            return {
                'success': False,
                'message': f"❌ Error preparando reporte: {str(e)}",
                'quick_replies': [
                    {"text": "🔄 Reintentar", "action": "retry_report"},
                    {"text": "🏠 Menú principal", "action": "main_menu"}
                ]
            }
    
    # Métodos para generar reportes específicos
    
    def _generate_attendance_report(self, start_date: date, end_date: date, 
                                  filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera reporte de asistencia para el período especificado
        
        Args:
            start_date: Fecha de inicio
            end_date: Fecha de fin
            filters: Filtros adicionales
            
        Returns:
            Datos del reporte
        """
        # Obtener registros de asistencia en el período
        records = AttendanceRecord.objects.filter(
            company=self.company,
            date__gte=start_date,
            date__lte=end_date
        )
        
        # Aplicar filtros adicionales
        if 'department' in filters:
            records = records.filter(employee__department=filters['department'])
            
        if 'supervisor' in filters:
            records = records.filter(employee__supervisor_id=filters['supervisor'])
        
        # Consolidar datos
        total_records = records.count()
        present = records.filter(status=ATTENDANCE_STATUSES.PRESENT).count()
        absent = records.filter(status=ATTENDANCE_STATUSES.ABSENT).count()
        late = records.filter(status=ATTENDANCE_STATUSES.LATE).count()
        excused = records.filter(status=ATTENDANCE_STATUSES.EXCUSED).count()
        
        # Crear DataFrame para análisis
        if total_records > 0:
            df = pd.DataFrame(list(records.values('employee__id', 'employee__first_name', 
                                               'employee__last_name', 'date', 'status',
                                               'check_in', 'check_out', 'hours_worked')))
            
            # Renombrar columnas
            df.rename(columns={
                'employee__id': 'ID',
                'employee__first_name': 'Nombre',
                'employee__last_name': 'Apellido',
                'date': 'Fecha',
                'status': 'Estado',
                'check_in': 'Entrada',
                'check_out': 'Salida',
                'hours_worked': 'Horas'
            }, inplace=True)
            
            # Calcular estadísticas
            avg_hours = df['Horas'].mean()
            df_summary = df.groupby('ID').agg({
                'Nombre': 'first',
                'Apellido': 'first',
                'Horas': 'sum',
                'Fecha': 'count'
            }).reset_index()
            df_summary.rename(columns={'Fecha': 'Días'}, inplace=True)
            df_summary['Promedio_Horas'] = df_summary['Horas'] / df_summary['Días']
            
            # Estadísticas adicionales
            employees_perfect = len(df_summary[df_summary['Días'] == (end_date - start_date).days + 1])
            
        else:
            df = pd.DataFrame()
            df_summary = pd.DataFrame()
            avg_hours = 0
            employees_perfect = 0
        
        # Construir datos del reporte
        report_data = {
            'summary': {
                'total_records': total_records,
                'present': present,
                'absent': absent,
                'late': late,
                'excused': excused,
                'period_days': (end_date - start_date).days + 1,
                'avg_hours': round(avg_hours, 2) if total_records > 0 else 0,
                'employees_perfect': employees_perfect
            },
            'records': records,
            'dataframe': df,
            'summary_df': df_summary
        }
        
        return report_data
    
    def _generate_employee_roster(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera reporte de planilla de empleados actual
        
        Args:
            filters: Filtros adicionales
            
        Returns:
            Datos del reporte
        """
        # Obtener todos los empleados activos
        employees = PayrollEmployee.objects.filter(
            company=self.company,
            is_active=True
        )
        
        # Aplicar filtros adicionales
        if 'department' in filters:
            employees = employees.filter(department=filters['department'])
            
        if 'role' in filters:
            role = filters['role']
            employees = employees.filter(roles__contains=[role])
        
        # Consolidar datos
        total_employees = employees.count()
        
        # Crear DataFrame para análisis
        if total_employees > 0:
            # Convertir a lista de diccionarios para DataFrame
            employees_data = []
            for emp in employees:
                emp_dict = {
                    'ID': emp.id,
                    'Nombre': emp.first_name,
                    'Apellido': emp.last_name,
                    'Email': emp.email,
                    'Departamento': emp.department,
                    'Posición': emp.position,
                    'Fecha_Contratación': emp.hire_date,
                    'Salario': getattr(emp, 'salary', 0),
                    'Supervisor': getattr(emp.supervisor, 'full_name', '') if getattr(emp, 'supervisor', None) else '',
                    'Roles': ', '.join(emp.roles) if hasattr(emp, 'roles') and emp.roles else ''
                }
                employees_data.append(emp_dict)
                
            df = pd.DataFrame(employees_data)
            
            # Estadísticas
            departments = df['Departamento'].value_counts().to_dict()
            positions = df['Posición'].value_counts().to_dict()
            avg_tenure = (timezone.now().date() - pd.to_datetime(df['Fecha_Contratación']).dt.date).mean().days / 365
            
        else:
            df = pd.DataFrame()
            departments = {}
            positions = {}
            avg_tenure = 0
        
        # Construir datos del reporte
        report_data = {
            'summary': {
                'total_employees': total_employees,
                'departments': departments,
                'positions': positions,
                'avg_tenure_years': round(avg_tenure, 2) if total_employees > 0 else 0
            },
            'employees': employees,
            'dataframe': df
        }
        
        return report_data
    
    def _generate_payroll_summary(self, start_date: date, end_date: date, 
                                filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera resumen de nómina para el período especificado
        
        Args:
            start_date: Fecha de inicio
            end_date: Fecha de fin
            filters: Filtros adicionales
            
        Returns:
            Datos del reporte
        """
        # Este método requeriría implementación específica según el modelo de datos
        # Por ahora, retornamos datos simulados
        
        # Simulación de datos
        from random import randint, uniform
        
        employees = PayrollEmployee.objects.filter(
            company=self.company,
            is_active=True
        )
        
        # Aplicar filtros adicionales
        if 'department' in filters:
            employees = employees.filter(department=filters['department'])
        
        total_employees = employees.count()
        
        # Datos simulados para demostración
        total_salary = sum(uniform(15000, 50000) for _ in range(total_employees))
        total_bonus = total_salary * 0.15
        total_deductions = total_salary * 0.35
        net_payroll = total_salary + total_bonus - total_deductions
        
        # Construir datos del reporte
        report_data = {
            'summary': {
                'total_employees': total_employees,
                'total_salary': round(total_salary, 2),
                'total_bonus': round(total_bonus, 2),
                'total_deductions': round(total_deductions, 2),
                'net_payroll': round(net_payroll, 2),
                'average_salary': round(total_salary / total_employees, 2) if total_employees > 0 else 0
            }
        }
        
        # Simular distribución por departamento
        departments = {}
        for emp in employees:
            dept = emp.department
            if dept not in departments:
                departments[dept] = {
                    'employees': 0,
                    'salary': 0,
                    'bonus': 0,
                    'deductions': 0,
                    'net': 0
                }
                
            departments[dept]['employees'] += 1
            salary = uniform(15000, 50000)
            bonus = salary * uniform(0.1, 0.2)
            deductions = salary * uniform(0.3, 0.4)
            net = salary + bonus - deductions
            
            departments[dept]['salary'] += salary
            departments[dept]['bonus'] += bonus
            departments[dept]['deductions'] += deductions
            departments[dept]['net'] += net
        
        report_data['departments'] = departments
        
        return report_data
    
    def _generate_terminations_report(self, start_date: date, end_date: date, 
                                    filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera reporte de bajas de personal
        
        Args:
            start_date: Fecha de inicio
            end_date: Fecha de fin
            filters: Filtros adicionales
            
        Returns:
            Datos del reporte
        """
        # Obtener empleados dados de baja en el período
        terminated_employees = PayrollEmployee.objects.filter(
            company=self.company,
            is_active=False,
            termination_date__gte=start_date,
            termination_date__lte=end_date
        )
        
        # Aplicar filtros adicionales
        if 'department' in filters:
            terminated_employees = terminated_employees.filter(department=filters['department'])
            
        if 'termination_type' in filters:
            terminated_employees = terminated_employees.filter(termination_type=filters['termination_type'])
        
        # Consolidar datos
        total_terminations = terminated_employees.count()
        
        # Crear DataFrame para análisis
        if total_terminations > 0:
            # Convertir a lista de diccionarios para DataFrame
            employees_data = []
            for emp in terminated_employees:
                tenure = (emp.termination_date - emp.hire_date).days / 365
                
                emp_dict = {
                    'ID': emp.id,
                    'Nombre': emp.first_name,
                    'Apellido': emp.last_name,
                    'Departamento': emp.department,
                    'Posición': emp.position,
                    'Fecha_Contratación': emp.hire_date,
                    'Fecha_Baja': emp.termination_date,
                    'Antigüedad_Años': round(tenure, 2),
                    'Motivo': getattr(emp, 'termination_reason', 'No especificado'),
                    'Tipo': getattr(emp, 'termination_type', 'No especificado')
                }
                employees_data.append(emp_dict)
                
            df = pd.DataFrame(employees_data)
            
            # Estadísticas
            dept_counts = df['Departamento'].value_counts().to_dict()
            reason_counts = df['Motivo'].value_counts().to_dict()
            avg_tenure = df['Antigüedad_Años'].mean()
            
        else:
            df = pd.DataFrame()
            dept_counts = {}
            reason_counts = {}
            avg_tenure = 0
        
        # Construir datos del reporte
        report_data = {
            'summary': {
                'total_terminations': total_terminations,
                'by_department': dept_counts,
                'by_reason': reason_counts,
                'avg_tenure_years': round(avg_tenure, 2) if total_terminations > 0 else 0
            },
            'terminated_employees': terminated_employees,
            'dataframe': df
        }
        
        return report_data

    # Métodos para formateo de reportes
    
    def _format_report(self, report_data: Dict[str, Any], 
                      report_format: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formatea el reporte según el formato solicitado
        
        Args:
            report_data: Datos del reporte
            report_format: Formato deseado (text, excel, pdf, chart)
            metadata: Metadatos del reporte
            
        Returns:
            Reporte formateado
        """
        if report_format == 'text':
            return self._format_as_text(report_data, metadata)
        elif report_format == 'excel':
            return self._format_as_excel(report_data, metadata)
        elif report_format == 'pdf':
            return self._format_as_pdf(report_data, metadata)
        elif report_format == 'chart':
            return self._format_as_chart(report_data, metadata)
        else:
            return {'error': f'Formato no soportado: {report_format}'}

    def _format_as_text(self, report_data: Dict[str, Any], 
                       metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formatea reporte como texto plano
        """
        report_type = metadata['report_type']
        text = f"--- {metadata['report_name'].upper()} ---\n\n"
        
        # Formatear según tipo de reporte
        if report_type == 'attendance':
            summary = report_data['summary']
            text += "RESUMEN DE ASISTENCIA:\n"
            text += f"• Registros totales: {summary['total_records']}\n"
            text += f"• Presentes: {summary['present']} ({round(summary['present']/summary['total_records']*100 if summary['total_records'] > 0 else 0, 1)}%)\n"
            text += f"• Ausentes: {summary['absent']} ({round(summary['absent']/summary['total_records']*100 if summary['total_records'] > 0 else 0, 1)}%)\n"
            text += f"• Llegadas tarde: {summary['late']} ({round(summary['late']/summary['total_records']*100 if summary['total_records'] > 0 else 0, 1)}%)\n"
            text += f"• Ausencias justificadas: {summary['excused']} ({round(summary['excused']/summary['total_records']*100 if summary['total_records'] > 0 else 0, 1)}%)\n"
            text += f"• Promedio de horas trabajadas: {summary['avg_hours']} hrs\n"
            
        elif report_type == 'employee_roster':
            summary = report_data['summary']
            text += "RESUMEN DE PLANILLA:\n"
            text += f"• Total de empleados activos: {summary['total_employees']}\n"
            text += f"• Antigüedad promedio: {summary['avg_tenure_years']} años\n\n"
            
            text += "DISTRIBUCIÓN POR DEPARTAMENTO:\n"
            for dept, count in summary['departments'].items():
                text += f"• {dept}: {count} empleados\n"
                
        elif report_type == 'payroll_summary':
            summary = report_data['summary']
            text += "RESUMEN DE NÓMINA:\n"
            text += f"• Total de empleados: {summary['total_employees']}\n"
            text += f"• Salario base total: ${summary['total_salary']:,.2f}\n"
            text += f"• Bonos/extras: ${summary['total_bonus']:,.2f}\n"
            text += f"• Deducciones: ${summary['total_deductions']:,.2f}\n"
            text += f"• Nómina neta: ${summary['net_payroll']:,.2f}\n"
            text += f"• Salario promedio: ${summary['average_salary']:,.2f}\n\n"
            
            text += "DISTRIBUCIÓN POR DEPARTAMENTO:\n"
            for dept, data in report_data.get('departments', {}).items():
                text += f"• {dept}: {data['employees']} emp, ${data['net']:,.2f}\n"
                
        elif report_type == 'terminations':
            summary = report_data['summary']
            text += "RESUMEN DE BAJAS DE PERSONAL:\n"
            text += f"• Total de bajas: {summary['total_terminations']}\n"
            text += f"• Antigüedad promedio: {summary['avg_tenure_years']} años\n\n"
            
            text += "BAJAS POR MOTIVO:\n"
            for reason, count in summary.get('by_reason', {}).items():
                text += f"• {reason}: {count}\n"
                
        else:
            # Formateo genérico para otros tipos
            text += "DATOS DEL REPORTE:\n"
            for key, value in report_data.get('summary', {}).items():
                # Convertir snake_case a título
                key_title = ' '.join(word.capitalize() for word in key.split('_'))
                text += f"• {key_title}: {value}\n"
                
        return {'text': text}
