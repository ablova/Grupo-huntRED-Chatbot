# /home/pablo/app/test/test_email_scraper.py
import asyncio
import unittest
from unittest.mock import AsyncMock, patch
from django.test import TestCase
from app.utilidades.email_scraper import EmailScraperV2

class TestEmailScraper(TestCase):
    def setUp(self):
        self.scraper = EmailScraperV2()

    async def test_extract_vacancies_from_html_async(self):
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
            job_listings = await self.scraper.extract_vacancies_from_html(sample_html)
        self.assertEqual(len(job_listings), 4, "Deberían extraerse 4 vacantes")
        expected_titles = [
            "Vice President Marketing, Stealth Educational Startup (Remote) - $200,000/year USD",
            "Chief Financial Officer / 180 MXP plus perks / REMOTE POSITION",
            "General Manager - Mexico MEX",
            "SVP & Managing Director, Production Latin America & US Hispanic"
        ]
        for job, expected_title in zip(job_listings, expected_titles):
            self.assertEqual(job["titulo"], expected_title, f"Título no coincide: {job['titulo']}")
            self.assertTrue(job["url_original"].startswith("https://www.linkedin.com/jobs/view/"), f"URL inválida: {job['url_original']}")

    def test_extract_vacancies(self):
        asyncio.run(self.test_extract_vacancies_from_html_async())

if __name__ == "__main__":
    import os
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai_huntred.settings")
    import django
    django.setup()
    unittest.main()