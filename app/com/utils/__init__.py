# /home/pablo/app/com/utils/__init__.py
from app.lazy_imports import LazyImporter

# Crear instancia del importador lazy
lazy_imports = LazyImporter()

# Registrar todos los módulos que necesitan importaciones lazy
lazy_imports.register('scraping_utils', '.scraping_utils')
lazy_imports.register('email_scraper', '.email_scraper')
lazy_imports.register('report_generator', '.report_generator')
lazy_imports.register('vacantes', '.vacantes')
lazy_imports.register('google_calendar', '.google_calendar')
lazy_imports.register('linkedin', '.linkedin')
lazy_imports.register('scraping', '.scraping')
lazy_imports.register('signature', '.signature')

# Registrar optimizadores para NLP y GPT
lazy_imports.register('optimizers', '.optimizers')

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
    'process_domain', 'run_all_scrapers',
    # Optimizadores del sistema
    'get_optimized_nlp', 'get_optimized_gpt', 'initialize_optimizations'
]

# Función para obtener importaciones de LinkedIn de manera lazy
def get_linkedin_imports():
    linkedin = lazy_imports.get_module('linkedin')
    return linkedin.LinkedInScraper, linkedin.process_linkedin_jobs

# Función para obtener importaciones de scraping de manera lazy
def get_scraping_imports():
    scraping = lazy_imports.get_module('scraping')
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

# Función para obtener optimizadores de NLP/GPT de manera lazy
def get_optimized_nlp():
    optimizers = lazy_imports.get_module('optimizers')
    # Intentar obtener conector optimizado
    try:
        import app.com.chatbot.optimized_connectors
        return app.com.chatbot.optimized_connectors.OptimizedNLPConnector
    except ImportError:
        # Llamar a inicializador de optimizadores
        optimizers.initialize_optimizers()
        return None

# Función para obtener modelo GPT optimizado de manera lazy
def get_optimized_gpt():
    optimizers = lazy_imports.get_module('optimizers')
    # Intentar obtener conector optimizado
    try:
        import app.com.chatbot.optimized_connectors
        return app.com.chatbot.optimized_connectors.OptimizedGPTConnector
    except ImportError:
        # Llamar a inicializador de optimizadores
        optimizers.initialize_optimizers()
        return None

# Función para inicializar optimizaciones
def initialize_optimizations():
    optimizers = lazy_imports.get_module('optimizers')
    return optimizers.initialize_optimizers()

# Inicializar optimizaciones de forma sigilosa sin bloquear la carga
try:
    import threading
    threading.Thread(target=lambda: lazy_imports.get_module('optimizers')).start()
except Exception:
    pass