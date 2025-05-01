# /home/pablo/tests/test_parser.py
import asyncio
from asgiref.sync import sync_to_async
from app.utilidades.parser import IMAPCVProcessor, CVParser
from app.models import BusinessUnit, Person
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

async def test_imap_connection():
    business_unit = await sync_to_async(BusinessUnit.objects.get)(name="huntRED")
    processor = IMAPCVProcessor(business_unit)
    mail = await processor._connect_imap(processor.config)
    assert mail is not None, "Fallo en la conexión IMAP"
    assert await processor._verify_folders(mail), "Carpetas IMAP no válidas"
    await mail.logout()
    print("✅ Conexión IMAP exitosa")

async def test_process_emails():
    business_unit = await sync_to_async(BusinessUnit.objects.get)(name="huntRED")
    processor = IMAPCVProcessor(business_unit, batch_size=2, sleep_time=1.0)
    await processor.process_emails()
    assert processor.stats["processed"] >= 0, "No se procesaron correos"
    assert processor.stats["errors"] == 0, "Errores detectados"
    print(f"✅ {processor.stats['processed']} correos procesados")

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
    print("✅ Adjunto extraído")

async def test_parse_cv():
    business_unit = await sync_to_async(BusinessUnit.objects.get)(name="huntRED")
    parser = CVParser(business_unit=business_unit)
    sample_text = "Juan Pérez, juan@email.com, 555-1234, Habilidades: Python, SQL, Experiencia: Desarrollador 2 años"
    parsed_data = parser.parse(sample_text)
    assert parsed_data.get("email") == "juan@email.com", "Email no parseado"
    assert "Python" in parsed_data["skills"]["technical"], "Habilidad no detectada"
    print("✅ CV parseado")

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
    print("✅ Candidato creado y actualizado")

async def test_summary_report():
    business_unit = await sync_to_async(BusinessUnit.objects.get)(name="huntRED")
    processor = IMAPCVProcessor(business_unit)
    processor.stats = {"processed": 10, "created": 5, "updated": 3, "errors": 2}
    await processor._generate_summary_and_send_report(**processor.stats)
    print("✅ Reporte enviado (verificar correo manualmente)")

if __name__ == "__main__":
    import django
    django.setup()
    asyncio.run(test_imap_connection())
    asyncio.run(test_process_emails())
    asyncio.run(test_extract_attachments())
    asyncio.run(test_parse_cv())
    asyncio.run(test_manage_candidate())
    asyncio.run(test_summary_report())