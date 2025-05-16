"""
Configuración centralizada para pruebas del sistema Grupo huntRED®.
Este archivo contiene constantes y datos de prueba utilizados por todos los tests.
"""

# Datos de contacto para pruebas
# Estos datos se pueden utilizar en cualquier test que requiera un destinatario
TEST_WHATSAPP = '+525518490291'  # Número de WhatsApp para pruebas
TEST_TELEGRAM_ID = '871198362'   # ID de Telegram para pruebas
TEST_EMAIL_PERSONAL = 'ablova@gmail.com'  # Email personal para pruebas
TEST_EMAIL_CORPORATE = 'pablo@huntred.com'  # Email corporativo para pruebas

# Datos de perfil de prueba
TEST_USER_NAME = 'Pablo'  # Nombre para pruebas
TEST_USER_LASTNAME = 'Lelo de Larrea y de Haro'  # Apellido para pruebas

# Business Units para pruebas
TEST_BUS = {
    'huntRED': 'huntRED',
    'huntU': 'huntU',
    'Amigro': 'Amigro',
    'huntRED_Executive': 'huntRED Executive',
    'SEXSI': 'SEXSI',
    'MilkyLeak': 'MilkyLeak'
}

# Configuración para mock de respuestas
MOCK_RESPONSES = {
    'whatsapp_success': {'messaging_product': 'whatsapp', 'contacts': [{'input': TEST_WHATSAPP, 'wa_id': TEST_WHATSAPP}], 'messages': [{'id': 'wamid.123456789'}]},
    'email_success': True,
    'telegram_success': {'ok': True, 'result': {'message_id': 123}}
}

# Tipos de pruebas
TEST_TYPES = {
    'unit': 'unit',
    'integration': 'integration',
    'e2e': 'e2e',
    'performance': 'performance'
}

# Directorios para artefactos de prueba
TEST_DIRS = {
    'fixtures': 'app/tests/fixtures',
    'mocks': 'app/tests/mocks',
    'data': 'app/tests/data'
}

# Timeouts para pruebas
TEST_TIMEOUTS = {
    'short': 1,    # 1 segundo
    'medium': 5,   # 5 segundos
    'long': 30     # 30 segundos
}

# Número de reintentos para operaciones asíncronas
TEST_RETRIES = 3
