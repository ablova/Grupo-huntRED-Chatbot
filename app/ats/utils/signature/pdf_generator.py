# app/ats/utils/signature/pdf_generator.py
import os
import json
import datetime
import asyncio
from typing import Dict, List, Any, Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Image, Table, TableStyle
from pypdf import PdfMerger
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from django.core.files.storage import default_storage
from asgiref.sync import sync_to_async
from app.models import Person, BusinessUnit, SkillAssessment
# from app.ats.chatbot.validation import get_truth_analyzer

# Obtener la instancia del analizador cuando sea necesario
# truth_analyzer = get_truth_analyzer()

# Intentar registrar la fuente SF Pro Display; usar Helvetica si falla
FONT_NAME = "Helvetica"
try:
    font_path = "/home/pablo/media/fonts/SFPRODISPLAY.ttf"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('SFProDisplay', font_path))
        FONT_NAME = "SFProDisplay"
except Exception as e:
    print(f"Advertencia: No se pudo cargar la fuente SFProDisplay: {e}. Usando Helvetica.")

def draw_header(c, business_unit: BusinessUnit, title: str):
    """Dibuja el encabezado con los logos y el título del documento."""
    huntred_logo_path = "/home/pablo/media/Grupo_huntRED.png"
    bu_logo_path = f"/home/pablo/media/{business_unit.name.lower()}.png"
    
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
    signature_path = f"/home/pablo/app/media/firma_{candidate.id}.png"
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

async def generate_cv_pdf(candidate: Person, business_unit: BusinessUnit, html_template: str = "modern"):
    """
    Genera un CV en formato HTML y PDF para el candidato usando TruthSense™ y SocialVerify™.
    
    Args:
        candidate: Persona/candidato a generar el CV
        business_unit: Unidad de negocio (objeto BusinessUnit)
        html_template: Nombre de la plantilla HTML a utilizar
        
    Returns:
        Dict con rutas a los archivos generados HTML y PDF
    """
    try:
        from django.template.loader import render_to_string
        from django.core.files.base import ContentFile
        from weasyprint import HTML, CSS
        from django.conf import settings
        import tempfile
        
        # Formatear el contexto para la plantilla
        context = await format_cv_context(candidate, business_unit)
        
        # Renderizar HTML usando el motor de plantillas de Django
        template_path = f'cv_generator/{html_template}.html'
        html_content = await sync_to_async(render_to_string)(template_path, context)
        
        # Definir rutas de salida
        html_output_path = f"/tmp/{candidate.id}_{business_unit.name.lower()}_cv.html"
        pdf_output_path = f"/tmp/{candidate.id}_{business_unit.name.lower()}_cv.pdf"
        
        # Guardar HTML
        with open(html_output_path, 'w', encoding='utf-8') as html_file:
            html_file.write(html_content)
        
        # Convertir HTML a PDF usando WeasyPrint
        # Este proceso es CPU-intensivo, limitamos su uso con optimizaciones
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as temp_html:
            temp_html.write(html_content.encode('utf-8'))
            temp_html_path = temp_html.name
        
        # Definir CSS para optimizar la conversión
        css = CSS(string='''
        @page {
            size: A4;
            margin: 1cm;
        }
        @media print {
            body {
                font-size: 12pt;
            }
            .no-print {
                display: none;
            }
        }
        ''')
        
        # Usar una configuración de prioridad baja para WeasyPrint para optimizar CPU
        os.nice(10)  # Reducir la prioridad del proceso para evitar bloquear el sistema
        
        # Convertir a PDF (operación CPU-intensiva)
        # Notificando que se está optimizando el uso de CPU conforme a los requisitos
        print("Optimizando conversión HTML a PDF para bajo uso de CPU...")
        HTML(temp_html_path).write_pdf(pdf_output_path, stylesheets=[css])
        
        # Eliminar archivo temporal
        os.unlink(temp_html_path)
        
        # Guardar en almacenamiento por defecto (para acceso posterior)
        with open(pdf_output_path, "rb") as f:
            pdf_content = f.read()
            await sync_to_async(default_storage.save)(f"cvs/{candidate.id}_{business_unit.name.lower()}_cv.pdf", ContentFile(pdf_content))
        
        with open(html_output_path, "rb") as f:
            html_content_bytes = f.read()
            await sync_to_async(default_storage.save)(f"cvs/{candidate.id}_{business_unit.name.lower()}_cv.html", ContentFile(html_content_bytes))
        
        # Devolver rutas a los archivos generados
        return {
            'html_path': html_output_path,
            'pdf_path': pdf_output_path,
            'storage_path': f"cvs/{candidate.id}_{business_unit.name.lower()}_cv.pdf",
            'html_storage_path': f"cvs/{candidate.id}_{business_unit.name.lower()}_cv.html"
        }
        
    except ImportError as e:
        # Caer en modo de compatibilidad si WeasyPrint no está disponible
        print(f"Error de importación al generar CV: {str(e)}")
        return await generate_cv_pdf_legacy(candidate, business_unit)
    except Exception as e:
        print(f"Error generando CV para {candidate.name}: {str(e)}")
        # En caso de error, usar la versión legacy
        return await generate_cv_pdf_legacy(candidate, business_unit)

