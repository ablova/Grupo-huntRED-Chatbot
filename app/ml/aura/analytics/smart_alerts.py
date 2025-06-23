"""
AURA - Smart Alerts
Alertas inteligentes y proactivas (deshabilitado por defecto)
"""

ENABLED = False

class SmartAlerts:
    def __init__(self):
        self.enabled = ENABLED
    def get_alerts(self, user_id):
        pass

smart_alerts = SmartAlerts() 