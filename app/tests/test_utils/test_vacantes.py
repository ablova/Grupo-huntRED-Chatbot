# /home/pablo/app/tests/test_utils/test_vacantes.py
import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from app.models import Vacante, BusinessUnit
from app.com.utils.vacantes import VacanteManager

import logging

logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_vacante_manager_init():
    """Test initialization of VacanteManager."""
    manager = VacanteManager()
    assert manager is not None
    logger.info("VacanteManager initialization test passed")

@pytest.mark.asyncio
async def test_obtener_vacantes():
    """Test obtaining vacancies with filters."""
    manager = VacanteManager()
    with patch('app.models.Vacante.objects.filter', new=AsyncMock(return_value=[])):
        vacantes = await manager.obtener_vacantes(business_unit_id=1)
        assert isinstance(vacantes, list)
        logger.info("Obtener vacantes test passed")

@pytest.mark.asyncio
async def test_crear_vacante():
    """Test creating a new vacancy."""
    manager = VacanteManager()
    datos_vacante = {
        "nombre": "Test Vacante",
        "empresa": "Test Empresa",
        "descripcion": "Test Descripcion",
        "url": "https://example.com/vacante",
        "fuente": "Test Fuente"
    }
    bu = BusinessUnit(name="test_bu")
    with patch('app.models.Vacante.objects.create', new=AsyncMock(return_value=Vacante(**datos_vacante))):
        vacante = await manager.crear_vacante(datos_vacante, bu)
        assert vacante is not None
        assert vacante.nombre == "Test Vacante"
        logger.info("Crear vacante test passed")

@pytest.mark.asyncio
async def test_actualizar_vacante():
    """Test updating an existing vacancy."""
    manager = VacanteManager()
    datos_actualizados = {
        "nombre": "Vacante Actualizada",
        "descripcion": "Descripcion Actualizada"
    }
    vacante = Vacante(nombre="Original", descripcion="Original Desc")
    with patch('app.models.Vacante.objects.filter', new=AsyncMock(return_value=[vacante])):
        with patch('app.models.Vacante.save', new=AsyncMock):
            resultado = await manager.actualizar_vacante(1, datos_actualizados)
            assert resultado is not None
            assert resultado.nombre == "Vacante Actualizada"
            logger.info("Actualizar vacante test passed")

@pytest.mark.asyncio
async def test_eliminar_vacante():
    """Test deleting a vacancy."""
    manager = VacanteManager()
    with patch('app.models.Vacante.objects.filter', new=AsyncMock(return_value=[Vacante()])):
        with patch('app.models.Vacante.delete', new=AsyncMock):
            resultado = await manager.eliminar_vacante(1)
            assert resultado == True
            logger.info("Eliminar vacante test passed")

@pytest.mark.asyncio
async def test_filtrar_vacantes_por_texto():
    """Test filtering vacancies by text."""
    manager = VacanteManager()
    with patch('app.models.Vacante.objects.filter', new=AsyncMock(return_value=[])):
        vacantes = await manager.filtrar_vacantes_por_texto("developer")
        assert isinstance(vacantes, list)
        logger.info("Filtrar vacantes por texto test passed")

@pytest.mark.asyncio
async def test_obtener_estados_vacante():
    """Test obtaining vacancy states."""
    manager = VacanteManager()
    estados = manager.obtener_estados_vacante()
    assert isinstance(estados, list)
    assert len(estados) > 0
    logger.info("Obtener estados vacante test passed")
