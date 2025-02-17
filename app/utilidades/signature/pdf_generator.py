import os
import datetime
from fpdf import FPDF
from django.core.files.storage import default_storage

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

        # Título del documento a la izquierda
        self.cell(70, 10, self.title, align="L")

        # Grupo huntRED® - Página X al centro
        self.cell(60, 10, f"Grupo huntRED® - Página {self.page_no()}", align="C")

        # Fecha de creación a la derecha
        creation_date = datetime.datetime.today().strftime("%d/%m/%Y")
        self.cell(70, 10, creation_date, align="R")

    def set_business_unit(self, business_unit):
        """Establece la unidad de negocio para usar su logo"""
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

def generate_candidate_summary(candidate):
    """
    Genera un resumen del candidato en PDF.
    """
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

def generate_contract_pdf(candidate, client, job_position, business_unit):
    """
    Genera la Carta Propuesta con información del candidato y la vacante.
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