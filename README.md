# Grupo huntRED® - Plataforma Inteligente de Reclutamiento, Talento y Automatización

<div align="center">
  <img src="static/images/logo.png" alt="Grupo huntRED® Logo" width="250">
  <h1>Grupo huntRED® AI Talent Platform</h1>
  <p>
    <em>Plataforma global de IA para reclutamiento, gestión de talento, automatización y crecimiento empresarial</em>
    <br>
    <strong>Versión 4.0 (2025)</strong>
  </p>
</div>

---

## 🚀 Descripción General

Grupo huntRED® es la plataforma más avanzada del mercado para la gestión integral de talento, reclutamiento, automatización de procesos, análisis predictivo y experiencia conversacional, con integración total de IA, machine learning, seguridad, monetización y escalabilidad global.

- **Arquitectura modular, escalable y segura**
- **Personalización por unidad de negocio (BU)**
- **Automatización inteligente y workflows conversacionales**
- **Integración multi-canal y multi-API**
- **Analytics predictivo, gamificación y UI/UX de vanguardia**

---

# 🏗️ Arquitectura y Módulos Detallados

## Diagrama Macro de Interacción de Módulos

```mermaid
flowchart TD
  CORE["CORE\n- Autenticación\n- Configuración\n- Seguridad"]
  ATS["ATS\n- Chatbot\n- Publish\n- Payments\n- Notifications\n- Proposals\n- Feedback & Assessments\n- Referral\n- Gamificación"]
  ML["Machine Learning & IA\n- GenIA\n- AURA\n- Gamification Analytics"]
  INTEGRACIONES["Integraciones & APIs"]
  UIUX["UI/UX Moderno"]
  SEGURIDAD["Seguridad & Compliance"]
  ESCALABILIDAD["Escalabilidad Global"]
  INFRA["Infraestructura & Tecnología"]

  CORE --> ATS
  CORE --> ML
  CORE --> INTEGRACIONES
  CORE --> UIUX
  CORE --> SEGURIDAD
  CORE --> ESCALABILIDAD
  CORE --> INFRA
  ATS --> ML
  ATS --> INTEGRACIONES
  ATS --> UIUX
  ATS --> SEGURIDAD
  ATS --> ESCALABILIDAD
  ATS --> INFRA
  ML --> INTEGRACIONES
  ML --> UIUX
  ML --> SEGURIDAD
  ML --> ESCALABILIDAD
  ML --> INFRA
  INTEGRACIONES --> UIUX
  INTEGRACIONES --> SEGURIDAD
  INTEGRACIONES --> ESCALABILIDAD
  INTEGRACIONES --> INFRA
  UIUX --> SEGURIDAD
  UIUX --> ESCALABILIDAD
  UIUX --> INFRA
  SEGURIDAD --> ESCALABILIDAD
  SEGURIDAD --> INFRA
  ESCALABILIDAD --> INFRA
```

---

## 1. CORE
- **Autenticación y autorización:** Login, registro, recuperación, MFA, gestión de sesiones, roles y permisos avanzados.
- **Configuración global:** Parámetros de sistema, logging, monitoreo, auditoría, settings por BU.
- **Seguridad avanzada:** Encriptación, hash, detección de amenazas, cumplimiento normativo, políticas de acceso.

---

## 2.X Submódulos ATS: Desglose y Profundización

### 2.1 Chatbot Conversacional
**Descripción extendida:**
Chatbot multicanal con IA híbrida (NLP local + GPT), workflows dinámicos, contexto persistente, integración con assessments, notificaciones y gamificación. Soporta flujos por BU, onboarding, entrevistas, feedback, y seguimiento automatizado.

**Flujos y mejores prácticas:**
- Definir intents y entidades por BU y rol.
- Mantener contexto de usuario y estado conversacional.
- Integrar fallback a humano y logs de conversación.
- Usar triggers para disparar notificaciones, assessments y workflows.

**Endpoints principales:**
| Método | Endpoint                              | Descripción                        |
|--------|---------------------------------------|------------------------------------|
| POST   | /api/chatbot/message/                 | Enviar/recibir mensaje             |
| GET    | /api/chatbot/conversations/           | Listar conversaciones              |
| POST   | /api/chatbot/trigger/                 | Disparar workflow                  |

**Requerimientos de datos:**
- Tabla conversations: id, user_id, channel, started_at, ended_at, status.
- Tabla messages: id, conversation_id, sender, content, timestamp, intent, score.

**Ejemplo de payload:**
```json
{
  "conversation_id": 42,
  "message": "Quiero aplicar a la vacante de Data Scientist",
  "channel": "WhatsApp"
}
```

**Relación con otros módulos:**
- Dispara notificaciones, assessments, workflows y gamificación.
- Alimenta métricas y segmentación para Publish y ML.

---

### 2.2 Publish (ver sección 13.18 para detalle extendido)

---

### 2.3 Payments
**Descripción extendida:**
Gestión de transacciones, suscripciones, facturación y conciliación con Stripe, PayPal y bancos. Soporta pricing dinámico, reporting financiero y recomendaciones de monetización.

**Flujos y mejores prácticas:**
- Validar métodos de pago y conciliación automática.
- Automatizar facturación y reporting.
- Monitorear logs de transacciones y alertas de fraude.

**Endpoints principales:**
| Método | Endpoint                              | Descripción                        |
|--------|---------------------------------------|------------------------------------|
| POST   | /api/payments/charge/                 | Procesar pago                      |
| GET    | /api/payments/invoices/               | Listar facturas                    |
| GET    | /api/payments/transactions/           | Listar transacciones               |

**Requerimientos de datos:**
- Tabla payments: id, user_id, amount, method, status, created_at.
- Tabla invoices: id, payment_id, pdf_url, status, issued_at.

**Ejemplo de payload:**
```json
{
  "user_id": 101,
  "amount": 299.99,
  "method": "stripe"
}
```

**Relación con otros módulos:**
- Dispara notificaciones y workflows de upgrade/cancelación.
- Alimenta métricas de revenue y reporting global.

---

### 2.4 Notifications (ver sección 13.19 para detalle extendido)

---

### 2.5 Proposals
**Descripción extendida:**
Generación, negociación y firma electrónica de propuestas comerciales y técnicas. Soporta seguimiento de estado, comentarios, cambios y documentación legal.

**Flujos y mejores prácticas:**
- Usar plantillas para propuestas recurrentes.
- Automatizar seguimiento y recordatorios.
- Integrar firma digital y logs de cambios.

**Endpoints principales:**
| Método | Endpoint                              | Descripción                        |
|--------|---------------------------------------|------------------------------------|
| POST   | /api/proposals/                       | Crear propuesta                    |
| GET    | /api/proposals/{id}/                  | Detalle de propuesta               |
| POST   | /api/proposals/{id}/sign/             | Firmar propuesta                   |

**Requerimientos de datos:**
- Tabla proposals: id, client_id, status, created_at, updated_at, signed_at.
- Tabla proposal_comments: id, proposal_id, user_id, comment, timestamp.

**Ejemplo de payload:**
```json
{
  "client_id": 55,
  "template_id": 3,
  "custom_fields": {"precio": 12000, "plazo": "30 días"}
}
```

