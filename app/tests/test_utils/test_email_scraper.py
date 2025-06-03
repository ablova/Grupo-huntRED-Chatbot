import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from app.models import BusinessUnit, Vacante
from app.ats.utils.email_scraper import connect_to_imap, fetch_emails, extract_job_info, save_to_vacante, move_email, process_emails

import logging

logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_connect_to_imap_success():
    """Test successful connection to IMAP server."""
    with patch('aioimaplib.IMAP4_SSL', new=AsyncMock):
        client = await connect_to_imap()
        assert client is not None
        logger.info("IMAP connection test passed")

@pytest.mark.asyncio
async def test_connect_to_imap_failure():
    """Test IMAP connection with failure and retries."""
    with patch('aioimaplib.IMAP4_SSL', new=AsyncMock(side_effect=Exception("Connection failed"))):
        try:
            await connect_to_imap()
            assert False, "Should have raised an exception"
        except Exception as e:
            assert "Connection failed" in str(e)
            logger.info("IMAP connection failure test passed")

@pytest.mark.asyncio
async def test_fetch_emails():
    """Test fetching emails from inbox."""
    with patch('aioimaplib.IMAP4_SSL', new=AsyncMock):
        emails = []
        async for email_id, email_msg in fetch_emails(batch_size=2):
            emails.append(email_id)
        assert len(emails) <= 2
        logger.info("Fetch emails test passed")

@pytest.mark.asyncio
async def test_extract_job_info():
    """Test extracting job information from email content."""
    email_message = AsyncMock()
    email_message.__getitem__.side_effect = lambda key: "Test Subject" if key == "Subject" else "Test From"
    email_message.is_multipart.return_value = False
    email_message.get_payload.return_value = b"Test Body with job opportunity"
    
    job_info = await extract_job_info(email_message)
    assert job_info is not None
    assert job_info["title"] == "Test Subject"
    assert job_info["company"] == "Test From"
    assert "Test Body" in job_info["description"]
    logger.info("Extract job info test passed")

@pytest.mark.asyncio
async def test_save_to_vacante():
    """Test saving job info to Vacante model."""
    job_info = {
        "title": "Test Job",
        "company": "Test Company",
        "description": "Test Description",
        "url": "https://example.com/job"
    }
    bu = BusinessUnit(name="test_bu")
    with patch('app.models.Vacante.save', new=AsyncMock):
        vacante = await save_to_vacante(job_info, bu)
        assert vacante is not None
        logger.info("Save to Vacante test passed")

@pytest.mark.asyncio
async def test_move_email():
    """Test moving email to a specified folder."""
    client = AsyncMock()
    email_id = b"123"
    folder = "parsed_folder"
    await move_email(client, email_id, folder)
    logger.info("Move email test passed")

@pytest.mark.asyncio
async def test_process_emails():
    """Test processing emails to extract job positions."""
    with patch('aioimaplib.IMAP4_SSL', new=AsyncMock):
        with patch('app.ats.utils.email_scraper.extract_job_info', new=AsyncMock(return_value={
            "title": "Test Job",
            "company": "Test Company",
            "description": "Test Description",
            "url": "https://example.com/job"
        })):
            with patch('app.models.Vacante.save', new=AsyncMock):
                await process_emails()
                logger.info("Process emails test passed")