from app.lazy_imports import lazy_imports, register_module, get_module

# Registrar todos los módulos que necesitan importaciones lazy
lazy_imports.register('scraping_utils', '.scraping_utils')
lazy_imports.register('email_scraper', '.email_scraper')
lazy_imports.register('report_generator', '.report_generator')
lazy_imports.register('vacantes', '.vacantes')
lazy_imports.register('google_calendar', '.google_calendar')
lazy_imports.register('linkedin', '.linkedin')
lazy_imports.register('scraping', '.scraping')
lazy_imports.register('signature', '.signature')

# Exportar todas las funciones y clases
__all__ = [
    'ScrapingMetrics', 'SystemHealthMonitor', 'ScrapingCache',
    'PlaywrightAntiDeteccion', 'inicializar_contexto_playwright',
    'visitar_pagina_humanizada', 'extraer_y_guardar_cookies',
    'generate_summary_report',
    'EmailScraper', 'process_email_content',
    'generate_report', 'generate_pdf_report',
    'VacanteManager', 'process_vacancy_data',
    'GoogleCalendarHandler', 'schedule_interview',
    'BiometricAuth', 'DigitalSign', 'IdentityValidation',
    'PDFGenerator', 'SignatureHandler',
    'LinkedInScraper', 'process_linkedin_jobs',
    'ScrapingPipeline', 'assign_business_unit', 'enrich_with_gpt',
    'save_vacantes', 'validar_url', 'extract_skills',
    'associate_divisions', 'extract_field', 'get_scraper',
    'publish_to_internal_system', 'scrape_and_publish',
    'process_domain', 'run_all_scrapers'
]

# Función para obtener importaciones de LinkedIn de manera lazy
def get_linkedin_imports():
    linkedin = get_module('linkedin')
    return linkedin.LinkedInScraper, linkedin.process_linkedin_jobs

# Función para obtener importaciones de scraping de manera lazy
def get_scraping_imports():
    scraping = get_module('scraping')
    return {
        'ScrapingPipeline': scraping.ScrapingPipeline,
        'assign_business_unit': scraping.assign_business_unit,
        'enrich_with_gpt': scraping.enrich_with_gpt,
        'save_vacantes': scraping.save_vacantes,
        'validar_url': scraping.validar_url,
        'extract_skills': scraping.extract_skills,
        'associate_divisions': scraping.associate_divisions,
        'extract_field': scraping.extract_field,
        'get_scraper': scraping.get_scraper,
        'publish_to_internal_system': scraping.publish_to_internal_system,
        'scrape_and_publish': scraping.scrape_and_publish,
        'process_domain': scraping.process_domain,
        'run_all_scrapers': scraping.run_all_scrapers
    }