**Relación con otros módulos:**
- Dispara notificaciones y workflows de aprobación/firma.
- Alimenta métricas de conversión y revenue.

---

### 2.6 Feedback & Assessments (ver sección 13.22 para detalle extendido)

---

### 2.7 Referral
**Descripción extendida:**
Sistema de referidos con invitaciones, tracking, recompensas y analytics. Soporta campañas de referidos, ranking y gamificación.

**Flujos y mejores prácticas:**
- Automatizar invitaciones y tracking de referidos.
- Configurar recompensas y niveles de referidos.
- Monitorear conversiones y ranking.

**Endpoints principales:**
| Método | Endpoint                              | Descripción                        |
|--------|---------------------------------------|------------------------------------|
| POST   | /api/referral/invite/                 | Enviar invitación                  |
| GET    | /api/referral/track/                  | Tracking de referidos              |
| GET    | /api/referral/leaderboard/            | Ranking de referidos               |

**Requerimientos de datos:**
- Tabla referrals: id, referrer_id, referred_id, status, invited_at, converted_at.
- Tabla rewards: id, referral_id, type, value, issued_at.

**Ejemplo de payload:**
```json
{
  "referrer_id": 12,
  "email": "nuevo@ejemplo.com"
}
```

**Relación con otros módulos:**
- Dispara notificaciones y gamificación.
- Alimenta métricas de conversión y engagement.

---

### 2.8 Gamificación
**Descripción extendida:**
Sistema de niveles, logros, recompensas y leaderboard para motivar y retener usuarios. Soporta personalización por BU y tipo de usuario.

**Flujos y mejores prácticas:**
- Definir reglas de puntos y logros por acción.
- Automatizar entrega de recompensas y notificaciones.
- Monitorear engagement y churn.

**Endpoints principales:**
| Método | Endpoint                              | Descripción                        |
|--------|---------------------------------------|------------------------------------|
| GET    | /api/gamification/levels/             | Listar niveles                     |
| POST   | /api/gamification/achievements/       | Registrar logro                    |
| GET    | /api/gamification/leaderboard/        | Leaderboard                        |

**Requerimientos de datos:**
- Tabla levels: id, name, points_required, bu.
- Tabla achievements: id, user_id, type, awarded_at.
- Tabla leaderboard: id, user_id, score, rank.

**Ejemplo de payload:**
```json
{
  "user_id": 77,
  "achievement_type": "primer_aplicacion"
}
```

**Relación con otros módulos:**
- Se alimenta de acciones en Chatbot, Publish, Referral y Assessments.
- Alimenta dashboards de engagement y retención.

---

## 3.X Submódulos ML: Desglose y Profundización

### 3.1 GenIA
**Descripción extendida:**
Motor de generación de contenido inteligente (textos, emails, posts, landing pages, preguntas de assessment, etc.) usando NLP avanzado y modelos generativos. Soporta personalización por BU, canal, idioma y fase de campaña.

**Flujos y mejores prácticas:**
- Usar plantillas dinámicas y variables contextuales.
- Validar outputs antes de publicar.
- Monitorear logs de generación y feedback de usuarios.

**Endpoints principales:**
| Método | Endpoint                              | Descripción                        |
|--------|---------------------------------------|------------------------------------|
| POST   | /api/genia/generate/                  | Generar contenido                  |
| GET    | /api/genia/templates/                 | Listar plantillas                  |

**Requerimientos de datos:**
- Tabla genia_templates: id, name, content, channel, bu, language.
- Tabla genia_logs: id, template_id, user_id, output, created_at.

**Ejemplo de payload:**
```json
{
  "template_id": 5,
  "variables": {"nombre": "Ana", "vacante": "Data Scientist"}
}
```

**Relación con otros módulos:**
- Alimenta Publish, Chatbot, Assessments y Notificaciones.
- Se retroalimenta con feedback y métricas de engagement.

---

### 3.2 AURA
**Descripción extendida:**
Motor de segmentación avanzada y analítica predictiva. Realiza clustering, scoring, recomendaciones y retargeting inteligente. Soporta segmentación demográfica, profesional, comportamental y predictiva.

**Flujos y mejores prácticas:**
- Actualizar segmentos periódicamente según resultados y feedback.
- Usar A/B testing y cohortes para optimización.
- Monitorear métricas de segmentación y conversión.

**Endpoints principales:**
| Método | Endpoint                              | Descripción                        |
|--------|---------------------------------------|------------------------------------|
| POST   | /api/aura/segment/                    | Crear segmento                     |
| GET    | /api/aura/segments/                   | Listar segmentos                   |
| POST   | /api/aura/score/                      | Calcular scoring                   |

**Requerimientos de datos:**
- Tabla aura_segments: id, name, rules_json, bu, created_at.
- Tabla aura_scores: id, segment_id, user_id, score, updated_at.

**Ejemplo de payload:**
```json
{
  "name": "Senior Data Science",
  "rules": {"skills": ["Python", "ML"], "experiencia": ">5"}
}
```

**Relación con otros módulos:**
- Alimenta Publish, Chatbot, Assessments y el motor de retargeting.
- Se retroalimenta con métricas y feedback de campañas.

---

### 3.3 Gamification Analytics
**Descripción extendida:**
Analítica avanzada de engagement, retención y churn. Modelos de predicción de abandono, optimización de recompensas y motivadores personalizados.

**Flujos y mejores prácticas:**
- Monitorear engagement y churn en tiempo real.
- Ajustar reglas de gamificación según predicciones.
- Usar cohortes y A/B testing para validar cambios.

**Endpoints principales:**
| Método | Endpoint                              | Descripción                        |
|--------|---------------------------------------|------------------------------------|
| GET    | /api/gamif-analytics/engagement/      | Métricas de engagement             |
| GET    | /api/gamif-analytics/churn/           | Predicción de abandono             |

**Requerimientos de datos:**
- Tabla gamif_engagement: id, user_id, score, timestamp.
- Tabla gamif_churn: id, user_id, probability, timestamp.

**Ejemplo de payload:**
```json
{
  "user_id": 88
}
```

**Relación con otros módulos:**
- Alimenta dashboards de engagement y retención.
- Se retroalimenta con acciones de gamificación y feedback de usuarios.

---

### 3.4 Analyzers
**Descripción extendida:**
Conjunto de analizadores ML para CV, skills, talento, mercado, feedback, etc. Cada analyzer extrae insights, calcula scoring y alimenta el perfil ML de candidatos y campañas.

**Flujos y mejores prácticas:**
- Ejecutar analyzers tras cada evento relevante (nueva aplicación, assessment, feedback).
- Mantener logs y versionado de modelos.
- Validar outputs y ajustar thresholds según resultados.

**Endpoints principales:**
| Método | Endpoint                              | Descripción                        |
|--------|---------------------------------------|------------------------------------|
| GET    | /api/analyzers/                       | Listar analyzers                   |
| POST   | /api/analyzers/run/                   | Ejecutar analyzer                  |
| GET    | /api/analyzers/{id}/results/          | Resultados de analyzer             |

**Requerimientos de datos:**
- Tabla analyzers: id, name, type, config_json, last_run.
- Tabla analyzer_results: id, analyzer_id, entity_id, score, output_json, timestamp.

