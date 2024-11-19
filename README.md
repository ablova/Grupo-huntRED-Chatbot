# /home/amigro/app/integrations/instagram.py

import logging
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from app.chatbot import ChatBotHandler

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def instagram_webhook(request):
    """
    Webhook para manejar mensajes entrantes desde Instagram.
    """
    try:
        data = request.body.decode('utf-8')
        # Aquí puedes procesar el mensaje de Instagram
        logger.info(f"Mensaje recibido desde Instagram: {data}")
        
        # Ejemplo de interacción con el chatbot
        chatbot_handler = ChatBotHandler()
        response, options = chatbot_handler.process_message('instagram', data['sender']['id'], data['message']['text'])

        return JsonResponse({'status': 'success', 'response': response}, status=200)
    except Exception as e:
        logger.error(f"Error en el webhook de Instagram: {e}")
        return JsonResponse({'status': 'error', 'message': 'Error interno del servidor'}, status=500)

async def send_instagram_message(recipient_id, message, access_token):
    """
    Envía un mensaje a un usuario de Instagram.
    """
    url = f"https://graph.facebook.com/v11.0/me/messages"
    params = {"access_token": access_token}
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": message},
    }
    response = requests.post(url, json=data, params=params)
    if response.status_code != 200:
        logger.error(f"Error enviando mensaje a Instagram: {response.text}")
    else:
        logger.info(f"Mensaje enviado correctamente a Instagram: {message}")

_____

# /home/amigro/app/integrations/messenger.py

import logging
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from app.chatbot import ChatBotHandler

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def messenger_webhook(request):
    """
    Webhook para manejar mensajes entrantes desde Messenger.
    """
    try:
        data = request.body.decode('utf-8')
        # Aquí puedes procesar el mensaje de Messenger
        logger.info(f"Mensaje recibido desde Messenger: {data}")
        
        # Ejemplo de interacción con el chatbot
        chatbot_handler = ChatBotHandler()
        response, options = chatbot_handler.process_message('messenger', data['sender']['id'], data['message']['text'])

        return JsonResponse({'status': 'success', 'response': response}, status=200)
    except Exception as e:
        logger.error(f"Error en el webhook de Messenger: {e}")
        return JsonResponse({'status': 'error', 'message': 'Error interno del servidor'}, status=500)

async def send_messenger_message(recipient_id, message, access_token):
    """
    Envía un mensaje a un usuario de Messenger.
    """
    url = f"https://graph.facebook.com/v11.0/me/messages"
    params = {"access_token": access_token}
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": message},
    }
    response = requests.post(url, json=data, params=params)
    if response.status_code != 200:
        logger.error(f"Error enviando mensaje a Messenger: {response.text}")
    else:
        logger.info(f"Mensaje enviado correctamente a Messenger: {message}")

_____

# /home/amigro/app/integrations/services.py

import logging
from app.models import TelegramAPI, WhatsAppAPI, MessengerAPI, InstagramAPI

logger = logging.getLogger(__name__)

def send_message(platform, user_id, message):
    """
    Envía un mensaje de texto a través de la plataforma especificada.
    """
    try:
        if platform == 'telegram':
            telegram_api = TelegramAPI.objects.first()
            if telegram_api:
                send_telegram_message(user_id, message, telegram_api.api_key)
            else:
                logger.error("No se encontró configuración de API de Telegram")

        elif platform == 'whatsapp':
            whatsapp_api = WhatsAppAPI.objects.first()
            if whatsapp_api:
                send_whatsapp_message(user_id, message, whatsapp_api.api_token, whatsapp_api.phoneID, whatsapp_api.v_api)
            else:
                logger.error("No se encontró configuración de API de WhatsApp")

        elif platform == 'messenger':
            messenger_api = MessengerAPI.objects.first()
            if messenger_api:
                send_messenger_message(user_id, message, messenger_api.page_access_token)
            else:
                logger.error("No se encontró configuración de API de Messenger")

        elif platform == 'instagram':
            instagram_api = InstagramAPI.objects.first()
            if instagram_api:
                send_instagram_message(user_id, message, instagram_api.access_token)
            else:
                logger.error("No se encontró configuración de API de Instagram")

        else:
            logger.error(f"Plataforma desconocida: {platform}")

    except Exception as e:
        logger.error(f"Error enviando mensaje a través de {platform}: {e}", exc_info=True)


def send_options(platform, user_id, message, options):
    """
    Envía un mensaje con opciones/botones en la plataforma.
    """
    try:
        if platform == 'whatsapp':
            whatsapp_api = WhatsAppAPI.objects.first()
            if whatsapp_api:
                send_whatsapp_message(user_id, message, whatsapp_api.api_token, whatsapp_api.phoneID, whatsapp_api.v_api, options)
            else:
                logger.error("No se encontró configuración de API de WhatsApp")

        # Aquí puedes expandir para enviar botones en otras plataformas
        else:
            logger.error(f"Envío de opciones no soportado para la plataforma {platform}")
    except Exception as e:
        logger.error(f"Error enviando opciones en {platform}: {e}", exc_info=True)


def send_image(platform, user_id, image_url):
    """
    Envía una imagen a través de la plataforma especificada.
    """
    try:
        if platform == 'whatsapp':
            whatsapp_api = WhatsAppAPI.objects.first()
            if whatsapp_api:
                send_whatsapp_message(user_id, '', whatsapp_api.api_token, whatsapp_api.phoneID, whatsapp_api.v_api, image_url=image_url)
            else:
                logger.error("No se encontró configuración de API de WhatsApp")
        else:
            logger.error(f"Envío de imágenes no soportado para la plataforma {platform}")

    except Exception as e:
        logger.error(f"Error enviando imagen en {platform}: {e}", exc_info=True)


def send_menu(platform, user_id):
    """
    Envía el menú persistente en la plataforma.
    """
    menu_message = """
    1 - Bienvenida
    2 - Registro
    3 - Ver Oportunidades
    4 - Actualizar Perfil
    5 - Invitar Familiares o Amigos
    6 - Términos y Condiciones
    7 - Contacto
    8 - Solicitar Ayuda
    """
    
    try:
        if platform == 'whatsapp':
            whatsapp_api = WhatsAppAPI.objects.first()
            if whatsapp_api:
                send_whatsapp_message(user_id, menu_message, whatsapp_api.api_token, whatsapp_api.phoneID, whatsapp_api.v_api)
            else:
                logger.error("No se encontró configuración de API de WhatsApp")

        elif platform == 'telegram':
            telegram_api = TelegramAPI.objects.first()
            if telegram_api:
                send_telegram_message(user_id, menu_message, telegram_api.api_key)
            else:
                logger.error("No se encontró configuración de API de Telegram")

        elif platform == 'messenger':
            messenger_api = MessengerAPI.objects.first()
            if messenger_api:
                send_messenger_message(user_id, menu_message, messenger_api.page_access_token)
            else:
                logger.error("No se encontró configuración de API de Messenger")

        elif platform == 'instagram':
            instagram_api = InstagramAPI.objects.first()
            if instagram_api:
                send_instagram_message(user_id, menu_message, instagram_api.access_token)
            else:
                logger.error("No se encontró configuración de API de Instagram")

        else:
            logger.error(f"Plataforma desconocida: {platform}")

    except Exception as e:
        logger.error(f"Error enviando el menú a través de {platform}: {e}", exc_info=True)

______

# /home/amigro/app/integrations/telegram.py

import requests
import logging

logger = logging.getLogger(__name__)

def send_telegram_message(user_id, message, api_key):
    """
    Envía un mensaje de Telegram al usuario especificado.
    """
    url = f"https://api.telegram.org/bot{api_key}/sendMessage"
    payload = {'chat_id': user_id, 'text': message}

    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            logger.error(f"Error al enviar mensaje de Telegram: {response.text}")
    except Exception as e:
        logger.error(f"Error enviando mensaje de Telegram: {e}", exc_info=True)

def telegram_webhook(request):
    """
    Webhook para recibir mensajes desde Telegram.
    """
    if request.method == 'POST':
        data = request.json()
        message = data['message']['text']
        user_id = data['message']['from']['id']
        # Lógica para procesar el mensaje de Telegram
        return JsonResponse({'status': 'received'})

    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)


_____


# /home/amigro/app/integrations/whatsapp.py

import logging
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from app.chatbot import ChatBotHandler

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def whatsapp_webhook(request):
    """
    Webhook para manejar mensajes entrantes desde WhatsApp.
    """
    try:
        data = request.body.decode('utf-8')
        # Aquí puedes procesar el mensaje de WhatsApp
        logger.info(f"Mensaje recibido desde WhatsApp: {data}")
        
        # Ejemplo de interacción con el chatbot
        chatbot_handler = ChatBotHandler()
        response, options = chatbot_handler.process_message('whatsapp', data['From'], data['Body'])

        return JsonResponse({'status': 'success', 'response': response}, status=200)
    except Exception as e:
        logger.error(f"Error en el webhook de WhatsApp: {e}")
        return JsonResponse({'status': 'error', 'message': 'Error interno del servidor'}, status=500)

async def send_whatsapp_message(recipient, message, api_token, phone_id, version_api):
    """
    Envía un mensaje a un usuario de WhatsApp utilizando la API.
    """
    url = f"https://graph.facebook.com/{version_api}/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "text": {
            "body": message
        }
    }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code != 200:
        logger.error(f"Error enviando mensaje a WhatsApp: {response.text}")
    else:
        logger.info(f"Mensaje enviado correctamente a WhatsApp: {message}")



async def invite_known_person(referrer, name, apellido, phone_number):
    """
    Función para invitar a un conocido por WhatsApp y crear un pre-registro del invitado.
    
    :param referrer: Usuario que realizó la invitación.
    :param name: Nombre del invitado.
    :param apellido: Apellido del invitado.
    :param phone_number: Número de contacto del invitado.
    """
    # Crear pre-registro del invitado
    invitado, created = await Person.objects.aget_or_create(phone=phone_number, defaults={
        'name': name,
        'apellido': apellido
    })
    
    # Crear el registro de la invitación
    await Invitacion.objects.acreate(referrer=referrer, invitado=invitado)

    # Enviar mensaje de invitación por WhatsApp
    if created:
        mensaje = f"Hola {name}, has sido invitado por {referrer.name} a unirte a Amigro.org. ¡Únete a nuestra comunidad!"
        await send_whatsapp_message(phone_number, mensaje)

    return invitado


_____

<!-- /home/amigro/app/templates/admin/base_site.html -->
{% block branding %}
    <div id="site-name">
        <img src="https://amigro.org/wp-content/uploads/2019/11/logo2-1.png" alt="Amigro" style="max-height: 50px;">
        <h1>{{ site_title|default:_('Django site admin') }}</h1>
    </div>
{% endblock %}

_____

<!--#/home/amigro/app/templates/admin/change_form_with_edit_button.html -->
{% extends "admin/change_form.html" %}

{% block submit_buttons_bottom %}
    {{ block.super }}
    <a href="{{ edit_flow_url }}" class="button">Editar Flujo</a>
{% endblock %}
_____

<!-- /home/amigro/app/templates/admin/chatbot_flow.html -->
{% extends "admin/base_site.html" %}

{% block extrahead %}
{{ block.super }}
<!-- Inclusión de GoJS desde CDN -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/gojs/2.1.53/go.js"></script>
<!-- Inclusión de Font Awesome para iconos -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">
<style>
    /* Estilo para el contenedor del diagrama */
    #myDiagramDiv {
        width: 100%;
        height: 600px;
        background-color: #DAE4E4;
        border: 1px solid #ccc;
    }
    .controls {
        margin-top: 20px;
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
    }
    .controls button {
        padding: 10px;
        border: none;
        background-color: #007bff;
        color: white;
        cursor: pointer;
        border-radius: 4px;
    }
    .controls button:hover {
        background-color: #0056b3;
    }
    #nodeProperties {
        width: 300px;
        padding: 10px;
        border: 1px solid #ccc;
        margin-top: 20px;
    }
    #simulator {
        margin-top: 40px;
    }
    #flowSelectorContainer {
        margin-bottom: 20px;
    }
    #flowSelector {
        padding: 5px;
        border-radius: 4px;
    }
</style>
{% endblock %}

{% block content %}
<h1>Editor de Flujo del Chatbot</h1>

<!-- Selector de Flujos (si manejas múltiples flujos) -->
<div id="flowSelectorContainer">
    <label for="flowSelector"><strong>Seleccionar Flujo:</strong></label>
    <select id="flowSelector" onchange="loadSelectedFlow()">
        {% for fl in flows %}
            <option value="{{ fl.id }}" {% if fl.id == flow.id %}selected{% endif %}>{{ fl.name }}</option>
        {% endfor %}
    </select>
</div>

<!-- Contenedor del diagrama -->
<div id="myDiagramDiv"></div>

<!-- Controles para agregar nodos, fases y guardar el flujo -->
<div class="controls">
    <button onclick="addNode('text')"><i class="fas fa-comment-alt"></i> Añadir Pregunta/Texto</button>
    <button onclick="addNode('decision')"><i class="fas fa-question-circle"></i> Añadir Decisión</button>
    <button onclick="addNode('input')"><i class="fas fa-keyboard"></i> Añadir Input</button>
    <button onclick="addNode('menu')"><i class="fas fa-list"></i> Añadir Menú</button>
    <button onclick="addNode('image')"><i class="fas fa-image"></i> Añadir Imagen</button>
    <button onclick="addNode('link')"><i class="fas fa-link"></i> Añadir Link</button>
    <button onclick="saveFlow()"><i class="fas fa-save"></i> Guardar Flujo</button>
    <button onclick="exportFlow()"><i class="fas fa-file-export"></i> Exportar Flujo</button>
    <button onclick="importFlow()"><i class="fas fa-file-import"></i> Importar Flujo</button>
</div>

