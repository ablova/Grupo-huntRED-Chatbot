"""
HuntRED® v2 - Proposals & Pricing Service
Complete proposal generation and pricing management system
"""

import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import json
import logging
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

logger = logging.getLogger(__name__)

class ProposalStatus(Enum):
    DRAFT = "draft"
    PENDING = "pending"
    SENT = "sent"
    VIEWED = "viewed"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

class PricingTier(Enum):
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"

class ProposalType(Enum):
    HR_SERVICES = "hr_services"
    PAYROLL_OUTSOURCING = "payroll_outsourcing"
    RECRUITMENT = "recruitment"
    CONSULTING = "consulting"
    TRAINING = "training"
    FULL_SUITE = "full_suite"

class ProposalsService:
    """Complete proposals and pricing management"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Pricing catalog
        self.pricing_catalog = {
            PricingTier.BASIC: {
                "name": "Plan Básico",
                "description": "Gestión básica de RRHH",
                "monthly_price": Decimal("2500.00"),
                "features": [
                    "Gestión de empleados hasta 50",
                    "Nómina básica",
                    "Reportes estándar",
                    "Soporte por email"
                ],
                "limitations": {
                    "max_employees": 50,
                    "payroll_runs": 12,
                    "reports": "basic",
                    "support": "email"
                }
            },
            PricingTier.PROFESSIONAL: {
                "name": "Plan Profesional",
                "description": "Solución completa para empresas medianas",
                "monthly_price": Decimal("7500.00"),
                "features": [
                    "Gestión de empleados hasta 200",
                    "Nómina avanzada con compliance México",
                    "Reportes avanzados y analytics",
                    "Sistema de asistencia",
                    "Bot WhatsApp",
                    "Soporte telefónico"
                ],
                "limitations": {
                    "max_employees": 200,
                    "payroll_runs": "unlimited",
                    "reports": "advanced",
                    "support": "phone_email"
                }
            },
            PricingTier.ENTERPRISE: {
                "name": "Plan Empresarial",
                "description": "Solución empresarial completa",
                "monthly_price": Decimal("15000.00"),
                "features": [
                    "Empleados ilimitados",
                    "Nómina multi-país",
                    "BI y analytics avanzados",
                    "Integraciones personalizadas",
                    "ML y predicciones",
                    "Soporte 24/7",
                    "Account manager dedicado"
                ],
                "limitations": {
                    "max_employees": "unlimited",
                    "payroll_runs": "unlimited",
                    "reports": "enterprise",
                    "support": "24_7_dedicated"
                }
            }
        }
        
        # Service modules pricing
        self.service_modules = {
            "payroll_outsourcing": {
                "name": "Outsourcing de Nómina",
                "price_per_employee": Decimal("120.00"),
                "minimum_fee": Decimal("5000.00"),
                "description": "Procesamiento completo de nómina"
            },
            "recruitment": {
                "name": "Reclutamiento Especializado",
                "price_percentage": Decimal("0.20"),  # 20% of annual salary
                "minimum_fee": Decimal("15000.00"),
                "description": "Búsqueda y selección de talento"
            },
            "hr_consulting": {
                "name": "Consultoría en RRHH",
                "hourly_rate": Decimal("1500.00"),
                "daily_rate": Decimal("8000.00"),
                "description": "Consultoría especializada"
            },
            "training": {
                "name": "Capacitación y Desarrollo",
                "price_per_participant": Decimal("2500.00"),
                "minimum_participants": 5,
                "description": "Programas de capacitación"
            }
        }
    
    async def create_proposal(self, proposal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new proposal"""
        try:
            proposal_id = str(uuid.uuid4())
            
            # Extract proposal information
            client_info = proposal_data.get("client_info", {})
            requirements = proposal_data.get("requirements", {})
            proposal_type = ProposalType(proposal_data.get("type", "hr_services"))
            
            # Calculate pricing
            pricing = await self._calculate_pricing(requirements, proposal_type)
            
            # Generate proposal content
            content = await self._generate_proposal_content(
                client_info, requirements, pricing, proposal_type
            )
            
            # Create proposal record
            proposal = {
                "id": proposal_id,
                "client_info": client_info,
                "requirements": requirements,
                "type": proposal_type.value,
                "pricing": pricing,
                "content": content,
                "status": ProposalStatus.DRAFT.value,
                "created_at": datetime.now(),
                "expires_at": datetime.now() + timedelta(days=30),
                "version": 1,
                "metadata": {
                    "created_by": proposal_data.get("created_by"),
                    "sales_rep": proposal_data.get("sales_rep"),
                    "lead_source": proposal_data.get("lead_source")
                }
            }
            
            # Save to database (mock implementation)
            # In real implementation, save to database
            
            logger.info(f"Proposal {proposal_id} created successfully")
            
            return {
                "success": True,
                "proposal_id": proposal_id,
                "proposal": proposal,
                "next_steps": [
                    "Review proposal content",
                    "Add custom terms if needed",
                    "Send to client for approval"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error creating proposal: {e}")
            return {"success": False, "error": str(e)}
    
    async def _calculate_pricing(self, requirements: Dict[str, Any], 
                                proposal_type: ProposalType) -> Dict[str, Any]:
        """Calculate pricing based on requirements"""
        
        employee_count = requirements.get("employee_count", 0)
        services_needed = requirements.get("services", [])
        contract_duration = requirements.get("contract_duration_months", 12)
        
        pricing = {
            "base_pricing": {},
            "additional_services": {},
            "discounts": {},
            "total_monthly": Decimal("0.00"),
            "total_annual": Decimal("0.00"),
            "implementation_fee": Decimal("0.00")
        }
        
        # Determine base tier
        if employee_count <= 50:
            base_tier = PricingTier.BASIC
        elif employee_count <= 200:
            base_tier = PricingTier.PROFESSIONAL
        else:
            base_tier = PricingTier.ENTERPRISE
        
        # Base pricing
        base_plan = self.pricing_catalog[base_tier]
        pricing["base_pricing"] = {
            "tier": base_tier.value,
            "monthly_price": base_plan["monthly_price"],
            "features": base_plan["features"]
        }
        
        total_monthly = base_plan["monthly_price"]
        
        # Additional services
        for service in services_needed:
            if service in self.service_modules:
                service_config = self.service_modules[service]
                service_cost = self._calculate_service_cost(service_config, requirements)
                
                pricing["additional_services"][service] = {
                    "name": service_config["name"],
                    "cost": service_cost,
                    "description": service_config["description"]
                }
                
                total_monthly += service_cost
        
        # Volume discounts
        if employee_count > 100:
            volume_discount = total_monthly * Decimal("0.10")  # 10% discount
            pricing["discounts"]["volume_discount"] = {
                "percentage": 10,
                "amount": volume_discount,
                "reason": "Volume discount for 100+ employees"
            }
            total_monthly -= volume_discount
        
        # Contract duration discount
        if contract_duration >= 24:
            duration_discount = total_monthly * Decimal("0.15")  # 15% discount
            pricing["discounts"]["duration_discount"] = {
                "percentage": 15,
                "amount": duration_discount,
                "reason": "Long-term contract discount (24+ months)"
            }
            total_monthly -= duration_discount
        elif contract_duration >= 12:
            duration_discount = total_monthly * Decimal("0.05")  # 5% discount
            pricing["discounts"]["duration_discount"] = {
                "percentage": 5,
                "amount": duration_discount,
                "reason": "Annual contract discount"
            }
            total_monthly -= duration_discount
        
        # Implementation fee
        implementation_fee = total_monthly * Decimal("0.5")  # 50% of monthly fee
        pricing["implementation_fee"] = implementation_fee
        
        # Final totals
        pricing["total_monthly"] = total_monthly
        pricing["total_annual"] = total_monthly * 12
        
        return pricing
    
    def _calculate_service_cost(self, service_config: Dict[str, Any], 
                               requirements: Dict[str, Any]) -> Decimal:
        """Calculate cost for additional service"""
        
        employee_count = requirements.get("employee_count", 0)
        
        if "price_per_employee" in service_config:
            cost = service_config["price_per_employee"] * employee_count
            return max(cost, service_config.get("minimum_fee", Decimal("0.00")))
        
        elif "hourly_rate" in service_config:
            estimated_hours = requirements.get("estimated_hours", 40)
            return service_config["hourly_rate"] * estimated_hours
        
        elif "price_per_participant" in service_config:
            participants = requirements.get("training_participants", 10)
            return service_config["price_per_participant"] * participants
        
        elif "price_percentage" in service_config:
            annual_salary = requirements.get("avg_annual_salary", Decimal("500000.00"))
            positions = requirements.get("positions_to_fill", 1)
            cost = annual_salary * service_config["price_percentage"] * positions
            return max(cost, service_config.get("minimum_fee", Decimal("0.00")))
        
        return Decimal("0.00")
    
    async def _generate_proposal_content(self, client_info: Dict[str, Any],
                                       requirements: Dict[str, Any],
                                       pricing: Dict[str, Any],
                                       proposal_type: ProposalType) -> Dict[str, Any]:
        """Generate comprehensive proposal content"""
        
        company_name = client_info.get("company_name", "Estimado Cliente")
        contact_name = client_info.get("contact_name", "")
        
        content = {
            "executive_summary": f"""
Propuesta de Servicios de Recursos Humanos para {company_name}

Estimado/a {contact_name},

En HuntRED® nos complace presentar esta propuesta personalizada para optimizar 
la gestión de recursos humanos de {company_name}. Nuestra solución integral 
está diseñada para empresas como la suya, que buscan eficiencia, compliance 
y crecimiento sostenible.

Con más de 10 años de experiencia en el mercado mexicano, ofrecemos tecnología 
de vanguardia combinada con expertise local para garantizar el éxito de su 
operación de RRHH.
            """,
            
            "company_analysis": self._generate_company_analysis(client_info, requirements),
            "solution_overview": self._generate_solution_overview(pricing, proposal_type),
            "implementation_plan": self._generate_implementation_plan(requirements),
            "pricing_details": pricing,
            "terms_and_conditions": self._generate_terms_and_conditions(),
            "next_steps": self._generate_next_steps(),
            "appendices": {
                "company_credentials": self._generate_company_credentials(),
                "case_studies": self._generate_case_studies(),
                "technical_specifications": self._generate_tech_specs()
            }
        }
        
        return content
    
    def _generate_company_analysis(self, client_info: Dict[str, Any], 
                                 requirements: Dict[str, Any]) -> str:
        """Generate company analysis section"""
        
        employee_count = requirements.get("employee_count", 0)
        industry = client_info.get("industry", "")
        current_challenges = requirements.get("current_challenges", [])
        
        analysis = f"""
ANÁLISIS DE NECESIDADES - {client_info.get("company_name", "")}

Perfil de la Empresa:
• Industria: {industry}
• Número de empleados: {employee_count}
• Ubicación: {client_info.get("location", "")}

Desafíos Identificados:
"""
        
        for challenge in current_challenges:
            analysis += f"• {challenge}\n"
        
        analysis += f"""

Oportunidades de Mejora:
• Automatización de procesos de nómina
• Implementación de sistema de asistencia digital
• Reportes y analytics avanzados
• Compliance automático con regulaciones mexicanas
• Mejora en la experiencia del empleado
"""
        
        return analysis
    
    def _generate_solution_overview(self, pricing: Dict[str, Any], 
                                  proposal_type: ProposalType) -> str:
        """Generate solution overview"""
        
        base_tier = pricing["base_pricing"]["tier"]
        features = pricing["base_pricing"]["features"]
        
        overview = f"""
SOLUCIÓN PROPUESTA - PLAN {base_tier.upper()}

Características Principales:
"""
        
        for feature in features:
            overview += f"• {feature}\n"
        
        if pricing["additional_services"]:
            overview += "\nServicios Adicionales:\n"
            for service_name, service_data in pricing["additional_services"].items():
                overview += f"• {service_data['name']}: {service_data['description']}\n"
        
        overview += f"""

Beneficios Clave:
• Reducción del 60% en tiempo de procesamiento de nómina
• 100% compliance con regulaciones mexicanas (IMSS, ISR, INFONAVIT)
• Acceso 24/7 a información de empleados
• Reportes ejecutivos en tiempo real
• Soporte especializado en español
• Implementación en menos de 30 días
"""
        
        return overview
    
    def _generate_implementation_plan(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Generate implementation timeline"""
        
        return {
            "timeline": "30 días",
            "phases": [
                {
                    "phase": "Fase 1: Preparación",
                    "duration": "Días 1-7",
                    "activities": [
                        "Kick-off meeting y definición de alcance",
                        "Recopilación de datos de empleados existentes",
                        "Configuración inicial del sistema",
                        "Creación de cuentas de usuario"
                    ]
                },
                {
                    "phase": "Fase 2: Migración de Datos",
                    "duration": "Días 8-14",
                    "activities": [
                        "Migración de base de datos de empleados",
                        "Configuración de estructura organizacional",
                        "Setup de políticas de nómina",
                        "Integración con sistemas existentes"
                    ]
                },
                {
                    "phase": "Fase 3: Capacitación",
                    "duration": "Días 15-21",
                    "activities": [
                        "Capacitación a administradores",
                        "Entrenamiento a usuarios finales",
                        "Documentación personalizada",
                        "Pruebas de usuario"
                    ]
                },
                {
                    "phase": "Fase 4: Go-Live",
                    "duration": "Días 22-30",
                    "activities": [
                        "Puesta en producción",
                        "Monitoreo intensivo",
                        "Soporte en vivo",
                        "Ajustes finales"
                    ]
                }
            ],
            "deliverables": [
                "Sistema completamente configurado",
                "Datos migrados y validados",
                "Usuarios capacitados",
                "Documentación completa",
                "Soporte post go-live"
            ]
        }
    
    def _generate_terms_and_conditions(self) -> Dict[str, Any]:
        """Generate terms and conditions"""
        
        return {
            "payment_terms": {
                "implementation_fee": "50% al firmar contrato, 50% al go-live",
                "monthly_fees": "Pago mensual por adelantado",
                "accepted_methods": ["Transferencia bancaria", "Cheque"]
            },
            "contract_terms": {
                "minimum_duration": "12 meses",
                "renewal": "Automática por períodos anuales",
                "termination": "Aviso de 60 días"
            },
            "service_level": {
                "uptime": "99.9% garantizado",
                "support_hours": "Lunes a Viernes 8:00-18:00 CST",
                "response_time": "< 4 horas para issues críticos"
            },
            "data_security": {
                "encryption": "AES-256 en tránsito y reposo",
                "backups": "Diarios con retención de 30 días",
                "compliance": "SOC 2 Type II, ISO 27001"
            }
        }
    
    def _generate_next_steps(self) -> List[str]:
        """Generate next steps"""
        
        return [
            "Revisión de propuesta por parte del cliente (5 días hábiles)",
            "Reunión de clarificaciones si es necesario",
            "Firma de contrato y orden de compra",
            "Pago de implementation fee",
            "Inicio de proyecto según timeline establecido"
        ]
    
    def _generate_company_credentials(self) -> Dict[str, Any]:
        """Generate company credentials"""
        
        return {
            "company_overview": """
HuntRED® es líder en soluciones de tecnología para Recursos Humanos en México, 
con más de 10 años de experiencia sirviendo a empresas de todos los tamaños.
            """,
            "certifications": [
                "ISO 27001 - Seguridad de la Información",
                "SOC 2 Type II - Controles de Seguridad",
                "Certificación SAT - Facturación Electrónica",
                "Partner Certificado Microsoft Azure"
            ],
            "clients": [
                "500+ empresas activas",
                "50,000+ empleados gestionados",
                "99.9% uptime histórico",
                "95% satisfacción del cliente"
            ]
        }
    
    def _generate_case_studies(self) -> List[Dict[str, Any]]:
        """Generate relevant case studies"""
        
        return [
            {
                "client": "Empresa Manufacturera - 150 empleados",
                "challenge": "Proceso manual de nómina tomaba 3 días",
                "solution": "Implementación de HuntRED® Plan Profesional",
                "results": [
                    "Reducción de tiempo de nómina a 2 horas",
                    "100% compliance automático",
                    "Ahorro de $50,000 MXN anuales"
                ]
            },
            {
                "client": "Empresa de Servicios - 80 empleados",
                "challenge": "Falta de visibilidad en métricas de RRHH",
                "solution": "Dashboard ejecutivo y reportes automáticos",
                "results": [
                    "Reportes en tiempo real",
                    "Mejor toma de decisiones",
                    "Reducción 40% en rotación"
                ]
            }
        ]
    
    def _generate_tech_specs(self) -> Dict[str, Any]:
        """Generate technical specifications"""
        
        return {
            "architecture": "Cloud-native en Microsoft Azure",
            "security": "Encriptación AES-256, autenticación multi-factor",
            "integrations": [
                "APIs REST para integraciones",
                "Conectores SAP, Oracle, Workday",
                "Webhooks para notificaciones en tiempo real"
            ],
            "mobile": "Apps nativas iOS y Android",
            "reporting": "Power BI integrado para analytics avanzados"
        }
    
    async def send_proposal(self, proposal_id: str, delivery_method: str = "email") -> Dict[str, Any]:
        """Send proposal to client"""
        try:
            # Get proposal (mock implementation)
            proposal = await self._get_proposal(proposal_id)
            
            if not proposal:
                return {"success": False, "error": "Proposal not found"}
            
            # Update status
            proposal["status"] = ProposalStatus.SENT.value
            proposal["sent_at"] = datetime.now()
            
            # Generate PDF or email content
            if delivery_method == "email":
                result = await self._send_proposal_email(proposal)
            else:
                result = await self._generate_proposal_pdf(proposal)
            
            logger.info(f"Proposal {proposal_id} sent via {delivery_method}")
            
            return {
                "success": True,
                "proposal_id": proposal_id,
                "delivery_method": delivery_method,
                "sent_at": proposal["sent_at"],
                "tracking_url": f"https://huntred.com/proposals/{proposal_id}/track"
            }
            
        except Exception as e:
            logger.error(f"Error sending proposal: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_proposal(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        """Get proposal by ID (mock implementation)"""
        # In real implementation, query from database
        return {
            "id": proposal_id,
            "status": ProposalStatus.DRAFT.value,
            "client_info": {"company_name": "Test Company"},
            "content": {}
        }
    
    async def _send_proposal_email(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Send proposal via email"""
        # Mock email sending
        return {"email_sent": True, "message_id": str(uuid.uuid4())}
    
    async def _generate_proposal_pdf(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Generate proposal PDF"""
        # Mock PDF generation
        return {"pdf_generated": True, "file_path": f"/proposals/{proposal['id']}.pdf"}
    
    async def track_proposal_engagement(self, proposal_id: str) -> Dict[str, Any]:
        """Track proposal engagement metrics"""
        try:
            return {
                "proposal_id": proposal_id,
                "metrics": {
                    "views": 3,
                    "time_spent": "12 minutes",
                    "sections_viewed": ["executive_summary", "pricing", "implementation"],
                    "last_viewed": datetime.now() - timedelta(hours=2),
                    "devices": ["desktop", "mobile"],
                    "locations": ["Mexico City"]
                },
                "engagement_score": 75,  # 0-100
                "likelihood_to_close": "high"
            }
            
        except Exception as e:
            logger.error(f"Error tracking proposal engagement: {e}")
            return {"error": str(e)}

# Global proposals service
def get_proposals_service(db: Session) -> ProposalsService:
    """Get proposals service instance"""
    return ProposalsService(db)