async def generate_cv_pdf_legacy(candidate: Person, business_unit: BusinessUnit):
    """Genera un CV en PDF para el candidato usando el método tradicional (ReportLab)."""
    output_path = f"/tmp/{candidate.id}_{business_unit.name.lower()}_cv.pdf"
    c = canvas.Canvas(output_path, pagesize=A4)
    
    # Encabezado
    draw_header(c, business_unit, f"Curriculum Vitae - {candidate.name if hasattr(candidate, 'name') else ''}")
    
    # Datos del candidato
    c.setFont(FONT_NAME, 16)
    c.drawString(10*mm, 240*mm, candidate.name if hasattr(candidate, 'name') else '')
    
    c.setFont(FONT_NAME, 12)
    if hasattr(candidate, 'headline') and candidate.headline:
        c.drawString(10*mm, 235*mm, candidate.headline)
    elif hasattr(candidate, 'current_position') and candidate.current_position:
        c.drawString(10*mm, 235*mm, candidate.current_position)
    
    # Datos de contacto
    contact_y = 225*mm
    c.drawString(10*mm, contact_y, f"Email: {candidate.email if hasattr(candidate, 'email') else ''}")
    contact_y -= 5*mm
    c.drawString(10*mm, contact_y, f"Teléfono: {candidate.phone if hasattr(candidate, 'phone') else ''}")
    contact_y -= 5*mm
    
    if hasattr(candidate, 'address') and candidate.address:
        c.drawString(10*mm, contact_y, f"Dirección: {candidate.address}")
        contact_y -= 5*mm
    
    # Línea separadora
    c.setStrokeColor('#000000')
    c.line(10*mm, contact_y - 2*mm, 200*mm, contact_y - 2*mm)
    
    # Resumen profesional
    if hasattr(candidate, 'summary') and candidate.summary:
        c.setFont(FONT_NAME, 14)
        summary_y = contact_y - 10*mm
        c.drawString(10*mm, summary_y, "Resumen Profesional")
        
        c.setFont(FONT_NAME, 10)
        summary_text = candidate.summary
        
        # Dividir por párrafos y mostrar el texto con alineación
        paragraphs = summary_text.split('\n')
        text_y = summary_y - 5*mm
        
        for para in paragraphs:
            text_y -= 5*mm
            c.drawString(15*mm, text_y, para)
        
        # Actualizar la posición Y después del resumen
        current_y = text_y - 10*mm
    else:
        current_y = contact_y - 10*mm
    
    # Experiencia profesional
    if hasattr(candidate, 'experience_set'):
        experiences = await sync_to_async(list)(candidate.experience_set.all())
        
        if experiences:
            c.setFont(FONT_NAME, 14)
            c.drawString(10*mm, current_y, "Experiencia Profesional")
            current_y -= 10*mm
            
            for experience in experiences:
                c.setFont(FONT_NAME, 12)
                c.drawString(15*mm, current_y, f"{experience.position} en {experience.company}")
                current_y -= 5*mm
                
                c.setFont(FONT_NAME, 10)
                date_str = f"{experience.start_date} - {experience.end_date if experience.end_date else 'Presente'}"
                c.drawString(15*mm, current_y, date_str)
                current_y -= 5*mm
                
                if experience.description:
                    c.setFont(FONT_NAME, 10)
                    lines = experience.description.split('\n')
                    for line in lines:
                        c.drawString(20*mm, current_y, line)
                        current_y -= 5*mm
                
                current_y -= 5*mm
    
    # Educación
    if hasattr(candidate, 'education_set'):
        educations = await sync_to_async(list)(candidate.education_set.all())
        
        if educations:
            c.setFont(FONT_NAME, 14)
            c.drawString(10*mm, current_y, "Educación")
            current_y -= 10*mm
            
            for education in educations:
                c.setFont(FONT_NAME, 12)
                degree_field = f"{education.degree}"
                if hasattr(education, 'field') and education.field:
                    degree_field += f" en {education.field}"
                c.drawString(15*mm, current_y, degree_field)
                current_y -= 5*mm
                
                c.setFont(FONT_NAME, 10)
                c.drawString(15*mm, current_y, education.institution)
                current_y -= 5*mm
                
                start_year = education.start_year if hasattr(education, 'start_year') else ''
                end_year = education.end_year if hasattr(education, 'end_year') and education.end_year else 'Presente'
                date_str = f"{start_year} - {end_year}"
                c.drawString(15*mm, current_y, date_str)
                current_y -= 10*mm
    
    # Habilidades
    if hasattr(candidate, 'skill_set'):
        skills = await sync_to_async(list)(candidate.skill_set.all())
        
        if skills:
            c.setFont(FONT_NAME, 14)
            c.drawString(10*mm, current_y, "Habilidades")
            current_y -= 10*mm
            
            c.setFont(FONT_NAME, 10)
            skill_text = ", ".join(skill.name for skill in skills)
            
            # Dividir las habilidades en líneas múltiples si es necesario
            max_width = 180*mm
            words = skill_text.split(', ')
            current_line = []
            
            for word in words:
                test_line = ', '.join(current_line + [word])
                if c.stringWidth(test_line, FONT_NAME, 10) <= max_width:
                    current_line.append(word)
                else:
                    c.drawString(15*mm, current_y, ', '.join(current_line))
                    current_y -= 5*mm
                    current_line = [word]
            
            if current_line:
                c.drawString(15*mm, current_y, ', '.join(current_line))
                current_y -= 10*mm
    
    # Gráfico de personalidad si está disponible
    if hasattr(candidate, 'extras') and 'personality_results' in candidate.extras:
        c.setFont(FONT_NAME, 14)
        c.drawString(10*mm, current_y, "Perfil de Personalidad")
        current_y -= 10*mm
        
        try:
            # Modificar para usar extras en lugar de metadata
            personality_data = candidate.extras['personality_results']
            traits = list(personality_data.keys())
            scores = list(personality_data.values())
            
            # Generar gráfico radar temporal
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
            
            c.drawImage(graph_path, 20*mm, current_y - 70*mm, width=160*mm, preserveAspectRatio=True)
            current_y -= 80*mm  # Espacio para el gráfico
            
            c.setFont(FONT_NAME, 10)
            for trait, score in personality_data.items():
                c.drawString(15*mm, current_y, f"{trait.capitalize()}: {score:.2f}")
                current_y -= 5*mm
                
            # Eliminar la imagen temporal
            if os.path.exists(graph_path):
                os.remove(graph_path)
                
        except Exception as e:
            c.drawString(15*mm, current_y, f"Error al generar gráfico de personalidad: {e}")
            current_y -= 10*mm
    
    # Añadir notificación de TruthSense™ si está disponible
    try:
        # Obtener datos de verificación (simplificados para la versión legacy)
        verification_data = await prepare_verification_data(candidate.id)
        truth_score = verification_data.get('truth_score', 0)
        
        if truth_score > 0:
            c.setFont(FONT_NAME, 8)
            c.drawString(10*mm, 30*mm, f"Perfil verificado por TruthSense™ - Puntuación: {truth_score}%")
            c.drawString(10*mm, 27*mm, f"Verificado el: {verification_data.get('verification_date', datetime.datetime.today().strftime('%d/%m/%Y'))}")
    except Exception as e:
        # No mostrar errores de verificación en el CV
        print(f"Error al incluir datos de TruthSense™: {e}")
    
    c.save()
    
    with open(output_path, "rb") as f:
        default_storage.save(f"cv/{candidate.id}.pdf", f)
    
    return output_path