<!-- Panel para editar las propiedades del nodo seleccionado -->
<div id="nodeProperties">
    <h3>Propiedades del Nodo</h3>
    <label for="nodeText">Texto del nodo:</label>
    <input type="text" id="nodeText" placeholder="Texto del nodo"><br><br>
    <label for="nodeType">Tipo de nodo:</label>
    <select id="nodeType" onchange="updatePropertiesPanel()">
        <option value="text">Pregunta/Texto</option>
        <option value="decision">Decisión</option>
        <option value="input">Input</option>
        <option value="menu">Menú</option>
        <option value="image">Imagen</option>
        <option value="link">Link</option>
        <option value="registration">Registro</option>
        <option value="document_verification">Verificación de Documentos</option>
        <option value="skill_assessment">Evaluación de Habilidades</option>
        <option value="job_recommendation">Recomendación de Trabajo</option>
        <option value="legal_info">Información Legal</option>
    </select><br><br>

    <!-- Opciones para nodos de decisión -->
    <div id="decisionOptions" style="display: none;">
        <label for="option1">Opción 1:</label>
        <input type="text" id="option1" placeholder="Opción 1"><br>
        <label for="option2">Opción 2:</label>
        <input type="text" id="option2" placeholder="Opción 2"><br>
        <label for="option3">Opción 3:</label>
        <input type="text" id="option3" placeholder="Opción 3"><br>
    </div>

    <!-- Placeholder para input -->
    <div id="inputProperties" style="display: none;">
        <label for="inputPlaceholder">Placeholder del input:</label>
        <input type="text" id="inputPlaceholder" placeholder="Placeholder del input"><br>
    </div>

    <!-- URL de imagen -->
    <div id="imageProperties" style="display: none;">
        <label for="imgSrc">URL de la imagen:</label>
        <input type="text" id="imgSrc" placeholder="URL de la imagen"><br>
    </div>

    <!-- URL del enlace -->
    <div id="linkProperties" style="display: none;">
        <label for="linkUrl">URL del link:</label>
        <input type="text" id="linkUrl" placeholder="URL del link"><br>
    </div>

    <button onclick="updateSelectedNode()"><i class="fas fa-edit"></i> Actualizar Nodo</button>
</div>

<!-- Simulador -->
<div id="simulator">
    <h3>Simulador</h3>
    <div id="simulatorContent"></div>
    <button onclick="simulateFlow()"><i class="fas fa-play"></i> Probar Chatbot</button>
</div>

<script>
    var myDiagram;
    var selectedNode = null;
    var flowmodel_id = "{{ flow.id }}";  // Obtener el ID del flujo actual

    function init() {
        var $ = go.GraphObject.make;

        myDiagram =
            $(go.Diagram, "myDiagramDiv", {
                "undoManager.isEnabled": true,
                initialContentAlignment: go.Spot.Center,
                "linkingTool.direction": go.Link.AvoidsNodes,
                "draggingTool.isGridSnapEnabled": true,
                "grid.visible": true,
                "grid.gridCellSize": new go.Size(10, 10),
                "animationManager.isEnabled": false,
                "toolManager.hoverDelay": 100,
                allowDrop: true,
                "linkingTool.isUnconnectedLinkValid": true,
                "linkingTool.portGravity": 20,
                "relinkingTool.isUnconnectedLinkValid": true,
                "relinkingTool.portGravity": 20,
                "relinkingTool.fromHandleArchetype":
                    $(go.Shape, "Diamond", { segmentIndex: 0, cursor: "pointer", desiredSize: new go.Size(8, 8), fill: "tomato", stroke: "darkred" }),
                "relinkingTool.toHandleArchetype":
                    $(go.Shape, "Diamond", { segmentIndex: -1, cursor: "pointer", desiredSize: new go.Size(8, 8), fill: "darkred", stroke: "tomato" }),
                "linkReshapingTool.handleArchetype":
                    $(go.Shape, "Diamond", { desiredSize: new go.Size(7, 7), fill: "lightblue", stroke: "deepskyblue" }),
                "InitialLayoutCompleted": onLayoutCompleted,
                "ExternalObjectsDropped": onObjectsDropped,
                model: $(go.GraphLinksModel, {
                    linkKeyProperty: "key",
                    nodeKeyProperty: "key"
                })
            });

        // Definir las plantillas de nodos
        myDiagram.nodeTemplateMap.add("text", createNodeTemplate("RoundedRectangle", "lightblue"));
        myDiagram.nodeTemplateMap.add("decision", createDecisionTemplate());
        myDiagram.nodeTemplateMap.add("input", createNodeTemplate("Ellipse", "lightyellow"));
        myDiagram.nodeTemplateMap.add("menu", createMenuTemplate());
        myDiagram.nodeTemplateMap.add("image", createImageTemplate());
        myDiagram.nodeTemplateMap.add("link", createLinkTemplate());
        myDiagram.nodeTemplateMap.add("registration", createNodeTemplate("RoundedRectangle", "lightgreen"));
        myDiagram.nodeTemplateMap.add("document_verification", createNodeTemplate("RoundedRectangle", "lightcoral"));
        myDiagram.nodeTemplateMap.add("skill_assessment", createNodeTemplate("RoundedRectangle", "lightyellow"));
        myDiagram.nodeTemplateMap.add("job_recommendation", createNodeTemplate("RoundedRectangle", "lightblue"));
        myDiagram.nodeTemplateMap.add("legal_info", createNodeTemplate("RoundedRectangle", "lightpink"));

        // Definir la plantilla de enlaces (conectores)
        myDiagram.linkTemplate =
            $(go.Link,
                { routing: go.Link.AvoidsNodes, curve: go.Link.JumpOver, corner: 5 },
                $(go.Shape, { strokeWidth: 2, stroke: "#555" }),
                $(go.Shape, { toArrow: "Standard", stroke: null, fill: "#555" }),
                $(go.Panel, "Auto",
                    $(go.Shape, "Rectangle", { fill: "#F8F8F8", stroke: "#E0E0E0" }),
                    $(go.TextBlock, { margin: 3, editable: true },
                        new go.Binding("text").makeTwoWay())
                )
            );

        // Evento para mostrar las propiedades del nodo seleccionado
        myDiagram.addDiagramListener("ChangedSelection", showNodeProperties);
    }

    // Crear plantillas de nodos
    function createNodeTemplate(shapeType, color) {
        return go.GraphObject.make(go.Node, "Auto",
            go.GraphObject.make(go.Shape, shapeType, { fill: color, strokeWidth: 2 }),
            go.GraphObject.make(go.TextBlock, { margin: 8, editable: true }, new go.Binding("text").makeTwoWay()),
            { fromLinkable: true, toLinkable: true }  // Permitir que el nodo sea conectado
        );
    }

    // Plantilla para nodos de decisión
    function createDecisionTemplate() {
        return go.GraphObject.make(go.Node, "Auto",
            go.GraphObject.make(go.Shape, "Diamond", { fill: "lightgreen", strokeWidth: 2 }),
            go.GraphObject.make(go.Panel, "Vertical",
                go.GraphObject.make(go.TextBlock, { margin: 8, editable: true }, new go.Binding("text").makeTwoWay()),
                go.GraphObject.make(go.Panel, "Vertical",
                    { itemTemplate: go.GraphObject.make(go.TextBlock, new go.Binding("text")) },
                    new go.Binding("itemArray", "options")
                )
            ),
            { fromLinkable: true, toLinkable: true }  // Permitir conexiones hacia/desde el nodo
        );
    }

    // Plantilla para nodos de menú
    function createMenuTemplate() {
        return go.GraphObject.make(go.Node, "Auto",
            go.GraphObject.make(go.Shape, "RoundedRectangle", { fill: "lightcoral", strokeWidth: 2 }),
            go.GraphObject.make(go.Panel, "Vertical",
                go.GraphObject.make(go.TextBlock, { margin: 8, editable: true }, new go.Binding("text").makeTwoWay()),
                go.GraphObject.make(go.Panel, "Vertical",
                    { itemTemplate: go.GraphObject.make(go.TextBlock, new go.Binding("text")) },
                    new go.Binding("itemArray", "options")
                )
            ),
            { fromLinkable: true, toLinkable: true }  // Permitir conexiones
        );
    }

    // Plantilla para nodos de imagen
    function createImageTemplate() {
        return go.GraphObject.make(go.Node, "Auto",
            go.GraphObject.make(go.Shape, "Rectangle", { fill: "lightpink", strokeWidth: 2 }),
            go.GraphObject.make(go.Panel, "Vertical",
                go.GraphObject.make(go.TextBlock, { margin: 8, editable: true }, new go.Binding("text").makeTwoWay()),
                go.GraphObject.make(go.Picture, { margin: 4, width: 80, height: 80 }, new go.Binding("source", "imgSrc"))
            ),
            { fromLinkable: true, toLinkable: true }  // Conectores habilitados
        );
    }

    // Plantilla para nodos de enlace
    function createLinkTemplate() {
        return go.GraphObject.make(go.Node, "Auto",
            go.GraphObject.make(go.Shape, "Rectangle", { fill: "lightblue", strokeWidth: 2 }),
            go.GraphObject.make(go.Panel, "Vertical",
                go.GraphObject.make(go.TextBlock, { margin: 8, editable: true }, new go.Binding("text").makeTwoWay()),
                go.GraphObject.make(go.TextBlock, { margin: 4, font: "italic 10px sans-serif" }, new go.Binding("text", "linkUrl").makeTwoWay())
            ),
            { fromLinkable: true, toLinkable: true }  // Conexiones habilitadas
        );
    }

    // Añadir nodo al diagrama
    function addNode(type) {
        var nodeData = { 
            key: 'node' + Date.now(),  // Generar una clave única
            text: "Nuevo " + capitalizeFirstLetter(type), 
            type: type, 
            fill: getNodeColor(type),
            isNew: true  // Marcar como nuevo
        };
        if (type === "decision") {
            nodeData.options = ["Opción 1", "Opción 2", "Opción 3"];
        }
        if (type === "menu") {
            nodeData.options = ["Registro", "Vacantes", "Agenda", "Información"];
        }
        if (type === "image") {
            nodeData.imgSrc = "URL de la imagen";
        }
        if (type === "link") {
            nodeData.linkUrl = "URL del link";
        }
        myDiagram.model.addNodeData(nodeData);
    }

    // Capitalizar la primera letra de una cadena
    function capitalizeFirstLetter(string) {
        return string.charAt(0).toUpperCase() + string.slice(1);
    }

    // Asignar colores diferentes para cada tipo de nodo
    function getNodeColor(type) {
        switch (type) {
            case "text": return "lightblue";
            case "decision": return "lightgreen";
            case "menu": return "lightcoral";
            case "input": return "lightyellow";
            case "image": return "lightpink";
            case "link": return "lightblue";
            case "registration": return "lightgreen";
            case "document_verification": return "lightcoral";
            case "skill_assessment": return "lightyellow";
            case "job_recommendation": return "lightblue";
            case "legal_info": return "lightpink";
            default: return "white";
        }
    }

    // Mostrar las propiedades del nodo seleccionado
    function showNodeProperties(e) {
        var node = myDiagram.selection.first();
        if (node instanceof go.Node) {
            selectedNode = node;
            document.getElementById("nodeText").value = node.data.text;
            document.getElementById("nodeType").value = node.data.type;
            updatePropertiesPanel();
            if (node.data.type === "decision" && node.data.options) {
                document.getElementById("option1").value = node.data.options[0] || "";
                document.getElementById("option2").value = node.data.options[1] || "";
                document.getElementById("option3").value = node.data.options[2] || "";
            }
            if (node.data.type === "input" && node.data.placeholder) {
                document.getElementById("inputPlaceholder").value = node.data.placeholder;
            }
            if (node.data.type === "image" && node.data.imgSrc) {
                document.getElementById("imgSrc").value = node.data.imgSrc;
            }
            if (node.data.type === "link" && node.data.linkUrl) {
                document.getElementById("linkUrl").value = node.data.linkUrl;
            }
        }
    }

    // Actualizar panel de propiedades basado en el tipo de nodo
    function updatePropertiesPanel() {
        var type = document.getElementById("nodeType").value;
        document.getElementById("decisionOptions").style.display = type === "decision" ? "block" : "none";
        document.getElementById("inputProperties").style.display = type === "input" ? "block" : "none";
        document.getElementById("imageProperties").style.display = type === "image" ? "block" : "none";
        document.getElementById("linkProperties").style.display = type === "link" ? "block" : "none";
    }

    // Actualizar el nodo seleccionado con la nueva información
    function updateSelectedNode() {
        if (selectedNode) {
            var newType = document.getElementById("nodeType").value;
            myDiagram.model.setDataProperty(selectedNode.data, "text", document.getElementById("nodeText").value);
            myDiagram.model.setDataProperty(selectedNode.data, "type", newType);
            myDiagram.model.setDataProperty(selectedNode.data, "fill", getNodeColor(newType));

            if (newType === "decision") {
                myDiagram.model.setDataProperty(selectedNode.data, "options", [
                    document.getElementById("option1").value,
                    document.getElementById("option2").value,
                    document.getElementById("option3").value
                ]);
            } else if (newType === "input") {
                myDiagram.model.setDataProperty(selectedNode.data, "placeholder", document.getElementById("inputPlaceholder").value);
            } else if (newType === "image") {
                myDiagram.model.setDataProperty(selectedNode.data, "imgSrc", document.getElementById("imgSrc").value);
            } else if (newType === "link") {
                myDiagram.model.setDataProperty(selectedNode.data, "linkUrl", document.getElementById("linkUrl").value);
            } else {
                // Limpiar propiedades si el nodo es diferente
                delete selectedNode.data.options;
                delete selectedNode.data.placeholder;
                delete selectedNode.data.imgSrc;
                delete selectedNode.data.linkUrl;
                myDiagram.model.setDataProperty(selectedNode.data, "options", null);
                myDiagram.model.setDataProperty(selectedNode.data, "placeholder", null);
                myDiagram.model.setDataProperty(selectedNode.data, "imgSrc", null);
                myDiagram.model.setDataProperty(selectedNode.data, "linkUrl", null);
            }
            myDiagram.model.updateTargetBindings(selectedNode.data);
        }
    }

    // Validar el flujo
    function validateFlow(nodes, links) {
        const errors = [];

        // Verificar que haya exactamente un nodo de inicio
        const startNodes = nodes.filter(node => node.type === 'text' && node.text.toLowerCase() === 'inicio');
        if (startNodes.length !== 1) {
            errors.push('Debe haber exactamente un nodo de inicio (Pregunta/Texto con texto "Inicio").');
        }

        // Verificar que todos los nodos estén conectados (excepto el nodo de inicio)
        const connectedNodes = new Set();
        links.forEach(link => {
            connectedNodes.add(link.from);
            connectedNodes.add(link.to);
        });
        nodes.forEach(node => {
            if (node.type !== 'text' || node.text.toLowerCase() !== 'inicio') {  // El nodo de inicio ya está conectado
                if (!connectedNodes.has(node.key)) {
                    errors.push(`El nodo "${node.text}" no está conectado al flujo.`);
                }
            }
        });

        // Verificar que los nodos de decisión tengan al menos dos opciones
        nodes.forEach(node => {
            if (node.type === 'decision') {
                if (!node.options || node.options.length < 2) {
                    errors.push(`El nodo de decisión "${node.text}" debe tener al menos dos opciones.`);
                }
            }
        });

        // Evitar ciclos simples (auto-conexiones)
        links.forEach(link => {
            if (link.from === link.to) {
                errors.push(`El nodo "${getNodeText(link.from)}" tiene una auto-conexión.`);
            }
        });

        return errors;
    }

    function getNodeText(key) {
        var node = myDiagram.findNodeForKey(key);
        return node ? node.data.text : '';
    }

    // Guardar el flujo
    function saveFlow() {
        const nodes = myDiagram.model.nodeDataArray;
        const links = myDiagram.model.linkDataArray;
        const validationErrors = validateFlow(nodes, links);
        if (validationErrors.length > 0) {
            alert(`Errores de validación:\n${validationErrors.join('\n')}`);
            return;
        }
        fetch("{% url 'admin:save_flow' %}", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': '{{ csrf_token }}'
            },
            body: JSON.stringify({ 
                flowmodel_id: flowmodel_id,
                nodes, 
                links
            })
        }).then(response => response.json())
          .then(data => {
              if (data.status === 'success') {
                  alert('Flujo guardado exitosamente.');
              } else {
                  alert('Error al guardar el flujo: ' + data.message);
              }
          })
          .catch(error => console.error('Error al guardar el flujo:', error));
    }

    // Simular el flujo del chatbot
    function simulateFlow() {
        const nodes = myDiagram.model.nodeDataArray;
        const links = myDiagram.model.linkDataArray;
        const simulatorContent = document.getElementById('simulatorContent');
        simulatorContent.innerHTML = '';

        // Encontrar el nodo de inicio
        let currentNode = nodes.find(node => node.type === 'text' && node.text.toLowerCase() === 'inicio');
        if (!currentNode) {
            alert('No se encontró un nodo de inicio (Pregunta/Texto con texto "Inicio").');
            return;
        }

        while (currentNode) {
            simulatorContent.innerHTML += `<p><strong>Bot:</strong> ${currentNode.text}</p>`;
            
            if (currentNode.type === 'decision') {
                // Solicitar al usuario una opción
                let userChoice = prompt(`Decisión: ${currentNode.text}\nOpciones: ${currentNode.options.join(', ')}`);
                if (!userChoice) {
                    alert('Simulación cancelada.');
                    return;
                }
                // Encontrar el enlace que corresponde a la elección
                let nextLink = links.find(link => link.from === currentNode.key && link.text.trim().toLowerCase() === userChoice.trim().toLowerCase());
                if (nextLink) {
                    currentNode = nodes.find(node => node.key === nextLink.to);
                } else {
                    alert(`Opción inválida: "${userChoice}"`);
                    return;
                }
            } else if (currentNode.type === 'link') {
                simulatorContent.innerHTML += `<p><strong>Bot:</strong> ${currentNode.linkUrl}</p>`;
                let nextLink = links.find(link => link.from === currentNode.key);
                currentNode = nextLink ? nodes.find(node => node.key === nextLink.to) : null;
            } else {
                // Obtener el siguiente enlace
                let nextLink = links.find(link => link.from === currentNode.key);
                currentNode = nextLink ? nodes.find(node => node.key === nextLink.to) : null;
            }
        }

        simulatorContent.innerHTML += `<p><strong>Bot:</strong> Gracias por usar el chatbot.</p>`;
    }

    // Exportar el flujo a JSON
    function exportFlow() {
        const flowData = myDiagram.model.toJson();
        const blob = new Blob([flowData], {type: "application/json"});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'chatbot_flow.json';
        a.click();
    }

    // Importar el flujo desde un archivo JSON
    function importFlow() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'application/json';
        input.onchange = e => {
            const file = e.target.files[0];
            const reader = new FileReader();
            reader.onload = event => {
                try {
                    const importedModel = go.Model.fromJson(event.target.result);
                    myDiagram.model = importedModel;
                    alert('Flujo importado correctamente.');
                } catch (error) {
                    alert('Error al importar el flujo: ' + error.message);
                    console.error('Error al importar el flujo:', error);
                }
            };
            reader.readAsText(file);
        };
        input.click();
    }

    // Función para crear nodos arrastrables (Opcional si decides incluir una paleta)
    function makeDraggableNode(text, nodeType) {
        var $ = go.GraphObject.make;
        var node = $(go.Node, "Auto",
            { locationSpot: go.Spot.Center },
            $(go.Shape, "RoundedRectangle", { fill: getNodeColor(nodeType) }),
            $(go.TextBlock, text, { margin: 8 })
        );
        return node;
    }

    // Inicializar paleta de nodos (Opcional)
    function initPalette() {
        var $ = go.GraphObject.make;
        var palette = $(go.Palette, "palette", {
            nodeTemplateMap: myDiagram.nodeTemplateMap,
            model: new go.GraphLinksModel([
                { key: "node1", text: "Pregunta/Texto", type: "text" },
                { key: "node2", text: "Decisión", type: "decision" },
                { key: "node3", text: "Input", type: "input" },
                { key: "node4", text: "Menú", type: "menu" },
                { key: "node5", text: "Imagen", type: "image" },
                { key: "node6", text: "Link", type: "link" },
                { key: "node7", text: "Registro", type: "registration" },
                { key: "node8", text: "Verificación de Documentos", type: "document_verification" },
                { key: "node9", text: "Evaluación de Habilidades", type: "skill_assessment" },
                { key: "node10", text: "Recomendación de Trabajo", type: "job_recommendation" },
                { key: "node11", text: "Información Legal", type: "legal_info" }
            ])
        });
    }

    // Función para editar el texto del nodo (Opcional)
    function editNodeText(e, obj) {
        var node = obj.part;
        if (node) {
            var tb = node.findObject("TextBlock");
            if (tb) myDiagram.commandHandler.editTextBlock(tb);
        }
    }

    // Evento llamado cuando se completa el layout inicial
    function onLayoutCompleted(e) {
        var newNodes = e.diagram.findNodesByExample({ isNew: true });
        newNodes.each(function(node) {
            var tb = node.findObject("TextBlock");
            if (tb) e.diagram.commandHandler.editTextBlock(tb);
            myDiagram.model.setDataProperty(node.data, "isNew", false);
        });
    }

    // Evento llamado cuando se sueltan objetos externos en el diagrama
    function onObjectsDropped(e) {
        var newNodes = e.subject;
        newNodes.each(function(node) {
            if (node instanceof go.Node) {
                var tb = node.findObject("TextBlock");
                if (tb) e.diagram.commandHandler.editTextBlock(tb);
                myDiagram.model.setDataProperty(node.data, "isNew", false);
            }
        });
    }

    // Inicializar el diagrama cuando la página esté cargada
    window.onload = function() {
        init();
        initPalette();
        loadFlow();
    };

    // Cargar el flujo desde la base de datos
    function loadFlow() {
        fetch("{% url 'admin:load_flow' %}?flowmodel_id=" + flowmodel_id)
            .then(response => response.json())
            .then(data => {
                if (data.nodes && data.links) {
                    var model = go.Model.fromJson(JSON.stringify({
                        class: "GraphLinksModel",
                        nodeDataArray: data.nodes,
                        linkDataArray: data.links
                    }));
                    myDiagram.model = model;
                }
            })
            .catch(error => console.error('Error al cargar el flujo:', error));
    }

