# /home/pablollh/app/utilidades/signature/pdf_generator.py
import os
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfMerger
import matplotlib.pyplot as plt
import numpy as np
from django.core.files.storage import default_storage

# Intentar registrar la fuente SF Pro Display; usar Helvetica si falla
FONT_NAME = "Helvetica"
try:
    font_path = "/home/pablollh/media/fonts/SFPRODISPLAY.ttf"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('SFProDisplay', font_path))
        FONT_NAME = "SFProDisplay"
except Exception as e:
    print(f"Advertencia: No se pudo cargar la fuente SFProDisplay: {e}. Usando Helvetica.")

def draw_header(c, business_unit, title):
    """Dibuja el encabezado con los logos y el título del documento."""
    huntred_logo_path = "/home/pablollh/media/Grupo_huntRED.png"
    bu_logo_path = f"/home/pablollh/media/{business_unit.lower()}.png"
    
    # Logo de huntRED® a la izquierda
    if os.path.exists(huntred_logo_path):
        c.drawImage(huntred_logo_path, 10*mm, 260*mm, width=40*mm, preserveAspectRatio=True)
    
    # Logo de la unidad de negocio a la derecha
    if os.path.exists(bu_logo_path):
        c.drawImage(bu_logo_path, 160*mm, 260*mm, width=40*mm, preserveAspectRatio=True)
    
    # Título centrado
    c.setFont(FONT_NAME, 12)
    c.drawCentredString(105*mm, 250*mm, title)

def draw_footer(c, page_num, title):
    """Dibuja el pie de página con el título, número de página y fecha."""
    c.setFont(FONT_NAME, 8)
    c.drawString(10*mm, 10*mm, title)
    c.drawCentredString(105*mm, 10*mm, f"Grupo huntRED® - Página {page_num}")
    creation_date = datetime.datetime.today().strftime("%d/%m/%Y")
    c.drawRightString(200*mm, 10*mm, creation_date)

def add_signature(c, candidate, y_position):
    """Añade la firma electrónica si está disponible."""
    signature_path = f"/home/pablollh/app/media/firma_{candidate.id}.png"
    if os.path.exists(signature_path):
        c.drawImage(signature_path, 60*mm, y_position, width=90*mm, preserveAspectRatio=True)
        return y_position - 25*mm
    else:
        c.drawString(60*mm, y_position, "Firma Digital No Disponible")
        return y_position - 20*mm

def generate_personality_graph(candidate):
    """Genera un gráfico de radar para los resultados de personalidad."""
    traits = list(candidate.metadata['personality_results'].keys())
    scores = list(candidate.metadata['personality_results'].values())
    
    num_traits = len(traits)
    angles = np.linspace(0, 2 * np.pi, num_traits, endpoint=False).tolist()
    angles += angles[:1]
    scores += scores[:1]
    
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(projection='polar'))
    ax.plot(angles, scores, linewidth=2, linestyle='solid', color='blue')
    ax.fill(angles, scores, 'blue', alpha=0.3)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(traits, fontsize=10)
    ax.set_title('Resultados de Personalidad', size=14, pad=20)
    ax.set_ylim(0, 5)
    
    graph_path = f"/tmp/{candidate.id}_personality_graph.png"
    plt.savefig(graph_path, bbox_inches='tight')
    plt.close()
    return graph_path

def generate_candidate_summary(candidate):
    """Genera un resumen del candidato en PDF."""
    output_path = f"/tmp/candidate_summaries/{candidate.id}.pdf"
    c = canvas.Canvas(output_path, pagesize=A4)
    
    # Encabezado
    draw_header(c, "huntred", "Resumen del Candidato")
    
    # Contenido
    c.setFont(FONT_NAME, 12)
    c.drawString(10*mm, 240*mm, f"Nombre: {candidate.full_name}")
    c.drawString(10*mm, 230*mm, f"Posición Aplicada: {candidate.position}")
    c.drawString(10*mm, 220*mm, f"Correo: {candidate.email}")
    c.drawString(10*mm, 210*mm, f"Teléfono: {candidate.phone}")
    
    # Pie de página
    draw_footer(c, 1, "Resumen del Candidato")
    
    c.save()
    
    with open(output_path, "rb") as f:
        default_storage.save(f"candidate_summaries/{candidate.id}.pdf", f)
    
    return output_path