**Ejemplo de payload:**
```json
{
  "analyzer_id": 2,
  "entity_id": 123
}
```

**Relación con otros módulos:**
- Alimenta Assessments, Publish, Chatbot, Workflow y el motor de matchmaking ML.
- Se retroalimenta con feedback y resultados de campañas y evaluaciones.

---

## Relación ATS ↔ ML: Flujo de Datos y Aprendizaje

- Cada interacción en ATS (aplicación, assessment, feedback, conversación) genera datos que alimentan los analyzers ML.
- Los analyzers actualizan el perfil de candidatos, campañas y segmentos, mejorando el matchmaking y la personalización.
- Los resultados de ML (scoring, recomendaciones, predicciones) retroalimentan los flujos de ATS, optimizando la experiencia y los resultados de negocio.

```mermaid
flowchart TD
  ATS_EVENT["Evento ATS (aplicación, assessment, feedback, chat)"] --> ANALYZER["Analyzer ML"]
  ANALYZER --> PERFIL["Perfil ML actualizado"]
  PERFIL --> MATCH["Matchmaking y recomendaciones"]
  MATCH --> ATS_FLOW["Flujos ATS optimizados"]
  ATS_FLOW --> ATS_EVENT
```

---

## 4. Integraciones & APIs
- **APIs externas:** WhatsApp, Telegram, Email, Slack, Google Calendar, LinkedIn, Indeed, Stripe, PayPal, SendGrid, Webhooks, etc.
- **Sincronización en tiempo real:** Websockets, eventos, colas, cache warming, callbacks.
- **Automatización de flujos:** Webhooks, triggers, tareas programadas, integración con CRMs, ERPs, bolsas de trabajo.
- **Gestión de errores y métricas:** Logging, alertas, dashboards de integraciones.

---

## 5. UI/UX Moderno

### Diagrama de Componentes UI/UX
```mermaid
flowchart TD
  UIUX["UI/UX Moderno"]
  subgraph UIUX_Mods["Componentes UI/UX"]
    UIUX_DASH["Dashboards\n- Personalizables\n- Kanban\n- Analytics visual"]
    UIUX_MENUS["Menús dinámicos\n- Acceso por rol\n- Temas dinámicos"]
    UIUX_DRAG["Drag & Drop\n- Gestión de vacantes\n- Workflows"]
    UIUX_GAMIF["Gamificación visual\n- Logros\n- Leaderboard\n- Animaciones"]
    UIUX_RESP["Responsive\n- Mobile first\n- Accesibilidad"]
  end
  UIUX --> UIUX_DASH
  UIUX --> UIUX_MENUS
  UIUX --> UIUX_DRAG
  UIUX --> UIUX_GAMIF
  UIUX --> UIUX_RESP

  UIUX_DASH -->|"Muestra"| ATS_CHATBOT
  UIUX_DASH -->|"Muestra"| ATS_PUBLISH
  UIUX_DASH -->|"Muestra"| ML_GENIA
  UIUX_DASH -->|"Muestra"| ML_AURA
  UIUX_GAMIF -->|"Visualiza"| ATS_GAMIF
  UIUX_MENUS -->|"Acceso"| CORE
  UIUX_DRAG -->|"Gestiona"| ATS_PUBLISH
  UIUX_DRAG -->|"Gestiona"| ATS_CHATBOT
  UIUX_RESP -->|"Optimiza"| Todos
```

- **Glassmorphism, micro-interacciones, drag & drop, kanban boards, cards, animaciones, temas dinámicos y diseño responsivo.**
- **Menús dinámicos, dashboards personalizables, experiencia visual de clase mundial, accesibilidad y soporte multilingüe.**

---

## 6. Seguridad y Compliance

### Diagrama de Componentes de Seguridad
```mermaid
flowchart TD
  SEGURIDAD["Seguridad & Compliance"]
  subgraph SEGURIDAD_Mods["Componentes de Seguridad"]
    SEG_ENC["Encriptación\n- Datos en tránsito\n- Datos en reposo"]
    SEG_MFA["MFA\n- Autenticación 2FA\n- Políticas de acceso"]
    SEG_AUDIT["Auditoría\n- Logging\n- Monitoreo continuo"]
    SEG_THREAT["Detección de amenazas\n- SQLi\n- XSS\n- Brute force"]
    SEG_COMPL["Compliance\n- GDPR\n- SOC2\n- ISO27001\n- HIPAA"]
  end
  SEGURIDAD --> SEG_ENC
  SEGURIDAD --> SEG_MFA
  SEGURIDAD --> SEG_AUDIT
  SEGURIDAD --> SEG_THREAT
  SEGURIDAD --> SEG_COMPL

  SEG_ENC -->|"Protege"| ATS
  SEG_MFA -->|"Asegura"| CORE
  SEG_AUDIT -->|"Monitorea"| Todos
  SEG_THREAT -->|"Defiende"| Todos
  SEG_COMPL -->|"Certifica"| Todos
```

- **Encriptación avanzada de datos en tránsito y en reposo, MFA, auditoría, detección de amenazas, cumplimiento GDPR, SOC2, ISO27001, CCPA, HIPAA, políticas de acceso, roles y permisos avanzados.**

---

## 7. Escalabilidad Global

### Diagrama de Componentes de Escalabilidad
```mermaid
flowchart TD
  ESCALABILIDAD["Escalabilidad Global"]
  subgraph ESCALABILIDAD_Mods["Componentes de Escalabilidad"]
    ESC_MICRO["Microservicios\n- Modularidad\n- Independencia"]
    ESC_MULTI["Multi-tenant\n- Separación de clientes\n- Personalización"]
    ESC_BALANCE["Balanceo de carga\n- Alta disponibilidad"]
    ESC_CDN["CDN\n- Distribución global"]
    ESC_CACHE["Cache distribuido\n- Redis\n- Performance"]
    ESC_REGION["Multi-región\n- Despliegue global"]
  end
  ESCALABILIDAD --> ESC_MICRO
  ESCALABILIDAD --> ESC_MULTI
  ESCALABILIDAD --> ESC_BALANCE
  ESCALABILIDAD --> ESC_CDN
  ESCALABILIDAD --> ESC_CACHE
  ESCALABILIDAD --> ESC_REGION

  ESC_MICRO -->|"Permite"| Todos
  ESC_MULTI -->|"Personaliza"| ATS
  ESC_BALANCE -->|"Optimiza"| Todos
  ESC_CDN -->|"Acelera"| UIUX
  ESC_CACHE -->|"Mejora"| ML
  ESC_REGION -->|"Expande"| Todos
```

- **Microservicios, multi-tenant, balanceo de carga, CDN, cache distribuido, despliegue multi-región, soporte internacional.**

---

## 8. Infraestructura y Tecnología
- **Backend:** Django 4.2+, Django REST Framework, Celery, ASGI, asyncio.
- **Base de Datos:** PostgreSQL, Redis (cache avanzado).
- **Machine Learning:** TensorFlow, Scikit-learn, Hugging Face, spaCy, TextBlob.
- **Frontend/UI:** CSS avanzado, HTML5, integración con frameworks modernos.
- **Contenerización:** Docker, Docker Compose.
- **Monitoreo:** Sentry, Prometheus, Django Silk.

