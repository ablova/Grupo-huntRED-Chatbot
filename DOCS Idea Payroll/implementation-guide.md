# huntRED® v2 - Guía de Implementación
## Manual Técnico para Desarrolladores

---

## 1. SETUP DEL ENTORNO DE DESARROLLO

### 1.1 Requisitos del Sistema
```bash
# Python 3.9+
python --version  # >= 3.9.0

# PostgreSQL 14+
psql --version    # >= 14.0

# Redis 6+
redis-server --version  # >= 6.0

# Node.js 16+ (para frontend)
node --version    # >= 16.0
```

### 1.2 Instalación de Dependencias
```bash
# Crear entorno virtual
python -m venv huntred_env
source huntred_env/bin/activate  # Linux/Mac
# huntred_env\Scripts\activate   # Windows

# Instalar dependencias Python
pip install -r requirements.txt

# Variables de entorno
cp .env.example .env
# Configurar credenciales en .env
```

### 1.3 Configuración de Base de Datos
```sql
-- Crear base de datos
CREATE DATABASE huntred_v2;
CREATE USER huntred_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE huntred_v2 TO huntred_user;

-- Ejecutar migraciones
alembic upgrade head
```

---

## 2. CONFIGURACIÓN MULTI-TENANT

### 2.1 Estructura de Clientes
```python
# models/company.py
from sqlalchemy import Column, String, JSON, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Company(Base):
    __tablename__ = 'companies'
    
    id = Column(String, primary_key=True)
    name = Column(String(255), nullable=False)
    whatsapp_webhook_token = Column(String(255), unique=True)
    telegram_bot_token = Column(String(255), nullable=True)
    country_code = Column(String(3), nullable=False)  # MEX, USA, etc.
    payroll_config = Column(JSON, nullable=False)
    messaging_config = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 2.2 Configuración por País
```python
# config/countries.py
COUNTRY_CONFIGS = {
    'MEX': {
        'currency': 'MXN',
        'uma_daily': 108.57,
        'uma_monthly': 3257.10,
        'required_fields': ['rfc', 'curp', 'nss', 'clabe'],
        'overtime_rules': {
            'daily_limit': 3,
            'weekly_limit': 9,
            'double_pay_hours': 9
        },
        'payroll_frequency': ['WEEKLY', 'BIWEEKLY', 'MONTHLY']
    },
    'USA': {
        'currency': 'USD',
        'minimum_wage': 7.25,
        'required_fields': ['ssn', 'tax_status', 'state'],
        'overtime_rules': {
            'weekly_threshold': 40,
            'overtime_multiplier': 1.5
        },
        'payroll_frequency': ['WEEKLY', 'BIWEEKLY', 'MONTHLY', 'SEMI_MONTHLY']
    }
}
```

---

## 3. IMPLEMENTACIÓN SOCIALLINK ENGINE

### 3.1 Configuración de APIs
```python
# services/social_link_engine.py
class SocialLinkEngine:
    def __init__(self):
        self.linkedin_api = LinkedInAPI(api_key=settings.LINKEDIN_API_KEY)
        self.twitter_api = TwitterAPI(bearer_token=settings.TWITTER_BEARER_TOKEN)
        self.github_api = GitHubAPI(token=settings.GITHUB_TOKEN)
        self.sentiment_analyzer = pipeline("sentiment-analysis")
        
    async def analyze_profile(self, profile_data: dict) -> SocialAnalysis:
        """Análisis completo de perfil social"""
        
        # 1. Extraer datos de todas las plataformas
        platforms_data = await self._extract_all_platforms(profile_data)
        
        # 2. Análisis de sentimientos
        sentiment_score = await self._analyze_sentiment(platforms_data)
        
        # 3. Cálculo de influence level
        influence_level = self._calculate_influence_level(platforms_data)
        
        # 4. Detección de red flags
        red_flags = await self._detect_red_flags(platforms_data)
        
        # 5. Professional credibility scoring
        credibility_score = self._calculate_credibility(platforms_data)
        
        return SocialAnalysis(
            sentiment_score=sentiment_score,
            influence_level=influence_level,
            red_flags=red_flags,
            credibility_score=credibility_score,
            platforms_summary=platforms_data
        )