def generate_contract_pdf(candidate: Person, client: Any, job_position: Any, business_unit: BusinessUnit):
    """Genera la Carta Propuesta con información del candidato y la vacante."""
    output_path = f"/tmp/{business_unit.name.lower()}_contracts/{candidate.id}.pdf"
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

async def prepare_verification_data(person_id: int) -> Dict:
    """
    Prepara los datos de verificación social para incluir en el CV.
    
    Args:
        person_id: ID del candidato
        
    Returns:
        Dict con datos de verificación para la plantilla
    """
    try:
        # Obtener el objeto Person
        # Usando sync_to_async para convertir operaciones síncronas de Django a asíncronas
        person = await sync_to_async(Person.objects.get)(id=person_id)
        
        # Obtener datos de verificación usando TruthSense™
        verification_data = await truth_analyzer.prepare_cv_verification_data(person)
        
        return verification_data
    except Exception as e:
        print(f"Error preparando datos de verificación: {e}")
        # Devolver datos por defecto en caso de error
        return {
            'truth_score': 0,
            'verification_date': datetime.datetime.now().strftime('%d/%m/%Y'),
            'show_verification': False,
            'social_verifications': [],
            'education_verifications': [],
            'experience_verifications': [],
            'social_connections': [],
            'social_connections_json': '[]',
            'person_id': str(person_id)
        }

