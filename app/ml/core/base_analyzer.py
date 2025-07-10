# app/ml/core/base_analyzer.py
"""
Redirección para mantener compatibilidad con imports en el sistema.

Este módulo importa BaseAnalyzer desde app.ml.analyzers.base_analyzer 
para mantener compatibilidad con el código que lo importa desde app.ml.core.base_analyzer.
Se mantiene una única fuente de verdad (app.ml.analyzers.base_analyzer) para evitar duplicación.
"""

# Importamos desde la ubicación original
from app.ml.analyzers.base_analyzer import BaseAnalyzer

# Exportamos BaseAnalyzer para mantener compatibilidad con imports existentes
# No se requieren más exportaciones aquí
