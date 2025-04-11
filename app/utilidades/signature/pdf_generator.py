import os
import datetime
from fpdf import FPDF
from django.core.files.storage import default_storage
from PyPDF2 import PdfMerger
import matplotlib.pyplot as plt
import numpy as np

class PDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_font("SFPRODISPLAY", "", "/home/pablo/app/media/fonts/SFPRODISPLAY.ttf", uni=True)

    def header(self):
        """Encabezado con los logos de Grupo huntRED® y la Unidad de Negocio en cada página."""
        huntred_logo_path = "/home/pablo/app/media/Grupo_huntRED.png"
        bu_logo_path = f"/home/pablo/app/media/{self.business_unit.lower()}.png"

        if os.path.exists(huntred_logo_path):
            self.image(huntred_logo_path, 10, 8, 40)  # Grupo huntRED® (izquierda)

        if os.path.exists(bu_logo_path):
            self.image(bu_logo_path, 160, 8, 40)  # Unidad de Negocio (derecha)

        self.set_font("SFPRODISPLAY", "", 12)  
        self.cell(200, 10, self.title, ln=True, align="C")
        self.ln(10)

    def footer(self):
        """Pie de página con título del documento, Grupo huntRED® - Página X y fecha de creación."""
        self.set_y(-15)
        self.set_font("SFPRODISPLAY", "", 8)
        self.cell(70, 10, self.title, align="L")
        self.cell(60, 10, f"Grupo huntRED® - Página {self.page_no()}", align="C")
        creation_date = datetime.datetime.today().strftime("%d/%m/%Y")
        self.cell(70, 10, creation_date, align="R")

    def set_business_unit(self, business_unit):
        """Establece la unidad de negocio para usar su logo."""
        self.business_unit = business_unit

    def add_signature(self, candidate):
        """Añade la firma electrónica si está disponible."""
        signature_path = f"/home/pablo/app/media/firma_{candidate.id}.png"
        
        if os.path.exists(signature_path):
            self.image(signature_path, 60, self.get_y() + 10, 90)  # Tamaño y posición
            self.ln(25)
        else:
            self.cell(200, 10, "Firma Digital No Disponible", ln=True, align="C")
            self.ln(20)

def generate_personality_graph(candidate):
    """Genera un gráfico de radar para los resultados de personalidad."""
    traits = list(candidate.metadata['personality_results'].keys())
    scores = list(candidate.metadata['personality_results'].values())
    
    # Crear gráfico de radar
    num_traits = len(traits)
    angles = np.linspace(0, 2 * np.pi, num_traits, endpoint=False).tolist()
    angles += angles[:1]  # Cerrar el círculo
    scores += scores[:1]  # Repetir el primer valor para cerrar
    
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(projection='polar'))
    ax.plot(angles, scores, linewidth=2, linestyle='solid', color='blue')
    ax.fill(angles, scores, 'blue', alpha=0.3)  # Relleno suave
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(traits, fontsize=10)
    ax.set_title('Resultados de Personalidad', size=14, pad=20)
    ax.set_ylim(0, 5)  # Escala de 0 a 5 (ajustar según tus necesidades)
    
    # Guardar como imagen temporal
    graph_path = f"/tmp/{candidate.id}_personality_graph.png"
    plt.savefig(graph_path, bbox_inches='tight')
    plt.close()
    return graph_path

def generate_candidate_summary(candidate):
    """Genera un resumen del candidato en PDF."""
    pdf = PDF()
    pdf.set_business_unit("huntred")
    pdf.title = "Resumen del Candidato"
    pdf.add_page()
    pdf.set_font("SFPRODISPLAY", "", 12)

    pdf.cell(200, 10, f"Nombre: {candidate.full_name}", ln=True)
    pdf.cell(200, 10, f"Posición Aplicada: {candidate.position}", ln=True)
    pdf.cell(200, 10, f"Correo: {candidate.email}", ln=True)
    pdf.cell(200, 10, f"Teléfono: {candidate.phone}", ln=True)
    pdf.ln(10)

    file_path = f"candidate_summaries/{candidate.id}.pdf"
    full_path = os.path.join("/tmp", file_path)
    pdf.output(full_path)

    with open(full_path, "rb") as f:
        default_storage.save(file_path, f)

    return file_path

