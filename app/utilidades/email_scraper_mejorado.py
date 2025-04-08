from typing import Optional, Dict
from django.db.models.query import sync_to_async
from django.utils.log import logger
from app.models import BusinessUnit, Worker, Vacante
from django.utils import timezone

async def assign_business_unit(job_title: str, job_description: str = None, location: str = None) -> Optional[int]:
    """Asigna una unidad de negocio a una vacante"""
    # Texto a analizar
    job_title_lower = job_title.lower() if job_title else ""
    job_desc_lower = job_description.lower() if job_description else ""
    location_lower = location.lower() if location else ""
    
    # Calcular puntuación para cada unidad de negocio
    try:
        bu_list = await sync_to_async(list)(BusinessUnit.objects.all())
        if not bu_list:
            logger.error("No hay unidades de negocio configuradas")
            return None
        
        scores = {bu.id: 0 for bu in bu_list}
        
        # Determinar nivel de seniority
        seniority_score = 0
        for term, score in [
            ("junior", 1), ("trainee", 1), ("entry", 1), 
            ("mid", 2), ("senior", 3), ("lead", 3), 
            ("manager", 4), ("director", 5), ("vp", 5), ("chief", 5)
        ]:
            if term in job_title_lower or term in job_desc_lower:
                seniority_score = max(seniority_score, score)
        
        # Analizar por unidad de negocio
        for bu in bu_list:
            bu_score = 0
            
            # LinkedIn tiene alta prioridad para huntu y huntRED
            if "linkedin" in job_title_lower or "linkedin" in job_desc_lower:
                if bu.name == "huntu":
                    bu_score += 20
                elif bu.name == "huntRED®":
                    bu_score += 15
            
            # Asignar basado en seniority
            if seniority_score >= 4:  # Director, VP, Chief
                if bu.name == "huntRED® Executive":
                    bu_score += 30
                elif bu.name == "huntRED®":
                    bu_score += 20
            elif seniority_score == 3:  # Senior, Lead
                if bu.name == "huntRED®":
                    bu_score += 25
                elif bu.name == "huntu":
                    bu_score += 10
            elif seniority_score <= 2:  # Junior, Mid
                if bu.name == "huntu":
                    bu_score += 20
                elif bu.name == "amigro":
                    bu_score += 10
            
            # Análisis por keywords técnicos (huntu)
            tech_keywords = ["developer", "software", "engineer", "data", "it", "tech", "programador", "desarrollador", "analista"]
            for keyword in tech_keywords:
                if keyword in job_title_lower or keyword in job_desc_lower:
                    if bu.name == "huntu":
                        bu_score += 5
            
            # Análisis por keywords de management (huntRED)
            mgmt_keywords = ["manager", "director", "executive", "gerente", "jefe", "líder", "management", "business"]
            for keyword in mgmt_keywords:
                if keyword in job_title_lower or keyword in job_desc_lower:
                    if bu.name == "huntRED®":
                        bu_score += 5
                    elif bu.name == "huntRED® Executive" and seniority_score >= 4:
                        bu_score += 8
            
            # Análisis por keywords de migración (amigro)
            migration_keywords = ["migration", "visa", "abroad", "international", "migración", "temporal", "extranjero"]
            for keyword in migration_keywords:
                if keyword in job_title_lower or keyword in job_desc_lower or keyword in location_lower:
                    if bu.name == "amigro":
                        bu_score += 15
            
            scores[bu.id] = bu_score
        
        # Obtener la unidad de negocio con mayor puntuación
        max_score = max(scores.values())
        if max_score == 0:
            # Si ninguna tiene puntuación, asignar a huntRED por defecto
            default_bu = await sync_to_async(BusinessUnit.objects.filter)(name="huntRED®")
            default_bu = await sync_to_async(lambda: default_bu.first())()
            if default_bu:
                return default_bu.id
            return None
        
        best_bu_id = max(scores, key=scores.get)
        logger.info(f"Unidad asignada: {best_bu_id} para '{job_title}' con puntuación {max_score}")
        return best_bu_id
    
    except Exception as e:
        logger.error(f"Error al asignar unidad de negocio: {e}")
        # Intentar obtener huntRED por defecto
        try:
            default_bu = await sync_to_async(BusinessUnit.objects.filter)(name="huntRED®")
            default_bu = await sync_to_async(lambda: default_bu.first())()
            if default_bu:
                return default_bu.id
        except:
            pass
        return None

