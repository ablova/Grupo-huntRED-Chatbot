# /home/pablo/ai_huntred/wsgi.py
"""
WSGI config for ai_huntred project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/wsgi/
"""
import os
from django.core.wsgi import get_wsgi_application
import tensorflow as tf
tf.config.set_visible_devices([], 'GPU')
logger.info("TensorFlow configurado para usar solo CPU.")

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_huntred.settings')

application = get_wsgi_application()