def generate_cv_pdf(candidate, business_unit):
    """
    Genera un CV en PDF para el candidato, incluyendo su información profesional y resultados de personalidad.
    Si el candidato ha subido un CV en huntRED® o huntu, se adjunta al final.
    """
    pdf = PDF()
    pdf.set_business_unit(business_unit)
    pdf.title = f"CV - {candidate.full_name}"
    pdf.add_page()
    pdf.set_font("SFPRODISPLAY", "", 12)

    # Datos personales
    pdf.set_font("SFPRODISPLAY", "B", 12)
    pdf.cell(200, 10, "Datos Personales", ln=True)
    pdf.set_font("SFPRODISPLAY", "", 12)
    pdf.cell(200, 10, f"Nombre: {candidate.full_name}", ln=True)
    pdf.cell(200, 10, f"Fecha de Nacimiento: {candidate.birth_date}", ln=True)
    pdf.cell(200, 10, f"Nacionalidad: {candidate.nationality}", ln=True)
    pdf.cell(200, 10, f"Teléfono: {candidate.phone}", ln=True)
    pdf.cell(200, 10, f"Correo Electrónico: {candidate.email}", ln=True)
    pdf.cell(200, 10, f"Dirección: {candidate.address}", ln=True)
    pdf.ln(10)

    # Resumen profesional
    if candidate.professional_summary:
        pdf.set_font("SFPRODISPLAY", "B", 12)
        pdf.cell(200, 10, "Resumen Profesional", ln=True)
        pdf.set_font("SFPRODISPLAY", "", 12)
        pdf.multi_cell(200, 10, candidate.professional_summary)
        pdf.ln(10)

    # Experiencia laboral
    pdf.set_font("SFPRODISPLAY", "B", 12)
    pdf.cell(200, 10, "Experiencia Laboral", ln=True)
    pdf.set_font("SFPRODISPLAY", "", 12)
    for job in candidate.work_experience:
        pdf.cell(200, 10, f"{job.company} - {job.position}", ln=True)
        pdf.cell(200, 10, f"Periodo: {job.start_date} - {job.end_date}", ln=True)
        pdf.multi_cell(200, 10, f"Responsabilidades: {job.responsibilities}")
        pdf.ln(5)
    pdf.ln(10)

    # Educación y certificaciones
    pdf.set_font("SFPRODISPLAY", "B", 12)
    pdf.cell(200, 10, "Educación y Certificaciones", ln=True)
    pdf.set_font("SFPRODISPLAY", "", 12)
    for edu in candidate.education:
        pdf.cell(200, 10, f"{edu.institution} - {edu.degree} ({edu.year_completed})", ln=True)
    pdf.ln(10)

    # Habilidades técnicas y blandas
    pdf.set_font("SFPRODISPLAY", "B", 12)
    pdf.cell(200, 10, "Habilidades Técnicas", ln=True)
    pdf.set_font("SFPRODISPLAY", "", 12)
    pdf.multi_cell(200, 10, ", ".join(candidate.hard_skills))
    pdf.ln(5)

    pdf.set_font("SFPRODISPLAY", "B", 12)
    pdf.cell(200, 10, "Habilidades Blandas", ln=True)
    pdf.set_font("SFPRODISPLAY", "", 12)
    pdf.multi_cell(200, 10, ", ".join(candidate.soft_skills))
    pdf.ln(10)

    # Idiomas
    if candidate.languages:
        pdf.set_font("SFPRODISPLAY", "B", 12)
        pdf.cell(200, 10, "Idiomas", ln=True)
        pdf.set_font("SFPRODISPLAY", "", 12)
        pdf.multi_cell(200, 10, ", ".join(candidate.languages))
        pdf.ln(10)

    # Resultados de personalidad
    if hasattr(candidate, 'metadata') and 'personality_results' in candidate.metadata:
        pdf.add_page()  # Nueva página para resultados
        pdf.set_font("SFPRODISPLAY", "B", 12)
        pdf.cell(200, 10, "Resultados de Prueba de Personalidad", ln=True)
        pdf.set_font("SFPRODISPLAY", "", 12)

        # Generar y añadir gráfico
        try:
            graph_path = generate_personality_graph(candidate)
            pdf.image(graph_path, x=10, y=pdf.get_y() + 10, w=180)
            pdf.ln(100)  # Espacio para el gráfico
            
            # Detalles textuales
            for trait, score in candidate.metadata['personality_results'].items():
                pdf.cell(200, 10, f"{trait.capitalize()}: {score:.2f}", ln=True)
            pdf.ln(10)
            
            # Limpiar archivo temporal
            if os.path.exists(graph_path):
                os.remove(graph_path)
        except Exception as e:
            pdf.cell(200, 10, f"Error al generar gráfico de personalidad: {e}", ln=True)

    # Integración del CV original
    if business_unit in ["huntred", "huntu"] and candidate.cv_file:
        original_cv_path = f"/home/pablo/app/media/cv/{candidate.cv_file}"
        if os.path.exists(original_cv_path):
            pdf.add_page()
            pdf.set_font("SFPRODISPLAY", "B", 12)
            pdf.cell(200, 10, "Anexo: CV Original del Candidato", ln=True)
            pdf.image(original_cv_path, x=10, y=pdf.get_y() + 10, w=180)
            pdf.ln(100)

    # Guardar el archivo
    file_path = f"cv/{candidate.id}.pdf"
    full_path = os.path.join("/tmp", file_path)
    pdf.output(full_path)

    with open(full_path, "rb") as f:
        default_storage.save(file_path, f)

    return file_path

