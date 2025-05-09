# /home/pablo/test/test_tasks.py
import pytest
import responses
from celery import shared_task
from app.tasks import ejecutar_scraping
from app.models import DominioScraping
from django.utils import timezone

@pytest.mark.django_db
@pytest.mark.asyncio
@responses.activate
async def test_ejecutar_scraping():
    # Mockear la respuesta HTTP
    responses.add(
        responses.GET,
        "https://example.com",
        body="<html><body><h1>Test Job</h1></body></html>",
        status=200
    )
    # Crear un dominio de prueba
    dominio = DominioScraping.objects.create(
        dominio="https://example.com",
        empresa="Test Company",
        plataforma="default",
        verificado=True,
        activo=True,
        frecuencia_scraping=3600
    )
    result = await ejecutar_scraping(dominio_id=dominio.id)
    assert result["status"] == "success"
    assert result["successful_domains"] == 1
    assert result["failed_domains"] == 0