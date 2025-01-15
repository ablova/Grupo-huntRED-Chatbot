# /home/pablollh/app/utilidades/report_generator.py

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import Image, Paragraph, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from PyPDF2 import PdfMerger
import os
import requests
import tempfile
from django.conf import settings
import logging



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

            # Añadir los logos
            if group_logo_path and os.path.exists(group_logo_path):
                c.drawImage(group_logo_path, 10*mm, height - 30*mm, width=40*mm, preserveAspectRatio=True, mask='auto')
            else:
                c.setFont("Helvetica-Bold", 12)
                c.drawString(10*mm, height - 30*mm, "Logo Grupo huntRED® No Disponible")

            if division_logo_path and os.path.exists(division_logo_path):
                c.drawImage(division_logo_path, width - 50*mm, height - 30*mm, width=40*mm, preserveAspectRatio=True, mask='auto')
            else:
                c.setFont("Helvetica-Bold", 12)
                c.drawString(width - 50*mm, height - 30*mm, "Logo División No Disponible")

            # Título
            c.setFont("Helvetica-Bold", 16)
            c.drawCentredString(width / 2, height - 50*mm, "Reporte de Análisis de Candidatos")

            # Secciones de análisis
            y_position = height - 60*mm
            for section, content in analysis_data.items():
                # Título de la sección
                c.setFont("Helvetica-Bold", 14)
                c.drawString(20*mm, y_position, f"{section.capitalize()}:")
                y_position -= 10*mm

                # Contenido
                c.setFont("Helvetica", 12)
                if isinstance(content, list):
                    text = "\n".join(content)
                else:
                    text = content
                text_object = c.beginText(25*mm, y_position)
                text_object.textLines(text)
                c.drawText(text_object)
                y_position -= 15*mm

                if y_position < 30*mm:
                    c.showPage()
                    y_position = height - 30*mm

            c.save()

            # Limpieza automática del directorio temporal
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
    
    # Título del reporte
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 30*mm, "Listado de Candidatos")
    
    # Tabla de candidatos
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
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('ALIGN',(0,0),(-1,-1),'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 12),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
    ]))
    
    # Calcular altura de la tabla
    table.wrapOn(c, width, height)
    table.drawOn(c, 20*mm, height - 40*mm - (len(data) * 6 * mm))
    
    c.save()

def merge_pdfs(main_pdf_path, analysis_pdf_path, output_pdf_path):
    """
    Fusiona el reporte principal con la página de análisis.
    
    :param main_pdf_path: Ruta al reporte principal de candidatos.
    :param analysis_pdf_path: Ruta al PDF de análisis.
    :param output_pdf_path: Ruta donde se guardará el PDF final.
    """
    merger = PdfMerger()
    
    # Añadir el reporte principal
    merger.append(main_pdf_path)
    
    # Añadir la página de análisis
    merger.append(analysis_pdf_path)
    
    # Guardar el PDF final
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