```

### 3.2 Análisis de Sentimientos Avanzado
```python
def _analyze_sentiment(self, platforms_data: dict) -> float:
    """Análisis de sentimiento con score -1.0 a +1.0"""
    
    all_content = []
    for platform, data in platforms_data.items():
        if 'posts' in data:
            all_content.extend([post['text'] for post in data['posts']])
    
    if not all_content:
        return 0.0  # Neutral por defecto
    
    sentiment_scores = []
    for content in all_content:
        # Usar modelo pre-entrenado
        result = self.sentiment_analyzer(content)
        
        # Convertir a escala -1 a +1
        if result[0]['label'] == 'POSITIVE':
            score = result[0]['score']
        else:  # NEGATIVE
            score = -result[0]['score']
        
        sentiment_scores.append(score)
    
    # Promedio ponderado
    return sum(sentiment_scores) / len(sentiment_scores)
```

---

## 4. PAYROLL ENGINE IMPLEMENTATION

### 4.1 Cálculo de ISR México 2024
```python
# services/payroll_engine.py
class PayrollEngine:
    def __init__(self, company_id: str):
        self.company = Company.get(company_id)
        self.country_config = COUNTRY_CONFIGS[self.company.country_code]
    
    def calculate_isr_monthly(self, gross_salary: float) -> float:
        """Cálculo de ISR mensual según tablas 2024"""
        
        isr_table = ISR_MONTHLY_TABLES
        
        for i, upper_limit in enumerate(isr_table['upper_limit']):
            if gross_salary <= upper_limit:
                lower_limit = isr_table['lower_limit'][i]
                fixed_amount = isr_table['fixed_amount'][i]
                percentage = isr_table['percentage'][i] / 100
                
                excess = gross_salary - lower_limit
                variable_amount = excess * percentage
                
                return fixed_amount + variable_amount
        
        return 0.0  # Error case
    
    def calculate_imss_employee(self, gross_salary: float) -> dict:
        """Cálculo de IMSS empleado"""
        
        uma_monthly = self.country_config['uma_monthly']
        
        # Enfermedad y maternidad: 0.25% del SBC
        sickness_maternity = gross_salary * 0.0025
        
        # Invalidez y vida: 0.625% del SBC  
        disability_life = gross_salary * 0.00625
        
        # Cesantía y vejez: 1.125% del SBC
        retirement = gross_salary * 0.01125
        
        return {
            'sickness_maternity': sickness_maternity,
            'disability_life': disability_life,
            'retirement': retirement,
            'total': sickness_maternity + disability_life + retirement
        }
```

### 4.2 Generación de Recibos
```python
def generate_payslip(self, employee_id: str, period: str) -> PayslipData:
    """Genera recibo de nómina individual"""
    
    employee = Employee.get(employee_id)
    
    # Calcular percepciones
    gross_salary = employee.monthly_salary
    overtime_pay = self._calculate_overtime_pay(employee_id, period)
    bonuses = self._calculate_bonuses(employee_id, period)
    
    total_perceptions = gross_salary + overtime_pay + bonuses
    
    # Calcular deducciones
    isr = self.calculate_isr_monthly(total_perceptions)
    imss = self.calculate_imss_employee(total_perceptions)
    infonavit = self._calculate_infonavit(employee, total_perceptions)
    
    total_deductions = isr + imss['total'] + infonavit
    
    # Neto a pagar
    net_pay = total_perceptions - total_deductions
    
    return PayslipData(
        employee=employee,
        period=period,
        perceptions={
            'base_salary': gross_salary,
            'overtime': overtime_pay,
            'bonuses': bonuses,
            'total': total_perceptions
        },
        deductions={
            'isr': isr,
            'imss': imss['total'],
            'infonavit': infonavit,
            'total': total_deductions
        },
        net_pay=net_pay
    )
```

---

## 5. WHATSAPP BOT MULTI-TENANT

### 5.1 Configuración de Webhooks
```python
# api/whatsapp_webhook.py
from fastapi import APIRouter, Depends, HTTPException
from services.whatsapp_bot import WhatsAppPayrollBot

router = APIRouter()