</script>
{% endblock %}

_____

<!-- /home/amigro/app/templates/django_admin_template.html -->
{% extends 'admin/base_site.html' %}
{% block content %}
<div id="flow-canvas" style="width: 100%; height: 400px; background: #f4f4f4; border: 1px solid #ccc;"></div>

<script>
    jsPlumb.ready(function() {
        var instance = jsPlumb.getInstance({
            // Configuración básica
            PaintStyle: { stroke: '#456', strokeWidth: 3 },
            Connector: ["Straight"],
            Anchor: "Continuous"
        });

        // Crear nodos
        var node1 = document.createElement('div');
        node1.innerText = 'Pregunta 1';
        node1.style.width = '100px';
        node1.style.height = '100px';
        node1.style.background = '#fff';
        node1.style.position = 'absolute';
        node1.style.left = '50px';
        node1.style.top = '50px';

        var node2 = document.createElement('div');
        node2.innerText = 'Pregunta 2';
        node2.style.width = '100px';
        node2.style.height = '100px';
        node2.style.background = '#fff';
        node2.style.position = 'absolute';
        node2.style.left = '200px';
        node2.style.top = '50px';

        document.getElementById('flow-canvas').appendChild(node1);
        document.getElementById('flow-canvas').appendChild(node2);

        instance.draggable(node1);
        instance.draggable(node2);

        // Conectar nodos
        instance.connect({ source: node1, target: node2 });
    });
</script>
{% endblock %}

_____


<!-- /home/amigro/app/templates/index.html -->
<!DOCTYPE html>
<html lang="es">

<head>
    <!-- Required meta tags -->
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <!-- Bootstrap CSS -->
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css"
        integrity="sha384-JcKb8q3iqJ61gNV9KGb8thSsNjpSL0n8PARn9HuZOnIxN0hoP+VmmDGMN5t9UJ0Z" crossorigin="anonymous">
    <!-- Font Awesome para iconos -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">
    <title>Prueba de envíos para el Chatbot de Amigro</title>
    <style>
        body {
            background-color: #f8f9fa;
        }

        .container {
            margin-top: 50px;
            margin-bottom: 50px;
        }

        .form-section {
            background-color: #ffffff;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
        }

        .form-section h2 {
            margin-bottom: 20px;
        }

        .preloaded-vars {
            margin-top: 15px;
        }

        .preloaded-vars input {
            margin-bottom: 10px;
        }

        .send-button {
            margin-top: 20px;
        }

        .chat-textarea {
            height: 300px;
            resize: none;
        }

        .loading-spinner {
            display: none;
            text-align: center;
            margin-top: 10px;
        }

        .alert {
            display: none;
            margin-top: 20px;
        }
    </style>
</head>