async def format_cv_context(person: Person, business_unit: BusinessUnit) -> Dict:
    """
    Formatea el contexto completo para la generación de CV HTML.
    
    Args:
        person: Objeto Person del candidato
        business_unit: Unidad de negocio (objeto BusinessUnit)
        
    Returns:
        Dict con todo el contexto necesario para la plantilla HTML
    """
    # Preparar datos básicos del candidato
    context = {
        'name': person.name or '',
        'email': person.email or '',
        'phone': person.phone or '',
        'headline': person.headline or '',
        'summary': person.summary or '',
        'language': person.language or 'es',
        'business_unit': business_unit.name
    }
    
    # Añadir experiencias profesionales
    experiences = await sync_to_async(list)(person.experience_set.all().order_by('-id'))
    context['experience'] = [{
        'company': exp.company,
        'position': exp.position,
        'start_date': exp.start_date,
        'end_date': exp.end_date or 'Presente',
        'description': exp.description,
        'achievements': exp.achievements.split('\n') if exp.achievements else []
    } for exp in experiences]
    
    # Añadir educación
    education = await sync_to_async(list)(person.education_set.all().order_by('-end_year'))
    context['education'] = [{
        'institution': edu.institution,
        'degree': edu.degree,
        'field': edu.field,
        'start_year': edu.start_year,
        'end_year': edu.end_year or 'Presente',
        'grade': edu.grade,
        'description': edu.description
    } for edu in education]
    
    # Añadir habilidades
    skills = await sync_to_async(list)(person.skill_set.all())
    context['skills'] = [{
        'name': skill.name,
        'proficiency': skill.proficiency * 20 if skill.proficiency else 50,  # Convertir a porcentaje (0-100)
        'years_experience': skill.years_experience,
        'description': skill.description,
        'certification': skill.certification
    } for skill in skills]
    
    # Añadir idiomas
    languages = await sync_to_async(list)(person.language_set.all())
    context['languages'] = [{
        'language': lang.language,
        'level': lang.level,
        'level_percentage': {
            'Básico': 20,
            'Intermedio': 50,
            'Avanzado': 80,
            'Nativo': 100,
            'Básico': 20,
            'Intermedio': 50,
            'Avanzado': 80,
            'Nativo': 100,
            'Basic': 20,
            'Intermediate': 50,
            'Advanced': 80,
            'Native': 100
        }.get(lang.level, 50),
        'certificate': lang.certification
    } for lang in languages]
    
    # Añadir datos de verificación (TruthSense™, SocialVerify™ y SocialLink™)
    verification_data = await prepare_verification_data(person.id)
    context.update(verification_data)
    
    # Personalidad y metadata adicional
    if person.extras and 'personality_results' in person.extras:
        context['personality'] = person.extras['personality_results']
    
    # URLs para QR y logos
    context['profile_qr_code_url'] = f"/media/qr_codes/{person.id}.png"
    context['huntred_logo_url'] = f"/static/images/logo_huntred.png"
    context['business_unit_logo_url'] = f"/static/images/logo_{business_unit.name.lower()}.png"
    
    # Añadir traducciones según idioma
    context['translations'] = get_cv_translations(person.language or 'es')
    
    return context

def get_cv_translations(language: str = 'es') -> Dict:
    """
    Obtiene las traducciones para las secciones del CV según el idioma.
    
    Args:
        language: Código de idioma ('es', 'en')
        
    Returns:
        Dict con las traducciones
    """
    translations = {
        'es': {
            'education': 'Educación',
            'experience': 'Experiencia Profesional',
            'skills': 'Habilidades',
            'languages': 'Idiomas',
            'certificates': 'Certificaciones',
            'projects': 'Proyectos',
            'personality': 'Personalidad',
            'contact': 'Contacto',
            'grade': 'Calificación',
            'verification': 'Verificación',
            'social_connections': 'Conexiones Sociales'
        },
        'en': {
            'education': 'Education',
            'experience': 'Professional Experience',
            'skills': 'Skills',
            'languages': 'Languages',
            'certificates': 'Certifications',
            'projects': 'Projects',
            'personality': 'Personality',
            'contact': 'Contact',
            'grade': 'Grade',
            'verification': 'Verification',
            'social_connections': 'Social Connections'
        }
    }
    
    return translations.get(language, translations['es'])

def generate_personality_report(candidate: Person, business_unit: BusinessUnit):
    """Genera un reporte independiente de personalidad con gráfico de radar."""
    output_path = f"/tmp/{candidate.id}_personality_report.pdf"
    c = canvas.Canvas(output_path, pagesize=A4)
    
    # Encabezado
    draw_header(c, business_unit, f"Reporte de Personalidad - {candidate.full_name}")
    
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