# /home/pablo/tests/test_email_scraper.py
import asyncio
from django.utils import timezone
from unittest.mock import AsyncMock, patch
from asgiref.sync import sync_to_async
from app.utilidades.email_scraper import EmailScraperV2, SystemHealthMonitor
from app.models import Vacante, Worker
import logging

logger = logging.getLogger(__name__)

async def test_imap_connection():
    scraper = EmailScraperV2()
    mail = await scraper.connect()
    assert mail is not None, "Fallo en la conexión IMAP"
    assert await scraper.ensure_connection(), "Conexión no estable"
    await scraper.mail.logout()
    print("✅ Conexión IMAP exitosa")

async def test_fetch_email():
    scraper = EmailScraperV2()
    await scraper.connect()
    resp, data = await scraper.mail.search("ALL")
    email_ids = data[0].decode().split()[:1]
    if email_ids:
        message = await scraper.fetch_email(email_ids[0])
        assert message is not None, "No se pudo obtener el correo"
        assert message.get("Subject"), "Correo sin asunto"
        print(f"✅ Correo {email_ids[0]} obtenido: {message.get('Subject')}")
    else:
        print("ℹ️ No hay correos para probar")
    await scraper.mail.logout()

async def test_process_job_alert_email():
    scraper = EmailScraperV2()
    await scraper.connect()
    resp, data = await scraper.mail.search("ALL")
    email_ids = data[0].decode().split()[:1]
    if email_ids:
        vacancies = await scraper.process_job_alert_email(email_ids[0])
        assert isinstance(vacancies, list), "Vacantes no retornadas como lista"
        if vacancies:
            assert vacancies[0]["titulo"], "Vacante sin título"
            print(f"✅ {len(vacancies)} vacantes extraídas del correo {email_ids[0]}")
        else:
            print("ℹ️ No se encontraron vacantes en el correo")
    else:
        print("ℹ️ No hay correos para probar")
    await scraper.mail.logout()

async def test_extract_vacancies():
    scraper = EmailScraperV2()
    sample_html = """
    <div>
        <a href="https://www.linkedin.com/jobs/view/123">Analista de Datos</a>
        <span class="company">Acme Corp</span>
        <span>Ciudad de México</span>
    </div>
    """
    vacancies = await scraper.extract_vacancies_from_html(sample_html)
    assert len(vacancies) > 0, "No se extrajeron vacantes"
    assert vacancies[0]["titulo"] == "Analista De Datos", "Título incorrecto"
    assert vacancies[0]["empresa"], "Empresa no asignada"
    print(f"✅ {len(vacancies)} vacantes extraídas")

async def test_scrape_vacancy_details():
    with patch('app.utilidades.email_scraper.EmailScraperV2.fetch_html', new_callable=AsyncMock) as mock_fetch_html, \
         patch('app.utilidades.scraping.ScrapingPipeline.process', new_callable=AsyncMock) as mock_process:
        mock_fetch_html.return_value = """
        <h1>Analista de Datos</h1>
        <div class="description">Descripción detallada</div>
        """
        # Mock pipeline.process to return a list with enriched data
        mock_process.return_value = [{
            "title": "Analista de Datos",
            "description": "Descripción detallada",
            "location": "No especificada",
            "company": "Unknown",
            "url": "https://www.linkedin.com/jobs/view/123",
            "posted_date": timezone.now().isoformat(),
            "skills": [],
            "salary": None,
            "job_type": None,
            "contract_type": None,
            "benefits": []
        }]
        scraper = EmailScraperV2()
        job_data = {
            "url_original": "https://www.linkedin.com/jobs/view/123",
            "titulo": "Analista",
            "empresa": None,
            "ubicacion": "No especificada",
            "descripcion": "",
            "fecha_publicacion": timezone.now()
        }
        enriched_job = await scraper.scrape_vacancy_details_from_url(job_data)
        assert enriched_job["titulo"] == "Analista de Datos", "Título no enriquecido"
        assert enriched_job["descripcion"] == "Descripción detallada", "Descripción no enriquecida"
        print("✅ Vacante enriquecida")

async def test_save_vacante():
    scraper = EmailScraperV2()
    job_data = {
        "url_original": "https://www.linkedin.com/jobs/view/test123",
        "titulo": "Prueba Analista",
        "empresa": (await sync_to_async(Worker.objects.get_or_create)(name="Acme", defaults={"company": "Acme"}))[0],
        "ubicacion": "CDMX",
        "descripcion": "Descripción de prueba",
        "modalidad": "Remoto",
        "requisitos": "Python, SQL",
        "beneficios": "Seguro",
        "skills_required": ["Python"],
        "salario": 20000.0,
        "fecha_publicacion": timezone.now()
    }
    success = await scraper.save_or_update_vacante(job_data)
    assert success, "Fallo al guardar vacante"
    vacante = await sync_to_async(Vacante.objects.filter(url_original=job_data["url_original"]).first)()
    assert vacante, "Vacante no encontrada en la base de datos"
    assert vacante.titulo == "Prueba Analista", "Título incorrecto en la base de datos"
    print("✅ Vacante guardada")

async def test_system_health():
    scraper = EmailScraperV2()
    health_monitor = SystemHealthMonitor(scraper)
    recommendations = await health_monitor.check_health()
    assert isinstance(recommendations, dict), "Recomendaciones no retornadas"
    print(f"✅ Estado del sistema: {recommendations}")

if __name__ == "__main__":
    import django
    django.setup()
    asyncio.run(test_imap_connection())
    asyncio.run(test_fetch_email())
    asyncio.run(test_process_job_alert_email())
    asyncio.run(test_extract_vacancies())
    asyncio.run(test_scrape_vacancy_details())
    asyncio.run(test_save_vacante())
    asyncio.run(test_system_health())