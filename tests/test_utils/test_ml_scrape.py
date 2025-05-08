# /home/pablo/test/test_ml_scrape.py
import pytest
import email
from email.mime.text import MIMEText
from app.ml.ml_scrape import MLScraper

@pytest.mark.asyncio
async def test_classify_email():
    scraper = MLScraper()
    # Crear un mensaje MIME válido
    msg = MIMEText("Job at linkedin.com")
    msg['From'] = 'test@linkedin.com'
    msg['Subject'] = 'Job Opportunity'
    platform = await scraper.classify_email(msg)
    assert platform == "linkedin"

@pytest.mark.asyncio
async def test_extract_vacancies_from_email():
    scraper = MLScraper()
    # Crear un mensaje MIME válido con una URL
    msg = MIMEText("Apply at https://linkedin.com/jobs/123")
    msg['From'] = 'test@linkedin.com'
    msg['Subject'] = 'Job Opportunity'
    vacancies = await scraper.extract_vacancies_from_email(msg)
    assert len(vacancies) == 1
    assert vacancies[0]["url_original"] == "https://linkedin.com/jobs/123"