# app/ml/aura/matchmaker.py
"""
Módulo puente para exportar NetworkMatchmaker como Matchmaker.
Este archivo sirve como alias para mantener compatibilidad con importaciones existentes.
"""

from app.ml.aura.networking.network_matchmaker import NetworkMatchmaker

# Crear alias para NetworkMatchmaker
Matchmaker = NetworkMatchmaker

# Exportar la instancia global para uso directo
matchmaker = NetworkMatchmaker()

__all__ = ['Matchmaker', 'matchmaker']
