# app/ats/models/core/business_unit.py
"""Compatibilidad para modelos de Unidad de Negocio.

Este archivo solía contener una definición duplicada de los modelos
`BusinessUnit` y `BusinessUnitMember`.  Para evitar el conflicto de
modelos duplicados en Django, ahora simplemente re-exporta los modelos
canónicos desde `app.models`.

Todas las referencias nuevas deben usar directamente:
    from app.models import BusinessUnit, BusinessUnitMembership

Las referencias heredadas que aún hagan:
    from app.ats.models.core.business_unit import BusinessUnit, BusinessUnitMember
seguirán funcionando gracias a los alias definidos abajo.

Una vez que el código legado sea migrado, este archivo podrá eliminarse.
"""

# Re-exportar el modelo canónico
from app.models import BusinessUnit as BusinessUnit  # noqa: F401

# Alias de compatibilidad para el nombre antiguo `BusinessUnitMember`
from app.models import BusinessUnitMembership as BusinessUnitMember  # noqa: F401 