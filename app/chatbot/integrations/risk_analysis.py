# /home/pablo/app/chatbot/integrations/risk_analysis.py
#
# Módulo para analizar riesgos y consistencia en perfiles de candidatos.
# Implementa métricas y análisis para evaluar la confiabilidad de los datos.
# Optimizado para bajo uso de CPU, escalabilidad, y robustez frente a fallos.

import re
from typing import Dict, Any, Optional
from app.models import Candidate

class RiskAnalysis:
    def __init__(self, candidate: Candidate):
        self.candidate = candidate
        self.risk_score = 0
        self.risk_factors = []
        
    def analyze_consistency(self) -> Dict:
        """Analiza la consistencia en los datos proporcionados"""
        inconsistencies = []
        
        # Verificar consistencia en nombres
        if self.candidate.nombre and self.candidate.apellido_paterno:
            if not re.match(r'^[A-Za-záéíóúÁÉÍÓÚñÑ\s]+$', self.candidate.nombre):
                inconsistencies.append('Nombre contiene caracteres no válidos')
            if not re.match(r'^[A-Za-záéíóúÁÉÍÓÚñÑ\s]+$', self.candidate.apellido_paterno):
                inconsistencies.append('Apellido paterno contiene caracteres no válidos')
        
        # Verificar consistencia en fecha de nacimiento
        if self.candidate.fecha_nacimiento:
            age = (datetime.now().date() - self.candidate.fecha_nacimiento).days / 365
            if age < 18 or age > 70:
                inconsistencies.append('Edad fuera de rango permitido')
                
        return {
            'inconsistencias': inconsistencies,
            'score': len(inconsistencias) * 10
        }
        
    def analyze_public_records(self) -> Dict:
        """Realiza una búsqueda básica en registros públicos"""
        # Implementar búsqueda en registros públicos
        # Esta es una implementación básica que podría expandirse
        public_records = []
        
        # Verificar si el email está en listas de spam
        if self.candidate.email:
            if self._check_spam_list(self.candidate.email):
                public_records.append('Email en lista de spam')
                
        return {
            'registros_publicos': public_records,
            'score': len(public_records) * 20
        }
        
    def analyze_behavioral_risk(self) -> Dict:
        """Analiza riesgos basados en comportamiento"""
        risks = []
        
        # Verificar patrones de comportamiento sospechosos
        if self.candidate.phone:
            if self._check_phone_pattern(self.candidate.phone):
                risks.append('Patrón de teléfono sospechoso')
                
        return {
            'riesgos_comportamiento': risks,
            'score': len(risks) * 15
        }
        
    def get_overall_risk_score(self) -> Dict:
        """Calcula el puntaje de riesgo general"""
        consistency = self.analyze_consistency()
        public_records = self.analyze_public_records()
        behavioral = self.analyze_behavioral_risk()
        
        self.risk_score = consistency['score'] + public_records['score'] + behavioral['score']
        
        return {
            'consistencia': consistency,
            'registros_publicos': public_records,
            'riesgos_comportamiento': behavioral,
            'puntaje_total': self.risk_score,
            'nivel_riesgo': self._get_risk_level()
        }
        
    def _get_risk_level(self) -> str:
        """Determina el nivel de riesgo basado en el puntaje"""
        if self.risk_score >= 70:
            return 'Alto'
        elif self.risk_score >= 40:
            return 'Medio'
        else:
            return 'Bajo'
            
    def _check_spam_list(self, email: str) -> bool:
        """Verifica si el email está en listas de spam"""
        # Implementar integración con servicio de verificación de spam
        # Esta es una implementación básica
        return False
        
    def _check_phone_pattern(self, phone: str) -> bool:
        """Verifica patrones de teléfono sospechosos"""
        # Implementar patrones de detección
        suspicious_patterns = [
            r'^\+111',  # Prefijos sospechosos
            r'^\+999',
            r'^\+000'
        ]
        
        for pattern in suspicious_patterns:
            if re.match(pattern, phone):
                return True
        return False

