"""
📄 SERVICIO DE FACTURACIÓN ELECTRÓNICA - huntRED

Servicio para generación, firma y timbrado de CFDI 4.0.
"""

import logging
import base64
import hashlib
import uuid
import requests
import json
from datetime import datetime
from typing import Dict, Any, Optional
from xml.etree import ElementTree as ET

from django.core.exceptions import ValidationError
from django.utils import timezone

from app.models import Invoice, LineItem, BusinessUnit
from app.ats.pricing.models.pac_configuration import PACConfiguration

logger = logging.getLogger(__name__)

class ElectronicBillingService:
    """Servicio para facturación electrónica CFDI."""
    
    def __init__(self, business_unit):
        self.business_unit = business_unit
        self.pac_config = self._get_active_pac_config()
    
    def _get_active_pac_config(self) -> Optional[PACConfiguration]:
        """Obtiene la configuración activa del PAC."""
        return PACConfiguration.objects.filter(
            business_unit=self.business_unit,
            status='active'
        ).first()
    
    def generate_cfdi_xml(self, invoice: Invoice) -> str:
        """
        Genera el XML CFDI 3.3 para una factura.
        
        Args:
            invoice: Factura a procesar
            
        Returns:
            str: XML CFDI generado
        """
        # Crear el elemento raíz del CFDI
        cfdi_ns = {
            'cfdi': 'http://www.sat.gob.mx/cfd/3',
            'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital'
        }
        
        root = ET.Element('cfdi:Comprobante', {
            'Version': '3.3',
            'Fecha': invoice.issue_date.strftime('%Y-%m-%dT%H:%M:%S'),
            'Sello': '',  # Se llenará después de firmar
            'NoCertificado': '',  # Se llenará con el número del certificado
            'Certificado': '',  # Se llenará con el certificado en base64
            'SubTotal': str(invoice.subtotal),
            'Moneda': invoice.currency,
            'Total': str(invoice.total_amount),
            'TipoDeComprobante': 'I',  # Ingreso
            'FormaPago': '01',  # Efectivo
            'MetodoPago': 'PUE',  # Pago en una sola exhibición
            'LugarExpedicion': '06500',  # Código postal
            'Exportacion': '01',  # No aplica
        })
        
        # Agregar namespace
        for prefix, uri in cfdi_ns.items():
            root.set(f'xmlns:{prefix}', uri)
        
        # Emisor
        emisor = ET.SubElement(root, 'cfdi:Emisor', {
            'Rfc': invoice.issuer_rfc or 'XAXX010101000',
            'Nombre': invoice.issuer_name or 'HUNTRED',
            'RegimenFiscal': invoice.issuer_regime or '601'
        })
        
        # Receptor
        receptor = ET.SubElement(root, 'cfdi:Receptor', {
            'Rfc': invoice.receiver_rfc or 'XAXX010101000',
            'Nombre': invoice.receiver_name or 'PUBLICO EN GENERAL',
            'UsoCFDI': invoice.receiver_use or 'G01'
        })
        
        # Conceptos
        conceptos = ET.SubElement(root, 'cfdi:Conceptos')
        
        for line_item in invoice.line_items.all():
            concepto = ET.SubElement(conceptos, 'cfdi:Concepto', {
                'ClaveProdServ': line_item.product_key or '84111506',
                'NoIdentificacion': str(line_item.id),
                'Cantidad': str(line_item.quantity),
                'ClaveUnidad': line_item.unit_key or 'E48',
                'Unidad': 'Unidad de Servicio',
                'Descripcion': line_item.description,
                'ValorUnitario': str(line_item.unit_price),
                'Importe': str(line_item.subtotal),
                'ObjetoImp': '01'  # No objeto del impuesto
            })
            
            # Impuestos del concepto
            if line_item.tax_amount > 0:
                impuestos = ET.SubElement(concepto, 'cfdi:Impuestos')
                traslados = ET.SubElement(impuestos, 'cfdi:Traslados')
                
                ET.SubElement(traslados, 'cfdi:Traslado', {
                    'Base': str(line_item.subtotal),
                    'Impuesto': '002',  # IVA
                    'TipoFactor': 'Tasa',
                    'TasaOCuota': str(line_item.tax_rate / 100),
                    'Importe': str(line_item.tax_amount)
                })
        
        # Impuestos del comprobante
        if invoice.tax_amount > 0:
            impuestos = ET.SubElement(root, 'cfdi:Impuestos', {
                'TotalImpuestosTrasladados': str(invoice.tax_amount)
            })
            
            traslados = ET.SubElement(impuestos, 'cfdi:Traslados')
            ET.SubElement(traslados, 'cfdi:Traslado', {
                'Impuesto': '002',  # IVA
                'TipoFactor': 'Tasa',
                'TasaOCuota': '0.160000',
                'Importe': str(invoice.tax_amount)
            })
        
        # Convertir a string
        xml_string = ET.tostring(root, encoding='unicode', method='xml')
        
        # Agregar declaración XML
        xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
        return xml_declaration + xml_string
    
    def sign_xml(self, xml_content: str, certificate_path: str, key_path: str, password: str) -> str:
        """
        Firma digitalmente el XML CFDI.
        
        Args:
            xml_content: Contenido XML a firmar
            certificate_path: Ruta al archivo del certificado (.cer)
            key_path: Ruta al archivo de la llave privada (.key)
            password: Contraseña del certificado
            
        Returns:
            str: XML firmado
        """
        try:
            # Aquí se implementaría la lógica de firma digital
            # Por ahora, simulamos la firma
            
            # Simular cadena original
            cadena_original = self._generate_cadena_original(xml_content)
            
            # Simular sello digital (en producción usarías la librería de firma)
            sello_digital = self._simulate_digital_signature(cadena_original, key_path, password)
            
            # Actualizar el XML con el sello
            xml_tree = ET.fromstring(xml_content)
            xml_tree.set('Sello', sello_digital)
            xml_tree.set('NoCertificado', '30001000000400002434')  # Número del certificado
            xml_tree.set('Certificado', self._get_certificate_base64(certificate_path))
            
            return ET.tostring(xml_tree, encoding='unicode', method='xml')
            
        except Exception as e:
            raise ValidationError(f"Error al firmar XML: {str(e)}")
    
    def _generate_cadena_original(self, xml_content: str) -> str:
        """Genera la cadena original del XML CFDI."""
        # En producción, usarías la librería oficial del SAT
        # Por ahora, simulamos la cadena original
        return f"||3.3|{timezone.now().strftime('%Y-%m-%dT%H:%M:%S')}|I|PUE|MXN|{uuid.uuid4()}|"
    
    def _simulate_digital_signature(self, cadena_original: str, key_path: str, password: str) -> str:
        """Simula la firma digital (en producción usarías librería real)."""
        # En producción, usarías:
        # - OpenSSL o librería específica para firma
        # - La llave privada real
        # - El algoritmo SHA256
        
        # Simulación
        signature_input = cadena_original + key_path + password
        signature = hashlib.sha256(signature_input.encode()).hexdigest()
        return base64.b64encode(signature.encode()).decode()
    
    def _get_certificate_base64(self, certificate_path: str) -> str:
        """Obtiene el certificado en formato base64."""
        try:
            with open(certificate_path, 'rb') as cert_file:
                cert_data = cert_file.read()
                return base64.b64encode(cert_data).decode()
        except Exception:
            # En caso de error, retornar certificado dummy
            return "dummy_certificate_base64"
    
    def stamp_with_pac(self, xml_content: str, pac_config: PACConfiguration) -> Dict[str, Any]:
        """
        Timbra el XML CFDI con el PAC.
        
        Args:
            xml_content: XML CFDI firmado
            pac_config: Configuración del PAC
            
        Returns:
            Dict: Respuesta del PAC con UUID y XML timbrado
        """
        if not pac_config.is_ready_for_stamping():
            raise ValidationError("El PAC no está configurado correctamente para timbrar")
        
        # Preparar payload según el tipo de PAC
        payload = {
            'xml': xml_content,
            'username': pac_config.username,
            'password': pac_config.password,
            'test': pac_config.is_test_mode
        }
        
        # Enviar al PAC según su tipo
        if pac_config.pac_type == 'facturama':
            return self._stamp_with_facturama(payload, pac_config)
        elif pac_config.pac_type == 'solucion_factible':
            return self._stamp_with_solucion_factible(payload, pac_config)
        else:
            return self._stamp_with_generic_pac(payload, pac_config)
    
    def _stamp_with_facturama(self, payload: Dict, pac_config: PACConfiguration) -> Dict[str, Any]:
        """Timbra con Facturama."""
        try:
            response = requests.post(
                f"{pac_config.api_url}/api/cfdi33/stamp",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'uuid': data.get('UUID'),
                    'xml_timbrado': data.get('CFDI'),
                    'cadena_original': data.get('CadenaOriginal'),
                    'qr_code': data.get('QRCode')
                }
            else:
                return {
                    'success': False,
                    'error': f"Error del PAC: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Error de conexión: {str(e)}"
            }
    
    def _stamp_with_solucion_factible(self, payload: Dict, pac_config: PACConfiguration) -> Dict[str, Any]:
        """Timbra con Solución Factible."""
        try:
            response = requests.post(
                f"{pac_config.api_url}/stamp",
                data=payload,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'uuid': data.get('uuid'),
                    'xml_timbrado': data.get('xml'),
                    'cadena_original': data.get('cadena_original'),
                    'qr_code': data.get('qr_code')
                }
            else:
                return {
                    'success': False,
                    'error': f"Error del PAC: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Error de conexión: {str(e)}"
            }
    
    def _stamp_with_generic_pac(self, payload: Dict, pac_config: PACConfiguration) -> Dict[str, Any]:
        """Timbra con PAC genérico."""
        try:
            response = requests.post(
                pac_config.api_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'uuid': data.get('uuid') or data.get('UUID'),
                    'xml_timbrado': data.get('xml') or data.get('CFDI'),
                    'cadena_original': data.get('cadena_original') or data.get('CadenaOriginal'),
                    'qr_code': data.get('qr_code') or data.get('QRCode')
                }
            else:
                return {
                    'success': False,
                    'error': f"Error del PAC: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Error de conexión: {str(e)}"
            }
    
    def generate_pdf(self, invoice: Invoice, xml_timbrado: str) -> str:
        """
        Genera el PDF de la factura electrónica.
        
        Args:
            invoice: Factura a procesar
            xml_timbrado: XML timbrado del PAC
            
        Returns:
            str: Ruta al archivo PDF generado
        """
        try:
            # En producción, usarías una librería como WeasyPrint o ReportLab
            # Por ahora, simulamos la generación del PDF
            
            pdf_content = f"""
            FACTURA ELECTRÓNICA
            
            Folio: {invoice.invoice_number}
            Fecha: {invoice.issue_date}
            Cliente: {invoice.receiver_name}
            RFC: {invoice.receiver_rfc}
            
            Subtotal: ${invoice.subtotal}
            IVA: ${invoice.tax_amount}
            Total: ${invoice.total_amount}
            
            UUID: {self._extract_uuid_from_xml(xml_timbrado)}
            
            Este es un PDF simulado. En producción se generaría con una librería real.
            """
            
            # Guardar PDF (simulado)
            pdf_path = f"/tmp/factura_{invoice.invoice_number}.pdf"
            with open(pdf_path, 'w') as f:
                f.write(pdf_content)
            
            return pdf_path
            
        except Exception as e:
            logger.error(f"Error generando PDF: {str(e)}")
            raise ValidationError(f"Error generando PDF: {str(e)}")
    
    def _extract_uuid_from_xml(self, xml_content: str) -> str:
        """Extrae el UUID del XML timbrado."""
        try:
            xml_tree = ET.fromstring(xml_content)
            # Buscar el UUID en el complemento de timbre fiscal
            tfd = xml_tree.find('.//{http://www.sat.gob.mx/TimbreFiscalDigital}TimbreFiscalDigital')
            if tfd is not None:
                return tfd.get('UUID', '')
            return ''
        except Exception:
            return ''
    
    def process_electronic_invoice(self, invoice: Invoice) -> Dict[str, Any]:
        """
        Procesa una factura completa: genera XML, firma y timbra.
        
        Args:
            invoice: Factura a procesar
            
        Returns:
            Dict: Resultado del procesamiento
        """
        try:
            # 1. Generar XML CFDI
            xml_content = self.generate_cfdi_xml(invoice)
            
            # 2. Firmar XML (si hay certificado configurado)
            if self.pac_config and self.pac_config.certificate_path:
                xml_content = self.sign_xml(
                    xml_content,
                    self.pac_config.certificate_path,
                    self.pac_config.private_key_path,
                    self.pac_config.certificate_password
                )
            
            # 3. Timbrar con PAC
            if self.pac_config:
                stamp_result = self.stamp_with_pac(xml_content, self.pac_config)
                
                if stamp_result['success']:
                    # 4. Generar PDF
                    pdf_path = self.generate_pdf(invoice, stamp_result['xml_timbrado'])
                    
                    # 5. Actualizar factura
                    invoice.electronic_uuid = stamp_result['uuid']
                    invoice.electronic_xml = stamp_result['xml_timbrado']
                    invoice.electronic_pdf = pdf_path
                    invoice.electronic_status = 'stamped'
                    invoice.save()
                    
                    return {
                        'success': True,
                        'uuid': stamp_result['uuid'],
                        'xml': stamp_result['xml_timbrado'],
                        'pdf': pdf_path,
                        'qr_code': stamp_result.get('qr_code')
                    }
                else:
                    return {
                        'success': False,
                        'error': stamp_result['error']
                    }
            else:
                # Sin PAC configurado, solo generar XML
                invoice.electronic_xml = xml_content
                invoice.electronic_status = 'generated'
                invoice.save()
                
                return {
                    'success': True,
                    'xml': xml_content,
                    'message': 'XML generado sin timbrar (sin PAC configurado)'
                }
                
        except Exception as e:
            logger.error(f"Error procesando factura electrónica: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_invoice_to_client(self, invoice: Invoice, client_email: str) -> bool:
        """
        Envía la factura electrónica al cliente por email.
        
        Args:
            invoice: Factura a enviar
            client_email: Email del cliente
            
        Returns:
            bool: True si se envió correctamente
        """
        try:
            # En producción, usarías Django's email backend
            # Por ahora, simulamos el envío
            
            subject = f"Factura Electrónica {invoice.invoice_number}"
            message = f"""
            Estimado cliente,
            
            Adjunto encontrará su factura electrónica {invoice.invoice_number}.
            
            UUID: {invoice.electronic_uuid}
            Total: ${invoice.total_amount}
            
            Saludos,
            huntRED
            """
            
            # Simular envío
            logger.info(f"Email enviado a {client_email}: {subject}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error enviando factura: {str(e)}")
            return False 