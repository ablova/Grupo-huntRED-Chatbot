# /home/amigro/app/gpt.py
import requests
import json
import os
import openai
import logging

#openai.organization = "org-B19vTHzNZ5FIuzsFOgDmisDi"
#openai.api_key = os.getenv("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")
#openai.api_key = "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"
#openai.Model.list()
logger = logging.getLogger(__name__)

def gpt_message(api_token, text, model):
    """
    Genera una respuesta utilizando la API de OpenAI GPT.

    Args:
        api_token (str): El token de autenticación para la API de OpenAI.
        text (str): El texto de entrada para el modelo.
        model (str): El modelo a utilizar (por ejemplo, 'gpt-3.5-turbo').

    Returns:
        dict: La respuesta de la API de OpenAI.

    Raises:
        Exception: Si ocurre un error al llamar a la API.
    """
    try:
        openai.api_key = api_token

        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "user", "content": text}
            ]
        )
        return response
    except Exception as e:
        logger.error(f"Error al llamar a la API de OpenAI: {e}", exc_info=True)
        raise e  # Re-lanzar la excepción para que pueda ser manejada por el llamador

if __name__ == "__main__":
    # No incluyas tu API Key directamente en el código
    api_token = "TU_API_KEY_AQUÍ"
    text = "Formúleme la siguiente pregunta de una manera realista..."
    model = "gpt-3.5-turbo"

    response = gpt_message(api_token, text, model)
    print(response)