---

## 9. Instalación y Configuración

1. Clona el repositorio:
   ```bash
   git clone https://github.com/Grupo-huntRED/Grupo-huntRED-Chatbot.git
   cd Grupo-huntRED-Chatbot
   ```
2. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Configura variables de entorno y servicios externos (ver `.env.example`).
4. Ejecuta migraciones y arranca los servicios:
   ```bash
   python manage.py migrate
   python manage.py runserver
   # Para Celery y workers
   celery -A ai_huntred.celery_app worker -l info
   ```
5. Accede a la plataforma en `http://localhost:8000`

---

## 10. Documentación y Recursos
- [Guía de Integración del Chatbot](docs/CHATBOT_INTEGRATION_GUIDE.md)
- [Guía Técnica de AURA y GenIA](docs/AURA_COMPLETE_GUIDE.md)
- [Documentación de Arquitectura](docs/architecture.md)
- [Guía de UI/UX](static/css/advanced-ui-system.css)
- [Ejemplos de Workflows y Flujos por BU](docs/technical/workflows.md)

---

## 11. Contribución y Soporte
- Pull requests y sugerencias son bienvenidas.
- Para soporte, abre un issue o contacta a soporte@huntred.com

---

## 12. Licencia

Este proyecto es propiedad de Grupo huntRED® y está protegido por derechos de autor. Uso comercial, distribución y sublicenciamiento requieren autorización expresa.

---

## 13. Módulo de Marketing & Campañas Inteligentes (Motor huntRED® Publish)

### Visión General

El módulo **huntRED® Publish** es el motor centralizado de marketing, campañas y orquestación multicanal de Grupo huntRED®, diseñado para potenciar la atracción de clientes y candidatos a través de campañas inteligentes, automatizadas y calendarizadas, con integración total de IA (AURA, GenIA), analítica avanzada, retargeting, flujos de aprobación y firma digital, y dashboards de monitoreo en tiempo real.

#### Alcance y Unidades de Negocio
- **huntRED® executive, huntRED®, huntRED® Inspiration, huntRED® Experience, huntU, amigro, huntRED® Solutions**: Cada BU puede lanzar campañas, segmentar audiencias, calendarizar lanzamientos, automatizar publicaciones y medir resultados, todo desde un solo panel.
- **huntRED® Solutions**: Este motor permite análisis avanzados y consultoría de marketing para clientes externos, con potencial de monetización y escalabilidad global.

### Mapa de Funcionalidades

#### 1. Gestión Integral de Campañas
- Creación, edición, calendarización y publicación de campañas multicanal (redes sociales, bolsas de trabajo, email, WhatsApp, Telegram, web, etc.).
- Fases de campaña: Expectativa, Lanzamiento, Consolidación, Retargeting.
- Objetivos claros: Atracción de clientes, candidatos, awareness, engagement, conversión.

#### 2. Segmentación y Targeting Inteligente (AURA)
- Segmentación demográfica, profesional, comportamental y predictiva.
- Motor de audiencias dinámicas: actualización automática según comportamiento y resultados.
- Integración con AURA para clustering, scoring y recomendaciones de targeting.

#### 3. Retargeting y Automatización
- Motor de retargeting inteligente: re-engagement de leads, triggers automáticos, campañas adaptativas.
- Automatización de envíos, recordatorios, publicaciones y seguimiento.
- Integración con Celery para tareas periódicas y eventos.

#### 4. Integración Multicanal y APIs
- Publicación directa en LinkedIn, Indeed, OCC, Glassdoor, Monster, Telegram, WhatsApp, Email, Google Calendar.
- Sincronización de eventos y entrevistas con Google Calendar.
- Webhooks y APIs para integración con sistemas externos.

#### 5. Generación Inteligente de Contenido (GenIA)
- Plantillas dinámicas para posts, emails, anuncios, landing pages, webinars, blogs.
- Generación automática y personalizada de contenido por fase, canal, audiencia y BU.
- Sugerencias creativas y optimización SEO.

#### 6. Workflow de Aprobación y Firma Digital
- Flujos de aprobación multinivel para campañas y contenidos.
- Registro de revisiones, comentarios y cambios.
- Firma digital integrada (DocuSign, Adobe Sign, firma biométrica).
- Auditoría y trazabilidad completa.

#### 7. Analítica y Dashboards Avanzados
- Métricas de alcance, conversión, engagement, ROI, retención, efectividad de canales y segmentos.
- Dashboards personalizables por BU, campaña, canal y segmento.
- Alertas, reporting automático y exportación de datos.

#### 8. Monitoreo, Compliance y Escalabilidad
- Auditoría de acciones, logs de cambios, cumplimiento normativo (GDPR, CCPA, etc.).
- Escalabilidad multi-BU, multi-tenant y multi-región.
- Soporte para marketplace de campañas y servicios premium.

### Diagrama de Flujo de Funcionalidades

```mermaid
flowchart TD
  CAMPANA["Campaña Inteligente"]
  SEGMENTA["Segmentación AURA"]
  RETARGET["Retargeting"]
  CONTENIDO["Generación de Contenido GenIA"]
  APROBACION["Aprobación & Firma"]
  PUBLICA["Publicación Multicanal"]
  CALENDAR["Calendarización & Google Calendar"]
  ANALYTICS["Analytics & Dashboards"]
  MONITOREO["Monitoreo & Compliance"]

  CAMPANA --> SEGMENTA
  CAMPANA --> CONTENIDO
  CAMPANA --> CALENDAR
  CAMPANA --> APROBACION
  SEGMENTA --> RETARGET
  SEGMENTA --> PUBLICA
  RETARGET --> PUBLICA
  CONTENIDO --> PUBLICA
  APROBACION --> PUBLICA
  PUBLICA --> CALENDAR
  PUBLICA --> ANALYTICS
  PUBLICA --> MONITOREO
  ANALYTICS --> MONITOREO
```

### Modelos y Componentes Clave
- **Campaign, CampaignPhase, CampaignApproval, CampaignSignature, CampaignMetric, CampaignAuditLog**
- **Segment, Audience, RetargetingRule, ContentTemplate, Channel, JobBoardIntegration, CalendarEvent**
- **Dashboards avanzados en Django Admin para campañas, métricas, aprobaciones y logs**

### Automatizaciones y Tareas Periódicas
- Generación y envío automático de contenido y campañas.
- Actualización de segmentos y audiencias.
- Publicación programada en bolsas y redes.
- Recordatorios y seguimiento automatizado.

### Ejemplo de Fases y Contenido de Campaña
| Fase         | Objetivo                        | Contenido Sugerido (GenIA)                                   |
|--------------|---------------------------------|--------------------------------------------------------------|
| Expectativa  | Generar interés y awareness     | Teasers, posts de intriga, emails de pre-lanzamiento         |
| Lanzamiento  | Captar leads y candidatos       | Anuncios, posts destacados, webinars, landing pages          |
| Consolidación| Engagement y conversión         | Testimonios, casos de éxito, recordatorios, ofertas exclusivas|
| Retargeting  | Re-engagement y cierre          | Emails personalizados, mensajes directos, ofertas limitadas  |

