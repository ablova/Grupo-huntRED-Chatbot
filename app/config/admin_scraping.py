# Ubicación del archivo: /home/pablo/app/config/admin_scraping.py
"""
Módulo de administración para modelos relacionados con scraping.

Este módulo contiene las clases de administración de Django para los modelos
relacionados con scraping y análisis de datos, siguiendo las reglas globales de Grupo huntRED®.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.urls import reverse, path
from django.shortcuts import render, redirect
from django.template.response import TemplateResponse
import matplotlib.pyplot as plt
import base64
from io import BytesIO

from app.ats.config.admin_base import BaseModelAdmin

# Importaciones de modelos de scraping
from app.models import (
    DominioScraping,
    RegistroScraping,
    ReporteScraping
)

class DominioScrapingAdmin(BaseModelAdmin):
    """Admin para gestión de dominios para scraping"""
    list_display = ('id', 'empresa', 'plataforma', 'verificado', 'email_scraping_enabled', 'valid_senders', 'ultima_verificacion', 'estado')
    search_fields = ('empresa', 'dominio', 'plataforma')
    list_filter = ('estado', 'plataforma')
    ordering = ("-id",)
    list_editable = ("plataforma", "estado")
    actions = ["marcar_como_definido", "ejecutar_scraping_action", "desactivar_dominios_invalidos"]

    def get_urls(self):
        """Definiendo URLs personalizadas para funcionalidades de scraping"""
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_site.admin_view(self.dashboard_view), name='dashboard'),
            path("<int:dominio_id>/ejecutar-scraping/", self.admin_site.admin_view(self.ejecutar_scraping_view), name="ejecutar_scraping",),
        ]
        return custom_urls + urls

    def dashboard_view(self, request):
        """Vista de dashboard para monitoreo de scraping"""
        def generate_dashboard_graph():
            """Generando gráfico de dashboard para análisis de scraping"""
            # Obtener datos para el gráfico
            dominios = DominioScraping.objects.all()
            estados = dominios.values_list('estado', flat=True)
            
            # Contar ocurrencias de cada estado
            estado_counts = {}
            for estado in estados:
                if estado in estado_counts:
                    estado_counts[estado] += 1
                else:
                    estado_counts[estado] = 1
            
            # Crear gráfico
            plt.figure(figsize=(10, 6))
            plt.bar(estado_counts.keys(), estado_counts.values())
            plt.title('Distribución de Estados de Dominios')
            plt.xlabel('Estado')
            plt.ylabel('Cantidad')
            
            # Convertir a formato base64 para mostrar en HTML
            buffer = BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)
            image_png = buffer.getvalue()
            buffer.close()
            
            return base64.b64encode(image_png).decode('utf-8')
        
        # Estadísticas generales
        total_dominios = DominioScraping.objects.count()
        dominios_activos = DominioScraping.objects.filter(estado='active').count()
        dominios_verificados = DominioScraping.objects.filter(verificado=True).count()
        
        # Gráfico de dashboard
        dashboard_graph = generate_dashboard_graph()
        
        context = {
            'title': 'Dashboard de Scraping',
            'total_dominios': total_dominios,
            'dominios_activos': dominios_activos,
            'dominios_verificados': dominios_verificados,
            'dashboard_graph': dashboard_graph,
        }
        
        return TemplateResponse(request, "admin/scraping_dashboard.html", context)

    def ejecutar_scraping_view(self, request, dominio_id):
        """Vista para ejecutar scraping en un dominio específico"""
        try:
            dominio = DominioScraping.objects.get(id=dominio_id)
            # Aquí se ejecutaría la lógica de scraping
            # Por ahora, solo cambiamos el estado para demostración
            dominio.estado = 'processing'
            dominio.save()
            self.message_user(request, f"Scraping iniciado para {dominio.empresa}")
        except DominioScraping.DoesNotExist:
            self.message_user(request, "Dominio no encontrado", level=messages.ERROR)
        
        return redirect("admin:app_dominioscraping_changelist")

    def ejecutar_scraping_action(self, request, queryset):
        """Acción para ejecutar scraping en múltiples dominios"""
        for dominio in queryset:
            # Aquí se ejecutaría la lógica de scraping
            dominio.estado = 'processing'
            dominio.save()
        self.message_user(request, f"Scraping iniciado para {queryset.count()} dominios")
    ejecutar_scraping_action.short_description = "Ejecutar scraping en los dominios seleccionados"

    def ejecutar_email_scraper_action(self, request, queryset):
        """Acción para ejecutar scraping de email en dominios seleccionados"""
        for dominio in queryset:
            if dominio.email_scraping_enabled:
                # Aquí se ejecutaría la lógica de email scraping
                self.message_user(request, f"Email scraping iniciado para {dominio.empresa}")
            else:
                self.message_user(request, f"Email scraping deshabilitado para {dominio.empresa}", level=messages.WARNING)
    ejecutar_email_scraper_action.short_description = "Ejecutar email scraping en los dominios seleccionados"

    def marcar_como_definido(self, request, queryset):
        """Acción para marcar dominios como definidos"""
        queryset.update(estado='defined')
        self.message_user(request, f"{queryset.count()} dominios marcados como definidos")
    marcar_como_definido.short_description = "Marcar como definidos"

    def desactivar_dominios_invalidos(self, request, queryset):
        """Acción para desactivar dominios inválidos"""
        queryset.update(estado='invalid')
        self.message_user(request, f"{queryset.count()} dominios marcados como inválidos")
    desactivar_dominios_invalidos.short_description = "Desactivar dominios inválidos"


class RegistroScrapingAdmin(BaseModelAdmin):
    """Admin para gestión de registros de scraping"""
    list_display = ('dominio', 'estado', 'fecha_inicio', 'fecha_fin', 'vacantes_encontradas')
    search_fields = ('dominio__empresa', 'dominio__url')
    list_filter = ('estado', 'fecha_inicio', 'vacantes_encontradas')


class ReporteScrapingAdmin(BaseModelAdmin):
    """Admin para gestión de reportes de scraping"""
    list_display = ('business_unit', 'fecha', 'vacantes_creadas', 'exitosos', 'fallidos', 'parciales')
    list_filter = ('business_unit', 'fecha')
    search_fields = ('business_unit__name',)
    date_hierarchy = 'fecha'
    actions = ['generar_reporte_pdf']
    
    def generar_reporte_pdf(self, request, queryset):
        """Generando reporte PDF de los registros seleccionados"""
        import io
        from django.http import FileResponse
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        # Crear el objeto PDF
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        y = 750  # posición inicial y
        
        # Título
        p.setFont("Helvetica-Bold", 16)
        p.drawString(100, y, "Reporte de Scraping - Grupo huntRED®")
        y -= 30
        
        # Encabezados
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "Business Unit")
        p.drawString(200, y, "Fecha")
        p.drawString(300, y, "Vacantes")
        p.drawString(380, y, "Éxitos")
        p.drawString(440, y, "Fallos")
        p.drawString(500, y, "Parciales")
        y -= 20
        
        # Línea separadora
        p.line(50, y, 550, y)
        y -= 20
        
        # Datos
        p.setFont("Helvetica", 10)
        total_vacantes = 0
        total_exitosos = 0
        total_fallidos = 0
        total_parciales = 0
        
        for reporte in queryset:
            p.drawString(50, y, reporte.business_unit.name)
            p.drawString(200, y, reporte.fecha.strftime("%d-%m-%Y"))
            p.drawString(300, y, str(reporte.vacantes_creadas))
            p.drawString(380, y, str(reporte.exitosos))
            p.drawString(440, y, str(reporte.fallidos))
            p.drawString(500, y, str(reporte.parciales))
            y -= 20
            
            # Acumular totales
            total_vacantes += reporte.vacantes_creadas
            total_exitosos += reporte.exitosos
            total_fallidos += reporte.fallidos
            total_parciales += reporte.parciales
            
            # Verificar si necesitamos una nueva página
            if y < 100:
                p.showPage()
                y = 750
                p.setFont("Helvetica-Bold", 12)
                p.drawString(50, y, "Business Unit")
                p.drawString(200, y, "Fecha")
                p.drawString(300, y, "Vacantes")
                p.drawString(380, y, "Éxitos")
                p.drawString(440, y, "Fallos")
                p.drawString(500, y, "Parciales")
                y -= 20
                p.line(50, y, 550, y)
                y -= 20
                p.setFont("Helvetica", 10)
        
        # Línea separadora para totales
        y -= 10
        p.line(50, y, 550, y)
        y -= 20
        
        # Totales
        p.setFont("Helvetica-Bold", 10)
        p.drawString(50, y, "TOTALES")
        p.drawString(300, y, str(total_vacantes))
        p.drawString(380, y, str(total_exitosos))
        p.drawString(440, y, str(total_fallidos))
        p.drawString(500, y, str(total_parciales))
        
        # Guardar PDF
        p.showPage()
        p.save()
        buffer.seek(0)
        
        # Devolver el PDF
        return FileResponse(buffer, as_attachment=True, filename="reporte_scraping.pdf")
        
    generar_reporte_pdf.short_description = "Generar reporte PDF de los seleccionados"
