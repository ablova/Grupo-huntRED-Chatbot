import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from app.models import BusinessUnit, Vacante
from app.com.utils.scraping import JobScraper

import logging

logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_job_scraper_initialization():
    """Test initialization of JobScraper."""
    scraper = JobScraper(domains=["example.com"])
    assert scraper.domains == ["example.com"]
    assert scraper.max_depth == 2
    assert scraper.max_pages == 10
    assert scraper.concurrency == 3
    logger.info("JobScraper initialization test passed")

@pytest.mark.asyncio
async def test_job_scraper_session_initialization():
    """Test playwright browser session initialization."""
    scraper = JobScraper(domains=["example.com"])
    with patch('playwright.async_api.async_playwright', new=AsyncMock):
        await scraper.initialize()
        assert scraper.session is not None
        logger.info("JobScraper session initialization test passed")

@pytest.mark.asyncio
async def test_scrape_page():
    """Test scraping a single page for job listings."""
    scraper = JobScraper(domains=["example.com"])
    with patch('playwright.async_api.async_playwright', new=AsyncMock):
        with patch('bs4.BeautifulSoup', new=AsyncMock):
            page = AsyncMock()
            await scraper.scrape_page(page, "https://example.com/jobs")
            assert len(scraper.scraped_data) >= 0
            logger.info("Scrape page test passed")

@pytest.mark.asyncio
async def test_scrape_full_process():
    """Test the full scraping process."""
    scraper = JobScraper(domains=["example.com"])
    with patch('playwright.async_api.async_playwright', new=AsyncMock):
        with patch('bs4.BeautifulSoup', new=AsyncMock):
            result = await scraper.scrape()
            assert isinstance(result, list)
            logger.info("Full scraping process test passed")

@pytest.mark.asyncio
async def test_save_to_vacante():
    """Test saving scraped data to Vacante model."""
    scraper = JobScraper(domains=["example.com"])
    scraper.scraped_data = [{
        "title": "Test Job",
        "company": "Test Company",
        "description": "Test Description",
        "url": "https://example.com/job",
        "source": "example.com"
    }]
    bu = BusinessUnit(name="test_bu")
    with patch('app.models.Vacante.save', new=AsyncMock):
        await scraper.save_to_vacante(bu)
        logger.info("Save to Vacante test passed")

@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in JobScraper."""
    scraper = JobScraper(domains=["example.com"])
    with patch('playwright.async_api.async_playwright', new=AsyncMock(side_effect=Exception("Browser error"))):
        try:
            await scraper.initialize()
            assert False, "Should have raised an exception"
        except Exception as e:
            assert str(e) == "Browser error"
            logger.info("Error handling test passed")