### Flujos de Aprobación y Firma Digital
- **Creación de campaña** → **Revisión** → **Aprobación** → **Firma digital** → **Publicación**
- Trazabilidad completa, control de calidad, cumplimiento y escalabilidad.

### Potencial de Monetización
- Licenciamiento, servicios premium, marketplace de campañas, fees por performance.

### Futuro: huntRED® Solutions
- El motor puede ser la base para servicios avanzados de análisis y consultoría de marketing para clientes externos, con integración total a la plataforma huntRED®.

### 13.1 Arquitectura y Modelos del Módulo Publish

#### Modelos Principales
- **Campaign**: Representa una campaña de marketing/captación. Incluye nombre, BU, objetivos, fases, canales, segmentos, fechas, estado, responsables, presupuesto, métricas asociadas.
- **CampaignPhase**: Fases (expectativa, lanzamiento, consolidación, retargeting), con fechas, contenido, objetivos, instrucciones y calendarización.
- **CampaignApproval**: Flujo de revisiones, responsables, comentarios, timestamps, estado (pendiente, aprobado, rechazado).
- **CampaignSignature**: Firma digital, usuario, método (DocuSign, biométrica), hash, fecha, validez legal.
- **CampaignMetric**: Métricas de alcance, conversión, engagement, ROI, por canal, segmento, fase y BU.
- **CampaignAuditLog**: Registro de acciones, cambios, aprobaciones, incidencias, usuario, timestamp.
- **Segment**: Definición de segmentos (demográficos, profesionales, comportamentales, predictivos), reglas, criterios, integración AURA.
- **Audience**: Audiencias dinámicas, actualización automática, historial de interacción.
- **RetargetingRule**: Reglas de re-engagement, triggers, condiciones, acciones automáticas.
- **ContentTemplate**: Plantillas dinámicas para cada canal, fase, idioma, BU, con variables y lógica condicional.
- **Channel**: Canales soportados (LinkedIn, WhatsApp, Telegram, Email, Web, Google Calendar, bolsas de trabajo).
- **JobBoardIntegration**: Configuración y estado de integración con bolsas externas (Indeed, OCC, Glassdoor, Monster, etc.).
- **CalendarEvent**: Eventos calendarizados, integración Google Calendar, recordatorios, sincronización.

#### Relaciones y Flujos de Datos
```mermaid
erDiagram
  Campaign ||--o{ CampaignPhase : contiene
  Campaign ||--o{ CampaignApproval : requiere
  Campaign ||--o{ CampaignSignature : firma
  Campaign ||--o{ CampaignMetric : mide
  Campaign ||--o{ CampaignAuditLog : audita
  Campaign ||--o{ Segment : segmenta
  Segment ||--o{ Audience : agrupa
  Campaign ||--o{ RetargetingRule : reimpacta
  CampaignPhase ||--o{ ContentTemplate : usa
  Campaign ||--o{ Channel : publica
  Campaign ||--o{ JobBoardIntegration : integra
  Campaign ||--o{ CalendarEvent : agenda
```

---

### 13.2 Ciclo de Vida de una Campaña Inteligente
1. **Ideación y Creación**: Selección de BU, objetivos, canales, presupuesto, responsables.
2. **Segmentación**: Definición de segmentos y audiencias con AURA (demográficos, skills, comportamiento, predicción de éxito).
3. **Generación de Contenido**: Uso de plantillas GenIA, personalización por fase, canal, idioma, BU.
4. **Calendarización**: Asignación de fechas, eventos, recordatorios, integración Google Calendar.
5. **Aprobación y Firma**: Flujo multinivel, revisiones, comentarios, firma digital, compliance.
6. **Publicación Multicanal**: Automatizada en redes, bolsas, email, chat, web, calendar.
7. **Automatización y Retargeting**: Triggers, reglas, re-engagement, seguimiento automático.
8. **Monitoreo y Métricas**: Dashboards en tiempo real, alertas, reporting, exportación.
9. **Cierre y Análisis**: Evaluación de resultados, feedback, logs, aprendizaje para futuras campañas.

---

### 13.3 Automatizaciones y Lógica de Negocio
- **Tareas periódicas (Celery):**
  - Generación y envío de contenido.
  - Actualización de segmentos y audiencias.
  - Publicación programada y seguimiento.
  - Recordatorios y alertas automáticas.
  - Recolecta y análisis de métricas.
- **Triggers y eventos:**
  - Cambios de estado de campaña/fase.
  - Interacciones de usuarios (apertura, clic, respuesta).
  - Resultados de retargeting y engagement.
- **Fallback y resiliencia:**
  - Reintentos automáticos, logs de error, alertas a admins.

---

### 13.4 Integración Multicanal y APIs
- **LinkedIn, WhatsApp, Telegram, Email, Web:**
  - Autenticación OAuth/API Key, callbacks, manejo de errores, reporting de entregas.
  - Personalización de mensajes, adjuntos, multimedia.
- **Google Calendar:**
  - Creación y actualización de eventos, recordatorios, sincronización bidireccional.
- **Bolsas de trabajo (Indeed, OCC, Glassdoor, Monster):**
  - Publicación automática, scraping de resultados, tracking de postulaciones.
- **Webhooks y APIs externas:**
  - Integración con CRMs, ERPs, sistemas de clientes.

---

### 13.5 Dashboards y Vistas Admin
- **Dashboards avanzados:**
  - Filtros por BU, campaña, canal, segmento, fase, fecha.
  - Visualizaciones: gráficos de conversión, embudos, mapas de calor, cohortes, comparativas.
  - Exportación a Excel, PDF, API.
  - Alertas configurables (umbral de conversión, engagement bajo, incidencias).
- **Vistas admin:**
  - Gestión de campañas, fases, aprobaciones, firmas, métricas, logs.
  - Workflows visuales, historial de cambios, auditoría.

---

### 13.6 Ejemplos de Casos de Uso por Unidad de Negocio
- **huntRED® executive:** Campañas de headhunting premium, targeting por skills y seniority, retargeting a ejecutivos pasivos.
- **huntRED®:** Campañas masivas de atracción, integración con bolsas, webinars, retargeting a candidatos inactivos.
- **huntRED® Inspiration:** Inclusión laboral, campañas segmentadas por discapacidad, contenido accesible, integración con ONGs.
- **huntRED® Experience:** Atracción de talento senior, campañas de mentoring, eventos calendarizados, retargeting por experiencia.
- **huntU:** Campañas universitarias, ferias de empleo, integración con bolsas universitarias, retargeting a egresados.
- **amigro:** Campañas de integración migrante, contenido multilingüe, segmentación por país de origen, retargeting a comunidades.
- **huntRED® Solutions:** Consultoría avanzada, análisis de campañas de clientes, dashboards personalizados, reporting ejecutivo.

---

### 13.7 Segmentación Avanzada y Retargeting (AURA + GenIA)
- **Segmentación dinámica:**
  - Por perfil profesional, skills, historial de interacción, engagement, predicción de éxito.
  - Actualización automática según resultados y feedback.
