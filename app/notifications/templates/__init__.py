"""Módulo de plantillas de notificaciones."""

from app.imports import imports

# Registrar los módulos para importación perezosa
imports.add_lazy_module('base', 'app.notifications.templates.base')
imports.add_lazy_module('proposal', 'app.notifications.templates.proposal')
imports.add_lazy_module('payment', 'app.notifications.templates.payment')
imports.add_lazy_module('opportunity', 'app.notifications.templates.opportunity')

__all__ = [
    'BaseTemplate',
    'ProposalTemplate',
    'PaymentTemplate',
    'OpportunityTemplate'
]

# Definir los getters para cada clase
def get_base_template():
    """Obtiene la clase BaseTemplate."""
    return imports.import_from('base', 'BaseTemplate')

def get_proposal_template():
    """Obtiene la clase ProposalTemplate."""
    return imports.import_from('proposal', 'ProposalTemplate')

def get_payment_template():
    """Obtiene la clase PaymentTemplate."""
    return imports.import_from('payment', 'PaymentTemplate')

def get_opportunity_template():
    """Obtiene la clase OpportunityTemplate."""
    return imports.import_from('opportunity', 'OpportunityTemplate')
