#!/usr/bin/env python3
# /home/pablo/app/com/chatbot/integrations/document_processor.py
#
# Procesador de documentos (CV y otros) para el chatbot.
# Gestiona la extracción de texto, análisis y almacenamiento 
# de documentos recibidos a través de múltiples canales.

import os
import io
import re
import logging
import asyncio
import httpx
import time
import json
from typing import Dict, Any, List, Optional, Tuple
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from asgiref.sync import sync_to_async

# Importamos las dependencias para procesamiento de documentos
try:
    import PyPDF2
    from docx import Document
    HAS_DOC_LIBRARIES = True
except ImportError:
    HAS_DOC_LIBRARIES = False
    logging.warning("Librerías para procesamiento de documentos no disponibles")

# Configuramos el logger
logger = logging.getLogger('chatbot')

class DocumentProcessor:
    """
    Procesa documentos recibidos a través de canales de chatbot.
    Soporta extracción de texto, análisis y gestión de:
    - PDF
    - DOCX/DOC
    - Imágenes (con OCR opcional)
    """
    
    def __init__(self, user_id: str = None, business_unit_id: str = None):
        self.user_id = user_id
        self.business_unit_id = business_unit_id
        self.storage_path = getattr(settings, 'DOCUMENTS_STORAGE_PATH', 'media/documents/')
        self.max_file_size = getattr(settings, 'MAX_DOCUMENT_SIZE_MB', 10) * 1024 * 1024  # En bytes
        self.supported_mime_types = {
            'pdf': ['application/pdf'],
            'word': ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
            'image': ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
        }
        
        # Aseguramos que existe la carpeta de almacenamiento
        os.makedirs(self.storage_path, exist_ok=True)
        
    async def process_document(self, file_data: bytes, filename: str, mime_type: str) -> Dict[str, Any]:
        """
        Procesa un documento determinando su tipo y aplicando el procesamiento adecuado.
        """
        try:
            # Validación básica
            if not file_data:
                return {"success": False, "error": "No se recibieron datos del archivo"}
                
            if len(file_data) > self.max_file_size:
                return {"success": False, "error": f"El archivo excede el tamaño máximo permitido ({self.max_file_size/(1024*1024)}MB)"}
            
            # Determinamos el tipo de archivo
            doc_type = self._determine_doc_type(mime_type)
            if not doc_type:
                return {"success": False, "error": "Tipo de archivo no soportado"}
                
            # Guardamos el documento
            file_path = await self._save_document(file_data, filename, doc_type)
            if not file_path:
                return {"success": False, "error": "Error al guardar el documento"}
                
            # Si es un CV, lo procesamos
            if self._is_cv(filename, mime_type):
                return await self._process_cv(file_path, doc_type, mime_type)
            
            # Documento genérico
            return {
                "success": True,
                "file_path": file_path,
                "doc_type": doc_type,
                "processed": False,
                "message": "Documento recibido correctamente"
            }
            
        except Exception as e:
            logger.error(f"Error procesando documento: {str(e)}", exc_info=True)
            return {"success": False, "error": f"Error al procesar el documento: {str(e)}"}
    
    async def _save_document(self, file_data: bytes, filename: str, doc_type: str) -> str:
        """
        Guarda un documento en el almacenamiento configurado.
        """
        try:
            # Generamos un nombre único para evitar colisiones
            timestamp = int(time.time())
            safe_filename = re.sub(r'[^\w\.-]', '_', filename)
            unique_filename = f"{doc_type}_{timestamp}_{safe_filename}"
            
            # Definimos la ruta según tipo y usuario
            user_path = f"user_{self.user_id}/" if self.user_id else ""
            relative_path = f"{self.storage_path}{user_path}{unique_filename}"
            
            # Guardar archivo usando Django Storage
            saved_path = await sync_to_async(default_storage.save)(relative_path, ContentFile(file_data))
            logger.info(f"Documento guardado en: {saved_path}")
            
            return saved_path
        except Exception as e:
            logger.error(f"Error guardando documento: {str(e)}", exc_info=True)
            return ""
    
    def _determine_doc_type(self, mime_type: str) -> str:
        """
        Determina el tipo de documento basado en su MIME type.
        """
        for doc_type, mime_types in self.supported_mime_types.items():
            if mime_type in mime_types:
                return doc_type
        return ""
    
    def _is_cv(self, filename: str, mime_type: str) -> bool:
        """
        Determina si un documento es probablemente un CV basado en nombre y tipo.
        """
        cv_indicators = ['cv', 'curriculum', 'resume', 'vitae']
        filename_lower = filename.lower()
        
        # Verificar si es un documento soportado
        is_document = mime_type in self.supported_mime_types['pdf'] + self.supported_mime_types['word']
        
        # Verificar si el nombre contiene indicadores de CV
        has_cv_indicator = any(indicator in filename_lower for indicator in cv_indicators)
        
        return is_document and has_cv_indicator
    
    async def _process_cv(self, file_path: str, doc_type: str, mime_type: str) -> Dict[str, Any]:
        """
        Procesa un archivo de CV extrayendo su contenido y analizándolo.
        """
        try:
            if not HAS_DOC_LIBRARIES:
                return {
                    "success": True,
                    "file_path": file_path, 
                    "processed": False,
                    "message": "CV recibido, pero las librerías de procesamiento no están disponibles"
                }
            
            # Extraer texto según el tipo
            if doc_type == 'pdf':
                text_content = await self._extract_text_from_pdf(file_path)
            elif doc_type == 'word':
                text_content = await self._extract_text_from_word(file_path)
            else:
                return {
                    "success": True,
                    "file_path": file_path,
                    "processed": False,
                    "message": "Formato de CV no soportado para extracción de texto"
                }
            
            if not text_content:
                return {
                    "success": True,
                    "file_path": file_path,
                    "processed": False,
                    "message": "No se pudo extraer texto del CV"
                }
            
            # Analizamos el CV con NLP/GPT
            cv_data = await self._analyze_cv_text(text_content)
            
            # Vinculamos el CV con el usuario si tenemos su ID
            if self.user_id:
                await self._link_cv_to_user(file_path, cv_data)
            
            return {
                "success": True,
                "file_path": file_path,
                "doc_type": doc_type,
                "processed": True,
                "cv_data": cv_data,
                "message": "CV procesado correctamente"
            }
            
        except Exception as e:
            logger.error(f"Error procesando CV: {str(e)}", exc_info=True)
            return {
                "success": False,
                "file_path": file_path,
                "error": f"Error al procesar el CV: {str(e)}"
            }
    
    async def _extract_text_from_pdf(self, file_path: str) -> str:
        """
        Extrae texto de un documento PDF.
        """
        try:
            # Usamos run_in_executor para no bloquear el loop de eventos
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, self._extract_pdf_text_sync, file_path)
        except Exception as e:
            logger.error(f"Error extrayendo texto de PDF: {str(e)}", exc_info=True)
            return ""
    
    def _extract_pdf_text_sync(self, file_path: str) -> str:
        """
        Método sincrónico para extraer texto de PDF (ejecutado en thread pool).
        """
        try:
            text_content = ""
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    text_content += page.extract_text() + "\n\n"
            return text_content.strip()
        except Exception as e:
            logger.error(f"Error en extracción sincrónica de PDF: {str(e)}", exc_info=True)
            return ""
    
    async def _extract_text_from_word(self, file_path: str) -> str:
        """
        Extrae texto de un documento Word.
        """
        try:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, self._extract_word_text_sync, file_path)
        except Exception as e:
            logger.error(f"Error extrayendo texto de Word: {str(e)}", exc_info=True)
            return ""
    
    def _extract_word_text_sync(self, file_path: str) -> str:
        """
        Método sincrónico para extraer texto de Word (ejecutado en thread pool).
        """
        try:
            text_content = ""
            doc = Document(file_path)
            for para in doc.paragraphs:
                text_content += para.text + "\n"
            return text_content.strip()
        except Exception as e:
            logger.error(f"Error en extracción sincrónica de Word: {str(e)}", exc_info=True)
            return ""
    
    async def _analyze_cv_text(self, text_content: str) -> Dict[str, Any]:
        """
        Analiza el texto del CV para extraer información relevante.
        Si tenemos integración con GPT, lo usamos, sino hacemos un análisis básico.
        """
        try:
            # Primero intentamos con NLP avanzado
            try:
                from app.com.chatbot.gpt import GPTService
                gpt_service = GPTService()
                
                # Truncamos el texto si es muy largo para no sobrecargar la API
                max_text_length = 3000
                truncated_text = text_content[:max_text_length] if len(text_content) > max_text_length else text_content
                
                prompt = (
                    f"Analiza este contenido de CV y extrae la siguiente información en formato JSON:\n\n"
                    f"- nombre: Nombre completo de la persona\n"
                    f"- email: Correo electrónico de contacto\n"
                    f"- telefono: Número telefónico\n"
                    f"- titulo: Puesto o título profesional\n"
                    f"- skills: Lista de habilidades técnicas principales (máximo 10)\n"
                    f"- experiencia_anos: Estimación de años de experiencia\n"
                    f"- ultimo_puesto: Último cargo ocupado\n"
                    f"- nivel_estudios: Nivel educativo más alto\n\n"
                    f"Texto del CV:\n{truncated_text}"
                )
                
                response = await gpt_service.generate_response(prompt)
                if response and "response" in response:
                    try:
                        # Intentamos extraer el JSON de la respuesta
                        json_str = response["response"]
                        # Intentar encontrar un objeto JSON en la respuesta
                        match = re.search(r'\{.*\}', json_str, re.DOTALL)
                        if match:
                            json_str = match.group(0)
                        
                        cv_data = json.loads(json_str)
                        cv_data["ai_processed"] = True
                        return cv_data
                    except json.JSONDecodeError:
                        logger.warning("Error decodificando JSON de respuesta GPT")
                
            except (ImportError, Exception) as e:
                logger.warning(f"No se pudo usar GPT para análisis de CV: {str(e)}")
            
            # Fallback a análisis básico con regex
            return self._basic_cv_analysis(text_content)
            
        except Exception as e:
            logger.error(f"Error analizando CV: {str(e)}", exc_info=True)
            return {"ai_processed": False, "error": str(e)}
    
    def _basic_cv_analysis(self, text_content: str) -> Dict[str, Any]:
        """
        Análisis básico de CV usando expresiones regulares.
        """
        cv_data = {
            "nombre": "",
            "email": "",
            "telefono": "",
            "titulo": "",
            "skills": [],
            "experiencia_anos": 0,
            "ultimo_puesto": "",
            "nivel_estudios": "",
            "ai_processed": False
        }
        
        # Extraer email
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text_content)
        if email_match:
            cv_data["email"] = email_match.group(0)
        
        # Extraer teléfono (patrón simplificado)
        phone_match = re.search(r'(?:\+\d{1,3}[ -]?)?(?:\(\d{1,4}\)|\d{1,4})[ -]?\d{1,4}[ -]?\d{1,9}', text_content)
        if phone_match:
            cv_data["telefono"] = phone_match.group(0)
        
        # Extraer habilidades comunes
        common_skills = [
            "python", "java", "javascript", "html", "css", "php", "ruby",
            "react", "angular", "vue", "node.js", "django", "flask",
            "sql", "mysql", "postgresql", "mongodb", "firebase",
            "aws", "azure", "gcp", "docker", "kubernetes",
            "git", "excel", "powerpoint", "word",
            "machine learning", "deep learning", "ai", "big data",
            "marketing", "ventas", "recursos humanos", "finanzas", "contabilidad",
            "gestión de proyectos", "scrum", "agile", "kanban",
            "inglés", "español", "francés", "alemán", "portugués", "italiano",
            "liderazgo", "trabajo en equipo", "comunicación", "negociación"
        ]
        
        for skill in common_skills:
            if re.search(r'\b' + re.escape(skill) + r'\b', text_content, re.IGNORECASE):
                cv_data["skills"].append(skill.lower())
        
        cv_data["skills"] = cv_data["skills"][:10]  # Limitamos a 10 habilidades
        
        return cv_data
    
    async def _link_cv_to_user(self, file_path: str, cv_data: Dict[str, Any]) -> bool:
        """
        Vincula el CV con el perfil del usuario en la base de datos.
        """
        try:
            # Este método debe implementarse según el modelo de datos específico
            # En este caso, necesita ser implementado con la estructura de BD de huntRED
            from app.models import Person
            
            # Actualización asíncrona del perfil
            user = await Person.objects.filter(id=self.user_id).afirst()
            if user:
                user.cv_url = file_path
                
                # Actualizar datos del usuario si tenemos información del CV
                if cv_data.get("nombre") and not user.nombre:
                    user.nombre = cv_data["nombre"]
                
                if cv_data.get("email") and not user.email:
                    user.email = cv_data["email"]
                
                if cv_data.get("telefono") and not user.telefono:
                    user.telefono = cv_data["telefono"]
                
                # Actualizar metadata para almacenar habilidades
                metadata = user.metadata or {}
                if cv_data.get("skills"):
                    metadata["skills"] = cv_data["skills"]
                
                user.metadata = metadata
                await user.asave()
                
                logger.info(f"CV vinculado al usuario {self.user_id}")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error vinculando CV a usuario: {str(e)}", exc_info=True)
            return False
