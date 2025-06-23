"""
AURA - Public API
API pública/documentada para terceros con autenticación, rate limiting y hooks de seguridad.
"""

import logging
import hashlib
import time
import json
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from functools import wraps
from dataclasses import dataclass, asdict
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

logger = logging.getLogger(__name__)

# Configuración del API
ENABLED = False
RATE_LIMIT_PER_MINUTE = 100
API_VERSION = "v1.0"

@dataclass
class APIEndpoint:
    """Estructura para definir endpoints del API"""
    path: str
    method: str
    description: str
    requires_auth: bool
    rate_limit: int
    parameters: Dict[str, Any]
    response_schema: Dict[str, Any]

@dataclass
class APIKey:
    """Estructura para manejar claves de API"""
    key: str
    user_id: str
    permissions: List[str]
    created_at: datetime
    last_used: Optional[datetime] = None
    is_active: bool = True

class RateLimiter:
    """Sistema de rate limiting por API key"""
    
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, api_key: str, limit: int) -> bool:
        """Verifica si la request está dentro del límite"""
        now = time.time()
        minute_ago = now - 60
        
        if api_key not in self.requests:
            self.requests[api_key] = []
        
        # Limpiar requests antiguas
        self.requests[api_key] = [req_time for req_time in self.requests[api_key] if req_time > minute_ago]
        
        if len(self.requests[api_key]) >= limit:
            return False
        
        self.requests[api_key].append(now)
        return True