- **Retargeting inteligente:**
  - Reglas adaptativas, triggers por comportamiento, personalización de mensajes y canales.
  - Integración con GenIA para generación de contenido específico de re-engagement.

---

### 13.8 Compliance, Seguridad y Auditoría
- **Flujos de aprobación y firma digital:**
  - Registro de revisiones, comentarios, responsables, timestamps, hash de documentos.
  - Integración con DocuSign, Adobe Sign, firma biométrica.
- **Auditoría y logs:**
  - Registro de todas las acciones, cambios, incidencias, accesos.
  - Exportación y reporting para compliance (GDPR, CCPA, ISO, SOC2).
- **Seguridad:**
  - Encriptación de datos, control de acceso granular, MFA, alertas de seguridad.

---

### 13.9 Personalización, Escalabilidad y Futuro
- **Multi-BU, multi-idioma, multi-región:**
  - Personalización de campañas, contenido, métricas y dashboards por unidad, idioma y región.
- **Marketplace de campañas y servicios premium:**
  - Plantillas, automatizaciones, analítica avanzada como productos.
- **Integración con huntRED® Solutions:**
  - Exportación de datos, dashboards ejecutivos, consultoría avanzada, integración con sistemas de clientes.

---

### 13.10 Glosario de Términos y Roles
- **BU:** Unidad de Negocio (ejecutive, Inspiration, Experience, etc.)
- **AURA:** Motor de segmentación y analítica predictiva.
- **GenIA:** Motor de generación de contenido inteligente.
- **Retargeting:** Estrategia de re-impacto a leads/candidatos no convertidos.
- **Celery:** Sistema de tareas asíncronas y automatización.
- **Admin:** Usuario con permisos de gestión y monitoreo.
- **Responsable de campaña:** Usuario encargado de la creación, seguimiento y resultados de campañas.
- **Aprobador:** Usuario con permisos para revisar y aprobar campañas/contenido.
- **Firmante:** Usuario autorizado para firma digital y validación legal.

---

### 13.11 Diagrama de Flujo de Usuario y Datos
```mermaid
flowchart TD
  U["Usuario/Admin"] -->|Crea| C["Campaña"]
  C -->|Define| S["Segmento/Audiencia"]
  C -->|Genera| CT["Contenido (GenIA)"]
  C -->|Calendariza| EV["Evento Calendar"]
  C -->|Solicita| AP["Aprobación"]
  AP -->|Firma| F["Firma Digital"]
  C -->|Publica| CH["Canal/Bolsa"]
  CH -->|Entrega| AU["Audiencia"]
  AU -->|Interacciona| M["Métricas"]
  M -->|Alimenta| RT["Retargeting"]
  C -->|Monitorea| D["Dashboard"]
  D -->|Audita| L["Logs/Auditoría"]
```

---

### 13.12 Ejemplos de Payloads y Endpoints API

#### Crear una campaña (POST /api/publish/campaign/)
```json
{
  "name": "Campaña Talento Senior 2025",
  "business_unit": "huntRED Experience",
  "objectives": ["Atracción de talento senior", "Engagement"],
  "phases": [
    {"name": "Expectativa", "start_date": "2025-01-10", "end_date": "2025-01-20"},
    {"name": "Lanzamiento", "start_date": "2025-01-21", "end_date": "2025-02-10"}
  ],
  "channels": ["LinkedIn", "Email", "Google Calendar"],
  "segments": [1, 2],
  "budget": 5000
}
```

#### Respuesta exitosa
```json
{
  "id": 101,
  "status": "pending_approval",
  "created_at": "2025-01-05T12:00:00Z"
}
```

#### Ejemplo de endpoint para métricas de campaña (GET /api/publish/campaign/101/metrics/)
```json
{
  "reach": 12000,
  "clicks": 950,
  "applications": 120,
  "conversion_rate": 0.126,
  "engagement_score": 87,
  "by_channel": {
    "LinkedIn": {"reach": 8000, "applications": 80},
    "Email": {"reach": 3000, "applications": 30},
    "Google Calendar": {"events": 10, "attendance": 7}
  }
}
```

#### Fragmento de automatización (Python/Celery)
```python
from app.ats.publish.tasks import send_campaign_content
send_campaign_content.apply_async(args=[campaign_id], eta=scheduled_time)
```

---

### 13.13 Ejemplo de Plantilla de Contenido Dinámico

```jinja
Asunto: ¡{{ campaign.name }} ya está aquí!

Hola {{ user.first_name }},

Te invitamos a participar en la campaña {{ campaign.name }} de {{ campaign.business_unit }}.

{{ phase.instructions }}

Para más información, visita: {{ campaign.landing_page_url }}

--
Equipo huntRED®
```

- Variables soportadas: `{{ user.first_name }}`, `{{ campaign.name }}`, `{{ campaign.business_unit }}`, `{{ phase.instructions }}`, `{{ campaign.landing_page_url }}`
- Soporte para condicionales, loops y traducción automática.

---

### 13.14 Ejemplo de Métricas y Dashboard

| Métrica              | Descripción                                 | Ejemplo |
|----------------------|---------------------------------------------|---------|
| Alcance (reach)      | Personas impactadas por la campaña          | 12,000  |
| Clics                | Interacciones en enlaces/contenido          | 950     |
| Aplicaciones         | Candidatos que aplicaron                    | 120     |
| Tasa de conversión   | Aplicaciones / Alcance                      | 12.6%   |
| Engagement Score     | Índice ponderado de interacción             | 87      |
| ROI                  | Retorno sobre inversión                     | 3.2     |
| Retargeting Impact   | % de leads recuperados por retargeting      | 18%     |

#### Visualización de Dashboard (ejemplo)
```mermaid
flowchart LR
  A[Alcance] --> B[Clics]
  B --> C[Aplicaciones]
  C --> D[Contrataciones]
  C --> E[Retargeting]
  E --> C
  D --> F[ROI]
```

---

### 13.15 Buenas Prácticas de Operación y Mantenimiento
- **Checklist para admins y responsables de campaña:**
  - Revisar y actualizar segmentos y audiencias antes de cada campaña.
  - Validar plantillas y contenido en todos los canales y dispositivos.
  - Calendarizar revisiones y aprobaciones con antelación.
  - Monitorear dashboards y configurar alertas de métricas clave.
  - Documentar aprendizajes y feedback tras cada campaña.
- **Recomendaciones para escalar y asegurar calidad:**
  - Usar automatizaciones para tareas repetitivas y reporting.
  - Realizar pruebas de integración antes de lanzar nuevas conexiones API.
  - Mantener logs y auditoría activos para trazabilidad y compliance.
  - Capacitar a los equipos en el uso de dashboards y workflows.

---

### 13.16 Ejemplo de Flujo de Error y Fallback
- **Escenario:** Falla la publicación en LinkedIn por error de autenticación.
- **Flujo:**
  1. El sistema detecta el error y lo registra en `CampaignAuditLog`.
  2. Se reintenta la publicación hasta 3 veces (con backoff exponencial).
  3. Si persiste el error, se notifica automáticamente al admin responsable y se sugiere acción manual.
  4. El dashboard muestra la incidencia y el estado pendiente de resolución.
  5. Una vez resuelto, se puede reintentar la acción desde la vista admin.
