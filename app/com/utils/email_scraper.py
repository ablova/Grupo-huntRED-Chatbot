# /home/pablo/app/com/utils/email_scraper.py
import asyncio
import aioimaplib
import email
import logging
import re
import random
import os
from datetime import datetime
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from django.utils import timezone
from functools import wraps
from asgiref.sync import sync_to_async
from app.models import Vacante, BusinessUnit, ConfiguracionBU, DominioScraping, Worker, USER_AGENTS
from app.ml.utils.scrape import MLScraper
from app.com.utils.scraping_utils import ScrapingMetrics, SystemHealthMonitor, ScrapingCache, generate_summary_report
from app.com.chatbot.gpt import GPTHandler
from urllib.parse import urlparse, urljoin
import aiohttp
import environ
import smtplib
from email.mime.text import MIMEText
from playwright.async_api import async_playwright
from app.com.utils.parser import parse_job_listing, save_job_to_vacante, extract_url

env = environ.Env()
environ.Env.read_env(env_file='/home/pablo/.env')

log_dir = "/home/pablo/logs"
log_file = os.path.join(log_dir, f"email_scraper_{datetime.now().strftime('%Y%m%d')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

IMAP_SERVER = env("IMAP_SERVER", default="mail.huntred.com")
EMAIL_ACCOUNT = env("EMAIL_ACCOUNT", default="pablo@huntred.com")
EMAIL_PASSWORD = env("EMAIL_PASSWORD", default="Natalia&Patricio1113!")
SMTP_SERVER = env("SMTP_SERVER", default="mail.huntred.com")
SMTP_PORT = env.int("SMTP_PORT", default=465)
CONNECTION_TIMEOUT = env.int("CONNECTION_TIMEOUT", default=90)
BATCH_SIZE_DEFAULT = env.int("BATCH_SIZE_DEFAULT", default=10)
MAX_RETRIES = env.int("MAX_RETRIES", default=3)
RETRY_DELAY = env.int("RETRY_DELAY", default=5)
MAX_ATTEMPTS = env.int("MAX_ATTEMPTS", default=10)

FOLDER_CONFIG = {
    "inbox": "INBOX",
    "jobs_folder": "INBOX.Jobs",
    "parsed_folder": "INBOX.Parsed",
    "error_folder": "INBOX.Error",
}

JOB_KEYWORDS = [
    "job", "vacante", "opportunity", "empleo", "position", 
    "director", "analista", "gerente", "asesor", "trabajo",
    "career", "linkedin"
]
EXCLUDED_TEXTS = [
    "unsubscribe", "manage", "help", "profile", "feed", 
    "preferences", "settings", "account", "notification"
]

async def connect_to_imap():
    """Connect to IMAP server with retry mechanism."""
    for attempt in range(MAX_RETRIES):
        try:
            client = aioimaplib.IMAP4_SSL(IMAP_SERVER, timeout=CONNECTION_TIMEOUT)
            await client.wait_hello_from_server()
            await client.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
            logger.info("Connected to IMAP server successfully")
            return client
        except Exception as e:
            logger.error(f"IMAP connection attempt {attempt + 1} failed: {str(e)}")
            if attempt == MAX_RETRIES - 1:
                logger.error("Max retries reached for IMAP connection")
                raise
            delay = RETRY_DELAY * (2 ** attempt) + random.uniform(0, 1)
            logger.info(f"Retrying IMAP connection in {delay:.2f} seconds...")
            await asyncio.sleep(delay)
    raise Exception("Failed to connect to IMAP server after max retries")

async def fetch_emails(batch_size=BATCH_SIZE_DEFAULT):
    """Fetch emails from the inbox with improved error handling."""
    try:
        client = await connect_to_imap()
        await client.select(FOLDER_CONFIG["inbox"])
        
        status, data = await client.search(None, "ALL")
        email_ids = data[0].split()
        logger.info(f"Found {len(email_ids)} emails in inbox")
        
        for i in range(0, min(len(email_ids), batch_size), 1):
            email_id = email_ids[i]
            try:
                status, data = await client.fetch(email_id, "(BODY.PEEK[])")
                raw_email = data[0][1]
                email_message = email.message_from_bytes(raw_email)
                yield email_id, email_message
            except Exception as e:
                logger.error(f"Error fetching email ID {email_id}: {str(e)}")
                continue
        
        await client.close()
        await client.logout()
    except Exception as e:
        logger.error(f"Error in fetch_emails: {str(e)}", exc_info=True)
        raise

async def extract_job_info(email_message):
    """Extract job information from email content using consolidated parser."""
    try:
        subject = email_message["Subject"] or ""
        from_addr = email_message["From"] or ""
        body = ""
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    body += part.get_payload(decode=True).decode("utf-8", errors="ignore")
                elif content_type == "text/html":
                    body += BeautifulSoup(part.get_payload(decode=True).decode("utf-8", errors="ignore"), "html.parser").get_text()
        else:
            body = email_message.get_payload(decode=True).decode("utf-8", errors="ignore")
        
        job_info = parse_job_listing(body, "", source_type="email")
        if job_info:
            job_info["title"] = subject
            job_info["company"] = from_addr
            logger.info(f"Job opportunity detected in email: {subject}")
            return job_info
        return None
    except Exception as e:
        logger.error(f"Error extracting job info: {str(e)}", exc_info=True)
        return None

async def save_to_vacante(job_info, bu):
    """Save extracted job info to Vacante model using parser utility."""
    return await save_job_to_vacante(job_info, bu)

async def move_email(client, email_id, folder):
    """Move email to specified folder with error handling."""
    try:
        await client.select(FOLDER_CONFIG["inbox"])
        await client.copy(email_id, FOLDER_CONFIG[folder])
        await client.delete(email_id)
        await client.expunge()
        logger.info(f"Moved email ID {email_id} to {folder}")
    except Exception as e:
        logger.error(f"Error moving email ID {email_id} to {folder}: {str(e)}")

async def process_emails():
    """Process emails to extract job positions with batch handling and robust error management."""
    try:
        bu = await sync_to_async(BusinessUnit.objects.get)(name="huntred")
        async for email_id, email_message in fetch_emails():
            try:
                job_info = await extract_job_info(email_message)
                if job_info:
                    vacante = await save_to_vacante(job_info, bu)
                    if vacante:
                        client = await connect_to_imap()
                        await move_email(client, email_id, "parsed_folder")
                        await client.close()
                        await client.logout()
                    else:
                        client = await connect_to_imap()
                        await move_email(client, email_id, "error_folder")
                        await client.close()
                        await client.logout()
                else:
                    client = await connect_to_imap()
                    await move_email(client, email_id, "jobs_folder")
                    await client.close()
                    await client.logout()
            except Exception as e:
                logger.error(f"Error processing email ID {email_id}: {str(e)}", exc_info=True)
                client = await connect_to_imap()
                await move_email(client, email_id, "error_folder")
                await client.close()
                await client.logout()
    except Exception as e:
        logger.error(f"Error in process_emails: {str(e)}", exc_info=True)
        raise

async def process_all_emails():
    await process_emails()

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai_huntred.settings")
    import django
    django.setup()
    asyncio.run(process_all_emails())