def generate_cv_pdf(candidate, business_unit):
    """Genera un CV en PDF para el candidato, incluyendo información profesional y personalidad."""
    output_path = f"/tmp/cv/{candidate.id}.pdf"
    c = canvas.Canvas(output_path, pagesize=A4)
    page_num = 1
    
    # Encabezado
    draw_header(c, business_unit, f"CV - {candidate.full_name}")
    
    # Datos personales
    c.setFont(FONT_NAME, 14)
    c.drawString(10*mm, 240*mm, "Datos Personales")
    c.setFont(FONT_NAME, 12)
    y_position = 230*mm
    c.drawString(10*mm, y_position, f"Nombre: {candidate.full_name}")
    y_position -= 10*mm
    c.drawString(10*mm, y_position, f"Fecha de Nacimiento: {candidate.birth_date}")
    y_position -= 10*mm
    c.drawString(10*mm, y_position, f"Nacionalidad: {candidate.nationality}")
    y_position -= 10*mm
    c.drawString(10*mm, y_position, f"Teléfono: {candidate.phone}")
    y_position -= 10*mm
    c.drawString(10*mm, y_position, f"Correo Electrónico: {candidate.email}")
    y_position -= 10*mm
    c.drawString(10*mm, y_position, f"Dirección: {candidate.address}")
    y_position -= 20*mm
    
    # Resumen profesional
    if candidate.professional_summary:
        c.setFont(FONT_NAME, 14)
        c.drawString(10*mm, y_position, "Resumen Profesional")
        y_position -= 10*mm
        c.setFont(FONT_NAME, 12)
        text = c.beginText(10*mm, y_position)
        text.textLines(candidate.professional_summary)
        c.drawText(text)
        y_position -= 20*mm
    
    # Experiencia laboral
    c.setFont(FONT_NAME, 14)
    c.drawString(10*mm, y_position, "Experiencia Laboral")
    y_position -= 10*mm
    c.setFont(FONT_NAME, 12)
    for job in candidate.work_experience:
        c.drawString(10*mm, y_position, f"{job.company} - {job.position}")
        y_position -= 10*mm
        c.drawString(10*mm, y_position, f"Periodo: {job.start_date} - {job.end_date}")
        y_position -= 10*mm
        text = c.beginText(10*mm, y_position)
        text.textLines(f"Responsabilidades: {job.responsibilities}")
        c.drawText(text)
        y_position -= 15*mm
    
    # Educación y certificaciones
    c.setFont(FONT_NAME, 14)
    c.drawString(10*mm, y_position, "Educación y Certificaciones")
    y_position -= 10*mm
    c.setFont(FONT_NAME, 12)
    for edu in candidate.education:
        c.drawString(10*mm, y_position, f"{edu.institution} - {edu.degree} ({edu.year_completed})")
        y_position -= 10*mm
    
    # Habilidades técnicas y blandas
    y_position -= 10*mm
    c.setFont(FONT_NAME, 14)
    c.drawString(10*mm, y_position, "Habilidades Técnicas")
    y_position -= 10*mm
    c.setFont(FONT_NAME, 12)
    text = c.beginText(10*mm, y_position)
    text.textLines(", ".join(candidate.hard_skills))
    c.drawText(text)
    y_position -= 10*mm
    
    c.setFont(FONT_NAME, 14)
    c.drawString(10*mm, y_position, "Habilidades Blandas")
    y_position -= 10*mm
    c.setFont(FONT_NAME, 12)
    text = c.beginText(10*mm, y_position)
    text.textLines(", ".join(candidate.soft_skills))
    c.drawText(text)
    y_position -= 20*mm
    
    # Idiomas
    if candidate.languages:
        c.setFont(FONT_NAME, 14)
        c.drawString(10*mm, y_position, "Idiomas")
        y_position -= 10*mm
        c.setFont(FONT_NAME, 12)
        text = c.beginText(10*mm, y_position)
        text.textLines(", ".join(candidate.languages))
        c.drawText(text)
        y_position -= 20*mm
    
    # Pie de página
    draw_footer(c, page_num, f"CV - {candidate.full_name}")
    
    # Resultados de personalidad (nueva página)
    if hasattr(candidate, 'metadata') and 'personality_results' in candidate.metadata:
        c.showPage()
        page_num += 1
        draw_header(c, business_unit, f"CV - {candidate.full_name}")
        c.setFont(FONT_NAME, 14)
        c.drawString(10*mm, 240*mm, "Resultados de Prueba de Personalidad")
        c.setFont(FONT_NAME, 12)
        try:
            graph_path = generate_personality_graph(candidate)
            c.drawImage(graph_path, 10*mm, 140*mm, width=180*mm, preserveAspectRatio=True)
            y_position = 120*mm
            for trait, score in candidate.metadata['personality_results'].items():
                c.drawString(10*mm, y_position, f"{trait.capitalize()}: {score:.2f}")
                y_position -= 10*mm
            if os.path.exists(graph_path):
                os.remove(graph_path)
        except Exception as e:
            c.drawString(10*mm, 120*mm, f"Error al generar gráfico de personalidad: {e}")
        draw_footer(c, page_num, f"CV - {candidate.full_name}")
    
    # Integración del CV original (nueva página)
    if business_unit in ["huntred", "huntu"] and candidate.cv_file:
        original_cv_path = f"/home/pablollh/app/media/cv/{candidate.cv_file}"
        if os.path.exists(original_cv_path):
            c.showPage()
            page_num += 1
            draw_header(c, business_unit, f"CV - {candidate.full_name}")
            c.setFont(FONT_NAME, 14)
            c.drawString(10*mm, 240*mm, "Anexo: CV Original del Candidato")
            c.drawImage(original_cv_path, 10*mm, 140*mm, width=180*mm, preserveAspectRatio=True)
            draw_footer(c, page_num, f"CV - {candidate.full_name}")
    
    c.save()
    
    with open(output_path, "rb") as f:
        default_storage.save(f"cv/{candidate.id}.pdf", f)
    
    return output_path

