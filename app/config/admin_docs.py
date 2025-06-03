# Ubicación del archivo: /home/pablo/app/config/admin_docs.py
"""
Generador de documentación automática para clases de administración.

Este módulo genera documentación detallada sobre todas las clases
de administración registradas en el sistema, siguiendo las reglas
globales de Grupo huntRED®.
"""
import os
import logging
import inspect
from django.urls import reverse
from django.db import models
import textwrap

# Importando configuración centralizada de admin
from app.ats.config.admin_registry import ADMIN_CLASS_MAPPING

logger = logging.getLogger(__name__)

def format_attribute_value(value):
    """Formateando valor de atributo para documentación."""
    if callable(value):
        return "Método/Función"
    elif isinstance(value, (list, tuple)):
        if len(value) > 5:
            return f"Lista con {len(value)} elementos: {value[:5]}..."
        return f"Lista: {value}"
    elif isinstance(value, dict):
        if len(value) > 5:
            items = list(value.items())[:5]
            return f"Diccionario con {len(value)} elementos: {items}..."
        return f"Diccionario: {value}"
    else:
        return str(value)

def generate_model_fields_docs(model):
    """Generando documentación de campos del modelo."""
    fields_doc = []
    fields_doc.append("### Campos del Modelo:")
    
    for field in model._meta.fields:
        field_type = type(field).__name__
        field_attrs = []
        
        # Atributos comunes a documentar
        if field.primary_key:
            field_attrs.append("primary_key=True")
        if field.unique:
            field_attrs.append("unique=True")
        if field.null:
            field_attrs.append("null=True")
        if field.blank:
            field_attrs.append("blank=True")
        if hasattr(field, 'max_length') and field.max_length:
            field_attrs.append(f"max_length={field.max_length}")
        if hasattr(field, 'default') and field.default != models.fields.NOT_PROVIDED:
            default_value = field.default() if callable(field.default) else field.default
            field_attrs.append(f"default={default_value}")
        
        # Formateando documentación
        fields_doc.append(f"- **{field.name}** ({field_type}): {', '.join(field_attrs)}")
    
    return "\n".join(fields_doc)

def generate_admin_attributes_docs(admin_class):
    """Generando documentación de atributos de clase admin."""
    attributes_doc = []
    attributes_doc.append("### Atributos de Administración:")
    
    for attr_name, attr_value in admin_class.__dict__.items():
        # Filtrando atributos privados y especiales
        if attr_name.startswith('_') or inspect.ismethod(attr_value) or inspect.isfunction(attr_value):
            continue
            
        # Documentando atributos importantes
        if attr_name in ['list_display', 'list_filter', 'search_fields', 'readonly_fields', 
                         'fieldsets', 'actions', 'ordering', 'date_hierarchy', 'list_editable']:
            formatted_value = format_attribute_value(attr_value)
            attributes_doc.append(f"- **{attr_name}**: {formatted_value}")
    
    return "\n".join(attributes_doc)

def generate_admin_methods_docs(admin_class):
    """Generando documentación de métodos de clase admin."""
    methods_doc = []
    methods_doc.append("### Métodos de Administración:")
    
    # Obteniendo métodos de la clase
    methods = inspect.getmembers(admin_class, predicate=inspect.isfunction)
    
    for method_name, method in methods:
        # Filtrando métodos privados y especiales
        if method_name.startswith('_') or method_name in ['__init__', '__new__', '__str__', '__repr__']:
            continue
            
        # Obteniendo docstring
        doc = inspect.getdoc(method)
        docstring = f": {textwrap.shorten(doc, width=80)}" if doc else ""
        
        # Generando firma del método
        try:
            signature = str(inspect.signature(method))
        except ValueError:
            signature = "()"
            
        methods_doc.append(f"- **{method_name}{signature}**{docstring}")
    
    return "\n".join(methods_doc)

def generate_admin_documentation(output_dir="docs/admin"):
    """
    Genera documentación automática para todas las clases admin registradas.
    
    Args:
        output_dir (str): Directorio donde se guardará la documentación.
                         Por defecto es "docs/admin".
    
    Returns:
        bool: True si la generación fue exitosa, False en caso contrario.
    """
    try:
        # Creando directorio si no existe
        os.makedirs(output_dir, exist_ok=True)
        
        # Archivo índice
        index_content = ["# Documentación de Administración\n"]
        index_content.append("## Modelos Registrados\n")
        
        # Generando documentación para cada modelo
        for model, admin_class in ADMIN_CLASS_MAPPING.items():
            model_name = model.__name__
            admin_name = admin_class.__name__
            
            logger.info(f"Generando documentación para {model_name} con {admin_name}")
            index_content.append(f"- [{model_name}]({model_name}.md): administrado por {admin_name}")
            
            # Contenido del archivo específico
            model_doc = [f"# Administración de {model_name}\n"]
            
            # Descripción del admin
            admin_doc = inspect.getdoc(admin_class)
            if admin_doc:
                model_doc.append(f"## Descripción\n{admin_doc}\n")
            
            # Documentación del modelo
            model_doc.append("## Modelo\n")
            model_doc.append(f"Nombre: `{model.__module__}.{model.__name__}`\n")
            model_doc.append(generate_model_fields_docs(model))
            
            # Documentación de la clase admin
            model_doc.append("\n## Clase de Administración\n")
            model_doc.append(f"Nombre: `{admin_class.__module__}.{admin_class.__name__}`\n")
            model_doc.append(generate_admin_attributes_docs(admin_class))
            model_doc.append("\n")
            model_doc.append(generate_admin_methods_docs(admin_class))
            
            # Enlaces a otras clases relacionadas
            model_doc.append("\n## Clases Relacionadas\n")
            base_classes = [cls.__name__ for cls in admin_class.__mro__[1:-1] 
                           if cls.__name__ not in ['object', 'ModelAdmin']]
            if base_classes:
                model_doc.append(f"Hereda de: {', '.join(base_classes)}")
            
            # Guardando archivo específico
            with open(os.path.join(output_dir, f"{model_name}.md"), "w") as f:
                f.write("\n".join(model_doc))
        
        # Guardando índice
        with open(os.path.join(output_dir, "index.md"), "w") as f:
            f.write("\n".join(index_content))
        
        logger.info(f"Documentación admin generada exitosamente en {output_dir}")
        return True
        
    except Exception as e:
        logger.error(f"Error generando documentación: {str(e)}")
        return False

def generate_console_documentation():
    """
    Genera documentación de admin en la consola para depuración.
    Esta función es útil para desarrollo y pruebas.
    """
    for model, admin_class in ADMIN_CLASS_MAPPING.items():
        print(f"\n{'='*80}")
        print(f"MODELO: {model.__name__}")
        print(f"ADMIN: {admin_class.__name__}")
        print(f"{'='*80}")
        
        # Descripción
        doc = inspect.getdoc(admin_class)
        if doc:
            print(f"\nDESCRIPCIÓN:\n{doc}")
        
        # Atributos principales
        for attr in ['list_display', 'list_filter', 'search_fields', 'readonly_fields']:
            if hasattr(admin_class, attr):
                value = getattr(admin_class, attr)
                print(f"\n{attr.upper()}: {value}")
        
        print("\nMÉTODOS PERSONALIZADOS:")
        methods = [name for name, method in inspect.getmembers(admin_class, predicate=inspect.isfunction) 
                  if not name.startswith('_') and name not in ['get_urls']]
        for method_name in methods:
            print(f"- {method_name}")
        
        print(f"\n{'-'*80}\n")

if __name__ == "__main__":
    # Ejecución directa para pruebas
    generate_console_documentation()
