# /home/pablo/app/tests/test_utils/test_scraping_utils.py
import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from app.ats.utils.scraping_utils import ScrapingMetrics, SystemHealthMonitor, ScrapingCache, inicializar_contexto_playwright, visitar_pagina_humanizada, extraer_y_guardar_cookies

import logging

logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_scraping_metrics():
    """Test ScrapingMetrics class initialization and methods."""
    metrics = ScrapingMetrics()
    assert metrics.total_paginas_visitadas == 0
    assert metrics.total_vacantes_extraidas == 0
    assert metrics.errores == 0
    
    metrics.registrar_pagina_visitada()
    assert metrics.total_paginas_visitadas == 1
    
    metrics.registrar_vacante_extraida()
    assert metrics.total_vacantes_extraidas == 1
    
    metrics.registrar_error()
    assert metrics.errores == 1
    
    assert isinstance(metrics.obtener_resumen(), dict)
    logger.info("ScrapingMetrics test passed")

@pytest.mark.asyncio
async def test_system_health_monitor():
    """Test SystemHealthMonitor class initialization and methods."""
    monitor = SystemHealthMonitor()
    assert monitor.uso_cpu == 0.0
    assert monitor.uso_memoria == 0.0
    assert monitor.errores_consecutivos == 0
    
    monitor.actualizar_estado(10.0, 20.0)
    assert monitor.uso_cpu == 10.0
    assert monitor.uso_memoria == 20.0
    
    monitor.registrar_error()
    assert monitor.errores_consecutivos == 1
    
    monitor.reiniciar_contador_errores()
    assert monitor.errores_consecutivos == 0
    
    assert isinstance(monitor.obtener_estado(), dict)
    logger.info("SystemHealthMonitor test passed")

@pytest.mark.asyncio
async def test_scraping_cache():
    """Test ScrapingCache class initialization and methods."""
    cache = ScrapingCache()
    assert cache.cache == {}
    
    cache.agregar('test_key', 'test_value')
    assert 'test_key' in cache.cache
    assert cache.cache['test_key']['valor'] == 'test_value'
    
    assert cache.obtener('test_key') == 'test_value'
    assert cache.obtener('nonexistent_key') is None
    
    cache.limpiar()
    assert cache.cache == {}
    logger.info("ScrapingCache test passed")

@pytest.mark.asyncio
async def test_inicializar_contexto_playwright():
    """Test initialization of playwright context."""
    with patch('playwright.async_api.async_playwright', new=AsyncMock):
        contexto, navegador = await inicializar_contexto_playwright(headless=True)
        assert contexto is not None
        assert navegador is not None
        logger.info("Inicializar contexto playwright test passed")

@pytest.mark.asyncio
async def test_visitar_pagina_humanizada():
    """Test humanized page visiting with playwright."""
    with patch('playwright.async_api.async_playwright', new=AsyncMock):
        pagina = AsyncMock()
        url = "https://example.com"
        contenido = await visitar_pagina_humanizada(pagina, url, intentos_maximos=1)
        assert contenido is not None
        logger.info("Visitar pagina humanizada test passed")

@pytest.mark.asyncio
async def test_extraer_y_guardar_cookies():
    """Test extraction and saving of cookies."""
    with patch('playwright.async_api.async_playwright', new=AsyncMock):
        contexto = AsyncMock()
        cookies = await extraer_y_guardar_cookies(contexto, "https://example.com")
        assert isinstance(cookies, list)
        logger.info("Extraer y guardar cookies test passed")
