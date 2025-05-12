"""
Sistema de plantillas para notificaciones.

Proporciona plantillas para los diferentes tipos de notificaciones
y funciones para renderizar contenido basado en contexto.
"""

import logging
from typing import Dict, Any, Optional
from django.template import Template, Context
from django.template.loader import get_template
from django.utils.html import strip_tags

from app.models import Person, BusinessUnit, Vacante

logger = logging.getLogger('notifications')

# Plantillas para responsable de proceso
PROCESO_CREADO_TEMPLATE = {
    'title': "Nuevo proceso de reclutamiento creado: {{ vacante.title }}",
    'content': """
    <p>Estimado/a {{ recipient.nombre }},</p>
    
    <p>Se ha creado un nuevo proceso de reclutamiento para la vacante <strong>{{ vacante.title }}</strong> 
    en la empresa <strong>{{ vacante.empresa.nombre }}</strong> para la unidad de negocio <strong>{{ business_unit.name }}</strong>.</p>
    
    <p>Detalles de la vacante:</p>
    <ul>
        <li><strong>Puesto:</strong> {{ vacante.title }}</li>
        <li><strong>Empresa:</strong> {{ vacante.empresa.nombre }}</li>
        <li><strong>Localización:</strong> {{ vacante.location }}</li>
        <li><strong>Salario:</strong> {% if vacante.salary %}{{ vacante.salary }}{% else %}No especificado{% endif %}</li>
    </ul>
    
    <p>Por favor, comienza a trabajar en este proceso según lo establecido en nuestros procedimientos.</p>
    
    <p>Saludos cordiales,<br>
    El equipo de {{ business_unit.name }}</p>
    """
}

FEEDBACK_REQUERIDO_TEMPLATE = {
    'title': "Feedback requerido: Entrevista con {{ candidato.nombre }}",
    'content': """
    <p>Estimado/a {{ recipient.nombre }},</p>
    
    <p>Necesitamos tu feedback sobre la entrevista realizada con <strong>{{ candidato.nombre }}</strong> 
    para la vacante <strong>{{ vacante.title }}</strong>.</p>
    
    <p>Por favor, completa el formulario de evaluación en las próximas 24 horas para poder continuar 
    con el proceso de selección.</p>
    
    <p><a href="{{ feedback_url }}">Completar evaluación aquí</a></p>
    
    <p>Datos del candidato:</p>
    <ul>
        <li><strong>Nombre:</strong> {{ candidato.nombre }}</li>
        <li><strong>Posición actual:</strong> {{ candidato.current_position }}</li>
        <li><strong>Fecha de entrevista:</strong> {{ entrevista_fecha|date:"d/m/Y H:i" }}</li>
    </ul>
    
    <p>Saludos cordiales,<br>
    El equipo de {{ business_unit.name }}</p>
    """
}

CONFIRMACION_ENTREVISTA_TEMPLATE = {
    'title': "Entrevista confirmada con {{ candidato.nombre }} para {{ vacante.title }}",
    'content': """
    <p>Estimado/a {{ recipient.nombre }},</p>
    
    <p>Se ha confirmado la entrevista con <strong>{{ candidato.nombre }}</strong> para la vacante
    <strong>{{ vacante.title }}</strong>.</p>
    
    <p>Detalles de la entrevista:</p>
    <ul>
        <li><strong>Fecha y hora:</strong> {{ entrevista_fecha|date:"d/m/Y H:i" }}</li>
        <li><strong>Tipo:</strong> {% if entrevista_virtual %}Virtual{% else %}Presencial{% endif %}</li>
        {% if entrevista_virtual %}<li><strong>Enlace:</strong> <a href="{{ entrevista_link }}">{{ entrevista_link }}</a></li>{% endif %}
        {% if entrevista_lugar %}<li><strong>Lugar:</strong> {{ entrevista_lugar }}</li>{% endif %}
    </ul>
    
    <p>Por favor, prepárate para la entrevista y asegúrate de revisar el perfil del candidato y la descripción de la vacante.</p>
    
    <p>Saludos cordiales,<br>
    El equipo de {{ business_unit.name }}</p>
    """
}

