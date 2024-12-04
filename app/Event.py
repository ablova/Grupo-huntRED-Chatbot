# /home/amigro/app/Event.py

import json
import os
from typing import Dict, List, Tuple, Any
from django.conf import settings
from app.models import Pregunta, Buttons, SubPregunta
from app.singleton import singleton
import logging

# Configuración del logger
logger = logging.getLogger('event')

@singleton
class PersonData:
    """
    Clase para manejar los datos del usuario utilizando la base de datos.
    """
    @classmethod
    async def get_next_question(cls, user_id: str) -> Tuple[str, List[Dict[str, str]], str]:
        """
        Obtiene la siguiente pregunta pendiente para el usuario.

        :param user_id: ID del usuario.
        :return: Tupla con la pregunta, botones y nombre de la pregunta.
        """
        try:
            interact = cls.read_json(user_id)
            if not interact:
                preguntas = await Pregunta.objects.all().async_all()
                interact = await cls.initialize(preguntas)
                cls.write_json(user_id, interact)
            for key, value in interact.items():
                if not value["response"]:
                    return value["request"], value["buttons"], key
                for sub_preguntas in value["sub_pregunta"].values():
                    for sub_pregunta in sub_preguntas:
                        if not sub_pregunta["response"]:
                            return sub_pregunta["request"], sub_pregunta["buttons"], key
            return "", [], ""
        except Exception as e:
            logger.error(f"Error obteniendo la siguiente pregunta para {user_id}: {e}", exc_info=True)
            return "", [], ""

    @classmethod
    async def set_user_response(cls, user_id: str, user_response: str) -> None:
        """
        Almacena la respuesta del usuario en la base de datos.

        :param user_id: ID del usuario.
        :param user_response: Respuesta proporcionada por el usuario.
        """
        try:
            interact = cls.read_json(user_id)
            if not interact:
                preguntas = await Pregunta.objects.all().async_all()
                interact = await cls.initialize(preguntas)
            for key, value in interact.items():
                if not value["response"]:
                    value["response"] = user_response
                    break
                for sub_preguntas in value["sub_pregunta"].values():
                    for sub_pregunta in sub_preguntas:
                        if not sub_pregunta["response"]:
                            sub_pregunta["response"] = user_response
                            cls.write_json(user_id, interact)
                            return
            cls.write_json(user_id, interact)
        except Exception as e:
            logger.error(f"Error estableciendo respuesta para {user_id}: {e}", exc_info=True)

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
    def valid_response(cls, user_id: str) -> Tuple[str, List[Dict[str, str]], str]:
        """
        Obtiene la respuesta válida para el usuario.
        """
        try:
            interact = cls.read_json(user_id)
            for key, value in interact.items():
                if not value["response"]:
                    return value["request"], value["buttons"], key
                for sub_preguntas in value["sub_pregunta"].values():
                    for sub_pregunta in sub_preguntas:
                        if not sub_pregunta["response"]:
                            return sub_pregunta["request"], sub_pregunta["buttons"], key
            return "", [], ""
        except Exception as e:
            logger.error(f"Error obteniendo respuesta válida para {user_id}: {e}", exc_info=True)
            return "", [], ""

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
    async def initialize(cls, preguntas: List[Pregunta]) -> Dict[str, Any]:
        """
        Inicializa los datos del usuario.
        """
        logger.info(f"Inicializando datos de usuario con {len(preguntas)} preguntas.")
        interact = {}
        for p in preguntas:
            buttons = [{"title": str(button.name), "id": str(button.id)} for button in await Buttons.objects.filter(pregunta=p).async_all()]
            sub_pregunta_data = await cls.build_subpreguntas(p)
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
    async def build_subpreguntas(pregunta: Pregunta) -> Dict[str, Any]:
        """
        Crea la estructura de subpreguntas para una pregunta.
        """
        sub_pregunta_data = {}
        sub_preguntas = await SubPregunta.objects.filter(pregunta=pregunta).async_all()
        for sec in sub_preguntas:
            buttons_sub = [{"title": str(button.name), "id": str(button.id)} for button in await Buttons.objects.filter(sub_pregunta=sec).async_all()]
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
    def valid_full(cls, data: Dict[str, Any]) -> bool:
        """
        Verifica si todos los datos del usuario están completos.
        """
        return all(value["response"] for key, value in data.items() if key != "end")