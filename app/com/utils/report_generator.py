# /home/pablo/app/com/utils/report_generator.py
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import Image, Paragraph, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from pypdf import PdfMerger
import os
import requests
import tempfile
from django.conf import settings
import logging

# Logger setup
logger = logging.getLogger(__name__)

# Register the SF Pro Display font
try:
    font_path = os.path.join(settings.MEDIA_ROOT, 'fonts', 'SFPRODISPLAY.ttf')
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('SFProDisplay', font_path))
    else:
        # Try to use a default font if the specific font isn't found
        logger.warning(f"Font file not found at {font_path}, using default font instead")
        # No font registration, ReportLab will use default fonts
except Exception as e:
    logger.error(f"Error registering font: {str(e)}")
    # Continue without the custom font


# ReportGenerator class to wrap the functions for easier import and usage
class ReportGenerator:
    """Clase para generar reportes PDF."""
    
    @staticmethod
    def generate_analysis_page(group_logo_url, division_logo_url, analysis_data, output_path):
        """Genera una página de análisis PDF."""
        return generate_analysis_page(group_logo_url, division_logo_url, analysis_data, output_path)
    
    @staticmethod
    def generate_main_candidate_report(candidates, output_path):
        """Genera el reporte principal de candidatos."""
        return generate_main_candidate_report(candidates, output_path)

def generate_analysis_page(group_logo_url, division_logo_url, analysis_data, output_path):
    """
    Genera una página de análisis en PDF con los logos de grupo y división y los datos de análisis.
    """
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            group_logo_path = download_image(group_logo_url, os.path.join(temp_dir, 'group_logo.png'))
            division_logo_path = download_image(division_logo_url, os.path.join(temp_dir, 'division_logo.png'))

            c = canvas.Canvas(output_path, pagesize=A4)
            width, height = A4
            styles = getSampleStyleSheet()

            # Add group logo or placeholder text
            if group_logo_path and os.path.exists(group_logo_path):
                c.drawImage(group_logo_path, 10*mm, height - 30*mm, width=40*mm, preserveAspectRatio=True, mask='auto')
            else:
                c.setFont("SFProDisplay", 12)
                c.drawString(10*mm, height - 30*mm, "Logo Grupo huntRED® No Disponible")

            # Add division logo or placeholder text
            if division_logo_path and os.path.exists(division_logo_path):
                c.drawImage(division_logo_path, width - 50*mm, height - 30*mm, width=40*mm, preserveAspectRatio=True, mask='auto')
            else:
                c.setFont("SFProDisplay", 12)
                c.drawString(width - 50*mm, height - 30*mm, "Logo División No Disponible")

            # Title
            c.setFont("SFProDisplay", 16)
            c.drawCentredString(width / 2, height - 50*mm, "Reporte de Análisis de Candidatos")

            # Analysis sections
            y_position = height - 60*mm
            for section, content in analysis_data.items():
                # Section title
                c.setFont("SFProDisplay", 14)
                c.drawString(20*mm, y_position, f"{section.capitalize()}:")
                y_position -= 10*mm

                # Section content
                c.setFont("SFProDisplay", 12)
                if isinstance(content, list):
                    text = "\n".join(content)
                else:
                    text = content
                text_object = c.beginText(25*mm, y_position)
                text_object.textLines(text)
                c.drawText(text_object)
                y_position -= 15*mm

                # Page break if needed
                if y_position < 30*mm:
                    c.showPage()
                    y_position = height - 30*mm

            c.save()
            logger.info(f"Reporte de análisis generado en {output_path}")

    except Exception as e:
        logger.error(f"Error generando página de análisis: {e}")

def generate_main_candidate_report(candidates, output_path):
    """
    Genera el reporte principal de candidatos en PDF.
    
    :param candidates: QuerySet de candidatos a incluir en el reporte.
    :param output_path: Ruta donde se guardará el PDF generado.
    """
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    
    # Report title
    c.setFont("SFProDisplay", 16)
    c.drawCentredString(width / 2, height - 30*mm, "Listado de Candidatos")
    
    # Candidate table
    data = [["Nombre", "Email", "Teléfono", "Skills", "Divisiones"]]
    
    for person in candidates:
        name = f"{person.nombre} {person.apellido_paterno} {person.apellido_materno or ''}".strip()
        email = person.email or "No disponible"
        phone = person.phone or "No disponible"
        skills = ", ".join(person.metadata.get('skills', []))
        divisions = ", ".join(person.metadata.get('divisions', []))
        data.append([name, email, phone, skills, divisions])
    
    table = Table(data, colWidths=[50*mm, 50*mm, 30*mm, 60*mm, 60*mm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'SFProDisplay'),
        ('FONTSIZE', (0,0), (-1,0), 12),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
    ]))
    
    # Draw the table
    table.wrapOn(c, width, height)
    table.drawOn(c, 20*mm, height - 40*mm - (len(data) * 6 * mm))
    
    c.save()

def merge_pdfs(main_pdf_path, analysis_pdf_path, output_pdf_path):
    """
    Fusiona el reporte principal con la página de análisis usando pypdf.
    
    :param main_pdf_path: Ruta al reporte principal de candidatos.
    :param analysis_pdf_path: Ruta al PDF de análisis.
    :param output_pdf_path: Ruta donde se guardará el PDF final.
    """
    merger = PdfMerger()
    
    merger.append(main_pdf_path)
    merger.append(analysis_pdf_path)
    merger.write(output_pdf_path)
    merger.close()

def download_image(url, save_path):
    """
    Descarga una imagen desde una URL y la guarda en save_path.
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(save_path, 'wb') as out_file:
            for chunk in response.iter_content(chunk_size=8192):
                out_file.write(chunk)
        logger.info(f"Imagen descargada: {save_path}")
        return save_path
    except Exception as e:
        logger.error(f"Error descargando imagen desde {url}: {e}")
        return None