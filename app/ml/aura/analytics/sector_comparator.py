"""
AURA - Sector Comparator
Comparativa sectorial de red y skills (deshabilitado por defecto)
"""

ENABLED = False

class SectorComparator:
    def __init__(self):
        self.enabled = ENABLED
    def compare(self, user_id, sector):
        pass

sector_comparator = SectorComparator() 