FELICITACION_CONTRATACION_TEMPLATE = {
    'title': "¡Felicidades! Contratación exitosa para {{ vacante.title }}",
    'content': """
    <p>¡Felicidades {{ recipient.nombre }}!</p>
    
    <p>Nos complace informarte que el candidato <strong>{{ candidato.nombre }}</strong> ha sido 
    contratado con éxito para la vacante <strong>{{ vacante.title }}</strong> en
    <strong>{{ vacante.empresa.nombre }}</strong>.</p>
    
    <p>Este logro refleja tu excelente trabajo en el proceso de reclutamiento y selección. 
    El cliente ha expresado su satisfacción con el candidato seleccionado.</p>
    
    <p>Detalles importantes:</p>
    <ul>
        <li><strong>Fecha de incorporación:</strong> {{ fecha_incorporacion|date:"d/m/Y" }}</li>
        <li><strong>Paquete salarial:</strong> {{ paquete_salarial }}</li>
        <li><strong>Comisión generada:</strong> {{ comision }}</li>
    </ul>
    
    <p>Recuerda solicitar el feedback final del cliente sobre el proceso completo para nuestro 
    seguimiento de calidad.</p>
    
    <p>Gracias por tu dedicación y compromiso.</p>
    
    <p>Saludos cordiales,<br>
    El equipo de {{ business_unit.name }}</p>
    """
}

# Plantillas para contacto en cliente
FIRMA_CONTRATO_TEMPLATE = {
    'title': "Solicitud de firma para contrato de {{ vacante.title }}",
    'content': """
    <p>Estimado/a {{ recipient.nombre }},</p>
    
    <p>Hemos preparado el contrato para el servicio de reclutamiento de la vacante <strong>{{ vacante.title }}</strong>.</p>
    
    <p>El contrato incluye los términos y condiciones discutidos previamente, incluyendo:</p>
    <ul>
        <li>Descripción detallada del servicio</li>
        <li>Honorarios y método de pago</li>
        <li>Garantías del servicio</li>
        <li>Plazos de entrega</li>
    </ul>
    
    <p>Por favor, revise el documento y proceda a firmarlo electrónicamente a través del siguiente enlace:</p>
    
    <p><a href="{{ firma_url }}">Firmar contrato</a></p>
    
    <p>El enlace expirará en 7 días. Si tiene alguna pregunta o necesita modificaciones al contrato, 
    no dude en contactarnos.</p>
    
    <p>Saludos cordiales,<br>
    El equipo de {{ business_unit.name }}</p>
    """
}

EMISION_PROPUESTA_TEMPLATE = {
    'title': "Nueva propuesta de servicio para {{ vacante.title }}",
    'content': """
    <p>Estimado/a {{ recipient.nombre }},</p>
    
    <p>Nos complace presentarle nuestra propuesta de servicios para el reclutamiento 
    de la posición <strong>{{ vacante.title }}</strong>.</p>
    
    <p>Nuestra propuesta incluye:</p>
    <ul>
        <li>Estrategia de búsqueda personalizada</li>
        <li>Proceso de selección riguroso</li>
        <li>Evaluaciones especializadas</li>
        <li>Verificación de antecedentes</li>
        <li>Garantía de reemplazo</li>
    </ul>
    
    <p>Puede acceder a la propuesta completa a través del siguiente enlace:</p>
    
    <p><a href="{{ propuesta_url }}">Ver propuesta completa</a></p>
    
    <p>Estamos disponibles para cualquier consulta o para agendar una reunión 
    donde podamos discutir los detalles de nuestra propuesta.</p>
    
    <p>Saludos cordiales,<br>
    El equipo de {{ business_unit.name }}</p>
    """
}