async def save_vacancy(self, job_data: Dict, business_unit: BusinessUnit = None) -> bool:
    """Guarda una vacante en la base de datos"""
    try:
        # Validar que tenemos los datos necesarios
        if not job_data or not isinstance(job_data, dict):
            logger.warning("job_data es None o no es un diccionario")
            return False
        
        # Validar campos requeridos
        if not job_data.get("titulo") or not job_data.get("url_original"):
            logger.warning(f"Faltan campos requeridos para la vacante {job_data.get('titulo', 'Unknown')}")
            return False
        
        # Determinar empresa basada en URL o fuente
        empresa_name = "Desconocido"
        if job_data.get("is_linkedin"):
            empresa_name = "LinkedIn"
        elif job_data.get("is_santander"):
            empresa_name = "Santander"
        elif job_data.get("is_honeywell"):
            empresa_name = "Honeywell"
        elif job_data.get("source"):
            empresa_name = job_data["source"].capitalize()
        
        # Crear o actualizar el Worker
        worker, created = await sync_to_async(Worker.objects.get_or_create)(
            name=empresa_name,
            defaults={
                "company": empresa_name,
                "job_description": job_data.get("descripcion", "")[:1000] if job_data.get("descripcion") else "",
                "address": job_data.get("ubicacion", "")[:200] if job_data.get("ubicacion") else "",
                "required_skills": ", ".join(job_data.get("skills_required", []))[:500],
                "job_type": job_data.get("modalidad", "")[:50] if job_data.get("modalidad") else None
            }
        )
        
        # Truncar datos para evitar errores de longitud
        truncated_data = {
            "titulo": job_data.get("titulo", "")[:300],
            "empresa": worker,
            "ubicacion": job_data.get("ubicacion", "")[:300],
            "descripcion": job_data.get("descripcion", "")[:3000] if job_data.get("descripcion") else "",
            "modalidad": job_data.get("modalidad", "")[:20] if job_data.get("modalidad") else None,
            "requisitos": job_data.get("requisitos", "")[:1000] if job_data.get("requisitos") else "",
            "beneficios": job_data.get("beneficios", "")[:1000] if job_data.get("beneficios") else "",
            "skills_required": job_data.get("skills_required", []),
            "business_unit": business_unit,
            "fecha_publicacion": job_data.get("fecha_publicacion", timezone.now()),
            "activa": True,
            "salario": job_data.get("salario", None)  # Asegurar que siempre existe la clave
        }
        
        # Crear o actualizar la Vacante
        vacante, created = await sync_to_async(Vacante.objects.get_or_create)(
            url_original=job_data["url_original"],
            defaults=truncated_data
        )
        
        if not created:
            # Actualizar campos con datos nuevos solo si es necesario
            for field, value in truncated_data.items():
                if getattr(vacante, field) != value and value:  # Solo actualizar si hay valor nuevo
                    setattr(vacante, field, value)
            await sync_to_async(vacante.save)()
        
        action = "creada" if created else "actualizada"
        logger.info(f"✅ Vacante {action}: {vacante.titulo} | Empresa: {worker.name}")
        
        # Actualizar estadísticas
        self.stats["vacantes_guardadas"] += 1
        
        return True
        
    except Exception as e:
        logger.error(f"Error al guardar vacante {job_data.get('titulo', 'Unknown')}: {e}")
        return False 