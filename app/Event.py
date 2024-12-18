# /home/pablollh/app/Event.py

import json
import os
from typing import Dict, List, Tuple, Any
from django.conf import settings
from app.singleton import singleton
import logging

# Configuración del logger
logger = logging.getLogger('event')

@singleton
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
        cls.set_user_response(user_id, user_response)

    @classmethod
    def clear(cls, user_id: str) -> None:
        """
        Limpia los datos del usuario.
        """
        logger.info(f"Limpieza de datos para usuario {user_id}")
        file_path = os.path.join(settings.MEDIA_ROOT, f"{user_id}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Datos eliminados para el usuario {user_id}")

    @classmethod
    def clear_all(cls) -> None:
        """
        Limpia todos los datos de todos los usuarios.
        """
        logger.warning("Limpieza de todos los datos de los usuarios.")
        media_dir = settings.MEDIA_ROOT
        for filename in os.listdir(media_dir):
            if filename.endswith('.json'):
                os.remove(os.path.join(media_dir, filename))

    @classmethod
    def valid(cls, user_id: str) -> bool:
        """
        Verifica si existen datos para el usuario.
        """
        return os.path.exists(os.path.join(settings.MEDIA_ROOT, f"{user_id}.json"))

    
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
    def write_json(cls, user_id: str, data: Dict[str, Any]) -> None:
        """
        Escribe los datos del usuario en un archivo JSON.
        """
        file_path = os.path.join(settings.MEDIA_ROOT, f"{user_id}.json")
        with open(file_path, "w") as file:
            json.dump(data, file, indent=2)

    @classmethod
    def valid_full(cls, data: Dict[str, Any]) -> bool:
        """
        Verifica si todos los datos del usuario están completos.
        """
        return all(value.get("response") for key, value in data.items() if key != "end")
    
    @classmethod
    def handle_file_error(cls, file_path: str, operation: str):
        """
        Manejo centralizado de errores de archivo.
        """
        logger.error(f"Error durante {operation} en {file_path}. Verifica permisos o formato.")