def generate_contract_pdf(candidate, client, job_position, business_unit):
    """
    Genera la Carta Propuesta con información del candidato y la vacante.
    Incluye validación legal de firma electrónica.
    """
    pdf = PDF()
    pdf.set_business_unit(business_unit)
    pdf.title = f"Carta Propuesta - {job_position.title}"
    pdf.add_page()
    pdf.set_font("SFPRODISPLAY", "", 12)

    pdf.cell(200, 10, f"Empresa: {client.name}", ln=True)
    pdf.cell(200, 10, f"Posición: {job_position.title}", ln=True)
    pdf.cell(200, 10, f"Nombre del candidato: {candidate.full_name}", ln=True)
    pdf.cell(200, 10, f"Salario ofrecido: {job_position.salary} MXN", ln=True)
    pdf.cell(200, 10, f"Fecha de inicio: {job_position.start_date}", ln=True)
    pdf.ln(20)

    # Insertar la firma digital
    pdf.cell(200, 10, "Firma del Candidato:", ln=True)
    pdf.add_signature(candidate)

    pdf.cell(200, 10, "Firma del Representante de la Empresa: ________________________", ln=True)
    pdf.ln(20)

    # Datos de validación legal
    pdf.set_font("SFPRODISPLAY", "I", 8)
    pdf.cell(200, 10, f"ID de Firma: {candidate.signature_id}", ln=True)
    pdf.cell(200, 10, f"Fecha de Firma: {candidate.signature_date}", ln=True)
    pdf.cell(200, 10, f"IP del Firmante: {candidate.signature_ip}", ln=True)

    full_path = os.path.join("/tmp", f"{business_unit.lower()}_contracts/{candidate.id}.pdf")
    pdf.output(full_path)

    with open(full_path, "rb") as f:
        default_storage.save(full_path, f)

    return full_path

def merge_signed_documents(contract_path, signed_path):
    """
    Combina los documentos firmados en un solo PDF final.
    """
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
    """
    Genera un reporte independiente de personalidad con gráfico de radar.
    """
    pdf = PDF()
    pdf.set_business_unit(unidad_negocio)
    pdf.title = f"Reporte de Personalidad - {candidate.full_name}"
    pdf.add_page()
    pdf.set_font("SFPRODISPLAY", "", 12)

    # Título
    pdf.cell(200, 10, f"Reporte de Personalidad para {candidate.full_name}", ln=True)
    pdf.ln(10)

    # Resultados de personalidad
    if hasattr(candidate, 'metadata') and 'personality_results' in candidate.metadata:
        pdf.set_font("SFPRODISPLAY", "B", 12)
        pdf.cell(200, 10, "Resultados de Prueba de Personalidad", ln=True)
        pdf.set_font("SFPRODISPLAY", "", 12)

        # Generar y añadir gráfico
        try:
            graph_path = generate_personality_graph(candidate)
            pdf.image(graph_path, x=10, y=pdf.get_y() + 10, w=180)
            pdf.ln(100)  # Espacio para el gráfico
            
            # Detalles textuales
            for trait, score in candidate.metadata['personality_results'].items():
                pdf.cell(200, 10, f"{trait.capitalize()}: {score:.2f}", ln=True)
            pdf.ln(10)
            
            # Limpiar archivo temporal
            if os.path.exists(graph_path):
                os.remove(graph_path)
        except Exception as e:
            pdf.cell(200, 10, f"Error al generar gráfico de personalidad: {e}", ln=True)

    # Guardar el reporte
    report_path = f"/tmp/{candidate.id}_personality_report.pdf"
    pdf.output(report_path)
    return report_path