- **Ventajas:** Resiliencia, trazabilidad, mínima pérdida de oportunidades.

---

### 13.17 Mantener la Documentación Viva
- **Proceso recomendado:**
  - Actualizar el README.md tras cada release mayor o cambio estructural.
  - Documentar endpoints, modelos y flujos nuevos en la sección correspondiente.
  - Incluir ejemplos de payloads y casos de uso reales.
  - Revisar y mejorar la documentación tras feedback de usuarios y clientes.
  - Fomentar la colaboración: cualquier miembro del equipo puede proponer mejoras vía pull request.
- **Herramientas sugeridas:**
  - Integrar documentación técnica con herramientas como Swagger/OpenAPI para APIs.
  - Usar diagramas Mermaid para mantener flujos y relaciones actualizados.
  - Mantener un changelog y una wiki interna para detalles avanzados.

---

### 13.18 Módulo Publish (Campañas y Marketing)

**Descripción:**
Motor centralizado para la gestión, calendarización y automatización de campañas multicanal, con integración de IA, retargeting, plantillas dinámicas y métricas avanzadas.

**Mejores prácticas:**
- Validar objetivos, segmentos y canales antes de lanzar campañas.
- Calendarizar fases y automatizar recordatorios.
- Usar plantillas GenIA para personalización y coherencia de marca.
- Monitorear métricas y ajustar campañas en tiempo real.
- Mantener logs de cambios y aprobaciones para auditoría.

**Endpoints REST principales:**
| Método | Endpoint                          | Descripción                        |
|--------|-----------------------------------|------------------------------------|
| GET    | /api/publish/campaigns/           | Listar campañas                    |
| POST   | /api/publish/campaigns/           | Crear campaña                      |
| GET    | /api/publish/campaigns/{id}/      | Detalle de campaña                 |
| PATCH  | /api/publish/campaigns/{id}/      | Actualizar campaña                 |
| POST   | /api/publish/campaigns/{id}/launch/| Lanzar campaña                    |
| GET    | /api/publish/campaigns/{id}/metrics/| Métricas de campaña              |
| POST   | /api/publish/campaigns/{id}/approve/| Aprobar campaña                  |
| POST   | /api/publish/campaigns/{id}/sign/ | Firmar digitalmente                |

**Requerimientos de base de datos:**
- Tabla campaigns: id, name, business_unit, objectives, status, created_at, updated_at, owner_id, budget.
- Tabla campaign_phases: id, campaign_id, name, start_date, end_date, instructions.
- Índices en business_unit, status, created_at.
- Registros mínimos: al menos una campaña activa por BU para pruebas.

**Casos de uso y recomendaciones:**
- Usar campañas de prueba para validar integraciones y flujos.
- Revisar métricas tras cada fase y ajustar targeting/segmentos.
- Documentar aprendizajes y feedback en cada cierre de campaña.

**Relación con otros módulos:**
- Consume segmentos de Segment, plantillas de ContentTemplate, métricas de Metrics, y se integra con Notificaciones y Workflow.

---

### 13.19 Módulo Notificaciones

**Descripción:**
Gestión de alertas, notificaciones automáticas y multicanal (email, chat, SMS, push, Slack), con tracking de entregas y plantillas personalizadas.

**Mejores prácticas:**
- Usar plantillas multilingües y personalizadas por BU.
- Configurar alertas críticas y de seguimiento.
- Monitorear logs de entrega y apertura.
- Mantener fallback a canales alternativos en caso de fallo.

**Endpoints REST principales:**
| Método | Endpoint                              | Descripción                        |
|--------|---------------------------------------|------------------------------------|
| GET    | /api/notifications/                   | Listar notificaciones              |
| POST   | /api/notifications/                   | Enviar notificación                |
| GET    | /api/notifications/{id}/              | Detalle de notificación            |
| GET    | /api/notifications/{id}/status/       | Estado de entrega                  |
| POST   | /api/notifications/templates/         | Crear plantilla                    |

**Requerimientos de base de datos:**
- Tabla notifications: id, recipient_id, channel, status, sent_at, opened_at, template_id.
- Tabla notification_templates: id, name, content, language, bu.
- Índices en recipient_id, channel, status.
- Registros mínimos: una plantilla y una notificación enviada por canal.

**Casos de uso y recomendaciones:**
- Configurar notificaciones automáticas para eventos clave (aplicación, entrevista, feedback).
- Usar tracking para medir efectividad y ajustar mensajes.

**Relación con otros módulos:**
- Se dispara desde Publish, Chatbot, Workflow y Assessments.

---

### 13.20 Módulo Chatbot

**Descripción:**
Chatbot conversacional multicanal (WhatsApp, Telegram, Web, Email, Slack, SMS) con workflows dinámicos, integración ML/NLP, contexto persistente y gamificación.

**Mejores prácticas:**
- Definir flujos por BU y rol, con fallback a humano.
- Mantener contexto y estado de usuario para personalización.
- Integrar evaluaciones y feedback en el flujo conversacional.
- Monitorear logs de conversación y métricas de engagement.

**Endpoints REST principales:**
| Método | Endpoint                              | Descripción                        |
|--------|---------------------------------------|------------------------------------|
| POST   | /api/chatbot/message/                 | Enviar/recibir mensaje             |
| GET    | /api/chatbot/conversations/           | Listar conversaciones              |
| GET    | /api/chatbot/conversations/{id}/      | Detalle de conversación            |
| POST   | /api/chatbot/trigger/                 | Disparar workflow                  |
| GET    | /api/chatbot/analytics/               | Métricas de uso y engagement       |

**Requerimientos de base de datos:**
- Tabla conversations: id, user_id, channel, started_at, ended_at, status.
- Tabla messages: id, conversation_id, sender, content, timestamp, intent, score.
- Índices en user_id, channel, status.
- Registros mínimos: una conversación y dos mensajes por canal.

**Casos de uso y recomendaciones:**
- Usar workflows guiados para onboarding, aplicación y feedback.
- Analizar intents y respuestas para mejorar el NLP y la experiencia.

**Relación con otros módulos:**
- Dispara notificaciones, assessments, workflows y gamificación.
- Alimenta métricas y segmentación para Publish y ML.

---

### 13.21 Módulo Workflow

**Descripción:**
Orquestador de procesos y flujos de negocio (aplicación, selección, entrevistas, onboarding, feedback), con lógica condicional, triggers y tareas automáticas.

**Mejores prácticas:**
- Definir workflows reutilizables y versionados por BU.
- Usar triggers para automatizar tareas y notificaciones.
- Monitorear logs de ejecución y tiempos de cada etapa.

**Endpoints REST principales:**
| Método | Endpoint                              | Descripción                        |
|--------|---------------------------------------|------------------------------------|
| GET    | /api/workflows/                       | Listar workflows                   |
| POST   | /api/workflows/                       | Crear workflow                     |
| GET    | /api/workflows/{id}/                  | Detalle de workflow                |
| POST   | /api/workflows/{id}/trigger/          | Disparar ejecución                 |
| GET    | /api/workflows/{id}/logs/             | Logs de ejecución                  |

