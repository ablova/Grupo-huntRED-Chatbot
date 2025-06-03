# Ubicacion SEXSI -- /home/pablo/app/sexsi/admin.py

from django.contrib import admin
from app.models import ConsentAgreement, PaymentTransaction, SexsiConfig, DiscountCoupon, Preference, AgreementPreference

@admin.register(ConsentAgreement)
class ConsentAgreementAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'creator', 'date_created', 'signature_method', 'is_signed_by_creator', 'is_signed_by_invitee', 'tos_accepted')
    list_filter = ('status', 'signature_method', 'is_signed_by_creator', 'is_signed_by_invitee', 'tos_accepted')
    search_fields = ('creator__username', 'invitee_contact',)
    change_list_template = "admin/consentagreement_change_list.html"
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        operations_by_status = {
            "Pendiente": self.model.objects.filter(is_signed_by_creator=False, is_signed_by_invitee=False),
            "Firmado por Anfitrión": self.model.objects.filter(is_signed_by_creator=True, is_signed_by_invitee=False),
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