CANDIDATOS_DISPONIBLES_TEMPLATE = {
    'title': "Candidatos disponibles para {{ vacante.title }}",
    'content': """
    <p>Estimado/a {{ recipient.nombre }},</p>
    
    <p>Hemos identificado {{ num_candidatos }} candidatos calificados para la vacante 
    <strong>{{ vacante.title }}</strong>.</p>
    
    <p>Puede revisar los perfiles detallados a través del siguiente enlace:</p>
    
    <p><a href="{{ dashboard_url }}">Ver candidatos</a></p>
    
    <p>Resumen de candidatos:</p>
    <ul>
    {% for candidato in candidatos %}
        <li><strong>{{ candidato.nombre }}</strong> - {{ candidato.current_position }} en {{ candidato.current_company }} 
        ({{ candidato.years_experience }} años de experiencia)</li>
    {% endfor %}
    </ul>
    
    <p>Por favor, revise los perfiles y háganos saber cuáles le interesaría entrevistar.</p>
    
    <p>Saludos cordiales,<br>
    El equipo de {{ business_unit.name }}</p>
    """
}

CANDIDATOS_BLIND_TEMPLATE = {
    'title': "Perfiles anónimos para {{ vacante.title }}",
    'content': """
    <p>Estimado/a {{ recipient.nombre }},</p>
    
    <p>Hemos preparado {{ num_candidatos }} perfiles anónimos para la vacante 
    <strong>{{ vacante.title }}</strong>.</p>
    
    <p>Estos perfiles muestran las habilidades, experiencia y logros de cada candidato, 
    manteniendo su información personal y empleador actual confidenciales.</p>
    
    <p>Puede revisar los perfiles a través del siguiente enlace:</p>
    
    <p><a href="{{ blind_profiles_url }}">Ver perfiles anónimos</a></p>
    
    <p>Si alguno de estos perfiles le interesa, podemos proporcionarle información más detallada 
    y coordinar entrevistas.</p>
    
    <p>Saludos cordiales,<br>
    El equipo de {{ business_unit.name }}</p>
    """
}

# Plantillas para consultor asignado
ESTATUS_DIARIO_TEMPLATE = {
    'title': "Estatus diario: Proceso {{ vacante.title }}",
    'content': """
    <p>Estimado/a {{ recipient.nombre }},</p>
    
    <p>A continuación, el estatus actual del proceso para la vacante <strong>{{ vacante.title }}</strong>:</p>
    
    <h3>Resumen general:</h3>
    <ul>
        <li><strong>Total de candidatos contactados:</strong> {{ stats.contactados }}</li>
        <li><strong>CV revisados:</strong> {{ stats.cv_revisados }}</li>
        <li><strong>Entrevistas iniciales:</strong> {{ stats.entrevistas_iniciales }}</li>
        <li><strong>Entrevistas con cliente:</strong> {{ stats.entrevistas_cliente }}</li>
        <li><strong>Candidatos en proceso final:</strong> {{ stats.proceso_final }}</li>
    </ul>
    
    <h3>Actividades recientes:</h3>
    <ul>
    {% for actividad in actividades_recientes %}
        <li><strong>{{ actividad.fecha|date:"d/m/Y" }}:</strong> {{ actividad.descripcion }}</li>
    {% endfor %}
    </ul>
    
    <h3>Próximos pasos:</h3>
    <ul>
    {% for paso in proximos_pasos %}
        <li><strong>{{ paso.fecha|date:"d/m/Y" }}:</strong> {{ paso.descripcion }}</li>
    {% endfor %}
    </ul>
    
    <p>Puede ver el informe completo y en tiempo real en su <a href="{{ dashboard_url }}">dashboard</a>.</p>
    
    <p>Saludos cordiales,<br>
    El equipo de {{ business_unit.name }}</p>
    """
}

