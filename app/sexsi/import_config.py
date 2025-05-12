from typing import Any, Callable
from app.import_config import register_module

# Register SEXSI modules at startup
register_module('contract_generator', 'app.sexsi.contract_generator.ContractGenerator')
register_module('contract_validator', 'app.sexsi.contract_validator.ContractValidator')
register_module('sexsi_payment_processor', 'app.sexsi.payment_processor.SEXSIPaymentProcessor')
register_module('contract_manager', 'app.sexsi.contract_manager.ContractManager')
register_module('signature_handler', 'app.sexsi.signature_handler.SignatureHandler')
register_module('contract_analyzer', 'app.sexsi.contract_analyzer.ContractAnalyzer')
register_module('contract_template_manager', 'app.sexsi.contract_template_manager.ContractTemplateManager')
register_module('contract_history', 'app.sexsi.contract_history.ContractHistory')

def get_contract_generator():
    """Get ContractGenerator instance."""
    from app.sexsi.contract_generator import ContractGenerator
    return ContractGenerator

def get_contract_validator():
    """Get ContractValidator instance."""
    from app.sexsi.contract_validator import ContractValidator
    return ContractValidator

def get_payment_processor():
    """Get SEXSIPaymentProcessor instance."""
    from app.sexsi.payment_processor import SEXSIPaymentProcessor
    return SEXSIPaymentProcessor

def get_contract_manager():
    """Get ContractManager instance."""
    from app.sexsi.contract_manager import ContractManager
    return ContractManager

def get_signature_handler():
    """Get SignatureHandler instance."""
    from app.sexsi.signature_handler import SignatureHandler
    return SignatureHandler

def get_contract_analyzer():
    """Get ContractAnalyzer instance."""
    from app.sexsi.contract_analyzer import ContractAnalyzer
    return ContractAnalyzer

def get_contract_template_manager():
    """Get ContractTemplateManager instance."""
    from app.sexsi.contract_template_manager import ContractTemplateManager
    return ContractTemplateManager

def get_contract_history():
    """Get ContractHistory instance."""
    from app.sexsi.contract_history import ContractHistory
    return ContractHistory
