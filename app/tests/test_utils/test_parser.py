# /home/pablo/test/test_parser.py
import pytest
from unittest.mock import AsyncMock, patch
from asgiref.sync import sync_to_async
from app.ats.utils.parser import IMAPCVProcessor, CVParser
from app.models import BusinessUnit, Person
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

@pytest.mark.django_db
@pytest.mark.asyncio
async def test_imap_connection():
    business_unit = await sync_to_async(BusinessUnit.objects.get)(name="huntRED")
    processor = IMAPCVProcessor(business_unit)
    with patch('app.utilidades.parser.aioimaplib.IMAP4_SSL', new_callable=AsyncMock) as mock_imap:
        mock_imap.return_value.wait_hello_from_server = AsyncMock()
        mock_imap.return_value.login = AsyncMock()
        mock_imap.return_value.select = AsyncMock(return_value=("OK", [b"1"]))
        mail = await processor._connect_imap(processor.config)
        assert mail is not None, "Fallo en la conexión IMAP"
        assert await processor._verify_folders(mail), "Carpetas IMAP no válidas"
        await mail.logout()

@pytest.mark.django_db
@pytest.mark.asyncio
async def test_process_emails():
    business_unit = await sync_to_async(BusinessUnit.objects.get)(name="huntRED")
    processor = IMAPCVProcessor(business_unit, batch_size=2, sleep_time=1.0)
    with patch('app.utilidades.parser.IMAPCVProcessor._connect_imap', new_callable=AsyncMock) as mock_connect:
        with patch('app.utilidades.parser.IMAPCVProcessor.process_email_batch', new_callable=AsyncMock) as mock_process:
            mock_connect.return_value = AsyncMock()
            mock_process.return_value = None
            await processor.process_emails()
            assert processor.stats["processed"] >= 0, "No se procesaron correos"
            assert processor.stats["errors"] == 0, "Errores detectados"

@pytest.mark.asyncio
async def test_extract_attachments():
    msg = MIMEMultipart()
    attachment = MIMEBase('application', 'pdf')
    attachment.set_payload(b"Sample PDF content")
    encoders.encode_base64(attachment)
    attachment.add_header('Content-Disposition', 'attachment', filename='test.pdf')
    msg.attach(attachment)
    business_unit = await sync_to_async(BusinessUnit.objects.get)(name="huntRED")
    parser = CVParser(business_unit=business_unit)
    attachments = parser.extract_attachments(msg)
    assert len(attachments) == 1, "No se extrajo el adjunto"
    assert attachments[0]['filename'] == 'test.pdf', "Nombre de archivo incorrecto"

@pytest.mark.django_db
@pytest.mark.asyncio
async def test_parse_cv():
    business_unit = await sync_to_async(BusinessUnit.objects.get)(name="huntRED")
    parser = CVParser(business_unit=business_unit)
    sample_text = "Juan Pérez, juan@email.com, 555-1234, Habilidades: Python, SQL, Experiencia: Desarrollador 2 años"
    parsed_data = parser.parse(sample_text)
    assert parsed_data.get("email") == "juan@email.com", "Email no parseado"
    assert "Python" in parsed_data["skills"]["technical"], "Habilidad no detectada"

@pytest.mark.django_db
@pytest.mark.asyncio
async def test_manage_candidate():
    business_unit = await sync_to_async(BusinessUnit.objects.get)(name="huntRED")
    parser = CVParser(business_unit=business_unit)
    parsed_data = {
        "email": "juan@email.com",
        "phone": "555-1234",
        "skills": {"technical": ["Python"], "soft": ["Comunicación"]},
        "experience": [{"role": "Desarrollador", "years": 2}],
        "education": [{"degree": "Ingeniería"}],
        "sentiment": "positive"
    }
    temp_path = Path("/tmp/test_cv.pdf")
    temp_path.write_bytes(b"Sample PDF")
    
    # Crear nuevo candidato
    await parser._create_new_candidate(parsed_data, temp_path)
    candidate = await sync_to_async(Person.objects.filter(email="juan@email.com").first)()
    assert candidate, "Candidato no creado"
    assert candidate.cv_parsed, "CV no marcado como parseado"
    
    # Actualizar candidato
    parsed_data["skills"]["technical"].append("SQL")
    await parser._update_candidate(candidate, parsed_data, temp_path)
    updated_candidate = await sync_to_async(Person.objects.filter(email="juan@email.com").first)()
    assert "SQL" in updated_candidate.metadata["skills"]["technical"], "Habilidad no actualizada"

