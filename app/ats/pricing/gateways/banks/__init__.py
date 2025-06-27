"""
Gateways bancarios para pagos y cobros bidireccionales.
"""
from .bbva import BBVAGateway
from .santander import SantanderGateway
from .banamex import BanamexGateway
from .banorte import BanorteGateway

__all__ = [
    'BBVAGateway',
    'SantanderGateway', 
    'BanamexGateway',
    'BanorteGateway',
] 