<body>
    <div class="container">
        <!-- Sección de Pruebas -->
        <div class="form-section">
            <h2>Ejecutor de Pruebas del Chatbot de Amigro</h2>
            <form id="test-form">
                <!-- Selección de Funciones -->
                <div class="form-group">
                    <label for="functions"><strong>Selecciona Funciones:</strong></label>
                    <select multiple class="form-control" id="functions" required>
                        <option value="send_message">Enviar Mensaje</option>
                        <option value="send_link">Enviar Link</option>
                        <option value="execute_action">Ejecutar Acción</option>
                        <option value="send_image">Enviar Imagen</option>
                        <!-- Agrega más funciones según sea necesario -->
                    </select>
                    <small class="form-text text-muted">Mantén presionada la tecla Ctrl (Windows) o Command (Mac) para seleccionar múltiples opciones.</small>
                </div>

                <!-- Selección de Plataforma -->
                <div class="form-group">
                    <label for="platform"><strong>Selecciona Plataforma:</strong></label>
                    <select class="form-control" id="platform" required>
                        <option value="">-- Selecciona una Plataforma --</option>
                        <option value="telegram">Telegram</option>
                        <option value="whatsapp">WhatsApp</option>
                        <option value="messenger">Messenger</option>
                        <option value="instagram">Instagram</option>
                    </select>
                </div>

                <!-- Variables Pre-Cargadas -->
                <div class="preloaded-vars" id="preloadedVars">
                    <!-- Las variables se agregarán aquí dinámicamente -->
                </div>

                <!-- Definición del Mensaje o Acción -->
                <div class="form-group">
                    <label for="action"><strong>Define el Mensaje/Acción:</strong></label>
                    <textarea class="form-control chat-textarea" id="action" placeholder="Escribe el mensaje, link o acción a ejecutar aquí..." required></textarea>
                </div>

                <!-- Botón de Envío -->
                <button type="submit" class="btn btn-primary send-button"><i class="fas fa-paper-plane"></i> Enviar Prueba</button>

                <!-- Spinner de Carga -->
                <div class="loading-spinner" id="loadingSpinner">
                    <div class="spinner-border text-primary" role="status">
                        <span class="sr-only">Enviando...</span>
                    </div>
                </div>

                <!-- Alertas -->
                <div class="alert alert-success" role="alert" id="successAlert">
                    Prueba enviada exitosamente.
                </div>
                <div class="alert alert-danger" role="alert" id="errorAlert">
                    Ocurrió un error al enviar la prueba.
                </div>
            </form>
        </div>

        <!-- Sección de Chatbot (opcional) -->
        <div class="row d-flex justify-content-center mt-5">
            <div class="col-12 text-center">
                <h1 class="h3">Prueba de envíos para el Chatbot de Amigro</h1>
                <p>Solo es para uso del Administrador - Pablo Lelo de Larrea H.</p>
            </div>
        </div>

        <div class="row d-flex justify-content-center mt-4">
            <div class="col-6">
                <form id="chat-form">
                    <div class="form-group">
                        <label for="exampleFormControlTextarea1" class="h4">Chatbot</label>
                        <textarea class="form-control chat-textarea" id="chat-text" readonly rows="10"></textarea><br>
                    </div>
                    <div class="form-group">
                        <input class="form-control" placeholder="Enter text here" id="input" type="text" required></br>
                    </div>
                    <div class="form-group">
                        <label for="platform">Selecciona Plataforma</label>
                        <select class="form-control" id="platform" required>
                            <option value="telegram">Telegram</option>
                            <option value="whatsapp">WhatsApp</option>
                            <option value="messenger">Messenger</option>
                            <option value="instagram">Instagram</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="use-gpt">¿Usar GPT?</label>
                        <select class="form-control" id="use-gpt" required>
                            <option value="true">Sí</option>
                            <option value="false">No</option>
                        </select>
                    </div>
                    <input class="btn btn-primary btn-lg btn-block" id="submit" type="button" value="Send">
                </form>
            </div>
        </div>
    </div>

    <!-- Bootstrap JS, Popper.js, and jQuery -->
    <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"
        integrity="sha384-DfXdz2htPH0lsSSs5nCTpuj/zy4C+OGpamoFVy38MVBnE+IbbVYUew+OrCXaRkfj" crossorigin="anonymous">
    </script>
    <script src="https://cdn.jsdelivr.net/npm/popper.js@1.16.1/dist/umd/popper.min.js"
        integrity="sha384-9/reFTGAW83EW2RDu2S0VKaIzap3H66lZH81PoYlFhbGU+6BZp6G7niu735Sk7lN" crossorigin="anonymous">
    </script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"
        integrity="sha384-B4gt1jrGC7Jh4AgTPSdUtOBvfO8shuf57BaghqFfPlYxofvL8/KUEfYiJOMMV+rV" crossorigin="anonymous">
    </script>

    <script>
        document.addEventListener('DOMContentLoaded', function () {
            // Variables para la sección de pruebas
            const testForm = document.getElementById('test-form');
            const preloadedVarsContainer = document.getElementById('preloadedVars');
            const platformSelectTest = document.getElementById('platform');
            const functionsSelect = document.getElementById('functions');
            const actionInput = document.getElementById('action');
            const loadingSpinner = document.getElementById('loadingSpinner');
            const successAlert = document.getElementById('successAlert');
            const errorAlert = document.getElementById('errorAlert');

            // Funciones disponibles con sus campos
            const availableFunctions = {
                'send_message': {
                    name: 'Enviar Mensaje',
                    fields: [
                        { label: 'Número de WhatsApp', id: 'whatsapp_number', type: 'text', placeholder: 'Ej. +1234567890' },
                        { label: 'ID de Telegram', id: 'telegram_id', type: 'text', placeholder: 'Ej. @usuario' },
                        { label: 'ID de Messenger', id: 'messenger_id', type: 'text', placeholder: 'Ej. 123456789' },
                        { label: 'ID de Instagram', id: 'instagram_id', type: 'text', placeholder: 'Ej. usuario_instagram' }
                    ]
                },
                'send_link': {
                    name: 'Enviar Link',
                    fields: [
                        { label: 'Link a Enviar', id: 'link', type: 'url', placeholder: 'Ej. https://ejemplo.com' }
                    ]
                },
                'execute_action': {
                    name: 'Ejecutar Acción',
                    fields: [
                        { label: 'Nombre de la Acción', id: 'action_name', type: 'text', placeholder: 'Ej. CrearUsuario' },
                        { label: 'Parámetros de la Acción', id: 'action_params', type: 'text', placeholder: 'Ej. {"nombre":"Juan","edad":30}' }
                    ]
                },
                'send_image': {
                    name: 'Enviar Imagen',
                    fields: [
                        { label: 'URL de la Imagen', id: 'image_url', type: 'url', placeholder: 'Ej. https://ejemplo.com/imagen.jpg' }
                    ]
                }
                // Agrega más funciones según sea necesario
            };

            // Actualizar variables pre-cargadas según las funciones y plataforma seleccionadas
            function updatePreloadedVars() {
                const selectedFunctions = Array.from(functionsSelect.selectedOptions).map(option => option.value);
                const selectedPlatform = platformSelectTest.value;

                // Limpiar contenedor
                preloadedVarsContainer.innerHTML = '';

                // Iterar sobre las funciones seleccionadas y agregar campos necesarios
                selectedFunctions.forEach(func => {
                    if (availableFunctions[func]) {
                        availableFunctions[func].fields.forEach(field => {
                            // Mostrar campos relevantes para la plataforma seleccionada o campos generales
                            if (field.id.includes(selectedPlatform) || ['link', 'action_name', 'action_params', 'image_url'].includes(field.id)) {
                                const formGroup = document.createElement('div');
                                formGroup.classList.add('form-group');

                                const label = document.createElement('label');
                                label.setAttribute('for', field.id);
                                label.innerHTML = field.label;

                                const input = document.createElement('input');
                                input.classList.add('form-control');
                                input.setAttribute('type', field.type);
                                input.setAttribute('id', field.id);
                                input.setAttribute('placeholder', field.placeholder);
                                input.required = true;

                                formGroup.appendChild(label);
                                formGroup.appendChild(input);
                                preloadedVarsContainer.appendChild(formGroup);
                            }
                        });
                    }
                });
            }

            // Escuchar cambios en la selección de funciones
            functionsSelect.addEventListener('change', updatePreloadedVars);

            // Escuchar cambios en la selección de plataforma
            platformSelectTest.addEventListener('change', updatePreloadedVars);

            // Manejar el envío del formulario de pruebas
            testForm.addEventListener('submit', async function (e) {
                e.preventDefault();

                // Obtener funciones seleccionadas
                const selectedFunctions = Array.from(functionsSelect.selectedOptions).map(option => option.value);
                if (selectedFunctions.length === 0) {
                    alert('Por favor selecciona al menos una función.');
                    return;
                }

                // Obtener plataforma seleccionada
                const platform = platformSelectTest.value;
                if (!platform) {
                    alert('Por favor selecciona una plataforma.');
                    return;
                }

                // Obtener valores de las variables pre-cargadas
                const formData = {};
                selectedFunctions.forEach(func => {
                    if (availableFunctions[func]) {
                        availableFunctions[func].fields.forEach(field => {
                            if (field.id.includes(platform) || ['link', 'action_name', 'action_params', 'image_url'].includes(field.id)) {
                                const value = document.getElementById(field.id).value.trim();
                                formData[field.id] = value;
                            }
                        });
                    }
                });

                // Obtener el mensaje o acción a ejecutar
                const action = actionInput.value.trim();
                if (!action) {
                    alert('Por favor define el mensaje, link o acción a ejecutar.');
                    return;
                }

                // Mostrar spinner de carga
                loadingSpinner.style.display = 'block';
                successAlert.style.display = 'none';
                errorAlert.style.display = 'none';

                try {
                    // Enviar datos al backend
                    const response = await fetch('/send-test-message/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': '{{ csrf_token }}'
                        },
                        body: JSON.stringify({
                            'functions': selectedFunctions,
                            'platform': platform,
                            'variables': formData,
                            'action': action
                        })
                    });

                    const data = await response.json();

                    if (response.ok) {
                        successAlert.style.display = 'block';
                        testForm.reset();
                        preloadedVarsContainer.innerHTML = '';
                    } else {
                        throw new Error(data.error || 'Error desconocido');
                    }
                } catch (error) {
                    console.error('Error:', error);
                    errorAlert.textContent = `Error: ${error.message}`;
                    errorAlert.style.display = 'block';
                } finally {
                    // Ocultar spinner de carga
                    loadingSpinner.style.display = 'none';
                }
            });

            // Inicializar variables pre-cargadas al cargar la página
            updatePreloadedVars();

            // Variables para la sección de chat (opcional)
            const chatForm = document.getElementById('chat-form');
            const chatMessages = document.getElementById('chatMessages');
            const messageInput = document.getElementById('input');
            const platformSelectChat = document.getElementById('platform');
            const useGptSelect = document.getElementById('use-gpt');
            const loadingSpinnerChat = document.getElementById('loadingSpinner');
            const platformIcon = document.getElementById('platformIcon');

            // Actualizar icono según la plataforma seleccionada
            function updatePlatformIconChat() {
                const platform = platformSelectChat.value;
                platformIcon.className = ''; // Limpiar clases anteriores
                switch (platform) {
                    case 'telegram':
                        platformIcon.classList.add('fab', 'fa-telegram-plane');
                        platformIcon.style.color = '#0088cc';
                        break;
                    case 'whatsapp':
                        platformIcon.classList.add('fab', 'fa-whatsapp');
                        platformIcon.style.color = '#25D366';
                        break;
                    case 'messenger':
                        platformIcon.classList.add('fab', 'fa-facebook-messenger');
                        platformIcon.style.color = '#0084ff';
                        break;
                    case 'instagram':
                        platformIcon.classList.add('fab', 'fa-instagram');
                        platformIcon.style.color = '#C13584';
                        break;
                    default:
                        platformIcon.classList.add('fas', 'fa-robot');
                        platformIcon.style.color = '#ffffff';
                }
            }

            // Inicializar icono al cargar la página
            updatePlatformIconChat();

            // Cambiar icono cuando se cambia la plataforma
            platformSelectChat.addEventListener('change', updatePlatformIconChat);

            // Función para agregar un mensaje al chat
            function addMessage(content, sender = 'bot') {
                const messageElement = document.createElement('div');
                messageElement.classList.add('message', sender);

                const messageBody = document.createElement('div');
                messageBody.classList.add('message-body');
                messageBody.innerHTML = content;

                messageElement.appendChild(messageBody);
                chatMessages.appendChild(messageElement);

                // Scroll al final
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }

            // Función para simular la respuesta del bot
            function simulateBotResponse(userMessage, platform, useGpt) {
                // Aquí puedes integrar lógica más compleja o llamadas a APIs
                // Por ahora, responderemos con una respuesta simple
                return new Promise((resolve) => {
                    setTimeout(() => {
                        let response = '';

                        if (useGpt === 'true') {
                            response = `GPT: Procesando tu mensaje en ${platform}: "${userMessage}"`;
                        } else {
                            response = `Bot: Recibí tu mensaje en ${platform}: "${userMessage}"`;
                        }

                        resolve(response);
                    }, 1000); // Simular tiempo de respuesta
                });
            }

            // Manejar el envío del formulario de chat
            chatForm.addEventListener('submit', async function (e) {
                e.preventDefault();

                const message = messageInput.value.trim();
                const platform = platformSelectChat.value;
                const useGpt = useGptSelect.value;

                if (message === "") {
                    alert("Por favor ingrese un mensaje.");
                    return;
                }

                // Agregar mensaje del usuario
                addMessage(message, 'user');

                // Limpiar el input
                messageInput.value = '';

                // Mostrar spinner de carga
                loadingSpinnerChat.style.display = 'block';

                try {
                    // Enviar mensaje al backend
                    const response = await fetch('/send-message/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': '{{ csrf_token }}'
                        },
                        body: JSON.stringify({
                            'message': message,
                            'platform': platform,
                            'use_gpt': useGpt
                        })
                    });

                    const data = await response.json();

                    // Simular la respuesta del bot
                    let botResponse = '';
                    if (data.response) {
                        botResponse = data.response;
                    } else {
                        // Si no hay respuesta del backend, usar la simulación local
                        botResponse = await simulateBotResponse(message, platform, useGpt);
                    }

                    // Agregar respuesta del bot
                    addMessage(botResponse, 'bot');
                } catch (error) {
                    console.error('Error:', error);
                    addMessage("Bot: Ocurrió un error al procesar tu mensaje.", 'bot');
                } finally {
                    // Ocultar spinner de carga
                    loadingSpinnerChat.style.display = 'none';
                }
            });

            // Opcional: manejar la tecla Enter para enviar el mensaje
            messageInput.addEventListener('keypress', function (e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    chatForm.dispatchEvent(new Event('submit'));
                }
            });
        });
    </script>
</body>

</html>

_____


# /home/amigro/chatbot_django/asgi.py
"""
ASGI config for chatbot_django project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatbot_django.settings')

application = get_asgi_application()
_____

# /home/amigro/chatbot_django/celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

# Establecer el entorno predeterminado de Django para las configuraciones de Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatbot_django.settings')

app = Celery('chatbot_django')

# Carga las configuraciones de Celery desde el archivo settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-detecta las tareas dentro de los apps instalados
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'check_and_renew_whatsapp_token_every_day': {
        'task': 'app.tasks.check_and_renew_whatsapp_token',
        'schedule': crontab(minute=0, hour=0),  # Se ejecuta diariamente a la medianoche
    },
    'check-whatsapp-token-every-day': {
        'task': 'app.tasks.check_and_update_whatsapp_token',
        'schedule': crontab(hour=0, minute=0),  # Ejecuta la tarea todos los días a medianoche
    },
    'clean_old_chat_logs': {
        'task': 'app.tasks.clean_old_chat_logs',
        'schedule': crontab(hour=1, minute=0),  # Ejecuta la tarea todos los días a la 1 AM
    },
    
} 

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

____

# /home/amigro/chatbot_django/settings.py
import os
import sentry_sdk
from pathlib import Path
from django.conf import settings
from sentry_sdk.integrations.django import DjangoIntegration


BASE_DIR = Path(__file__).resolve().parent.parent

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,
    send_default_pii=True
)

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-rxkhgtlsk84*0)-ivntl4&cnt8sp9ahu0aib$709q^crthve&u')

DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = [
    "35.209.109.141",
    "chatbot.amigro.org",
    "*.amigro.org",
    "localhost",
    "127.0.0.1"
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'app',
    'corsheaders',  # Correcto
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # CORS middleware
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Para archivos estáticos en producción
]

ROOT_URLCONF = 'chatbot_django.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'chatbot_django.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
#DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.postgresql',
#        'NAME': os.getenv('DB_NAME'),
#        'USER': os.getenv('DB_USER'),
#        'PASSWORD': os.getenv('DB_PASSWORD'),
#        'HOST': os.getenv('DB_HOST'),
#        'PORT': os.getenv('DB_PORT', '5432'),
#    }
#}
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/Mexico_City'
USE_TZ = True

USE_I18N = True

USE_L10N = True


STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS configuration
# CORS_ORIGIN_ALLOW_ALL = True  # Cambia a False en producción y define los dominios permitidos
CORS_ORIGIN_ALLOW_ALL = False
CORS_ORIGIN_WHITELIST = [
     'https://chatbot.amigro.org',
     'https://amigro.org',
]


# Celery configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_TASK_RETRY_DELAY = 300  # Reintentar cada 5 minutos
CELERY_TASK_MAX_RETRIES = 5  # Máximo 5 reintentos

CELERY_WORKER_LOG_FILE = '/home/amigro/logs/worker.log'
CELERY_WORKER_LOG_LEVEL = 'INFO'
CELERY_WORKER_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/error.log'),
            'formatter': 'verbose',
        },
        'telegram_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/telegram.log'),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'whatsapp_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/whatsapp.log'),
            'formatter': 'verbose',
        },
        'messenger_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/messenger.log'),
            'formatter': 'verbose',
        },
        'instagram_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/instagram.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'telegram': {
            'handlers': ['telegram_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'whatsapp': {
            'handlers': ['whatsapp_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'messenger': {
            'handlers': ['messenger_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'instagram': {
            'handlers': ['instagram_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}
_____

# /home/amigro/chatbot_django/urls.py
"""chatbot_django URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from app.admin import admin_site
from django.contrib import admin
from django.urls import path, include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.http import HttpResponse

