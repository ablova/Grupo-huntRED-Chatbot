# /home/pablo/app/sexsi/import_config.py
#
# NOTA: Este archivo está obsoleto y se mantiene temporalmente para compatibilidad.
# El registro de módulos ahora es gestionado automáticamente por ModuleRegistry en app/module_registry.py
# Ver MEMORY[3c0a8858-351a-4fd1-85d8-615be684afab]
#
# De acuerdo con las reglas globales de Grupo huntRED®:
# - No Redundancies: Se evitan duplicaciones en el código
# - Code Consistency: Se siguen estándares de Django
# - Modularity: Se usa código modular y reusable

# La nueva forma de registrar módulos es a través de ModuleRegistry:
# from app.module_registry import module_registry
# module_registry.register_module('contract_generator', 'app.sexsi.contract_generator.ContractGenerator')

# Estas llamadas a register_module ya no son necesarias, el registro es automático

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
