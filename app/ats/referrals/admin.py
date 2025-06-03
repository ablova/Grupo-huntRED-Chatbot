from django.contrib import admin
from .models import ReferralProgram

@admin.register(ReferralProgram)
class ReferralProgramAdmin(admin.ModelAdmin):
    list_display = ('referrer', 'referred_company', 'referral_code', 'status',
                   'commission_percentage', 'created_at', 'completed_at')
    list_filter = ('status', 'created_at', 'completed_at')
    search_fields = ('referrer__email', 'referred_company', 'referral_code')
    readonly_fields = ('referral_code', 'created_at', 'completed_at')
    fieldsets = (
        ('Información Básica', {
            'fields': ('referrer', 'referred_company', 'referral_code')
        }),
        ('Comisión', {
            'fields': ('commission_percentage',)
        }),
        ('Estado', {
            'fields': ('status', 'created_at', 'completed_at')
        }),
        ('Propuesta', {
            'fields': ('proposal',)
        })
    )

    def has_add_permission(self, request):
        return False  # No permitir crear referencias desde el admin

    def has_delete_permission(self, request, obj=None):
        return False  # No permitir eliminar referencias desde el admin 