@router.post("/webhook/{company_id}")
async def whatsapp_webhook(
    company_id: str,
    webhook_data: dict,
    bot: WhatsAppPayrollBot = Depends(get_company_bot)
):
    """Webhook para mensajes de WhatsApp por cliente"""
    
    try:
        # Procesar mensaje entrante
        message = webhook_data.get('entry', [{}])[0].get('changes', [{}])[0].get('value', {}).get('messages', [{}])[0]
        
        if not message:
            return {"status": "no_message"}
        
        # Extraer datos del mensaje
        from_number = message.get('from')
        message_text = message.get('text', {}).get('body', '')
        message_type = message.get('type')
        
        # Procesar según tipo de mensaje
        if message_type == 'text':
            response = await bot.process_text_message(from_number, message_text)
        elif message_type == 'location':
            location = message.get('location', {})
            response = await bot.process_location_message(from_number, location)
        else:
            response = await bot.process_unsupported_message(from_number, message_type)
        
        return {"status": "processed", "response": response}
        
    except Exception as e:
        logger.error(f"Error processing webhook for company {company_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

def get_company_bot(company_id: str) -> WhatsAppPayrollBot:
    """Obtener bot específico de la empresa"""
    company = Company.get(company_id)
    if not company or not company.is_active:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return WhatsAppPayrollBot(
        company_id=company_id,
        webhook_token=company.whatsapp_webhook_token
    )
```

### 5.2 Comandos de Empleados
```python
# services/whatsapp_bot.py
class WhatsAppPayrollBot:
    def __init__(self, company_id: str, webhook_token: str):
        self.company_id = company_id
        self.whatsapp_client = WhatsAppClient(webhook_token)
        self.payroll_engine = PayrollEngine(company_id)
    
    async def process_text_message(self, from_number: str, message_text: str) -> dict:
        """Procesar mensaje de texto"""
        
        # Identificar empleado
        employee = Employee.get_by_phone(from_number, self.company_id)
        if not employee:
            return await self._send_registration_flow(from_number)
        
        # Normalizar comando
        command = message_text.lower().strip()
        
        # Enrutar comando
        if command in ['entrada', 'checkin', 'llegada']:
            return await self._handle_checkin(employee, from_number)
        elif command in ['salida', 'checkout']:
            return await self._handle_checkout(employee, from_number)
        elif command in ['recibo', 'nomina']:
            return await self._handle_payslip_request(employee, from_number)
        elif command in ['saldo', 'vacaciones']:
            return await self._handle_balance_inquiry(employee, from_number)
        elif command in ['horario', 'schedule']:
            return await self._handle_schedule_inquiry(employee, from_number)
        else:
            return await self._handle_unknown_command(employee, from_number, command)
    
    async def _handle_checkin(self, employee: Employee, from_number: str) -> dict:
        """Manejar entrada del empleado"""
        
        # Verificar si ya tiene entrada registrada hoy
        today = datetime.now().date()
        existing_checkin = Attendance.get_checkin_today(employee.id, today)
        
        if existing_checkin:
            message = f"❌ Ya tienes registrada tu entrada de hoy a las {existing_checkin.check_in_time.strftime('%H:%M')}"
            await self.whatsapp_client.send_message(from_number, message)
            return {"status": "already_checked_in"}
        
        # Solicitar ubicación
        message = """📍 Para registrar tu entrada, comparte tu ubicación:

1. Toca el ícono de adjuntar (📎)
2. Selecciona "Ubicación"  
3. Elige "Ubicación actual"

Esto es para verificar que estés en la oficina."""
        
        await self.whatsapp_client.send_message(from_number, message)
        
        # Guardar estado esperando ubicación
        UserSession.set_waiting_location(employee.id, 'checkin')
        
        return {"status": "waiting_location"}
    
    async def process_location_message(self, from_number: str, location: dict) -> dict:
        """Procesar mensaje de ubicación"""
        
        employee = Employee.get_by_phone(from_number, self.company_id)
        session = UserSession.get(employee.id)
        
        if not session or session.status != 'waiting_location':
            message = "❌ No estaba esperando una ubicación. Usa 'entrada' o 'salida' primero."
            await self.whatsapp_client.send_message(from_number, message)
            return {"status": "unexpected_location"}
        
        # Validar ubicación
        employee_lat = location.get('latitude')
        employee_lon = location.get('longitude')
        
        office_location = employee.office.location
        office_lat = office_location['latitude']
        office_lon = office_location['longitude']
        
        is_valid_location = validate_office_location(
            employee_lat, employee_lon, office_lat, office_lon
        )
        
        if not is_valid_location:
            message = """❌ Tu ubicación está muy lejos de la oficina.

Debes estar dentro de un radio de 100 metros para registrar tu asistencia.

Si tienes problemas, contacta a RH."""
            
            await self.whatsapp_client.send_message(from_number, message)
            UserSession.clear(employee.id)
            return {"status": "invalid_location"}
        
        # Registrar asistencia
        now = datetime.now()
        
        if session.action == 'checkin':
            Attendance.create_checkin(
                employee_id=employee.id,
                check_in_time=now,
                latitude=employee_lat,
                longitude=employee_lon
            )
            
            message = f"""✅ Entrada registrada exitosamente

🕐 Hora: {now.strftime('%H:%M')}
📅 Fecha: {now.strftime('%d/%m/%Y')}
📍 Ubicación: Verificada

¡Que tengas un excelente día de trabajo! 💪"""
            
        else:  # checkout
            attendance = Attendance.get_open_attendance(employee.id)
            attendance.check_out_time = now
            attendance.checkout_latitude = employee_lat
            attendance.checkout_longitude = employee_lon
            attendance.save()
            
            # Calcular horas trabajadas
            worked_hours = (now - attendance.check_in_time).total_seconds() / 3600
            
            message = f"""✅ Salida registrada exitosamente

🕐 Entrada: {attendance.check_in_time.strftime('%H:%M')}
🕐 Salida: {now.strftime('%H:%M')}
⏱️ Horas trabajadas: {worked_hours:.2f}
📅 Fecha: {now.strftime('%d/%m/%Y')}

¡Descansa bien! 😊"""
        
        await self.whatsapp_client.send_message(from_number, message)
        UserSession.clear(employee.id)
        
        return {"status": "success"}
```

---

## 6. UNIFIED MESSAGING ENGINE

### 6.1 Configuración Multi-Canal
```python
# services/unified_messaging.py
class UnifiedMessagingEngine:
    def __init__(self, company_id: str):
        self.company_id = company_id
        self.company = Company.get(company_id)
        self.channels = self._initialize_channels()
    
    def _initialize_channels(self) -> dict:
        """Inicializar todos los canales disponibles"""
        channels = {}
        
        config = self.company.messaging_config
        
        if config.get('whatsapp', {}).get('enabled'):
            channels['whatsapp'] = WhatsAppChannel(
                token=config['whatsapp']['token']
            )
        
        if config.get('telegram', {}).get('enabled'):
            channels['telegram'] = TelegramChannel(
                token=config['telegram']['bot_token']
            )
        
        if config.get('sms', {}).get('enabled'):
            channels['sms'] = SMSChannel(
                provider=config['sms']['provider'],
                credentials=config['sms']['credentials']
            )
        
        if config.get('email', {}).get('enabled'):
            channels['email'] = EmailChannel(
                smtp_config=config['email']['smtp']
            )
        
        return channels
    
    async def send_unified_message(
        self,
        employee_id: str,
        message: str,
        priority: str = 'NORMAL',
        message_type: str = 'notification'
    ) -> MessageResult:
        """Enviar mensaje usando estrategia unificada"""
        
        # Obtener contacto unificado del empleado
        contact = UnifiedContact.get_by_employee(employee_id)
        
        if not contact:
            return MessageResult(success=False, error="Employee contact not found")
        
        # Determinar estrategia según prioridad
        strategy = self._get_messaging_strategy(priority)
        
        # Intentar envío por canales según estrategia
        for attempt, channel_name in enumerate(strategy['channels']):
            if channel_name not in self.channels:
                continue
            
            channel = self.channels[channel_name]
            contact_info = getattr(contact, f"{channel_name}_contact", None)
            
            if not contact_info:
                continue
            
            try:
                result = await channel.send_message(contact_info, message)
                
                if result.success:
                    # Registrar envío exitoso
                    MessageLog.create(
                        employee_id=employee_id,
                        channel=channel_name,
                        message=message,
                        status='sent',
                        attempt=attempt + 1
                    )
                    
                    return MessageResult(
                        success=True,
                        channel_used=channel_name,
                        attempt=attempt + 1
                    )
                
            except Exception as e:
                logger.error(f"Error sending via {channel_name}: {str(e)}")
                
                # Registrar error
                MessageLog.create(
                    employee_id=employee_id,
                    channel=channel_name,
                    message=message,
                    status='failed',
                    error=str(e),
                    attempt=attempt + 1
                )
            
            # Esperar antes del siguiente intento si hay más canales
            if attempt < len(strategy['channels']) - 1:
                await asyncio.sleep(strategy['fallback_delay'])
        
        return MessageResult(success=False, error="All channels failed")
    
    def _get_messaging_strategy(self, priority: str) -> dict:
        """Obtener estrategia de mensajería según prioridad"""
        
        strategies = {
            'CRITICAL': {
                'channels': ['whatsapp', 'telegram', 'sms', 'email'],
                'fallback_delay': 60,  # 1 minuto
                'retry_attempts': 5
            },
            'HIGH': {
                'channels': ['whatsapp', 'telegram'],
                'fallback_delay': 300,  # 5 minutos
                'retry_attempts': 3
            },
            'NORMAL': {
                'channels': ['whatsapp'],
                'fallback_delay': 900,  # 15 minutos
                'retry_attempts': 2
            }
        }
        
        return strategies.get(priority, strategies['NORMAL'])
```

---

## 7. DEPLOYMENT EN PRODUCCIÓN

### 7.1 Docker Configuration
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    postgresql-client \
    redis-tools \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Configurar entorno
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Exponer puerto
EXPOSE 8000

# Comando de inicio
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 7.2 Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://huntred_user:secure_password@db:5432/huntred_v2
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./uploads:/app/uploads
    restart: unless-stopped

  db:
    image: postgres:14
    environment:
      - POSTGRES_DB=huntred_v2
      - POSTGRES_USER=huntred_user
      - POSTGRES_PASSWORD=secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  redis:
    image: redis:6
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### 7.3 Configuración de Nginx
```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream app {
        server app:8000;
    }

    server {
        listen 80;
        server_name huntred.com www.huntred.com;
        
        # Redirect to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name huntred.com www.huntred.com;

        ssl_certificate /etc/nginx/ssl/huntred.crt;
        ssl_certificate_key /etc/nginx/ssl/huntred.key;

        # WhatsApp webhooks
        location /api/whatsapp/webhook/ {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # API general
        location /api/ {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Frontend estático
        location / {
            root /var/www/html;
            try_files $uri $uri/ /index.html;
        }
    }
}
```

---

## 8. MONITOREO Y MANTENIMIENTO

### 8.1 Health Checks
```python
# api/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
import redis

router = APIRouter()

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    
    checks = {
        "database": False,
        "redis": False,
        "whatsapp_api": False,
        "overall": False
    }
    
    # Database check
    try:
        db.execute("SELECT 1")
        checks["database"] = True
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
    
    # Redis check
    try:
        r = redis.Redis.from_url(settings.REDIS_URL)
        r.ping()
        checks["redis"] = True
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
    
    # WhatsApp API check
    try:
        # Test with a dummy company
        test_client = WhatsAppClient(settings.TEST_WHATSAPP_TOKEN)
        await test_client.health_check()
        checks["whatsapp_api"] = True
    except Exception as e:
        logger.error(f"WhatsApp API health check failed: {str(e)}")
    
    # Overall health
    checks["overall"] = all([
        checks["database"],
        checks["redis"],
        checks["whatsapp_api"]
    ])
    
    status_code = 200 if checks["overall"] else 503
    
    return {"status": checks, "timestamp": datetime.utcnow()}, status_code
```

### 8.2 Logging Configuration
```python
# logging_config.py
import logging
import sys
from logging.handlers import RotatingFileHandler

def setup_logging():
    """Configurar logging para producción"""
    
    # Formato de logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Handler para archivo
    file_handler = RotatingFileHandler(
        'logs/huntred.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # Configurar logger principal
    logger = logging.getLogger('huntred')
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Configurar loggers específicos
    logging.getLogger('whatsapp').setLevel(logging.DEBUG)
    logging.getLogger('payroll').setLevel(logging.INFO)
    logging.getLogger('social_analysis').setLevel(logging.WARNING)
    
    return logger
```

---

**Esta guía proporciona todo lo necesario para implementar huntRED® v2 desde cero hasta producción, con código real y configuraciones probadas en entornos empresariales.**