def health_check(request):
    return HttpResponse("OK")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include("app.urls")),
    path('health/', health_check, name='health_check'),
]
urlpatterns += staticfiles_urlpatterns()
_____


# /home/amigro/chatbot_django/wsgi.py
"""
WSGI config for chatbot_django project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatbot_django.settings')

application = get_wsgi_application()
_____


# /home/amigro/app/admin.py

import json
from django.urls import path, reverse
from django.contrib import admin
from django.utils.html import format_html
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import (
    MetaAPI, WhatsAppAPI, TelegramAPI, MessengerAPI, InstagramAPI,
    Person, Pregunta, Worker, Buttons, Etapa, SubPregunta, GptApi,
    SmtpConfig, Chat, FlowModel, ChatState
)

# Definición personalizada del AdminSite
class CustomAdminSite(admin.AdminSite):
    site_header = "Amigro Admin"
    site_title = "Amigro Admin Portal"
    index_title = "Bienvenido a Amigro.org parte de Grupo huntRED®"

    def each_context(self, request):
        context = super().each_context(request)
        context['admin_css'] = 'admin/css/custom_admin.css'  # Estilos personalizados, si tienes alguno.
        return context

# Instancia de CustomAdminSite
admin_site = CustomAdminSite(name='custom_admin')

# Registrar los modelos con CustomAdminSite
@admin.register(Person, site=admin_site)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('name', 'apellido_paterno', 'apellido_materno', 'phone', 'nationality', 'skills', 'ubication', 'email', 'preferred_language')
    search_fields = ('name', 'apellido_paterno', 'phone', 'email', 'nationality')

@admin.register(Worker, site=admin_site)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ('name', 'job_id', 'company', 'job_type', 'salary', 'address', 'experience_required')
    search_fields = ('name', 'company', 'job_type')

@admin.register(Pregunta, site=admin_site)
class PreguntaAdmin(admin.ModelAdmin):
    list_display = ('name', 'etapa', 'option', 'input_type', 'requires_response')
    search_fields = ('name', 'etapa__nombre')  # Asegúrate de que 'nombre' exista en Etapa

@admin.register(SubPregunta, site=admin_site)
class SubPreguntaAdmin(admin.ModelAdmin):
    list_display = ('name', 'option', 'input_type', 'requires_response')
    search_fields = ('name', 'parent_sub_pregunta__name')

@admin.register(ChatState, site=admin_site)
class ChatStateAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'platform', 'current_question', 'last_interaction', 'context')
    search_fields = ('user_id', 'platform')

@admin.register(FlowModel, site=admin_site)
class FlowModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(TelegramAPI, site=admin_site)
class TelegramAPIAdmin(admin.ModelAdmin):
    list_display = ('bot_name', 'api_key')

@admin.register(WhatsAppAPI, site=admin_site)
class WhatsAppAPIAdmin(admin.ModelAdmin):
    list_display = ('phoneID', 'api_token')

@admin.register(MessengerAPI, site=admin_site)
class MessengerAPIAdmin(admin.ModelAdmin):
    list_display = ('page_access_token',)

@admin.register(InstagramAPI, site=admin_site)
class InstagramAPIAdmin(admin.ModelAdmin):
    list_display = ('app_id', 'access_token', 'instagram_account_id')

@admin.register(MetaAPI, site=admin_site)
class MetaAPIAdmin(admin.ModelAdmin):
    list_display = ('app_id', 'app_secret', 'verify_token')

@admin.register(GptApi, site=admin_site)
class GptApiAdmin(admin.ModelAdmin):
    list_display = ('api_token', 'model', 'organization')
    search_fields = ('model', 'organization')

@admin.register(Buttons, site=admin_site)
class ButtonsAdmin(admin.ModelAdmin):
    list_display = ('name', 'active')
    search_fields = ('name',)

@admin.register(Etapa, site=admin_site)
class EtapaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'activo')  # Asegúrate de que 'nombre' y 'descripcion' existan en Etapa
    search_fields = ('nombre', 'descripcion')

@admin.register(SmtpConfig, site=admin_site)
class SmtpConfigAdmin(admin.ModelAdmin):
    list_display = ('host', 'port', 'use_tls', 'use_ssl')
    search_fields = ('host',)

@admin.register(Chat, site=admin_site)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('From', 'To', 'ProfileName', 'created_at')  # Ajusta según los campos en Chat
    search_fields = ('From', 'To')

_____

# /home/amigro/app/apps.py

from django.apps import AppConfig

class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

_____

# /home/amigro/app/chatbot.py

import logging
from .models import ChatState, Pregunta, Person, FlowModel, Invitacion
from app.vacantes import match_person_with_jobs, get_available_slots, book_interview_slot, solicitud
from app.integrations.services import send_message, send_options, send_menu

# Inicializa el logger
logger = logging.getLogger(__name__)

class ChatBotHandler:
    def __init__(self):
        self.flow_model = None

    async def process_message(self, platform, user_id, text):
        """
        Procesa el mensaje del usuario y gestiona la conversación según el flujo de preguntas.
        """
        if not self.flow_model:
            self.flow_model = await FlowModel.objects.afirst()

        event = await self.get_or_create_event(user_id, platform)
        analysis = analyze_text(text)

        if not event.current_question:
            event.current_question = await self.flow_model.preguntas.afirst()  # Cambiado a 'preguntas'

        response, options = await self.process_user_response(event, text, analysis)

        await event.asave()
        await self.send_response(platform, user_id, response, options)

        return response, options

    async def get_or_create_event(self, user_id, platform):
        """
        Crea o recupera el estado del chat del usuario.
        """
        event, created = await ChatState.objects.aget_or_create(user_id=user_id)
        if created:
            event.flow_model = self.flow_model
            event.platform = platform
            await event.asave()
        else:
            if event.platform != platform:
                event.platform = platform
                await event.asave()
        return event

    async def process_user_response(self, event, user_message, analysis):
        """
        Procesa la respuesta del usuario y determina la siguiente pregunta en base a condiciones.
        """
        intents = analysis.get('intents', [])
        entities = analysis.get('entities', [])

        logger.info(f"Intenciones detectadas: {intents}")
        logger.info(f"Entidades detectadas: {entities}")

        # Menú Persistente
        if user_message.lower() in ['menu', 'inicio', 'volver', 'menu principal']:
            return await handle_persistent_menu(event)

        if 'saludo' in intents:
            response = "¡Hola! ¿En qué puedo ayudarte hoy?"
            return response, []

        elif 'despedida' in intents:
            response = "¡Hasta luego!"
            event.current_question = None
            return response, []

        elif 'buscar_vacante' in intents:
            response = "Claro, puedo ayudarte a buscar vacantes. ¿En qué área estás interesado?"
            event.current_question = await Pregunta.objects.aget(option='buscar_vacante')
            return response, []

        elif 'postular_vacante' in intents:
            response = "Para postularte a una vacante, necesito algunos datos. ¿Puedes proporcionarme tu nombre y habilidades?"
            event.current_question = await Pregunta.objects.aget(option='solicitar_datos')
            return response, []

        return await self.determine_next_question(event, user_message, analysis)

    async def determine_next_question(self, event, user_message, analysis):
        """
        Determina la siguiente pregunta en el flujo basado en la intención y entidades extraídas del mensaje.
        """
        # Si no hay una pregunta actual, asignar la primera pregunta del flujo
        if not event.current_question:
            event.current_question = await self.flow_model.preguntas.afirst()
            if not event.current_question:
                return "Lo siento, no se encontró una pregunta inicial en el flujo.", []

        # Obtener o crear un usuario asociado con el evento
        user, _ = await Person.objects.aget_or_create(number_interaction=event.user_id)

        # Verificar si la pregunta actual requiere habilidades
        if event.current_question.input_type == 'skills':
            user.skills = user_message
            await user.asave()

            recommended_jobs = match_person_with_jobs(user)
            if recommended_jobs:
                response = "Aquí tienes algunas vacantes que podrían interesarte:\n"
                for idx, (job, score) in enumerate(recommended_jobs[:5]):
                    response += f"{idx + 1}. {job['title']} en {job['company']}\n"
                response += "Por favor, ingresa el número de la vacante que te interesa."
                event.context = {'recommended_jobs': recommended_jobs}
                return response, []
            else:
                response = "Lo siento, no encontré vacantes que coincidan con tu perfil."
                return response, []

        # Manejo de selección de vacante
        elif event.current_question.input_type == 'select_job':
            try:
                job_index = int(user_message) - 1
            except ValueError:
                return "Por favor, ingresa un número válido.", []

            recommended_jobs = event.context.get('recommended_jobs')
            if recommended_jobs and 0 <= job_index < len(recommended_jobs):
                selected_job = recommended_jobs[job_index]
                event.context['selected_job'] = selected_job
                event.current_question = await Pregunta.objects.aget(option='schedule_interview')
                return event.current_question.content, []
            else:
                return "Selección inválida.", []

        # Procesar agendado de entrevista
        elif event.current_question.input_type == 'schedule_interview':
            selected_job = event.context.get('selected_job')
            if not selected_job:
                return "No se encontró la vacante seleccionada.", []

            available_slots = get_available_slots(selected_job)
            if available_slots:
                response = "Estos son los horarios disponibles para la entrevista:\n"
                for idx, slot in enumerate(available_slots):
                    response += f"{idx + 1}. {slot}\n"
                response += "Por favor, selecciona el número del horario que prefieras."
                event.context['available_slots'] = available_slots
                return response, []
            else:
                return "No hay horarios disponibles.", []

        # Reserva de entrevista
        elif event.current_question.input_type == 'confirm_interview_slot':
            try:
                slot_index = int(user_message) - 1
            except ValueError:
                return "Por favor, ingresa un número válido.", []

            available_slots = event.context.get('available_slots')
            if available_slots and 0 <= slot_index < len(available_slots):
                selected_slot = available_slots[slot_index]
                if book_interview_slot(event.context['selected_job'], slot_index, user):
                    response = f"Has reservado tu entrevista en el horario: {selected_slot}."
                    return response, []
                else:
                    return "No se pudo reservar el slot, por favor intenta nuevamente.", []
            else:
                return "Selección inválida.", []

        # Guardar el estado del evento
        await event.asave()
        next_question = await Pregunta.objects.filter(id__gt=event.current_question.id).first()
        if next_question:
            event.current_question = next_question
            return next_question.content, []
        else:
            event.current_question = None
            return "No hay más preguntas.", []

    async def send_response(self, platform, user_id, response, options=None):
        """
        Envía la respuesta generada al usuario, con opciones si están disponibles.
        """
        await send_message(platform, user_id, response)

        if options:
            await send_options(platform, user_id, options)

    async def recap_information(self, user):
        """
        Función para hacer un recap de la información proporcionada por el usuario y permitirle hacer ajustes.
        """
        recap_message = (
            f"Recapitulación de tu información:\n"
            f"Nombre: {user.name}\n"
            f"Apellido Paterno: {user.apellido_paterno}\n"
            f"Apellido Materno: {user.apellido_materno}\n"
            f"Fecha de Nacimiento: {user.fecha_nacimiento}\n"
            f"Sexo: {user.sexo}\n"
            f"Nacionalidad: {user.nationality}\n"
            f"Permiso de Trabajo: {user.permiso_trabajo}\n"
            f"CURP: {user.curp}\n"
            f"Ubicación: {user.ubicacion}\n"
            f"Experiencia Laboral: {user.work_experience}\n"
            f"Nivel Salarial Esperado: {user.nivel_salarial}"
        )
        return recap_message

    async def invite_known_person(self, referrer, name, apellido, phone_number):
        """
        Función para invitar a un conocido por WhatsApp y crear un pre-registro del invitado.
        """
        invitado, created = await Person.objects.aget_or_create(phone=phone_number, defaults={
            'name': name,
            'apellido_paterno': apellido
        })

        await Invitacion.objects.acreate(referrer=referrer, invitado=invitado)

        if created:
            mensaje = f"Hola {name}, has sido invitado por {referrer.name} a unirte a Amigro.org. ¡Únete a nuestra comunidad!"
            await send_message("whatsapp", phone_number, mensaje)

        return invitado



____

#/home/amigro/app/Event.py

import json
import os
import os.path as path
from typing import Dict, List, Tuple, Any
from django.conf import settings
from app.models import Pregunta, Buttons, SubPregunta
from app.singleton import singleton
import logging

# Inicializa el logger
logger = logging.getLogger('event')

#@singleton  # Si necesitas que sea singleton, descomenta esta línea.
class PersonData:

    @classmethod
    def getter(cls, user_id: str) -> Tuple[str, List[Dict[str, str]], str]:
        """
        Obtiene los datos del usuario.
        """
        logger.info(f"Obteniendo datos para usuario: {user_id}")
        return cls.valid_response(user_id)
    
    @classmethod
    def get_all(cls, user_id: str) -> Dict[str, Any]:
        """
        Obtiene todos los datos del usuario.
        """
        logger.info(f"Obteniendo todos los datos para usuario: {user_id}")
        return cls.read_json(user_id)

    @classmethod
    def setter(cls, user_id: str, user_response: str) -> None:
        """
        Establece la respuesta del usuario.
        """
        logger.info(f"Guardando respuesta para usuario {user_id}: {user_response}")
        interact = cls.initialize(Pregunta.objects.all()) if not cls.valid(user_id) else cls.read_json(user_id)

        # Refactoriza para manejar preguntas y sub-preguntas de forma separada
        for key, value in interact.items():
            if not value["response"]:
                value["response"] = user_response
                break
            for sub_preguntas in value["sub_pregunta"].values():
                for sub_pregunta in sub_preguntas:
                    if not sub_pregunta["response"]:
                        logger.info(f"SubPregunta: {sub_pregunta['request']}")
                        sub_pregunta["response"] = user_response
                        cls.write_json(user_id, interact)
                        return

        cls.write_json(user_id, interact)

    @classmethod
    def clear(cls, user_id: str) -> None:
        """
        Limpia los datos del usuario.
        """
        logger.info(f"Limpieza de datos para usuario {user_id}")
        interact = cls.read_json(user_id)
        if interact:
            interact.pop(next(iter(interact)))
            cls.write_json(user_id, interact)

    @classmethod
    def clear_all(cls) -> None:
        """
        Limpia todos los datos de todos los usuarios.
        """
        logger.warning("Limpieza de todos los datos de los usuarios.")
        media_dir = os.path.join(settings.MEDIA_ROOT)
        for filename in os.listdir(media_dir):
            if filename.endswith('.json'):
                os.remove(os.path.join(media_dir, filename))

    @classmethod
    def valid(cls, user_id: str) -> bool:
        """
        Verifica si existen datos para el usuario.
        """
        return path.exists(os.path.join(settings.MEDIA_ROOT, f"{user_id}.json"))

    @classmethod
    def valid_response(cls, user_id: str) -> Tuple[str, List[Dict[str, str]], str]:
        """
        Obtiene la respuesta válida para el usuario.
        """
        request, _button, p = "", [], ""
        interact = cls.read_json(user_id)
        for p, value in interact.items():
            if not value["response"]:
                return value["request"], value["buttons"], p
            for sub_preguntas in value["sub_pregunta"].values():
                for sp_data in sub_preguntas:
                    logger.info(f"SubPregunta: {sp_data['request']}")
                    if not sp_data["response"]:
                        return sp_data["request"], sp_data["buttons"], p
        return request, _button, p

    @classmethod
    def read_json(cls, user_id: str) -> Dict[str, Any]:
        """
        Lee el archivo JSON de interacciones del usuario.
        """
        file_path = os.path.join(settings.MEDIA_ROOT, f"{user_id}.json")
        try:
            with open(file_path, "r") as file:
                return json.load(file)
        except FileNotFoundError:
            logger.error(f"Archivo no encontrado para el usuario {user_id}")
            return {}
        except json.JSONDecodeError:
            logger.error(f"Error al decodificar JSON para el usuario {user_id}")
            return {}

    @classmethod
    def initialize(cls, preguntas: List[Pregunta]) -> Dict[str, Any]:
        """
        Inicializa los datos del usuario.
        """
        logger.info(f"Inicializando datos de usuario con {len(preguntas)} preguntas.")
        interact = {"init": {"request": "init", "response": "", "valid": "", "yes_or_not": "", "buttons": [], "sub_pregunta": {}}}
        for p in preguntas:
            buttons = [{"title": str(button.name), "id": str(button.id)} for button in Buttons.objects.filter(pregunta=p)]
            sub_pregunta_data = cls.build_subpreguntas(p)
            interact[p.option] = {
                "request": p.name,
                "response": "",
                "valid": p.valid,
                "yes_or_not": p.yes_or_not,
                "buttons": buttons,
                "sub_pregunta": sub_pregunta_data
            }
        return interact

    @staticmethod
    def build_subpreguntas(pregunta: Pregunta) -> Dict[str, Any]:
        """
        Crea la estructura de subpreguntas para una pregunta.
        """
        sub_pregunta_data = {}
        for sec in SubPregunta.objects.filter(pregunta=pregunta):
            buttons_sub = [{"title": str(button.name), "id": str(button.id)} for button in Buttons.objects.filter(sub_pregunta=sec)]
            etape_number = sec.etape.number if sec.etape else ""
            sub_pregunta_data.setdefault(etape_number, []).append({
                "request": sec.name,
                "response": "",
                "valid": sec.valid,
                "yes_or_not": sec.yes_or_not,
                "buttons": buttons_sub,
                "secuence": sec.secuence,
                "etape": etape_number
            })
        return sub_pregunta_data

    @classmethod
    def write_json(cls, user_id: str, data: Dict[str, Any]) -> None:
        """
        Escribe los datos del usuario en un archivo JSON.
        """
        file_path = os.path.join(settings.MEDIA_ROOT, f"{user_id}.json")
        with open(file_path, "w") as file:
            json.dump(data, file, indent=2)

    @classmethod
    def rename_file(cls, user_id: str) -> None:
        """
        Renombra el archivo JSON del usuario.
        """
        old_name = os.path.join(settings.MEDIA_ROOT, f"{user_id}.json")
        for i in range(20):
            new_name = os.path.join(settings.MEDIA_ROOT, f"{user_id}-{i}.json")
            if not path.exists(new_name):
                os.rename(old_name, new_name)
                logger.info(f"Archivo JSON renombrado para el usuario {user_id}")
                break

    @classmethod
    def valid_full(cls, data: Dict[str, Any]) -> bool:
        """
        Verifica si todos los datos del usuario están completos.
        """
        return all(value["response"] for key, value in data.items() if key != "end")

_____

# /home/amigro/app/google_calendar.py

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

def create_calendar_event(slot, user, job):
    # Configurar las credenciales
    creds = Credentials.from_authorized_user_file('path/to/credentials.json', ['https://www.googleapis.com/auth/calendar'])
    service = build('calendar', 'v3', credentials=creds)
    
    # Crear el evento
    event = {
        'summary': f'Entrevista con {user.name} para {job.name}',
        'start': {
            'dateTime': f"{slot['date']}T{slot['time']}:00",
            'timeZone': 'America/Mexico_City',
        },
        'end': {
            'dateTime': f"{slot['date']}T{slot['time']}:30",  # Duración de 30 minutos
            'timeZone': 'America/Mexico_City',
        },
        'attendees': [
            {'email': user.email},
        ],
    }
    
    event = service.events().insert(calendarId='primary', body=event).execute()
    return event.get('htmlLink')

_____

# /home/amigro/app/gpt.py
import requests
import json
import os
import openai
import logging

#openai.organization = "org-B19vTHzNZ5FIuzsFOgDmisDi"
#openai.api_key = os.getenv("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")
#openai.api_key = "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"
#openai.Model.list()
logger = logging.getLogger(__name__)

def gpt_message(api_token, text, model):
    """
    Genera una respuesta utilizando la API de OpenAI GPT.

    Args:
        api_token (str): El token de autenticación para la API de OpenAI.
        text (str): El texto de entrada para el modelo.
        model (str): El modelo a utilizar (por ejemplo, 'gpt-3.5-turbo').

    Returns:
        dict: La respuesta de la API de OpenAI.

    Raises:
        Exception: Si ocurre un error al llamar a la API.
    """
    try:
        openai.api_key = api_token

        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "user", "content": text}
            ]
        )
        return response
    except Exception as e:
        logger.error(f"Error al llamar a la API de OpenAI: {e}", exc_info=True)
        raise e  # Re-lanzar la excepción para que pueda ser manejada por el llamador

if __name__ == "__main__":
    # No incluyas tu API Key directamente en el código
    api_token = "TU_API_KEY_AQUÍ"
    text = "Formúleme la siguiente pregunta de una manera realista..."
    model = "gpt-3.5-turbo"

    response = gpt_message(api_token, text, model)
    print(response)



_____

# /home/amigro/app/models.py

from django.db import models
from datetime import datetime

# Estado del Chat
class ChatState(models.Model):
    user_id = models.CharField(max_length=50)
    platform = models.CharField(max_length=20)  # 'telegram', 'whatsapp', 'messenger'
    current_question = models.ForeignKey('Pregunta', on_delete=models.CASCADE, null=True, blank=True)
    last_interaction = models.DateTimeField(auto_now=True)
    context = models.JSONField(blank=True, null=True, default=dict)

    def __str__(self):
        return f"ChatState {self.user_id} - {self.platform}"

class Condicion(models.Model):
    nombre = models.CharField(max_length=100)
    valor_esperado = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Condicion: {self.nombre} (espera: {self.valor_esperado})"

class Etapa(models.Model):
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class Pregunta(models.Model):
    INPUT_TYPE_CHOICES = [
        ('text', 'Texto'),
        ('name', 'Nombre'),
        ('apellido_paterno', 'Apellido Paterno'),
        ('apellido_materno', 'Apellido Materno'),
        ('nationality', 'Nacionalidad'),
        ('fecha_nacimiento', 'Fecha de Nacimiento'),
        ('sexo', 'Sexo'),
        ('email', 'Email'),
        ('phone', 'Celular'),
        ('family_traveling', 'Viaja con Familia'),
        ('policie', 'Politica Migratoria'),
        ('group_aditionality', 'Viaja en Grupo'),
        ('passport', 'Pasaporte'),
        ('additional_official_documentation', 'Documentación Adicional'),
        ('int_work', 'Intención de Trabajo'),
        ('menor', 'Menores'),
        ('refugio', 'Refugio'),
        ('perm_humanitario', 'Permiso Humanitario'),
        ('solicita_refugio', 'Solicitud de Refugio'),
        ('cita', 'Fecha de Cita'),
        ('piensa_solicitar_refugio', 'Contempla Solicitud de Refugio'),
        ('industria_work', 'Industria de Trabajo'),
        ('licencia', 'Licencia para Trabajar'),
        ('curp', 'CURP'),
        ('date_permit', 'Fecha del Permiso'),
        ('ubication', 'Ubicación'),
        ('work_experience', 'Experiencia Laboral'),
        ('saludo', 'Saludo'),
        ('file', 'Archivo / CV'),
        ('per_trabajo', 'Permiso de Trabajo'),
        ('preferred_language', 'Idioma Preferido'),
        ('skills', 'Habilidades'),
        ('experience_years', 'Años de Experiencia'),
        ('desired_job_types', 'Tipo de Trabajo Deseado'),
        ('nivel_salarial', 'Nivel Salarial Deseado'),
    ]

    ACTION_TYPE_CHOICES = [
        ('none', 'Ninguna acción'),
        ('mostrar_vacantes', 'Mostrar Vacantes'),
        ('enviar_whatsapp_plantilla', 'Enviar Plantilla WhatsApp'),
        ('enviar_imagen', 'Enviar Imagen'),
        ('enviar_url', 'Enviar URL'),
        ('recap', 'Hacer Recapitulación'),
        # Otras acciones personalizadas que necesites
    ]

    name = models.TextField(max_length=800)
    etapa = models.ForeignKey('Etapa', on_delete=models.CASCADE, default=1)
    option = models.CharField(max_length=50)
    valid = models.BooleanField(null=True, blank=True)
    active = models.BooleanField(default=True)
    content = models.TextField(blank=True, null=True)
    sub_pregunta = models.ManyToManyField('SubPregunta', blank=True, related_name='pregunta_principal')
    decision = models.JSONField(blank=True, null=True, default=dict)  # {respuesta: id_pregunta_siguiente}
    condiciones = models.ManyToManyField(Condicion, blank=True)
    input_type = models.CharField(max_length=100, choices=INPUT_TYPE_CHOICES, blank=True, null=True)
    requires_response = models.BooleanField(default=True)
    field_person = models.CharField(max_length=50, blank=True, null=True)  # Relaciona la pregunta con el campo de Person
    action_type = models.CharField(max_length=50, choices=ACTION_TYPE_CHOICES, default='none')  # Acciones personalizadas

    def __str__(self):
        return str(self.name)


class SubPregunta(models.Model):
    INPUT_TYPE_CHOICES = Pregunta.INPUT_TYPE_CHOICES
    ACTION_TYPE_CHOICES = Pregunta.ACTION_TYPE_CHOICES  # Mismas opciones que Pregunta

    name = models.CharField(max_length=800)
    option = models.CharField(max_length=50)
    valid = models.BooleanField(null=True, blank=True)
    active = models.BooleanField(default=True)
    content = models.TextField(blank=True, null=True)
    parent_sub_pregunta = models.ForeignKey('self', blank=True, null=True, on_delete=models.SET_NULL)
    decision = models.JSONField(blank=True, null=True, default=dict)
    input_type = models.CharField(max_length=100, choices=INPUT_TYPE_CHOICES, blank=True, null=True)
    requires_response = models.BooleanField(default=True)
    field_person = models.CharField(max_length=50, blank=True, null=True)  # Relaciona la subpregunta con el campo de Person
    action_type = models.CharField(max_length=50, choices=ACTION_TYPE_CHOICES, default='none')  # Acciones personalizadas

    def __str__(self):
        return str(self.name)

class TelegramAPI(models.Model):
    api_key = models.CharField(max_length=255)
    bot_name = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.bot_name or "Telegram Bot"

class MetaAPI(models.Model):
    app_id = models.CharField(max_length=255, default='662158495636216')
    app_secret = models.CharField(max_length=255, default='7732534605ab6a7b96c8e8e81ce02e6b')
    verify_token = models.CharField(max_length=255, default='amigro_secret_token')

    def __str__(self):
        return f"MetaAPI {self.app_id}"

class WhatsAppAPI(models.Model):
    phoneID = models.CharField(max_length=100)
    api_token = models.CharField(max_length=500)
    WABID = models.CharField(max_length=100, default='104851739211207')
    v_api = models.CharField(max_length=100)

    def __str__(self):
        return f"WhatsApp API {self.phoneID}"

class MessengerAPI(models.Model):
    page_access_token = models.CharField(max_length=255)

    def __str__(self):
        return "Messenger Configuration"

class InstagramAPI(models.Model):
    app_id = models.CharField(max_length=255, default='1615393869401916')
    access_token = models.CharField(max_length=255, default='5d8740cb80ae42d8b5cafb47e6c461d5')
    instagram_account_id = models.CharField(max_length=255, default='17841457231476550')

    def __str__(self):
        return f"InstagramAPI {self.app_id}"

class GptApi(models.Model):
    api_token = models.CharField(max_length=500)
    organization = models.CharField(max_length=100, blank=True, null=True)
    project = models.CharField(max_length=100, blank=True, null=True)
    model = models.CharField(max_length=100)
    form_pregunta = models.CharField(max_length=500)
    work_pregunta = models.CharField(max_length=500)

    def __str__(self):
        return f"Model: {self.model} | Organization: {self.organization} | Project: {self.project}"

class Chat(models.Model):
    body = models.TextField(max_length=1000)
    SmsStatus = models.CharField(max_length=15, null=True, blank=True)
    From = models.CharField(max_length=15)
    To = models.CharField(max_length=15)
    ProfileName = models.CharField(max_length=50)
    ChannelPrefix = models.CharField(max_length=50)
    MessageSid = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True) #Agregando campo de fecha de creación
    updated_at = models.DateTimeField(auto_now_add=True) #Agregando campo de fecha de creación
    message_count = models.IntegerField(default=0)

    def __str__(self):
        return str(self.body)

class Worker(models.Model):
    name = models.CharField(max_length=100)
    job_id = models.CharField(max_length=100, blank=True, null=True)
    url_name = models.CharField(max_length=100, blank=True, null=True)
    salary = models.CharField(max_length=100, blank=True, null=True)
    job_type = models.CharField(max_length=100, blank=True, null=True)
    img_company = models.CharField(max_length=500, blank=True, null=True)
    company = models.CharField(max_length=100, blank=True, null=True)
    address = models.CharField(max_length=200, blank=True, null=True)
    longitude = models.CharField(max_length=100, blank=True, null=True)
    latitude = models.CharField(max_length=100, blank=True, null=True)
    required_skills = models.TextField(blank=True, null=True)
    experience_required = models.IntegerField(blank=True, null=True)
    job_description = models.TextField(blank=True, null=True)
    interview_slots = models.JSONField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['job_id']),
            models.Index(fields=['company']),
        ]

    def __str__(self) -> str:
        return str(self.name)

class Person(models.Model):
    number_interaction = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=100)
    apellido_paterno = models.CharField(max_length=200, blank=True, null=True)
    apellido_materno = models.CharField(max_length=200, blank=True, null=True)
    nationality = models.CharField(max_length=100, blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    sexo = models.CharField(max_length=20, choices=[('M', 'Masculino'), ('F', 'Femenino'), ('O', 'Otro')])
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=40, blank=True, null=True)
    family_traveling = models.BooleanField(default=False)
    policie = models.BooleanField(default=False)
    group_aditionality = models.BooleanField(default=False)
    passport = models.CharField(max_length=50, blank=True, null=True)
    additional_official_documentation = models.CharField(max_length=50, blank=True, null=True)
    int_work = models.BooleanField(default=False)
    menor = models.BooleanField(default=False)
    refugio = models.BooleanField(default=False)
    perm_humanitario = models.BooleanField(default=False)
    solicita_refugio = models.BooleanField(default=False)
    cita = models.DateTimeField(blank=True, null=True)
    piensa_solicitar_refugio = models.BooleanField(default=False)
    industria_work = models.BooleanField(default=False)
    licencia = models.BooleanField(default=False)
    curp = models.CharField(max_length=50, blank=True, null=True)
    date_permit = models.DateField(blank=True, null=True)
    ubication = models.CharField(max_length=100, blank=True, null=True)
    work_experience = models.TextField(blank=True, null=True)
    saludo = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='person_files/', blank=True, null=True)
    per_trabajo = models.TextField(blank=True, null=True)
    preferred_language = models.CharField(max_length=5, default='es_MX')
    skills = models.TextField(blank=True, null=True)
    experience_years = models.IntegerField(blank=True, null=True)
    desired_job_types = models.CharField(max_length=100, blank=True, null=True)
    nivel_salarial = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.name} {self.lastname}"

class Invitacion(models.Model):
    referrer = models.ForeignKey(Person, related_name='invitaciones_enviadas', on_delete=models.CASCADE)
    invitado = models.ForeignKey(Person, related_name='invitaciones_recibidas', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class SmtpConfig(models.Model):
    host = models.CharField(max_length=255)
    port = models.IntegerField()
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    use_tls = models.BooleanField(default=True)
    use_ssl = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.host}:{self.port}"

class Buttons(models.Model):
    name = models.CharField(max_length=800)
    active = models.BooleanField()
    pregunta = models.ManyToManyField(Pregunta, blank=True)
    sub_pregunta = models.ManyToManyField(SubPregunta, blank=True)

    def __str__(self):
        return str(self.name)

class FlowModel(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    preguntas = models.ManyToManyField(Pregunta, related_name='flowmodels')
    flow_data_json = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


_____


# /home/amigro/app/nlp_utils.py

import spacy
from spacy.matcher import Matcher
import logging

logger = logging.getLogger(__name__)

try:
    # Cargar el modelo en español de spaCy
    nlp = spacy.load("es_core_news_sm")
except Exception as e:
    logger.error(f"Error al cargar el modelo de spaCy: {e}")
    raise e  # Re-lanzar la excepción para que el programa pueda manejarlo adecuadamente

# Inicializar el Matcher de spaCy
matcher = Matcher(nlp.vocab)

# Definir patrones para identificar intenciones
patterns = [
    {"label": "saludo", "pattern": [{"LOWER": {"IN": ["hola", "buenos días", "buenas tardes", "buenas noches"]}}]},
    {"label": "despedida", "pattern": [{"LOWER": {"IN": ["adiós", "hasta luego", "nos vemos", "chao", "gracias"]}}]},
    {"label": "buscar_vacante", "pattern": [{"LEMMA": "buscar"}, {"LEMMA": "vacante"}]},
    {"label": "postular_vacante", "pattern": [{"LEMMA": "postular"}, {"LEMMA": "vacante"}]},
    # Añade más patrones según tus necesidades
]

# Añadir patrones al Matcher
for pattern in patterns:
    matcher.add(pattern["label"], [pattern["pattern"]])

def analyze_text(text):
    """
    Analiza el texto del usuario y extrae intenciones y entidades.

    Args:
        text (str): Mensaje del usuario.

    Returns:
        dict: Diccionario con intenciones y entidades extraídas.
    """
    try:
        doc = nlp(text.lower())

        # Buscar patrones de intención
        matches = matcher(doc)
        intents = []
        for match_id, start, end in matches:
            intent = nlp.vocab.strings[match_id]
            intents.append(intent)

        # Extraer entidades nombradas
        entities = [(ent.text, ent.label_) for ent in doc.ents]

        # Retornar análisis
        return {
            "intents": intents,
            "entities": entities,
        }
    except Exception as e:
        logger.error(f"Error al analizar el texto: {e}", exc_info=True)
        return {
            "intents": [],
            "entities": [],
        }

_____

# /home/amigro/app/singleton.py
def singleton(cls):
    instances = dict()

    def wrap(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
        
    return wrap


_____

# /home/amigro/app/tasks.py

import requests
from celery import shared_task
from app.integrations.services import WhatsAppService, MessengerService, TelegramService, send_options, WhatsAppAPI, MessengerAPI, TelegramAPI, InstagramAPI
from app.models import Person, Worker, WhatsAppAPI
from app.vacantes import match_person_with_jobs
import logging

# Inicializa el logger
logger = logging.getLogger('celery_tasks')

# Tarea para enviar mensajes de WhatsApp de manera asíncrona
@shared_task(bind=True, max_retries=3)
def send_whatsapp_message(self, recipient, message):  # Añadir 'self' como primer argumento
    try:
        whatsapp_api = WhatsAppAPI.objects.first()
        if whatsapp_api:
            api_token = whatsapp_api.api_token
            phone_id = whatsapp_api.phoneID
            version_api = whatsapp_api.v_api
            whatsapp_service = WhatsAppService(api_token=api_token, phone_id=phone_id, version_api=version_api)
            whatsapp_service.send_message(recipient, message)
            logger.info(f"Mensaje de WhatsApp enviado correctamente a {recipient}")
        else:
            logger.error("No se encontró configuración de API de WhatsApp.")
    except Exception as e:
        logger.error(f"Error enviando mensaje a WhatsApp: {e}")
        self.retry(exc=e, countdown=60)  # Reintenta después de 60 segundos

# Tarea para enviar botones de WhatsApp de manera asíncrona
@shared_task(bind=True, max_retries=3)
def send_whatsapp_options(self, recipient, message, options, api_token, phone_id, version_api):
    try:
        send_options('whatsapp', recipient, message)
        logger.info(f"Opciones enviadas a WhatsApp {recipient}")
    except Exception as e:
        logger.error(f"Error enviando opciones a WhatsApp: {e}")
        self.retry(exc=e, countdown=60)

# Tarea para enviar mensajes de Telegram de manera asíncrona
@shared_task(bind=True, max_retries=3)
def send_telegram_message(self, chat_id, message, bot_token):
    try:
        telegram_service = TelegramService(bot_token=bot_token)
        telegram_service.send_message(chat_id, message)
        logger.info(f"Mensaje de Telegram enviado correctamente a {chat_id}")
    except Exception as e:
        logger.error(f"Error enviando mensaje a Telegram: {e}")
        self.retry(exc=e, countdown=60)

# Tarea para enviar botones de Telegram de manera asíncrona
@shared_task(bind=True, max_retries=3)
def send_telegram_options(self, chat_id, message, options, bot_token):
    try:
        send_options('telegram', chat_id, message)
        logger.info(f"Opciones enviadas a Telegram {chat_id}")
    except Exception as e:
        logger.error(f"Error enviando opciones a Telegram: {e}")
        self.retry(exc=e, countdown=60)

# Tarea para enviar mensajes de Messenger de manera asíncrona
@shared_task(bind=True, max_retries=3)
def send_messenger_message(self, recipient_id, message, access_token):
    try:
        messenger_service = MessengerService(access_token=access_token)
        messenger_service.send_message(recipient_id, message)
        logger.info(f"Mensaje de Messenger enviado correctamente a {recipient_id}")
    except Exception as e:
        logger.error(f"Error enviando mensaje a Messenger: {e}")
        self.retry(exc=e, countdown=60)

# Actualizar recomendaciones de trabajo para una persona
@shared_task
def update_job_recommendations():
    try:
        for person in Person.objects.filter(int_work=True):
            matching_jobs = match_person_with_jobs(person)
            logger.info(f"Recomendaciones de trabajo actualizadas para {person.name}")
    except Exception as e:
        logger.error(f"Error actualizando recomendaciones de trabajo: {e}")

# Limpiar estados de chat antiguos
@shared_task
def clean_old_chat_states():
    try:
        # Agregar lógica para eliminar estados antiguos
        logger.info("Estados de chat antiguos limpiados correctamente.")
    except Exception as e:
        logger.error(f"Error limpiando estados de chat antiguos: {e}")


_____


# /home/amigro/app/tests.py

from django.test import TestCase
from .models import FlowModel
from django.urls import reverse
import json

class FlowModelTest(TestCase):
    def setUp(self):
        self.flow = FlowModel.objects.create(
            name='Flujo de Prueba',
            description='Descripción del flujo de prueba',
            flow_data_json=json.dumps({
                'nodes': [
                    {'key': 'node1', 'text': 'Inicio', 'type': 'text', 'fill': 'lightblue'},
                    {'key': 'node2', 'text': 'Pregunta 1', 'type': 'text', 'fill': 'lightblue'}
                ],
                'links': [
                    {'key': 'link1', 'from': 'node1', 'to': 'node2', 'text': 'Sí'}
                ]
            })
        )

    def test_load_flow(self):
        response = self.client.get(reverse('admin:load_flow') + f'?flowmodel_id={self.flow.id}')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('nodes', data)
        self.assertIn('links', data)
        self.assertEqual(len(data['nodes']), 2)
        self.assertEqual(len(data['links']), 1)

    def test_save_flow(self):
        new_flow_data = {
            'flowmodel_id': self.flow.id,
            'nodes': [
                {'key': 'node1', 'text': 'Inicio', 'type': 'text', 'fill': 'lightblue'},
                {'key': 'node2', 'text': 'Pregunta 1 Actualizada', 'type': 'text', 'fill': 'lightblue'}
            ],
            'links': [
                {'key': 'link1', 'from': 'node1', 'to': 'node2', 'text': 'No'}
            ]
        }
        response = self.client.post(reverse('admin:save_flow'), data=json.dumps(new_flow_data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        self.flow.refresh_from_db()
        updated_flow = json.loads(self.flow.flow_data_json)
        self.assertEqual(updated_flow['nodes'][1]['text'], 'Pregunta 1 Actualizada')
        self.assertEqual(updated_flow['links'][0]['text'], 'No')
___
# /home/amigro/app/urls.py

from django.urls import path, include  # Asegúrate de importar `include`
from django.conf.urls.static import static
from django.conf import settings
from . import views
from .views import index
from app.admin import admin_site
from app.integrations.telegram import telegram_webhook
from app.integrations.whatsapp import whatsapp_webhook
from app.integrations.messenger import messenger_webhook
from app.integrations.instagram import instagram_webhook

urlpatterns = [
    path('', index, name="index"),  # Página principal

    # Webhooks para las distintas integraciones
    path('webhook/whatsapp/048bd814-7716-4073-8acf-d491db68e9a1', whatsapp_webhook, name='whatsapp_webhook'),
    path('webhook/telegram/871198362', telegram_webhook, name='telegram_webhook'),
    path('webhook/messenger/109623338672452', messenger_webhook, name='messenger_webhook'),
    path('webhook/instagram/109623338672452', instagram_webhook, name='instagram_webhook'),  # Token para Instagram

    # Rutas para administrar preguntas
    path('preguntas/', views.create_pregunta, name='create_pregunta'),
    path('preguntas/<int:id>/', views.update_pregunta, name='update_pregunta'),
    path('preguntas/<int:id>/position/', views.update_position, name='update_position'),
    path('preguntas/<int:id>/delete/', views.delete_pregunta, name='delete_pregunta'),

    # Rutas para la administración del flujo del chatbot
    path('admin/', admin_site.urls),  # Admin personalizado

    # Rutas relacionadas con el flujo del chatbot
    path('admin/app/flowmodel/<int:flowmodel_id>/edit-flow/', views.edit_flow, name='edit_flow'),
    path('admin/app/save_flow_structure/', views.save_flow_structure, name='save_flow_structure'),
    path('admin/app/export_chatbot_flow/', views.export_chatbot_flow, name='export_chatbot_flow'),
    path('admin/app/load_flow_data/', views.load_flow_data, name='load_flow_data'),

    # Rutas para enviar mensajes
    path('send-message/', views.send_message, name='send_message'),
    path('send-test-message/', views.send_test_message, name='send_test_message'),
]

# Añadir rutas para archivos estáticos y media
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
#APP 713dd8c2-0801-4720-af2a-910da63c42d3   7732534605ab6a7b96c8e8e81ce02e6b
_____

# /home/amigro/app/vacantes.py

import requests
from bs4 import BeautifulSoup
from app.models import Worker, Person
import logging
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Configuración del logger
logger = logging.getLogger(__name__)

# Mantener la sesión abierta
s = requests.session()

def get_session():
    headers = {'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N)'}
    try:
        response = requests.get("https://amigro.org/my-profile/", headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        data = soup.find("input", {"id": "login_security"}).get("value")
        return data
    except requests.RequestException as e:
        logger.error(f"Error obteniendo sesión: {e}")
        return None

def consult(page, url):
    payload = (
        'lang=&search_keywords=&search_location=&filter_job_type%5B%5D=freelance&'
        'filter_job_type%5B%5D=full-time&filter_job_type%5B%5D=internship&'
        'filter_job_type%5B%5D=part-time&filter_job_type%5B%5D=temporary&'
        'per_page=6&orderby=title&order=DESC'
    )
    headers = {'Content-Type': 'application/x-www-form-urlencoded', 'user-agent': 'Mozilla/5.0'}
    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
        html = response.json()
        soup = BeautifulSoup(html["html"], "html.parser")
        vacantes = []

        for li in soup.find_all("li"):
            if "data-title" in str(li):
                vacantes.append({
                    "id": li.get("data-job_id"),
                    "title": li.get("data-title"),
                    "salary": li.get("data-salary"),
                    "job_type": li.get("data-job_type_class"),
                    "company": li.get("data-company"),
                    "location": {
                        "address": li.get("data-address"),
                        "longitude": li.get("data-longitude"),
                        "latitude": li.get("data-latitude"),
                    },
                    "agenda": {
                        "slot 1": li.get("job_booking_1"),
                        "slot 2": li.get("job_booking_2"),
                        "slot 3": li.get("job_booking_3"),
                        "slot 4": li.get("job_booking_4"),
                        "slot 5": li.get("job_booking_5"),

                    } 
                })
        return vacantes
    except requests.RequestException as e:
        logger.error(f"Error consultando vacantes: {e}")
        return []

def register(username, email, password, name, lastname):
    data_session = get_session()
    if not data_session:
        return "Error obteniendo la sesión para registro."

    url = "https://amigro.org/wp-admin/admin-ajax.php"
    payload = (
        f'action=workscoutajaxregister&role=candidate&username={username}&email={email}'
        f'&password={password}&first-name={name}&last-name={lastname}&privacy_policy=on'
        f'&register_security={data_session}'
    )
    headers = {'Content-Type': 'application/x-www-form-urlencoded', 'user-agent': 'Mozilla/5.0'}
    try:
        response = s.post(url, headers=headers, data=payload)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logger.error(f"Error registrando usuario: {e}")
        return None

def login(username, password):
    data_session = get_session()
    if not data_session:
        return "Error obteniendo la sesión para login."

    url = "https://amigro.org/wp-login.php"
    payload = f'_wp_http_referer=%2Fmy-profile%2F&log={username}&pwd={password}&login_security={data_session}'
    headers = {'Content-Type': 'application/x-www-form-urlencoded', 'user-agent': 'Mozilla/5.0'}
    try:
        response = s.post(url, headers=headers, data=payload)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        return soup.find('div', {'class': 'user-avatar-title'})
    except requests.RequestException as e:
        logger.error(f"Error iniciando sesión: {e}")
        return None

def solicitud(vacante_url, name, email, message, job_id):
    payload = f'candidate_email={email}&application_message={message}&job_id={job_id}&candidate_name={name}'
    headers = {'Content-Type': 'application/x-www-form-urlencoded', 'user-agent': 'Mozilla/5.0'}
    try:
        response = s.post(vacante_url, headers=headers, data=payload, allow_redirects=True)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        texto = soup.find("p", class_="job-manager-message").text
        return texto
    except requests.RequestException as e:
        logger.error(f"Error enviando solicitud: {e}")
        return None

# Coincidencia de trabajos con habilidades del candidato
def match_person_with_jobs(person):
    logger.info(f"Buscando coincidencias de trabajo para {person.name}")
    all_jobs = Worker.objects.all()
    user_skills = person.skills.lower().split(',') if person.skills else []
    user_skills_text = ' '.join(user_skills)

    job_descriptions = []
    job_list = []
    for job in all_jobs:
        job_skills = job.required_skills.lower().split(',') if job.required_skills else []
        job_descriptions.append(' '.join(job_skills))
        job_list.append(job)

    if not job_descriptions:
        return []

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(job_descriptions + [user_skills_text])
    cosine_similarities = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])
    similarity_scores = cosine_similarities[0]

    top_jobs = sorted(zip(job_list, similarity_scores), key=lambda x: x[1], reverse=True)
    return top_jobs[:5]  # Retorna las 5 mejores coincidencias

def get_available_slots(job):
    """
    Extrae los slots de entrevista disponibles de una vacante.
    """
    agenda = job.get("agenda", {})
    available_slots = [slot for slot in agenda.values() if slot]
    
    if available_slots:
        return available_slots
    else:
        logger.info(f"No hay slots disponibles para la vacante {job['title']}")
        return None

def book_interview_slot(job, slot_index, person):
    """
    Reserva un slot de entrevista para una persona en una vacante específica.
    
    Args:
        job (dict): Información de la vacante.
        slot_index (int): Índice del slot seleccionado.
        person (Person): Instancia de la persona que va a reservar el slot.

    Returns:
        bool: True si la reserva fue exitosa, False si no.
    """
    available_slots = get_available_slots(job)

    if available_slots and 0 <= slot_index < len(available_slots):
        selected_slot = available_slots[slot_index]

        # Aquí puedes agregar la lógica para registrar el slot en el sistema de gestión de entrevistas
        # Esto puede implicar enviar una solicitud a un sistema externo o registrar la información localmente.

        logger.info(f"Slot reservado para {person.name} en {selected_slot} para la vacante {job['title']}")
        return True
    else:
        logger.error(f"No se pudo reservar el slot para {person.name}. Slot no disponible o inválido.")
        return False



_____


# /home/amigro/app/views.py

import json
import logging
from django.core.cache import cache
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.template.response import TemplateResponse
from django.conf import settings
from .nlp_utils import analyze_text
from .gpt import gpt_message
from app.integrations.services import send_message as smg   
from .models import GptApi, SmtpConfig, Pregunta, FlowModel, ChatState, Condicion, Etapa, Person
import spacy

logging.basicConfig(filename="logger.log", level=logging.ERROR)

# Configuración de spaCy
nlp = spacy.load("es_core_news_sm")

# Vista para la página principal
def index(request):
    return render(request, "index.html")

# Función para crear preguntas
@csrf_exempt
def create_pregunta(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        pregunta = Pregunta.objects.create(name=data['name'])
        return JsonResponse({'id': pregunta.id})

# Función para actualizar preguntas
@csrf_exempt
def update_pregunta(request, id):
    if request.method == 'PUT':
        data = json.loads(request.body)
        pregunta = Pregunta.objects.get(id=id)
        pregunta.name = data['name']
        pregunta.save()
        return JsonResponse({'status': 'success'})

# Función para actualizar posiciones de preguntas
@csrf_exempt
def update_position(request, id):
    if request.method == 'PUT':
        data = json.loads(request.body)
        pregunta = Pregunta.objects.get(id=id)
        pregunta.position = data['position']  # Suponiendo que tienes un campo de posición
        pregunta.save()
        return JsonResponse({'status': 'success'})

# Función para eliminar preguntas
@csrf_exempt
def delete_pregunta(request, id):
    if request.method == 'DELETE':
        pregunta = Pregunta.objects.get(id=id)
        pregunta.delete()
        return JsonResponse({'status': 'deleted'})

# Función para imprimir pregunta y subpreguntas (recursiva)
def print_pregunta_y_subpreguntas(pregunta):
    print(f"Pregunta: {pregunta.name}")
    for sub_pregunta in pregunta.sub_preguntas.all():
        print(f"    SubPregunta: {sub_pregunta.name}")
        print_pregunta_y_subpreguntas(sub_pregunta)  # Recursividad para explorar más

# Cargar datos del flujo
def load_flow_data(request, flowmodel_id):
    """
    Carga los datos del flujo en formato JSON.
    """
    flow = get_object_or_404(FlowModel, pk=flowmodel_id)
    flow_data_json = flow.flow_data_json  # Carga los datos del flujo en formato JSON
    return JsonResponse({'flow_data': flow_data_json})

# Vista para editar el flujo del chatbot
def edit_flow(request, flowmodel_id):
    flow = get_object_or_404(FlowModel, pk=flowmodel_id)
    context = {
        'flow': flow,
        'questions_json': flow.flow_data_json or "[]"  # Asegúrate de pasar los datos en formato JSON o vacío
    }
    return TemplateResponse(request, "admin/chatbot_flow.html", context)

# Guardar la estructura del flujo
@csrf_exempt
def save_flow_structure(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        flowmodel_id = data.get('flowmodel_id')
        flow = get_object_or_404(FlowModel, pk=flowmodel_id)
        flow.flow_data_json = json.dumps(data.get('nodes'))  # Guardar la estructura del flujo en formato JSON
        flow.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

# Exportar el flujo del chatbot
@csrf_exempt
def export_chatbot_flow(request):
    if request.method == 'POST':
        flow_data = json.loads(request.body)
        return JsonResponse({'status': 'exported', 'data': flow_data})
    return JsonResponse({'status': 'error'}, status=400)

# Función para cargar preguntas y subpreguntas asociadas al flujo
def load_flow_questions_data(request, flowmodel_id):
    flow = FlowModel.objects.prefetch_related('preguntas__sub_preguntas').get(pk=flowmodel_id)
    
    flow_structure = {
        'flow_data': flow.flow_data_json,  # JSON del flujo
        'preguntas': [
            {
                'id': pregunta.id,
                'name': pregunta.name,
                'sub_preguntas': [
                    {'id': sub_pregunta.id, 'name': sub_pregunta.name}
                    for sub_pregunta in pregunta.sub_preguntas.all()
                ]
            }
            for pregunta in flow.preguntas.all()
        ]
    }

    return JsonResponse(flow_structure)

# Función para recibir mensajes del chatbot
@csrf_exempt
def recv_message(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            message = data.get('message')
            platform = data.get('platform')
            use_gpt = data.get('use_gpt')

            analysis = analyze_text(message)
            response = process_spacy_analysis(analysis, message)

            if not response and use_gpt == 'yes':
                try:
                    gpt_api = GptApi.objects.first()
                    gpt_response = gpt_message(api_token=gpt_api.api_token, text=message, model=gpt_api.model)
                    response = gpt_response['choices'][0]['message']['content']
                except Exception as e:
                    logging.error(f"Error llamando a GPT: {e}")
                    response = "Lo siento, ocurrió un error al procesar tu solicitud."

            if platform == 'telegram':
                send_telegram_message(data['username'], response)
            elif platform == 'whatsapp':
                send_whatsapp_message(data['username'], response)
            elif platform == 'messenger':
                send_messenger_message(data['username'], response)

            return JsonResponse({'status': 'success', 'response': response})
        except json.JSONDecodeError:
            logger.error("Error decodificando JSON")
            return JsonResponse({'status': 'error', 'message': 'JSON inválido'}, status=400)
        except Exception as e:
            logger.error(f"Error inesperado: {e}")
            return JsonResponse({'status': 'error', 'message': 'Error interno del servidor'}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

# Enviar mensaje de prueba
@csrf_exempt
def send_test_message(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            platform = data.get('platform')
            message = data.get('message')

            if platform == 'whatsapp':
                # Lógica para WhatsApp
                pass
            elif platform == 'telegram':
                # Lógica para Telegram
                pass
            elif platform == 'messenger':
                # Lógica para Messenger
                pass

            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    else:
        return JsonResponse({'error': 'Método no permitido'}, status=405)

# Función para enviar mensajes
@csrf_exempt
def send_message(request):
    """
    Envía un mensaje a través de una plataforma específica.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message = data.get('message')
            platform = data.get('platform')

            # Lógica de envío de mensajes basada en la plataforma
            if platform == 'whatsapp':
                # Envía un mensaje por WhatsApp (lógica necesaria)
                response = f"Mensaje enviado a WhatsApp: {message}"
            elif platform == 'telegram':
                # Envía un mensaje por Telegram (lógica necesaria)
                response = f"Mensaje enviado a Telegram: {message}"
            elif platform == 'messenger':
                # Envía un mensaje por Messenger (lógica necesaria)
                response = f"Mensaje enviado a Messenger: {message}"
            elif platform == 'instagram':
                # Envía un mensaje por Instagram (lógica necesaria)
                response = f"Mensaje enviado a Instagram: {message}"
            else:
                return JsonResponse({'error': 'Plataforma no soportada.'}, status=400)

            return JsonResponse({'status': 'success', 'response': response})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)


____


FIN DEL ENVIO DE ARCHIVOS# Grupo-huntRED-Chatbot
