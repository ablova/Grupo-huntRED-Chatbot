# /home/pablo/test/test_email_scraper.py
import pytest
from unittest.mock import AsyncMock, patch
from app.utilidades.email_scraper import EmailScraperV2

@pytest.mark.django_db
@pytest.mark.asyncio
async def test_extract_vacancies_from_html():
    scraper = EmailScraperV2()
    sample_html = """
    <table>
        <tr>
            <td><a href="https://www.linkedin.com/jobs/view/3834705219">Vice President Marketing, Stealth Educational Startup (Remote) - $200,000/year USD</a></td>
            <td>Crossover · Cancún, ROO (En remoto)</td>
        </tr>
        <tr>
            <td><a href="https://www.linkedin.com/jobs/view/3844440240">Chief Financial Officer / 180 MXP plus perks / REMOTE POSITION</a></td>
            <td>AMERICAN RECRUITERS MEXICO · México (En remoto)</td>
        </tr>
        <tr>
            <td><a href="https://www.linkedin.com/jobs/view/3843711518">General Manager - Mexico MEX</a></td>
            <td>American Airlines · Área metropolitana de Ciudad de México</td>
        </tr>
        <tr>
            <td><a href="https://www.linkedin.com/jobs/view/3839095035">SVP & Managing Director, Production Latin America & US Hispanic</a></td>
            <td>Sony Pictures Entertainment · Área metropolitana de Ciudad de México (Híbrido)</td>
        </tr>
    </table>
    """
    with patch('app.models.Worker.objects.get_or_create', new_callable=AsyncMock) as mock_get_or_create:
        mock_get_or_create.side_effect = [
            (AsyncMock(name="Crossover"), False),
            (AsyncMock(name="AMERICAN RECRUITERS MEXICO"), False),
            (AsyncMock(name="American Airlines"), False),
            (AsyncMock(name="Sony Pictures Entertainment"), False)
        ]
        job_listings = await scraper.extract_vacancies_from_html(sample_html)
    assert len(job_listings) == 4, "Deberían extraerse 4 vacantes"
    expected_titles = [
        "Vice President Marketing, Stealth Educational Startup (Remote) - $200,000/year USD",
        "Chief Financial Officer / 180 MXP plus perks / REMOTE POSITION",
        "General Manager - Mexico MEX",
        "SVP & Managing Director, Production Latin America & US Hispanic"
    ]
    for job, expected_title in zip(job_listings, expected_titles):
        assert job["titulo"] == expected_title, f"Título no coincide: {job['titulo']}"
        assert job["url_original"].startswith("https://www.linkedin.com/jobs/view/"), f"URL inválida: {job['url_original']}"