class PublicAPI:
    """
    API pública avanzada para terceros:
    - Autenticación con API keys
    - Rate limiting configurable
    - Endpoints documentados
    - Hooks de seguridad y logging
    - Validación de parámetros
    """
    
    def __init__(self):
        self.enabled = ENABLED
        self.api_keys = {}
        self.rate_limiter = RateLimiter()
        self.endpoints = {}
        self.hooks = {
            'pre_request': [],
            'post_request': [],
            'error_handler': []
        }
        
        # Registrar endpoints por defecto
        self._register_default_endpoints()
    
    def _register_default_endpoints(self):
        """Registra los endpoints por defecto del API"""
        
        # Endpoint de información del API
        self.register_endpoint(
            APIEndpoint(
                path="/api/v1/info",
                method="GET",
                description="Información general del API AURA",
                requires_auth=False,
                rate_limit=10,
                parameters={},
                response_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "version": {"type": "string"},
                        "status": {"type": "string"},
                        "endpoints": {"type": "array"}
                    }
                }
            )
        )
        
        # Endpoint de autenticación
        self.register_endpoint(
            APIEndpoint(
                path="/api/v1/auth",
                method="POST",
                description="Autenticar y obtener API key",
                requires_auth=False,
                rate_limit=5,
                parameters={
                    "username": {"type": "string", "required": True},
                    "password": {"type": "string", "required": True}
                },
                response_schema={
                    "type": "object",
                    "properties": {
                        "api_key": {"type": "string"},
                        "expires_at": {"type": "string"},
                        "permissions": {"type": "array"}
                    }
                }
            )
        )
        
        # Endpoint de análisis de compatibilidad
        self.register_endpoint(
            APIEndpoint(
                path="/api/v1/compatibility/analyze",
                method="POST",
                description="Analizar compatibilidad entre perfiles",
                requires_auth=True,
                rate_limit=20,
                parameters={
                    "profile1": {"type": "object", "required": True},
                    "profile2": {"type": "object", "required": True},
                    "analysis_type": {"type": "string", "default": "holistic"}
                },
                response_schema={
                    "type": "object",
                    "properties": {
                        "compatibility_score": {"type": "number"},
                        "analysis_details": {"type": "object"},
                        "recommendations": {"type": "array"}
                    }
                }
            )
        )
        
        # Endpoint de recomendaciones
        self.register_endpoint(
            APIEndpoint(
                path="/api/v1/recommendations",
                method="GET",
                description="Obtener recomendaciones personalizadas",
                requires_auth=True,
                rate_limit=30,
                parameters={
                    "user_id": {"type": "string", "required": True},
                    "type": {"type": "string", "default": "all"},
                    "limit": {"type": "integer", "default": 10}
                },
                response_schema={
                    "type": "object",
                    "properties": {
                        "recommendations": {"type": "array"},
                        "total_count": {"type": "integer"},
                        "next_page": {"type": "string"}
                    }
                }
            )
        )
        
        # Endpoint de análisis de skills
        self.register_endpoint(
            APIEndpoint(
                path="/api/v1/skills/analyze",
                method="POST",
                description="Analizar gap de skills y generar recomendaciones",
                requires_auth=True,
                rate_limit=15,
                parameters={
                    "user_profile": {"type": "object", "required": True},
                    "target_role": {"type": "string", "required": True},
                    "include_market_data": {"type": "boolean", "default": True}
                },
                response_schema={
                    "type": "object",
                    "properties": {
                        "skill_gaps": {"type": "array"},
                        "recommended_skills": {"type": "array"},
                        "learning_path": {"type": "object"},
                        "market_insights": {"type": "object"}
                    }
                }
            )
        )
        
        # Endpoint de networking
        self.register_endpoint(
            APIEndpoint(
                path="/api/v1/networking/matches",
                method="GET",
                description="Obtener matches de networking",
                requires_auth=True,
                rate_limit=25,
                parameters={
                    "user_id": {"type": "string", "required": True},
                    "match_type": {"type": "string", "default": "all"},
                    "limit": {"type": "integer", "default": 20}
                },
                response_schema={
                    "type": "object",
                    "properties": {
                        "matches": {"type": "array"},
                        "match_scores": {"type": "object"},
                        "next_actions": {"type": "array"}
                    }
                }
            )
        )
    
    def register_endpoint(self, endpoint: APIEndpoint):
        """Registra un nuevo endpoint en el API"""
        key = f"{endpoint.method}:{endpoint.path}"
        self.endpoints[key] = endpoint
        logger.info(f"PublicAPI: endpoint registrado {endpoint.method} {endpoint.path}")
    
    def generate_api_key(self, user_id: str, permissions: List[str] = None) -> str:
        """Genera una nueva API key para un usuario"""
        if permissions is None:
            permissions = ["read"]
        
        # Generar key única
        timestamp = str(int(time.time()))
        key_data = f"{user_id}:{timestamp}:{','.join(permissions)}"
        api_key = hashlib.sha256(key_data.encode()).hexdigest()[:32]
        
        # Registrar la key
        self.api_keys[api_key] = APIKey(
            key=api_key,
            user_id=user_id,
            permissions=permissions,
            created_at=datetime.now()
        )
        
        logger.info(f"PublicAPI: API key generada para usuario {user_id}")
        return api_key
    
    def validate_api_key(self, api_key: str) -> Optional[APIKey]:
        """Valida una API key y retorna la información asociada"""
        if api_key not in self.api_keys:
            return None
        
        key_info = self.api_keys[api_key]
        if not key_info.is_active:
            return None
        
        # Actualizar último uso
        key_info.last_used = datetime.now()
        return key_info
    
    def check_permissions(self, api_key: str, required_permissions: List[str]) -> bool:
        """Verifica si una API key tiene los permisos requeridos"""
        key_info = self.validate_api_key(api_key)
        if not key_info:
            return False
        
        return all(perm in key_info.permissions for perm in required_permissions)
    
    def add_hook(self, hook_type: str, callback: Callable):
        """Agrega un hook personalizado"""
        if hook_type in self.hooks:
            self.hooks[hook_type].append(callback)
            logger.info(f"PublicAPI: hook {hook_type} agregado")
    
    def _execute_hooks(self, hook_type: str, data: Dict[str, Any]):
        """Ejecuta los hooks de un tipo específico"""
        for hook in self.hooks.get(hook_type, []):
            try:
                hook(data)
            except Exception as e:
                logger.error(f"PublicAPI: error en hook {hook_type}: {e}")
    
    def handle_request(self, method: str, path: str, headers: Dict[str, str], 
                      body: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Maneja una request HTTP al API público
        """
        if not self.enabled:
            return {"error": "API público deshabilitado", "status": 503}
        
        # Ejecutar hooks pre-request
        request_data = {
            "method": method,
            "path": path,
            "headers": headers,
            "body": body,
            "timestamp": datetime.now()
        }
        self._execute_hooks('pre_request', request_data)
        
        try:
            # Buscar endpoint
            endpoint_key = f"{method}:{path}"
            endpoint = self.endpoints.get(endpoint_key)
            
            if not endpoint:
                return {"error": "Endpoint no encontrado", "status": 404}
            
            # Verificar autenticación
            api_key = headers.get('X-API-Key')
            if endpoint.requires_auth:
                if not api_key:
                    return {"error": "API key requerida", "status": 401}
                
                key_info = self.validate_api_key(api_key)
                if not key_info:
                    return {"error": "API key inválida", "status": 401}
            
            # Verificar rate limiting
            if api_key and not self.rate_limiter.is_allowed(api_key, endpoint.rate_limit):
                return {"error": "Rate limit excedido", "status": 429}
            
            # Validar parámetros
            if body:
                validation_result = self._validate_parameters(body, endpoint.parameters)
                if not validation_result["valid"]:
                    return {"error": f"Parámetros inválidos: {validation_result['errors']}", "status": 400}
            
            # Procesar request
            response = self._process_endpoint(endpoint, body or {}, api_key)
            
            # Ejecutar hooks post-request
            response_data = {
                "method": method,
                "path": path,
                "response": response,
                "timestamp": datetime.now()
            }
            self._execute_hooks('post_request', response_data)
            
            return response
            
        except Exception as e:
            logger.error(f"PublicAPI: error procesando request: {e}")
            
            # Ejecutar hooks de error
            error_data = {
                "method": method,
                "path": path,
                "error": str(e),
                "timestamp": datetime.now()
            }
            self._execute_hooks('error_handler', error_data)
            
            return {"error": "Error interno del servidor", "status": 500}
    
    def _validate_parameters(self, body: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Valida los parámetros de entrada según el schema"""
        errors = []
        
        for param_name, param_schema in schema.items():
            if param_schema.get("required", False) and param_name not in body:
                errors.append(f"Parámetro requerido faltante: {param_name}")
            elif param_name in body:
                # Validación básica de tipos
                expected_type = param_schema.get("type")
                if expected_type == "string" and not isinstance(body[param_name], str):
                    errors.append(f"Parámetro {param_name} debe ser string")
                elif expected_type == "integer" and not isinstance(body[param_name], int):
                    errors.append(f"Parámetro {param_name} debe ser integer")
                elif expected_type == "boolean" and not isinstance(body[param_name], bool):
                    errors.append(f"Parámetro {param_name} debe ser boolean")
        
        return {"valid": len(errors) == 0, "errors": errors}
    
    def _process_endpoint(self, endpoint: APIEndpoint, body: Dict[str, Any], api_key: str = None) -> Dict[str, Any]:
        """Procesa un endpoint específico"""
        
        if endpoint.path == "/api/v1/info":
            return {
                "name": "AURA Public API",
                "version": API_VERSION,
                "status": "active",
                "endpoints": [f"{ep.method} {ep.path}" for ep in self.endpoints.values()],
                "status_code": 200
            }
        
        elif endpoint.path == "/api/v1/auth":
            # Simulación de autenticación
            username = body.get("username")
            password = body.get("password")
            
            if username and password:
                # En producción, validar contra base de datos
                api_key = self.generate_api_key(username, ["read", "write"])
                return {
                    "api_key": api_key,
                    "expires_at": (datetime.now() + timedelta(days=30)).isoformat(),
                    "permissions": ["read", "write"],
                    "status_code": 200
                }
            else:
                return {"error": "Credenciales inválidas", "status_code": 401}
        
        elif endpoint.path == "/api/v1/compatibility/analyze":
            # Simulación de análisis de compatibilidad
            profile1 = body.get("profile1", {})
            profile2 = body.get("profile2", {})
            
            return {
                "compatibility_score": 0.85,
                "analysis_details": {
                    "energy_match": 0.9,
                    "vibrational_alignment": 0.8,
                    "skill_complementarity": 0.85
                },
                "recommendations": [
                    "Excelente compatibilidad energética",
                    "Considerar colaboración en proyectos",
                    "Potencial sinergia en networking"
                ],
                "status_code": 200
            }
        
        elif endpoint.path == "/api/v1/recommendations":
            # Simulación de recomendaciones
            user_id = body.get("user_id")
            rec_type = body.get("type", "all")
            limit = body.get("limit", 10)
            
            return {
                "recommendations": [
                    {"type": "skill", "title": "Machine Learning", "priority": "high"},
                    {"type": "connection", "title": "Juan Pérez", "reason": "Experto en IA"},
                    {"type": "event", "title": "Tech Conference 2024", "date": "2024-06-15"}
                ],
                "total_count": 15,
                "next_page": f"/api/v1/recommendations?page=2&user_id={user_id}",
                "status_code": 200
            }
        
        elif endpoint.path == "/api/v1/skills/analyze":
            # Simulación de análisis de skills
            user_profile = body.get("user_profile", {})
            target_role = body.get("target_role", "")
            
            return {
                "skill_gaps": [
                    {"skill": "Python", "current_level": "intermediate", "required_level": "advanced"},
                    {"skill": "Docker", "current_level": "basic", "required_level": "intermediate"}
                ],
                "recommended_skills": ["Python", "Docker", "Kubernetes"],
                "learning_path": {
                    "estimated_time": "3 months",
                    "courses": ["Python Advanced", "Docker Fundamentals"],
                    "resources": ["Documentation", "Online courses"]
                },
                "market_insights": {
                    "demand": "high",
                    "salary_range": "$80k-$120k",
                    "growth_rate": "15%"
                },
                "status_code": 200
            }
        
        elif endpoint.path == "/api/v1/networking/matches":
            # Simulación de matches de networking
            user_id = body.get("user_id")
            match_type = body.get("match_type", "all")
            
            return {
                "matches": [
                    {"id": "1", "name": "María García", "match_score": 0.92, "reason": "Experiencia similar"},
                    {"id": "2", "name": "Carlos López", "match_score": 0.88, "reason": "Intereses comunes"}
                ],
                "match_scores": {"1": 0.92, "2": 0.88},
                "next_actions": [
                    "Enviar mensaje de introducción",
                    "Programar coffee chat",
                    "Compartir recursos"
                ],
                "status_code": 200
            }
        
        return {"error": "Endpoint no implementado", "status_code": 501}
    
    def get_endpoints(self) -> List[Dict[str, Any]]:
        """Retorna la lista de endpoints disponibles"""
        return [
            {
                "path": endpoint.path,
                "method": endpoint.method,
                "description": endpoint.description,
                "requires_auth": endpoint.requires_auth,
                "rate_limit": endpoint.rate_limit,
                "parameters": endpoint.parameters
            }
            for endpoint in self.endpoints.values()
        ]
    
    def get_api_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del API"""
        return {
            "total_endpoints": len(self.endpoints),
            "active_api_keys": len([k for k in self.api_keys.values() if k.is_active]),
            "total_requests": sum(len(requests) for requests in self.rate_limiter.requests.values()),
            "enabled": self.enabled,
            "version": API_VERSION
        }

# Instancia global del API público
public_api = PublicAPI()

# Ejemplo de uso:
# api_key = public_api.generate_api_key("user123", ["read", "write"])
# response = public_api.handle_request("GET", "/api/v1/info", {"X-API-Key": api_key})
# print(response)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def send_proposal(request):
    try:
        data = json.loads(request.body)
        email = data['email']
        proposal = data['proposal']
        pdf_base64 = data.get('pdf_base64')
        client_logo = data.get('client_logo')
        # Send email to user with CC to hola@huntred.com
        from app.chatbot.integrations.services import send_email
        send_email(
            business_unit_name=proposal.get('business_unit', 'huntRED'),
            subject='Tu Cotización huntRED®',
            to_email=email,
            body=f"Adjunto encontrarás tu cotización.\n\n{json.dumps(proposal, indent=2)}",
            from_email='no-reply@huntred.com',
            cc=['hola@huntred.com'],
            attachment=pdf_base64,
            client_logo=client_logo
        )
        return JsonResponse({'status': 'success', 'message': 'Cotización enviada correctamente.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def track_share(request):
    try:
        data = json.loads(request.body)
        email = data['email']
        proposal = data['proposal']
        platform = data['platform']
        from app.chatbot.integrations.services import send_email
        send_email(
            business_unit_name=proposal.get('business_unit', 'huntRED'),
            subject=f'Cotización Compartida vía {platform}',
            to_email='hola@huntred.com',
            body=f"Usuario: {email}\nPlataforma: {platform}\nCotización:\n{json.dumps(proposal, indent=2)}",
            from_email='no-reply@huntred.com'
        )
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def track_event(request):
    try:
        data = json.loads(request.body)
        from app.chatbot.integrations.services import send_email
        send_email(
            business_unit_name=data.get('business_unit', 'huntRED'),
            subject=f'Evento: {data["event"]}',
            to_email='hola@huntred.com',
            body=f"Usuario: {data.get('email', 'Anónimo')}\nEvento: {data['event']}\nDetalles:\n{json.dumps(data.get('proposal', {}), indent=2)}",
            from_email='no-reply@huntred.com'
        )
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