@pytest.mark.django_db
@pytest.mark.asyncio
async def test_summary_report():
    business_unit = await sync_to_async(BusinessUnit.objects.get)(name="huntRED")
    processor = IMAPCVProcessor(business_unit)
    processor.stats = {"processed": 10, "created": 5, "updated": 3, "errors": 2}
    with patch('app.utilidades.parser.send_email', new_callable=AsyncMock) as mock_send_email:
        await processor._generate_summary_and_send_report(**processor.stats)
        mock_send_email.assert_called_once()

import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from bs4 import BeautifulSoup
from app.models import BusinessUnit, Vacante
from app.ats.utils.parser import parse_job_listing, extract_url, save_job_to_vacante

import logging

logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_parse_job_listing_web():
    """Test parsing job listing from web content."""
    sample_html = """
    <html>
        <body>
            <h1 class="job-title">Software Engineer</h1>
            <span class="company">Tech Corp</span>
            <div class="description">Develop and maintain software solutions.</div>
            <a href="/apply">Apply Now</a>
        </body>
    </html>
    """
    job_info = parse_job_listing(sample_html, "https://example.com/job", source_type="web")
    assert job_info is not None
    assert job_info["title"] == "Software Engineer"
    assert job_info["company"] == "Tech Corp"
    assert "Develop and maintain" in job_info["description"]
    assert job_info["url"] == "https://example.com/apply"
    assert job_info["source"] == "example.com"
    logger.info("Parse job listing from web test passed")

@pytest.mark.asyncio
async def test_parse_job_listing_email():
    """Test parsing job listing from email content."""
    sample_email = """
    <html>
        <head><title>Job Opportunity</title></head>
        <body>
            <p>From: Hiring Manager</p>
            <p>We have an opening for a Project Manager.</p>
            <p>Visit https://careers.example.com for details.</p>
        </body>
    </html>
    """
    job_info = parse_job_listing(sample_email, "", source_type="email")
    assert job_info is not None
    assert job_info["title"] == "Job Opportunity"
    assert job_info["company"] == "From: Hiring Manager"
    assert "We have an opening" in job_info["description"]
    assert job_info["url"] == "https://careers.example.com"
    assert job_info["source"] == "Email Scraping"
    logger.info("Parse job listing from email test passed")

@pytest.mark.asyncio
async def test_parse_job_listing_no_keywords():
    """Test parsing job listing with no relevant keywords."""
    sample_html = """
    <html>
        <body>
            <h1 class="job-title">Office Supplies Sale</h1>
            <span class="company">Office Depot</span>
            <div class="description">Discount on office supplies.</div>
        </body>
    </html>
    """
    job_info = parse_job_listing(sample_html, "https://example.com/sale", source_type="web")
    assert job_info is None
    logger.info("Parse job listing with no keywords test passed")

@pytest.mark.asyncio
async def test_extract_url():
    """Test extracting URL from text content."""
    text = "Visit our site at https://example.com/careers for more info."
    url = extract_url(text)
    assert url == "https://example.com/careers"
    logger.info("Extract URL test passed")

@pytest.mark.asyncio
async def test_extract_url_no_url():
    """Test extracting URL when no URL is present."""
    text = "Visit our site for more info."
    url = extract_url(text)
    assert url == ""
    logger.info("Extract URL with no URL test passed")

@pytest.mark.asyncio
async def test_save_job_to_vacante():
    """Test saving parsed job info to Vacante model."""
    job_info = {
        "title": "Test Job",
        "company": "Test Company",
        "description": "Test Description",
        "url": "https://example.com/job",
        "source": "Test Source"
    }
    bu = BusinessUnit(name="test_bu")
    with patch('app.models.Vacante.save', new=AsyncMock):
        vacante = await save_job_to_vacante(job_info, bu)
        assert vacante is not None
        logger.info("Save job to Vacante test passed")

@pytest.mark.asyncio
async def test_save_job_to_vacante_error():
    """Test error handling when saving to Vacante model."""
    job_info = {
        "title": "Test Job",
        "company": "Test Company",
        "description": "Test Description",
        "url": "https://example.com/job",
        "source": "Test Source"
    }
    bu = BusinessUnit(name="test_bu")
    with patch('app.models.Vacante.save', new=AsyncMock(side_effect=Exception("Save failed"))):
        vacante = await save_job_to_vacante(job_info, bu)
        assert vacante is None
        logger.info("Save job to Vacante error handling test passed")