#/home/amigro/app/Event.py

import json
import os
import os.path as path
from typing import Dict, List, Tuple, Any
from django.conf import settings
from app.models import Pregunta, Buttons, SubPregunta
from app.singleton import singleton
import logging

# Inicializa el logger
logger = logging.getLogger('event')

#@singleton  # Si necesitas que sea singleton, descomenta esta línea.
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
        interact = cls.initialize(Pregunta.objects.all()) if not cls.valid(user_id) else cls.read_json(user_id)

        # Refactoriza para manejar preguntas y sub-preguntas de forma separada
        for key, value in interact.items():
            if not value["response"]:
                value["response"] = user_response
                break
            for sub_preguntas in value["sub_pregunta"].values():
                for sub_pregunta in sub_preguntas:
                    if not sub_pregunta["response"]:
                        logger.info(f"SubPregunta: {sub_pregunta['request']}")
                        sub_pregunta["response"] = user_response
                        cls.write_json(user_id, interact)
                        return

        cls.write_json(user_id, interact)

    @classmethod
    def clear(cls, user_id: str) -> None:
        """
        Limpia los datos del usuario.
        """
        logger.info(f"Limpieza de datos para usuario {user_id}")
        interact = cls.read_json(user_id)
        if interact:
            interact.pop(next(iter(interact)))
            cls.write_json(user_id, interact)

    @classmethod
    def clear_all(cls) -> None:
        """
        Limpia todos los datos de todos los usuarios.
        """
        logger.warning("Limpieza de todos los datos de los usuarios.")
        media_dir = os.path.join(settings.MEDIA_ROOT)
        for filename in os.listdir(media_dir):
            if filename.endswith('.json'):
                os.remove(os.path.join(media_dir, filename))

    @classmethod
    def valid(cls, user_id: str) -> bool:
        """
        Verifica si existen datos para el usuario.
        """
        return path.exists(os.path.join(settings.MEDIA_ROOT, f"{user_id}.json"))

    @classmethod
    def valid_response(cls, user_id: str) -> Tuple[str, List[Dict[str, str]], str]:
        """
        Obtiene la respuesta válida para el usuario.
        """
        request, _button, p = "", [], ""
        interact = cls.read_json(user_id)
        for p, value in interact.items():
            if not value["response"]:
                return value["request"], value["buttons"], p
            for sub_preguntas in value["sub_pregunta"].values():
                for sp_data in sub_preguntas:
                    logger.info(f"SubPregunta: {sp_data['request']}")
                    if not sp_data["response"]:
                        return sp_data["request"], sp_data["buttons"], p
        return request, _button, p

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
    def initialize(cls, preguntas: List[Pregunta]) -> Dict[str, Any]:
        """
        Inicializa los datos del usuario.
        """
        logger.info(f"Inicializando datos de usuario con {len(preguntas)} preguntas.")
        interact = {"init": {"request": "init", "response": "", "valid": "", "yes_or_not": "", "buttons": [], "sub_pregunta": {}}}
        for p in preguntas:
            buttons = [{"title": str(button.name), "id": str(button.id)} for button in Buttons.objects.filter(pregunta=p)]
            sub_pregunta_data = cls.build_subpreguntas(p)
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
    def build_subpreguntas(pregunta: Pregunta) -> Dict[str, Any]:
        """
        Crea la estructura de subpreguntas para una pregunta.
        """
        sub_pregunta_data = {}
        for sec in SubPregunta.objects.filter(pregunta=pregunta):
            buttons_sub = [{"title": str(button.name), "id": str(button.id)} for button in Buttons.objects.filter(sub_pregunta=sec)]
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
    def rename_file(cls, user_id: str) -> None:
        """
        Renombra el archivo JSON del usuario.
        """
        old_name = os.path.join(settings.MEDIA_ROOT, f"{user_id}.json")
        for i in range(20):
            new_name = os.path.join(settings.MEDIA_ROOT, f"{user_id}-{i}.json")
            if not path.exists(new_name):
                os.rename(old_name, new_name)
                logger.info(f"Archivo JSON renombrado para el usuario {user_id}")
                break

    @classmethod
    def valid_full(cls, data: Dict[str, Any]) -> bool:
        """
        Verifica si todos los datos del usuario están completos.
        """
        return all(value["response"] for key, value in data.items() if key != "end")