**Requerimientos de base de datos:**
- Tabla workflows: id, name, business_unit, version, status, created_at.
- Tabla workflow_steps: id, workflow_id, name, order, type, config_json.
- Tabla workflow_logs: id, workflow_id, step_id, status, started_at, ended_at.
- Índices en business_unit, status, version.
- Registros mínimos: un workflow con dos pasos y un log de ejecución.

**Casos de uso y recomendaciones:**
- Usar workflows para automatizar procesos repetitivos y asegurar compliance.
- Versionar y documentar cambios para trazabilidad.

**Relación con otros módulos:**
- Orquesta campañas, assessments, notificaciones y tareas de Publish.

---

### 13.22 Módulo Assessments & Analyzers

**Descripción:**
Gestión de evaluaciones técnicas, culturales, psicométricas y feedback 360°, con integración directa a analyzers ML para scoring, insights y matchmaking.

**Mejores prácticas:**
- Validar la integridad de los datos antes de procesar.
- Usar triggers para recalcular scoring y actualizar el perfil ML tras cada evaluación.
- Mantener logs de cambios y resultados para auditoría.

**Endpoints REST principales:**
| Método | Endpoint                              | Descripción                        |
|--------|---------------------------------------|------------------------------------|
| GET    | /api/assessments/                     | Listar evaluaciones                |
| POST   | /api/assessments/                     | Crear evaluación                   |
| GET    | /api/assessments/{id}/                | Detalle de evaluación              |
| POST   | /api/assessments/{id}/submit/         | Enviar respuestas                  |
| GET    | /api/assessments/{id}/results/        | Obtener resultados y scoring       |
| GET    | /api/analyzers/                       | Listar analyzers                   |
| POST   | /api/analyzers/run/                   | Ejecutar analyzer manualmente      |

**Requerimientos de base de datos:**
- Tabla assessments: id, candidate_id, type, status, created_at, updated_at.
- Tabla assessment_questions: id, assessment_id, question_id, respuesta, score.
- Tabla analyzers: id, name, type, config_json, last_run.
- Índices en candidate_id, type, analyzer_id.
- Registros mínimos: una evaluación, un analyzer y un resultado asociado.

**Capacidades analíticas y relación con ML:**
- Cada assessment dispara un analyzer (ej: TechnicalSkillAnalyzer) que actualiza el perfil ML del candidato.
- Los resultados alimentan el módulo de matchmaking, mejorando la precisión de sugerencias y rankings.
- Soporte para feedback automático y manual, enriqueciendo los datos de entrenamiento ML.

**Casos de uso y recomendaciones:**
- Mantener histórico de evaluaciones para análisis longitudinal.
- Permitir feedback y revisión de resultados para mejora continua.

**Relación con otros módulos:**
- Alimenta Publish, Chatbot, Workflow y el módulo ML de matchmaking.

---

### 13.23 Módulo Integraciones de Canales

**Descripción:**
Gestión y actualización de integraciones con canales externos (WhatsApp, Telegram, Email, LinkedIn, Google Calendar, bolsas de trabajo, etc.), con soporte para versionado y adaptación a nuevas plataformas.

**Mejores prácticas:**
- Usar configuración centralizada y versionado para cada integración.
- Monitorear logs de errores y cambios de API.
- Documentar endpoints, scopes y permisos requeridos.
- Implementar pruebas automáticas de endpoints críticos.

**Endpoints REST principales:**
| Método | Endpoint                              | Descripción                        |
|--------|---------------------------------------|------------------------------------|
| GET    | /api/integrations/                    | Listar integraciones activas       |
| POST   | /api/integrations/                    | Registrar nueva integración        |
| PATCH  | /api/integrations/{id}/               | Actualizar configuración           |
| GET    | /api/integrations/{id}/status/        | Verificar estado y versión         |
| POST   | /api/integrations/{id}/test/          | Probar integración                 |

**Requerimientos de base de datos:**
- Tabla integrations: id, name, type, config_json, status, version, last_checked.
- Índices en name, type, status.
- Registros mínimos: una integración activa por canal principal.

**Mantenimiento y actualización:**
- Revisar periódicamente la documentación oficial de cada canal.
- Si surge una nueva plataforma (ej: nueva red de META), seguir el proceso: análisis de API, desarrollo de integración, pruebas, despliegue y documentación.
- Mantener changelog de integraciones y comunicar cambios a usuarios/admins.
- Implementar fallback y alertas ante cambios inesperados.

**Casos de uso y recomendaciones:**
- Probar integraciones tras cada actualización de API.
- Documentar incidencias y soluciones para futuras referencias.

**Relación con otros módulos:**
- Soporta Publish, Notificaciones, Chatbot, Workflow y Assessments.

---

### 13.24 Extracción de Candidatos desde SmartRecruiters sin API Key (Web Scraping)

Si no cuentas con una API Key de SmartRecruiters, puedes extraer tus candidatos y CVs mediante web scraping automatizado del portal web. Esta opción es útil para migraciones masivas o recuperación de datos históricos cuando la API no está disponible.

#### ¿Cómo funciona?
- Se utiliza un script basado en Playwright (o Selenium) que automatiza el login, la navegación y la descarga de datos y CVs desde la interfaz web de SmartRecruiters.
- El script recorre la lista de candidatos, extrae sus datos y descarga los CVs adjuntos uno a uno.

#### Ventajas
- No requiere permisos de API ni cuenta premium.
- Permite obtener grandes volúmenes de datos (más de 50,000 candidatos) de manera ordenada.

#### Limitaciones y advertencias
- El scraping puede romperse si SmartRecruiters cambia el diseño de la web.
- Puede estar limitado por captchas, autenticación 2FA o políticas de uso.
- Requiere mantener credenciales de usuario y manejar cookies de sesión.
- Úsalo bajo tu propio riesgo y revisa los Términos de Servicio de SmartRecruiters.
- No es recomendable para automatizaciones recurrentes, solo para migraciones puntuales.

#### Requerimientos
- Python 3.8+
- playwright (`pip install playwright` y `playwright install`)
- Credenciales válidas de usuario SmartRecruiters

#### Ejemplo de uso
```python
from app.ats.integrations.smartrecruiters import SmartRecruitersWebScraper
import asyncio

scraper = SmartRecruitersWebScraper(username='pablo@huntred.com', password='Latituded800!')
async def run_scraping():
    await scraper.initialize()
    await scraper.login()
    candidates = await scraper.scrape_candidates(max_pages=1000)
    await scraper.close()
    print(f"Total candidatos extraídos: {len(candidates)}")

asyncio.run(run_scraping())
```

#### Recomendaciones para grandes volúmenes
- Divide la extracción en lotes (por ejemplo, 1000 candidatos por sesión).
- Monitorea el uso de recursos y el avance del scraping.
- Filtra y procesa solo los formatos de CV soportados (PDF, DOCX).
- Almacena los datos y CVs en tu base de datos y ejecuta el parsing con CVParser.

#### Alternativas
- Si tienes acceso a la API Key, usa la integración oficial (más robusta y escalable).
- Si necesitas una exportación masiva y ordenada, contacta al soporte de SmartRecruiters para solicitar un dump completo de tus datos y archivos.

---