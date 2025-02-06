# Ubicacion SEXSI -- /home/pablollh/app/sexsi/admin.py

from django.contrib import admin
from app.sexsi.models import ConsentAgreement, PaymentTransaction, SexsiConfig

@admin.register(ConsentAgreement)
class ConsentAgreementAdmin(admin.ModelAdmin):
    list_display = ('id', 'creator', 'date_created', 'signature_method', 'is_signed_by_creator', 'is_signed_by_invitee', 'tos_accepted')
    list_filter = ('signature_method', 'is_signed_by_creator', 'is_signed_by_invitee', 'tos_accepted')
    search_fields = ('creator__username', 'invitee_contact',)
    change_list_template = "admin/consentagreement_change_list.html"
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        operations_by_status = {
            "Pendiente": self.model.objects.filter(is_signed_by_creator=False, is_signed_by_invitee=False),
            "Firmado por Creador": self.model.objects.filter(is_signed_by_creator=True, is_signed_by_invitee=False),
            "Firmado por Invitado": self.model.objects.filter(is_signed_by_creator=False, is_signed_by_invitee=True),
            "Completado": self.model.objects.filter(is_signed_by_creator=True, is_signed_by_invitee=True),
        }
        extra_context['operations_by_status'] = operations_by_status
        return super().changelist_view(request, extra_context=extra_context)

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'agreement', 'signature_method', 'transaction_status', 'amount', 'created_at')
    list_filter = ('signature_method', 'transaction_status')
    search_fields = ('agreement__id', 'paypal_transaction_id')

@admin.register(SexsiConfig)
class SexsiConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'hellosign_api_key', 'paypal_client_id')
    search_fields = ('name',)
