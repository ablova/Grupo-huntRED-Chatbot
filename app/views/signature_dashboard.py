"""
Dashboard centralizado para el seguimiento y gestión de firmas electrónicas.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.http import JsonResponse
from django.db.models import Q
from datetime import datetime, timedelta

from app.models import (
    InternalDocumentSignature,
    ConsentAgreement,
    Proposal,
    Contract
)
from app.ats.utils.signature.digital_signature_providers import get_signature_provider
from app.ats.utils.signature.blockchain import BlockchainSignature
from app.ats.utils.signature.biometric import AdvancedBiometricValidation

@method_decorator(login_required, name='dispatch')
class SignatureDashboardView(View):
    """
    Vista principal del dashboard de firmas.
    """
    template_name = 'dashboard/signature_dashboard.html'

    def get(self, request):
        context = self._get_dashboard_context(request)
        return render(request, self.template_name, context)

    def _get_dashboard_context(self, request):
        """Obtiene el contexto para el dashboard."""
        # Obtener documentos pendientes de firma
        pending_documents = self._get_pending_documents(request.user)
        
        # Obtener estadísticas
        stats = self._get_signature_stats(request.user)
        
        # Obtener actividad reciente
        recent_activity = self._get_recent_activity(request.user)
        
        return {
            'pending_documents': pending_documents,
            'stats': stats,
            'recent_activity': recent_activity,
            'blockchain_status': self._get_blockchain_status(),
            'biometric_status': self._get_biometric_status()
        }

    def _get_pending_documents(self, user):
        """Obtiene documentos pendientes de firma."""
        return {
            'internal_documents': InternalDocumentSignature.objects.filter(
                Q(creator=user) | Q(reviewer=user),
                status__in=['pending', 'signed_by_creator']
            ),
            'consent_agreements': ConsentAgreement.objects.filter(
                Q(creator=user) | Q(invitee=user),
                status__in=['pending', 'pending_review']
            ),
            'proposals': Proposal.objects.filter(
                Q(creator=user) | Q(reviewer=user),
                status__in=['pending', 'review']
            ),
            'contracts': Contract.objects.filter(
                Q(creator=user) | Q(reviewer=user),
                status__in=['pending', 'review']
            )
        }

    def _get_signature_stats(self, user):
        """Obtiene estadísticas de firmas."""
        today = datetime.now()
        last_week = today - timedelta(days=7)
        
        return {
            'total_pending': self._count_pending_documents(user),
            'signed_today': self._count_signed_documents(user, today),
            'signed_this_week': self._count_signed_documents(user, last_week),
            'average_response_time': self._calculate_average_response_time(user)
        }

    def _get_recent_activity(self, user):
        """Obtiene actividad reciente de firmas."""
        return {
            'recent_signatures': self._get_recent_signatures(user),
            'pending_approvals': self._get_pending_approvals(user),
            'expiring_soon': self._get_expiring_documents(user)
        }

    def _get_blockchain_status(self):
        """Obtiene el estado de la blockchain."""
        blockchain = BlockchainSignature()
        return {
            'is_active': blockchain.is_active(),
            'last_block': blockchain.get_last_block(),
            'total_transactions': blockchain.get_total_transactions()
        }

    def _get_biometric_status(self):
        """Obtiene el estado de la validación biométrica."""
        biometric = AdvancedBiometricValidation()
        return {
            'is_active': biometric.is_active(),
            'validation_methods': biometric.get_available_methods(),
            'success_rate': biometric.get_success_rate()
        }

    def _count_pending_documents(self, user):
        """Cuenta documentos pendientes."""
        return sum(len(docs) for docs in self._get_pending_documents(user).values())

    def _count_signed_documents(self, user, since_date):
        """Cuenta documentos firmados desde una fecha."""
        return InternalDocumentSignature.objects.filter(
            Q(creator=user) | Q(reviewer=user),
            status='completed',
            updated_at__gte=since_date
        ).count()

    def _calculate_average_response_time(self, user):
        """Calcula el tiempo promedio de respuesta."""
        # Implementar cálculo de tiempo promedio
        return timedelta(hours=24)

    def _get_recent_signatures(self, user):
        """Obtiene firmas recientes."""
        return InternalDocumentSignature.objects.filter(
            Q(creator=user) | Q(reviewer=user),
            status='completed'
        ).order_by('-updated_at')[:5]

    def _get_pending_approvals(self, user):
        """Obtiene aprobaciones pendientes."""
        return InternalDocumentSignature.objects.filter(
            reviewer=user,
            status='signed_by_creator'
        ).order_by('-created_at')[:5]

    def _get_expiring_documents(self, user):
        """Obtiene documentos próximos a expirar."""
        return InternalDocumentSignature.objects.filter(
            Q(creator=user) | Q(reviewer=user),
            status__in=['pending', 'signed_by_creator'],
            token_expiry__lte=datetime.now() + timedelta(days=7)
        ).order_by('token_expiry')[:5] 