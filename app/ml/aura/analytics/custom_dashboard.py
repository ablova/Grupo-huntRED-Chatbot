"""
AURA - Custom Dashboard
Dashboard personalizable por usuario/empresa (deshabilitado por defecto)
"""

ENABLED = False

class CustomDashboard:
    def __init__(self):
        self.enabled = ENABLED
    def get_dashboard(self, user_id):
        pass

custom_dashboard = CustomDashboard() 