def generate_contract_pdf(candidate, client, job_position, business_unit):
    """Genera la Carta Propuesta con información del candidato y la vacante."""
    output_path = f"/tmp/{business_unit.lower()}_contracts/{candidate.id}.pdf"
    c = canvas.Canvas(output_path, pagesize=A4)
    
    # Encabezado
    draw_header(c, business_unit, f"Carta Propuesta - {job_position.title}")
    
    # Contenido
    c.setFont(FONT_NAME, 12)
    y_position = 240*mm
    c.drawString(10*mm, y_position, f"Empresa: {client.name}")
    y_position -= 10*mm
    c.drawString(10*mm, y_position, f"Posición: {job_position.title}")
    y_position -= 10*mm
    c.drawString(10*mm, y_position, f"Nombre del candidato: {candidate.full_name}")
    y_position -= 10*mm
    c.drawString(10*mm, y_position, f"Salario ofrecido: {job_position.salary} MXN")
    y_position -= 10*mm
    c.drawString(10*mm, y_position, f"Fecha de inicio: {job_position.start_date}")
    y_position -= 20*mm
    
    # Firma del Candidato
    c.drawString(10*mm, y_position, "Firma del Candidato:")
    y_position -= 10*mm
    y_position = add_signature(c, candidate, y_position)
    
    # Firma del Representante
    c.drawString(10*mm, y_position, "Firma del Representante de la Empresa: ________________________")
    y_position -= 20*mm
    
    # Datos de validación legal
    c.setFont(FONT_NAME, 8)
    c.drawString(10*mm, y_position, f"ID de Firma: {candidate.signature_id}")
    y_position -= 10*mm
    c.drawString(10*mm, y_position, f"Fecha de Firma: {candidate.signature_date}")
    y_position -= 10*mm
    c.drawString(10*mm, y_position, f"IP del Firmante: {candidate.signature_ip}")
    
    # Pie de página
    draw_footer(c, 1, f"Carta Propuesta - {job_position.title}")
    
    c.save()
    
    with open(output_path, "rb") as f:
        default_storage.save(output_path, f)
    
    return output_path

def merge_signed_documents(contract_path, signed_path):
    """Combina los documentos firmados en un solo PDF final."""
    merger = PdfMerger()
    
    try:
        if os.path.exists(contract_path):
            merger.append(contract_path)
        
        signed_files = [
            f"{contract_path}_signed_candidate.pdf",
            f"{contract_path}_signed_client.pdf"
        ]
        
        for signed_file in signed_files:
            if os.path.exists(signed_file):
                merger.append(signed_file)
        
        merger.write(signed_path)
        merger.close()
        
        with open(signed_path, "rb") as f:
            default_storage.save(signed_path, f)
        
        return signed_path
    
    except Exception as e:
        return f"Error al combinar documentos firmados: {e}"

def generate_personality_report(candidate, unidad_negocio):
    """Genera un reporte independiente de personalidad con gráfico de radar."""
    output_path = f"/tmp/{candidate.id}_personality_report.pdf"
    c = canvas.Canvas(output_path, pagesize=A4)
    
    # Encabezado
    draw_header(c, unidad_negocio, f"Reporte de Personalidad - {candidate.full_name}")
    
    # Título
    c.setFont(FONT_NAME, 12)
    c.drawString(10*mm, 240*mm, f"Reporte de Personalidad para {candidate.full_name}")
    
    # Resultados de personalidad
    if hasattr(candidate, 'metadata') and 'personality_results' in candidate.metadata:
        c.setFont(FONT_NAME, 14)
        c.drawString(10*mm, 230*mm, "Resultados de Prueba de Personalidad")
        c.setFont(FONT_NAME, 12)
        try:
            graph_path = generate_personality_graph(candidate)
            c.drawImage(graph_path, 10*mm, 130*mm, width=180*mm, preserveAspectRatio=True)
            y_position = 110*mm
            for trait, score in candidate.metadata['personality_results'].items():
                c.drawString(10*mm, y_position, f"{trait.capitalize()}: {score:.2f}")
                y_position -= 10*mm
            if os.path.exists(graph_path):
                os.remove(graph_path)
        except Exception as e:
            c.drawString(10*mm, 110*mm, f"Error al generar gráfico de personalidad: {e}")
    
    # Pie de página
    draw_footer(c, 1, f"Reporte de Personalidad - {candidate.full_name}")
    
    c.save()
    return output_path