# Ubicacion SEXSI -- /home/pablollh/app/sexsi/admin.py

from django.contrib import admin
from app.sexsi.models import ConsentAgreement, PaymentTransaction, SexsiConfig

@admin.register(ConsentAgreement)
class ConsentAgreementAdmin(admin.ModelAdmin):
    list_display = ('id', 'creator', 'date_created', 'signature_method', 'is_signed_by_creator', 'is_signed_by_invitee')
    list_filter = ('signature_method', 'is_signed_by_creator', 'is_signed_by_invitee')
    search_fields = ('creator__username', 'invitee_contact',)
    change_list_template = "admin/consentagreement_change_list.html"
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        # Agrupamos las operaciones según el estado:
        operations_by_status = {
            "Pendiente": self.model.objects.filter(is_signed_by_creator=False, is_signed_by_invitee=False),
            "Firmado por Creador": self.model.objects.filter(is_signed_by_creator=True, is_signed_by_invitee=False),
            "Firmado por Invitado": self.model.objects.filter(is_signed_by_creator=False, is_signed_by_invitee=True),
            "Completado": self.model.objects.filter(is_signed_by_creator=True, is_signed_by_invitee=True),
        }
        extra_context['operations_by_status'] = operations_by_status
        return super().changelist_view(request, extra_context=extra_context)