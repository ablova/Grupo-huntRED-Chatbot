"""
Conector de Contactos para el Sistema Aura

Este módulo integra datos de contactos para enriquecer la red de relaciones
profesionales y personales.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class Contact:
    """Contacto del sistema."""
    contact_id: str
    name: str
    email: Optional[str]
    phone: Optional[str]
    company: Optional[str]
    position: Optional[str]
    relationship_type: str  # personal, professional, both
    relationship_strength: float  # 0-1
    last_contact: Optional[datetime]
    notes: Optional[str]

class ContactsConnector:
    """
    Conector para integrar datos de contactos con el sistema Aura.
    
    Enriquece la información con contactos personales y profesionales
    para análisis de red y networking.
    """
    
    def __init__(self):
        """Inicializa el conector de contactos."""
        self.logger = logger
        self.logger.info("Conector de Contactos inicializado")
    
    async def get_contacts(
        self,
        person_id: int,
        contact_type: Optional[str] = None,
        max_contacts: int = 100
    ) -> List[Contact]:
        """
        Obtiene contactos del sistema.
        
        Args:
            person_id: ID de la persona en el sistema huntRED
            contact_type: Tipo de contacto (personal, professional, both)
            max_contacts: Máximo número de contactos a obtener
            
        Returns:
            Lista de contactos
        """
        try:
            # En una implementación real, esto consultaría la base de datos
            # Por ahora, simulamos contactos
            
            contacts = []
            for i in range(min(max_contacts, 20)):
                contact = Contact(
                    contact_id=f"contact_{i}",
                    name=f"Contacto {i}",
                    email=f"contacto{i}@email.com",
                    phone=f"+1-555-{i:03d}-{i:04d}",
                    company=f"Empresa {i}",
                    position=f"Posición {i}",
                    relationship_type="professional" if i % 2 == 0 else "personal",
                    relationship_strength=0.7 + (i * 0.01),
                    last_contact=datetime.now(),
                    notes=f"Notas del contacto {i}"
                )
                contacts.append(contact)
            
            # Filtrar por tipo si se especifica
            if contact_type:
                contacts = [c for c in contacts if c.relationship_type == contact_type]
            
            return contacts
            
        except Exception as e:
            self.logger.error(f"Error obteniendo contactos: {str(e)}")
            return []
    
    async def find_common_contacts(
        self,
        person_id: int,
        target_company: str
    ) -> List[Contact]:
        """
        Encuentra contactos en común con una empresa objetivo.
        
        Args:
            person_id: ID de la persona
            target_company: Empresa objetivo
            
        Returns:
            Lista de contactos en común
        """
        try:
            contacts = await self.get_contacts(person_id)
            
            # Filtrar contactos que trabajan en la empresa objetivo
            common_contacts = []
            for contact in contacts:
                if contact.company and target_company.lower() in contact.company.lower():
                    common_contacts.append(contact)
            
            return common_contacts
            
        except Exception as e:
            self.logger.error(f"Error encontrando contactos en común: {str(e)}")
            return []
    
    async def analyze_network_strength(
        self,
        person_id: int
    ) -> Dict[str, Any]:
        """
        Analiza la fortaleza de la red de contactos.
        
        Args:
            person_id: ID de la persona
            
        Returns:
            Análisis de la red de contactos
        """
        try:
            contacts = await self.get_contacts(person_id)
            
            if not contacts:
                return {
                    "total_contacts": 0,
                    "network_strength": 0,
                    "professional_contacts": 0,
                    "personal_contacts": 0,
                    "average_relationship_strength": 0
                }
            
            professional_contacts = [c for c in contacts if c.relationship_type in ["professional", "both"]]
            personal_contacts = [c for c in contacts if c.relationship_type in ["personal", "both"]]
            
            avg_strength = sum(c.relationship_strength for c in contacts) / len(contacts)
            
            return {
                "total_contacts": len(contacts),
                "network_strength": avg_strength * len(contacts),
                "professional_contacts": len(professional_contacts),
                "personal_contacts": len(personal_contacts),
                "average_relationship_strength": avg_strength
            }
            
        except Exception as e:
            self.logger.error(f"Error analizando red de contactos: {str(e)}")
            return {
                "total_contacts": 0,
                "network_strength": 0,
                "professional_contacts": 0,
                "personal_contacts": 0,
                "average_relationship_strength": 0
            } 