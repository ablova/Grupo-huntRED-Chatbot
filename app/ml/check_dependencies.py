#!/usr/bin/env python3
import os
import sys
import tensorflow as tf
import spacy
import nltk
from django.conf import settings

def check_ml_dependencies():
    errors = []
    
    # Verificar TensorFlow
    try:
        tf_version = tf.__version__
        print(f"✅ TensorFlow {tf_version} instalado correctamente")
    except Exception as e:
        errors.append(f"❌ Error con TensorFlow: {e}")
    
    # Verificar modelos spaCy
    try:
        spacy.load("es_core_news_sm")
        print("✅ Modelo spaCy español cargado correctamente")
    except Exception as e:
        errors.append(f"❌ Error con spaCy: {e}")
    
    # Verificar NLTK
    try:
        nltk.data.find('tokenizers/punkt')
        print("✅ Datos NLTK encontrados")
    except Exception as e:
        errors.append(f"❌ Error con NLTK: {e}")
    
    # Verificar directorios de modelos
    ml_dir = settings.ML_MODELS_DIR
    if not os.path.exists(ml_dir):
        errors.append(f"❌ Directorio de modelos no encontrado: {ml_dir}")
    
    if errors:
        print("\nErrores encontrados:")
        for error in errors:
            print(error)
        sys.exit(1)
    
    print("\n✅ Todas las dependencias están correctamente configuradas")

if __name__ == "__main__":
    check_ml_dependencies() 