# Plantillas para pagos y facturación
RECORDATORIO_PAGO_TEMPLATE = {
    'title': "Recordatorio de pago: {{ factura.numero }} - {{ vacante.title }}",
    'content': """
    <p>Estimado/a {{ recipient.nombre }},</p>
    
    <p>Le recordamos que el pago de la factura <strong>{{ factura.numero }}</strong> 
    por los servicios de reclutamiento para la vacante <strong>{{ vacante.title }}</strong> 
    vence el {{ factura.fecha_vencimiento|date:"d/m/Y" }}.</p>
    
    <p>Detalles de la factura:</p>
    <ul>
        <li><strong>Número de factura:</strong> {{ factura.numero }}</li>
        <li><strong>Fecha de emisión:</strong> {{ factura.fecha_emision|date:"d/m/Y" }}</li>
        <li><strong>Monto total:</strong> {{ factura.monto_total }}</li>
        <li><strong>Concepto:</strong> {{ factura.concepto }}</li>
    </ul>
    
    <p>Puede realizar el pago mediante transferencia bancaria a las siguientes coordenadas:</p>
    <ul>
        <li><strong>Banco:</strong> {{ datos_bancarios.banco }}</li>
        <li><strong>Titular:</strong> {{ datos_bancarios.titular }}</li>
        <li><strong>Cuenta:</strong> {{ datos_bancarios.cuenta }}</li>
        <li><strong>CLABE:</strong> {{ datos_bancarios.clabe }}</li>
    </ul>
    
    <p>O bien, puede confirmar el pago respondiendo a este mensaje a través de WhatsApp:</p>
    
    <p><a href="https://wa.me/{{ business_unit.whatsapp_number }}?text=Confirmo%20pago%20de%20factura%20{{ factura.numero }}%20Código:%20{{ verification_code }}">Confirmar pago por WhatsApp</a></p>
    
    <p>Saludos cordiales,<br>
    El equipo de {{ business_unit.name }}</p>
    """
}

# Diccionario de plantillas
TEMPLATES = {
    # Responsable de proceso
    'proceso_creado': PROCESO_CREADO_TEMPLATE,
    'feedback_requerido': FEEDBACK_REQUERIDO_TEMPLATE,
    'confirmacion_entrevista': CONFIRMACION_ENTREVISTA_TEMPLATE,
    'felicitacion_contratacion': FELICITACION_CONTRATACION_TEMPLATE,
    
    # Contacto en cliente
    'firma_contrato': FIRMA_CONTRATO_TEMPLATE,
    'emision_propuesta': EMISION_PROPUESTA_TEMPLATE,
    'candidatos_disponibles': CANDIDATOS_DISPONIBLES_TEMPLATE,
    'candidatos_blind': CANDIDATOS_BLIND_TEMPLATE,
    
    # Consultor asignado
    'estatus_diario': ESTATUS_DIARIO_TEMPLATE,
    
    # Pagos y facturación
    'recordatorio_pago': RECORDATORIO_PAGO_TEMPLATE,
}

def get_notification_template(
    template_name: str,
    recipient: Person,
    business_unit: BusinessUnit,
    context: Dict[str, Any] = None
) -> Dict[str, str]:
    """
    Obtiene una plantilla de notificación y la renderiza con el contexto proporcionado.
    
    Args:
        template_name: Nombre de la plantilla (coincide con el tipo de notificación)
        recipient: Destinatario de la notificación
        business_unit: Unidad de negocio relacionada
        context: Contexto adicional para renderizar la plantilla
    
    Returns:
        Diccionario con 'title' y 'content' renderizados
    """
    # Si no hay contexto, crear uno vacío
    context = context or {}
    
    # Asegurarse de que recipient y business_unit estén en el contexto
    if 'recipient' not in context:
        context['recipient'] = recipient
    if 'business_unit' not in context:
        context['business_unit'] = business_unit
        
    # Obtener la plantilla
    template_data = TEMPLATES.get(template_name)
    
    if not template_data:
        logger.warning(f"No se encontró plantilla para {template_name}, usando plantilla genérica")
        # Plantilla genérica si no se encuentra la solicitada
        title = f"Notificación de {business_unit.name}"
        content = f"<p>Estimado/a {recipient.nombre},</p><p>Esta es una notificación importante del sistema.</p>"
        return {'title': title, 'content': content}
    
    # Renderizar la plantilla con el contexto
    try:
        title_template = Template(template_data['title'])
        content_template = Template(template_data['content'])
        
        django_context = Context(context)
        
        title = title_template.render(django_context)
        content = content_template.render(django_context)
        
        return {
            'title': title,
            'content': content,
            'text_content': strip_tags(content)  # Versión texto plano para SMS
        }
    except Exception as e:
        logger.error(f"Error renderizando plantilla {template_name}: {e}")
        # Plantilla de respaldo en caso de error
        title = f"Notificación de {business_unit.name}"
        content = f"<p>Estimado/a {recipient.nombre},</p><p>Esta es una notificación importante del sistema.</p>"
        return {'title': title, 'content': content}
